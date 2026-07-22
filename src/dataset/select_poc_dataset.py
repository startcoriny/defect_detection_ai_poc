import csv
import json
import logging
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METADATA_ROOT = PROJECT_ROOT / "metadata"
INVENTORY_PATH = METADATA_ROOT / "raw_dataset_inventory.csv"
CLASS_MAPPING_PATH = METADATA_ROOT / "class_mapping.json"
QUALITY_REPORT_PATH = (
    PROJECT_ROOT / "reports" / "data-quality" / "data_quality_report.csv"
)

LOGGER = logging.getLogger(__name__)
TARGET_COUNT = 100
RANDOM_SEED = 42
TARGET_CLASSES = {"porosity", "slag_inclusion"}
GROUP_NAMES = ("normal", "porosity", "slag_inclusion", "both")
FIELD_NAMES = (
    "image_name",
    "status",
    "classes",
    "object_count",
    "group",
    "selected",
    "exclusion_reason",
    "duplicate",
    "quality_status",
    "split_group",
)


# CSV의 True/False 문자열을 불리언 값으로 변환한다.
def parse_boolean(value: str) -> bool:
    return value.strip().lower() == "true"


# 세미콜론으로 구분된 코드 목록을 집합으로 변환한다.
def parse_codes(value: str) -> set[str]:
    return {code.strip() for code in value.split(";") if code.strip()}


# 원본 클래스 목록을 매핑 파일에 정의된 표준 클래스 집합으로 변환한다.
def map_classes(raw_classes: str, class_mapping: dict[str, str | None]) -> set[str]:
    standard_classes = set()
    for raw_class in parse_codes(raw_classes):
        if raw_class not in class_mapping:
            raise ValueError(f"Class mapping is missing for: {raw_class}")
        standard_class = class_mapping[raw_class]
        if standard_class is not None:
            standard_classes.add(standard_class)
    return standard_classes


# 클래스 매핑 JSON을 읽고 값 형식을 검증한다.
def load_class_mapping() -> dict[str, str | None]:
    with CLASS_MAPPING_PATH.open(encoding="utf-8") as mapping_file:
        class_mapping = json.load(mapping_file)

    if not isinstance(class_mapping, dict) or not all(
        isinstance(key, str) and (value is None or isinstance(value, str))
        for key, value in class_mapping.items()
    ):
        raise ValueError("class_mapping.json must contain a string-to-string mapping")
    return class_mapping


