"""원본 추론 결과를 YOLO 자동 라벨과 CVAT Import 묶음으로 변환한다."""

from __future__ import annotations

import json
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)
MODEL_VERSION = "EXP-P1-DET-001"
CONFIDENCE_THRESHOLD = 0.25
EXPECTED_IMAGE_COUNT = 46
EXPECTED_CLASS_COUNT = 6
IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PREDICTIONS_PATH = PROJECT_ROOT / "predictions" / "prediction_results.json"
CLASSES_PATH = PROJECT_ROOT / "metadata" / "yolo_classes.txt"
TEST_IMAGES_DIR = PROJECT_ROOT / "data" / "processed" / "dataset_v1" / "images" / "test"
OUTPUT_ROOT = PROJECT_ROOT / "auto-labels"
STAGING_ROOT = PROJECT_ROOT / ".auto-labels-staging"


def now_iso() -> str:
    """현재 로컬 시각을 시간대가 포함된 ISO 8601 문자열로 반환한다."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def require_file(path: Path) -> Path:
    """필수 입력 파일의 존재를 확인한다."""
    if not path.is_file():
        raise FileNotFoundError(f"필수 입력 파일이 없습니다: {path}")
    return path


def load_class_names() -> list[str]:
    """YOLO 클래스 이름을 원본 줄 순서대로 읽고 개수를 검증한다."""
    class_names = [
        line.strip()
        for line in require_file(CLASSES_PATH)
        .read_text(encoding="utf-8-sig")
        .splitlines()
        if line.strip()
    ]
    if len(class_names) != EXPECTED_CLASS_COUNT:
        raise ValueError(
            "클래스 수가 예상과 다릅니다: "
            f"expected={EXPECTED_CLASS_COUNT}, actual={len(class_names)}"
        )
    if len(class_names) != len(set(class_names)):
        raise ValueError("metadata/yolo_classes.txt에 중복 클래스가 있습니다.")
    return class_names


def load_test_images() -> list[Path]:
    """Test 이미지 파일을 파일명 순으로 읽고 예상 수량을 검증한다."""
    if not TEST_IMAGES_DIR.is_dir():
        raise FileNotFoundError(f"Test 이미지 폴더가 없습니다: {TEST_IMAGES_DIR}")

    image_paths = sorted(
        (
            path
            for path in TEST_IMAGES_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        ),
        key=lambda path: path.name,
    )
    if len(image_paths) != EXPECTED_IMAGE_COUNT:
        raise ValueError(
            "Test 이미지 수가 예상과 다릅니다: "
            f"expected={EXPECTED_IMAGE_COUNT}, actual={len(image_paths)}"
        )
    if len({path.stem for path in image_paths}) != len(image_paths):
        raise ValueError("Test 이미지에 확장자를 제외한 파일명이 중복됩니다.")
    return image_paths


def load_prediction_results() -> dict[str, Any]:
    """원본 Prediction JSON을 읽고 최상위 설정을 검증한다."""
    with require_file(PREDICTIONS_PATH).open(encoding="utf-8") as predictions_file:
        data: Any = json.load(predictions_file)
    if not isinstance(data, dict):
        raise ValueError("prediction_results.json 최상위 값은 객체여야 합니다.")
    if data.get("model_version") != MODEL_VERSION:
        raise ValueError(
            "원본 모델 버전이 예상과 다릅니다: "
            f"expected={MODEL_VERSION}, actual={data.get('model_version')}"
        )

    inference_config = data.get("inference_config")
    if not isinstance(inference_config, dict):
        raise ValueError(
            "prediction_results.json의 inference_config가 올바르지 않습니다."
        )
    if inference_config.get("confidence_threshold") != CONFIDENCE_THRESHOLD:
        raise ValueError(
            "원본 Confidence Threshold가 예상과 다릅니다: "
            f"expected={CONFIDENCE_THRESHOLD}, "
            f"actual={inference_config.get('confidence_threshold')}"
        )
    return data


def validate_prediction(
    prediction: Any,
    image_name: str,
    class_names: list[str],
) -> tuple[int, list[float]]:
    """단일 예측의 클래스와 정규화 좌표를 검증한다."""
    if not isinstance(prediction, dict):
        raise ValueError(f"{image_name}: prediction 항목은 객체여야 합니다.")

    class_id = prediction.get("class_id")
    if (
        not isinstance(class_id, int)
        or isinstance(class_id, bool)
        or not 0 <= class_id < len(class_names)
    ):
        raise ValueError(f"{image_name}: 유효하지 않은 class_id입니다: {class_id}")

    class_name = prediction.get("class_name")
    if class_name != class_names[class_id]:
        raise ValueError(
            f"{image_name}: class_id와 class_name이 일치하지 않습니다: "
            f"{class_id}, {class_name}"
        )

    coordinates = prediction.get("bbox_normalized_xywh")
    if not isinstance(coordinates, list) or len(coordinates) != 4:
        raise ValueError(f"{image_name}: bbox_normalized_xywh는 숫자 4개여야 합니다.")
    if any(
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not 0.0 <= float(value) <= 1.0
        for value in coordinates
    ):
        raise ValueError(
            f"{image_name}: 정규화 좌표가 0~1 범위를 벗어났습니다: {coordinates}"
        )
    return class_id, [float(value) for value in coordinates]


def build_label_contents(
    prediction_results: dict[str, Any],
    image_paths: list[Path],
    class_names: list[str],
) -> dict[str, str]:
    """이미지별 예측을 소수점 6자리 YOLO 라벨 문자열로 변환한다."""
    images = prediction_results.get("images")
    if not isinstance(images, list):
        raise ValueError("prediction_results.json의 images가 배열이 아닙니다.")

    predictions_by_name: dict[str, list[Any]] = {}
    for image_result in images:
        if not isinstance(image_result, dict):
            raise ValueError("images 항목은 객체여야 합니다.")
        image_name = image_result.get("image_name")
        predictions = image_result.get("predictions")
        if not isinstance(image_name, str) or not image_name:
            raise ValueError("images 항목에 유효한 image_name이 없습니다.")
        if image_name in predictions_by_name:
            raise ValueError(f"중복된 추론 이미지가 있습니다: {image_name}")
        if not isinstance(predictions, list):
            raise ValueError(f"{image_name}: predictions가 배열이 아닙니다.")
        predictions_by_name[image_name] = predictions

    test_image_names = {path.name for path in image_paths}
    prediction_image_names = set(predictions_by_name)
    if test_image_names != prediction_image_names:
        missing = sorted(test_image_names - prediction_image_names)
        unexpected = sorted(prediction_image_names - test_image_names)
        raise ValueError(
            "Test 이미지와 추론 결과 이미지가 일치하지 않습니다: "
            f"missing={missing}, unexpected={unexpected}"
        )

    label_contents: dict[str, str] = {}
    for image_path in image_paths:
        lines: list[str] = []
        for prediction in predictions_by_name[image_path.name]:
            class_id, coordinates = validate_prediction(
                prediction,
                image_path.name,
                class_names,
            )
            coordinate_text = " ".join(f"{value:.6f}" for value in coordinates)
            lines.append(f"{class_id} {coordinate_text}")
        label_contents[image_path.stem] = (
            "".join(f"{line}\n" for line in lines) if lines else ""
        )
    return label_contents


def prepare_staging_root() -> None:
    """이전 임시 결과를 제거하고 출력 하위 디렉터리를 준비한다."""
    if STAGING_ROOT.exists():
        shutil.rmtree(STAGING_ROOT)
    (STAGING_ROOT / "yolo-labels").mkdir(parents=True)
    (STAGING_ROOT / "prediction-metadata").mkdir()
    (STAGING_ROOT / "cvat-import" / "obj_train_data").mkdir(parents=True)


def write_yolo_labels(label_contents: dict[str, str]) -> None:
    """모든 Test 이미지에 대응하는 YOLO TXT를 생성한다."""
    labels_dir = STAGING_ROOT / "yolo-labels"
    for image_stem, content in label_contents.items():
        (labels_dir / f"{image_stem}.txt").write_text(content, encoding="utf-8")


def write_prediction_metadata() -> None:
    """Export 설정을 기록하고 원본 Prediction JSON을 그대로 복사한다."""
    metadata_dir = STAGING_ROOT / "prediction-metadata"
    export_metadata = {
        "model_version": MODEL_VERSION,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "exported_at": now_iso(),
        "source": "predictions/prediction_results.json",
    }
    (metadata_dir / "export_metadata.json").write_text(
        json.dumps(export_metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    shutil.copy2(PREDICTIONS_PATH, metadata_dir / "prediction_results.json")


def write_cvat_import(
    image_paths: list[Path],
    label_contents: dict[str, str],
) -> None:
    """CVAT YOLO 1.1/Darknet Import용 파일과 이미지·라벨 묶음을 생성한다."""
    cvat_dir = STAGING_ROOT / "cvat-import"
    object_dir = cvat_dir / "obj_train_data"

    shutil.copy2(CLASSES_PATH, cvat_dir / "obj.names")
    (cvat_dir / "obj.data").write_text(
        "\n".join(
            (
                f"classes = {EXPECTED_CLASS_COUNT}",
                "train = train.txt",
                "names = obj.names",
                "backup = backup/",
                "",
            )
        ),
        encoding="utf-8",
    )
    (cvat_dir / "train.txt").write_text(
        "".join(f"obj_train_data/{path.name}\n" for path in image_paths),
        encoding="utf-8",
    )

    for image_path in image_paths:
        shutil.copy2(image_path, object_dir / image_path.name)
        (object_dir / f"{image_path.stem}.txt").write_text(
            label_contents[image_path.stem],
            encoding="utf-8",
        )


def publish_output() -> None:
    """완성된 임시 결과를 최종 auto-labels 디렉터리로 교체한다."""
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    STAGING_ROOT.replace(OUTPUT_ROOT)


def main() -> int:
    """Prediction JSON 검증부터 자동 라벨 결과 발행까지 수행한다."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
    )
    try:
        class_names = load_class_names()
        image_paths = load_test_images()
        prediction_results = load_prediction_results()
        label_contents = build_label_contents(
            prediction_results,
            image_paths,
            class_names,
        )

        prepare_staging_root()
        write_yolo_labels(label_contents)
        write_prediction_metadata()
        write_cvat_import(image_paths, label_contents)
        publish_output()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        if STAGING_ROOT.exists():
            shutil.rmtree(STAGING_ROOT)
        LOGGER.error("자동 라벨 생성 실패: %s", error)
        return 1

    nonempty_count = sum(bool(content) for content in label_contents.values())
    LOGGER.info(
        "자동 라벨 생성 완료: 이미지 %d장, 예측 포함 %d장, 빈 라벨 %d개",
        len(image_paths),
        nonempty_count,
        len(image_paths) - nonempty_count,
    )
    LOGGER.info("출력 위치: %s", OUTPUT_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
