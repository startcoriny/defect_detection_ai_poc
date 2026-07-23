"""소량 데이터로 YOLO 학습부터 추론까지 전체 흐름을 점검한다."""

from __future__ import annotations

import csv
import logging
from pathlib import Path

import yaml
from ultralytics import YOLO

LOGGER = logging.getLogger(__name__)
TARGET_GROUPS = ("normal", "porosity", "slag_inclusion")
IMAGES_PER_GROUP = 5
VALIDATION_COLUMNS = ("metrics/precision(B)", "metrics/recall(B)")
IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


def configure_logging(output_dir: Path) -> None:
    """콘솔과 파일에 스모크 테스트 실행 로그를 기록한다."""
    output_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                output_dir / "smoke_test.log",
                encoding="utf-8",
            ),
        ],
        force=True,
    )


def load_smoke_images(project_root: Path) -> list[Path]:
    """메타데이터에서 대상 그룹별 이미지 5장을 이름순으로 선택한다."""
    metadata_path = project_root / "metadata" / "selected_dataset.csv"
    selected_by_group: dict[str, list[str]] = {group: [] for group in TARGET_GROUPS}

    with metadata_path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        required_columns = {"image_name", "group", "selected", "split_group"}
        missing_columns = required_columns.difference(reader.fieldnames or ())
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"selected_dataset.csv 필수 컬럼 누락: {missing}")

        for row in reader:
            group = row["group"]
            if (
                row["selected"] == "True"
                and row["split_group"] == "train"
                and group in selected_by_group
            ):
                selected_by_group[group].append(row["image_name"])

    image_paths: list[Path] = []
    for group in TARGET_GROUPS:
        image_names = sorted(selected_by_group[group])[:IMAGES_PER_GROUP]
        if len(image_names) != IMAGES_PER_GROUP:
            raise ValueError(
                f"{group} 그룹의 train 선택 이미지가 "
                f"{IMAGES_PER_GROUP}장보다 적습니다: {len(image_names)}장"
            )

        group_paths = [
            (
                project_root
                / "data"
                / "processed"
                / "dataset_v1"
                / "images"
                / "train"
                / f"{image_name}.jpg"
            ).resolve()
            for image_name in image_names
        ]
        missing_images = [path for path in group_paths if not path.is_file()]
        if missing_images:
            missing = "\n".join(str(path) for path in missing_images)
            raise FileNotFoundError(f"스모크 테스트 이미지 누락:\n{missing}")

        image_paths.extend(group_paths)
        LOGGER.info(
            "스모크 데이터 구성 - %s: %d장 (%s)",
            group,
            len(group_paths),
            ", ".join(image_names),
        )

    return image_paths


