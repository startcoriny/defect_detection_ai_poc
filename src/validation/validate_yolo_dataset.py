import csv
import hashlib
import logging
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.image_utils import read_image  # noqa: E402

LOGGER = logging.getLogger(__name__)
DATA_YAML_PATH = PROJECT_ROOT / "data" / "processed" / "dataset_v1" / "data.yaml"
REPORT_ROOT = PROJECT_ROOT / "reports" / "dataset"
REPORT_PATH = REPORT_ROOT / "final_dataset_validation_report.csv"
SUMMARY_PATH = REPORT_ROOT / "final_dataset_validation_summary.md"
SPLITS = ("train", "val", "test")
REPORT_FIELDS = ("split", "image_name", "check", "severity", "detail")
ERROR_CHECKS = (
    "image_missing",
    "label_missing",
    "image_unreadable",
    "label_line_value_count_mismatch",
    "class_id_out_of_range",
    "coordinate_out_of_range",
    "cross_split_duplicate",
)
WARNING_CHECKS = ("class_missing_in_split",)


# data.yaml에서 데이터셋 경로와 유효 클래스 번호를 읽는다.
def _load_dataset_config() -> tuple[Path, dict[str, Path], set[int]]:
    with DATA_YAML_PATH.open("r", encoding="utf-8") as yaml_file:
        config = yaml.safe_load(yaml_file)
    if not isinstance(config, dict):
        raise ValueError("data.yaml의 최상위 값은 매핑이어야 합니다.")

    dataset_path = Path(config["path"])
    dataset_root = (
        dataset_path
        if dataset_path.is_absolute()
        else (PROJECT_ROOT / dataset_path).resolve()
    )
    names = config["names"]
    if isinstance(names, list):
        class_ids = set(range(len(names)))
    elif isinstance(names, dict):
        class_ids = {int(class_id) for class_id in names}
    else:
        raise ValueError("data.yaml의 names는 목록 또는 매핑이어야 합니다.")
    if class_ids != set(range(len(class_ids))):
        raise ValueError("data.yaml의 class_id는 0부터 연속이어야 합니다.")

    image_directories = {}
    for split in SPLITS:
        relative_path = Path(config[split])
        image_directories[split] = (
            relative_path
            if relative_path.is_absolute()
            else dataset_root / relative_path
        )
    return dataset_root, image_directories, class_ids


# 이미지 경로에 대응하는 분할별 라벨 폴더 경로를 만든다.
def _label_directory(dataset_root: Path, image_directory: Path) -> Path:
    try:
        relative_parts = list(image_directory.relative_to(dataset_root).parts)
    except ValueError as error:
        raise ValueError("이미지 경로가 데이터셋 path 아래에 있어야 합니다.") from error
    if "images" not in relative_parts:
        raise ValueError("분할 이미지 경로에 images 디렉터리가 없습니다.")
    relative_parts[relative_parts.index("images")] = "labels"
    return dataset_root.joinpath(*relative_parts)


# 보고서에 기록할 검증 이슈 한 건을 추가한다.
def _add_issue(
    issues: list[dict[str, str]],
    split: str,
    image_name: str,
    check: str,
    severity: str,
    detail: str,
) -> None:
    issues.append(
        {
            "split": split,
            "image_name": image_name,
            "check": check,
            "severity": severity,
            "detail": detail,
        }
    )


# 라벨 한 줄의 값 개수, 클래스 번호, 정규화 좌표를 검사한다.
def _validate_label_line(
    line: str,
    line_number: int,
    split: str,
    image_name: str,
    class_ids: set[int],
    issues: list[dict[str, str]],
) -> int | None:
    values = line.split()
    if len(values) != 5:
        _add_issue(
            issues,
            split,
            image_name,
            "label_line_value_count_mismatch",
            "ERROR",
            f"{line_number}행: 값 {len(values)}개 (필요: 5개)",
        )
        return None

    parsed_class_id = None
    try:
        parsed_class_id = int(values[0])
    except ValueError:
        pass
    if parsed_class_id not in class_ids:
        _add_issue(
            issues,
            split,
            image_name,
            "class_id_out_of_range",
            "ERROR",
            f"{line_number}행: class_id={values[0]}",
        )

    invalid_coordinates = []
    coordinate_names = ("center_x", "center_y", "width", "height")
    for coordinate_name, raw_value in zip(coordinate_names, values[1:]):
        try:
            coordinate = float(raw_value)
        except ValueError:
            invalid_coordinates.append(f"{coordinate_name}={raw_value}")
            continue
        if not math.isfinite(coordinate) or not 0.0 <= coordinate <= 1.0:
            invalid_coordinates.append(f"{coordinate_name}={raw_value}")
    if invalid_coordinates:
        _add_issue(
            issues,
            split,
            image_name,
            "coordinate_out_of_range",
            "ERROR",
            f"{line_number}행: {', '.join(invalid_coordinates)}",
        )
    return parsed_class_id if parsed_class_id in class_ids else None


