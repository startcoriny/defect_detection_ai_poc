import csv
import json
import logging
import random
import sys
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
INVENTORY_PATH = PROJECT_ROOT / "metadata" / "raw_dataset_inventory.csv"
CLASS_MAPPING_PATH = PROJECT_ROOT / "metadata" / "class_mapping.json"
WARNING_FILES_PATH = PROJECT_ROOT / "reports" / "data-quality" / "warning_files.csv"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "original-polygon"
SAMPLE_SIZE = 50
RANDOM_SEED = 42
OVERLAY_ALPHA = 0.3
COORDINATE_FIELDS = ("image_name", "annotation_index", "issue")
ERROR_FIELDS = ("image_name", "reason")
FORCED_WARNING_CODES = {"out_of_bounds_coordinate", "negative_coordinate"}
COLORS = (
    (0, 255, 255),
    (255, 128, 0),
    (0, 200, 0),
    (255, 0, 255),
    (0, 128, 255),
    (255, 0, 0),
)


# CSV의 문자열 불리언 값을 판별합니다.
def is_true(value: str) -> bool:
    return value.strip().lower() == "true"


# 원본 인벤토리에서 시각화 가능한 레코드만 읽습니다.
def load_valid_records() -> list[dict[str, str]]:
    with INVENTORY_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        return [
            row for row in csv.DictReader(csv_file) if is_true(row.get("valid", ""))
        ]


# 클래스 매핑 파일을 읽고 표준 결함 클래스 목록을 반환합니다.
def load_class_mapping() -> dict[str, str | None]:
    mapping = load_json(CLASS_MAPPING_PATH)
    if not isinstance(mapping, dict):
        raise ValueError("class_mapping.json root must be an object")
    return mapping


# 인벤토리의 원본 클래스 목록을 표준 클래스 집합으로 변환합니다.
def get_standard_classes(
    record: dict[str, str], class_mapping: dict[str, str | None]
) -> set[str]:
    raw_classes = (name for name in record.get("classes", "").split(";") if name)
    return {
        standard_class
        for raw_class in raw_classes
        if (standard_class := class_mapping.get(raw_class)) is not None
    }


# 데이터 품질 경고 중 경계 초과 좌표가 있는 이미지명을 읽습니다.
def load_forced_warning_names() -> set[str]:
    names = set()
    with WARNING_FILES_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            warning_codes = {
                code.strip()
                for code in row.get("warning_codes", "").split(";")
                if code.strip()
            }
            if warning_codes & FORCED_WARNING_CODES:
                names.add(row["image_name"])
    return names


# 고정 시드로 클래스별 표본을 뽑고 필수 사례를 추가합니다.
def select_samples(
    records: list[dict[str, str]], class_mapping: dict[str, str | None]
) -> list[dict[str, str]]:
    rng = random.Random(RANDOM_SEED)
    selected: dict[str, dict[str, str]] = {}

    groups: list[tuple[str, list[dict[str, str]]]] = [
        ("normal", [record for record in records if record["status"] == "normal"])
    ]
    standard_classes = sorted(
        standard_class
        for standard_class in class_mapping.values()
        if standard_class is not None
    )
    for standard_class in standard_classes:
        eligible = [
            record
            for record in records
            if standard_class in get_standard_classes(record, class_mapping)
        ]
        groups.append((standard_class, eligible))

    for group_name, eligible in groups:
        sample_count = min(SAMPLE_SIZE, len(eligible))
        sorted_eligible = sorted(eligible, key=lambda row: row["image_name"])
        sampled = rng.sample(sorted_eligible, sample_count)
        for record in sampled:
            selected[record["image_name"]] = record
        LOGGER.info(
            "Sample group %s: selected=%d, eligible=%d",
            group_name,
            sample_count,
            len(eligible),
        )

    most_annotated = max(records, key=lambda row: int(row["num_annotations"]))
    was_added = most_annotated["image_name"] not in selected
    selected[most_annotated["image_name"]] = most_annotated
    LOGGER.info(
        "Forced maximum-annotation sample: candidates=1, added=%d (%s, annotations=%s)",
        int(was_added),
        most_annotated["image_name"],
        most_annotated["num_annotations"],
    )

    records_by_name = {record["image_name"]: record for record in records}
    warning_names = load_forced_warning_names()
    warning_added = 0
    for image_name in sorted(warning_names):
        record = records_by_name.get(image_name)
        if record is None:
            LOGGER.warning(
                "Forced warning sample is not a valid record: %s", image_name
            )
            continue
        warning_added += image_name not in selected
        selected[image_name] = record
    LOGGER.info(
        "Forced boundary-warning samples: candidates=%d, added=%d",
        len(warning_names),
        warning_added,
    )

    samples = sorted(selected.values(), key=lambda row: row["image_name"])
    LOGGER.info("Final samples after deduplication: %d", len(samples))
    for record in samples:
        LOGGER.info("Selected image: %s", record["image_name"])
    return samples


