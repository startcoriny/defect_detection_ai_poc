"""YOLO26s Baseline 모델을 학습하고 정식 실험 기록을 생성한다."""

from __future__ import annotations

import csv
import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from time import monotonic
from typing import Any

import yaml
from ultralytics import YOLO

LOGGER = logging.getLogger(__name__)
EXPERIMENT_ID = "EXP-P1-DET-007"
EXPERIMENT_NAME = "RT_AL_YOLO26S_960_SlagOversample"
METRIC_COLUMNS = {
    "precision": "metrics/precision(B)",
    "recall": "metrics/recall(B)",
    "map50": "metrics/mAP50(B)",
    "map50_95": "metrics/mAP50-95(B)",
}
LOSS_COLUMNS = (
    "train/box_loss",
    "train/cls_loss",
    "train/l1_loss",
    "val/box_loss",
    "val/cls_loss",
    "val/l1_loss",
)
DEFERRED_SECTIONS = (
    "10. 추론 설정",
    "11. 전체·클래스별 성능",
    "12. Threshold 비교",
    "13. 정성 평가",
    "14. 원인 분석",
    "15. Baseline 비교",
    "16. 결론",
    "17. 다음 실험 계획",
)


def now_iso() -> str:
    """현재 로컬 시각을 시간대가 포함된 ISO 8601 문자열로 반환한다."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def configure_logging(logs_dir: Path) -> None:
    """콘솔과 파일에 Baseline 학습 로그를 함께 기록한다."""
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "train.log"
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


def prepare_experiment_files(project_root: Path, experiment_dir: Path) -> None:
    """실험 폴더를 만들고 기존 환경·데이터 요약 파일을 복사한다."""
    (experiment_dir / "models").mkdir(parents=True, exist_ok=True)
    (experiment_dir / "visualizations").mkdir(parents=True, exist_ok=True)

    environment_sources = (
        require_file(project_root / "configs" / "environment" / "environment_info.txt"),
        require_file(project_root / "configs" / "environment" / "package_versions.txt"),
    )
    environment_text = "\n\n".join(
        path.read_text(encoding="utf-8-sig").rstrip() for path in environment_sources
    )
    (experiment_dir / "environment.txt").write_text(
        f"{environment_text}\n",
        encoding="utf-8",
    )

    shutil.copy2(
        require_file(
            project_root / "reports" / "dataset" / "v2" / "split_distribution.csv"
        ),
        experiment_dir / "dataset_summary.csv",
    )


def get_git_value(project_root: Path, *arguments: str) -> str:
    """실행 시점의 Git 정보를 조회한다."""
    completed = subprocess.run(
        ["git", *arguments],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def count_dataset_images(dataset_dir: Path) -> dict[str, int]:
    """데이터셋 분할별 JPG 이미지 수를 직접 센다."""
    counts: dict[str, int] = {}
    for split in ("train", "val", "test"):
        image_dir = dataset_dir / "images" / split
        if not image_dir.is_dir():
            raise FileNotFoundError(f"이미지 분할 폴더가 없습니다: {image_dir}")
        counts[split] = sum(1 for path in image_dir.glob("*.jpg") if path.is_file())
    return counts


def load_dataset_classes(project_root: Path) -> dict[int, str]:
    """분할 요약에 실제 객체가 있는 클래스 정보를 메타데이터에서 읽는다."""
    active_class_ids: set[int] = set()
    summary_path = require_file(
        project_root / "reports" / "dataset" / "v2" / "split_distribution.csv"
    )
    with summary_path.open(encoding="utf-8-sig", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            if int(row["object_count"]) > 0:
                active_class_ids.add(int(row["class_id"]))

    classes: dict[int, str] = {}
    statistics_path = require_file(project_root / "metadata" / "class_statistics.csv")
    with statistics_path.open(encoding="utf-8-sig", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            class_id = int(row["class_id"])
            if class_id in active_class_ids:
                classes[class_id] = row["class_name"]

    if classes != {3: "porosity", 4: "slag_inclusion"}:
        raise ValueError(f"예상과 다른 데이터셋 클래스 구성입니다: {classes}")
    return classes


def load_split_summary(
    summary_path: Path,
) -> tuple[dict[str, int], dict[int, dict[str, int]]]:
    """분할별 객체 수와 클래스별 객체 분포를 읽는다."""
    split_objects = {"train": 0, "val": 0, "test": 0}
    class_objects: dict[int, dict[str, int]] = {}
    with summary_path.open(encoding="utf-8-sig", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            split = row["split"]
            class_id = int(row["class_id"])
            object_count = int(row["object_count"])
            split_objects[split] += object_count
            class_objects.setdefault(
                class_id,
                {"train": 0, "val": 0, "test": 0},
            )[split] = object_count
    return split_objects, class_objects


def read_results(results_path: Path) -> tuple[dict[str, float], dict[str, float]]:
    """results.csv에서 Ultralytics fitness 기준 Best 행과 마지막 행을 읽는다."""
    with require_file(results_path).open(
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        rows = [
            {key.strip(): value.strip() for key, value in row.items()}
            for row in csv.DictReader(csv_file)
        ]
    if not rows:
        raise ValueError(f"학습 결과가 비어 있습니다: {results_path}")

    required_columns = {"epoch", *METRIC_COLUMNS.values(), *LOSS_COLUMNS}
    missing_columns = required_columns.difference(rows[0])
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"results.csv 필수 컬럼 누락: {missing}")

    numeric_rows = [
        {key: float(value) for key, value in row.items() if value != ""} for row in rows
    ]
    # Detection fitness는 mAP50 10%, mAP50-95 90%로 best.pt를 선택한다.
    best_row = max(
        numeric_rows,
        key=lambda row: (
            0.1 * row[METRIC_COLUMNS["map50"]] + 0.9 * row[METRIC_COLUMNS["map50_95"]]
        ),
    )
    return best_row, numeric_rows[-1]


def copy_training_artifacts(run_dir: Path, experiment_dir: Path) -> None:
    """Ultralytics 학습 산출물을 정식 실험 폴더로 복사한다."""
    copies = {
        run_dir / "weights" / "best.pt": experiment_dir / "models" / "best.pt",
        run_dir / "weights" / "last.pt": experiment_dir / "models" / "last.pt",
        run_dir / "results.png": (experiment_dir / "visualizations" / "results.png"),
        run_dir
        / "confusion_matrix.png": (
            experiment_dir / "visualizations" / "confusion_matrix.png"
        ),
        run_dir / "args.yaml": experiment_dir / "train_config.yaml",
    }
    missing = [str(source) for source in copies if not source.is_file()]
    if missing:
        raise FileNotFoundError("학습 산출물 누락:\n" + "\n".join(missing))
    for source, destination in copies.items():
        shutil.copy2(source, destination)


def load_yaml(path: Path) -> dict[str, Any]:
    """YAML 파일을 매핑으로 읽는다."""
    with require_file(path).open(encoding="utf-8-sig") as yaml_file:
        value = yaml.safe_load(yaml_file)
    if not isinstance(value, dict):
        raise ValueError(f"YAML 최상위 값이 매핑이 아닙니다: {path}")
    return value


def build_experiment_data(
    *,
    project_root: Path,
    experiment_dir: Path,
    status: str,
    started_at: str,
    ended_at: str,
    git_commit: str,
    image_counts: dict[str, int],
    classes: dict[int, str],
    actual_batch: int | None = None,
    metrics: dict[str, float] | None = None,
) -> dict[str, Any]:
    """템플릿 스키마에 맞는 실험 메타데이터를 구성한다."""
    return {
        "experiment": {
            "id": EXPERIMENT_ID,
            "name": EXPERIMENT_NAME,
            "status": status,
            "type": "detection_training",
            "started_at": started_at,
            "ended_at": ended_at,
            "git_commit": git_commit,
        },
        "purpose": {
            "problem": (
                "AI-Hub RT·AL 데이터의 YOLO Detection 파이프라인이 "
                "정상적으로 학습되는지 검증한다."
            ),
            "hypothesis": (
                "Polygon을 Bounding Box로 변환한 데이터로 두 결함 클래스를 "
                "학습하고 재현 가능한 Baseline 성능을 얻을 수 있다."
            ),
            "success_criteria": (
                "학습이 정상 종료되고 best/last 모델과 Precision, Recall, "
                "mAP 지표가 기록된다."
            ),
        },
        "dataset": {
            "name": "ai_hub_welding_rt_al",
            "version": "dataset_v3",
            "inspection_type": "RT",
            "material": "AL",
            "classes": classes,
            "split": {
                "train": 0.70,
                "val": 0.15,
                "test": 0.15,
                "seed": 42,
            },
            "image_count": image_counts,
        },
        "model": {
            "library": "ultralytics",
            "task": "detect",
            "weights": "yolo26s.pt",
            "pretrained": True,
        },
        "training": {
            "epochs": 50,
            "patience": 15,
            "imgsz": 960,
            "requested_batch": -1,
            "actual_batch": actual_batch,
            "optimizer": "auto",
            "device": "cpu",
            "seed": 42,
            "deterministic": True,
        },
        "inference": {
            "confidence": None,
            "iou": None,
            "imgsz": None,
        },
        "metrics": metrics
        or {
            "precision": None,
            "recall": None,
            "map50": None,
            "map50_95": None,
        },
        "artifacts": {
            "best_model": str((experiment_dir / "models" / "best.pt").resolve()),
            "last_model": str((experiment_dir / "models" / "last.pt").resolve()),
            "results_directory": str((experiment_dir / "runs" / "train").resolve()),
            "prediction_json": None,
            "evaluation_report": None,
        },
        "conclusion": {
            "hypothesis_result": None,
            "adopted": False,
            "next_experiment": None,
        },
    }


def write_experiment_yaml(path: Path, data: dict[str, Any]) -> None:
    """실험 메타데이터를 YAML로 저장한다."""
    with path.open("w", encoding="utf-8") as yaml_file:
        yaml.safe_dump(
            data,
            yaml_file,
            allow_unicode=True,
            sort_keys=False,
        )


def format_duration(seconds: float) -> str:
    """초 단위 실행 시간을 읽기 쉬운 시·분·초 문자열로 변환한다."""
    total_seconds = int(round(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def metric_value(row: dict[str, float], name: str) -> str:
    """결과 행의 평가 지표를 고정 소수점 문자열로 변환한다."""
    return f"{row[METRIC_COLUMNS[name]]:.6f}"


def loss_value(row: dict[str, float], prefix: str) -> str:
    """Box·Class·L1 손실을 합산해 표시한다."""
    return f"{sum(row[f'{prefix}/{name}_loss'] for name in ('box', 'cls', 'l1')):.6f}"


def environment_markdown(environment_path: Path) -> str:
    """재사용한 환경 파일 내용을 Markdown 코드 블록으로 만든다."""
    content = environment_path.read_text(encoding="utf-8-sig").rstrip()
    return f"```text\n{content}\n```"


def write_experiment_markdown(
    *,
    project_root: Path,
    experiment_dir: Path,
    started_at: str,
    ended_at: str,
    elapsed_seconds: float,
    git_branch: str,
    git_commit: str,
    image_counts: dict[str, int],
    classes: dict[int, str],
    actual_args: dict[str, Any],
    best_row: dict[str, float],
    last_row: dict[str, float],
) -> None:
    """템플릿 3~9절과 후속 작업용 섹션 골격을 Markdown으로 기록한다."""
    summary_path = experiment_dir / "dataset_summary.csv"
    split_objects, class_objects = load_split_summary(summary_path)
    total_images = sum(image_counts.values())
    total_objects = sum(split_objects.values())
    final_epoch = int(last_row["epoch"]) + 1
    best_epoch = int(best_row["epoch"]) + 1
    early_stopping = "예" if final_epoch < 50 else "아니오"
    class_rows = "\n".join(
        (
            f"| {class_name} | {class_id} | "
            f"{class_objects[class_id]['train']} | "
            f"{class_objects[class_id]['val']} | "
            f"{class_objects[class_id]['test']} | "
            f"{sum(class_objects[class_id].values())} |"
        )
        for class_id, class_name in classes.items()
    )
    augmentation_rows = "\n".join(
        f"| {label} | library default ({actual_args.get(argument)}) | 아니오 |"
        for label, argument in (
            ("HSV Hue", "hsv_h"),
            ("HSV Saturation", "hsv_s"),
            ("HSV Value", "hsv_v"),
            ("Rotation", "degrees"),
            ("Translation", "translate"),
            ("Scale", "scale"),
            ("Horizontal Flip", "fliplr"),
            ("Vertical Flip", "flipud"),
            ("Mosaic", "mosaic"),
            ("MixUp", "mixup"),
        )
    )
    deferred = "\n\n".join(
        f"# {section}\n\n실험 후 작성(작업18~25에서 채움)"
        for section in DEFERRED_SECTIONS
    )
    result_rows = "\n".join(
        (f"| {label} | {formatter(best_row, key)} | " f"{formatter(last_row, key)} |")
        for label, formatter, key in (
            ("Train Loss (Box+Class+L1)", loss_value, "train"),
            ("Validation Loss (Box+Class+L1)", loss_value, "val"),
            ("Precision", metric_value, "precision"),
            ("Recall", metric_value, "recall"),
            ("mAP50", metric_value, "map50"),
            ("mAP50-95", metric_value, "map50_95"),
        )
    )
    markdown = f"""# 1. 실험 기본 정보

