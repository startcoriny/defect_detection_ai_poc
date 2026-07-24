"""Baseline 모델로 Test 이미지를 추론하고 결과 산출물을 저장한다."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ultralytics import YOLO

LOGGER = logging.getLogger(__name__)
EXPERIMENT_ID = "EXP-P1-DET-003"
CONFIDENCE_THRESHOLD = 0.25
IOU_THRESHOLD = 0.70
IMAGE_SIZE = 960
DEVICE = "cpu"
IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


def configure_logging(output_dir: Path) -> None:
    """콘솔과 파일에 Test 추론 로그를 함께 기록한다."""
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "inference.log"
    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    logging.basicConfig(
        level=logging.INFO,
        handlers=[stream_handler, file_handler],
        force=True,
    )

    # Ultralytics는 전용 로거를 사용하므로 같은 파일 핸들러를 연결한다.
    ultralytics_logger = logging.getLogger("ultralytics")
    ultralytics_logger.addHandler(file_handler)


def require_file(path: Path) -> Path:
    """필수 입력 파일의 존재를 확인한다."""
    if not path.is_file():
        raise FileNotFoundError(f"필수 파일이 없습니다: {path}")
    return path


def load_class_names(path: Path) -> dict[int, str]:
    """기존 YOLO 클래스 파일에서 ID와 클래스명 매핑을 읽는다."""
    with require_file(path).open(encoding="utf-8-sig") as class_file:
        class_names = {
            class_id: line.strip()
            for class_id, line in enumerate(class_file)
            if line.strip()
        }
    if not class_names:
        raise ValueError(f"클래스 이름 파일이 비어 있습니다: {path}")
    return class_names


def load_test_images(test_dir: Path) -> list[Path]:
    """Test 디렉터리의 지원 이미지 파일을 이름순으로 불러온다."""
    if not test_dir.is_dir():
        raise FileNotFoundError(f"Test 이미지 디렉터리가 없습니다: {test_dir}")
    image_paths = sorted(
        (
            path.resolve()
            for path in test_dir.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        ),
        key=lambda path: path.name,
    )
    if not image_paths:
        raise ValueError(f"Test 이미지가 없습니다: {test_dir}")
    return image_paths


def extract_predictions(
    result: Any,
    class_names: dict[int, str],
) -> list[dict[str, Any]]:
    """Ultralytics 결과에서 클래스와 Bounding Box 정보를 추출한다."""
    predictions: list[dict[str, Any]] = []
    for box in result.boxes:
        class_id = int(box.cls.item())
        if class_id not in class_names:
            raise ValueError(f"클래스 매핑에 없는 예측 ID입니다: {class_id}")
        predictions.append(
            {
                "class_id": class_id,
                "class_name": class_names[class_id],
                "confidence": float(box.conf.item()),
                "bbox_xyxy": [float(value) for value in box.xyxy[0].tolist()],
                "bbox_normalized_xywh": [
                    float(value) for value in box.xywhn[0].tolist()
                ],
            }
        )
    return predictions


def build_summary(
    total_images: int,
    succeeded: int,
    failures: list[dict[str, str]],
    inference_times: list[float],
) -> dict[str, int | float]:
    """성공한 이미지의 Ultralytics 추론 시간을 기준으로 요약 통계를 계산한다."""
    total_time = sum(inference_times)
    return {
        "total_images": total_images,
        "succeeded": succeeded,
        "failed": len(failures),
        "total_inference_time_ms": total_time,
        "avg_inference_time_ms": (
            total_time / len(inference_times) if inference_times else 0.0
        ),
        "min_inference_time_ms": min(inference_times, default=0.0),
        "max_inference_time_ms": max(inference_times, default=0.0),
    }


def write_results(path: Path, data: dict[str, Any]) -> None:
    """추론 결과를 UTF-8 JSON 파일로 저장한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=2)
        json_file.write("\n")


def run_inference(project_root: Path) -> dict[str, Any]:
    """Test 이미지를 개별 추론하고 성공 및 실패 결과를 모두 구성한다."""
    model_path = require_file(
        (project_root / "experiments" / EXPERIMENT_ID / "models" / "best.pt").resolve()
    )
    class_names = load_class_names(project_root / "metadata" / "yolo_classes.txt")
    image_paths = load_test_images(
        project_root / "data" / "processed" / "dataset_v1" / "images" / "test"
    )
    prediction_project = (
        project_root / "outputs" / EXPERIMENT_ID / "predictions"
    ).resolve()
    model = YOLO(str(model_path))

    images: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    inference_times: list[float] = []
    LOGGER.info(
        "Test 추론 시작 - model=%s, images=%d, device=%s",
        model_path,
        len(image_paths),
        DEVICE,
    )

    for index, image_path in enumerate(image_paths, start=1):
        try:
            results = model.predict(
                source=str(image_path),
                conf=CONFIDENCE_THRESHOLD,
                iou=IOU_THRESHOLD,
                imgsz=IMAGE_SIZE,
                device=DEVICE,
                save=True,
                save_txt=True,
                save_conf=False,
                project=str(prediction_project),
                name="test",
                exist_ok=True,
            )
            if len(results) != 1:
                raise RuntimeError(
                    "단일 이미지의 추론 결과 수가 1개가 아닙니다: " f"{len(results)}개"
                )

            result = results[0]
            inference_time = float(result.speed["inference"])
            predictions = extract_predictions(result, class_names)
            images.append(
                {
                    "image_name": image_path.name,
                    "status": "success",
                    "inference_time_ms": inference_time,
                    "predictions": predictions,
                }
            )
            inference_times.append(inference_time)
            LOGGER.info(
                "Test 이미지 처리 완료 [%d/%d] - %s, predictions=%d, "
                "inference=%.3fms",
                index,
                len(image_paths),
                image_path.name,
                len(predictions),
                inference_time,
            )
        except Exception as error:
            images.append(
                {
                    "image_name": image_path.name,
                    "status": "failed",
                    "inference_time_ms": None,
                    "predictions": [],
                }
            )
            failures.append(
                {
                    "image_name": image_path.name,
                    "error": f"{type(error).__name__}: {error}",
                }
            )
            LOGGER.exception(
                "Test 이미지 처리 실패 [%d/%d] - %s",
                index,
                len(image_paths),
                image_path.name,
            )

    return {
        "model_version": EXPERIMENT_ID,
        "model_path": str(model_path),
        "inference_config": {
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "iou_threshold": IOU_THRESHOLD,
            "imgsz": IMAGE_SIZE,
            "device": DEVICE,
        },
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "summary": build_summary(
            total_images=len(image_paths),
            succeeded=len(image_paths) - len(failures),
            failures=failures,
            inference_times=inference_times,
        ),
        "images": images,
        "failures": failures,
    }


def main() -> None:
    """프로젝트 경로를 설정하고 Test 추론 결과를 파일로 저장한다."""
    project_root = Path(__file__).resolve().parents[3]
    output_dir = (project_root / "outputs" / EXPERIMENT_ID / "predictions").resolve()
    result_path = (
        project_root / "predictions" / EXPERIMENT_ID / "prediction_results.json"
    )
    configure_logging(output_dir)

    try:
        results = run_inference(project_root)
        write_results(result_path, results)
        summary = results["summary"]
        LOGGER.info(
            "Test 추론 완료 - total=%d, succeeded=%d, failed=%d, result=%s",
            summary["total_images"],
            summary["succeeded"],
            summary["failed"],
            result_path,
        )
    except Exception:
        LOGGER.exception("Test 추론 준비 또는 결과 저장 실패")
        raise


if __name__ == "__main__":
    main()