# 좌표 배열을 검사하고 그릴 수 있는 OpenCV 점 배열로 변환합니다.
def prepare_points(
    annotation: dict[str, Any],
    image_name: str,
    annotation_index: int,
    width: int,
    height: int,
    coordinate_issues: list[dict[str, Any]],
) -> np.ndarray | None:
    coordinate = annotation["coordinate"]
    x_values = coordinate["x"]
    y_values = coordinate["y"]
    if len(x_values) != len(y_values):
        issue = "coordinate_count_mismatch"
        LOGGER.warning("%s annotation %d: %s", image_name, annotation_index, issue)
        coordinate_issues.append(
            {
                "image_name": image_name,
                "annotation_index": annotation_index,
                "issue": issue,
            }
        )
        return None

    points = np.column_stack((x_values, y_values))
    is_out_of_bounds = (
        np.any(points[:, 0] < 0)
        or np.any(points[:, 0] > width)
        or np.any(points[:, 1] < 0)
        or np.any(points[:, 1] > height)
    )
    if is_out_of_bounds:
        issue = "out_of_bounds_coordinate"
        LOGGER.warning("%s annotation %d: %s", image_name, annotation_index, issue)
        coordinate_issues.append(
            {
                "image_name": image_name,
                "annotation_index": annotation_index,
                "issue": issue,
            }
        )

    return np.rint(points).astype(np.int32).reshape((-1, 1, 2))


# 한 이미지의 결함 Polygon과 식별 정보를 그립니다.
def draw_visualization(
    image: np.ndarray,
    label_data: dict[str, Any],
    image_name: str,
    class_mapping: dict[str, str | None],
    coordinate_issues: list[dict[str, Any]],
) -> np.ndarray:
    image_data = label_data["image_data"]
    width = int(image_data["width"])
    height = int(image_data["height"])
    annotations = label_data["annotations"]
    overlay = image.copy()
    drawable: list[tuple[np.ndarray, tuple[int, int, int], str]] = []

    for annotation_index, annotation in enumerate(annotations):
        raw_class = annotation["case"]
        if raw_class == "":
            continue
        standard_class = class_mapping.get(raw_class, raw_class)
        points = prepare_points(
            annotation,
            image_name,
            annotation_index,
            width,
            height,
            coordinate_issues,
        )
        if points is None:
            continue
        color = COLORS[annotation_index % len(COLORS)]
        cv2.fillPoly(overlay, [points], color)
        drawable.append((points, color, f"{standard_class} #{annotation_index}"))

    result = cv2.addWeighted(overlay, OVERLAY_ALPHA, image, 1 - OVERLAY_ALPHA, 0)
    for points, color, label in drawable:
        cv2.polylines(result, [points], True, color, 2, cv2.LINE_AA)
        first_x, first_y = points[0, 0]
        cv2.putText(
            result,
            label,
            (max(0, int(first_x)), max(20, int(first_y))),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
            cv2.LINE_AA,
        )

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


# Unicode 경로에서도 동작하도록 JPEG 인코딩 후 바이트로 저장합니다.
def save_image(image: np.ndarray, output_path: Path) -> None:
    success, encoded = cv2.imencode(".jpg", image)
    if not success:
        raise OSError("JPEG encoding failed")
    output_path.write_bytes(encoded.tobytes())


# 표본 이미지를 시각화하고 좌표 및 파일 오류 목록을 반환합니다.
def visualize_samples(
    samples: list[dict[str, str]], class_mapping: dict[str, str | None]
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    coordinate_issues: list[dict[str, Any]] = []
    error_files: list[dict[str, str]] = []

    for record in samples:
        image_name = record["image_name"]
        image = read_image(PROJECT_ROOT / record["image_path"])
        if image is None:
            reason = "image_read_failed"
            LOGGER.error("%s: %s", image_name, reason)
            error_files.append({"image_name": image_name, "reason": reason})
            continue

        try:
            label_data = load_json(PROJECT_ROOT / record["json_path"])
            if not isinstance(label_data, dict):
                raise TypeError("JSON root must be an object")
            result = draw_visualization(
                image,
                label_data,
                image_name,
                class_mapping,
                coordinate_issues,
            )
            save_image(result, OUTPUT_ROOT / f"{image_name}.jpg")
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
            cv2.error,
        ) as error:
            reason = f"{type(error).__name__}: {error}"
            LOGGER.error("Visualization skipped for %s (%s)", image_name, reason)
            error_files.append({"image_name": image_name, "reason": reason})

    return coordinate_issues, error_files


# 검사 결과 CSV를 헤더와 함께 저장합니다.
def write_csv(
    path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, Any]]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# 원본 Polygon 표본 선정과 시각화를 실행합니다.
def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
    )
    try:
        records = load_valid_records()
        class_mapping = load_class_mapping()
        samples = select_samples(records, class_mapping)
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, ValueError) as error:
        LOGGER.error("Failed to prepare visualization samples (%s)", error)
        return 1

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    coordinate_issues, error_files = visualize_samples(samples, class_mapping)
    write_csv(
        OUTPUT_ROOT / "coordinate_check.csv", COORDINATE_FIELDS, coordinate_issues
    )
    write_csv(OUTPUT_ROOT / "error_files.csv", ERROR_FIELDS, error_files)
    LOGGER.info(
        "Visualization complete: samples=%d, images=%d, "
        "coordinate_issues=%d, errors=%d",
        len(samples),
        len(samples) - len(error_files),
        len(coordinate_issues),
        len(error_files),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
