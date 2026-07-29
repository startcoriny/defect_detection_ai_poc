import csv
import json
import logging
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.image_utils import read_image  # noqa: E402
from common.json_utils import load_json  # noqa: E402

LOGGER = logging.getLogger(__name__)
EXPERIMENT_ID = "EXP-P1-DET-007"
PREDICTIONS_PATH = (
    PROJECT_ROOT / "predictions" / EXPERIMENT_ID / "prediction_results.json"
)
AUTO_LABEL_ROOT = PROJECT_ROOT / "auto-labels" / EXPERIMENT_ID
LABEL_ROOT = AUTO_LABEL_ROOT / "yolo-labels"
PREDICTION_METADATA_ROOT = AUTO_LABEL_ROOT / "prediction-metadata"
EXPORT_METADATA_PATH = PREDICTION_METADATA_ROOT / "export_metadata.json"
PRESERVED_PREDICTIONS_PATH = PREDICTION_METADATA_ROOT / "prediction_results.json"
CLASS_NAMES_PATH = PROJECT_ROOT / "metadata" / "yolo_classes.txt"
IMAGE_ROOT = PROJECT_ROOT / "data" / "processed" / "dataset_v3" / "images" / "test"
CVAT_IMPORT_ROOT = AUTO_LABEL_ROOT / "cvat-import"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / EXPERIMENT_ID / "auto-label-visualization"
MISMATCHES_PATH = (
    PROJECT_ROOT
    / "reports"
    / "evaluation"
    / EXPERIMENT_ID
    / "auto_label_roundtrip_mismatches.csv"
)
MISMATCH_FIELDS = ("image_name", "prediction_index", "reason")
COORDINATE_TOLERANCE = 1e-4
BOX_COLOR = (255, 0, 255)


# JSON 객체를 읽고 최상위 자료형을 검증합니다.
def load_json_object(path: Path) -> dict[str, Any]:
    data = load_json(path)
    if not isinstance(data, dict):
        raise TypeError(f"JSON root must be an object: {path}")
    return data


