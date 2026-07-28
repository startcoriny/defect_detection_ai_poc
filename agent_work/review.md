# 코드 리뷰: EXP-005 스크립트 생성 (dataset_v3 기반, Train slag_inclusion 오버샘플링)

## 요구사항 충족 여부

- `src/dataset/v3/oversample_slag.py` 생성 — Val·Test 원본 그대로 복사, Train은 전량 복사 후 slag_inclusion 포함 이미지만 `_dup1`로 추가 복제. 지시대로 구현 확인.
- `src/model/exp5/`, `src/evaluation/exp5/`, `src/visualization/exp5/`에 7개 생성 — `EXPERIMENT_ID`/`EXPERIMENT_NAME`/`MODEL_VERSION`, 데이터 경로(`dataset_v2`→`dataset_v3`) 전부 exp4 대비 지정된 대로 치환. `diff --strip-trailing-cr`로 확인.
- 학습 하이퍼파라미터는 exp4와 완전히 동일 — diff로 확인.
- Test 이미지 개수 하드코딩(84)은 dataset_v3의 Test가 dataset_v2와 동일하므로 손대지 않는 것이 맞고, 실제로 손대지 않았음을 확인.
- black/ruff 전부 통과.

## 실행 결과 (전체 파이프라인)

- `oversample_slag.py` 실행: Train 398→482장(slag_inclusion 포함 84장 복제), slag_inclusion 객체 168→336(정확히 2배), porosity 380→382(둘 다 있는 이미지 1장 함께 복제). Val·Test는 dataset_v2와 diff 결과 완전히 동일 확인.
- 학습: 50 epoch 완주(Early Stopping 미발동), 2.179시간.
- 추론: Test 84장 전체 성공(84/84)
- 자동 라벨 export + 라운드트립 검증: PASS(불일치 0건, CVAT 구조 확인)
- Threshold 비교, 전체 평가(`calculate_metrics.py`), 오류 사례 수집(`collect_error_cases.py`) 정상 실행

## 발견한 버그 2건 (CLAUDE가 직접 정정, 스코프 한정)

1. **section 5.2/5.3 Train 객체 수가 dataset_v2(오버샘플링 전) 수치를 그대로 참조**: `reports/dataset/v2/split_distribution.csv`를 그대로 쓰도록 지시했는데, 이미지 수(482)는 실제 폴더를 세어 정확하지만 Train 객체 수는 오버샘플링 반영 전 수치(548)였다. `oversample_slag.py` 실행 로그의 실제 수치(718 = porosity 382 + slag_inclusion 336)로 experiment.md를 수동 정정.
2. **Epoch 번호 표시 버그(신규 발견, EXP-001부터 있었을 것으로 추정)**: `train_baseline.py`의 `read_results()`가 `best_epoch = int(best_row["epoch"]) + 1`로 계산하는데, Ultralytics `results.csv`의 `epoch` 컬럼은 이미 1부터 시작하는 값이라(직접 확인: 50 epoch 학습 시 첫 행 1, 마지막 행 50) `+1`이 불필요하다. "종료 Epoch"·"Best Epoch"가 항상 실제보다 1 크게 표시된다. `best.pt` 선택·성능 수치에는 영향 없음(Ultralytics 자체 기준으로 저장). EXP-005만 정정했고, EXP-001~004는 순수 표시 문제라 재정정하지 않았다(사용자에게 보고, 필요 시 요청 대기).

부수적으로 EXP-003에서 발견했던 fitness 공식 버그도 이번엔 실제로 다른 epoch(37 vs 47)을 가리켜, 9.1절 Best 결과를 진짜 Best(mAP50-95 기준 epoch 37)로 정정했다(둘의 mAP50-95 차이는 0.0003 수준으로 결론에는 영향 없음).

## 핵심 결과 (EXP-004 대비)

- slag_inclusion Recall 0.179→0.487(주 지표, 목표 0.30 이상 크게 초과 충족) — EXP-002(0.333)보다도 높음
- porosity Recall 0.298→0.405(가드레일 충족, 오히려 개선)
- 전체 mAP50-95 0.082→0.131(가드레일 충족)
- Precision 0.798→0.535(트레이드오프, 오탐 9→38건) — Recall-Precision 트레이드오프로 예상된 결과

## 사용자가 직접 확인하는 방법

1. `venv/Scripts/python.exe src/dataset/v3/oversample_slag.py` 재실행 — 로그의 Train 복제 전/후 개수 확인
2. `diff --strip-trailing-cr src/model/exp4/train_baseline.py src/model/exp5/train_baseline.py` — 하이퍼파라미터 외 차이 없는지 확인
3. `cat reports/evaluation/EXP-P1-DET-005/model_performance.csv` — 전체·클래스별 성능 확인

## 결과

완료 조건 전부 충족. 발견된 2건의 버그는 스코프 한정으로 직접 수정했고, 모두 모델 성능이 아닌 문서화 로직에 국한된 문제였음을 확인했다.
