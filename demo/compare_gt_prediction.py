import json
import logging
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.image_utils import read_image  # noqa: E402
from common.json_utils import load_json  # noqa: E402
from visualization.exp5.visualize_prediction import (  # noqa: E402
    parse_yolo_line,
    restore_box,
)

LOGGER = logging.getLogger(__name__)
EXPERIMENT_ID = "EXP-P1-DET-005"
IMAGE_ROOT = PROJECT_ROOT / "data" / "processed" / "dataset_v3" / "images" / "test"
GT_LABEL_ROOT = PROJECT_ROOT / "data" / "processed" / "dataset_v3" / "labels" / "test"
PREDICTIONS_PATH = (
    PROJECT_ROOT / "predictions" / EXPERIMENT_ID / "prediction_results.json"
)
CLASS_NAMES_PATH = PROJECT_ROOT / "metadata" / "yolo_classes.txt"
OUTPUT_ROOT = PROJECT_ROOT / "demo" / "comparison-images"

DEMO_CASES = [
    ("RT_AL_02_14489691.jpg", "성공 사례: porosity 2건 모두 정확히 검출"),
    ("RT_AL_05_14492165.jpg", "성공 사례: slag_inclusion 정확히 검출"),
    ("RT_AL_02_14488212.jpg", "실패 사례(미탐): Small porosity 놓침"),
    (
        "RT_AL_05_14492954.jpg",
        "실패 사례(위치 오류): 예측 박스가 GT보다 작게 그려짐",
    ),
]

GT_COLOR = (0, 200, 0)
PREDICTION_COLOR = (0, 0, 255)
TEXT_COLOR = (255, 255, 255)
DIVIDER_WIDTH = 4
CASE_BANNER_HEIGHT = 50


