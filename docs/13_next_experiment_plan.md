# EXP-P1-DET-006 실험 계획: CLAHE 대비 강조 전처리

## 1. 문제 정의

EXP-001부터 EXP-005까지 5개 실험 내내 "예측 박스가 GT보다 작게 그려지는" 위치 오류(localization_error) 패턴이 해결되지 않았다(`experiments/EXP-P1-DET-005/experiment.md` 13절·14.2절). EXP-005에서도 localization_error가 11건(porosity 5, slag_inclusion 6) 발생했고, mAP50(0.342) 대비 mAP50-95(0.131)의 격차가 커 — IoU 기준을 엄격히 할수록 성능이 크게 떨어진다는 것은 박스가 GT와 정확히 겹치지 않는다는 뜻이다.

`data/processed/dataset_v3/images/test` 샘플 5장의 그레이스케일 표준편차를 확인한 결과 16.1~41.2로 폭넓게 낮은 대비 영역이 존재함을 확인했다(용접 RT 이미지 특성상 결함 경계가 흐릿한 경우가 많음). **가설**: 결함 경계의 저대비가 모델이 결함의 실제 범위를 정확히 인식하지 못하게 해 박스를 작게 그리게 만든다. CLAHE(Contrast Limited Adaptive Histogram Equalization)로 지역 대비를 강화하면 경계가 더 뚜렷해져 박스 위치·크기 정밀도가 개선될 것이다.

## 2. 검토한 후보와 기각 이유

| 후보 | 내용 | 채택 여부 |
| --- | --- | --- |
| Box loss gain 확대 | EXP-003에서 7.5→15.0 시도, 효과 없이 기각됨 | 기각(이미 검증됨) |
| 모델 크기 확대(yolo26n→yolo26s) | 모델 용량 증가로 정밀도 개선 가능 | 이번엔 보류 — 학습 비용이 크고, "박스 정밀도"라는 특정 문제에 대한 인과관계가 CLAHE보다 간접적. CLAHE로 개선이 없으면 다음 후보로 검토 |
| CLAHE 대비 강조 | 채택 | 아래 참조 |

### 구현 방식 결정: 전체 이미지 전처리(dataset_v4) vs Ultralytics 내장 Albumentations 증강

Ultralytics는 `albumentations` 패키지가 설치돼 있으면 자동으로 CLAHE를 포함한 증강을 추가하지만 **기본 확률이 0.01(1%)로 고정돼 있고 `train()` 인자로 노출되지 않는다**(`ultralytics/data/augment.py`의 `Albumentations` 클래스). 이 정도 확률로는 유의미한 변화를 기대하기 어렵고, Train에만 적용되고 Val/Test 분포는 그대로라 학습·평가 조건이 어긋난다.

대신 **`data/processed/dataset_v3`의 모든 이미지(Train/Val/Test)에 CLAHE를 결정론적으로 적용**해 `dataset_v4`를 새로 만든다. 라벨(YOLO 좌표)은 기하 변형이 없으므로 그대로 복사한다. OpenCV(`cv2.createCLAHE`)가 이미 설치돼 있어 새 의존성 설치가 필요 없다(EXP-005 설계 시 "새 의존성 필요"로 기각했던 이유가 해소됨).

## 3. 변경 변수 (In Scope)

- `src/dataset/v4/apply_clahe.py`(신규): `dataset_v3`의 Train/Val/Test 이미지 전체에 CLAHE 적용(`clipLimit=2.0`, `tileGridSize=(8,8)` — OpenCV 기본 권장값) 후 `dataset_v4`에 저장. 라벨은 그대로 복사. `data.yaml` 재생성.
- `src/model/exp6/`, `src/evaluation/exp6/`, `src/visualization/exp6/`: exp5를 복사해 `dataset_v3`→`dataset_v4` 경로만 교체. 하이퍼파라미터(imgsz=960, box=7.5, epochs=50, patience=15)는 EXP-005와 완전히 동일하게 유지 — CLAHE 적용 여부만 유일한 변수.

## 4. 고정 조건 (Out of Scope)

- Train/Val/Test 분할 구성은 dataset_v3와 동일(이미지 내용만 CLAHE로 변경, 장수·클래스 분포·slag_inclusion 오버샘플링 상태 불변)
- 학습 하이퍼파라미터, 모델 크기(yolo26n) 변경 없음
- Threshold는 EXP-005 결론(0.25 유지)을 그대로 따름

## 5. 성공 기준

| 기준 | 목표 | 판단 방식 |
| --- | --- | --- |
| 주 지표: 전체 mAP50-95 | EXP-005(0.131) 대비 개선 | mAP50-95는 IoU 임계값을 0.5~0.95로 엄격하게 평균한 지표라, 박스 위치·크기 정밀도가 좋아지면 가장 먼저 반응한다 |
| 보조 지표: localization_error 건수 | EXP-005(11건) 대비 감소 | `collect_error_cases.py` 오류 유형 집계 기준 |
| 가드레일 1: slag_inclusion Recall | EXP-005(0.487) 대비 크게 하락하지 않음(0.40 이상) | 오버샘플링으로 얻은 성과를 CLAHE가 훼손하지 않는지 확인 |
| 가드레일 2: porosity Recall | EXP-005(0.405) 대비 크게 하락하지 않음(0.30 이상) | 상동 |

## 6. 후속 우선순위

이번 실험이 효과가 없다면 모델 크기 확대(yolo26n→yolo26s)를 다음 후보로 검토한다. 효과가 있다면 dataset_v4를 이후 실험의 기본 데이터셋으로 채택하고, 그 시점에 작업26(PoC 결과 문서화) 진입을 재검토한다.
