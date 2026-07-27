# 구현 지시서: EXP-004 스크립트 생성 (데이터 확장, dataset_v2)

## 배경

EXP-P1-DET-004는 `docs/11_next_experiment_plan.md`에 따라 dataset_v2(로컬 RT/AL 637장 중 567장 활용, dataset_v1의 299장보다 확장)를 사용한다. 학습 하이퍼파라미터는 EXP-P1-DET-002(imgsz=960, box=7.5 기본값)와 완전히 동일하게 유지하고, **데이터셋 경로만** dataset_v2로 바꾼다(변수를 "데이터 양" 하나로 한정).

dataset_v2는 이미 `data/processed/dataset_v2/`에 구축 완료됐다(`src/dataset/v2/`, `src/conversion/v2/` 스크립트로 생성, `data.yaml` 검증 통과 — train 398장/val 85장/test 84장).

## 기능 및 요구사항

`src/model/exp2/`, `src/evaluation/exp2/`, `src/visualization/exp2/`의 7개 스크립트를 각각 `src/model/exp4/`, `src/evaluation/exp4/`, `src/visualization/exp4/`로 복사하고 다음만 바꾼다(그 외 로직·하이퍼파라미터·산출물 경로 구조는 exp2와 동일한 패턴을 그대로 따르되 실험 ID와 데이터 경로만 교체):

1. `EXPERIMENT_ID = "EXP-P1-DET-002"` → `"EXP-P1-DET-004"` (해당되는 모든 파일: `train_baseline.py`, `run_inference.py`, `compare_thresholds.py`, `calculate_metrics.py`, `collect_error_cases.py`, `visualize_prediction.py`)
2. `export_auto_labels.py`의 `MODEL_VERSION = "EXP-P1-DET-002"` → `"EXP-P1-DET-004"`
3. `train_baseline.py`의 `EXPERIMENT_NAME = "RT_AL_YOLO26N_960_ImgszUp"` → `"RT_AL_YOLO26N_960_DatasetV2"`
4. **데이터셋 경로**: exp2의 각 스크립트에서 `data/processed/dataset_v1`(또는 `dataset_v1`)을 가리키는 모든 경로/문자열을 `data/processed/dataset_v2`(또는 `dataset_v2`)로 바꾼다. `train_baseline.py`의 `model.train(data=..., ...)`에 전달하는 data.yaml 경로, `run_inference.py`·`compare_thresholds.py`·`calculate_metrics.py`가 참조하는 Test 이미지/라벨 경로, `collect_error_cases.py`가 참조하는 GT 라벨 경로 등 dataset_v1을 가리키는 부분을 전부 찾아서 바꾼다. **imgsz=960, box=7.5(EXP-002와 동일, 즉 명시적으로 설정하지 않거나 EXP-002와 같은 값), epochs=50, patience=15, batch=-1, optimizer="auto", device="cpu" 등 그 외 학습 하이퍼파라미터는 절대 건드리지 않는다.**
5. 산출물 경로(`predictions/`, `auto-labels/`, `outputs/`, `reports/evaluation/`, `errors/`)에 들어가는 실험 ID 하위 폴더도 자동으로 `EXP-P1-DET-004`가 되도록(이미 exp2에서 `EXPERIMENT_ID` 변수를 참조하는 구조이므로 1번 변경만으로 따라감 — 별도 하드코딩된 경로가 있는지 확인)
6. `collect_error_cases.py`(exp4)의 import를 `from evaluation.exp4.calculate_metrics import (...)`로 변경

## 구현 범위 (In Scope)

- `src/model/exp4/`, `src/evaluation/exp4/`, `src/visualization/exp4/`에 7개 스크립트 생성

## 구현 제외 범위 (Out of Scope)

- exp1, exp2, exp3 스크립트 수정 — 절대 건드리지 않는다
- `src/dataset/v2/`, `src/conversion/v2/` 수정 — 이번 작업 범위 아님(이미 완료됨)
- 실제 학습·추론 실행 — CLAUDE가 수행
- `.gitignore`, `docs/*.md` 수정 — 이번 작업 범위 아님

## 완료 기준 (Definition of Done)

- `( )` exp4의 7개 스크립트에 `EXP-P1-DET-002` 잔재가 전혀 없다(`grep -rn "EXP-P1-DET-002" src/*/exp4` 결과 0건).
- `( )` exp4의 7개 스크립트에 `dataset_v1` 잔재가 전혀 없다(`grep -rn "dataset_v1" src/*/exp4` 결과 0건, 전부 `dataset_v2`로 교체됨).
- `( )` `train_baseline.py`(exp4)의 `imgsz`, `box` 등 학습 하이퍼파라미터가 exp2와 완전히 동일하다(`diff`로 데이터 경로·EXPERIMENT_ID·EXPERIMENT_NAME 외 차이가 없는지 확인 가능해야 함).
- `( )` exp2와 exp4의 산출물 경로가 겹치지 않는다.
- `( )` 코드가 PEP 8 / black 포맷을 따른다(ruff 통과).

## 제약사항

- `src/model/exp2/`, `src/evaluation/exp2/`, `src/visualization/exp2/`는 읽기만 하고 수정하지 않는다.
- 이 작업은 CODEX 샌드박스에서 Python을 실행해 검증할 수 없다. 코드 작성까지만 CODEX가 담당하고, 실제 실행·검증은 CLAUDE가 수행한다.

## 테스트 방법 (CLAUDE가 이어서 수행)

1. `grep -rn "EXP-P1-DET-002\|EXP-P1-DET-004" src/model/exp4 src/evaluation/exp4 src/visualization/exp4`로 잔재 확인
2. `grep -rn "dataset_v1\|dataset_v2" src/model/exp4 src/evaluation/exp4 src/visualization/exp4`로 데이터 경로 확인
3. `diff --strip-trailing-cr src/model/exp2/train_baseline.py src/model/exp4/train_baseline.py`로 하이퍼파라미터 외 변경이 없는지 확인
4. `black --check`, `ruff check`를 exp4 7개 파일에 실행
