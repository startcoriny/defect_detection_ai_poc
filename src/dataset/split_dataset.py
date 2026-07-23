"""선별 데이터셋을 그룹과 객체 크기로 층화해 세 분할로 나눕니다."""

import csv
import logging
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METADATA_ROOT = PROJECT_ROOT / "metadata"
SPLIT_ROOT = PROJECT_ROOT / "splits"
REPORT_ROOT = PROJECT_ROOT / "reports" / "dataset"
LOGGER = logging.getLogger(__name__)

SEED = 42
SPLITS = ("train", "val", "test")
TARGET_RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}
EXPECTED_STRATUM_COUNTS = {
    "both_mixed": 1,
    "normal": 100,
    "porosity_mixed": 22,
    "porosity_small_dominant": 77,
    "slag_inclusion_mixed": 69,
    "slag_inclusion_small_dominant": 30,
}
DISTRIBUTION_FIELDS = (
    "split",
    "class_id",
    "class_name",
    "image_count",
    "object_count",
)


# CSV 파일을 원본 필드 순서와 함께 읽습니다.
def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError(f"CSV 헤더가 없습니다: {path}")
        return reader.fieldnames, list(reader)


# 선별 행과 분할에 필요한 필드의 유효성을 검사합니다.
def load_selected_rows(
    rows: list[dict[str, str]], field_names: list[str]
) -> list[dict[str, str]]:
    required = {"image_name", "selected", "group", "duplicate", "split_group"}
    missing_fields = required - set(field_names)
    if missing_fields:
        raise ValueError(
            "selected_dataset.csv에 필수 컬럼이 없습니다: "
            + ", ".join(sorted(missing_fields))
        )

    selected_rows = [row for row in rows if row["selected"] == "True"]
    image_names = [row["image_name"] for row in selected_rows]
    if len(image_names) != len(set(image_names)):
        raise ValueError("선택 데이터에 동일한 image_name이 두 번 이상 있습니다.")

    duplicate_names = [
        row["image_name"] for row in selected_rows if row["duplicate"] == "True"
    ]
    if duplicate_names:
        raise ValueError(
            "선택 데이터에 중복 이미지가 있습니다: "
            + ", ".join(sorted(duplicate_names))
        )

    valid_groups = {"normal", "porosity", "slag_inclusion", "both"}
    invalid_groups = sorted({row["group"] for row in selected_rows} - valid_groups)
    if invalid_groups:
        raise ValueError("알 수 없는 group 값이 있습니다: " + ", ".join(invalid_groups))
    return selected_rows


# 표준 클래스 6개를 ID 순서로 읽고 유효성을 검사합니다.
def load_standard_classes() -> list[dict[str, Any]]:
    field_names, rows = read_csv(METADATA_ROOT / "class_statistics.csv")
    if not {"class_id", "class_name"} <= set(field_names):
        raise ValueError("class_statistics.csv에 필수 클래스 컬럼이 없습니다.")

    classes = [
        {"class_id": int(row["class_id"]), "class_name": row["class_name"]}
        for row in rows
    ]
    classes.sort(key=lambda row: row["class_id"])
    if [row["class_id"] for row in classes] != list(range(6)):
        raise ValueError("표준 클래스 ID는 0부터 5까지 모두 존재해야 합니다.")
    return classes