- 실험 ID: {EXPERIMENT_ID}
- 실험명: {EXPERIMENT_NAME}
- 실험 상태: COMPLETED
- 작성자: 자동 기록
- 실험 시작 일시: {started_at}
- 실험 종료 일시: {ended_at}
- 관련 단계: 작업17
- 실험 유형: DETECTION_TRAINING
- Git Branch: {git_branch}
- Git Commit: {git_commit}
- 설정 파일 경로: {experiment_dir / "train_config.yaml"}
- 결과 폴더 경로: {experiment_dir / "runs" / "train"}

# 2. 목적과 가설

- 실험 목적: AI-Hub RT·AL 데이터에서 Polygon을 Bounding Box로 변환한
  YOLO Detection 파이프라인이 정상적으로 학습되는지 검증한다.
- 검증할 핵심 질문: 새로운 Test 이미지에서 porosity와 slag_inclusion의
  위치를 예측할 수 있는 Baseline 성능을 얻을 수 있는가?
- 현재 문제: 전체 데이터셋으로 측정한 최초의 실제 성능 기준이 없다.
- 가설: 변환·검증된 dataset_v3로 두 결함 클래스를 학습하면 재현 가능한 최초 Baseline 지표를 얻을 수 있다.
- 예상 결과: 학습이 정상 종료되고 best/last 모델 및 Precision·Recall·mAP 지표가 생성된다.
- 성공 판단 기준: 예외 없이 정상 종료되고 필수 모델·로그·설정·시각화 산출물이 모두 보존된다.

