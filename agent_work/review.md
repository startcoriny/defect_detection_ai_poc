# 코드 리뷰: EXP-005 Threshold 재선정 스크립트 생성

## 요구사항 충족 여부

- `src/model/exp5/select_threshold.py` 신규 생성 — `compare_thresholds.py`를 복사해 threshold 튜플(0.25~0.50, 0.05 간격), `report_path`, `metrics_project`/`prediction_project` 3곳만 변경. `diff --strip-trailing-cr` 확인 결과 의도한 3곳 외 차이 없음.
- 기존 `compare_thresholds.py`와 `threshold_comparison.csv`는 변경되지 않음 확인.
- black/ruff 통과.

## 실행 결과

- `venv/Scripts/python.exe src/model/exp5/select_threshold.py` 실행(재학습 없이 기존 `best.pt`로 평가만 반복, CPU) — 6개 threshold 전부 정상 완료, `reports/evaluation/EXP-P1-DET-005/threshold_selection.csv` 생성 확인.

## 핵심 결과

| Threshold | Precision | Recall | mAP50-95 |
| --- | ---: | ---: | ---: |
| 0.25(현재) | 0.561 | 0.447 | 0.131 |
| 0.30 | 0.667 | 0.374 | 0.114 |
| 0.35 | 0.706 | 0.293 | 0.100 |
| 0.40 | 0.714 | 0.244 | 0.090 |
| 0.45 | 0.786 | 0.179 | 0.071 |
| 0.50 | 0.889 | 0.130 | 0.062 |

Threshold를 올릴수록 Precision·Recall이 거의 1:1로 맞바꿔지는 단조 감소 형태 — 뚜렷하게 유리한 구간 없음. 자동 라벨링(사람 검수) 파이프라인 특성상 미탐 비용이 오탐 비용보다 크다고 판단해 **현재 Threshold 0.25 유지**를 권장, `experiment.md` 12.1절에 반영.

## 결과

새 실험 ID 없이 EXP-005 문서에 추가 분석(12.1절)으로 반영 완료. 17절(다음 실험 계획)도 "Threshold 재선정 완료(0.25 유지)"로 갱신.
