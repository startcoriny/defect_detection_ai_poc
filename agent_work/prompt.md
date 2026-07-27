# 구현 지시서: dataset_v2 구축 스크립트 생성 (EXP-P1-DET-004용 데이터 확장)

## 배경

EXP-P1-DET-001~003 세 실험 모두 "저대비·Small 결함 미탐"을 해결하지 못했다(`docs/11_next_experiment_plan.md` 참조). `docs/context/01-experiment-scope.md` 4.3절의 "데이터 부족 시 처리" 마지막 단계에 따라, 로컬에 이미 보유한 RT/AL 원본 637장(현재 dataset_v1은 그중 약 300장만 사용) 중 미사용분을 추가로 투입해 `dataset_v2`를 만든다. 소재(AL)는 그대로 유지하고 "데이터 양"만 변수로 바꾼다.

**이 작업은 dataset_v2 구축 스크립트 생성까지만 다룬다. 실제 실행(각 스크립트 실행)과 이후 EXP-P1-DET-004 학습·평가는 CLAUDE가 별도로 진행한다.**

## 기존 파이프라인 구조 (읽기만 하고 수정하지 않음)

dataset_v1은 5개 스크립트가 순서대로 실행되어 만들어졌다.

1. `src/dataset/select_poc_dataset.py` — RT/AL 후보 중 품질 검사 통과·비중복 이미지를 그룹(`normal`/`porosity`/`slag_inclusion`/`both`)별로 `TARGET_COUNT=100`까지 무작위 표본 추출 → `metadata/selected_dataset.csv`, `metadata/included_files.txt`, `metadata/excluded_files.txt`
2. `src/conversion/polygon_to_box.py` — `metadata/selected_dataset.csv`의 선택 이미지에 대해 Polygon→Box 변환 → `metadata/bbox_annotations.csv`, `metadata/bbox_conversion_errors.csv`, `outputs/polygon-box-comparison/*.jpg`(시각 비교용)
3. `src/conversion/box_to_yolo.py` — `metadata/bbox_annotations.csv`를 YOLO 포맷으로 변환 → `outputs/yolo_labels/*.txt`, `metadata/yolo_classes.txt`
4. `src/dataset/split_dataset.py` — `metadata/selected_dataset.csv`의 `split_group` 컬럼을 그룹×크기 층화 방식으로 채움(같은 파일에 덮어쓰기) → `splits/{train,val,test}.txt`, `reports/dataset/{split_distribution.csv, split_validation_report.md}`
5. `src/dataset/build_yolo_dataset.py` — 위 산출물을 조합해 실제 YOLO 학습 폴더 구성 → `data/processed/dataset_v1/{images,labels}/{train,val,test}/`, `data/processed/dataset_v1/data.yaml`

이 중 **`metadata/raw_dataset_inventory.csv`, `metadata/class_mapping.json`, `metadata/class_statistics.csv`, `reports/data-quality/data_quality_report.csv`는 RT/AL·RT/ST·VT/ST 전체(2,250장) 기준으로 이미 만들어진 공용 산출물**이라 dataset_v2에도 그대로 재사용한다(수정 금지, 새로 만들 필요 없음).

## 기능 및 요구사항

위 5개 스크립트를 각각 `src/dataset/v2/`, `src/conversion/v2/`로 복사해 다음과 같이 수정한다. **기존 5개 스크립트(`src/dataset/{select_poc_dataset.py, split_dataset.py, build_yolo_dataset.py}`, `src/conversion/{polygon_to_box.py, box_to_yolo.py}`)는 절대 수정하지 않는다** — `dataset_v1`과 EXP-001~003의 재현성을 그대로 보존해야 한다.