# 품질검사 결과를 이미지 이름 기준으로 읽는다.
def load_quality_results() -> dict[str, dict[str, str]]:
    quality_results = {}
    with QUALITY_REPORT_PATH.open(encoding="utf-8-sig", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            image_name = row["image_name"]
            if image_name in quality_results:
                raise ValueError(f"Duplicate quality report row: {image_name}")
            quality_results[image_name] = row
    return quality_results


# RT·AL 인벤토리 레코드만 읽어 선별 후보를 구성한다.
def build_candidates() -> list[dict[str, Any]]:
    class_mapping = load_class_mapping()
    quality_results = load_quality_results()
    candidates = []

    with INVENTORY_PATH.open(encoding="utf-8-sig", newline="") as csv_file:
        for inventory_row in csv.DictReader(csv_file):
            if (
                inventory_row["inspection_type"] != "RT"
                or inventory_row["material"] != "AL"
            ):
                continue

            image_name = inventory_row["image_name"]
            quality_row = quality_results.get(image_name, {})
            include = parse_boolean(quality_row.get("include", ""))
            warning_codes = parse_codes(quality_row.get("warning_codes", ""))
            duplicate = bool({"duplicate_filename", "duplicate_image"} & warning_codes)
            standard_classes = map_classes(inventory_row["classes"], class_mapping)
            candidate = {
                "image_name": image_name,
                "status": inventory_row["status"],
                "classes": ";".join(sorted(standard_classes)),
                "object_count": inventory_row["num_annotations"],
                "group": "excluded",
                "selected": False,
                "exclusion_reason": "",
                "duplicate": duplicate,
                "quality_status": "pass" if include else "fail",
                "split_group": "",
                "_standard_classes": standard_classes,
            }
            classify_candidate(
                candidate,
                valid=parse_boolean(inventory_row["valid"]),
                include=include,
            )
            candidates.append(candidate)

    return candidates


# 우선순위 규칙에 따라 후보의 그룹 또는 단일 제외 사유를 정한다.
def classify_candidate(
    candidate: dict[str, Any], *, valid: bool, include: bool
) -> None:
    classes = candidate["_standard_classes"]
    if not valid:
        candidate["exclusion_reason"] = "image_or_json_missing"
    elif not include:
        candidate["exclusion_reason"] = "quality_check_failed"
    elif candidate["duplicate"]:
        candidate["exclusion_reason"] = "duplicate"
    elif not classes.issubset(TARGET_CLASSES) and classes & TARGET_CLASSES:
        candidate["exclusion_reason"] = "off_target_class_present"
    elif candidate["status"] == "normal":
        candidate["group"] = "normal"
    elif classes == {"porosity"}:
        candidate["group"] = "porosity"
    elif classes == {"slag_inclusion"}:
        candidate["group"] = "slag_inclusion"
    elif classes == TARGET_CLASSES:
        candidate["group"] = "both"
    else:
        candidate["exclusion_reason"] = "non_target_class"


# 고정 시드로 그룹별 목표 수량을 표본 추출하고 복수 클래스는 항상 포함한다.
def select_samples(candidates: list[dict[str, Any]]) -> None:
    grouped = {
        group_name: sorted(
            (
                candidate
                for candidate in candidates
                if candidate["group"] == group_name
                and not candidate["exclusion_reason"]
            ),
            key=lambda candidate: candidate["image_name"],
        )
        for group_name in GROUP_NAMES
    }

    for candidate in grouped["both"]:
        candidate["selected"] = True

    random_generator = random.Random(RANDOM_SEED)
    sample_sizes = {
        "normal": min(TARGET_COUNT, len(grouped["normal"])),
        "porosity": min(
            max(TARGET_COUNT - 1, 0),
            len(grouped["porosity"]),
        ),
        "slag_inclusion": min(
            max(TARGET_COUNT - 1, 0),
            len(grouped["slag_inclusion"]),
        ),
    }
    for group_name, sample_size in sample_sizes.items():
        for candidate in random_generator.sample(grouped[group_name], sample_size):
            candidate["selected"] = True

    for candidate in candidates:
        if candidate["group"] != "excluded" and not candidate["selected"]:
            candidate["exclusion_reason"] = "quota_not_selected"


# 선정 CSV와 포함·제외 파일 목록을 metadata 디렉터리에 기록한다.
def write_results(candidates: list[dict[str, Any]]) -> None:
    METADATA_ROOT.mkdir(parents=True, exist_ok=True)
    with (METADATA_ROOT / "selected_dataset.csv").open(
        "w", encoding="utf-8", newline=""
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELD_NAMES)
        writer.writeheader()
        writer.writerows(
            {field_name: candidate[field_name] for field_name in FIELD_NAMES}
            for candidate in candidates
        )

    selected_names = sorted(
        candidate["image_name"] for candidate in candidates if candidate["selected"]
    )
    with (METADATA_ROOT / "included_files.txt").open(
        "w", encoding="utf-8", newline=""
    ) as included_file:
        for image_name in selected_names:
            included_file.write(f"{image_name}\n")

    excluded_rows = sorted(
        (
            candidate["image_name"],
            candidate["exclusion_reason"],
        )
        for candidate in candidates
        if not candidate["selected"]
    )
    with (METADATA_ROOT / "excluded_files.txt").open(
        "w", encoding="utf-8", newline=""
    ) as excluded_file:
        for image_name, exclusion_reason in excluded_rows:
            excluded_file.write(f"{image_name},{exclusion_reason}\n")


# 후보·그룹·목표 차이·제외 사유·선정 객체 수를 요약해 기록한다.
def log_summary(candidates: list[dict[str, Any]]) -> None:
    LOGGER.info("RT+AL candidates: %d", len(candidates))
    for group_name in GROUP_NAMES:
        group_candidates = [
            candidate for candidate in candidates if candidate["group"] == group_name
        ]
        selected_candidates = [
            candidate for candidate in group_candidates if candidate["selected"]
        ]
        object_count = sum(
            int(candidate["object_count"]) for candidate in selected_candidates
        )
        LOGGER.info(
            "Group %s: total=%d, selected=%d, selected_object_count=%d",
            group_name,
            len(group_candidates),
            len(selected_candidates),
            object_count,
        )

    for class_name in ("normal", "porosity", "slag_inclusion"):
        actual_count = sum(
            candidate["selected"]
            and (
                candidate["group"] == "normal"
                if class_name == "normal"
                else class_name in candidate["_standard_classes"]
            )
            for candidate in candidates
        )
        LOGGER.info(
            "Target %s: planned=%d, actual=%d, difference=%+d",
            class_name,
            TARGET_COUNT,
            actual_count,
            actual_count - TARGET_COUNT,
        )

    exclusion_counts = Counter(
        candidate["exclusion_reason"]
        for candidate in candidates
        if candidate["exclusion_reason"]
    )
    for exclusion_reason, count in sorted(exclusion_counts.items()):
        LOGGER.info("Exclusion %s: %d", exclusion_reason, count)


# 1차 PoC 데이터 선별 전체 절차를 실행한다.
def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
    )
    candidates = build_candidates()
    select_samples(candidates)
    write_results(candidates)
    log_summary(candidates)
    return 0


if __name__ == "__main__":
    sys.exit(main())
