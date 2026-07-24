# 구현 지시서: EXP-003 스크립트 생성 (box loss gain 7.5→15.0)

## 배경

EXP-P1-DET-002(imgsz 640→960)는 부분적 성공이었다 — 전체 Recall·mAP50-95·Medium 객체 Recall은 개선됐지만, 원래 목표였던 Small 객체 Recall은 개선되지 않았다(`experiments/EXP-P1-DET-002/experiment.md` 15~17절). 대신 EXP-001·EXP-002 공통으로 **박스 위치 정밀도 부족**(mAP50이 mAP50-95의 2~4배, 위치 오류 사례에서 예측 박스가 GT보다 체계적으로 작게 나옴)이 관찰됐다. 이번 실험(EXP-P1-DET-003)은 **imgsz=960은 그대로 유지**하고(EXP-002의 개선분을 잃지 않기 위함), Ultralytics 학습 하이퍼파라미터 중 박스 좌표 회귀에 직접 관여하는 `box`(box loss gain, 기본값 7.5)를 **15.0으로 2배 올리는 것 하나만** 변경한다.

**사전 확인한 사실**: `venv/Lib/site-packages/ultralytics/cfg/default.yaml`에서 `box: 7.5 # (float) box loss gain`을 확인했다. `model.train(..., box=15.0, ...)`처럼 `model.train()`에 직접 키워드 인자로 전달 가능한 표준 Ultralytics 하이퍼파라미터다.

## 기능 및 요구사항

`src/model/exp2/`, `src/evaluation/exp2/`, `src/visualization/exp2/`의 7개 스크립트를 각각 `src/model/exp3/`, `src/evaluation/exp3/`, `src/visualization/exp3/`로 복사하고 다음만 바꾼다(그 외 로직·`imgsz`(960 유지)·산출물 경로 구조는 exp2와 동일한 패턴을 그대로 따르되 실험 ID만 교체):

1. `EXPERIMENT_ID = "EXP-P1-DET-002"` → `"EXP-P1-DET-003"` (해당되는 모든 파일: `train_baseline.py`, `run_inference.py`, `compare_thresholds.py`, `calculate_metrics.py`, `collect_error_cases.py`, `visualize_prediction.py`)
2. `export_auto_labels.py`의 `MODEL_VERSION = "EXP-P1-DET-002"` → `"EXP-P1-DET-003"`
3. `train_baseline.py`의 `EXPERIMENT_NAME = "RT_AL_YOLO26N_960_ImgszUp"` → `"RT_AL_YOLO26N_960_BoxGain15"`
4. `train_baseline.py`의 `model.train(...)` 호출에 **`box=15.0`**을 새로 추가한다(`imgsz=960`은 그대로 둔다). 다른 하이퍼파라미터(epochs=50, patience=15, batch=-1, optimizer="auto" 등)는 EXP-002와 완전히 동일하게 유지한다.
5. 산출물 경로(`predictions/`, `auto-labels/`, `outputs/`, `reports/evaluation/`, `errors/`)에 들어가는 실험 ID 하위 폴더도 자동으로 `EXP-P1-DET-003`이 되도록(이미 EXP-002에서 `EXPERIMENT_ID` 변수를 참조하는 구조이므로 1번 변경만으로 따라감 — 별도 하드코딩된 경로가 있는지 확인)
6. `collect_error_cases.py`(exp3)의 import를 `from evaluation.exp3.calculate_metrics import (...)`로 변경

## 구현 범위 (In Scope)

- `src/model/exp3/`, `src/evaluation/exp3/`, `src/visualization/exp3/`에 7개 스크립트 생성

## 구현 제외 범위 (Out of Scope)

- exp1, exp2 스크립트 수정 — 절대 건드리지 않는다
- 실제 학습·추론 실행 — CLAUDE가 수행
- `.gitignore`, `docs/*.md` 수정 — 이번 작업 범위 아님

## 완료 기준 (Definition of Done)

- `( )` exp3의 7개 스크립트에 `EXP-P1-DET-002` 잔재가 전혀 없다(`grep -rn "EXP-P1-DET-002" src/*/exp3` 결과 0건).
- `( )` `train_baseline.py`(exp3)에 `box=15.0`이 `model.train()` 호출에 추가돼 있고, `imgsz=960`은 그대로다.
- `( )` exp2와 exp3의 산출물 경로가 겹치지 않는다.
- `( )` 코드가 PEP 8 / black 포맷을 따른다(ruff 통과).

## 제약사항

- `src/model/exp2/`, `src/evaluation/exp2/`, `src/visualization/exp2/`는 읽기만 하고 수정하지 않는다.
- 이 작업은 CODEX 샌드박스에서 Python을 실행해 검증할 수 없다. 코드 작성까지만 CODEX가 담당하고, 실제 실행·검증은 CLAUDE가 수행한다.

## 테스트 방법 (CLAUDE가 이어서 수행)

1. `grep -rn "EXP-P1-DET-002\|EXP-P1-DET-003" src/model/exp3 src/evaluation/exp3 src/visualization/exp3`로 잔재 확인
2. `grep -n "box=15.0\|imgsz=960" src/model/exp3/train_baseline.py`로 하이퍼파라미터 확인
3. `black --check`, `ruff check`를 exp3 7개 파일에 실행