**공통 필수 수정 사항 (5개 파일 전부 해당)**: 원본은 전부 `src/<카테고리>/<파일명>.py` 구조(프로젝트 루트 기준 2단계 깊이)라 `PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent`(부모 3단계)로 프로젝트 루트를 계산한다. `v2/` 하위 폴더로 옮기면 `src/<카테고리>/v2/<파일명>.py`(3단계 깊이)가 되므로, **5개 파일 전부 이 줄을 `PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent`(부모 4단계)로 바꿔야 한다.** 이걸 놓치면 `PROJECT_ROOT`가 실제로는 `src/dataset/` 같은 엉뚱한 경로를 가리키게 되어 이후 모든 입출력 경로가 깨진다. (`polygon_to_box.py`의 `SRC_ROOT = PROJECT_ROOT / "src"`, `sys.path.insert(...)` 부분은 `PROJECT_ROOT`만 올바르게 고치면 그대로 정상 동작한다 — 별도 추가 수정 불필요.)

### 1. `src/dataset/v2/select_poc_dataset.py`

- `TARGET_COUNT = 100` → `TARGET_COUNT = 1000`으로 변경한다. (RT/AL 전체가 637장이므로 어떤 그룹도 1000을 넘지 않는다 — 결과적으로 품질 검사·중복 제거·`off_target_class_present` 제외를 통과한 후보를 사실상 전량 선택하게 된다. `select_samples()`의 나머지 로직은 그대로 둔다.)
- 출력 경로 3개를 전부 `metadata/v2/` 하위로 변경한다: `METADATA_ROOT / "selected_dataset.csv"` → `metadata/v2/selected_dataset.csv`, `included_files.txt` → `metadata/v2/included_files.txt`, `excluded_files.txt` → `metadata/v2/excluded_files.txt`. (스크립트 안에서 이 경로들을 만드는 상수/변수를 적절히 두면 된다 — 예: 새 상수 `OUTPUT_ROOT = PROJECT_ROOT / "metadata" / "v2"`를 추가하고 `write_results()`에서 이를 사용하도록 수정.)
- **입력 경로는 그대로 유지한다**: `INVENTORY_PATH`, `CLASS_MAPPING_PATH`, `QUALITY_REPORT_PATH`는 원본 스크립트와 동일하게 `metadata/raw_dataset_inventory.csv`, `metadata/class_mapping.json`, `reports/data-quality/data_quality_report.csv`를 계속 가리켜야 한다(공용 산출물이므로 복사하지 않는다).
- `log_summary()`의 `LOGGER.info("Target %s: planned=%d, ...", class_name, TARGET_COUNT, ...)` 부분은 `TARGET_COUNT`(=1000) 그대로 두면 로그에 "planned=1000"이 찍히지만, 이건 로그 문구일 뿐이라 기능에 영향 없다. 그대로 둔다.

### 2. `src/conversion/v2/polygon_to_box.py`

- `SELECTED_DATASET_PATH`를 `metadata/v2/selected_dataset.csv`로 변경한다.
- `BBOX_ANNOTATIONS_PATH`, `BBOX_ERRORS_PATH`를 각각 `metadata/v2/bbox_annotations.csv`, `metadata/v2/bbox_conversion_errors.csv`로 변경한다.
- `OUTPUT_ROOT`(시각 비교 이미지 저장 경로, 원본은 `outputs/polygon-box-comparison/`)를 `outputs/polygon-box-comparison-v2/`로 변경한다.
- **입력 경로는 그대로 유지한다**: `INVENTORY_PATH`, `CLASS_MAPPING_PATH`, `CLASS_STATISTICS_PATH`는 원본과 동일한 공용 경로(`metadata/raw_dataset_inventory.csv`, `metadata/class_mapping.json`, `metadata/class_statistics.csv`)를 계속 가리켜야 한다.

### 3. `src/conversion/v2/box_to_yolo.py`

