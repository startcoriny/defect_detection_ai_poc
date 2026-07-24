# 구현 지시서: 실험별 스크립트 폴더 분리 + EXP-002(imgsz=960) 스크립트 생성

## 배경

Baseline(EXP-P1-DET-001) 실험 사이클(작업17~24)에서 만든 스크립트 7개가 전부 `src/model/`, `src/evaluation/`, `src/visualization/`에 평평하게 섞여 있고, `EXPERIMENT_ID`/`imgsz` 같은 값이 스크립트 안에 하드코딩돼 있다. 이제 두 번째 실험(EXP-P1-DET-002, `imgsz` 640→960만 변경)을 시작하는데, 사용자가 명시적으로 요청한 방식은 다음과 같다.

- 실험별로 스크립트를 **폴더로 분리**한다(`exp1/`, `exp2/`처럼 사람이 보기 쉬운 이름, 영어 사용 가능). 팀원이 시연하거나 각자 로컬에서 재현할 때 "실험1 폴더 하나만 보면 되는" 구조가 목적이다.
- 기존 EXP-001 스크립트는 **내용을 바꾸지 않는다**(재현성 보존). 새 실험은 **복사본**을 만들어 값만 바꾼다.

이 작업은 두 부분으로 나뉜다: **(A) 기존 7개 스크립트를 `exp1/` 하위 폴더로 이동**(동작은 100% 동일하게 유지, 경로 깊이만 보정) + **(B) `exp2/` 복사본 생성**(`EXPERIMENT_ID`/`imgsz` 변경 + 산출물 경로를 실험별로 분리).

## 왜 (B)에서 산출물 경로도 바꿔야 하는가 (중요)

`run_inference.py`(→`predictions/prediction_results.json`), `export_auto_labels.py`(→`auto-labels/`), `visualize_prediction.py`(→`outputs/auto-label-visualization/`, `metadata/auto_label_roundtrip_mismatches.csv`), `compare_thresholds.py`(→`outputs/threshold-comparison/`, `reports/evaluation/threshold_comparison.csv`), `calculate_metrics.py`(→`reports/evaluation/{model_performance.csv,object_size_performance.csv,evaluation/}`), `collect_error_cases.py`(→`errors/`, `reports/evaluation/{error_cases.csv,error_type_counts.csv}`)의 산출물 경로가 전부 **실험 구분 없이 고정된 경로**다. exp2 스크립트를 그대로 실행하면 exp1의 결과(이미 커밋되어 문서에서 참조 중인 파일들)를 덮어쓴다. 그래서 **exp1 스크립트는 경로를 그대로 두고(기존 커밋된 산출물과의 정합성 유지), exp2 스크립트만 산출물 경로에 `EXPERIMENT_ID`(`EXP-P1-DET-002`) 하위 폴더를 추가**해서 서로 충돌하지 않게 한다.

## (A) 기존 스크립트를 `exp1/`로 이동 (동작 변경 없음)

`git mv`로 이동하고, 아래 두 가지만 고친다(그 외 로직·산출물 경로·동작은 전혀 바꾸지 않는다):

1. `Path(__file__).resolve().parents[2]` → `parents[3]`(폴더가 한 단계 더 깊어졌으므로), `visualize_prediction.py`의 `Path(__file__).resolve().parent.parent.parent` → `.parent.parent.parent.parent`
2. `src/evaluation/collect_error_cases.py`의 `from evaluation.calculate_metrics import (...)` → `from evaluation.exp1.calculate_metrics import (...)`(같은 이유로 `sys.path`에 `src/`를 넣는 방식은 그대로 유지, import 경로만 한 단계 늘어남)

이동 대상(괄호 안은 이동 후 경로):

- `src/model/train_baseline.py` → `src/model/exp1/train_baseline.py`
- `src/model/run_inference.py` → `src/model/exp1/run_inference.py`
- `src/model/export_auto_labels.py` → `src/model/exp1/export_auto_labels.py`
- `src/model/compare_thresholds.py` → `src/model/exp1/compare_thresholds.py`
- `src/evaluation/calculate_metrics.py` → `src/evaluation/exp1/calculate_metrics.py`
- `src/evaluation/collect_error_cases.py` → `src/evaluation/exp1/collect_error_cases.py`
- `src/visualization/visualize_prediction.py` → `src/visualization/exp1/visualize_prediction.py`

이동하지 않는 것: `src/model/smoke_test.py`(실험 비교 대상이 아닌 1회성 점검 도구), `src/visualization/visualize_original_polygon.py`, `src/visualization/visualize_yolo_label.py`(실험과 무관한 데이터 준비 단계 도구).

## (B) `exp2/` 복사본 생성 (imgsz=960, 산출물 경로 분리)

위 7개 파일을 각각 `src/model/exp2/`, `src/evaluation/exp2/`, `src/visualization/exp2/`에 복사하고 다음을 바꾼다(그 외 로직은 exp1과 동일하게 유지):