# 3. 기준 실험

없음. 최초 Baseline.

# 5. 데이터셋 정보

## 5.1 데이터셋 식별

- 데이터셋 이름: ai_hub_welding_rt_al
- 데이터셋 버전: dataset_v3
- 데이터 출처: AI-Hub
- 검사 유형: RT
- 소재: AL
- 원본 라벨 형식: AI-Hub JSON Polygon
- 학습 라벨 형식: YOLO Detection
- 클래스 매핑: `metadata/yolo_classes.txt`
- 데이터 선정 목록: `metadata/v2/selected_dataset.csv`
- 데이터 검증 보고서: `reports/dataset/v2/`

## 5.2 데이터 수

| 구분 | 이미지 수 | 객체 수 |
| --- | ---: | ---: |
| Train | {image_counts["train"]} | {split_objects["train"]} |
| Validation | {image_counts["val"]} | {split_objects["val"]} |
| Test | {image_counts["test"]} | {split_objects["test"]} |
| 전체 | {total_images} | {total_objects} |

## 5.3 클래스별 객체 분포

| 클래스 | 클래스 ID | Train 객체 | Val 객체 | Test 객체 | 전체 객체 |
| --- | ---: | ---: | ---: | ---: | ---: |
{class_rows}

## 5.4 데이터 분할 정보