- `SELECTED_DATASET_PATH`를 `metadata/v2/selected_dataset.csv`로 변경한다.
- `BBOX_ANNOTATIONS_PATH`를 `metadata/v2/bbox_annotations.csv`로 변경한다(위 2번 스크립트가 만든 파일).
- `YOLO_CLASSES_PATH`를 `metadata/v2/yolo_classes.txt`로 변경한다.
- `OUTPUT_ROOT`(YOLO 라벨 txt 저장 경로, 원본은 `outputs/yolo_labels/`)를 `outputs/yolo_labels_v2/`로 변경한다.
- **입력 경로는 그대로 유지한다**: `CLASS_STATISTICS_PATH`는 공용 경로(`metadata/class_statistics.csv`) 그대로.

### 4. `src/dataset/v2/split_dataset.py`

- `METADATA_ROOT`는 그대로 두되(공용 `class_statistics.csv`를 여전히 읽어야 하므로), `selected_dataset.csv`를 읽고 쓰는 부분만 `metadata/v2/selected_dataset.csv`를 가리키도록 바꾼다. 구체적으로:
  - `main()`의 `read_csv(METADATA_ROOT / "selected_dataset.csv")` → `read_csv(METADATA_ROOT / "v2" / "selected_dataset.csv")`
  - `load_annotations()`의 `read_csv(METADATA_ROOT / "bbox_annotations.csv")` → `read_csv(METADATA_ROOT / "v2" / "bbox_annotations.csv")` (2번 스크립트가 만든 파일)
  - `write_selected_dataset()`의 `path = METADATA_ROOT / "selected_dataset.csv"` → `path = METADATA_ROOT / "v2" / "selected_dataset.csv"`
  - `load_standard_classes()`가 읽는 `METADATA_ROOT / "class_statistics.csv"`는 공용 경로이므로 그대로 둔다.
- `SPLIT_ROOT`(원본 `PROJECT_ROOT / "splits"`)를 `PROJECT_ROOT / "splits" / "v2"`로 변경한다.
- `REPORT_ROOT`(원본 `PROJECT_ROOT / "reports" / "dataset"`)를 `PROJECT_ROOT / "reports" / "dataset" / "v2"`로 변경한다.
- **`EXPECTED_STRATUM_COUNTS`(dataset_v1의 정확한 층화 그룹별 이미지 수를 하드코딩한 딕셔너리, 예: `{"both_mixed": 1, "normal": 100, ...}`)를 완전히 제거하고, `build_split_assignments()`에서 이 값과 비교해 `ValueError`를 던지는 검증 블록도 함께 제거한다.** dataset_v2는 각 층화 그룹의 실제 이미지 수가 dataset_v1과 다르므로 이 하드코딩된 기댓값과 비교하는 검증은 애초에 성립하지 않는다. 대신 그 자리에 `LOGGER.info("층화 키별 이미지 수: %s", dict(sorted(actual_counts.items())))`처럼 실제 값을 로그로만 남기도록 바꾼다(예외를 던지지 않는다).
- **`write_validation_report()`의 `ratio_range` 검증(`if ratio_range >= 24.0: raise ValueError(...)`)은 일반적인 상한선 점검이므로 그대로 유지한다.** 다만 보고서 본문에 있는 다음 문장은 dataset_v1의 과거 특정 실험값을 가리키는 문장이라 dataset_v2에는 맞지 않으므로 **삭제하거나 일반적인 문장으로 바꾼다**:
  ```
  f"세 분할의 작은 객체 비율 범위는 {ratio_range:.2f}%p이다. "
  "이전 group 단독 층화의 train 55.80%, val 62.32%, test 79.79%와 "
  "그 범위 24.0%p보다 감소했다.",
  ```
  → 예를 들어 `f"세 분할의 작은 객체 비율 범위는 {ratio_range:.2f}%p이다(상한 24.0%p 이내)."` 정도로 대체한다. 정확한 문구는 자유롭게 정하되, 존재하지 않는 "이전 실험값과 비교해 감소했다"는 식의 주장은 넣지 않는다.

