import csv
import json
import logging
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.file_utils import get_sorted_file_stems  # noqa: E402
from common.json_utils import load_json  # noqa: E402

LOGGER = logging.getLogger(__name__)
RAW_DATA_ROOT = PROJECT_ROOT / "data" / "raw" / "steel"
IMAGE_ROOT = RAW_DATA_ROOT / "01.원천데이터"
LABEL_ROOT = RAW_DATA_ROOT / "02.라벨링데이터"
METADATA_ROOT = PROJECT_ROOT / "metadata"
CATEGORIES = ("1. RTAL", "2. RTST", "3. VTST")
REQUIRED_JSON_KEYS = {"info", "image_data", "meta", "annotations"}
FIELD_NAMES = (
    "image_id",
    "image_name",
    "image_path",
    "json_path",
    "image_exists",
    "json_exists",
    "parse_success",
    "inspection_type",
    "material",
    "width",
    "height",
    "status",
    "classes",
    "num_annotations",
    "valid",
)


# 프로젝트 루트 기준 경로를 슬래시 형식으로 변환한다.
def relative_path(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


# 파싱 전 상태의 빈 인벤토리 레코드를 생성한다.
def create_empty_record(
    stem: str,
    image_path: Path,
    json_path: Path,
    image_exists: bool,
    json_exists: bool,
) -> dict[str, Any]:
    return {
        "image_id": "",
        "image_name": stem,
        "image_path": relative_path(image_path) if image_exists else "",
        "json_path": relative_path(json_path) if json_exists else "",
        "image_exists": image_exists,
        "json_exists": json_exists,
        "parse_success": False,
        "inspection_type": "",
        "material": "",
        "width": "",
        "height": "",
        "status": "",
        "classes": "",
        "num_annotations": 0,
        "valid": False,
    }


# 필수 구조가 확인된 JSON 정보를 인벤토리 레코드에 반영한다.
def populate_record(record: dict[str, Any], label_data: Any) -> None:
    if not isinstance(label_data, dict):
        raise ValueError("JSON root must be an object")

    missing_keys = REQUIRED_JSON_KEYS - label_data.keys()
    if missing_keys:
        missing = ", ".join(sorted(missing_keys))
        raise ValueError(f"missing required top-level keys: {missing}")

    info = label_data["info"]
    image_data = label_data["image_data"]
    meta = label_data["meta"]
    annotations = label_data["annotations"]
    if not isinstance(annotations, list):
        raise ValueError("annotations must be a list")

    class_names = {
        annotation["case"] for annotation in annotations if annotation["case"]
    }
    record.update(
        {
            "image_id": info["id"],
            "parse_success": True,
            "inspection_type": info["type"],
            "material": info["material"],
            "width": image_data["width"],
            "height": image_data["height"],
            "status": ("normal" if meta["annotation_case"] == ["normal"] else "defect"),
            "classes": ";".join(sorted(class_names)),
            "num_annotations": len(annotations),
        }
    )
    record["valid"] = (
        record["image_exists"] and record["json_exists"] and record["parse_success"]
    )


# 세 카테고리의 이미지와 JSON 합집합으로 인벤토리 레코드를 생성한다.
def build_records() -> list[dict[str, Any]]:
    records = []
    for category in CATEGORIES:
        image_directory = IMAGE_ROOT / category
        json_directory = LABEL_ROOT / category
        image_stems = set(get_sorted_file_stems(image_directory, ".jpg"))
        json_stems = set(get_sorted_file_stems(json_directory, ".json"))

        for stem in sorted(image_stems | json_stems):
            image_exists = stem in image_stems
            json_exists = stem in json_stems
            image_path = image_directory / f"{stem}.jpg"
            json_path = json_directory / f"{stem}.json"
            record = create_empty_record(
                stem, image_path, json_path, image_exists, json_exists
            )

            if not image_exists:
                LOGGER.error("Image missing: %s", image_path)
            if not json_exists:
                LOGGER.error("JSON missing: %s", json_path)
            else:
                try:
                    populate_record(record, load_json(json_path))
                except (
                    OSError,
                    UnicodeError,
                    json.JSONDecodeError,
                    KeyError,
                    TypeError,
                    ValueError,
                ) as error:
                    LOGGER.error("JSON parse failed: %s (%s)", json_path, error)

            records.append(record)

    return records


# 유효 레코드의 분포와 무효 사유별 개수를 집계한다.
def build_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    inspection_counts: Counter[str] = Counter()
    material_counts: Counter[str] = Counter()
    class_image_counts: Counter[str] = Counter()
    class_object_counts: Counter[str] = Counter()
    invalid_reasons = {
        "image_missing": 0,
        "json_missing": 0,
        "parse_failed": 0,
    }

    valid_records = [record for record in records if record["valid"]]
    for record in valid_records:
        inspection_counts[record["inspection_type"]] += 1
        material_counts[record["material"]] += 1

        label_data = load_json(PROJECT_ROOT / record["json_path"])
        record_classes = set()
        for annotation in label_data["annotations"]:
            class_name = annotation["case"]
            if class_name:
                record_classes.add(class_name)
                class_object_counts[class_name] += 1
        class_image_counts.update(record_classes)

    for record in records:
        if not record["image_exists"]:
            invalid_reasons["image_missing"] += 1
        if not record["json_exists"]:
            invalid_reasons["json_missing"] += 1
        if record["json_exists"] and not record["parse_success"]:
            invalid_reasons["parse_failed"] += 1

    class_names = sorted(class_image_counts.keys() | class_object_counts.keys())
    return {
        "total_images": sum(record["image_exists"] for record in valid_records),
        "by_inspection_type": dict(sorted(inspection_counts.items())),
        "by_material": dict(sorted(material_counts.items())),
        "by_class": {
            class_name: {
                "image_count": class_image_counts[class_name],
                "object_count": class_object_counts[class_name],
            }
            for class_name in class_names
        },
        "invalid_count": len(records) - len(valid_records),
        "invalid_reasons": invalid_reasons,
    }


# CSV와 JSON 인벤토리 파일을 metadata 디렉터리에 기록한다.
def write_inventory(records: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    METADATA_ROOT.mkdir(parents=True, exist_ok=True)
    csv_path = METADATA_ROOT / "raw_dataset_inventory.csv"
    json_path = METADATA_ROOT / "raw_dataset_inventory.json"

    with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELD_NAMES)
        writer.writeheader()
        writer.writerows(records)

    with json_path.open("w", encoding="utf-8") as json_file:
        json.dump(
            {"summary": summary, "records": records},
            json_file,
            ensure_ascii=False,
            indent=2,
        )


# 데이터 인벤토리 전체 생성 절차를 실행한다.
def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    records = build_records()
    summary = build_summary(records)
    write_inventory(records, summary)
    LOGGER.info("Inventory created with %d records", len(records))
    return 0


if __name__ == "__main__":
    sys.exit(main())