- Train/Validation/Test 비율: 0.70 / 0.15 / 0.15
- Random Seed: 42
- 분할 방법 및 상세 분포: `dataset_summary.csv`

# 6. 전처리·변환 정보

- Polygon → Bounding Box 변환: 작업9 산출물 참조
- YOLO Detection 라벨 변환: 작업10 산출물 참조
- Bounding Box 계산: Polygon 좌표의 x/y 최솟값과 최댓값 사용
- 이미지 Resize: Ultralytics 기본 letterbox, 라이브러리 기본값
- Aspect Ratio 유지 및 Padding: Ultralytics letterbox 기본 동작
- 정규화: Ultralytics 라이브러리 기본값
- 학습 입력: `data/processed/dataset_v3/data.yaml`

# 7. 실행 환경

작업1에서 동일 머신·동일 가상환경으로 수집한 값을 재사용했다.

{environment_markdown(experiment_dir / "environment.txt")}

- 실행 장비: 로컬 Windows 머신
- 실행 경로: {project_root}
- 가상환경: `venv`
- Docker 사용 여부: 아니오
- 인터넷 연결 필요 여부: 아니오

# 8. 모델 및 학습 설정

## 8.1 모델 정보

- 라이브러리: ultralytics
- 작업 유형: detect
- 모델 계열: YOLO26
- 모델 크기: s
- 사전 학습 가중치: yolo26s.pt
- 사전 학습 사용 여부: 예
- 클래스 수: {len(classes)}
- 모델 파일 경로: {project_root / "yolo26s.pt"}