# 한 분할의 실제 이미지와 라벨 파일을 처음부터 검사한다.
def _validate_split(
    split: str,
    image_directory: Path,
    label_directory: Path,
    class_ids: set[int],
    issues: list[dict[str, str]],
) -> tuple[dict[str, int], set[int], set[str], set[str]]:
    if not image_directory.is_dir():
        raise ValueError(f"이미지 디렉터리가 없습니다: {image_directory}")
    if not label_directory.is_dir():
        raise ValueError(f"라벨 디렉터리가 없습니다: {label_directory}")

    image_paths = {path.stem: path for path in image_directory.glob("*.jpg")}
    label_paths = {path.stem: path for path in label_directory.glob("*.txt")}
    LOGGER.info(
        "%s: 이미지 %d개, 라벨 %d개",
        split,
        len(image_paths),
        len(label_paths),
    )

    empty_label_count = 0
    appeared_classes = set()
    failed_names = set()
    all_names = set(image_paths) | set(label_paths)
    for stem in sorted(all_names):
        image_path = image_paths.get(stem)
        label_path = label_paths.get(stem)
        image_name = image_path.name if image_path else f"{stem}.jpg"
        issue_start = len(issues)

        if image_path is None:
            _add_issue(
                issues,
                split,
                image_name,
                "image_missing",
                "ERROR",
                f"대응 이미지 없음: {label_path.name}",
            )
        elif read_image(image_path) is None:
            _add_issue(
                issues,
                split,
                image_name,
                "image_unreadable",
                "ERROR",
                "src/common/image_utils.read_image 디코딩 실패",
            )

        if label_path is None:
            _add_issue(
                issues,
                split,
                image_name,
                "label_missing",
                "ERROR",
                f"대응 라벨 없음: {stem}.txt",
            )
        else:
            try:
                label_content = label_path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as error:
                _add_issue(
                    issues,
                    split,
                    image_name,
                    "label_line_value_count_mismatch",
                    "ERROR",
                    f"라벨 읽기 실패: {error}",
                )
            else:
                if not label_content.strip():
                    if image_path is not None:
                        empty_label_count += 1
                else:
                    for line_number, line in enumerate(
                        label_content.splitlines(), start=1
                    ):
                        class_id = _validate_label_line(
                            line,
                            line_number,
                            split,
                            image_name,
                            class_ids,
                            issues,
                        )
                        if class_id is not None:
                            appeared_classes.add(class_id)

        if any(issue["severity"] == "ERROR" for issue in issues[issue_start:]):
            failed_names.add(stem)

    counts = {
        "images": len(image_paths),
        "labels": len(label_paths),
        "empty_labels": empty_label_count,
        "total_files": len(all_names),
    }
    return counts, appeared_classes, failed_names, set(image_paths)


# 분할 간 같은 이미지 파일명이 존재하는지 검사한다.
def _validate_cross_split_duplicates(
    image_names_by_split: dict[str, set[str]],
    issues: list[dict[str, str]],
    failed_names_by_split: dict[str, set[str]],
) -> None:
    splits_by_name = defaultdict(list)
    for split, image_names in image_names_by_split.items():
        for image_name in image_names:
            splits_by_name[image_name].append(split)

    for stem, duplicate_splits in sorted(splits_by_name.items()):
        if len(duplicate_splits) < 2:
            continue
        detail = f"중복 분할: {', '.join(duplicate_splits)}"
        for split in duplicate_splits:
            _add_issue(
                issues,
                split,
                f"{stem}.jpg",
                "cross_split_duplicate",
                "ERROR",
                detail,
            )
            failed_names_by_split[split].add(stem)


# 전체에 등장한 클래스가 특정 분할에서 누락됐는지 검사한다.
def _validate_missing_classes(
    classes_by_split: dict[str, set[int]],
    issues: list[dict[str, str]],
) -> None:
    all_appeared_classes = set().union(*classes_by_split.values())
    for split in SPLITS:
        for class_id in sorted(all_appeared_classes - classes_by_split[split]):
            _add_issue(
                issues,
                split,
                "",
                "class_missing_in_split",
                "WARNING",
                f"class_id={class_id}",
            )


