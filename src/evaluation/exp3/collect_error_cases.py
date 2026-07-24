"""Baseline 모델의 Test 실패 사례를 객관적 오류 유형별로 수집한다."""

from __future__ import annotations

import csv
import logging
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.image_utils import read_image  # noqa: E402
from evaluation.exp3.calculate_metrics import (  # noqa: E402
    GroundTruth,
    Prediction,
    calculate_iou,
    extract_predictions,
    load_class_names,
    load_ground_truths,
    load_test_images,
    normalized_xywh_to_xyxy,
    require_file,
)

LOGGER = logging.getLogger(__name__)

EXPERIMENT_ID = "EXP-P1-DET-003"
CONFIDENCE_THRESHOLD = 0.25
NMS_IOU_THRESHOLD = 0.70
MATCH_IOU_THRESHOLD = 0.5
LOCALIZATION_IOU_THRESHOLD = 0.1
DUPLICATE_IOU_THRESHOLD = 0.3
EDGE_RATIO = 0.05
IMAGE_SIZE = 960
DEVICE = "cpu"
ERROR_TYPES = (
    "false_positive",
    "false_negative",
    "wrong_class",
    "localization_error",
)
ERROR_CASE_FIELDS = (
    "case_id",
    "image_name",
    "error_type",
    "gt_class",
    "gt_size_bucket",
    "pred_class",
    "confidence",
    "box_area_ratio",
    "near_edge",
    "duplicate_of_tp",
    "case_image_path",
)
ERROR_COUNT_FIELDS = ("error_type", "class_name", "count")
GT_COLOR = (0, 255, 0)
PREDICTION_COLOR = (255, 0, 255)
TEXT_COLOR = (255, 255, 255)


@dataclass(frozen=True)
class ErrorCase:
    """단일 실패 사례의 오류 유형과 연결된 GT·예측을 보관한다."""

    error_type: str
    ground_truth: GroundTruth | None
    gt_box: tuple[float, float, float, float] | None
    prediction: Prediction | None
    duplicate_of_tp: bool = False


def find_best_gt(
    prediction: Prediction,
    ground_truths: list[GroundTruth],
    gt_boxes: list[tuple[float, float, float, float]],
    available_gt_indexes: set[int],
    *,
    same_class: bool | None,
    minimum_iou: float,
    maximum_iou: float | None = None,
) -> int | None:
    """현재 매칭 단계의 조건을 만족하는 최대 IoU GT 인덱스를 찾는다."""
    candidates: list[tuple[float, int]] = []
    for gt_index in available_gt_indexes:
        classes_match = ground_truths[gt_index].class_id == prediction.class_id
        if same_class is not None and classes_match != same_class:
            continue
        iou = calculate_iou(prediction.xyxy, gt_boxes[gt_index])
        if iou < minimum_iou:
            continue
        if maximum_iou is not None and iou >= maximum_iou:
            continue
        candidates.append((iou, gt_index))
    if not candidates:
        return None
    return max(candidates, key=lambda candidate: (candidate[0], -candidate[1]))[1]


def match_stage(
    predictions: list[Prediction],
    ground_truths: list[GroundTruth],
    gt_boxes: list[tuple[float, float, float, float]],
    available_prediction_indexes: set[int],
    available_gt_indexes: set[int],
    *,
    same_class: bool | None,
    minimum_iou: float,
    maximum_iou: float | None = None,
) -> list[tuple[int, int]]:
    """Confidence 순으로 한 단계의 조건에 맞는 예측·GT 쌍을 그리디 매칭한다."""
    matches: list[tuple[int, int]] = []
    for prediction_index, prediction in enumerate(predictions):
        if prediction_index not in available_prediction_indexes:
            continue
        gt_index = find_best_gt(
            prediction,
            ground_truths,
            gt_boxes,
            available_gt_indexes,
            same_class=same_class,
            minimum_iou=minimum_iou,
            maximum_iou=maximum_iou,
        )
        if gt_index is None:
            continue
        available_prediction_indexes.remove(prediction_index)
        available_gt_indexes.remove(gt_index)
        matches.append((prediction_index, gt_index))
    return matches


