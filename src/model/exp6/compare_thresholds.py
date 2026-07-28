"""동일한 모델과 Test 데이터에서 Confidence Threshold별 성능을 비교한다."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

from ultralytics import YOLO

LOGGER = logging.getLogger(__name__)
EXPERIMENT_ID = "EXP-P1-DET-006"
CONFIDENCE_THRESHOLDS = (0.10, 0.25, 0.50, 0.75)
IOU_THRESHOLD = 0.70
IMAGE_SIZE = 960
DEVICE = "cpu"
TEST_IMAGE_COUNT = 84
ACTIVE_CLASS_IDS = (3, 4)
IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}
CSV_COLUMNS = (
    "threshold",
    "predicted_count",
    "tp",
    "fp",
    "fn",
    "precision",
    "recall",
    "avg_labels_per_image",
    "fp_to_remove",
    "fn_to_add",
    "ultra_mp",
    "ultra_mr",
    "ultra_map50",
    "ultra_map50_95",
)


def require_file(path: Path) -> Path:
    """필수 입력 파일의 존재를 확인한다."""
    if not path.is_file():
        raise FileNotFoundError(f"필수 파일이 없습니다: {path}")
    return path


def load_test_images(test_dir: Path) -> list[Path]:
    """Test 이미지 파일을 이름순으로 불러온다."""
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
    if len(image_paths) != TEST_IMAGE_COUNT:
        raise ValueError(
            f"Test 이미지는 {TEST_IMAGE_COUNT}장이어야 합니다: "
            f"{len(image_paths)}장 ({test_dir})"
        )
    return image_paths


def safe_ratio(numerator: int, denominator: int) -> float | None:
    """분모가 0이면 공란 저장을 위해 None을 반환한다."""
    return numerator / denominator if denominator else None


def build_comparison_row(threshold: float, metrics: Any) -> dict[str, Any]:
    """Confusion Matrix에서 활성 클래스의 TP, FP, FN과 전체 지표를 계산한다."""
    matrix = metrics.confusion_matrix.matrix
    expected_size = max(ACTIVE_CLASS_IDS) + 2
    if matrix.ndim != 2 or min(matrix.shape) < expected_size:
        raise ValueError(
            "Confusion Matrix 크기가 활성 클래스와 background를 포함하지 않습니다: "
            f"{matrix.shape}"
        )

    tp_total = 0
    fp_total = 0
    fn_total = 0
    for class_id in ACTIVE_CLASS_IDS:
        true_positive = int(matrix[class_id][class_id])
        false_positive = int(matrix[class_id, :].sum() - true_positive)
        false_negative = int(matrix[:, class_id].sum() - true_positive)
        tp_total += true_positive
        fp_total += false_positive
        fn_total += false_negative

    predicted_count = tp_total + fp_total
    return {
        "threshold": f"{threshold:.2f}",
        "predicted_count": predicted_count,
        "tp": tp_total,
        "fp": fp_total,
        "fn": fn_total,
        "precision": safe_ratio(tp_total, predicted_count),
        "recall": safe_ratio(tp_total, tp_total + fn_total),
        "avg_labels_per_image": predicted_count / TEST_IMAGE_COUNT,
        "fp_to_remove": fp_total,
        "fn_to_add": fn_total,
        "ultra_mp": float(metrics.box.mp),
        "ultra_mr": float(metrics.box.mr),
        "ultra_map50": float(metrics.box.map50),
        "ultra_map50_95": float(metrics.box.map),
    }


def save_prediction_images(
    model: YOLO,
    image_paths: list[Path],
    threshold: float,
    prediction_project: Path,
) -> None:
    """단일 이미지 단위로 예측해 실패를 격리하고 시각화 결과를 저장한다."""
    output_name = f"conf_{threshold:.2f}"
    failures: list[Path] = []

    for index, image_path in enumerate(image_paths, start=1):
        try:
            model.predict(
                source=str(image_path),
                conf=threshold,
                iou=IOU_THRESHOLD,
                imgsz=IMAGE_SIZE,
                device=DEVICE,
                save=True,
                project=str(prediction_project),
                name=output_name,
                exist_ok=True,
            )
            LOGGER.info(
                "예측 이미지 저장 [%d/%d] - threshold=%.2f, image=%s",
                index,
                len(image_paths),
                threshold,
                image_path.name,
            )
        except Exception:
            failures.append(image_path)
            LOGGER.exception(
                "예측 이미지 저장 실패 [%d/%d] - threshold=%.2f, image=%s",
                index,
                len(image_paths),
                threshold,
                image_path.name,
            )

    if failures:
        LOGGER.error(
            "Threshold %.2f 예측 이미지 저장 실패 합계=%d, images=%s",
            threshold,
            len(failures),
            ", ".join(path.name for path in failures),
        )


def write_comparison_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Threshold 비교 결과를 UTF-8 CSV 파일로 저장한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def compare_thresholds(project_root: Path) -> list[dict[str, Any]]:
    """고정된 평가 설정에서 네 개 Confidence Threshold를 순서대로 비교한다."""
    model_path = require_file(
        (project_root / "experiments" / EXPERIMENT_ID / "models" / "best.pt").resolve()
    )
    data_path = require_file(
        (project_root / "data" / "processed" / "dataset_v4" / "data.yaml").resolve()
    )
    image_paths = load_test_images(
        project_root / "data" / "processed" / "dataset_v4" / "images" / "test"
    )
    metrics_project = (
        project_root / "outputs" / EXPERIMENT_ID / "threshold-comparison" / "metrics"
    ).resolve()
    prediction_project = (
        project_root / "outputs" / EXPERIMENT_ID / "threshold-comparison" / "images"
    ).resolve()
    model = YOLO(str(model_path))
    rows: list[dict[str, Any]] = []

    for threshold in CONFIDENCE_THRESHOLDS:
        output_name = f"conf_{threshold:.2f}"
        LOGGER.info("Threshold 평가 시작 - threshold=%.2f", threshold)
        metrics = model.val(
            data=str(data_path),
            split="test",
            conf=threshold,
            iou=IOU_THRESHOLD,
            imgsz=IMAGE_SIZE,
            device=DEVICE,
            plots=True,
            project=str(metrics_project),
            name=output_name,
            exist_ok=True,
            verbose=False,
        )
        rows.append(build_comparison_row(threshold, metrics))
        save_prediction_images(
            model=model,
            image_paths=image_paths,
            threshold=threshold,
            prediction_project=prediction_project,
        )
        LOGGER.info("Threshold 평가 완료 - threshold=%.2f", threshold)

    return rows


def main() -> None:
    """프로젝트 경로를 설정하고 Threshold 비교표와 예측 이미지를 생성한다."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    project_root = Path(__file__).resolve().parents[3]
    report_path = (
        project_root
        / "reports"
        / "evaluation"
        / EXPERIMENT_ID
        / "threshold_comparison.csv"
    )
    rows = compare_thresholds(project_root)
    write_comparison_csv(report_path, rows)
    LOGGER.info("Threshold 비교 완료 - report=%s", report_path)


if __name__ == "__main__":
    main()