# 선택 이미지의 객체와 작업12 기준 상대 면적을 읽습니다.
def load_annotations(
    selected_names: set[str], standard_classes: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    standard_by_id = {row["class_id"]: row["class_name"] for row in standard_classes}
    _, rows = read_csv(METADATA_ROOT / "bbox_annotations.csv")
    annotations = []
    for row in rows:
        image_name = row["image_name"]
        if image_name not in selected_names:
            continue

        class_id = int(row["class_id"])
        if standard_by_id.get(class_id) != row["class_name"]:
            raise ValueError(
                f"표준 클래스와 annotation 클래스가 일치하지 않습니다: {class_id}"
            )
        box_width = float(row["box_width"])
        box_height = float(row["box_height"])
        image_width = float(row["image_width"])
        image_height = float(row["image_height"])
        if min(box_width, box_height, image_width, image_height) <= 0:
            raise ValueError(f"객체 또는 이미지 치수가 올바르지 않습니다: {image_name}")
        annotations.append(
            {
                "image_name": image_name,
                "class_id": class_id,
                "class_name": row["class_name"],
                "relative_area": (box_width / image_width)
                * (box_height / image_height),
            }
        )
    return annotations


# 이미지별 객체 중 절반 이상이 작은 객체인지에 따라 크기 특성을 계산합니다.
def build_size_classes(
    selected_rows: list[dict[str, str]], annotations: list[dict[str, Any]]
) -> dict[str, str]:
    object_counts = Counter(row["image_name"] for row in annotations)
    small_counts = Counter(
        row["image_name"] for row in annotations if row["relative_area"] < 0.01
    )
    size_classes = {}
    for row in selected_rows:
        image_name = row["image_name"]
        object_count = object_counts[image_name]
        if row["group"] == "normal":
            if object_count:
                raise ValueError(f"정상 이미지에 객체가 있습니다: {image_name}")
            continue
        if not object_count:
            raise ValueError(f"불량 이미지에 객체가 없습니다: {image_name}")
        size_classes[image_name] = (
            "small_dominant"
            if small_counts[image_name] * 2 >= object_count
            else "mixed"
        )
    return size_classes


# 그룹과 크기 특성을 결합한 문자열 층화 키를 반환합니다.
def build_stratum_key(row: dict[str, str], size_classes: dict[str, str]) -> str:
    if row["group"] == "normal":
        return "normal"
    return f"{row['group']}_{size_classes[row['image_name']]}"


# 알파벳순 층화 키와 하나의 난수 생성기로 분할을 생성합니다.
def build_split_assignments(
    selected_rows: list[dict[str, str]], size_classes: dict[str, str]
) -> tuple[dict[str, str], dict[str, str]]:
    grouped_names: dict[str, list[str]] = defaultdict(list)
    image_strata = {}
    for row in selected_rows:
        stratum = build_stratum_key(row, size_classes)
        image_strata[row["image_name"]] = stratum
        grouped_names[stratum].append(row["image_name"])

    actual_counts = {key: len(names) for key, names in sorted(grouped_names.items())}
    if actual_counts != EXPECTED_STRATUM_COUNTS:
        raise ValueError(
            "층화 키별 이미지 수가 예상값과 다릅니다: "
            f"expected={EXPECTED_STRATUM_COUNTS}, actual={actual_counts}"
        )

    rng = random.Random(SEED)
    assignments = {}
    for stratum in sorted(grouped_names):
        image_names = sorted(grouped_names[stratum])
        rng.shuffle(image_names)
        n_train = round(len(image_names) * TARGET_RATIOS["train"])
        n_val = round(len(image_names) * TARGET_RATIOS["val"])
        n_test = len(image_names) - n_train - n_val
        boundaries = (n_train, n_train + n_val)
        for image_name in image_names[: boundaries[0]]:
            assignments[image_name] = "train"
        for image_name in image_names[boundaries[0] : boundaries[1]]:
            assignments[image_name] = "val"
        for image_name in image_names[boundaries[1] : boundaries[1] + n_test]:
            assignments[image_name] = "test"
    return assignments, image_strata


# 분할 간 교집합과 필수 이미지 포함 여부를 검증합니다.
def validate_assignments(
    selected_rows: list[dict[str, str]],
    assignments: dict[str, str],
    annotations: list[dict[str, Any]],
) -> tuple[dict[str, set[str]], dict[tuple[str, str], int]]:
    if len(assignments) != len(selected_rows):
        raise ValueError("일부 선택 이미지에 분할이 배정되지 않았습니다.")

    split_names = {
        split: {name for name, value in assignments.items() if value == split}
        for split in SPLITS
    }
    for index, left in enumerate(SPLITS):
        for right in SPLITS[index + 1 :]:
            if split_names[left] & split_names[right]:
                raise ValueError(f"{left}과 {right} 분할에 동일 이미지가 있습니다.")

    required_counts: Counter[tuple[str, str]] = Counter(
        (assignments[row["image_name"]], row["group"])
        for row in selected_rows
        if row["group"] == "normal"
    )
    class_images: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in annotations:
        if row["class_name"] in {"porosity", "slag_inclusion"}:
            key = (assignments[row["image_name"]], row["class_name"])
            class_images[key].add(row["image_name"])
    for key, image_names in class_images.items():
        required_counts[key] = len(image_names)

    for split in SPLITS:
        for category in ("normal", "porosity", "slag_inclusion"):
            if required_counts[(split, category)] == 0:
                raise ValueError(f"{split} 분할에 {category} 이미지가 없습니다.")
    return split_names, dict(required_counts)


# 분할별 표준 클래스의 이미지 수와 객체 수를 집계합니다.
def build_distribution(
    assignments: dict[str, str],
    annotations: list[dict[str, Any]],
    standard_classes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    image_names: dict[tuple[str, int], set[str]] = defaultdict(set)
    object_counts: Counter[tuple[str, int]] = Counter()
    for row in annotations:
        key = (assignments[row["image_name"]], row["class_id"])
        image_names[key].add(row["image_name"])
        object_counts[key] += 1

    return [
        {
            "split": split,
            **class_row,
            "image_count": len(image_names[(split, class_row["class_id"])]),
            "object_count": object_counts[(split, class_row["class_id"])],
        }
        for split in SPLITS
        for class_row in standard_classes
    ]


# selected_dataset.csv에서 선택 행의 split_group만 갱신합니다.
def write_selected_dataset(
    field_names: list[str],
    rows: list[dict[str, str]],
    assignments: dict[str, str],
) -> None:
    for row in rows:
        if row["selected"] == "True":
            row["split_group"] = assignments[row["image_name"]]

    path = METADATA_ROOT / "selected_dataset.csv"
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(rows)


# 분할별 이미지 이름을 오름차순으로 한 줄씩 기록합니다.
def write_split_files(assignments: dict[str, str]) -> None:
    SPLIT_ROOT.mkdir(parents=True, exist_ok=True)
    for split in SPLITS:
        image_names = sorted(
            name
            for name, assigned_split in assignments.items()
            if assigned_split == split
        )
        (SPLIT_ROOT / f"{split}.txt").write_text(
            "".join(f"{name}\n" for name in image_names), encoding="utf-8"
        )


# 분할별 클래스 분포를 고정된 컬럼 순서로 기록합니다.
def write_distribution(rows: list[dict[str, Any]]) -> None:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    path = REPORT_ROOT / "split_distribution.csv"
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=DISTRIBUTION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


# 검증 결과와 층화 통계를 한글 보고서로 기록합니다.
def write_validation_report(
    assignments: dict[str, str],
    split_names: dict[str, set[str]],
    required_counts: dict[tuple[str, str], int],
    image_strata: dict[str, str],
    annotations: list[dict[str, Any]],
) -> None:
    split_counts = Counter(assignments.values())
    stratum_counts = Counter(
        (assignments[image_name], stratum)
        for image_name, stratum in image_strata.items()
    )
    small_counts: Counter[str] = Counter()
    object_counts: Counter[str] = Counter()
    for row in annotations:
        split = assignments[row["image_name"]]
        object_counts[split] += 1
        if row["relative_area"] < 0.01:
            small_counts[split] += 1

    small_ratios = {
        split: small_counts[split] / object_counts[split] * 100 for split in SPLITS
    }
    ratio_range = max(small_ratios.values()) - min(small_ratios.values())
    if ratio_range >= 24.0:
        raise ValueError(
            f"작은 객체 비율 범위가 이전 결과보다 줄지 않았습니다: {ratio_range:.2f}%p"
        )

    total = len(assignments)
    strata = sorted(EXPECTED_STRATUM_COUNTS)
    lines = [
        "# 데이터셋 분할 검증 보고서",
        "",
        "## 분할 결과",
        "",
        "| 분할 | 이미지 수 | 실제 비율 | 목표 비율 |",
        "|---|---:|---:|---:|",
    ]
    lines.extend(
        f"| {split} | {split_counts[split]} | "
        f"{split_counts[split] / total * 100:.2f}% | "
        f"{TARGET_RATIOS[split] * 100:.0f}% |"
        for split in SPLITS
    )
    lines.extend(
        [
            "",
            "## 필수 이미지 포함 검증",
            "",
            "| 분할 | 정상 | porosity | slag_inclusion |",
            "|---|---:|---:|---:|",
        ]
    )
    lines.extend(
        f"| {split} | {required_counts[(split, 'normal')]} | "
        f"{required_counts[(split, 'porosity')]} | "
        f"{required_counts[(split, 'slag_inclusion')]} |"
        for split in SPLITS
    )
    lines.extend(
        [
            "",
            "모든 분할에 정상, porosity, slag_inclusion 이미지가 1장 이상 포함되었다.",
            "",
            "## 그룹 × 크기 층화 분포",
            "",
            "| 분할 | " + " | ".join(strata) + " |",
            "|---|" + "|".join("---:" for _ in strata) + "|",
        ]
    )
    lines.extend(
        "| "
        + split
        + " | "
        + " | ".join(str(stratum_counts[(split, stratum)]) for stratum in strata)
        + " |"
        for split in SPLITS
    )
    lines.extend(
        [
            "",
            "## 작은 객체 분포",
            "",
            "작은 객체는 작업12와 동일하게 `relative_area < 0.01`로 정의했다.",
            "",
            "| 분할 | 작은 객체 수 | 전체 객체 수 | 작은 객체 비율 |",
            "|---|---:|---:|---:|",
        ]
    )
    lines.extend(
        f"| {split} | {small_counts[split]} | {object_counts[split]} | "
        f"{small_ratios[split]:.2f}% |"
        for split in SPLITS
    )
    lines.extend(
        [
            "",
            f"세 분할의 작은 객체 비율 범위는 {ratio_range:.2f}%p이다. "
            "이전 group 단독 층화의 train 55.80%, val 62.32%, test 79.79%와 "
            "그 범위 24.0%p보다 감소했다.",
            "",
            "## 무결성 및 재현성 검증",
            "",
            "- 선택 이미지 중 `duplicate == True`: 0건 확인",
            f"- Random Seed: {SEED}",
            f"- train ∩ val: {len(split_names['train'] & split_names['val'])}장",
            f"- train ∩ test: {len(split_names['train'] & split_names['test'])}장",
            f"- val ∩ test: {len(split_names['val'] & split_names['test'])}장",
            "- 동일 이미지가 여러 분할에 속하지 않음: 확인(교집합 크기 0)",
            "",
        ]
    )
    (REPORT_ROOT / "split_validation_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


# 데이터 분할부터 산출물 생성과 검증까지 순서대로 수행합니다.
def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
    )
    field_names, rows = read_csv(METADATA_ROOT / "selected_dataset.csv")
    selected_rows = load_selected_rows(rows, field_names)
    standard_classes = load_standard_classes()
    selected_names = {row["image_name"] for row in selected_rows}
    annotations = load_annotations(selected_names, standard_classes)
    size_classes = build_size_classes(selected_rows, annotations)
    assignments, image_strata = build_split_assignments(selected_rows, size_classes)
    split_names, required_counts = validate_assignments(
        selected_rows, assignments, annotations
    )
    distribution = build_distribution(assignments, annotations, standard_classes)

    write_selected_dataset(field_names, rows, assignments)
    write_split_files(assignments)
    write_distribution(distribution)
    write_validation_report(
        assignments,
        split_names,
        required_counts,
        image_strata,
        annotations,
    )
    LOGGER.info(
        "데이터셋 분할 완료: train %d장, val %d장, test %d장",
        *(Counter(assignments.values())[split] for split in SPLITS),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