def classify_errors(
    ground_truths: list[GroundTruth],
    predictions: list[Prediction],
    image_height: int,
    image_width: int,
) -> list[ErrorCase]:
    """TP, 클래스 오류, 위치 오류, FP·FN 순서로 객체를 분류한다."""
    gt_boxes = [
        normalized_xywh_to_xyxy(gt.xywh, image_height, image_width)
        for gt in ground_truths
    ]
    available_predictions = set(range(len(predictions)))
    available_ground_truths = set(range(len(ground_truths)))

    tp_matches = match_stage(
        predictions,
        ground_truths,
        gt_boxes,
        available_predictions,
        available_ground_truths,
        same_class=True,
        minimum_iou=MATCH_IOU_THRESHOLD,
    )
    wrong_class_matches = match_stage(
        predictions,
        ground_truths,
        gt_boxes,
        available_predictions,
        available_ground_truths,
        same_class=False,
        minimum_iou=MATCH_IOU_THRESHOLD,
    )
    localization_matches = match_stage(
        predictions,
        ground_truths,
        gt_boxes,
        available_predictions,
        available_ground_truths,
        same_class=True,
        minimum_iou=LOCALIZATION_IOU_THRESHOLD,
        maximum_iou=MATCH_IOU_THRESHOLD,
    )

    cases = [
        ErrorCase("wrong_class", ground_truths[gt], gt_boxes[gt], predictions[pred])
        for pred, gt in wrong_class_matches
    ]
    cases.extend(
        ErrorCase(
            "localization_error",
            ground_truths[gt],
            gt_boxes[gt],
            predictions[pred],
        )
        for pred, gt in localization_matches
    )

    tp_predictions = [predictions[pred] for pred, _ in tp_matches]
    for prediction_index in sorted(available_predictions):
        prediction = predictions[prediction_index]
        duplicate_of_tp = any(
            prediction.class_id == tp_prediction.class_id
            and calculate_iou(prediction.xyxy, tp_prediction.xyxy)
            >= DUPLICATE_IOU_THRESHOLD
            for tp_prediction in tp_predictions
        )
        cases.append(
            ErrorCase(
                "false_positive",
                None,
                None,
                prediction,
                duplicate_of_tp,
            )
        )
    cases.extend(
        ErrorCase("false_negative", ground_truths[index], gt_boxes[index], None)
        for index in sorted(available_ground_truths)
    )
    return cases


def is_near_edge(
    box: tuple[float, float, float, float],
    image_height: int,
    image_width: int,
) -> bool:
    """Box 경계가 이미지 가장자리의 5% 이내인지 확인한다."""
    x_min, y_min, x_max, y_max = box
    return (
        x_min <= image_width * EDGE_RATIO
        or y_min <= image_height * EDGE_RATIO
        or x_max >= image_width * (1.0 - EDGE_RATIO)
        or y_max >= image_height * (1.0 - EDGE_RATIO)
    )


def box_area_ratio(
    box: tuple[float, float, float, float],
    image_height: int,
    image_width: int,
) -> float:
    """예측 Box 면적이 원본 이미지에서 차지하는 비율을 계산한다."""
    width = max(0.0, box[2] - box[0])
    height = max(0.0, box[3] - box[1])
    return width * height / (image_width * image_height)


def draw_labeled_box(
    image: np.ndarray,
    box: tuple[float, float, float, float],
    label: str,
    color: tuple[int, int, int],
) -> None:
    """이미지에 Bounding Box와 객체 라벨을 그린다."""
    image_height, image_width = image.shape[:2]
    x_min, y_min, x_max, y_max = (int(round(value)) for value in box)
    top_left = (
        min(max(x_min, 0), image_width - 1),
        min(max(y_min, 0), image_height - 1),
    )
    bottom_right = (
        min(max(x_max, 0), image_width - 1),
        min(max(y_max, 0), image_height - 1),
    )
    cv2.rectangle(image, top_left, bottom_right, color, 2, cv2.LINE_AA)
    label_origin = (top_left[0], max(45, top_left[1] - 6))
    cv2.putText(
        image,
        label,
        label_origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color,
        2,
        cv2.LINE_AA,
    )