# 데이터셋의 모든 파일 해시를 경로 순서대로 결합해 매니페스트 해시를 만든다.
def _calculate_manifest_hash(dataset_root: Path) -> str:
    manifest_hasher = hashlib.sha256()
    for file_path in sorted(
        (path for path in dataset_root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(dataset_root).as_posix(),
    ):
        file_hasher = hashlib.sha256()
        with file_path.open("rb") as dataset_file:
            for chunk in iter(lambda: dataset_file.read(1024 * 1024), b""):
                file_hasher.update(chunk)
        manifest_hasher.update(file_hasher.hexdigest().encode("ascii"))
    return manifest_hasher.hexdigest()


# 발견된 ERROR와 WARNING만 고정 컬럼 순서의 CSV로 저장한다.
def _write_report(issues: list[dict[str, str]]) -> None:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8", newline="") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=REPORT_FIELDS)
        writer.writeheader()
        writer.writerows(issues)


# 검증 통계, 판정, 매니페스트 해시를 한글 Markdown으로 저장한다.
def _write_summary(
    split_counts: dict[str, dict[str, int]],
    failed_names_by_split: dict[str, set[str]],
    issue_counts: Counter[tuple[str, str]],
    manifest_hash: str,
) -> None:
    total_errors = sum(
        count for (severity, _), count in issue_counts.items() if severity == "ERROR"
    )
    verdict = "학습 가능" if total_errors == 0 else "학습 불가 — 아래 오류 확인 필요"
    lines = [
        "# 데이터셋 최종 검증 요약",
        "",
        "## 분할별 집계",
        "",
        "| 분할 | 이미지 수 | 정상(빈 라벨) 이미지 수 | 검증 성공 파일 수 | 검증 실패 파일 수 |",
        "|---|---:|---:|---:|---:|",
    ]
    for split in SPLITS:
        counts = split_counts[split]
        failed_count = len(failed_names_by_split[split])
        success_count = counts["total_files"] - failed_count
        lines.append(
            f"| {split} | {counts['images']} | {counts['empty_labels']} | "
            f"{success_count} | {failed_count} |"
        )

    lines.extend(
        [
            "",
            "## 체크 항목별 건수",
            "",
            "| 체크 항목 | 심각도 | 건수 |",
            "|---|---|---:|",
        ]
    )
    for severity, checks in (
        ("ERROR", ERROR_CHECKS),
        ("WARNING", WARNING_CHECKS),
    ):
        for check in checks:
            lines.append(
                f"| {check} | {severity} | {issue_counts[(severity, check)]} |"
            )

    lines.extend(
        [
            "",
            "## 학습 가능 여부",
            "",
            f"**{verdict}**",
            "",
            "## 데이터셋 버전 고정",
            "",
            f"- 데이터셋 매니페스트 해시(SHA-256): `{manifest_hash}`",
            "- 계산 범위: `data/processed/dataset_v1/`의 모든 파일",
            "- 계산 방식: 상대경로 오름차순으로 각 파일의 SHA-256 해시를 "
            "이어붙인 뒤 다시 SHA-256 계산",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


# YOLO 데이터셋 전체를 독립 재검증하고 최종 학습 가능 여부를 판정한다.
def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
    )
    try:
        dataset_root, image_directories, class_ids = _load_dataset_config()
        issues = []
        split_counts = {}
        classes_by_split = {}
        failed_names_by_split = {}
        image_names_by_split = {}
        for split in SPLITS:
            result = _validate_split(
                split,
                image_directories[split],
                _label_directory(dataset_root, image_directories[split]),
                class_ids,
                issues,
            )
            (
                split_counts[split],
                classes_by_split[split],
                failed_names_by_split[split],
                image_names_by_split[split],
            ) = result

        _validate_cross_split_duplicates(
            image_names_by_split, issues, failed_names_by_split
        )
        _validate_missing_classes(classes_by_split, issues)
        manifest_hash = _calculate_manifest_hash(dataset_root)
    except (
        OSError,
        UnicodeError,
        KeyError,
        TypeError,
        ValueError,
        yaml.YAMLError,
    ) as error:
        LOGGER.error("데이터셋 최종 검증을 실행할 수 없습니다: %s", error)
        return 1

    issue_counts = Counter((issue["severity"], issue["check"]) for issue in issues)
    _write_report(issues)
    _write_summary(
        split_counts,
        failed_names_by_split,
        issue_counts,
        manifest_hash,
    )

    for severity, checks in (
        ("ERROR", ERROR_CHECKS),
        ("WARNING", WARNING_CHECKS),
    ):
        for check in checks:
            LOGGER.info(
                "%s %s: %d건",
                severity,
                check,
                issue_counts[(severity, check)],
            )
    total_errors = sum(
        count for (severity, _), count in issue_counts.items() if severity == "ERROR"
    )
    LOGGER.info("데이터셋 매니페스트 해시: %s", manifest_hash)
    LOGGER.info("최종 판정: %s", "학습 가능" if total_errors == 0 else "학습 불가")
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
