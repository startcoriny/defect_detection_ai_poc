# 구현 지시서: EXP-005 스크립트 생성 (Train slag_inclusion 오버샘플링, dataset_v3)

## 배경

EXP-P1-DET-005는 `docs/12_next_experiment_plan.md`에 따라 dataset_v3(dataset_v2의 Train 분할에서 slag_inclusion 포함 이미지를 1벌 더 복제, Val/Test는 dataset_v2와 동일)를 사용한다. 학습 하이퍼파라미터는 EXP-P1-DET-004(imgsz=960, box=7.5)와 완전히 동일하게 유지하고, **데이터셋 경로만** dataset_v3로 바꾼다.

dataset_v3는 이미 `data/processed/dataset_v3/`에 구축 완료됐다(`src/dataset/v3/oversample_slag.py`로 생성, Train 482장/Val 85장/Test 84장 — **Test는 dataset_v2와 완전히 동일하게 84장이다**).

## 기능 및 요구사항

`src/model/exp4/`, `src/evaluation/exp4/`, `src/visualization/exp4/`의 7개 스크립트를 각각 `src/model/exp5/`, `src/evaluation/exp5/`, `src/visualization/exp5/`로 복사하고 다음만 바꾼다:

1. `EXPERIMENT_ID = "EXP-P1-DET-004"` → `"EXP-P1-DET-005"` (해당되는 모든 파일: `train_baseline.py`, `run_inference.py`, `compare_thresholds.py`, `calculate_metrics.py`, `collect_error_cases.py`, `visualize_prediction.py`)
2. `export_auto_labels.py`의 `MODEL_VERSION = "EXP-P1-DET-004"` → `"EXP-P1-DET-005"`
3. `train_baseline.py`의 `EXPERIMENT_NAME = "RT_AL_YOLO26N_960_DatasetV2"` → `"RT_AL_YOLO26N_960_SlagOversample"`
4. **데이터셋 경로**: 각 스크립트에서 `data/processed/dataset_v2`(또는 `dataset_v2`)를 가리키는 모든 경로/문자열을 `data/processed/dataset_v3`(또는 `dataset_v3`)로 바꾼다. `imgsz=960, box=7.5, epochs=50, patience=15, batch=-1, optimizer="auto", device="cpu"` 등 학습 하이퍼파라미터는 절대 건드리지 않는다.
5. **`train_baseline.py`에서 `reports/dataset/v2/split_distribution.csv`를 참조하는 부분(있다면)은 그대로 `reports/dataset/v2/`를 유지한다** — dataset_v3는 `reports/dataset/v3/` 같은 별도 분할 리포트를 만들지 않았고(오버샘플링은 순수 파일 복제라 Train 분할 자체가 dataset_v2 기준 그대로다), Val/Test 구성도 dataset_v2와 동일하므로 이 부분은 exp4와 동일하게 둔다. (Test 이미지 개수 하드코딩이 있다면 dataset_v2와 동일하게 84 그대로 유지 — 바꾸지 않는다.)
6. 산출물 경로(`predictions/`, `auto-labels/`, `outputs/`, `reports/evaluation/`, `errors/`)에 들어가는 실험 ID 하위 폴더는 1번 변경만으로 자동으로 `EXP-P1-DET-005`가 되도록(exp4와 동일한 구조 유지)
7. `collect_error_cases.py`(exp5)의 import를 `from evaluation.exp5.calculate_metrics import (...)`로 변경

## 구현 범위 (In Scope)

- `src/model/exp5/`, `src/evaluation/exp5/`, `src/visualization/exp5/`에 7개 스크립트 생성

## 구현 제외 범위 (Out of Scope)

- exp1, exp2, exp3, exp4 스크립트 수정 — 절대 건드리지 않는다
- `src/dataset/v3/oversample_slag.py` 수정 — 이번 작업 범위 아님(이미 완료됨)
- 실제 학습·추론 실행 — CLAUDE가 수행
- `.gitignore`, `docs/*.md` 수정 — 이번 작업 범위 아님

## 완료 기준 (Definition of Done)

- `( )` exp5의 7개 스크립트에 `EXP-P1-DET-004` 잔재가 전혀 없다(`grep -rn "EXP-P1-DET-004" src/*/exp5` 결과 0건).
- `( )` exp5의 7개 스크립트에 `dataset_v2` 잔재가 전혀 없다(`grep -rn "dataset_v2" src/*/exp5` 결과 0건, 전부 `dataset_v3`로 교체됨). 단 `reports/dataset/v2/`(공용 분할 리포트 참조, 있다면)는 그대로 유지한다.
- `( )` Test 이미지 개수 관련 하드코딩 상수(있다면)가 84로 유지돼 있다(exp4와 동일, 바뀌지 않음).
- `( )` `train_baseline.py`(exp5)의 `imgsz`, `box` 등 학습 하이퍼파라미터가 exp4와 완전히 동일하다.
- `( )` exp4와 exp5의 산출물 경로가 겹치지 않는다.
- `( )` 코드가 PEP 8 / black 포맷을 따른다(ruff 통과).

## 제약사항

- `src/model/exp4/`, `src/evaluation/exp4/`, `src/visualization/exp4/`는 읽기만 하고 수정하지 않는다.
- 이 작업은 CODEX 샌드박스에서 Python을 실행해 검증할 수 없다. 코드 작성까지만 CODEX가 담당하고, 실제 실행·검증은 CLAUDE가 수행한다.

## 테스트 방법 (CLAUDE가 이어서 수행)

1. `grep -rn "EXP-P1-DET-004\|EXP-P1-DET-005" src/model/exp5 src/evaluation/exp5 src/visualization/exp5`로 잔재 확인
2. `grep -rn "dataset_v2\|dataset_v3" src/model/exp5 src/evaluation/exp5 src/visualization/exp5`로 데이터 경로 확인
3. `diff --strip-trailing-cr src/model/exp4/train_baseline.py src/model/exp5/train_baseline.py`로 하이퍼파라미터 외 변경이 없는지 확인
4. `black --check`, `ruff check`를 exp5 7개 파일에 실행
