# 구현 지시서: EXP-006 스크립트 생성 (CLAHE 전처리, dataset_v4)

## 배경

EXP-P1-DET-006은 `docs/13_next_experiment_plan.md`에 따라 dataset_v4(dataset_v3의 모든 이미지에 CLAHE 대비 강조를 적용, Train 482/Val 85/Test 84 — dataset_v3와 장수 동일)를 사용한다. 학습 하이퍼파라미터는 EXP-P1-DET-005(imgsz=960, box=7.5, epochs=50, patience=15)와 완전히 동일하게 유지하고, **데이터셋 경로만** dataset_v4로 바꾼다.

dataset_v4는 이미 `data/processed/dataset_v4/`에 구축 완료됐다(`src/dataset/v4/apply_clahe.py`로 생성, Train/Val/Test 장수는 dataset_v3와 완전히 동일).

## 기능 및 요구사항

`src/model/exp5/`, `src/evaluation/exp5/`, `src/visualization/exp5/`의 7개 스크립트를 각각 `src/model/exp6/`, `src/evaluation/exp6/`, `src/visualization/exp6/`로 복사하고 다음만 바꾼다.

1. `EXPERIMENT_ID = "EXP-P1-DET-005"` → `"EXP-P1-DET-006"` (해당되는 모든 파일: `train_baseline.py`, `run_inference.py`, `select_threshold.py`가 있다면 제외하고 `compare_thresholds.py`, `calculate_metrics.py`, `collect_error_cases.py`, `visualize_prediction.py`) — **exp5의 `select_threshold.py`는 exp6로 복사하지 않는다(exp5 전용 추가 분석 파일이라 이번 복사 대상 아님, exp5의 원래 7개 스크립트만 복사)**
2. `export_auto_labels.py`의 `MODEL_VERSION = "EXP-P1-DET-005"` → `"EXP-P1-DET-006"`
3. `train_baseline.py`의 `EXPERIMENT_NAME = "RT_AL_YOLO26N_960_SlagOversample"` → `"RT_AL_YOLO26N_960_CLAHE"`
4. **데이터셋 경로**: 각 스크립트에서 `data/processed/dataset_v3`(또는 `dataset_v3`)를 가리키는 모든 경로/문자열을 `data/processed/dataset_v4`(또는 `dataset_v4`)로 바꾼다. `imgsz=960, box=7.5, epochs=50, patience=15, batch=-1, optimizer="auto", device="cpu"` 등 학습 하이퍼파라미터는 절대 건드리지 않는다.
5. `train_baseline.py`에서 `reports/dataset/v2/split_distribution.csv`를 참조하는 부분(있다면)은 exp5와 동일하게 **그대로 `reports/dataset/v2/`를 유지한다**(dataset_v4도 Val/Test 구성은 dataset_v2·v3와 동일 — 이미지 픽셀만 CLAHE로 바뀌었을 뿐 분할·장수는 무관하다). Test 이미지 개수 하드코딩(84)도 그대로 유지한다.
6. 산출물 경로(`predictions/`, `auto-labels/`, `outputs/`, `reports/evaluation/`, `errors/`)에 들어가는 실험 ID 하위 폴더는 1번 변경만으로 자동으로 `EXP-P1-DET-006`이 되도록(exp5와 동일한 구조 유지)
7. `collect_error_cases.py`(exp6)의 import를 `from evaluation.exp6.calculate_metrics import (...)`로 변경

## 구현 범위 (In Scope)

- `src/model/exp6/`, `src/evaluation/exp6/`, `src/visualization/exp6/`에 7개 스크립트 생성 (exp5의 `select_threshold.py`는 제외)

## 구현 제외 범위 (Out of Scope)

- exp1~exp5 스크립트 수정 — 절대 건드리지 않는다
- `src/dataset/v4/apply_clahe.py` 수정 — 이번 작업 범위 아님(이미 완료됨)
- 실제 학습·추론 실행 — CLAUDE가 수행
- `.gitignore`, `docs/*.md` 수정 — 이번 작업 범위 아님

## 완료 기준 (Definition of Done)

- `( )` exp6의 7개 스크립트에 `EXP-P1-DET-005` 잔재가 전혀 없다(`grep -rn "EXP-P1-DET-005" src/*/exp6` 결과 0건).
- `( )` exp6의 7개 스크립트에 `dataset_v3` 잔재가 전혀 없다(`grep -rn "dataset_v3" src/*/exp6` 결과 0건, 전부 `dataset_v4`로 교체됨). 단 `reports/dataset/v2/`(공용 분할 리포트 참조)는 그대로 유지한다.
- `( )` Test 이미지 개수 관련 하드코딩 상수가 84로 유지돼 있다(exp5와 동일, 바뀌지 않음).
- `( )` `train_baseline.py`(exp6)의 `imgsz`, `box` 등 학습 하이퍼파라미터가 exp5와 완전히 동일하다.
- `( )` exp5와 exp6의 산출물 경로가 겹치지 않는다.
- `( )` 코드가 PEP 8 / black 포맷을 따른다(ruff 통과).

## 제약사항

- `src/model/exp5/`, `src/evaluation/exp5/`, `src/visualization/exp5/`는 읽기만 하고 수정하지 않는다.
- 이 작업은 CODEX 샌드박스에서 Python을 실행해 검증할 수 없다. 코드 작성까지만 CODEX가 담당하고, 실제 실행·검증은 CLAUDE가 수행한다.

## 테스트 방법 (CLAUDE가 이어서 수행)

1. `grep -rn "EXP-P1-DET-005\|EXP-P1-DET-006" src/model/exp6 src/evaluation/exp6 src/visualization/exp6`로 잔재 확인
2. `grep -rn "dataset_v3\|dataset_v4" src/model/exp6 src/evaluation/exp6 src/visualization/exp6`로 데이터 경로 확인
3. `diff --strip-trailing-cr src/model/exp5/train_baseline.py src/model/exp6/train_baseline.py`로 하이퍼파라미터 외 변경이 없는지 확인
4. `black --check`, `ruff check`를 exp6 7개 파일에 실행
