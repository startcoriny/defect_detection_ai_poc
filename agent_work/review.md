# 코드 리뷰: Confidence Threshold 비교 (`src/model/compare_thresholds.py`)

## 요구사항 충족 여부

- Confidence 0.10/0.25/0.50/0.75 4개, 나머지 설정(iou=0.70, imgsz=640, device=cpu) 고정 — 확인
- `model.val(..., plots=True)`로 Confusion Matrix 확보 후 TP/FP/FN 직접 계산(하드코딩 재구현 없이 Ultralytics 로직 재사용) — 확인
- `reports/evaluation/threshold_comparison.csv` 4행 생성 — 확인
- Threshold별 예측 시각화 이미지 46장×4 — 확인
- `project=` 절대경로 사용, 개별 이미지 순회+실패 격리 — 확인
- black/ruff 통과 — 확인(black은 CLAUDE가 재포맷 적용)

## 발견한 사항 (버그 아님, 중요한 해석상 주의점)

`model.val()`의 NMS는 `multi_label=True`로 동작하는 반면(Ultralytics `val.py:106-127`, 공식 평가 관례와 일치 — mAP/Precision/Recall을 공인된 방식대로 계산하려면 이게 맞다), 실제 배포 경로인 `model.predict()`(작업19~21이 실제로 쓰는 방식)는 `multi_label=False`가 기본값이다(`predict.py`가 이 인자를 넘기지 않아 `nms.py`의 기본값 `False`를 그대로 씀). 그 결과 이 스크립트의 `predicted_count`/`avg_labels_per_image`/`fp_to_remove`/`fn_to_add`는 **평가 관례상의 multi-label 집계**이지, 실제 오토라벨링 배포에서 사람이 보게 될 라벨 수와는 다르다.

실제로 직접 `model.predict()`로 재확인한 결과(코드 수정 없이 별도 검증):

| Threshold | CSV(`predicted_count`, multi-label 평가 기준) | 실제 배포(`predict()`, single-label) |
| --- | ---: | ---: |
| 0.10 | 59 | 49 |
| 0.25 | 16 | 13 |
| 0.50 | 1 | **0** |
| 0.75 | 0 | 0 |

0.50에서 특히 주목할 점: CSV는 "TP 1건"을 보고하지만, 실제 배포 방식으로는 그 threshold에서 **탐지되는 결함이 하나도 없다**. 이건 코드 버그가 아니라 두 NMS 모드의 근본적인 차이이며, 스코프 수정 대상이 아니라 **해석 시 반드시 병기해야 하는 사실**이다. Precision/Recall/mAP(`ultra_mp` 등, `metrics.box.*`)는 공식 평가 지표라 그대로 신뢰 가능하지만, "이미지당 평균 라벨 수"·"삭제해야 하는 오탐 수" 같은 실무 워크로드 해석에는 이 표 대신 위 실측 single-label 수치를 함께 봐야 한다.

## 실행 결과

```
threshold,predicted_count,tp,fp,fn,precision,recall,avg_labels_per_image,...
0.10,59,23,36,35,0.390,0.397,1.283,...
0.25,16,12,4,46,0.750,0.207,0.348,...
0.50,1,1,0,57,1.000,0.017,0.022,...
0.75,0,0,0,58,,0.000,0.000,...
```

- 4개 Threshold 모두 처리 완료, 각 46장씩 시각화 이미지 생성 확인
- black `--check`, ruff `check` 통과

## 사용자가 직접 확인하는 방법

1. `venv/Scripts/python.exe src/model/compare_thresholds.py` 실행(4×46장 처리, CPU로 수 초~수십 초)
2. `reports/evaluation/threshold_comparison.csv` — 4행 확인
3. `outputs/threshold-comparison/images/conf_<값>/` — 각 46장, threshold가 높을수록 박스가 줄어드는지 육안 확인
4. 위 "발견한 사항"의 single-label 실측치는 재현하려면 `model.predict()`를 Test 46장에 개별 호출해 `len(result.boxes)`를 합산

## 결과

완료 조건 4개(설정 고정, 비교표 생성, Threshold별 이미지 생성, black/ruff 통과) 모두 충족. 다만 "이미지당 평균 라벨 수" 등 워크로드 지표는 CSV 값 그대로 인용하지 않고 위 표의 single-label 실측치를 함께 제시해야 함 — `experiment.md`의 "12. Threshold 비교" 절 작성 시 반영 예정.