# 클래스 ID 순서대로 클래스명 목록을 읽습니다.
def load_class_names() -> list[str]:
    class_names = [
        line.strip()
        for line in CLASS_NAMES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not class_names:
        raise ValueError(f"클래스 목록이 비어 있습니다: {CLASS_NAMES_PATH}")
    return class_names


# 예측 JSON의 이미지 레코드를 이미지명으로 인덱싱합니다.
def index_prediction_records(data: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("images"), list):
        raise TypeError(f"예측 JSON 형식이 올바르지 않습니다: {PREDICTIONS_PATH}")

    records: dict[str, dict[str, Any]] = {}
    for record in data["images"]:
        if not isinstance(record, dict):
            raise TypeError("예측 이미지 레코드는 객체여야 합니다.")
        image_name = str(record["image_name"])
        if image_name in records:
            raise ValueError(f"중복 이미지명: {image_name}")
        records[image_name] = record
    return records


# GT 라벨 파일을 YOLO 라벨 튜플 목록으로 변환합니다.
def load_gt_labels(
    label_path: Path,
) -> list[tuple[int, float, float, float, float]]:
    labels = []
    for line_number, line in enumerate(
        label_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        try:
            labels.append(parse_yolo_line(line))
        except ValueError as error:
            raise ValueError(
                f"잘못된 GT 라벨: {label_path}:{line_number} ({error})"
            ) from error
    return labels


# 박스와 라벨 텍스트를 지정한 색상으로 이미지에 그립니다.
def draw_labeled_box(
    image: np.ndarray,
    box: tuple[float, float, float, float],
    label_text: str,
    color: tuple[int, int, int],
) -> None:
    x_min, y_min, x_max, y_max = box
    top_left = (int(round(x_min)), int(round(y_min)))
    bottom_right = (int(round(x_max)), int(round(y_max)))
    cv2.rectangle(image, top_left, bottom_right, color, 3, cv2.LINE_AA)
    cv2.putText(
        image,
        label_text,
        (max(0, top_left[0]), max(22, top_left[1] - 6)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        color,
        2,
        cv2.LINE_AA,
    )


# GT 박스와 클래스명을 원본 이미지 사본에 표시합니다.
def create_gt_panel(
    image: np.ndarray,
    labels: list[tuple[int, float, float, float, float]],
    class_names: list[str],
) -> np.ndarray:
    panel = image.copy()
    height, width = panel.shape[:2]
    for label in labels:
        class_id = label[0]
        if not 0 <= class_id < len(class_names):
            raise ValueError(f"GT class_id 범위 오류: {class_id}")
        draw_labeled_box(
            panel,
            restore_box(label, width, height),
            class_names[class_id],
            GT_COLOR,
        )
    draw_panel_title(panel, "GT")
    return panel


# 예측 박스와 클래스명·신뢰도를 원본 이미지 사본에 표시합니다.
def create_prediction_panel(
    image: np.ndarray,
    predictions: list[dict[str, Any]],
) -> np.ndarray:
    panel = image.copy()
    height, width = panel.shape[:2]
    for prediction in predictions:
        coordinates = prediction["bbox_normalized_xywh"]
        if not isinstance(coordinates, list) or len(coordinates) != 4:
            raise ValueError("예측 bbox_normalized_xywh 형식이 올바르지 않습니다.")
        normalized_box = (0, *(float(value) for value in coordinates))
        label_text = f"{prediction['class_name']} {float(prediction['confidence']):.3f}"
        draw_labeled_box(
            panel,
            restore_box(normalized_box, width, height),
            label_text,
            PREDICTION_COLOR,
        )
    draw_panel_title(panel, "Prediction")
    return panel


# 패널 좌측 상단에 패널 이름을 표시합니다.
def draw_panel_title(panel: np.ndarray, title: str) -> None:
    cv2.putText(
        panel,
        title,
        (12, 34),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        TEXT_COLOR,
        2,
        cv2.LINE_AA,
    )


# 두 패널을 구분선과 함께 연결하고 상단에 케이스 라벨을 표시합니다.
def compose_comparison(
    gt_panel: np.ndarray,
    prediction_panel: np.ndarray,
    case_label: str,
) -> np.ndarray:
    divider = np.full(
        (gt_panel.shape[0], DIVIDER_WIDTH, 3),
        255,
        dtype=np.uint8,
    )
    panels = cv2.hconcat([gt_panel, divider, prediction_panel])
    banner = np.zeros(
        (CASE_BANNER_HEIGHT, panels.shape[1], 3),
        dtype=np.uint8,
    )
    cv2.putText(
        banner,
        case_label,
        (12, 34),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        TEXT_COLOR,
        2,
        cv2.LINE_AA,
    )
    return cv2.vconcat([banner, panels])


# Unicode 경로를 지원하도록 JPEG 인코딩 후 바이트로 저장합니다.
def save_image(image: np.ndarray, output_path: Path) -> None:
    success, encoded = cv2.imencode(".jpg", image)
    if not success:
        raise OSError(f"JPEG 인코딩 실패: {output_path}")
    output_path.write_bytes(encoded.tobytes())


# 단일 데모 케이스의 GT·예측 비교 이미지를 생성합니다.
def process_case(
    image_name: str,
    case_label: str,
    prediction_records: dict[str, dict[str, Any]],
    class_names: list[str],
) -> bool:
    label_path = GT_LABEL_ROOT / f"{Path(image_name).stem}.txt"
    if not label_path.is_file():
        LOGGER.error("GT 라벨 파일이 없습니다: %s", label_path)
        return False

    record = prediction_records.get(image_name)
    if record is None:
        LOGGER.error("예측 레코드가 없습니다: %s", image_name)
        return False

    image = read_image(IMAGE_ROOT / image_name)
    if image is None:
        LOGGER.error("원본 이미지를 읽을 수 없습니다: %s", IMAGE_ROOT / image_name)
        return False

    predictions = record.get("predictions")
    if not isinstance(predictions, list):
        raise TypeError(f"예측 목록 형식이 올바르지 않습니다: {image_name}")

    gt_labels = load_gt_labels(label_path)
    gt_panel = create_gt_panel(image, gt_labels, class_names)
    prediction_panel = create_prediction_panel(image, predictions)
    comparison = compose_comparison(gt_panel, prediction_panel, case_label)
    save_image(comparison, OUTPUT_ROOT / image_name)
    return True


# 선정된 네 건의 GT·예측 비교 이미지 생성을 실행합니다.
def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
    )
    try:
        prediction_records = index_prediction_records(load_json(PREDICTIONS_PATH))
        class_names = load_class_names()
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        success_count = sum(
            process_case(
                image_name,
                case_label,
                prediction_records,
                class_names,
            )
            for image_name, case_label in DEMO_CASES
        )
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
        cv2.error,
    ) as error:
        LOGGER.exception("비교 이미지 생성 실패 (%s)", error)
        return 1

    LOGGER.info("비교 이미지 생성 완료: %d/%d", success_count, len(DEMO_CASES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
