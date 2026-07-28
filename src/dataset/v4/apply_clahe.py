"""dataset_v3 전체 이미지에 CLAHE를 적용해 dataset_v4를 구축합니다."""

import logging
import shutil
import sys
from pathlib import Path
from typing import Any

import cv2
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SOURCE_ROOT = PROJECT_ROOT / "data" / "processed" / "dataset_v3"
TARGET_ROOT = PROJECT_ROOT / "data" / "processed" / "dataset_v4"
DATASET_PATH = "data/processed/dataset_v4"
SPLITS = ("train", "val", "test")
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


# 출력 디렉터리 구조를 새로 만듭니다.
def prepare_target_directories() -> None:
    if TARGET_ROOT.exists():
        shutil.rmtree(TARGET_ROOT)
    for category in ("images", "labels"):
        for split in SPLITS:
            (TARGET_ROOT / category / split).mkdir(parents=True, exist_ok=True)


# 지정한 split의 이미지에는 CLAHE를 적용하고 라벨은 그대로 복사합니다.
def process_split(split: str, basenames: set[str]) -> None:
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    for basename in sorted(basenames):
        source_image_path = SOURCE_ROOT / "images" / split / f"{basename}.jpg"
        target_image_path = TARGET_ROOT / "images" / split / f"{basename}.jpg"

        image = cv2.imread(str(source_image_path))
        if image is None:
            raise ValueError(f"이미지를 읽을 수 없습니다: {source_image_path}")
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        l_enhanced = clahe.apply(l_channel)
        enhanced_lab = cv2.merge((l_enhanced, a_channel, b_channel))
        result = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        if not cv2.imwrite(str(target_image_path), result):
            raise OSError(f"이미지를 저장할 수 없습니다: {target_image_path}")

        shutil.copy2(
            SOURCE_ROOT / "labels" / split / f"{basename}.txt",
            TARGET_ROOT / "labels" / split / f"{basename}.txt",
        )


# dataset_v3 설정을 유지하면서 dataset path만 v4로 변경합니다.
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


# 원본과 출력 데이터셋의 split별 파일 구성이 정확히 같은지 검증합니다.
def validate_result(source_basenames: dict[str, set[str]]) -> None:
    for split in SPLITS:
        target_basenames = validate_image_label_pairs(TARGET_ROOT, split)
        if target_basenames != source_basenames[split]:
            missing_files = sorted(source_basenames[split] - target_basenames)
            unexpected_files = sorted(target_basenames - source_basenames[split])
            raise ValueError(
                f"{split} 파일 구성이 dataset_v3와 다릅니다: "
                f"missing_files={missing_files}, "
                f"unexpected_files={unexpected_files}"
            )


# dataset_v4 생성과 검증을 수행합니다.
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
        prepare_target_directories()
        for split in SPLITS:
            process_split(split, source_basenames[split])
            LOGGER.info("%s 처리 이미지 수: %d", split, len(source_basenames[split]))
        write_data_yaml()
        validate_result(source_basenames)
    except (OSError, ValueError, yaml.YAMLError) as error:
        LOGGER.error("dataset_v4 구축 실패: %s", error)
        return 1

    LOGGER.info("dataset_v4 구축 완료: %s", TARGET_ROOT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
