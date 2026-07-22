import csv
import hashlib
import json
import logging
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from validation.validate_image import validate_image  # noqa: E402
from validation.validate_json import validate_json  # noqa: E402
from validation.validate_polygon import (  # noqa: E402
    validate_duplicate_annotations,
    validate_polygon,
)

LOGGER = logging.getLogger(__name__)
INVENTORY_PATH = PROJECT_ROOT / "metadata" / "raw_dataset_inventory.json"
REPORT_ROOT = PROJECT_ROOT / "reports" / "data-quality"
REPORT_FIELDS = (
    "image_name",
    "image_path",
    "json_path",
    "error_codes",
    "warning_codes",
    "info_codes",
    "error_count",
    "warning_count",
    "info_count",
    "include",
)
ISSUE_CODES = (
    "image_missing",
    "json_missing",
    "image_corrupted",
    "invalid_image_dimensions",
    "json_parse_failed",
    "missing_required_fields",
    "invalid_annotation_structure",
    "missing_class_info",
    "coordinate_count_mismatch",
    "insufficient_points",
    "empty_polygon",
    "non_numeric_coordinate",
    "dimension_mismatch",
    "negative_coordinate",
    "out_of_bounds_coordinate",
    "duplicate_filename",
    "duplicate_image",
    "duplicate_annotation",
    "possible_self_intersection",
)


# Resolve an inventory path relative to the project root.
def _resolve_path(path_value: Any) -> Path | str:
    if not path_value:
        return ""
    path = Path(path_value)
    return path if path.is_absolute() else PROJECT_ROOT / path


# Confirm that polygon validation is safe for one annotation.
def _has_valid_annotation_structure(annotation: Any) -> bool:
    if not isinstance(annotation, dict):
        return False
    if not {"tool", "coordinate", "class", "case"}.issubset(annotation):
        return False
    coordinate = annotation["coordinate"]
    return isinstance(coordinate, dict) and "x" in coordinate and "y" in coordinate