### 5. `src/dataset/v2/build_yolo_dataset.py`

- `SELECTED_DATASET_PATH`를 `metadata/v2/selected_dataset.csv`로 변경한다.
- `CLASS_PATH`(원본 `metadata/yolo_classes.txt`)를 `metadata/v2/yolo_classes.txt`로 변경한다(3번 스크립트가 만든 파일).
- `LABEL_ROOT`(원본 `outputs/yolo_labels/`)를 `outputs/yolo_labels_v2/`로 변경한다(3번 스크립트가 만든 폴더).
- `DATASET_ROOT`(원본 `data/processed/dataset_v1`)를 `data/processed/dataset_v2`로 변경한다.
- `DATASET_PATH`(문자열 `"data/processed/dataset_v1"`, `data.yaml`의 `path` 필드와 검증에 사용됨)를 `"data/processed/dataset_v2"`로 변경한다.
- **`EXPECTED_SPLIT_COUNTS = {"train": 209, "val": 44, "test": 46}`(dataset_v1 전용 하드코딩 값)를 제거하고, 대신 `load_selected_rows()` 안에서 실제 분할별 개수(`split_counts`, 이미 계산되어 있음)를 그대로 신뢰하도록 바꾼다** — 즉 `if dict(split_counts) != EXPECTED_SPLIT_COUNTS: raise ValueError(...)` 검증 블록을 제거하고, 대신 `LOGGER.info("분할별 이미지 수: %s", dict(split_counts))`로 실제 값을 로그로 남긴다(예외를 던지지 않는다).
- **`validate_dataset_files()`도 같은 이유로 `EXPECTED_SPLIT_COUNTS`를 참조하는 부분(`if len(image_names) != EXPECTED_SPLIT_COUNTS[split]: raise ValueError(...)`)을 제거한다.** 대신 `image_names`와 `label_names`의 basename이 서로 일치하는지 검증하는 로직(바로 위 블록)은 그대로 유지한다 — 이것은 절대 개수가 아니라 이미지-라벨 쌍의 정합성을 확인하는 것이라 dataset_v2에도 그대로 유효하다. 개수는 `LOGGER.info("%s 분할: 이미지 %d개, 라벨 %d개", split, len(image_names), len(label_names))` 로그로만 남긴다(이미 있는 로그 그대로 둔다).

## 구현 범위 (In Scope)

- `src/dataset/v2/{select_poc_dataset.py, split_dataset.py, build_yolo_dataset.py}` 생성
- `src/conversion/v2/{polygon_to_box.py, box_to_yolo.py}` 생성
- 위 5개 파일 안에서 필요한 `import` 경로(예: `sys.path` 조작이 있는 `polygon_to_box.py`)는 새 위치(`src/conversion/v2/`)에서도 정상 동작하도록 조정한다.

## 구현 제외 범위 (Out of Scope)

- 기존 `src/dataset/{select_poc_dataset.py, split_dataset.py, build_yolo_dataset.py}`, `src/conversion/{polygon_to_box.py, box_to_yolo.py}` 수정 — 절대 건드리지 않는다.
- `src/model/exp4/`, `src/evaluation/exp4/`, `src/visualization/exp4/` 생성 — 이번 작업 범위 아님(dataset_v2가 만들어진 뒤 별도로 진행).
- 스크립트 실제 실행 — CLAUDE가 수행한다. CODEX는 코드 작성만 한다.
- `metadata/v2/`, `data/processed/dataset_v2/`, `outputs/{polygon-box-comparison-v2, yolo_labels_v2}/`, `splits/v2/`, `reports/dataset/v2/` 등 산출물 디렉터리를 미리 만들거나 커밋하는 것 — 스크립트가 실행 시점에 자체적으로 만들어야 한다(`mkdir(parents=True, exist_ok=True)` 패턴은 원본 스크립트에 이미 있으므로 그대로 유지).

## 완료 기준 (Definition of Done)