def write_smoke_files(
    project_root: Path,
    output_dir: Path,
    image_paths: list[Path],
) -> Path:
    """이미지 경로 목록과 스모크 테스트 전용 데이터 YAML을 생성한다."""
    image_list_path = output_dir / "smoke_images.txt"
    image_list_path.write_text(
        "".join(f"{path.as_posix()}\n" for path in image_paths),
        encoding="utf-8",
    )

    classes_path = project_root / "metadata" / "yolo_classes.txt"
    class_names = [
        line.strip()
        for line in classes_path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    if not class_names:
        raise ValueError("metadata/yolo_classes.txt에 클래스가 없습니다.")

    smoke_data = {
        "path": project_root.as_posix(),
        # 성능 측정이 아니라 학습과 검증 실행 여부만 확인하므로 같은 목록을 쓴다.
        "train": "outputs/smoke_test/smoke_images.txt",
        "val": "outputs/smoke_test/smoke_images.txt",
        "names": dict(enumerate(class_names)),
    }
    data_path = output_dir / "smoke_data.yaml"
    with data_path.open("w", encoding="utf-8") as yaml_file:
        yaml.safe_dump(
            smoke_data,
            yaml_file,
            allow_unicode=True,
            sort_keys=False,
        )

    LOGGER.info("스모크 이미지 경로 목록 생성: %s", image_list_path)
    LOGGER.info("스모크 데이터 설정 생성: %s", data_path)
    return data_path


def validate_training_outputs(run_dir: Path) -> tuple[Path, Path]:
    """체크포인트 생성과 Validation 지표 기록 여부를 확인한다."""
    best_path = run_dir / "weights" / "best.pt"
    last_path = run_dir / "weights" / "last.pt"
    missing_models = [path for path in (best_path, last_path) if not path.is_file()]
    if missing_models:
        missing = ", ".join(str(path) for path in missing_models)
        raise FileNotFoundError(f"모델 파일이 생성되지 않았습니다: {missing}")
    LOGGER.info("검증 완료 - 모델 파일 생성됨: best.pt, last.pt")

    results_path = run_dir / "results.csv"
    if not results_path.is_file():
        raise FileNotFoundError(f"학습 결과 파일이 없습니다: {results_path}")
    with results_path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)
        try:
            columns = {column.strip() for column in next(reader)}
        except StopIteration as exc:
            raise ValueError("results.csv가 비어 있습니다.") from exc

    missing_columns = set(VALIDATION_COLUMNS).difference(columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Validation 지표 컬럼이 없습니다: {missing}")
    LOGGER.info(
        "검증 완료 - Validation 실행됨: %s",
        ", ".join(VALIDATION_COLUMNS),
    )
    return best_path, last_path


def run_prediction(
    best_path: Path,
    image_paths: list[Path],
    runs_dir: Path,
) -> None:
    """저장된 best.pt를 다시 로드해 이미지 3장의 추론 결과를 확인한다."""
    prediction_sources = [str(path) for path in image_paths[:3]]
    model = YOLO(str(best_path))
    results = model.predict(
        source=prediction_sources,
        save=True,
        project=str(runs_dir),
        name="predict",
        exist_ok=True,
        device="cpu",
    )
    if len(results) != len(prediction_sources):
        raise RuntimeError(
            "추론 결과 수가 입력 이미지 수와 다릅니다: "
            f"{len(results)}개 / {len(prediction_sources)}개"
        )

    predict_dir = runs_dir / "predict"
    saved_images = (
        [
            path
            for path in predict_dir.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        ]
        if predict_dir.is_dir()
        else []
    )
    if len(saved_images) != len(prediction_sources):
        raise FileNotFoundError(
            "추론 결과 이미지 개수가 부족합니다: "
            f"{len(saved_images)}장 / {len(prediction_sources)}장"
        )
    LOGGER.info("검증 완료 - 추론 가능: 결과 이미지 %d장", len(saved_images))


def main() -> None:
    """스모크 데이터를 구성하고 학습·검증·추론을 순서대로 실행한다."""
    project_root = Path(__file__).resolve().parents[2]
    output_dir = project_root / "outputs" / "smoke_test"
    runs_dir = output_dir / "runs"
    configure_logging(output_dir)

    try:
        model_path = project_root / "yolo26n.pt"
        if not model_path.is_file():
            raise FileNotFoundError(f"사전 학습 모델이 없습니다: {model_path}")

        image_paths = load_smoke_images(project_root)
        data_path = write_smoke_files(project_root, output_dir, image_paths)

        LOGGER.info("학습 시작 - 15장, 2 epochs, CPU")
        model = YOLO(str(model_path))
        model.train(
            data=str(data_path),
            epochs=2,
            imgsz=640,
            batch=4,
            device="cpu",
            workers=0,
            seed=42,
            deterministic=True,
            patience=50,
            project=str(runs_dir),
            name="smoke",
            exist_ok=True,
        )
        LOGGER.info("학습 종료 - 학습 오류 없이 완료")

        run_dir = runs_dir / "smoke"
        best_path, _ = validate_training_outputs(run_dir)
        run_prediction(best_path, image_paths, runs_dir)

        LOGGER.info("최종 판정 - 학습 오류 없이 완료: 확인")
        LOGGER.info("최종 판정 - Validation 실행됨: 확인")
        LOGGER.info("최종 판정 - 모델 파일 생성됨: 확인")
        LOGGER.info("최종 판정 - 추론 가능: 확인")
        LOGGER.info("최종 판정 - Baseline 학습 시작 가능: 확인")
    except Exception:
        LOGGER.exception("Smoke Test 실행 실패")
        raise


if __name__ == "__main__":
    main()
