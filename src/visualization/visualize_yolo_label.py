import csv
import json
import logging
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.image_utils import read_image  # noqa: E402
from common.json_utils import load_json  # noqa: E402

LOGGER = logging.getLogger(__name__)
SELECTED_DATASET_PATH = PROJECT_ROOT / "metadata" / "selected_dataset.csv"
INVENTORY_PATH = PROJECT_ROOT / "metadata" / "raw_dataset_inventory.csv"
BBOX_ANNOTATIONS_PATH = PROJECT_ROOT / "metadata" / "bbox_annotations.csv"
MISMATCHES_PATH = PROJECT_ROOT / "metadata" / "yolo_roundtrip_mismatches.csv"
LABEL_ROOT = PROJECT_ROOT / "outputs" / "yolo_labels"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "yolo-label-visualization"
MISMATCH_FIELDS = ("image_name", "annotation_index", "reason")
POLYGON_COLOR = (0, 255, 255)
ROUNDTRIP_BOX_COLOR = (255, 0, 255)
COORDINATE_TOLERANCE = 0.5


# CSV의 문자열 불리언 값을 판별합니다.
def is_true(value: str) -> bool:
    return value.strip().lower() == "true"


# 선택 목록과 인벤토리를 이미지명으로 조인합니다.
def load_selected_records() -> list[dict[str, str]]:
    with SELECTED_DATASET_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        selected_names = [
            row["image_name"]
            for row in csv.DictReader(csv_file)
            if is_true(row.get("selected", ""))
        ]
    if len(selected_names) != len(set(selected_names)):
        raise ValueError("selected_dataset.csv에 중복된 선택 이미지명이 있습니다.")

    with INVENTORY_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        inventory = {
            row["image_name"]: row
            for row in csv.DictReader(csv_file)
            if row["image_name"] in selected_names
        }
    missing_names = sorted(set(selected_names) - inventory.keys())
    if missing_names:
        raise ValueError(f"인벤토리에 없는 선택 이미지: {', '.join(missing_names)}")
    return [inventory[image_name] for image_name in sorted(selected_names)]


# 정답 Box를 이미지별 annotation_index 순서로 읽습니다.
def load_expected_boxes(
    selected_names: set[str],
) -> dict[str, list[dict[str, str]]]:
    boxes_by_image: dict[str, list[dict[str, str]]] = defaultdict(list)
    with BBOX_ANNOTATIONS_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            if row["image_name"] not in selected_names:
                raise ValueError(
                    f"선택 목록에 없는 Bounding Box 이미지: {row['image_name']}"
                )
            boxes_by_image[row["image_name"]].append(row)
    for boxes in boxes_by_image.values():
        boxes.sort(key=lambda row: int(row["annotation_index"]))
    return dict(boxes_by_image)


# YOLO 한 줄을 class_id와 정규화 좌표로 변환합니다.
def parse_yolo_line(line: str, image_name: str, line_number: int) -> tuple[int, ...]:
    values = line.split()
    if len(values) != 5:
        raise ValueError(f"잘못된 YOLO 라벨: {image_name} line={line_number}")
    return (int(values[0]), *(float(value) for value in values[1:]))


# 정규화된 YOLO 좌표를 원본 픽셀 좌표로 복원합니다.
def restore_box(
    values: tuple[int, ...], width: float, height: float
) -> dict[str, float | int]:
    class_id, center_x, center_y, box_width, box_height = values
    return {
        "class_id": class_id,
        "x_min": (center_x - box_width / 2) * width,
        "y_min": (center_y - box_height / 2) * height,
        "x_max": (center_x + box_width / 2) * width,
        "y_max": (center_y + box_height / 2) * height,
    }


# 복원 Box가 원본 Polygon을 허용 오차 안에서 포함하는지 확인합니다.
def contains_polygon(box: dict[str, float | int], annotation: dict[str, Any]) -> bool:
    coordinate = annotation["coordinate"]
    x_values = coordinate["x"]
    y_values = coordinate["y"]
    if len(x_values) != len(y_values) or not x_values:
        return False
    return all(
        float(box["x_min"]) - COORDINATE_TOLERANCE
        <= float(x)
        <= float(box["x_max"]) + COORDINATE_TOLERANCE
        and float(box["y_min"]) - COORDINATE_TOLERANCE
        <= float(y)
        <= float(box["y_max"]) + COORDINATE_TOLERANCE
        for x, y in zip(x_values, y_values)
    )