# 클래스 ID 순서대로 클래스명 목록을 읽습니다.
def load_class_names() -> list[str]:
    names = [
        line.strip()
        for line in CLASS_NAMES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not names:
        raise ValueError(f"클래스 목록이 비어 있습니다: {CLASS_NAMES_PATH}")
    return names


# 이미지별 Prediction을 중복 없이 인덱싱합니다.
def index_images(data: dict[str, Any], source: Path) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for record in data["images"]:
        image_name = record["image_name"]
        if image_name in indexed:
            raise ValueError(f"중복 이미지명: {image_name} ({source})")
        indexed[image_name] = record
    return indexed


# YOLO 라벨 한 줄을 class_id와 정규화 좌표로 변환합니다.
def parse_yolo_line(line: str) -> tuple[int, float, float, float, float]:
    values = line.split()
    if len(values) != 5:
        raise ValueError("field_count")
    try:
        return (
            int(values[0]),
            float(values[1]),
            float(values[2]),
            float(values[3]),
            float(values[4]),
        )
    except ValueError as error:
        raise ValueError("non_numeric_value") from error


# 정규화된 중심 좌표를 픽셀 모서리 좌표로 복원합니다.
def restore_box(
    label: tuple[int, float, float, float, float],
    width: int,
    height: int,
) -> tuple[float, float, float, float]:
    _, center_x, center_y, box_width, box_height = label
    return (
        (center_x - box_width / 2) * width,
        (center_y - box_height / 2) * height,
        (center_x + box_width / 2) * width,
        (center_y + box_height / 2) * height,
    )


# 복원 Box와 클래스·Confidence를 이미지에 표시합니다.
def draw_predictions(
    image: np.ndarray,
    image_name: str,
    model_version: str,
    labels: list[tuple[int, float, float, float, float] | None],
    class_names: list[str],
    confidences: list[float],
) -> np.ndarray:
    result = image.copy()
    height, width = result.shape[:2]
    for index, label in enumerate(labels):
        if label is None or not 0 <= label[0] < len(class_names):
            continue
        x_min, y_min, x_max, y_max = restore_box(label, width, height)
        top_left = (int(round(x_min)), int(round(y_min)))
        bottom_right = (int(round(x_max)), int(round(y_max)))
        cv2.rectangle(
            result,
            top_left,
            bottom_right,
            BOX_COLOR,
            3,
            cv2.LINE_AA,
        )
        confidence = confidences[index] if index < len(confidences) else float("nan")
        label_text = f"{class_names[label[0]]} {confidence:.3f}"
        cv2.putText(
            result,
            label_text,
            (max(0, top_left[0]), max(22, top_left[1] - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            BOX_COLOR,
            2,
            cv2.LINE_AA,
        )

    cv2.putText(
        result,
        f"{image_name} | model: {model_version}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return result


# Unicode 경로를 지원하도록 JPEG 인코딩 후 바이트로 저장합니다.
def save_image(image: np.ndarray, output_path: Path) -> None:
    success, encoded = cv2.imencode(".jpg", image)
    if not success:
        raise OSError("JPEG encoding failed")
    output_path.write_bytes(encoded.tobytes())


# 불일치 결과를 고정된 컬럼 순서로 저장합니다.
def write_mismatches(rows: list[dict[str, Any]]) -> None:
    MISMATCHES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MISMATCHES_PATH.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=MISMATCH_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


# 한 이미지의 TXT와 원본 Prediction을 순서대로 왕복 검증합니다.
def validate_labels(
    image_name: str,
    expected: list[dict[str, Any]],
    class_names: list[str],
    mismatches: list[dict[str, Any]],
) -> list[tuple[int, float, float, float, float] | None]:
    label_path = LABEL_ROOT / f"{Path(image_name).stem}.txt"
    if not label_path.is_file():
        mismatches.append(
            {
                "image_name": image_name,
                "prediction_index": "",
                "reason": "label_file_missing",
            }
        )
        return []

    lines = label_path.read_text(encoding="utf-8").splitlines()
    if len(lines) != len(expected):
        mismatches.append(
            {
                "image_name": image_name,
                "prediction_index": "",
                "reason": "object_count_mismatch",
            }
        )

    labels: list[tuple[int, float, float, float, float] | None] = []
    for index, line in enumerate(lines):
        try:
            label = parse_yolo_line(line)
        except ValueError as error:
            mismatches.append(
                {
                    "image_name": image_name,
                    "prediction_index": index,
                    "reason": f"invalid_label_{error}",
                }
            )
            labels.append(None)
            continue
        labels.append(label)
        if index >= len(expected):
            continue

        prediction = expected[index]
        class_id = label[0]
        if class_id != int(prediction["class_id"]):
            mismatches.append(
                {
                    "image_name": image_name,
                    "prediction_index": index,
                    "reason": "class_id_mismatch",
                }
            )
        coordinates = label[1:]
        expected_coordinates = prediction["bbox_normalized_xywh"]
        if (
            len(expected_coordinates) != 4
            or max(
                abs(actual - float(reference))
                for actual, reference in zip(coordinates, expected_coordinates)
            )
            > COORDINATE_TOLERANCE
        ):
            mismatches.append(
                {
                    "image_name": image_name,
                    "prediction_index": index,
                    "reason": "coordinate_mismatch",
                }
            )
        if not 0 <= class_id < len(class_names):
            reason = "class_id_out_of_range"
        elif class_names[class_id] != prediction["class_name"]:
            reason = "class_name_mismatch"
        else:
            reason = ""
        if reason:
            mismatches.append(
                {
                    "image_name": image_name,
                    "prediction_index": index,
                    "reason": reason,
                }
            )
    return labels


# 전체 Test 이미지의 자동 라벨을 검증하고 재시각화합니다.
def validate_and_visualize(
    original: dict[str, Any],
    preserved: dict[str, Any],
    class_names: list[str],
    model_version: str,
    mismatches: list[dict[str, Any]],
) -> int:
    original_images = index_images(original, PREDICTIONS_PATH)
    preserved_images = index_images(preserved, PRESERVED_PREDICTIONS_PATH)
    visualized_count = 0

    for image_name, record in original_images.items():
        expected = record["predictions"]
        labels = validate_labels(image_name, expected, class_names, mismatches)
        metadata_record = preserved_images.get(image_name)
        if metadata_record is None:
            mismatches.append(
                {
                    "image_name": image_name,
                    "prediction_index": "",
                    "reason": "prediction_metadata_missing",
                }
            )
            confidences: list[float] = []
        else:
            metadata_predictions = metadata_record["predictions"]
            confidences = [
                float(prediction["confidence"]) for prediction in metadata_predictions
            ]
            if len(confidences) != len(expected):
                mismatches.append(
                    {
                        "image_name": image_name,
                        "prediction_index": "",
                        "reason": "confidence_count_mismatch",
                    }
                )
            for index, (prediction, metadata_prediction) in enumerate(
                zip(expected, metadata_predictions)
            ):
                if float(prediction["confidence"]) != float(
                    metadata_prediction["confidence"]
                ):
                    mismatches.append(
                        {
                            "image_name": image_name,
                            "prediction_index": index,
                            "reason": "confidence_mismatch",
                        }
                    )

        image = read_image(IMAGE_ROOT / image_name)
        if image is None:
            mismatches.append(
                {
                    "image_name": image_name,
                    "prediction_index": "",
                    "reason": "image_read_failed",
                }
            )
            continue
        visualization = draw_predictions(
            image,
            image_name,
            model_version,
            labels,
            class_names,
            confidences,
        )
        save_image(visualization, OUTPUT_ROOT / image_name)
        visualized_count += 1
    return visualized_count


# CVAT YOLO Import 패키지의 필수 파일과 개수를 확인합니다.
def validate_cvat_structure() -> bool:
    names_path = CVAT_IMPORT_ROOT / "obj.names"
    data_path = CVAT_IMPORT_ROOT / "obj.data"
    train_path = CVAT_IMPORT_ROOT / "train.txt"
    object_root = CVAT_IMPORT_ROOT / "obj_train_data"

    names_count = (
        len(names_path.read_text(encoding="utf-8").splitlines())
        if names_path.is_file()
        else 0
    )
    train_count = (
        len(train_path.read_text(encoding="utf-8").splitlines())
        if train_path.is_file()
        else 0
    )
    object_files = list(object_root.iterdir()) if object_root.is_dir() else []
    image_count = sum(path.suffix.lower() == ".jpg" for path in object_files)
    label_count = sum(path.suffix.lower() == ".txt" for path in object_files)
    total_count = len([path for path in object_files if path.is_file()])

    LOGGER.info(
        "CVAT 구조: obj.names=%s (%d줄), obj.data=%s, train.txt=%s (%d줄)",
        names_path.is_file(),
        names_count,
        data_path.is_file(),
        train_path.is_file(),
        train_count,
    )
    LOGGER.info(
        "CVAT 구조: obj_train_data 이미지=%d, 라벨=%d, 전체=%d",
        image_count,
        label_count,
        total_count,
    )
    valid = (
        names_path.is_file()
        and names_count == 6
        and data_path.is_file()
        and train_path.is_file()
        and train_count == 84
        and image_count == 84
        and label_count == 84
        and total_count == 168
    )
    LOGGER.info("CVAT Import 구조 확인: %s", "PASS" if valid else "FAIL")
    return valid


# 자동 라벨 왕복 검증, 시각화, CVAT 구조 확인을 실행합니다.
def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
    )
    try:
        original = load_json_object(PREDICTIONS_PATH)
        preserved = load_json_object(PRESERVED_PREDICTIONS_PATH)
        export_metadata = load_json_object(EXPORT_METADATA_PATH)
        class_names = load_class_names()
        mismatches: list[dict[str, Any]] = []
        model_version = str(original["model_version"])
        if export_metadata.get("model_version") != model_version:
            mismatches.append(
                {
                    "image_name": "",
                    "prediction_index": "",
                    "reason": "model_version_mismatch",
                }
            )
        if preserved.get("model_version") != model_version:
            mismatches.append(
                {
                    "image_name": "",
                    "prediction_index": "",
                    "reason": "prediction_metadata_model_version_mismatch",
                }
            )

        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        visualized_count = validate_and_visualize(
            original,
            preserved,
            class_names,
            model_version,
            mismatches,
        )
        write_mismatches(mismatches)
        cvat_valid = validate_cvat_structure()
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
        cv2.error,
    ) as error:
        LOGGER.error("자동 라벨 왕복 검증 실패 (%s)", error)
        return 1

    LOGGER.info("대상 이미지 수: %d", len(original["images"]))
    LOGGER.info("시각화 이미지 수: %d", visualized_count)
    LOGGER.info("발견된 불일치 건수: %d", len(mismatches))
    reason_counts = Counter(row["reason"] for row in mismatches)
    for reason, count in sorted(reason_counts.items()):
        LOGGER.info("불일치 사유: %s=%d", reason, count)
    passed = not mismatches and cvat_valid
    LOGGER.info("전체 통과 여부: %s", "PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