## 8.2 학습 설정

| 설정 | 값 |
| --- | --- |
| Epoch | {actual_args.get("epochs")} |
| Patience | {actual_args.get("patience")} |
| Image Size | {actual_args.get("imgsz")} |
| Batch Size 요청값 | -1 (auto) |
| 실제 Batch Size | {actual_args.get("batch")} |
| Optimizer | {actual_args.get("optimizer")} |
| Initial Learning Rate | library default ({actual_args.get("lr0")}) |
| Weight Decay | library default ({actual_args.get("weight_decay")}) |
| AMP | library default ({actual_args.get("amp")}) |
| Device | {actual_args.get("device")} |
| Workers | {actual_args.get("workers")} |
| Seed | {actual_args.get("seed")} |
| Deterministic | {actual_args.get("deterministic")} |
| Cache | {actual_args.get("cache")} |

## 8.3 데이터 증강 설정

커스텀 증강 설정 없이 Ultralytics library default를 사용했다.

| 증강 | 값 | 기본값 변경 |
| --- | --- | --- |
{augmentation_rows}

# 9. 학습 실행 결과

- 학습 시작 일시: {started_at}
- 학습 종료 일시: {ended_at}
- 총 실행 시간: {format_duration(elapsed_seconds)}
- 정상 종료 여부: 예
- Early Stopping 여부: {early_stopping}
- 종료 Epoch: {final_epoch}
- Best Epoch: {best_epoch}
- Best 모델 경로: {experiment_dir / "models" / "best.pt"}
- Last 모델 경로: {experiment_dir / "models" / "last.pt"}
- 결과 폴더: {experiment_dir / "runs" / "train"}

## 9.1 학습 결과 요약

| 지표 | Best 결과 | Last 결과 |
| --- | ---: | ---: |
{result_rows}

Best epoch loss:

- Box Loss: {best_row["train/box_loss"]:.6f}
- Class Loss: {best_row["train/cls_loss"]:.6f}
- L1 Loss: {best_row["train/l1_loss"]:.6f}

## 9.2 학습 과정 해석

