import json
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = {"info", "image_data", "meta", "annotations"}
ANNOTATION_FIELDS = {"tool", "coordinate", "class", "case"}


# Read and validate the required structure of one label JSON file.
def validate_json(
    json_path: str | Path,
) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    path = Path(json_path) if json_path else None
    if path is None or not path.is_file():
        return None, [{"severity": "ERROR", "code": "json_missing"}]

    try:
        with path.open("r", encoding="utf-8") as json_file:
            label_data = json.load(json_file)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, [{"severity": "ERROR", "code": "json_parse_failed"}]

    if not isinstance(label_data, dict):
        return None, [{"severity": "ERROR", "code": "missing_required_fields"}]

    issues = []
    if not REQUIRED_FIELDS.issubset(label_data):
        issues.append({"severity": "ERROR", "code": "missing_required_fields"})
        return label_data, issues

    annotations = label_data["annotations"]
    if not isinstance(annotations, list):
        issues.append({"severity": "ERROR", "code": "invalid_annotation_structure"})
        return label_data, issues

    invalid_structure = False
    for annotation in annotations:
        if not isinstance(annotation, dict) or not ANNOTATION_FIELDS.issubset(
            annotation
        ):
            invalid_structure = True
            continue

        if annotation["class"] == "defect" and annotation["case"] == "":
            issues.append({"severity": "ERROR", "code": "missing_class_info"})

        coordinate = annotation["coordinate"]
        if (
            not isinstance(coordinate, dict)
            or "x" not in coordinate
            or "y" not in coordinate
        ):
            invalid_structure = True
            continue

    if invalid_structure:
        issues.append({"severity": "ERROR", "code": "invalid_annotation_structure"})

    return label_data, issues