# 원본 Polygon과 YOLO에서 복원한 Box를 함께 그립니다.
def draw_comparison(
    image: np.ndarray,
    label_data: dict[str, Any],
    image_name: str,
    restored_by_index: dict[int, dict[str, Any]],
) -> np.ndarray:
    result = image.copy()
    for annotation_index, annotation in enumerate(label_data["annotations"]):
        if annotation["case"] == "":
            continue
        coordinate = annotation["coordinate"]
        if len(coordinate["x"]) == len(coordinate["y"]) and coordinate["x"]:
            points = np.rint(
                np.column_stack((coordinate["x"], coordinate["y"]))
            ).astype(np.int32)
            cv2.polylines(
                result,
                [points.reshape((-1, 1, 2))],
                True,
                POLYGON_COLOR,
                1,
                cv2.LINE_AA,
            )

        box = restored_by_index.get(annotation_index)
        if box is None:
            continue
        top_left = (int(round(box["x_min"])), int(round(box["y_min"])))
        bottom_right = (int(round(box["x_max"])), int(round(box["y_max"])))
        cv2.rectangle(
            result,
            top_left,
            bottom_right,
            ROUNDTRIP_BOX_COLOR,
            3,
            cv2.LINE_AA,
        )
        cv2.putText(
            result,
            str(box["class_name"]),
            (max(0, top_left[0]), max(20, top_left[1] - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            ROUNDTRIP_BOX_COLOR,
            2,
            cv2.LINE_AA,
        )

    image_data = label_data["image_data"]
    cv2.putText(
        result,
        f"{image_name} {int(image_data['width'])}x{int(image_data['height'])}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
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
    with MISMATCHES_PATH.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=MISMATCH_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


# 선택 이미지 전체의 왕복 좌표를 검증하고 시각화합니다.
def validate_and_visualize(
    records: list[dict[str, str]],
    boxes_by_image: dict[str, list[dict[str, str]]],
) -> tuple[list[dict[str, Any]], int, float]:
    mismatches: list[dict[str, Any]] = []
    compared_count = 0
    maximum_error = 0.0

    for record in records:
        image_name = record["image_name"]
        expected = boxes_by_image.get(image_name, [])
        label_path = LABEL_ROOT / f"{image_name}.txt"
        if not label_path.is_file():
            mismatches.append(
                {
                    "image_name": image_name,
                    "annotation_index": "",
                    "reason": "label_file_missing",
                }
            )
            continue

        label_text = label_path.read_text(encoding="utf-8")
        lines = label_text.splitlines()
        if not expected and label_text:
            mismatches.append(
                {
                    "image_name": image_name,
                    "annotation_index": "",
                    "reason": "normal_image_label_not_empty",
                }
            )
        elif len(expected) != len(lines):
            mismatches.append(
                {
                    "image_name": image_name,
                    "annotation_index": "",
                    "reason": "object_count_mismatch",
                }
            )

        label_data = load_json(PROJECT_ROOT / record["json_path"])
        if not isinstance(label_data, dict):
            raise TypeError(f"JSON root must be an object: {image_name}")
        annotations = label_data["annotations"]
        restored_by_index: dict[int, dict[str, Any]] = {}

        for line_number, (row, line) in enumerate(zip(expected, lines), start=1):
            restored = restore_box(
                parse_yolo_line(line, image_name, line_number),
                float(row["image_width"]),
                float(row["image_height"]),
            )
            annotation_index = int(row["annotation_index"])
            compared_count += 1
            if int(restored["class_id"]) != int(row["class_id"]):
                mismatches.append(
                    {
                        "image_name": image_name,
                        "annotation_index": annotation_index,
                        "reason": "class_mismatch",
                    }
                )

            coordinate_error = max(
                abs(float(restored[field]) - float(row[field]))
                for field in ("x_min", "y_min", "x_max", "y_max")
            )
            maximum_error = max(maximum_error, coordinate_error)
            if coordinate_error > COORDINATE_TOLERANCE:
                mismatches.append(
                    {
                        "image_name": image_name,
                        "annotation_index": annotation_index,
                        "reason": "coordinate_rounding_error_exceeded",
                    }
                )
            if annotation_index >= len(annotations) or not contains_polygon(
                restored, annotations[annotation_index]
            ):
                mismatches.append(
                    {
                        "image_name": image_name,
                        "annotation_index": annotation_index,
                        "reason": "polygon_not_contained",
                    }
                )

            restored["class_name"] = row["class_name"]
            restored_by_index[annotation_index] = restored

        image = read_image(PROJECT_ROOT / record["image_path"])
        if image is None:
            raise OSError(f"이미지 읽기 실패: {image_name}")
        comparison = draw_comparison(image, label_data, image_name, restored_by_index)
        save_image(comparison, OUTPUT_ROOT / f"{image_name}.jpg")

    return mismatches, compared_count, maximum_error


# YOLO 라벨 왕복 검증과 전체 이미지 시각화를 실행합니다.
def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
    )
    try:
        records = load_selected_records()
        boxes_by_image = load_expected_boxes(
            {record["image_name"] for record in records}
        )
        LOGGER.info("대상 이미지 수: %d", len(records))
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        mismatches, compared_count, maximum_error = validate_and_visualize(
            records, boxes_by_image
        )
        write_mismatches(mismatches)
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
        cv2.error,
    ) as error:
        LOGGER.error("YOLO 라벨 왕복 검증 실패 (%s)", error)
        return 1

    LOGGER.info("검증한 객체 쌍 수: %d", compared_count)
    LOGGER.info("발견된 불일치 건수: %d", len(mismatches))
    reason_counts = Counter(row["reason"] for row in mismatches)
    for reason, count in sorted(reason_counts.items()):
        LOGGER.info("불일치 사유: %s=%d", reason, count)
    LOGGER.info("관측된 최대 좌표 오차(px): %.6f", maximum_error)
    LOGGER.info("전체 통과 여부: %s", "PASS" if not mismatches else "FAIL")
    return 0 if not mismatches else 1


if __name__ == "__main__":
    sys.exit(main())
