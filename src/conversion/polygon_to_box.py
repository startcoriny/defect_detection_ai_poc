import csv
import json
import logging
import sys
from collections import Counter
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
CLASS_MAPPING_PATH = PROJECT_ROOT / "metadata" / "class_mapping.json"
CLASS_STATISTICS_PATH = PROJECT_ROOT / "metadata" / "class_statistics.csv"
BBOX_ANNOTATIONS_PATH = PROJECT_ROOT / "metadata" / "bbox_annotations.csv"
BBOX_ERRORS_PATH = PROJECT_ROOT / "metadata" / "bbox_conversion_errors.csv"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "polygon-box-comparison"
BBOX_FIELDS = (
    "image_name",
    "annotation_index",
    "class_name",
    "class_id",
    "x_min",
    "y_min",
    "x_max",
    "y_max",
    "box_width",
    "box_height",
    "image_width",
    "image_height",
)
ERROR_FIELDS = ("image_name", "annotation_index", "reason")
POLYGON_COLOR = (0, 255, 255)
BOX_COLOR = (0, 0, 255)


# CSV의 문자열 불리언 값을 판별합니다.
def is_true(value: str) -> bool:
    return value.strip().lower() == "true"


# 선별 목록과 인벤토리를 이미지명으로 조인합니다.
def load_selected_records() -> list[dict[str, str]]:
    with SELECTED_DATASET_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        selected_names = {
            row["image_name"]
            for row in csv.DictReader(csv_file)
            if is_true(row.get("selected", ""))
        }

    with INVENTORY_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        inventory = {
            row["image_name"]: row
            for row in csv.DictReader(csv_file)
            if row["image_name"] in selected_names
        }

    missing_names = sorted(selected_names - inventory.keys())
    if missing_names:
        raise ValueError(f"인벤토리에 없는 선별 이미지: {', '.join(missing_names)}")
    return [inventory[image_name] for image_name in sorted(selected_names)]


# 원본 클래스명에서 표준 클래스명으로의 매핑을 읽습니다.
def load_class_mapping() -> dict[str, str | None]:
    mapping = load_json(CLASS_MAPPING_PATH)
    if not isinstance(mapping, dict):
        raise ValueError("class_mapping.json root must be an object")
    return mapping


# 작업 6에서 확정한 표준 클래스별 고정 ID를 읽습니다.
def load_class_ids() -> dict[str, int]:
    with CLASS_STATISTICS_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        return {
            row["class_name"]: int(row["class_id"]) for row in csv.DictReader(csv_file)
        }


# Polygon 하나를 이미지 경계 안의 Bounding Box로 변환합니다.
def convert_annotation(
    annotation: dict[str, Any],
    image_name: str,
    annotation_index: int,
    width: int,
    height: int,
    class_mapping: dict[str, str | None],
    class_ids: dict[str, int],
) -> tuple[dict[str, Any] | None, str | None]:
    coordinate = annotation["coordinate"]
    x_values = coordinate["x"]
    y_values = coordinate["y"]
    if len(x_values) != len(y_values):
        return None, "coordinate_count_mismatch"
    if not x_values:
        return None, "degenerate_box_after_clipping"

    x_min = max(min(x_values), 0)
    x_max = min(max(x_values), width)
    y_min = max(min(y_values), 0)
    y_max = min(max(y_values), height)
    if x_min >= x_max or y_min >= y_max:
        return None, "degenerate_box_after_clipping"

    raw_class = annotation["case"]
    if raw_class not in class_mapping or class_mapping[raw_class] is None:
        raise ValueError(f"표준 클래스 매핑 없음: {raw_class!r}")
    class_name = class_mapping[raw_class]
    if class_name not in class_ids:
        raise ValueError(f"고정 class_id 없음: {class_name!r}")

    return (
        {
            "image_name": image_name,
            "annotation_index": annotation_index,
            "class_name": class_name,
            "class_id": class_ids[class_name],
            "x_min": x_min,
            "y_min": y_min,
            "x_max": x_max,
            "y_max": y_max,
            "box_width": x_max - x_min,
            "box_height": y_max - y_min,
            "image_width": width,
            "image_height": height,
        },
        None,
    )


