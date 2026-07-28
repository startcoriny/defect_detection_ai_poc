"""Train의 slag_inclusion 포함 이미지를 복제해 dataset_v3를 구축합니다."""

import logging
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SOURCE_ROOT = PROJECT_ROOT / "data" / "processed" / "dataset_v2"
TARGET_ROOT = PROJECT_ROOT / "data" / "processed" / "dataset_v3"
DATASET_PATH = "data/processed/dataset_v3"
SPLITS = ("train", "val", "test")
SLAG_INCLUSION_CLASS_ID = 4
POROSITY_CLASS_ID = 3
LOGGER = logging.getLogger(__name__)


# 이미지와 라벨의 basename이 정확히 일치하는지 확인합니다.
def validate_image_label_pairs(dataset_root: Path, split: str) -> set[str]:
    image_dir = dataset_root / "images" / split
    label_dir = dataset_root / "labels" / split
    if not image_dir.is_dir() or not label_dir.is_dir():
        raise FileNotFoundError(f"{split} 이미지 또는 라벨 디렉터리가 없습니다.")

    image_names = {path.stem for path in image_dir.glob("*.jpg") if path.is_file()}
    label_names = {path.stem for path in label_dir.glob("*.txt") if path.is_file()}
    if image_names != label_names:
        missing_labels = sorted(image_names - label_names)
        missing_images = sorted(label_names - image_names)
        raise ValueError(
            f"{split} 이미지·라벨 basename이 일치하지 않습니다: "
            f"missing_labels={missing_labels}, missing_images={missing_images}"
        )
    return image_names


