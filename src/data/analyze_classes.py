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
LABEL_ROOT = (
    PROJECT_ROOT / "data" / "raw" / "steel" / "02.\ub77c\ubca8\ub9c1\ub370\uc774\ud130"
)
METADATA_ROOT = PROJECT_ROOT / "metadata"
CATEGORIES = ("1. RTAL", "2. RTST", "3. VTST")
ORIGINAL_FIELD_NAMES = (
    "raw_class",
    "image_count",
    "object_count",
    "rt_image_count",
    "vt_image_count",
)
STATISTICS_FIELD_NAMES = (
    "class_id",
    "class_name",
    "image_count",
    "object_count",
    "rt_image_count",
    "vt_image_count",
)


# Collect raw class statistics by scanning every source annotation JSON file.
def analyze_original_classes() -> list[dict[str, Any]]:
    image_counts: Counter[str] = Counter()
    object_counts: Counter[str] = Counter()
    rt_image_counts: Counter[str] = Counter()
    vt_image_counts: Counter[str] = Counter()

    for category in CATEGORIES:
        json_directory = LABEL_ROOT / category
        for stem in get_sorted_file_stems(json_directory, ".json"):
            json_path = json_directory / f"{stem}.json"
            try:
                inspection_type, raw_classes = extract_classes(load_json(json_path))
            except (
                OSError,
                UnicodeError,
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ) as error:
                LOGGER.error("JSON parse failed: %s (%s)", json_path, error)
                continue

            classes_in_image = set(raw_classes)
            object_counts.update(raw_classes)
            image_counts.update(classes_in_image)
            if inspection_type == "RT":
                rt_image_counts.update(classes_in_image)
            elif inspection_type == "VT":
                vt_image_counts.update(classes_in_image)

    return [
        {
            "raw_class": raw_class,
            "image_count": image_counts[raw_class],
            "object_count": object_counts[raw_class],
            "rt_image_count": rt_image_counts[raw_class],
            "vt_image_count": vt_image_counts[raw_class],
        }
        for raw_class in sorted(image_counts.keys() | object_counts.keys())
    ]


# Validate one label document and return its inspection type and non-empty cases.
def extract_classes(label_data: Any) -> tuple[str, list[str]]:
    if not isinstance(label_data, dict):
        raise ValueError("JSON root must be an object")

    info = label_data["info"]
    annotations = label_data["annotations"]
    if not isinstance(info, dict):
        raise TypeError("info must be an object")
    if not isinstance(annotations, list):
        raise TypeError("annotations must be a list")

    inspection_type = info["type"]
    if not isinstance(inspection_type, str):
        raise TypeError("info.type must be a string")

    raw_classes = []
    for annotation in annotations:
        if not isinstance(annotation, dict):
            raise TypeError("each annotation must be an object")
        raw_class = annotation["case"]
        if not isinstance(raw_class, str):
            raise TypeError("annotations[].case must be a string")
        if raw_class:
            raw_classes.append(raw_class)

    return inspection_type, raw_classes


# Convert a raw class spelling to the project-standard class name.
def normalize_class_name(raw_class: str) -> str:
    return raw_class.lower().replace(" ", "_")


# Map every discovered raw spelling while marking normal as non-detectable.
def build_class_mapping(
    original_statistics: list[dict[str, Any]],
) -> dict[str, str | None]:
    mapping = {
        row["raw_class"]: normalize_class_name(row["raw_class"])
        for row in original_statistics
    }
    mapping["normal"] = None
    return mapping


# Sum raw-class statistics for raw spellings mapped to the same standard class.
def build_class_statistics(
    original_statistics: list[dict[str, Any]],
    class_mapping: dict[str, str | None],
) -> list[dict[str, Any]]:
    grouped: dict[str, Counter[str]] = {}
    for row in original_statistics:
        class_name = class_mapping[row["raw_class"]]
        if class_name is None:
            continue
        totals = grouped.setdefault(class_name, Counter())
        for field_name in ORIGINAL_FIELD_NAMES[1:]:
            totals[field_name] += row[field_name]

    # Alphabetical class-name order fixes IDs for every downstream YOLO task.
    return [
        {
            "class_id": class_id,
            "class_name": class_name,
            **{
                field_name: grouped[class_name][field_name]
                for field_name in ORIGINAL_FIELD_NAMES[1:]
            },
        }
        for class_id, class_name in enumerate(sorted(grouped))
    ]


# Write the three deterministic class-analysis deliverables.
def write_results(
    original_statistics: list[dict[str, Any]],
    class_mapping: dict[str, str | None],
    class_statistics: list[dict[str, Any]],
) -> None:
    METADATA_ROOT.mkdir(parents=True, exist_ok=True)

    with (METADATA_ROOT / "original_class_list.csv").open(
        "w", encoding="utf-8", newline=""
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=ORIGINAL_FIELD_NAMES)
        writer.writeheader()
        writer.writerows(original_statistics)

    with (METADATA_ROOT / "class_mapping.json").open(
        "w", encoding="utf-8"
    ) as json_file:
        json.dump(class_mapping, json_file, ensure_ascii=False, indent=2)
        json_file.write("\n")

    with (METADATA_ROOT / "class_statistics.csv").open(
        "w", encoding="utf-8", newline=""
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=STATISTICS_FIELD_NAMES)
        writer.writeheader()
        writer.writerows(class_statistics)


# Log class volumes and whether each class occurs in both inspection types.
def log_summary(
    original_statistics: list[dict[str, Any]],
    class_statistics: list[dict[str, Any]],
) -> None:
    LOGGER.info("Discovered raw classes: %d", len(original_statistics))
    LOGGER.info("Standard classes: %d", len(class_statistics))
    for row in class_statistics:
        occurrence = (
            "RT and VT"
            if row["rt_image_count"] > 0 and row["vt_image_count"] > 0
            else "one inspection type only"
        )
        LOGGER.info(
            "%d: %s - image_count=%d, object_count=%d, "
            "rt_image_count=%d, vt_image_count=%d (%s)",
            row["class_id"],
            row["class_name"],
            row["image_count"],
            row["object_count"],
            row["rt_image_count"],
            row["vt_image_count"],
            occurrence,
        )


# Run the complete class-analysis workflow.
def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
    )
    original_statistics = analyze_original_classes()
    class_mapping = build_class_mapping(original_statistics)
    class_statistics = build_class_statistics(original_statistics, class_mapping)
    write_results(original_statistics, class_mapping, class_statistics)
    log_summary(original_statistics, class_statistics)
    return 0


if __name__ == "__main__":
    sys.exit(main())
