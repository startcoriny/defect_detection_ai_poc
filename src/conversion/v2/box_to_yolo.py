import csv
import logging
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SELECTED_DATASET_PATH = PROJECT_ROOT / "metadata" / "v2" / "selected_dataset.csv"
BBOX_ANNOTATIONS_PATH = PROJECT_ROOT / "metadata" / "v2" / "bbox_annotations.csv"
CLASS_STATISTICS_PATH = PROJECT_ROOT / "metadata" / "class_statistics.csv"
YOLO_CLASSES_PATH = PROJECT_ROOT / "metadata" / "v2" / "yolo_classes.txt"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "yolo_labels_v2"

LOGGER = logging.getLogger(__name__)


# CSV의 문자열 불리언 값을 판별합니다.
def is_true(value: str) -> bool:
    return value.strip().lower() == "true"


# YOLO 라벨을 생성할 선별 이미지명을 읽습니다.
def load_selected_image_names() -> list[str]:
    with SELECTED_DATASET_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        image_names = [
            row["image_name"]
            for row in csv.DictReader(csv_file)
            if is_true(row.get("selected", ""))
        ]

    if len(image_names) != len(set(image_names)):
        raise ValueError("selected_dataset.csv에 중복된 선별 이미지명이 있습니다.")
    return sorted(image_names)


# class_id 순서대로 표준 클래스 목록을 읽고 연속된 ID인지 검증합니다.
def load_classes() -> list[tuple[int, str]]:
    with CLASS_STATISTICS_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        classes = sorted(
            (
                (int(row["class_id"]), row["class_name"])
                for row in csv.DictReader(csv_file)
            ),
            key=lambda item: item[0],
        )

    class_ids = [class_id for class_id, _ in classes]
    if class_ids != list(range(len(classes))):
        raise ValueError("class_id는 0부터 빈 번호 없이 연속되어야 합니다.")
    if len({class_name for _, class_name in classes}) != len(classes):
        raise ValueError("class_statistics.csv에 중복된 클래스명이 있습니다.")
    return classes


# Bounding Box 행을 이미지별 annotation_index 순서로 그룹핑합니다.
def load_boxes(
    selected_image_names: set[str], valid_class_ids: set[int]
) -> dict[str, list[dict[str, str]]]:
    boxes_by_image: dict[str, list[dict[str, str]]] = defaultdict(list)
    with BBOX_ANNOTATIONS_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            image_name = row["image_name"]
            if image_name not in selected_image_names:
                raise ValueError(f"선별 목록에 없는 Bounding Box 이미지: {image_name}")
            class_id = int(row["class_id"])
            if class_id not in valid_class_ids:
                raise ValueError(f"정의되지 않은 class_id: {class_id} ({image_name})")
            boxes_by_image[image_name].append(row)

    for boxes in boxes_by_image.values():
        boxes.sort(key=lambda row: int(row["annotation_index"]))
    return dict(boxes_by_image)


# 픽셀 Bounding Box 한 건을 YOLO Detection 라인으로 변환합니다.
def convert_box_to_yolo(row: dict[str, str]) -> str:
    image_name = row["image_name"]
    image_width = float(row["image_width"])
    image_height = float(row["image_height"])
    if image_width <= 0 or image_height <= 0:
        raise ValueError(f"이미지 크기는 양수여야 합니다: {image_name}")

    x_min = float(row["x_min"])
    y_min = float(row["y_min"])
    x_max = float(row["x_max"])
    y_max = float(row["y_max"])
    normalized = (
        (x_min + x_max) / 2 / image_width,
        (y_min + y_max) / 2 / image_height,
        (x_max - x_min) / image_width,
        (y_max - y_min) / image_height,
    )
    if not all(0.0 <= value <= 1.0 for value in normalized):
        annotation_index = row["annotation_index"]
        raise ValueError(
            "YOLO 좌표가 0~1 범위를 벗어났습니다: "
            f"{image_name} annotation_index={annotation_index}"
        )

    center_x, center_y, box_width, box_height = normalized
    return (
        f"{int(row['class_id'])} {center_x:.6f} {center_y:.6f} "
        f"{box_width:.6f} {box_height:.6f}"
    )


# 모든 선별 이미지의 라벨 파일과 클래스 매핑 파일을 생성합니다.
def write_yolo_files(
    image_names: list[str],
    boxes_by_image: dict[str, list[dict[str, str]]],
    classes: list[tuple[int, str]],
) -> tuple[int, int, Counter[int]]:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    class_counts: Counter[int] = Counter()
    empty_label_count = 0
    object_count = 0

    for image_name in image_names:
        boxes = boxes_by_image.get(image_name, [])
        lines = [convert_box_to_yolo(row) for row in boxes]
        label_text = "" if not lines else "\n".join(lines) + "\n"
        with (OUTPUT_ROOT / f"{image_name}.txt").open(
            "w", encoding="utf-8", newline="\n"
        ) as label_file:
            label_file.write(label_text)

        if not boxes:
            empty_label_count += 1
        object_count += len(boxes)
        class_counts.update(int(row["class_id"]) for row in boxes)

    class_text = "\n".join(class_name for _, class_name in classes) + "\n"
    with YOLO_CLASSES_PATH.open("w", encoding="utf-8", newline="\n") as class_file:
        class_file.write(class_text)

    return empty_label_count, object_count, class_counts


# Bounding Box CSV를 YOLO Detection 라벨로 변환합니다.
def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
    )
    try:
        image_names = load_selected_image_names()
        classes = load_classes()
        valid_class_ids = {class_id for class_id, _ in classes}
        boxes_by_image = load_boxes(set(image_names), valid_class_ids)

        LOGGER.info("대상 이미지 수: %d", len(image_names))
        empty_count, object_count, class_counts = write_yolo_files(
            image_names, boxes_by_image, classes
        )
    except (OSError, UnicodeError, KeyError, TypeError, ValueError) as error:
        LOGGER.error("Box to YOLO 변환 실패 (%s)", error)
        return 1

    LOGGER.info("생성된 라벨 파일 수: %d", len(image_names))
    LOGGER.info("빈 라벨 수: %d", empty_count)
    LOGGER.info("객체가 있는 라벨 파일 수: %d", len(image_names) - empty_count)
    LOGGER.info("전체 객체 수: %d", object_count)
    for class_id, class_name in classes:
        LOGGER.info(
            "클래스별 객체 수: class_id=%d class_name=%s count=%d",
            class_id,
            class_name,
            class_counts[class_id],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