# 원본 Polygon과 변환된 Box를 한 이미지에 그립니다.
def draw_comparison(
    image: np.ndarray,
    label_data: dict[str, Any],
    image_name: str,
    boxes_by_index: dict[int, dict[str, Any]],
) -> np.ndarray:
    result = image.copy()
    for annotation_index, annotation in enumerate(label_data["annotations"]):
        if annotation["case"] == "":
            continue
        coordinate = annotation["coordinate"]
        x_values = coordinate["x"]
        y_values = coordinate["y"]
        if len(x_values) == len(y_values) and x_values:
            points = np.rint(np.column_stack((x_values, y_values))).astype(np.int32)
            cv2.polylines(
                result,
                [points.reshape((-1, 1, 2))],
                True,
                POLYGON_COLOR,
                1,
                cv2.LINE_AA,
            )

        box = boxes_by_index.get(annotation_index)
        if box is None:
            continue
        top_left = (int(round(box["x_min"])), int(round(box["y_min"])))
        bottom_right = (int(round(box["x_max"])), int(round(box["y_max"])))
        cv2.rectangle(result, top_left, bottom_right, BOX_COLOR, 3, cv2.LINE_AA)
        cv2.putText(
            result,
            str(box["class_name"]),
            (max(0, top_left[0]), max(20, top_left[1] - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            BOX_COLOR,
            2,
            cv2.LINE_AA,
        )

    height = int(label_data["image_data"]["height"])
    width = int(label_data["image_data"]["width"])
    cv2.putText(
        result,
        f"{image_name} {width}x{height}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return result


# Unicode 경로에서도 동작하도록 JPEG 인코딩 후 저장합니다.
def save_image(image: np.ndarray, output_path: Path) -> None:
    success, encoded = cv2.imencode(".jpg", image)
    if not success:
        raise OSError("JPEG encoding failed")
    output_path.write_bytes(encoded.tobytes())


# 지정된 컬럼 순서로 CSV를 저장합니다.
def write_csv(
    path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, Any]]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# 선별 이미지 전체를 변환하고 비교 이미지를 생성합니다.
def run_conversion(
    records: list[dict[str, str]],
    class_mapping: dict[str, str | None],
    class_ids: dict[str, int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, tuple[int, int]]]:
    boxes: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    count_mismatches: dict[str, tuple[int, int]] = {}

    for record in records:
        image_name = record["image_name"]
        label_data = load_json(PROJECT_ROOT / record["json_path"])
        if not isinstance(label_data, dict):
            raise TypeError(f"JSON root must be an object: {image_name}")
        width = int(label_data["image_data"]["width"])
        height = int(label_data["image_data"]["height"])
        annotations = label_data["annotations"]
        before_count = 0
        image_boxes: dict[int, dict[str, Any]] = {}

        for annotation_index, annotation in enumerate(annotations):
            if annotation["case"] == "":
                continue
            before_count += 1
            box, reason = convert_annotation(
                annotation,
                image_name,
                annotation_index,
                width,
                height,
                class_mapping,
                class_ids,
            )
            if reason is not None:
                errors.append(
                    {
                        "image_name": image_name,
                        "annotation_index": annotation_index,
                        "reason": reason,
                    }
                )
                continue
            if box is not None:
                boxes.append(box)
                image_boxes[annotation_index] = box

        after_count = len(image_boxes)
        if before_count != after_count:
            count_mismatches[image_name] = (before_count, after_count)

        image = read_image(PROJECT_ROOT / record["image_path"])
        if image is None:
            raise OSError(f"이미지 읽기 실패: {image_name}")
        comparison = draw_comparison(image, label_data, image_name, image_boxes)
        save_image(comparison, OUTPUT_ROOT / f"{image_name}.jpg")

    return boxes, errors, count_mismatches


# Polygon 변환, 오류 기록, 전체 비교 이미지 생성을 실행합니다.
def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
    )
    try:
        records = load_selected_records()
        class_mapping = load_class_mapping()
        class_ids = load_class_ids()
        LOGGER.info("대상 이미지 수: %d", len(records))
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        boxes, errors, count_mismatches = run_conversion(
            records, class_mapping, class_ids
        )
        write_csv(BBOX_ANNOTATIONS_PATH, BBOX_FIELDS, boxes)
        write_csv(BBOX_ERRORS_PATH, ERROR_FIELDS, errors)
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
        cv2.error,
    ) as error:
        LOGGER.error("Polygon to Box 변환 실패 (%s)", error)
        return 1

    processed_count = len(boxes) + len(errors)
    LOGGER.info(
        "처리 완료: annotations=%d, success=%d, errors=%d",
        processed_count,
        len(boxes),
        len(errors),
    )
    reason_counts = Counter(error["reason"] for error in errors)
    for reason, count in sorted(reason_counts.items()):
        LOGGER.info("오류 사유: %s=%d", reason, count)
    for image_name, (before_count, after_count) in sorted(count_mismatches.items()):
        LOGGER.warning(
            "객체 수 불일치: %s before=%d after=%d",
            image_name,
            before_count,
            after_count,
        )
    LOGGER.info("객체 수 불일치 이미지 수: %d", len(count_mismatches))
    return 0


if __name__ == "__main__":
    sys.exit(main())