- `( )` `src/dataset/v2/`, `src/conversion/v2/`에 5개 파일이 생성됐다.
- `( )` 5개 파일 전부 `PROJECT_ROOT`가 `parent.parent.parent.parent`(부모 4단계)로 바뀌어 있다(`grep -n "PROJECT_ROOT = " src/dataset/v2/*.py src/conversion/v2/*.py`로 확인).
- `( )` `grep -rn "dataset_v1\|metadata/selected_dataset.csv\|outputs/yolo_labels/\|outputs/polygon-box-comparison/" src/dataset/v2 src/conversion/v2`(경로 문자열 기준)에 dataset_v1 전용 경로가 남아있지 않다. 단, `metadata/raw_dataset_inventory.csv`, `metadata/class_mapping.json`, `metadata/class_statistics.csv`, `reports/data-quality/data_quality_report.csv`(공용 산출물)를 가리키는 부분은 원본과 동일하게 남아있어야 한다(이건 정상이다).
- `( )` `EXPECTED_STRATUM_COUNTS`(split_dataset.py), `EXPECTED_SPLIT_COUNTS`(build_yolo_dataset.py) 하드코딩 값과 그에 대한 `ValueError` 검증이 v2 버전에서 제거되고, 대신 실제 값을 로그로 남기는 형태로 바뀌었다.
- `( )` `TARGET_COUNT = 1000`(select_poc_dataset.py v2)으로 바뀌었다.
- `( )` 기존 5개 원본 스크립트는 git diff 상 전혀 변경되지 않았다.
- `( )` 코드가 PEP 8 / black 포맷을 따른다(ruff 통과).

## 제약사항

- 원본 스크립트는 읽기만 하고 수정하지 않는다.
- 이 작업은 CODEX 샌드박스에서 Python을 실행해 검증할 수 없다. 코드 작성까지만 CODEX가 담당하고, 실제 실행·검증은 CLAUDE가 수행한다.
- 위 지시서에 없는 임의의 추가 변경(로직 개선, 리팩터링, 주석 추가 등)은 하지 않는다 — 지정된 경로·상수 변경 외에는 원본과 동일하게 유지한다.

## 테스트 방법 (CLAUDE가 이어서 수행)

0. `grep -n "PROJECT_ROOT = " src/dataset/v2/*.py src/conversion/v2/*.py`로 전부 `parent.parent.parent.parent`인지 확인
1. `grep -rn "dataset_v1\|EXPECTED_STRATUM_COUNTS\|EXPECTED_SPLIT_COUNTS" src/dataset/v2 src/conversion/v2`로 v1 전용 하드코딩 잔재가 없는지 확인
2. `black --check`, `ruff check`를 새 5개 파일에 실행
3. `venv/Scripts/python.exe src/dataset/v2/select_poc_dataset.py` → `metadata/v2/selected_dataset.csv` 생성 및 그룹별 선택 건수 확인(로그의 `Group ...: total=X, selected=Y` — Y가 X와 거의 같아야 함, 즉 사실상 전량 선택)
4. `venv/Scripts/python.exe src/conversion/v2/polygon_to_box.py` → `metadata/v2/bbox_annotations.csv` 생성 확인
5. `venv/Scripts/python.exe src/conversion/v2/box_to_yolo.py` → `outputs/yolo_labels_v2/`에 라벨 파일 수가 선택 이미지 수와 일치하는지 확인
6. `venv/Scripts/python.exe src/dataset/v2/split_dataset.py` → 예외 없이 완료, `reports/dataset/v2/split_validation_report.md` 내용 확인(층화 검증 통과, ratio_range < 24.0%p)
7. `venv/Scripts/python.exe src/dataset/v2/build_yolo_dataset.py` → `data/processed/dataset_v2/data.yaml` 및 `images/labels` 각 분할 폴더 생성 확인, 로그의 실제 분할별 이미지 수 확인
