import csv
import logging
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METADATA_ROOT = PROJECT_ROOT / "metadata"
REPORT_ROOT = PROJECT_ROOT / "reports" / "dataset"
LOGGER = logging.getLogger(__name__)

SUMMARY_FIELD_NAMES = ("key", "value")
CLASS_FIELD_NAMES = ("class_id", "class_name", "image_count", "object_count")
SIZE_FIELD_NAMES = ("class_name", "size_bucket", "count", "percentage")
SIZE_BUCKETS = ("Small", "Medium", "Large")


# CSV 파일을 딕셔너리 목록으로 읽습니다.
def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


# 선별 데이터와 원본 인벤토리를 결합해 이미지별 해상도를 반환합니다.
def load_selected_images() -> dict[str, tuple[int, int]]:
    selected_rows = read_csv(METADATA_ROOT / "selected_dataset.csv")
    selected_names = {
        row["image_name"] for row in selected_rows if row["selected"] == "True"
    }
    if len(selected_names) != sum(row["selected"] == "True" for row in selected_rows):
        raise ValueError("selected_dataset.csv에 중복된 선택 이미지가 있습니다.")

    inventory = {}
    for row in read_csv(METADATA_ROOT / "raw_dataset_inventory.csv"):
        image_name = row["image_name"]
        if image_name not in selected_names:
            continue
        if image_name in inventory:
            raise ValueError(f"인벤토리에 중복 이미지가 있습니다: {image_name}")
        width = int(row["width"])
        height = int(row["height"])
        if width <= 0 or height <= 0:
            raise ValueError(f"이미지 치수가 올바르지 않습니다: {image_name}")
        inventory[image_name] = (width, height)

    missing_names = selected_names - inventory.keys()
    if missing_names:
        raise ValueError(
            "인벤토리에 선택 이미지가 없습니다: " + ", ".join(sorted(missing_names))
        )
    return inventory


# 선택 이미지에 속한 객체만 읽고 객체 치수와 클래스 정보를 검증합니다.
def load_annotations(
    selected_images: dict[str, tuple[int, int]],
) -> list[dict[str, Any]]:
    annotations = []
    for row in read_csv(METADATA_ROOT / "bbox_annotations.csv"):
        image_name = row["image_name"]
        if image_name not in selected_images:
            continue
        box_width = float(row["box_width"])
        box_height = float(row["box_height"])
        image_width = float(row["image_width"])
        image_height = float(row["image_height"])
        if min(box_width, box_height, image_width, image_height) <= 0:
            raise ValueError(f"객체 또는 이미지 치수가 올바르지 않습니다: {image_name}")
        annotations.append(
            {
                "image_name": image_name,
                "class_id": int(row["class_id"]),
                "class_name": row["class_name"],
                "relative_area": (box_width / image_width)
                * (box_height / image_height),
            }
        )
    return annotations


# 표준 클래스 목록을 ID 순서로 읽습니다.
def load_standard_classes() -> list[dict[str, Any]]:
    classes = [
        {"class_id": int(row["class_id"]), "class_name": row["class_name"]}
        for row in read_csv(METADATA_ROOT / "class_statistics.csv")
    ]
    classes.sort(key=lambda row: row["class_id"])
    if [row["class_id"] for row in classes] != list(range(6)):
        raise ValueError("표준 클래스 ID는 0부터 5까지 모두 존재해야 합니다.")
    return classes


# 객체의 상대 면적을 Small, Medium, Large 중 하나로 분류합니다.
def classify_size(relative_area: float) -> str:
    if relative_area < 0.01:
        return "Small"
    if relative_area < 0.05:
        return "Medium"
    return "Large"