1. `EXPERIMENT_ID = "EXP-P1-DET-001"` → `"EXP-P1-DET-002"` (해당되는 모든 파일)
2. `train_baseline.py`의 `EXPERIMENT_NAME = "RT_AL_YOLO26N_640_Baseline"` → `"RT_AL_YOLO26N_960_ImgszUp"`
3. `imgsz=640`/`IMAGE_SIZE = 640` → `imgsz=960`/`IMAGE_SIZE = 960` (학습·추론·평가 전부, 작업25 계획서(`docs/10_next_experiment_plan.md`)에 명시된 유일한 변경 변수)
4. `export_auto_labels.py`의 `MODEL_VERSION = "EXP-P1-DET-001"` → `"EXP-P1-DET-002"`
5. **산출물 경로에 `EXP-P1-DET-002` 하위 폴더 추가**(exp1은 그대로 두고, exp2만 아래처럼 변경):
   - `run_inference.py`: `predictions/prediction_results.json` → `predictions/EXP-P1-DET-002/prediction_results.json`, `outputs/predictions` → `outputs/EXP-P1-DET-002/predictions`
   - `export_auto_labels.py`: `PREDICTIONS_PATH`를 위와 동일하게 `predictions/EXP-P1-DET-002/prediction_results.json`으로, `OUTPUT_ROOT = auto-labels/` → `auto-labels/EXP-P1-DET-002/`
   - `visualize_prediction.py`: `predictions/prediction_results.json`·`auto-labels/...` 참조 경로를 위와 동일하게 `EXP-P1-DET-002` 하위로, `OUTPUT_ROOT`(`outputs/auto-label-visualization/`) → `outputs/EXP-P1-DET-002/auto-label-visualization/`, `MISMATCHES_PATH`(`metadata/auto_label_roundtrip_mismatches.csv`) → `reports/evaluation/EXP-P1-DET-002/auto_label_roundtrip_mismatches.csv`(exp2부터는 실험 산출물을 `metadata/`가 아니라 `reports/evaluation/<실험ID>/`로 모음)
   - `compare_thresholds.py`: `outputs/threshold-comparison/` → `outputs/EXP-P1-DET-002/threshold-comparison/`, `reports/evaluation/threshold_comparison.csv` → `reports/evaluation/EXP-P1-DET-002/threshold_comparison.csv`
   - `calculate_metrics.py`: `reports/evaluation/model_performance.csv`·`object_size_performance.csv` → `reports/evaluation/EXP-P1-DET-002/` 하위로, `model.val()`의 `project=`도 `reports/evaluation/EXP-P1-DET-002/evaluation`으로
   - `collect_error_cases.py`: `errors/` → `errors/EXP-P1-DET-002/`, `reports/evaluation/error_cases.csv`·`error_type_counts.csv` → `reports/evaluation/EXP-P1-DET-002/` 하위로
6. `collect_error_cases.py`(exp2)의 import는 `from evaluation.exp2.calculate_metrics import (...)`

## `.gitignore` 추가 (CLAUDE가 직접 처리 예정이므로 이 스크립트에서는 손대지 않음)

`reports/evaluation/EXP-P1-DET-002/evaluation/`이 새로 생기는데, 기존 `.gitignore`의 `reports/evaluation/evaluation/` 규칙은 exp1 전용이라 이 새 경로를 못 잡는다. **이 파일은 CODEX가 건드리지 말고 CLAUDE가 직접 처리한다.**

## 구현 범위 (In Scope)

- (A) 7개 파일 `exp1/`로 이동 + 경로 깊이·import 보정(동작 불변)
- (B) 7개 파일 `exp2/`에 생성 + 위 변경사항 반영

## 구현 제외 범위 (Out of Scope)

- `.gitignore` 수정 — CLAUDE가 직접 처리
- 실제 학습·추론 실행 — CODEX 샌드박스에서 Python 실행 불가, CLAUDE가 `venv/Scripts/python.exe`로 수행
- `docs/08_error_analysis.md`, `docs/10_next_experiment_plan.md` 등 PoC 전역 문서 수정 — 이번 작업 범위 아님
- `src/model/smoke_test.py`, `src/visualization/visualize_original_polygon.py`, `src/visualization/visualize_yolo_label.py` 이동 또는 수정

## 완료 기준 (Definition of Done)

- `( )` 기존 7개 스크립트가 `exp1/`로 이동됐고, 경로 깊이·import만 고쳐졌을 뿐 그 외 로직·산출물 경로는 원본과 100% 동일하다.
- `( )` `exp2/`에 7개 스크립트가 생성됐고, `EXPERIMENT_ID`/`imgsz`/산출물 경로가 위 명세대로 EXP-P1-DET-002 기준으로 바뀌었다.
- `( )` exp1과 exp2 스크립트를 각각 실행해도 서로의 산출물을 덮어쓰지 않는다(경로가 겹치지 않음).
- `( )` 코드가 PEP 8 / black 포맷을 따른다(ruff 통과).

## 제약사항

- exp1 스크립트의 로직·산출물 경로는 절대 바꾸지 않는다(이미 커밋되어 문서·리뷰가 참조 중).
- 이 작업은 CODEX 샌드박스에서 Python을 실행해 검증할 수 없다. 코드 작성까지만 CODEX가 담당하고, 실제 실행·검증은 CLAUDE가 수행한다.

## 테스트 방법 (CLAUDE가 이어서 수행)

1. `src/model/exp1/train_baseline.py` 등 7개 파일에서 `parents[3]`(또는 `.parent`×4) 확인, `grep -rn "EXP-P1-DET-001" src/model/exp1 src/evaluation/exp1 src/visualization/exp1`로 exp1 산출물 경로가 원본과 동일한지 확인
2. `grep -rn "EXP-P1-DET-002\|imgsz.*960\|IMAGE_SIZE = 960" src/model/exp2 src/evaluation/exp2 src/visualization/exp2`로 exp2 값 확인
3. `black --check`, `ruff check`를 `src/model/exp1 src/model/exp2 src/evaluation/exp1 src/evaluation/exp2 src/visualization/exp1 src/visualization/exp2`에 실행
4. exp1 스크립트 하나(예: `run_inference.py`)를 실제로 실행해 기존과 동일한 결과가 재현되는지 확인(회귀 테스트)
