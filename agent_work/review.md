# 코드 리뷰: 모델 성능 평가 (`src/evaluation/calculate_metrics.py`)

## 요구사항 충족 여부

- 전체·클래스별 Precision/Recall/AP50/AP50-95를 Ultralytics `model.val()`로 산출(재구현 없음) — 확인
- 객체 크기별(Small/Medium/Large) Recall을 직접 IoU 매칭으로 산출(작업12 기준 재사용, 실제 배포와 동일한 single-label `predict()` 사용) — 확인
- `reports/evaluation/{model_performance.csv, object_size_performance.csv}` 생성 — 확인
- Confusion Matrix 경로 로그 — 확인
- `project=` 절대경로 사용 — 확인
- black/ruff 통과 — 확인(black은 CLAUDE가 재포맷 적용)

## 발견한 문제 → 직접 조치(스코프 한정, gitignore만)

`model.val(project=report_dir, name="evaluation")`가 `reports/evaluation/evaluation/`에 PR curve 등 대용량 이미지(약 1.8MB, `BoxF1_curve.png` 등 10개 파일)를 그대로 남긴다. 기존 `.gitignore`에 `experiments/*/runs/`는 있지만 이 새 경로는 빠져 있어, 그대로 두면 대용량 이미지가 커밋될 뻔했다. `.gitignore`에 `reports/evaluation/evaluation/` 한 줄을 추가해 제외했다(코드 변경 아님, CODEX 재호출 없이 직접 처리 — 기존 gitignore 정책과 동일한 성격의 추가).

## 실행 결과

```
model_performance.csv:
overall,all,0.6746,0.1881,0.1749,0.0433
class,porosity,0.5714,0.1429,0.1370,0.0235
class,slag_inclusion,0.7778,0.2333,0.2128,0.0631

object_size_performance.csv:
Small,33,4,29,0.1212
Medium,24,4,20,0.1667
Large,1,0,1,0.0000
```

- `gt_count` 합계(33+24+1=58)가 Test 전체 객체 수(58)와 정확히 일치(교차 검증)
- `overall` 행이 `compare_thresholds.py`(작업22)에서 conf=0.25로 직접 확인했던 값(mp=0.6746, mr=0.1881, map50=0.1749, map50_95=0.0433)과 정확히 일치(같은 조건이므로 당연히 같아야 하고, 실제로 같음 — 재현성 확인)
- `confusion_matrix.png` 육안 확인: porosity→porosity 5, porosity→background 2, slag→slag 7, slag→background 1, slag→porosity(오분류) 1, background→porosity(미탐) 22, background→slag(미탐) 23. **이 값은 작업18에서 확인했던 것(배경 오탐 1833/926건)과 완전히 다르다** — 작업18의 그래프는 학습 중 Ultralytics 내부 검증(낮은 conf로 sweep, mAP 계산용)에서 나온 것이고, 이번 것은 실제 배포 조건(conf=0.25)으로 명시적으로 재평가한 결과라 신뢰도가 더 높다. 이 차이는 `experiment.md` 11절에 명확히 정리해야 함.
- black `--check`, ruff `check` 통과

## 사용자가 직접 확인하는 방법

1. `venv/Scripts/python.exe src/evaluation/calculate_metrics.py` 실행(수십 초)
2. `reports/evaluation/model_performance.csv` — overall 1행 + 클래스 2행 확인
3. `reports/evaluation/object_size_performance.csv` — Small/Medium/Large 3행, `gt_count` 합 58 확인
4. `reports/evaluation/evaluation/confusion_matrix.png` 육안 확인(단, 이 폴더는 gitignore 대상이라 로컬에만 존재)

## 결과

완료 조건 5개(전체 지표, 클래스별 지표, 객체 크기별 Recall, Confusion Matrix 경로 로그, black/ruff 통과) 모두 충족. `experiment.md` "11. 전체·클래스별 성능" 절 작성은 이 리뷰 이후 별도로 진행.