정량·정성 해석은 후속 평가 작업18~25에서 작성한다. 본 작업에서는 학습 완료 여부와 원시 학습 지표를 기록한다.

{deferred}
"""
    (experiment_dir / "experiment.md").write_text(markdown, encoding="utf-8")


def main() -> None:
    """Baseline 학습부터 산출물 복사와 실험 기록까지 순서대로 실행한다."""
    project_root = Path(__file__).resolve().parents[3]
    experiment_dir = project_root / "experiments" / EXPERIMENT_ID
    runs_dir = (experiment_dir / "runs").resolve()
    run_dir = runs_dir / "train"
    configure_logging(experiment_dir / "logs")

    started_at = now_iso()
    started_clock = monotonic()
    git_commit = ""
    image_counts = {"train": 0, "val": 0, "test": 0}
    classes: dict[int, str] = {}

    try:
        prepare_experiment_files(project_root, experiment_dir)
        model_path = require_file(project_root / "yolo26s.pt")
        data_path = require_file(
            project_root / "data" / "processed" / "dataset_v3" / "data.yaml"
        )
        image_counts = count_dataset_images(data_path.parent)
        classes = load_dataset_classes(project_root)
        git_commit = get_git_value(project_root, "rev-parse", "HEAD")
        git_branch = get_git_value(project_root, "branch", "--show-current")

        LOGGER.info(
            "Baseline 학습 시작 - experiment=%s, images=%s",
            EXPERIMENT_ID,
            image_counts,
        )
        model = YOLO(str(model_path))
        model.train(
            data=str(data_path),
            epochs=50,
            patience=15,
            imgsz=960,
            batch=-1,
            device="cpu",
            workers=0,
            cache=True,
            seed=42,
            deterministic=True,
            optimizer="auto",
            project=str(runs_dir),
            name="train",
            exist_ok=True,
        )
        actual_batch = model.trainer.batch_size
        if not isinstance(actual_batch, int) or actual_batch <= 0:
            raise ValueError(f"실제 batch 값을 확인할 수 없습니다: {actual_batch}")
        LOGGER.info("Baseline 학습 정상 종료")

        copy_training_artifacts(run_dir, experiment_dir)
        actual_args = load_yaml(experiment_dir / "train_config.yaml")
        actual_args["batch"] = actual_batch

        best_row, last_row = read_results(run_dir / "results.csv")
        last_metrics = {
            name: last_row[column] for name, column in METRIC_COLUMNS.items()
        }
        ended_at = now_iso()
        elapsed_seconds = monotonic() - started_clock
        experiment_data = build_experiment_data(
            project_root=project_root,
            experiment_dir=experiment_dir,
            status="completed",
            started_at=started_at,
            ended_at=ended_at,
            git_commit=git_commit,
            image_counts=image_counts,
            classes=classes,
            actual_batch=actual_batch,
            metrics=last_metrics,
        )
        write_experiment_yaml(
            experiment_dir / "experiment.yaml",
            experiment_data,
        )
        write_experiment_markdown(
            project_root=project_root,
            experiment_dir=experiment_dir,
            started_at=started_at,
            ended_at=ended_at,
            elapsed_seconds=elapsed_seconds,
            git_branch=git_branch,
            git_commit=git_commit,
            image_counts=image_counts,
            classes=classes,
            actual_args=actual_args,
            best_row=best_row,
            last_row=last_row,
        )
        LOGGER.info("실험 기록 생성 완료: %s", experiment_dir)
    except Exception:
        ended_at = now_iso()
        LOGGER.exception("Baseline 학습 또는 실험 기록 생성 실패")
        experiment_dir.mkdir(parents=True, exist_ok=True)
        failed_data = build_experiment_data(
            project_root=project_root,
            experiment_dir=experiment_dir,
            status="failed",
            started_at=started_at,
            ended_at=ended_at,
            git_commit=git_commit,
            image_counts=image_counts,
            classes=classes,
        )
        write_experiment_yaml(experiment_dir / "experiment.yaml", failed_data)
        raise


if __name__ == "__main__":
    main()
