# 구현 지시서: EXP-007 스크립트 생성 (모델 크기 확대, yolo26n→yolo26s)

## 배경

EXP-P1-DET-007은 `docs/decisions/14_next_experiment_plan.md`에 따라 **dataset_v3**(EXP-005가 채택한 최종 Baseline — dataset_v4는 EXP-006에서 실패로 폐기됨)를 그대로 사용하고, 모델만 `yolo26n.pt` → `yolo26s.pt`로 바꾼다. `yolo26s.pt`는 프로젝트 루트에 이미 다운로드돼 있다(10,009,784 파라미터, 22.8 GFLOPs). 학습 하이퍼파라미터는 EXP-P1-DET-005(imgsz=960, box=7.5, epochs=50, patience=15)와 완전히 동일하게 유지한다.

## 기능 및 요구사항

`src/model/exp5/`, `src/evaluation/exp5/`, `src/visualization/exp5/`의 7개 스크립트를 각각 `src/model/exp7/`, `src/evaluation/exp7/`, `src/visualization/exp7/`로 복사하고 다음만 바꾼다. **데이터셋 경로(`dataset_v3`)는 그대로 유지한다 — 이번 실험은 dataset_v3를 그대로 쓰고 모델만 바뀐다.**

1. `EXPERIMENT_ID = "EXP-P1-DET-005"` → `"EXP-P1-DET-007"` (해당되는 모든 파일: `train_baseline.py`, `run_inference.py`, `compare_thresholds.py`, `calculate_metrics.py`, `collect_error_cases.py`, `visualize_prediction.py`) — exp5의 `select_threshold.py`는 exp5 전용 추가 분석 파일이라 복사 대상 아님(exp5의 원래 7개 스크립트만 복사)
2. `export_auto_labels.py`의 `MODEL_VERSION = "EXP-P1-DET-005"` → `"EXP-P1-DET-007"`
3. `train_baseline.py`의 `EXPERIMENT_NAME = "RT_AL_YOLO26N_960_SlagOversample"` → `"RT_AL_YOLO26S_960_SlagOversample"`
4. **모델 파일**: `train_baseline.py`에서 `yolo26n.pt`를 가리키는 부분(예: `project_root / "yolo26n.pt"`, 메타데이터 문자열 `"weights": "yolo26n.pt"`, 문서 텍스트의 "모델 크기: n", "사전 학습 가중치: yolo26n.pt", "모델 파일 경로: ... yolo26n.pt")을 전부 `yolo26s.pt` / "모델 크기: s"로 바꾼다. `imgsz=960, box=7.5, epochs=50, patience=15, batch=-1, optimizer="auto", device="cpu"` 등 학습 하이퍼파라미터는 절대 건드리지 않는다.
5. **데이터셋 경로는 그대로 `dataset_v3` 유지** — 다른 파일(`run_inference.py`, `compare_thresholds.py`, `calculate_metrics.py`, `collect_error_cases.py`, `visualize_prediction.py`, `export_auto_labels.py`)에는 애초에 모델 경로 언급이 없으므로 EXPERIMENT_ID 문자열 변경 외에는 exp5와 동일해야 한다.
6. Test 이미지 개수 하드코딩(84)은 그대로 유지한다. `reports/dataset/v2/split_distribution.csv` 참조 부분도 exp5와 동일하게 유지한다.
7. 산출물 경로(`predictions/`, `auto-labels/`, `outputs/`, `reports/evaluation/`, `errors/`)에 들어가는 실험 ID 하위 폴더는 1번 변경만으로 자동으로 `EXP-P1-DET-007`이 되도록(exp5와 동일한 구조 유지)
8. `collect_error_cases.py`(exp7)의 import를 `from evaluation.exp7.calculate_metrics import (...)`로 변경

## 구현 범위 (In Scope)

- `src/model/exp7/`, `src/evaluation/exp7/`, `src/visualization/exp7/`에 7개 스크립트 생성

## 구현 제외 범위 (Out of Scope)

- exp1~exp6 스크립트 수정 — 절대 건드리지 않는다
- 데이터셋(`dataset_v3`) 변경 — 이번 작업 범위 아님
- 실제 학습·추론 실행 — CLAUDE가 수행
- `.gitignore`, `docs/*.md` 수정 — 이번 작업 범위 아님

## 완료 기준 (Definition of Done)

- `( )` exp7의 7개 스크립트에 `EXP-P1-DET-005` 잔재가 전혀 없다(`grep -rn "EXP-P1-DET-005" src/*/exp7` 결과 0건).
- `( )` `train_baseline.py`(exp7)에 `yolo26n` 잔재가 전혀 없다(전부 `yolo26s`로 교체).
- `( )` exp7의 다른 6개 스크립트(`train_baseline.py` 제외)는 `dataset_v3` 경로가 exp5와 동일하게 유지된다(변경 없음).
- `( )` Test 이미지 개수 관련 하드코딩 상수가 84로 유지돼 있다(exp5와 동일).
- `( )` `train_baseline.py`(exp7)의 `imgsz`, `box`, `epochs`, `patience` 등 학습 하이퍼파라미터가 exp5와 완전히 동일하다(모델 관련 항목만 다름).
- `( )` exp5와 exp7의 산출물 경로가 겹치지 않는다.
- `( )` 코드가 PEP 8 / black 포맷을 따른다(ruff 통과).

## 제약사항

- `src/model/exp5/`, `src/evaluation/exp5/`, `src/visualization/exp5/`는 읽기만 하고 수정하지 않는다.
- 이 작업은 CODEX 샌드박스에서 Python을 실행해 검증할 수 없다. 코드 작성까지만 CODEX가 담당하고, 실제 실행·검증은 CLAUDE가 수행한다.

## 테스트 방법 (CLAUDE가 이어서 수행)

1. `grep -rn "EXP-P1-DET-005\|EXP-P1-DET-007" src/model/exp7 src/evaluation/exp7 src/visualization/exp7`로 잔재 확인
2. `grep -rn "yolo26n\|yolo26s" src/model/exp7/train_baseline.py`로 모델 경로 확인
3. `diff --strip-trailing-cr src/model/exp5/train_baseline.py src/model/exp7/train_baseline.py`로 모델 관련 항목 외 변경이 없는지 확인
4. `diff --strip-trailing-cr src/model/exp5/run_inference.py src/model/exp7/run_inference.py` 등 나머지 파일도 EXPERIMENT_ID 외 차이가 없는지 확인
5. `black --check`, `ruff check`를 exp7 7개 파일에 실행
