"""Baseline 모델의 Test 성능과 객체 크기별 Recall을 계산한다."""

from __future__ import annotations

import csv
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from ultralytics import YOLO

LOGGER = logging.getLogger(__name__)

EXPERIMENT_ID = "EXP-P1-DET-001"
CONFIDENCE_THRESHOLD = 0.25
NMS_IOU_THRESHOLD = 0.70
MATCH_IOU_THRESHOLD = 0.5
IMAGE_SIZE = 640
DEVICE = "cpu"
EXPECTED_IMAGE_COUNT = 46
SIZE_BUCKETS = ("Small", "Medium", "Large")
IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}

MODEL_PERFORMANCE_FIELDS = (
    "scope",
    "class_name",
    "precision",
    "recall",
    "ap50",
    "ap50_95",
)
OBJECT_SIZE_FIELDS = ("size_bucket", "gt_count", "tp", "fn", "recall")


@dataclass(frozen=True)
class GroundTruth:
    """단일 GT 객체의 클래스, 정규화 좌표, 크기 버킷을 보관한다."""

    class_id: int
    xywh: tuple[float, float, float, float]
    size_bucket: str


@dataclass(frozen=True)
class Prediction:
    """단일 예측 객체의 클래스, Confidence, 픽셀 좌표를 보관한다."""

    class_id: int
    confidence: float
    xyxy: tuple[float, float, float, float]


def require_file(path: Path) -> Path:
    """필수 입력 파일의 존재를 확인한다."""
    if not path.is_file():
        raise FileNotFoundError(f"필수 파일이 없습니다: {path}")
    return path


def load_class_names(path: Path) -> dict[int, str]:
    """YOLO 클래스 파일에서 ID와 클래스명 매핑을 읽는다."""
    class_names = {
        class_id: line.strip()
        for class_id, line in enumerate(
            require_file(path).read_text(encoding="utf-8-sig").splitlines()
        )
        if line.strip()
    }
    if not class_names:
        raise ValueError(f"클래스 이름 파일이 비어 있습니다: {path}")
    return class_names


def load_test_images(test_dir: Path) -> list[Path]:
    """Test 이미지 파일을 이름순으로 읽고 예상 수량을 검증한다."""
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
    if len(image_paths) != EXPECTED_IMAGE_COUNT:
        raise ValueError(
            "Test 이미지 수가 예상과 다릅니다: "
            f"expected={EXPECTED_IMAGE_COUNT}, actual={len(image_paths)}"
        )
    if len({path.stem for path in image_paths}) != len(image_paths):
        raise ValueError("Test 이미지에 확장자를 제외한 파일명이 중복됩니다.")
    return image_paths


def classify_size(relative_area: float) -> str:
    """작업12 기준으로 객체의 상대 면적을 크기 버킷으로 분류한다."""
    if relative_area < 0.01:
        return "Small"
    if relative_area < 0.05:
        return "Medium"
    return "Large"


def parse_label_line(
    line: str,
    label_path: Path,
    line_number: int,
    class_names: dict[int, str],
) -> GroundTruth:
    """YOLO 라벨 한 줄을 검증하고 GT 객체로 변환한다."""
    fields = line.split()
    if len(fields) != 5:
        raise ValueError(f"YOLO 라벨 필드가 5개가 아닙니다: {label_path}:{line_number}")
    try:
        class_id = int(fields[0])
        center_x, center_y, width, height = map(float, fields[1:])
    except ValueError as error:
        raise ValueError(
            f"YOLO 라벨에 숫자가 아닌 값이 있습니다: {label_path}:{line_number}"
        ) from error

    if class_id not in class_names:
        raise ValueError(
            f"클래스 매핑에 없는 GT ID입니다: {label_path}:{line_number}: {class_id}"
        )
    if not all(0.0 <= value <= 1.0 for value in (center_x, center_y, width, height)):
        raise ValueError(
            f"정규화 좌표가 0~1 범위를 벗어났습니다: {label_path}:{line_number}"
        )
    if width <= 0.0 or height <= 0.0:
        raise ValueError(f"GT 너비 또는 높이가 0입니다: {label_path}:{line_number}")

    return GroundTruth(
        class_id=class_id,
        xywh=(center_x, center_y, width, height),
        size_bucket=classify_size(width * height),
    )


