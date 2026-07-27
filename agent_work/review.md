# 코드 리뷰: EXP-004 스크립트 생성 (dataset_v2 기반)

## 요구사항 충족 여부

- `src/model/exp4/`, `src/evaluation/exp4/`, `src/visualization/exp4/`에 7개 생성 — 확인
- `EXPERIMENT_ID`/`EXPERIMENT_NAME`/`MODEL_VERSION`, 데이터 경로(`dataset_v1`→`dataset_v2`) 전부 exp2 대비 지정된 대로 치환 — `diff --strip-trailing-cr`로 확인
- 학습 하이퍼파라미터(imgsz=960, box=7.5, epochs=50, patience=15 등)는 exp2와 완전히 동일 — diff로 확인, 데이터 경로·실험 ID 외 차이 없음
- black/ruff 전부 통과

## 발견한 문제 및 수정 (CLAUDE가 직접 수정, 스코프 한정)

CODEX가 만든 exp4 스크립트에서 exp2 원본에 있던 **dataset_v1 전용 하드코딩 상수**를 두 종류 놓친 것을 발견해 CLAUDE가 직접 고쳤다(둘 다 기계적인 상수 치환이라 CODEX에 재위임하지 않고 바로 수정):

1. **Test 이미지 개수 하드코딩(46 → 84)**: `export_auto_labels.py`의 `EXPECTED_IMAGE_COUNT`, `compare_thresholds.py`의 `TEST_IMAGE_COUNT`, `calculate_metrics.py`의 `EXPECTED_IMAGE_COUNT`, `visualize_prediction.py`의 CVAT 구조 검증(`train_count == 46`, `image_count == 46`, `label_count == 46`, `total_count == 92`)이 dataset_v1의 Test 개수(46)를 그대로 갖고 있었다. dataset_v2의 실제 Test 개수(84, `total_count`는 84+84=168)로 수정. `export_auto_labels.py` 실행 시 `expected=46, actual=84` 오류로 실제로 발견됨.
2. **`dataset_summary.csv` 생성 경로 버그**: `train_baseline.py`(exp4)가 `reports/dataset/split_distribution.csv`(dataset_v1 경로)를 그대로 복사해 `experiment.md` 5.2·5.3절에 dataset_v1의 수치(Train 332객체 등)가 잘못 기록됐다. `reports/dataset/v2/split_distribution.csv`로 경로를 고치고, 이미 생성된 `dataset_summary.csv`와 `experiment.md` 5.1~5.3절을 실제 dataset_v2 수치로 수동 정정했다. **학습 자체(`model.train(data=...)`)는 처음부터 올바르게 `dataset_v2/data.yaml`을 사용했으므로, 이 버그는 문서화 산출물에만 있었고 모델 성능·평가 결과에는 영향이 없다.**

## 실행 결과 (전체 파이프라인)

- 학습: 50 epoch 완주(Early Stopping 미발동), 1.859시간. Best epoch(fitness=mAP50-95 기준) 41(0-index) — 기존 `read_results()`의 `0.1*mAP50+0.9*mAP50-95` 공식으로도 동일 epoch을 가리켜(EXP-001/002와 동일 패턴) 별도 정정 불필요.
- 추론: Test 84장 전체 성공(84/84)
- 자동 라벨 export + 라운드트립 검증: PASS(불일치 0건, CVAT 구조 확인)
- Threshold 비교, 전체 평가(`calculate_metrics.py`), 오류 사례 수집(`collect_error_cases.py`) 정상 실행

## 핵심 결과 (EXP-002 대비)

- porosity Recall 0.143→0.298(주 지표, 목표 0.25 이상 충족)
- Small Recall 0.121→0.241(가드레일 충족)
- mAP50-95 0.075→0.082(가드레일 충족)
- slag_inclusion Recall 0.333→0.179(회귀, 클래스별 데이터 증가 비율 불균등 추정 — porosity 약 2.4배 vs slag 약 1.2배)

## 사용자가 직접 확인하는 방법

1. `diff --strip-trailing-cr src/model/exp2/train_baseline.py src/model/exp4/train_baseline.py` — 하이퍼파라미터 외 차이 없는지 확인
2. `cat experiments/EXP-P1-DET-004/dataset_summary.csv` — dataset_v2 실제 수치(porosity 575, slag_inclusion 237) 확인
3. `cat reports/evaluation/EXP-P1-DET-004/model_performance.csv` — 전체·클래스별 성능 확인

## 결과

완료 조건 전부 충족. 발견된 2건의 하드코딩 버그는 스코프 한정으로 직접 수정했고, 둘 다 모델 성능이 아닌 검증·문서화 로직에 국한된 문제였음을 확인했다.