def visualize_case(
    image: np.ndarray,
    image_name: str,
    error_case: ErrorCase,
    class_names: dict[int, str],
) -> np.ndarray:
    """원본 이미지에 사례의 GT와 예측 Box 및 오류 유형을 표시한다."""
    visualization = image.copy()
    if error_case.gt_box is not None and error_case.ground_truth is not None:
        gt_name = class_names[error_case.ground_truth.class_id]
        draw_labeled_box(visualization, error_case.gt_box, f"GT: {gt_name}", GT_COLOR)
    if error_case.prediction is not None:
        prediction = error_case.prediction
        pred_name = class_names[prediction.class_id]
        draw_labeled_box(
            visualization,
            prediction.xyxy,
            f"Pred: {pred_name} {prediction.confidence:.3f}",
            PREDICTION_COLOR,
        )
    cv2.putText(
        visualization,
        f"{image_name} | {error_case.error_type}",
        (10, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        TEXT_COLOR,
        2,
        cv2.LINE_AA,
    )
    return visualization


def save_image(image: np.ndarray, output_path: Path) -> None:
    """Unicode 경로를 지원하도록 JPEG 인코딩 결과를 바이트로 저장한다."""
    success, encoded = cv2.imencode(".jpg", image)
    if not success:
        raise OSError(f"JPEG 인코딩에 실패했습니다: {output_path}")
    output_path.write_bytes(encoded.tobytes())


def write_csv(
    path: Path,
    field_names: Iterable[str],
    rows: list[dict[str, str | int | float | bool]],
) -> None:
    """고정된 컬럼 순서로 UTF-8 CSV 파일을 저장한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(rows)


def prepare_error_directories(error_root: Path) -> dict[str, Path]:
    """오류 유형별 출력 폴더를 만들고 이전 생성 JPEG를 제거한다."""
    directories = {}
    for error_type in ERROR_TYPES:
        directory = error_root / error_type
        directory.mkdir(parents=True, exist_ok=True)
        for old_image in directory.glob("*.jpg"):
            old_image.unlink()
        directories[error_type] = directory
    return directories


def build_case_row(
    case_id: str,
    image_name: str,
    error_case: ErrorCase,
    class_names: dict[int, str],
    image_height: int,
    image_width: int,
    case_image_path: Path,
) -> dict[str, str | int | float | bool]:
    """실패 사례의 객관적 보조 정보를 CSV 행으로 구성한다."""
    gt = error_case.ground_truth
    prediction = error_case.prediction
    candidate_boxes = (
        error_case.gt_box,
        prediction.xyxy if prediction else None,
    )
    available_boxes = [box for box in candidate_boxes if box]
    return {
        "case_id": case_id,
        "image_name": image_name,
        "error_type": error_case.error_type,
        "gt_class": class_names[gt.class_id] if gt else "",
        "gt_size_bucket": gt.size_bucket if gt else "",
        "pred_class": class_names[prediction.class_id] if prediction else "",
        "confidence": f"{prediction.confidence:.6f}" if prediction else "",
        "box_area_ratio": (
            f"{box_area_ratio(prediction.xyxy, image_height, image_width):.8f}"
            if prediction
            else ""
        ),
        "near_edge": any(
            is_near_edge(box, image_height, image_width) for box in available_boxes
        ),
        "duplicate_of_tp": (
            error_case.duplicate_of_tp
            if error_case.error_type == "false_positive"
            else False
        ),
        "case_image_path": case_image_path.relative_to(PROJECT_ROOT).as_posix(),
    }


def collect_cases(
    model: YOLO,
    image_paths: list[Path],
    ground_truths_by_stem: dict[str, list[GroundTruth]],
    class_names: dict[int, str],
    error_directories: dict[str, Path],
) -> list[dict[str, str | int | float | bool]]:
    """Test 이미지 전체를 추론해 실패 사례 이미지와 CSV 행을 생성한다."""
    rows: list[dict[str, str | int | float | bool]] = []
    for image_index, image_path in enumerate(image_paths, start=1):
        image = read_image(image_path)
        if image is None:
            raise OSError(f"이미지 읽기에 실패했습니다: {image_path}")
        image_height, image_width = image.shape[:2]
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
                f"단일 이미지의 추론 결과 수가 1개가 아닙니다: {image_path}: "
                f"{len(results)}개"
            )
        result_height, result_width = map(int, results[0].orig_shape)
        if (result_height, result_width) != (image_height, image_width):
            raise ValueError(f"추론 결과와 원본 이미지 크기가 다릅니다: {image_path}")
        predictions = extract_predictions(results[0], class_names)
        error_cases = classify_errors(
            ground_truths_by_stem[image_path.stem],
            predictions,
            image_height,
            image_width,
        )
        for case_number, error_case in enumerate(error_cases, start=1):
            case_id = f"{image_path.stem}_{case_number:03d}"
            case_image_path = (
                error_directories[error_case.error_type] / f"{case_id}.jpg"
            )
            visualization = visualize_case(
                image,
                image_path.name,
                error_case,
                class_names,
            )
            save_image(visualization, case_image_path)
            rows.append(
                build_case_row(
                    case_id,
                    image_path.name,
                    error_case,
                    class_names,
                    image_height,
                    image_width,
                    case_image_path,
                )
            )
        LOGGER.info(
            "실패 사례 수집 [%d/%d] - %s, gt=%d, predictions=%d, errors=%d",
            image_index,
            len(image_paths),
            image_path.name,
            len(ground_truths_by_stem[image_path.stem]),
            len(predictions),
            len(error_cases),
        )
    return rows


def build_count_rows(
    case_rows: list[dict[str, str | int | float | bool]],
) -> list[dict[str, str | int | float | bool]]:
    """오류 유형과 대표 클래스별 사례 건수를 집계한다."""
    counts = Counter(
        (
            str(row["error_type"]),
            str(row["gt_class"] or row["pred_class"]),
        )
        for row in case_rows
    )
    return [
        {"error_type": error_type, "class_name": class_name, "count": count}
        for (error_type, class_name), count in sorted(counts.items())
    ]


def main() -> int:
    """고정된 작업23 평가 조건으로 Test 실패 사례를 수집한다."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        stream=sys.stdout,
    )
    model_path = require_file(
        PROJECT_ROOT / "experiments" / EXPERIMENT_ID / "models" / "best.pt"
    )
    dataset_root = PROJECT_ROOT / "data" / "processed" / "dataset_v1"
    image_paths = load_test_images(dataset_root / "images" / "test")
    class_names = load_class_names(PROJECT_ROOT / "metadata" / "yolo_classes.txt")
    ground_truths = load_ground_truths(
        dataset_root / "labels" / "test",
        image_paths,
        class_names,
    )
    error_directories = prepare_error_directories(
        PROJECT_ROOT / "errors" / EXPERIMENT_ID
    )
    report_directory = PROJECT_ROOT / "reports" / "evaluation" / EXPERIMENT_ID

    LOGGER.info("실패 사례 수집 시작 - model=%s", model_path)
    model = YOLO(str(model_path))
    case_rows = collect_cases(
        model,
        image_paths,
        ground_truths,
        class_names,
        error_directories,
    )
    error_cases_path = report_directory / "error_cases.csv"
    error_counts_path = report_directory / "error_type_counts.csv"
    write_csv(error_cases_path, ERROR_CASE_FIELDS, case_rows)
    write_csv(error_counts_path, ERROR_COUNT_FIELDS, build_count_rows(case_rows))
    LOGGER.info("실패 사례 %d건 저장: %s", len(case_rows), error_cases_path)
    LOGGER.info("오류 유형·클래스별 집계 저장: %s", error_counts_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