def load_ground_truths(
    label_dir: Path,
    image_paths: list[Path],
    class_names: dict[int, str],
) -> dict[str, list[GroundTruth]]:
    """모든 Test 이미지와 일대일 대응하는 YOLO GT 라벨을 읽는다."""
    if not label_dir.is_dir():
        raise FileNotFoundError(f"Test 라벨 디렉터리가 없습니다: {label_dir}")

    label_paths = sorted(label_dir.glob("*.txt"), key=lambda path: path.name)
    image_stems = {path.stem for path in image_paths}
    label_stems = {path.stem for path in label_paths}
    if image_stems != label_stems:
        raise ValueError(
            "Test 이미지와 라벨 파일이 일치하지 않습니다: "
            f"missing={sorted(image_stems - label_stems)}, "
            f"unexpected={sorted(label_stems - image_stems)}"
        )

    ground_truths: dict[str, list[GroundTruth]] = {}
    for label_path in label_paths:
        objects = []
        for line_number, line in enumerate(
            label_path.read_text(encoding="utf-8-sig").splitlines(),
            start=1,
        ):
            if line.strip():
                objects.append(
                    parse_label_line(
                        line,
                        label_path,
                        line_number,
                        class_names,
                    )
                )
        ground_truths[label_path.stem] = objects
    return ground_truths


def to_list(values: Any) -> list[Any]:
    """Tensor 또는 NumPy 배열을 일반 Python 리스트로 변환한다."""
    if hasattr(values, "tolist"):
        converted = values.tolist()
        return converted if isinstance(converted, list) else [converted]
    return list(values)


def scalar_values(values: Any) -> list[float]:
    """Ultralytics 지표 배열을 float 리스트로 변환한다."""
    return [float(value) for value in to_list(values)]


def get_active_class_ids(metrics: Any) -> list[int]:
    """Ultralytics 버전별 위치를 지원해 활성 클래스 ID를 읽는다."""
    class_indexes = getattr(metrics, "ap_class_index", None)
    if class_indexes is None:
        class_indexes = getattr(metrics.box, "ap_class_index", None)
    if class_indexes is None:
        raise AttributeError(
            "Ultralytics metrics에서 ap_class_index를 찾을 수 없습니다."
        )
    return [int(value) for value in to_list(class_indexes)]


def build_model_performance_rows(
    metrics: Any,
    class_names: dict[int, str],
) -> list[dict[str, str | float]]:
    """Ultralytics 전체·클래스별 지표를 CSV 행으로 구성한다."""
    rows: list[dict[str, str | float]] = [
        {
            "scope": "overall",
            "class_name": "all",
            "precision": float(metrics.box.mp),
            "recall": float(metrics.box.mr),
            "ap50": float(metrics.box.map50),
            "ap50_95": float(metrics.box.map),
        }
    ]

    active_class_ids = get_active_class_ids(metrics)
    precision = scalar_values(metrics.box.p)
    recall = scalar_values(metrics.box.r)
    ap50 = scalar_values(metrics.box.ap50)
    ap50_95 = scalar_values(metrics.box.ap)
    metric_lengths = {
        len(active_class_ids),
        len(precision),
        len(recall),
        len(ap50),
        len(ap50_95),
    }
    if len(metric_lengths) != 1:
        raise ValueError(
            "활성 클래스 ID와 클래스별 지표 배열의 길이가 일치하지 않습니다."
        )

    for index, class_id in enumerate(active_class_ids):
        if class_id not in class_names:
            raise ValueError(f"클래스 매핑에 없는 평가 ID입니다: {class_id}")
        rows.append(
            {
                "scope": "class",
                "class_name": class_names[class_id],
                "precision": precision[index],
                "recall": recall[index],
                "ap50": ap50[index],
                "ap50_95": ap50_95[index],
            }
        )
    return rows


