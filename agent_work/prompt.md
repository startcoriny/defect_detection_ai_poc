# 구현 지시서: imgsz 확대 실험 (EXP-P1-DET-009)

## 배경

`EXP-P1-DET-005`(imgsz 960)부터 지금까지 "Small 객체(상대 면적 1% 미만) Recall이 낮다"는 문제가 반복돼왔다(EXP-005 기준 Small Recall 0.356, 라이브 데모에서도 "Small porosity 미탐" 실패 사례로 실제 확인됨). `EXP-P1-DET-008`(GPU, imgsz 960)에서 GPU 학습이 CPU 대비 6.39배 빠르다는 것을 확인했으니, 이번엔 그 여유를 활용해 imgsz를 960→1280으로 키우면 Small 객체 Recall이 개선되는지 검증한다.

비교 변수는 imgsz 단 하나여야 한다. 기준 실험은 EXP-008(GPU, imgsz 960)이다 — device는 이미 GPU로 고정된 상태에서 imgsz만 바꿔 순수하게 해상도 효과만 분리한다. 이번 실험은 학습만으로는 끝나지 않는다. Small Recall을 실제로 확인하려면 Test 추론과 크기별 평가까지 필요하다(EXP-005가 이미 거친 것과 동일한 평가 방식).

사용자는 이번에도 GPU 서버(Ubuntu, Claude Code 없음)에서 직접 실행한다.

## 기능 및 요구사항

### A. `src/model/exp9/train_baseline.py`

`src/model/exp8/train_baseline.py`를 복사한 뒤 아래만 변경한다(그 외 exp8의 CUDA fail-fast, 실행 시점 환경 캡처 로직은 그대로 유지).

1. `EXPERIMENT_ID = "EXP-P1-DET-009"`, `EXPERIMENT_NAME = "RT_AL_YOLO26N_1280_ImgszSmallObject"`
2. `model.train(...)`의 `imgsz=960`을 `imgsz=1280`으로 변경한다.
3. 목적/가설/기준실험 텍스트를 imgsz 취지로 다시 쓴다.
   - 목적: EXP-P1-DET-008과 동일 설정(GPU, dataset_v3, YOLO26n, epochs=50 등)에서 imgsz만 960→1280으로 키워 Small 객체 Recall 개선 여부를 검증한다.
   - 가설: imgsz 외 모든 설정이 동일할 때, imgsz 1280이 960보다 Small 객체(상대 면적 1% 미만) Recall을 유의미하게 개선한다.
   - 기준 실험: `EXP-P1-DET-008` (동일 GPU, imgsz=960).
4. `build_experiment_data()`의 `"training": {..., "imgsz": ...}`가 960이 아니라 1280을 반영하도록 확인한다(코드가 `actual_args`에서 읽어오는 구조라면 자동 반영되므로, 하드코딩된 값이 남아있지 않은지만 확인).
5. exp8에서 추가했던 **"9.2 CPU Baseline 대비 비교" 절은 이번 실험 취지(속도 비교가 아니라 imgsz 비교)에 맞지 않으므로 제거**하고, exp5/6/7 원래의 "9.2 학습 과정 해석"(정량·정성 해석은 후속 평가에서 작성한다는 취지의 짧은 문구) 형태로 되돌린다. `CPU_BASELINE_SECONDS` 상수와 관련 로직도 함께 제거한다.

### B. `src/model/exp9/run_inference.py`

`src/model/exp5/run_inference.py`를 그대로 복사해 상수만 변경한다.
- `EXPERIMENT_ID = "EXP-P1-DET-009"`
- `IMAGE_SIZE = 1280`
- `DEVICE = "0"`

### C. `src/evaluation/exp9/calculate_metrics.py`

`src/evaluation/exp5/calculate_metrics.py`를 그대로 복사해 상수만 변경한다.
- `EXPERIMENT_ID = "EXP-P1-DET-009"`
- `IMAGE_SIZE = 1280`
- `DEVICE = "0"`
- `classify_size()`의 크기 버킷 기준(상대 면적 0.01 / 0.05)은 그대로 둔다(imgsz와 무관한 기준이라 EXP-005와 직접 비교 가능해야 한다).

## 참고해야 할 문서/코드

- `src/model/exp8/train_baseline.py` (복사 원본 A)
- `src/model/exp5/run_inference.py`, `src/evaluation/exp5/calculate_metrics.py` (복사 원본 B, C)
- `experiments/EXP-P1-DET-005/experiment.md`의 "11.3 객체 크기별 성능"(Small Recall 0.356 등 비교 기준값)
- `experiments/EXP-P1-DET-008/experiment.md` (이번 실험의 기준 실험 데이터)

## 구현 제외 범위 (Out of Scope)

- Threshold 비교, 오류 사례 수집(`compare_thresholds.py`, `collect_error_cases.py`) 등은 만들지 않는다. 이번 요청은 학습 + 추론 + 크기별 평가까지가 범위다.
- `setup_gpu_env.sh`는 수정하지 않는다(EXP-008에서 이미 검증됨, 그대로 재사용).
- `experiment.md`의 10~17절(추론 설정, 성능, 결론 등) 서술 내용을 CODEX가 채우지 않는다 — 이 부분은 실제 실행 결과가 나온 뒤 CLAUDE가 작성한다. 기존 placeholder("실험 후 작성") 그대로 둔다.

## 완료 기준 (Definition of Done)

- 세 파일(`src/model/exp9/train_baseline.py`, `src/model/exp9/run_inference.py`, `src/evaluation/exp9/calculate_metrics.py`)이 존재하고 문법 검사를 통과한다.
- `black`, `ruff` 통과.
- `diff src/model/exp8/train_baseline.py src/model/exp9/train_baseline.py`로 위 A절 1~5 항목 외 의도치 않은 변경이 없는지 확인한다.
- `diff src/model/exp5/run_inference.py src/model/exp9/run_inference.py`, `diff src/evaluation/exp5/calculate_metrics.py src/evaluation/exp9/calculate_metrics.py`로 상수 외 변경이 없는지 확인한다.
- 이 저장소에는 GPU가 없어 실제 실행 검증은 사용자가 GPU 서버에서 수행한다. 실행 순서는 다음과 같다.
  1. `venv/bin/python src/model/exp9/train_baseline.py`
  2. `venv/bin/python src/model/exp9/run_inference.py`
  3. `venv/bin/python src/evaluation/exp9/calculate_metrics.py`
  4. 결과 확인 대상: `experiments/EXP-P1-DET-009/experiment.md`, `reports/evaluation/EXP-P1-DET-009/object_size_performance.csv`

## 제약사항

- 파일 헤더/주석 스타일은 원본과 동일한 컨벤션을 유지한다.
- 예외를 삼키지 않는다(기존 exp5/exp8과 동일한 실패 처리 방식 유지).