# 이미지, 객체, 해상도 핵심 통계를 지정된 순서로 집계합니다.
def build_summary(
    selected_images: dict[str, tuple[int, int]],
    annotations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    object_counts = Counter(row["image_name"] for row in annotations)
    image_classes: dict[str, set[str]] = defaultdict(set)
    for row in annotations:
        image_classes[row["image_name"]].add(row["class_name"])

    total_images = len(selected_images)
    total_objects = len(annotations)
    defect_images = len(object_counts)
    normal_images = total_images - defect_images
    widths = [resolution[0] for resolution in selected_images.values()]
    heights = [resolution[1] for resolution in selected_images.values()]
    values = (
        ("total_images", total_images),
        ("normal_images", normal_images),
        ("defect_images", defect_images),
        ("total_objects", total_objects),
        ("avg_objects_per_image", f"{total_objects / total_images:.6f}"),
        (
            "avg_objects_per_defect_image",
            f"{total_objects / defect_images:.6f}" if defect_images else "0.000000",
        ),
        ("multi_object_images", sum(count >= 2 for count in object_counts.values())),
        (
            "multi_class_images",
            sum(len(class_names) >= 2 for class_names in image_classes.values()),
        ),
        ("distinct_resolutions", len(set(selected_images.values()))),
        ("image_width_min", min(widths)),
        ("image_width_max", max(widths)),
        ("image_height_min", min(heights)),
        ("image_height_max", max(heights)),
    )
    return [{"key": key, "value": value} for key, value in values]


# 6개 표준 클래스의 이미지 수와 객체 수를 집계합니다.
def build_class_distribution(
    standard_classes: list[dict[str, Any]],
    annotations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    standard_by_id = {row["class_id"]: row["class_name"] for row in standard_classes}
    image_names: dict[int, set[str]] = defaultdict(set)
    object_counts: Counter[int] = Counter()
    for row in annotations:
        class_id = row["class_id"]
        if standard_by_id.get(class_id) != row["class_name"]:
            raise ValueError(
                f"표준 클래스와 객체 클래스가 일치하지 않습니다: {class_id}"
            )
        image_names[class_id].add(row["image_name"])
        object_counts[class_id] += 1

    return [
        {
            **class_row,
            "image_count": len(image_names[class_row["class_id"]]),
            "object_count": object_counts[class_row["class_id"]],
        }
        for class_row in standard_classes
    ]


# 전체 및 실제 등장 클래스별 객체 크기 분포를 집계합니다.
def build_size_distribution(
    annotations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    class_names = sorted({row["class_name"] for row in annotations})
    rows = []
    for class_name in ["all", *class_names]:
        group = (
            annotations
            if class_name == "all"
            else [row for row in annotations if row["class_name"] == class_name]
        )
        counts = Counter(classify_size(row["relative_area"]) for row in group)
        for bucket in SIZE_BUCKETS:
            count = counts[bucket]
            rows.append(
                {
                    "class_name": class_name,
                    "size_bucket": bucket,
                    "count": count,
                    "percentage": f"{count / len(group) * 100:.2f}",
                }
            )
    return rows


# 필드 순서를 고정해 CSV 산출물을 기록합니다.
def write_csv(
    path: Path, field_names: tuple[str, ...], rows: list[dict[str, Any]]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(rows)


# 집계 결과를 바탕으로 한글 데이터셋 분석 보고서를 기록합니다.
def write_report(
    selected_images: dict[str, tuple[int, int]],
    summary_rows: list[dict[str, Any]],
    class_rows: list[dict[str, Any]],
    size_rows: list[dict[str, Any]],
) -> None:
    summary = {row["key"]: row["value"] for row in summary_rows}
    resolution_counts = Counter(selected_images.values())
    top_resolutions = sorted(
        resolution_counts.items(), key=lambda item: (-item[1], item[0][0], item[0][1])
    )[:5]
    all_sizes = {
        row["size_bucket"]: row for row in size_rows if row["class_name"] == "all"
    }

    lines = [
        "# 선별 데이터셋 통계 분석 보고서",
        "",
        "## 데이터셋 개요",
        "",
        f"- 전체 이미지: {summary['total_images']}장",
        f"- 정상 이미지: {summary['normal_images']}장",
        f"- 불량 이미지: {summary['defect_images']}장",
        f"- 전체 객체: {summary['total_objects']}개",
        f"- 이미지당 평균 객체: {summary['avg_objects_per_image']}개",
        f"- 불량 이미지당 평균 객체: {summary['avg_objects_per_defect_image']}개",
        "",
        "## 클래스 분포",
        "",
        "| 클래스 ID | 클래스명 | 이미지 수 | 객체 수 |",
        "|---:|---|---:|---:|",
    ]
    lines.extend(
        f"| {row['class_id']} | {row['class_name']} | "
        f"{row['image_count']} | {row['object_count']} |"
        for row in class_rows
    )
    lines.extend(
        [
            "",
            "## 객체 크기 분포",
            "",
            "| 클래스명 | 크기 구간 | 객체 수 | 비율(%) |",
            "|---|---|---:|---:|",
        ]
    )
    lines.extend(
        f"| {row['class_name']} | {row['size_bucket']} | "
        f"{row['count']} | {row['percentage']} |"
        for row in size_rows
    )
    lines.extend(
        [
            "",
            f"전체 객체 중 Small 객체는 {all_sizes['Small']['count']}개"
            f"({all_sizes['Small']['percentage']}%)로, "
            "상대 면적이 1% 미만인 작은 결함이 데이터셋에서 큰 비중을 차지한다. "
            "따라서 후속 데이터 분할과 모델 평가에서 작은 결함의 분포가 유지되는지 확인할 필요가 있다.",
            "",
            "## 이미지 해상도 분포",
            "",
            "| 순위 | 해상도(width × height) | 이미지 수 |",
            "|---:|---:|---:|",
        ]
    )
    lines.extend(
        f"| {rank} | {width} × {height} | {count} |"
        for rank, ((width, height), count) in enumerate(top_resolutions, start=1)
    )
    lines.extend(
        [
            "",
            f"서로 다른 해상도는 총 {summary['distinct_resolutions']}종이다. "
            f"너비 범위는 {summary['image_width_min']}~{summary['image_width_max']}px, "
            f"높이 범위는 {summary['image_height_min']}~{summary['image_height_max']}px이다.",
            "",
            "## 복수 객체 및 복수 클래스 이미지",
            "",
            f"객체가 2개 이상인 이미지는 {summary['multi_object_images']}장이고, "
            f"서로 다른 클래스가 2개 이상인 이미지는 {summary['multi_class_images']}장이다. "
            "복수 객체 이미지는 한 이미지 안의 여러 결함을 함께 탐지해야 함을 뜻한다. "
            "복수 클래스 이미지 수는 작업8에서 두 클래스를 함께 포함하도록 강제 선별한 이미지 수와 일치하는지 확인하는 지표다.",
            "",
        ]
    )
    (REPORT_ROOT / "dataset_analysis_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


# 선별 데이터셋 통계 산출물 네 개를 생성합니다.
def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
    )
    selected_images = load_selected_images()
    annotations = load_annotations(selected_images)
    standard_classes = load_standard_classes()
    summary_rows = build_summary(selected_images, annotations)
    class_rows = build_class_distribution(standard_classes, annotations)
    size_rows = build_size_distribution(annotations)

    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    write_csv(
        REPORT_ROOT / "selected_dataset_statistics.csv",
        SUMMARY_FIELD_NAMES,
        summary_rows,
    )
    write_csv(REPORT_ROOT / "class_distribution.csv", CLASS_FIELD_NAMES, class_rows)
    write_csv(REPORT_ROOT / "object_size_distribution.csv", SIZE_FIELD_NAMES, size_rows)
    write_report(selected_images, summary_rows, class_rows, size_rows)
    LOGGER.info(
        "데이터셋 통계 생성 완료: 이미지 %d장, 객체 %d개",
        len(selected_images),
        len(annotations),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