# YOLO 라벨의 첫 토큰을 기준으로 클래스별 객체 수를 계산합니다.
def count_objects(label_paths: list[Path]) -> Counter[int]:
    counts: Counter[int] = Counter()
    for label_path in label_paths:
        for line_number, line in enumerate(
            label_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            tokens = line.split()
            if not tokens:
                continue
            try:
                class_id = int(tokens[0])
            except ValueError as error:
                raise ValueError(
                    f"잘못된 class_id입니다: {label_path}:{line_number}"
                ) from error
            counts[class_id] += 1
    return counts


# 라벨 각 줄의 첫 토큰에서 slag_inclusion 포함 여부를 확인합니다.
def contains_slag_inclusion(label_path: Path) -> bool:
    for line in label_path.read_text(encoding="utf-8").splitlines():
        tokens = line.split()
        if tokens and tokens[0] == str(SLAG_INCLUSION_CLASS_ID):
            return True
    return False


# 출력 디렉터리 구조를 새로 만듭니다.
def prepare_target_directories() -> None:
    if TARGET_ROOT.exists():
        shutil.rmtree(TARGET_ROOT)
    for category in ("images", "labels"):
        for split in SPLITS:
            (TARGET_ROOT / category / split).mkdir(parents=True, exist_ok=True)


# 지정한 split의 원본 이미지·라벨 쌍을 그대로 복사합니다.
def copy_split(split: str, basenames: set[str]) -> None:
    for basename in sorted(basenames):
        shutil.copy2(
            SOURCE_ROOT / "images" / split / f"{basename}.jpg",
            TARGET_ROOT / "images" / split / f"{basename}.jpg",
        )
        shutil.copy2(
            SOURCE_ROOT / "labels" / split / f"{basename}.txt",
            TARGET_ROOT / "labels" / split / f"{basename}.txt",
        )


# Train에서 slag_inclusion 포함 이미지·라벨 쌍을 _dup1 이름으로 복제합니다.
def duplicate_slag_train_images(train_basenames: set[str]) -> set[str]:
    duplicated_names = set()
    for basename in sorted(train_basenames):
        source_label = SOURCE_ROOT / "labels" / "train" / f"{basename}.txt"
        if not contains_slag_inclusion(source_label):
            continue

        duplicate_name = f"{basename}_dup1"
        shutil.copy2(
            SOURCE_ROOT / "images" / "train" / f"{basename}.jpg",
            TARGET_ROOT / "images" / "train" / f"{duplicate_name}.jpg",
        )
        shutil.copy2(
            source_label,
            TARGET_ROOT / "labels" / "train" / f"{duplicate_name}.txt",
        )
        duplicated_names.add(duplicate_name)
    return duplicated_names


# dataset_v2의 설정을 유지하면서 dataset path만 v3로 변경합니다.
def write_data_yaml() -> None:
    source_yaml_path = SOURCE_ROOT / "data.yaml"
    with source_yaml_path.open("r", encoding="utf-8") as yaml_file:
        yaml_data: Any = yaml.safe_load(yaml_file)
    if not isinstance(yaml_data, dict):
        raise ValueError(f"data.yaml 최상위 값이 매핑이 아닙니다: {source_yaml_path}")
    if "names" not in yaml_data:
        raise ValueError(f"data.yaml에 names가 없습니다: {source_yaml_path}")

    yaml_data["path"] = DATASET_PATH
    with (TARGET_ROOT / "data.yaml").open("w", encoding="utf-8") as yaml_file:
        yaml.safe_dump(yaml_data, yaml_file, allow_unicode=True, sort_keys=False)


# 원본과 출력 데이터셋의 구조 및 split별 파일 수를 검증합니다.
def validate_result(
    source_basenames: dict[str, set[str]], duplicate_count: int
) -> None:
    for split in SPLITS:
        target_names = validate_image_label_pairs(TARGET_ROOT, split)
        expected_count = len(source_basenames[split])
        if split == "train":
            expected_count += duplicate_count
        if len(target_names) != expected_count:
            raise ValueError(
                f"{split} 이미지 수가 예상과 다릅니다: "
                f"expected={expected_count}, actual={len(target_names)}"
            )

    # Val·Test는 원본 이름까지 동일해야 오버샘플링이나 이름 변경이 없음을 보장합니다.
    for split in ("val", "test"):
        target_names = validate_image_label_pairs(TARGET_ROOT, split)
        if target_names != source_basenames[split]:
            raise ValueError(f"{split} 파일 구성이 dataset_v2와 다릅니다.")


# dataset_v3 생성과 검증을 수행합니다.
def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
    )
    try:
        source_basenames = {
            split: validate_image_label_pairs(SOURCE_ROOT, split) for split in SPLITS
        }
        source_train_labels = [
            SOURCE_ROOT / "labels" / "train" / f"{name}.txt"
            for name in sorted(source_basenames["train"])
        ]
        before_counts = count_objects(source_train_labels)

        prepare_target_directories()
        for split in SPLITS:
            copy_split(split, source_basenames[split])
        duplicated_names = duplicate_slag_train_images(source_basenames["train"])
        write_data_yaml()
        validate_result(source_basenames, len(duplicated_names))

        target_train_labels = sorted((TARGET_ROOT / "labels" / "train").glob("*.txt"))
        after_counts = count_objects(target_train_labels)
    except (OSError, ValueError, yaml.YAMLError) as error:
        LOGGER.error("dataset_v3 구축 실패: %s", error)
        return 1

    LOGGER.info("Train 원본 이미지 수: %d", len(source_basenames["train"]))
    LOGGER.info("slag_inclusion 포함(복제 대상) 이미지 수: %d", len(duplicated_names))
    LOGGER.info(
        "복제 후 Train 전체 이미지 수: %d",
        len(source_basenames["train"]) + len(duplicated_names),
    )
    LOGGER.info(
        "Train porosity 객체 수: 복제 전 %d, 복제 후 %d",
        before_counts[POROSITY_CLASS_ID],
        after_counts[POROSITY_CLASS_ID],
    )
    LOGGER.info(
        "Train slag_inclusion 객체 수: 복제 전 %d, 복제 후 %d",
        before_counts[SLAG_INCLUSION_CLASS_ID],
        after_counts[SLAG_INCLUSION_CLASS_ID],
    )
    LOGGER.info("dataset_v3 구축 완료: %s", TARGET_ROOT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
