# 구현 지시서: EXP-005 Threshold 재선정 스크립트 생성

## 배경

EXP-P1-DET-005의 `src/model/exp5/compare_thresholds.py`는 이미 `CONFIDENCE_THRESHOLDS = (0.10, 0.25, 0.50, 0.75)` 네 지점만 비교해 `reports/evaluation/EXP-P1-DET-005/threshold_comparison.csv`를 생성·보존하고 있다(재학습 없이 기존 `best.pt`로 평가만 반복하는 스크립트).

기존 결과를 보면 0.25→0.50 구간에서 Precision(0.561→0.889)과 Recall(0.447→0.130)이 급격히 갈린다. 배포용 운영 threshold를 정하려면 이 구간을 더 세밀하게 스캔해야 한다. 단, exp5는 이미 사용된(리포트가 확정된) 폴더이므로 기존 `compare_thresholds.py`와 그 출력 파일은 절대 덮어쓰지 않는다.

## 기능 및 요구사항

`src/model/exp5/compare_thresholds.py`를 복사해 같은 폴더에 `src/model/exp5/select_threshold.py`를 새로 만들고 다음만 바꾼다.

1. `CONFIDENCE_THRESHOLDS = (0.10, 0.25, 0.50, 0.75)` → `(0.25, 0.30, 0.35, 0.40, 0.45, 0.50)`로 변경. (0.25/0.50은 기존 결과와 대조 검증용으로 재사용, 그 사이 4개 지점을 새로 추가)
2. `main()`의 `report_path`를 `reports/evaluation/EXP-P1-DET-005/threshold_comparison.csv` → `reports/evaluation/EXP-P1-DET-005/threshold_selection.csv`로 변경 (기존 파일과 충돌 금지).
3. `compare_thresholds()`의 `metrics_project`, `prediction_project`를 각각 `outputs/EXP-P1-DET-005/threshold-comparison/metrics`, `outputs/EXP-P1-DET-005/threshold-comparison/images` → `outputs/EXP-P1-DET-005/threshold-selection/metrics`, `outputs/EXP-P1-DET-005/threshold-selection/images`로 변경 (기존 폴더와 충돌 금지).
4. 그 외 로직(모델 경로, 데이터셋 경로 `dataset_v3`, IoU=0.70, imgsz=960, device="cpu" 등)은 전혀 건드리지 않는다.

## 구현 범위 (In Scope)

- `src/model/exp5/select_threshold.py` 신규 생성 1개 파일

## 구현 제외 범위 (Out of Scope)

- `src/model/exp5/compare_thresholds.py` 및 그 출력 파일(`threshold_comparison.csv`, `outputs/EXP-P1-DET-005/threshold-comparison/`) 수정 — 절대 건드리지 않는다
- exp1~exp4 관련 스크립트 수정
- 재학습, 새 실험 ID 부여, 데이터셋 변경
- 스크립트 실행 — CLAUDE가 수행

## 완료 기준 (Definition of Done)

- `( )` `src/model/exp5/select_threshold.py`가 존재하고 `compare_thresholds.py`와 diff 시 threshold 튜플·report_path·project 경로 3곳 외 차이가 없다.
- `( )` 기존 `src/model/exp5/compare_thresholds.py`와 `reports/evaluation/EXP-P1-DET-005/threshold_comparison.csv`는 변경되지 않았다.
- `( )` black/ruff 통과.

## 제약사항

- `compare_thresholds.py`는 읽기만 하고 수정하지 않는다.
- 이 작업은 CODEX 샌드박스에서 Python을 실행해 검증할 수 없다. 코드 작성까지만 CODEX가 담당하고, 실제 실행·검증은 CLAUDE가 수행한다.

## 테스트 방법 (CLAUDE가 이어서 수행)

1. `diff --strip-trailing-cr src/model/exp5/compare_thresholds.py src/model/exp5/select_threshold.py`로 의도한 3곳 외 차이가 없는지 확인
2. `black --check src/model/exp5/select_threshold.py`, `ruff check src/model/exp5/select_threshold.py`
3. `venv/Scripts/python.exe src/model/exp5/select_threshold.py` 실행 후 `reports/evaluation/EXP-P1-DET-005/threshold_selection.csv` 생성 확인