# Validate every inventory record without rescanning the raw dataset.
def _validate_records(
    inventory_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results = []
    for inventory_record in inventory_records:
        image_path = _resolve_path(inventory_record.get("image_path"))
        json_path = _resolve_path(inventory_record.get("json_path"))
        label_data, issues = validate_json(json_path)

        expected_width = None
        expected_height = None
        if label_data is not None:
            image_data = label_data.get("image_data")
            if isinstance(image_data, dict):
                expected_width = image_data.get("width")
                expected_height = image_data.get("height")

        issues.extend(validate_image(image_path, expected_width, expected_height))

        required_fields = {"info", "image_data", "meta", "annotations"}
        if (
            label_data is not None
            and required_fields.issubset(label_data)
            and isinstance(label_data["annotations"], list)
        ):
            valid_annotations = [
                annotation
                for annotation in label_data["annotations"]
                if _has_valid_annotation_structure(annotation)
            ]
            for annotation in valid_annotations:
                issues.extend(
                    validate_polygon(
                        annotation["coordinate"],
                        expected_width,
                        expected_height,
                    )
                )
            issues.extend(validate_duplicate_annotations(valid_annotations))

        results.append(
            {
                "image_name": inventory_record.get("image_name", ""),
                "image_path": inventory_record.get("image_path", ""),
                "json_path": inventory_record.get("json_path", ""),
                "resolved_image_path": image_path,
                "issues": issues,
            }
        )
    return results


# Add duplicate filename and exact-image issues to all related records.
def _add_cross_record_issues(results: list[dict[str, Any]]) -> None:
    filename_groups = defaultdict(list)
    hash_groups = defaultdict(list)

    for index, result in enumerate(results):
        category_path = result["image_path"] or result["json_path"]
        category = Path(category_path).parent.name if category_path else ""
        filename_groups[result["image_name"]].append((index, category))

        image_path = result["resolved_image_path"]
        if isinstance(image_path, Path) and image_path.is_file():
            try:
                image_hasher = hashlib.sha256()
                with image_path.open("rb") as image_file:
                    for chunk in iter(lambda: image_file.read(1024 * 1024), b""):
                        image_hasher.update(chunk)
            except OSError:
                continue
            image_hash = image_hasher.hexdigest()
            hash_groups[image_hash].append(index)

    for grouped_records in filename_groups.values():
        categories = {category for _, category in grouped_records}
        if len(grouped_records) >= 2 and len(categories) >= 2:
            for index, _ in grouped_records:
                results[index]["issues"].append(
                    {"severity": "WARNING", "code": "duplicate_filename"}
                )

    for grouped_indexes in hash_groups.values():
        if len(grouped_indexes) >= 2:
            for index in grouped_indexes:
                results[index]["issues"].append(
                    {"severity": "WARNING", "code": "duplicate_image"}
                )


# Preserve issue order while removing repeated codes from CSV code columns.
def _unique_codes(issues: list[dict[str, str]], severity: str) -> str:
    return ";".join(
        dict.fromkeys(
            issue["code"] for issue in issues if issue["severity"] == severity
        )
    )


# Convert validation results into the final report row schema.
def _build_report_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for result in results:
        issues = result["issues"]
        counts = Counter(issue["severity"] for issue in issues)
        rows.append(
            {
                "image_name": result["image_name"],
                "image_path": result["image_path"],
                "json_path": result["json_path"],
                "error_codes": _unique_codes(issues, "ERROR"),
                "warning_codes": _unique_codes(issues, "WARNING"),
                "info_codes": _unique_codes(issues, "INFO"),
                "error_count": counts["ERROR"],
                "warning_count": counts["WARNING"],
                "info_count": counts["INFO"],
                "include": counts["ERROR"] == 0,
            }
        )
    return rows


# Write a CSV file with an explicit, stable column order.
def _write_csv(
    output_path: Path,
    field_names: tuple[str, ...],
    rows: list[dict[str, Any]],
) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()
        writer.writerows({field: row[field] for field in field_names} for row in rows)


# Generate the four requested data-quality CSV reports.
def _write_reports(rows: list[dict[str, Any]]) -> None:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    _write_csv(REPORT_ROOT / "data_quality_report.csv", REPORT_FIELDS, rows)

    error_rows = [row for row in rows if row["error_count"] > 0]
    _write_csv(
        REPORT_ROOT / "error_files.csv",
        ("image_name", "image_path", "json_path", "error_codes"),
        error_rows,
    )
    warning_rows = [
        row for row in rows if row["error_count"] == 0 and row["warning_count"] > 0
    ]
    _write_csv(
        REPORT_ROOT / "warning_files.csv",
        ("image_name", "image_path", "json_path", "warning_codes"),
        warning_rows,
    )
    excluded_rows = [
        {
            **row,
            "exclusion_reason": row["error_codes"],
        }
        for row in error_rows
    ]
    _write_csv(
        REPORT_ROOT / "excluded_files.csv",
        ("image_name", "image_path", "json_path", "exclusion_reason"),
        excluded_rows,
    )


# Log the occurrence count for every issue code.
def _log_issue_summary(results: list[dict[str, Any]]) -> None:
    issue_counts = Counter(
        issue["code"] for result in results for issue in result["issues"]
    )
    LOGGER.info("Validated %d records", len(results))
    for code in ISSUE_CODES:
        LOGGER.info("%s: %d", code, issue_counts[code])


# Run the complete inventory-based data quality validation workflow.
def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
    )
    if not INVENTORY_PATH.is_file():
        LOGGER.error(
            "Inventory not found. Run `python src/data/build_inventory.py` first."
        )
        return 1

    try:
        with INVENTORY_PATH.open("r", encoding="utf-8") as inventory_file:
            inventory = json.load(inventory_file)
        inventory_records = inventory["records"]
        if not isinstance(inventory_records, list):
            raise TypeError("records must be a list")
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        LOGGER.error("Failed to read inventory: %s", error)
        return 1

    results = _validate_records(inventory_records)
    _add_cross_record_issues(results)
    rows = _build_report_rows(results)
    _write_reports(rows)
    _log_issue_summary(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