def normalized_xywh_to_xyxy(
    xywh: tuple[float, float, float, float],
    image_height: int,
    image_width: int,
) -> tuple[float, float, float, float]:
    """정규화 YOLO 좌표를 원본 이미지의 픽셀 xyxy 좌표로 변환한다."""
    center_x, center_y, width, height = xywh
    half_width = width * image_width / 2.0
    half_height = height * image_height / 2.0
    center_x_pixels = center_x * image_width
    center_y_pixels = center_y * image_height
    return (
        center_x_pixels - half_width,
        center_y_pixels - half_height,
        center_x_pixels + half_width,
        center_y_pixels + half_height,
    )


def calculate_iou(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    """두 픽셀 xyxy Bounding Box의 IoU를 계산한다."""
    intersection_width = max(0.0, min(first[2], second[2]) - max(first[0], second[0]))
    intersection_height = max(0.0, min(first[3], second[3]) - max(first[1], second[1]))
    intersection = intersection_width * intersection_height
    first_area = max(0.0, first[2] - first[0]) * max(0.0, first[3] - first[1])
    second_area = max(0.0, second[2] - second[0]) * max(0.0, second[3] - second[1])
    union = first_area + second_area - intersection
    return intersection / union if union > 0.0 else 0.0


def extract_predictions(result: Any, class_names: dict[int, str]) -> list[Prediction]:
    """단일 Ultralytics 예측 결과에서 매칭에 필요한 값을 추출한다."""
    predictions = []
    for box in result.boxes:
        class_id = int(box.cls.item())
        if class_id not in class_names:
            raise ValueError(f"클래스 매핑에 없는 예측 ID입니다: {class_id}")
        xyxy_values = [float(value) for value in box.xyxy[0].tolist()]
        predictions.append(
            Prediction(
                class_id=class_id,
                confidence=float(box.conf.item()),
                xyxy=(
                    xyxy_values[0],
                    xyxy_values[1],
                    xyxy_values[2],
                    xyxy_values[3],
                ),
            )
        )
    return sorted(
        predictions,
        key=lambda prediction: prediction.confidence,
        reverse=True,
    )


def match_image(
    ground_truths: list[GroundTruth],
    predictions: list[Prediction],
    image_height: int,
    image_width: int,
) -> tuple[list[GroundTruth], list[GroundTruth]]:
    """Confidence 순 예측을 같은 클래스의 미매칭 GT와 IoU 0.5로 매칭한다."""
    gt_boxes = [
        normalized_xywh_to_xyxy(gt.xywh, image_height, image_width)
        for gt in ground_truths
    ]
    unmatched_gt_indexes = set(range(len(ground_truths)))
    matched_gt_indexes: set[int] = set()

    for prediction in predictions:
        candidates = [
            (calculate_iou(prediction.xyxy, gt_boxes[index]), index)
            for index in unmatched_gt_indexes
            if ground_truths[index].class_id == prediction.class_id
        ]
        if not candidates:
            continue
        best_iou, best_index = max(candidates, key=lambda candidate: candidate[0])
        if best_iou >= MATCH_IOU_THRESHOLD:
            unmatched_gt_indexes.remove(best_index)
            matched_gt_indexes.add(best_index)

    matched = [ground_truths[index] for index in sorted(matched_gt_indexes)]
    unmatched = [ground_truths[index] for index in sorted(unmatched_gt_indexes)]
    return matched, unmatched


def evaluate_object_sizes(
    model: YOLO,
    image_paths: list[Path],
    ground_truths_by_stem: dict[str, list[GroundTruth]],
    class_names: dict[int, str],
) -> list[dict[str, str | int | float]]:
    """Test 이미지를 개별 추론하고 GT 크기 버킷별 Recall을 집계한다."""
    counts = {bucket: {"tp": 0, "fn": 0} for bucket in SIZE_BUCKETS}
    for index, image_path in enumerate(image_paths, start=1):
        results = model.predict(
            source=str(image_path),
            conf=CONFIDENCE_THRESHOLD,
            iou=NMS_IOU_THRESHOLD,
            imgsz=IMAGE_SIZE,
            device=DEVICE,
            verbose=False,
        )
        if len(results) != 1:
            raise RuntimeError(
                f"단일 이미지의 추론 결과 수가 1개가 아닙니다: {len(results)}개"
            )
        result = results[0]
        image_height, image_width = map(int, result.orig_shape)
        predictions = extract_predictions(result, class_names)
        matched, unmatched = match_image(
            ground_truths_by_stem[image_path.stem],
            predictions,
            image_height,
            image_width,
        )
        for ground_truth in matched:
            counts[ground_truth.size_bucket]["tp"] += 1
        for ground_truth in unmatched:
            counts[ground_truth.size_bucket]["fn"] += 1
        LOGGER.info(
            "크기별 평가 진행 [%d/%d] - %s, gt=%d, predictions=%d",
            index,
            len(image_paths),
            image_path.name,
            len(ground_truths_by_stem[image_path.stem]),
            len(predictions),
        )

    rows: list[dict[str, str | int | float]] = []
    for bucket in SIZE_BUCKETS:
        true_positives = counts[bucket]["tp"]
        false_negatives = counts[bucket]["fn"]
        gt_count = true_positives + false_negatives
        rows.append(
            {
                "size_bucket": bucket,
                "gt_count": gt_count,
                "tp": true_positives,
                "fn": false_negatives,
                "recall": true_positives / gt_count if gt_count else 0.0,
            }
        )
    return rows


def write_csv(
    path: Path,
    field_names: Iterable[str],
    rows: list[dict[str, str | int | float]],
) -> None:
    """평가 결과 행을 UTF-8 CSV 파일로 저장한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    """Ultralytics 공식 평가와 객체 크기별 평가를 실행해 CSV로 저장한다."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        stream=sys.stdout,
    )
    project_root = Path(__file__).resolve().parents[3]
    model_path = require_file(
        (project_root / "experiments" / EXPERIMENT_ID / "models" / "best.pt").resolve()
    )
    dataset_root = project_root / "data" / "processed" / "dataset_v1"
    data_yaml = require_file((dataset_root / "data.yaml").resolve())
    image_paths = load_test_images(dataset_root / "images" / "test")
    class_names = load_class_names(project_root / "metadata" / "yolo_classes.txt")
    ground_truths = load_ground_truths(
        dataset_root / "labels" / "test",
        image_paths,
        class_names,
    )
    report_dir = (project_root / "reports" / "evaluation").resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    model = YOLO(str(model_path))
    LOGGER.info("Ultralytics Test 평가 시작 - model=%s", model_path)
    metrics = model.val(
        data=str(data_yaml),
        split="test",
        conf=CONFIDENCE_THRESHOLD,
        iou=NMS_IOU_THRESHOLD,
        imgsz=IMAGE_SIZE,
        device=DEVICE,
        plots=True,
        project=str(report_dir),
        name="evaluation",
        exist_ok=True,
    )
    model_performance_path = report_dir / "model_performance.csv"
    write_csv(
        model_performance_path,
        MODEL_PERFORMANCE_FIELDS,
        build_model_performance_rows(metrics, class_names),
    )

    size_rows = evaluate_object_sizes(
        model,
        image_paths,
        ground_truths,
        class_names,
    )
    object_size_path = report_dir / "object_size_performance.csv"
    write_csv(object_size_path, OBJECT_SIZE_FIELDS, size_rows)

    confusion_matrix_path = report_dir / "evaluation" / "confusion_matrix.png"
    LOGGER.info("전체·클래스별 성능 저장: %s", model_performance_path)
    LOGGER.info("객체 크기별 성능 저장: %s", object_size_path)
    LOGGER.info("Confusion Matrix 이미지: %s", confusion_matrix_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
