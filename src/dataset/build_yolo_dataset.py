"""확정된 분할에 따라 YOLO 학습 데이터셋을 구성합니다."""

import csv
import hashlib
import logging
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METADATA_ROOT = PROJECT_ROOT / "metadata"
SELECTED_DATASET_PATH = METADATA_ROOT / "selected_dataset.csv"
INVENTORY_PATH = METADATA_ROOT / "raw_dataset_inventory.csv"
CLASS_PATH = METADATA_ROOT / "yolo_classes.txt"
LABEL_ROOT = PROJECT_ROOT / "outputs" / "yolo_labels"
DATASET_ROOT = PROJECT_ROOT / "data" / "processed" / "dataset_v1"
STAGING_ROOT = DATASET_ROOT.with_name(f"{DATASET_ROOT.name}.tmp")
LOGGER = logging.getLogger(__name__)

SPLITS = ("train", "val", "test")
EXPECTED_SPLIT_COUNTS = {"train": 209, "val": 44, "test": 46}
DATASET_PATH = "data/processed/dataset_v1"


# CSV 파일을 읽고 필수 헤더가 있는지 확인합니다.
def read_csv(path: Path, required_fields: set[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        field_names = set(reader.fieldnames or [])
        missing_fields = required_fields - field_names
        if missing_fields:
            raise ValueError(
                f"{path.name}에 필수 컬럼이 없습니다: "
                + ", ".join(sorted(missing_fields))
            )
        return list(reader)


# 선택된 이미지와 확정된 분할 정보를 읽고 유효성을 검사합니다.
def load_selected_rows() -> list[dict[str, str]]:
    rows = read_csv(
        SELECTED_DATASET_PATH,
        {"image_name", "selected", "split_group"},
    )
    selected_rows = [row for row in rows if row["selected"] == "True"]
    image_names = [row["image_name"].strip() for row in selected_rows]
    if not selected_rows:
        raise ValueError("selected == True인 이미지가 없습니다.")
    if any(not image_name for image_name in image_names):
        raise ValueError("선택 데이터에 비어 있는 image_name이 있습니다.")
    if len(image_names) != len(set(image_names)):
        raise ValueError("선택 데이터에 동일한 image_name이 두 번 이상 있습니다.")

    split_counts = Counter(row["split_group"].strip() for row in selected_rows)
    invalid_splits = sorted(set(split_counts) - set(SPLITS))
    if invalid_splits:
        raise ValueError(
            "선택 데이터에 알 수 없는 split_group 값이 있습니다: "
            + ", ".join(invalid_splits)
        )
    if dict(split_counts) != EXPECTED_SPLIT_COUNTS:
        raise ValueError(
            "분할별 이미지 수가 예상값과 다릅니다: "
            f"expected={EXPECTED_SPLIT_COUNTS}, actual={dict(split_counts)}"
        )
    return selected_rows


# 인벤토리에서 선택 이미지의 원본 경로를 프로젝트 기준 절대 경로로 변환합니다.
def load_image_paths(selected_names: set[str]) -> dict[str, Path]:
    rows = read_csv(INVENTORY_PATH, {"image_name", "image_path"})
    image_paths: dict[str, Path] = {}
    for row in rows:
        image_name = row["image_name"].strip()
        if image_name not in selected_names:
            continue
        if image_name in image_paths:
            raise ValueError(f"인벤토리에 이미지가 중복되어 있습니다: {image_name}")

        relative_path = Path(row["image_path"].strip())
        if relative_path.is_absolute():
            raise ValueError(
                f"인벤토리 image_path는 프로젝트 상대 경로여야 합니다: {image_name}"
            )
        image_paths[image_name] = PROJECT_ROOT / relative_path

    missing_names = sorted(selected_names - set(image_paths))
    if missing_names:
        raise ValueError(
            "인벤토리에 원본 이미지 경로가 없습니다: " + ", ".join(missing_names)
        )
    return image_paths


# 클래스 파일을 ID 순서대로 읽고 6개 표준 클래스인지 확인합니다.
def load_class_names() -> list[str]:
    class_names = [
        line.strip()
        for line in CLASS_PATH.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    if len(class_names) != 6:
        raise ValueError(
            f"yolo_classes.txt에는 클래스가 정확히 6개 있어야 합니다: {len(class_names)}"
        )
    if len(class_names) != len(set(class_names)):
        raise ValueError("yolo_classes.txt에 중복 클래스가 있습니다.")
    return class_names


# 모든 원본 이미지와 라벨이 복사 전에 존재하고 형식이 맞는지 확인합니다.
def validate_sources(
    selected_rows: list[dict[str, str]], image_paths: dict[str, Path]
) -> dict[str, Path]:
    label_paths = {}
    errors = []
    for row in selected_rows:
        image_name = row["image_name"].strip()
        image_path = image_paths[image_name]
        label_path = LABEL_ROOT / f"{image_name}.txt"
        if image_path.suffix.lower() != ".jpg":
            errors.append(f"원본 이미지 확장자가 .jpg가 아닙니다: {image_path}")
        if not image_path.is_file():
            errors.append(f"원본 이미지가 없습니다: {image_path}")
        if not label_path.is_file():
            errors.append(f"YOLO 라벨이 없습니다: {label_path}")
        label_paths[image_name] = label_path

    if errors:
        raise FileNotFoundError("\n".join(errors))
    return label_paths


# 파일 내용의 SHA-256 해시를 계산합니다.
def calculate_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# 파일을 복사하고 원본과 대상의 내용이 같은지 확인합니다.
def copy_and_verify(source: Path, destination: Path) -> None:
    shutil.copy2(source, destination)
    if source.stat().st_size != destination.stat().st_size:
        raise OSError(f"복사 파일 크기가 원본과 다릅니다: {destination}")
    if calculate_hash(source) != calculate_hash(destination):
        raise OSError(f"복사 파일 내용이 원본과 다릅니다: {destination}")


# 임시 디렉터리에 분할 폴더를 만들고 이미지와 라벨을 복사합니다.
def build_staging_dataset(
    selected_rows: list[dict[str, str]],
    image_paths: dict[str, Path],
    label_paths: dict[str, Path],
) -> None:
    if STAGING_ROOT.exists():
        shutil.rmtree(STAGING_ROOT)
    for category in ("images", "labels"):
        for split in SPLITS:
            (STAGING_ROOT / category / split).mkdir(parents=True, exist_ok=True)

    for row in sorted(selected_rows, key=lambda item: item["image_name"]):
        image_name = row["image_name"].strip()
        split = row["split_group"].strip()
        copy_and_verify(
            image_paths[image_name],
            STAGING_ROOT / "images" / split / f"{image_name}.jpg",
        )
        copy_and_verify(
            label_paths[image_name],
            STAGING_ROOT / "labels" / split / f"{image_name}.txt",
        )


# 클래스 파일의 순서를 보존해 data.yaml을 생성합니다.
def write_data_yaml(class_names: list[str]) -> None:
    yaml_data = {
        "path": DATASET_PATH,
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": dict(enumerate(class_names)),
    }
    with (STAGING_ROOT / "data.yaml").open("w", encoding="utf-8") as yaml_file:
        yaml.safe_dump(
            yaml_data,
            yaml_file,
            allow_unicode=True,
            sort_keys=False,
        )


# 분할별 이미지·라벨 쌍과 수량 및 정상 이미지 포함 여부를 검사합니다.
def validate_dataset_files(
    dataset_root: Path,
    selected_rows: list[dict[str, str]],
    label_paths: dict[str, Path],
) -> int:
    for split in SPLITS:
        image_names = {
            path.stem for path in (dataset_root / "images" / split).glob("*.jpg")
        }
        label_names = {
            path.stem for path in (dataset_root / "labels" / split).glob("*.txt")
        }
        if image_names != label_names:
            missing_labels = sorted(image_names - label_names)
            missing_images = sorted(label_names - image_names)
            raise ValueError(
                f"{split} 이미지·라벨 basename이 일치하지 않습니다: "
                f"missing_labels={missing_labels}, missing_images={missing_images}"
            )
        if len(image_names) != EXPECTED_SPLIT_COUNTS[split]:
            raise ValueError(
                f"{split} 파일 수가 예상값과 다릅니다: "
                f"expected={EXPECTED_SPLIT_COUNTS[split]}, actual={len(image_names)}"
            )
        LOGGER.info(
            "%s 분할: 이미지 %d개, 라벨 %d개",
            split,
            len(image_names),
            len(label_names),
        )

    empty_label_names = {
        image_name
        for image_name, label_path in label_paths.items()
        if label_path.stat().st_size == 0
    }
    copied_empty_names = {
        row["image_name"].strip()
        for row in selected_rows
        if (
            dataset_root
            / "labels"
            / row["split_group"].strip()
            / f"{row['image_name'].strip()}.txt"
        )
        .stat()
        .st_size
        == 0
    }
    if not empty_label_names:
        raise ValueError("선택 데이터에 정상 이미지용 빈 라벨이 없습니다.")
    if copied_empty_names != empty_label_names:
        raise ValueError("정상 이미지용 빈 라벨이 모두 복사되지 않았습니다.")
    return len(copied_empty_names)


# data.yaml의 클래스 매핑과 모든 데이터 경로를 검사합니다.
def validate_data_yaml(class_names: list[str]) -> None:
    yaml_path = DATASET_ROOT / "data.yaml"
    with yaml_path.open("r", encoding="utf-8") as yaml_file:
        yaml_data: Any = yaml.safe_load(yaml_file)
    if not isinstance(yaml_data, dict):
        raise ValueError("data.yaml의 최상위 값은 매핑이어야 합니다.")

    expected_names = dict(enumerate(class_names))
    if yaml_data.get("names") != expected_names:
        raise ValueError(
            "data.yaml 클래스 매핑이 yolo_classes.txt와 다릅니다: "
            f"expected={expected_names}, actual={yaml_data.get('names')}"
        )
    if yaml_data.get("path") != DATASET_PATH:
        raise ValueError(f"data.yaml path가 올바르지 않습니다: {yaml_data.get('path')}")

    yaml_dataset_root = PROJECT_ROOT / yaml_data["path"]
    for split in SPLITS:
        relative_path = yaml_data.get(split)
        if not isinstance(relative_path, str):
            raise ValueError(f"data.yaml의 {split} 경로가 올바르지 않습니다.")
        resolved_path = yaml_dataset_root / relative_path
        if not resolved_path.is_dir():
            raise FileNotFoundError(
                f"data.yaml의 {split} 디렉터리가 없습니다: {resolved_path}"
            )
    LOGGER.info("data.yaml 검증 완료: 경로 유효, 클래스 %d개 일치", len(class_names))


# 데이터셋을 교체한 뒤 최종 구조와 설정을 검증합니다.
def publish_dataset() -> None:
    DATASET_ROOT.parent.mkdir(parents=True, exist_ok=True)
    if DATASET_ROOT.exists():
        shutil.rmtree(DATASET_ROOT)
    STAGING_ROOT.replace(DATASET_ROOT)


# 입력 검증부터 데이터셋 생성과 최종 검증까지 수행합니다.
def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
    )
    try:
        selected_rows = load_selected_rows()
        selected_names = {row["image_name"].strip() for row in selected_rows}
        image_paths = load_image_paths(selected_names)
        class_names = load_class_names()
        label_paths = validate_sources(selected_rows, image_paths)

        build_staging_dataset(selected_rows, image_paths, label_paths)
        write_data_yaml(class_names)
        normal_count = validate_dataset_files(
            STAGING_ROOT,
            selected_rows,
            label_paths,
        )
        publish_dataset()
        validate_data_yaml(class_names)
    except (OSError, ValueError, yaml.YAMLError) as error:
        if STAGING_ROOT.exists():
            shutil.rmtree(STAGING_ROOT)
        LOGGER.error("YOLO 데이터셋 구성 실패: %s", error)
        return 1

    LOGGER.info("전체 복사 파일 수: %d개", len(selected_rows) * 2)
    LOGGER.info("정상 이미지 수: %d장", normal_count)
    LOGGER.info("YOLO 데이터셋 구성 완료: %s", DATASET_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
