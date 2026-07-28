# 1. 실험 기본 정보

- 실험 ID: EXP-P1-DET-006
- 실험명: RT_AL_YOLO26N_960_CLAHE
- 실험 상태: COMPLETED
- 작성자: 자동 기록
- 실험 시작 일시: 2026-07-28T18:58:03+09:00
- 실험 종료 일시: 2026-07-28T21:11:05+09:00
- 관련 단계: 작업17
- 실험 유형: DETECTION_TRAINING
- Git Branch: feature/exp006-clahe-preprocessing
- Git Commit: d07ed3e2bad9b8c718e6959b935793048d803084
- 설정 파일 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-006\train_config.yaml
- 결과 폴더 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-006\runs\train

# 2. 목적과 가설

- 실험 목적: AI-Hub RT·AL 데이터에서 Polygon을 Bounding Box로 변환한
  YOLO Detection 파이프라인이 정상적으로 학습되는지 검증한다.
- 검증할 핵심 질문: 새로운 Test 이미지에서 porosity와 slag_inclusion의
  위치를 예측할 수 있는 Baseline 성능을 얻을 수 있는가?
- 현재 문제: 전체 데이터셋으로 측정한 최초의 실제 성능 기준이 없다.
- 가설: 변환·검증된 dataset_v4로 두 결함 클래스를 학습하면 재현 가능한 최초 Baseline 지표를 얻을 수 있다.
- 예상 결과: 학습이 정상 종료되고 best/last 모델 및 Precision·Recall·mAP 지표가 생성된다.
- 성공 판단 기준: 예외 없이 정상 종료되고 필수 모델·로그·설정·시각화 산출물이 모두 보존된다.

# 3. 기준 실험

없음. 최초 Baseline.

# 5. 데이터셋 정보

## 5.1 데이터셋 식별

- 데이터셋 이름: ai_hub_welding_rt_al
- 데이터셋 버전: dataset_v4
- 데이터 출처: AI-Hub
- 검사 유형: RT
- 소재: AL
- 원본 라벨 형식: AI-Hub JSON Polygon
- 학습 라벨 형식: YOLO Detection
- 클래스 매핑: `metadata/yolo_classes.txt`
- 데이터 선정 목록: `metadata/v2/selected_dataset.csv`(선별 자체는 dataset_v2·v3와 동일 — dataset_v4는 dataset_v3 전체 이미지에 CLAHE만 적용한 것, 장수·분포는 dataset_v3와 동일)
- 데이터 검증 보고서: `reports/dataset/v2/`(Val·Test는 dataset_v2와 동일 구성), Train 구성: `src/dataset/v3/oversample_slag.py` 실행 결과(dataset_v3와 동일, 아래 표에 반영)

**[정정]** 이 절의 자동 생성 값은 `reports/dataset/v2/split_distribution.csv`(dataset_v2 기준, Train 오버샘플링 반영 전)를 그대로 참조한다. dataset_v4는 dataset_v3(Train 오버샘플링 적용됨)의 모든 이미지에 CLAHE만 적용한 것이라 장수·객체 수가 dataset_v3와 완전히 동일한데, 아래 표는 EXP-005와 동일하게 정정한 값이다. 모델 성능(9~14절)에는 영향이 없다 — 학습 자체는 처음부터 실제 dataset_v4(Train 482장, porosity 382객체·slag_inclusion 336객체)로 정상 진행됐다.

## 5.2 데이터 수 (정정됨)

| 구분 | 이미지 수 | 객체 수 |
| --- | ---: | ---: |
| Train | 482 | 718 |
| Validation | 85 | 141 |
| Test | 84 | 123 |
| 전체 | 651 | 982 |

## 5.3 클래스별 객체 분포 (정정됨)

| 클래스 | 클래스 ID | Train 객체 | Val 객체 | Test 객체 | 전체 객체 |
| --- | ---: | ---: | ---: | ---: | ---: |
| porosity | 3 | 382 | 111 | 84 | 577 |
| slag_inclusion | 4 | 336 | 30 | 39 | 405 |

## 5.4 데이터 분할 정보

- Train/Validation/Test 비율: 0.70 / 0.15 / 0.15
- Random Seed: 42
- 분할 방법 및 상세 분포: `dataset_summary.csv`

# 6. 전처리·변환 정보

- Polygon → Bounding Box 변환: 작업9 산출물 참조
- YOLO Detection 라벨 변환: 작업10 산출물 참조
- Bounding Box 계산: Polygon 좌표의 x/y 최솟값과 최댓값 사용
- 이미지 Resize: Ultralytics 기본 letterbox, 라이브러리 기본값
- Aspect Ratio 유지 및 Padding: Ultralytics letterbox 기본 동작
- 정규화: Ultralytics 라이브러리 기본값
- 학습 입력: `data/processed/dataset_v4/data.yaml`

# 7. 실행 환경

작업1에서 동일 머신·동일 가상환경으로 수집한 값을 재사용했다.

```text
System Information
  Python : 3.13.14
  OS     : Windows-11-10.0.26200-SP0
  CPU    : Intel64 Family 6 Model 198 Stepping 2, GenuineIntel
  RAM    : 31.46 GiB

Package Imports
  torch       : SUCCESS (2.13.0+cpu)
  ultralytics : SUCCESS (8.4.104)
  cv2         : SUCCESS (5.0.0)
  numpy       : SUCCESS (2.5.1)
  pandas      : SUCCESS (3.0.3)
  matplotlib  : SUCCESS (3.11.1)
  yaml        : SUCCESS (6.0.3)

Compute Device
  CUDA Available : No
  Device         : CPU

Pretrained Model
  yolo26n.pt: SUCCESS

certifi==2026.6.17
charset-normalizer==3.4.9
contourpy==1.3.3
cycler==0.12.1
filelock==3.32.0
fonttools==4.63.0
fsspec==2026.6.0
idna==3.18
Jinja2==3.1.6
kiwisolver==1.5.0
MarkupSafe==3.0.3
matplotlib==3.11.1
mpmath==1.3.0
networkx==3.6.1
numpy==2.5.1
nvidia-ml-py==13.610.43
opencv-python==5.0.0.93
packaging==26.2
pandas==3.0.3
pillow==12.3.0
polars==1.43.0
polars-runtime-32==1.43.0
psutil==7.2.2
pyparsing==3.3.2
python-dateutil==2.9.0.post0
PyYAML==6.0.3
requests==2.34.2
setuptools==83.0.0
six==1.17.0
sympy==1.14.0
torch==2.13.0
torchvision==0.28.0
typing_extensions==4.16.0
tzdata==2026.3
ultralytics==8.4.104
ultralytics-thop==2.0.20
urllib3==2.7.0
```

- 실행 장비: 로컬 Windows 머신
- 실행 경로: C:\develop\widep\defect_detection_ai_test
- 가상환경: `venv`
- Docker 사용 여부: 아니오
- 인터넷 연결 필요 여부: 아니오

# 8. 모델 및 학습 설정

## 8.1 모델 정보

- 라이브러리: ultralytics
- 작업 유형: detect
- 모델 계열: YOLO26
- 모델 크기: n
- 사전 학습 가중치: yolo26n.pt
- 사전 학습 사용 여부: 예
- 클래스 수: 2
- 모델 파일 경로: C:\develop\widep\defect_detection_ai_test\yolo26n.pt

## 8.2 학습 설정

| 설정 | 값 |
| --- | --- |
| Epoch | 50 |
| Patience | 15 |
| Image Size | 960 |
| Batch Size 요청값 | -1 (auto) |
| 실제 Batch Size | 16 |
| Optimizer | auto |
| Initial Learning Rate | library default (0.01) |
| Weight Decay | library default (0.0005) |
| AMP | library default (True) |
| Device | cpu |
| Workers | 0 |
| Seed | 42 |
| Deterministic | True |
| Cache | True |

## 8.3 데이터 증강 설정

커스텀 증강 설정 없이 Ultralytics library default를 사용했다.

| 증강 | 값 | 기본값 변경 |
| --- | --- | --- |
| HSV Hue | library default (0.015) | 아니오 |
| HSV Saturation | library default (0.7) | 아니오 |
| HSV Value | library default (0.4) | 아니오 |
| Rotation | library default (0.0) | 아니오 |
| Translation | library default (0.1) | 아니오 |
| Scale | library default (0.5) | 아니오 |
| Horizontal Flip | library default (0.5) | 아니오 |
| Vertical Flip | library default (0.0) | 아니오 |
| Mosaic | library default (1.0) | 아니오 |
| MixUp | library default (0.0) | 아니오 |

# 9. 학습 실행 결과

- 학습 시작 일시: 2026-07-28T18:58:03+09:00
- 학습 종료 일시: 2026-07-28T21:11:05+09:00
- 총 실행 시간: 02:13:02
- 정상 종료 여부: 예
- Early Stopping 여부: 아니오
- 종료 Epoch: **50**(스크립트 자동 판정은 "51"로 잘못 기록됨 — 아래 "9.0 발견한 버그" 참조)
- Best Epoch: **36**(스크립트 자동 판정은 "37"로 잘못 기록됨 — 아래 참조)
- Best 모델 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-006\models\best.pt
- Last 모델 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-006\models\last.pt
- 결과 폴더: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-006\runs\train

## 9.0 발견한 버그: `read_results()`의 Epoch 번호가 항상 1 많게 표시됨 (EXP-005에서 발견, 동일 재현)

EXP-005에서 발견한 것과 동일한 버그다(`train_baseline.py`의 `read_results()`가 `epoch + 1`로 계산하는데 Ultralytics `results.csv`의 `epoch`는 이미 1부터 시작). 이번엔 EXP-003에서 발견한 fitness 공식 버그(`0.1*mAP50+0.9*mAP50-95` vs 실제 `mAP50-95` 단독)를 함께 확인한 결과 **두 공식이 같은 epoch(36)을 가리켰다** — 그래서 9.1절의 수치 자체는 정정할 필요가 없고, Epoch 번호 표시만 위와 같이 정정했다. `best.pt` 선택에는 영향 없음(Ultralytics 자체 기준으로 저장).

## 9.1 학습 결과 요약

| 지표 | Best 결과 | Last 결과 |
| --- | ---: | ---: |
| Train Loss (Box+Class+L1) | 3.436680 | 3.024610 |
| Validation Loss (Box+Class+L1) | 4.472330 | 4.154760 |
| Precision | 0.634100 | 0.433360 |
| Recall | 0.396850 | 0.390540 |
| mAP50 | 0.453100 | 0.385960 |
| mAP50-95 | 0.160630 | 0.140840 |

Best epoch loss:

- Box Loss: 1.711510
- Class Loss: 1.720090
- L1 Loss: 0.005080

## 9.2 학습 과정 해석

총 학습 시간 02:13:02로 EXP-005(02:10:53)와 거의 동일하다(Train 이미지 수가 482장으로 동일하고, CLAHE 전처리는 학습 전에 이미 끝나 있어 학습 자체의 연산량에 영향을 주지 않는다). Best(epoch 36)와 Last(epoch 50)의 지표 차이가 EXP-005와 비슷한 폭으로 존재해, 학습 곡선의 전반적 형태 자체는 정상이었다 — 다만 도달한 최종 성능 수준 자체가 아래에서 보듯 EXP-005보다 낮다.

# 10. 추론 설정

- Confidence Threshold: 0.25(기존과 동일)
- IoU Threshold: 0.70
- Image Size: 960
- Device: cpu
- Test 이미지: 84장 전체 추론 성공(84/84), 자동 라벨 export 및 CVAT 라운드트립 검증 PASS

# 11. 전체·클래스별 성능

## 11.1 전체 성능

| 지표 | EXP-005(dataset_v3) | EXP-006(dataset_v4, CLAHE) |
| --- | ---: | ---: |
| Precision | 0.535 | 0.544 |
| Recall | 0.446 | **0.350**(↓) |
| mAP50 | 0.342 | **0.295**(↓) |
| **mAP50-95(주 지표)** | **0.131** | **0.103**(↓) |

## 11.2 클래스별 성능

| 클래스 | EXP-005 Recall | EXP-006 Recall | EXP-005 mAP50-95 | EXP-006 mAP50-95 |
| --- | ---: | ---: | ---: | ---: |
| porosity | 0.405 | **0.262**(↓) | - | 0.120 |
| slag_inclusion | 0.487 | **0.359**(↓) | - | 0.086 |

두 클래스 모두 Recall이 뚜렷하게 하락했다 — CLAHE가 특정 클래스에만 악영향을 준 것이 아니라 전반적으로 탐지 성능을 낮췄다.

## 11.3 객체 크기별 성능

| 크기 | GT 수 | TP | FN | Recall(EXP-006) | Recall(EXP-005) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Small | 87 | 25 | 62 | 0.287 | 0.356(↓) |
| Medium | 33 | 12 | 21 | 0.364 | 0.515(↓) |
| Large | 3 | 0 | 3 | 0.000 | 0.000 |

Small·Medium 모두 EXP-005보다 하락했다 — 애초에 겨냥했던 "저대비·작은 결함" 개선 효과가 나타나지 않았다.

# 12. Threshold 비교

| Threshold | Precision | Recall | mAP50 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: |
| 0.10 | 0.377 | 0.488 | 0.343 | 0.118 |
| 0.25(현재) | 0.544 | 0.350 | 0.295 | 0.103 |
| 0.50 | 0.808 | 0.171 | 0.156 | 0.057 |
| 0.75 | 1.000 | 0.041 | 0.028 | 0.012 |

EXP-005의 0.25 기준 결과(Precision 0.561, Recall 0.447, mAP50-95 0.131 — 12.1절 참고)와 비교하면 전 구간에서 EXP-006이 낮다. Threshold를 조정해도 이 격차를 만회할 수 없다(가장 낮은 Threshold인 0.10에서도 mAP50-95 0.118로 EXP-005의 0.25 기준치 0.131에 못 미친다).

# 13. 정성 평가

위치 오류(localization_error) 대표 사례 `RT_AL_02_14487829_001`(EXP-005에서도 같은 이미지를 확인했던 사례)을 다시 확인한 결과, **CLAHE 적용 후에도 "예측 박스가 GT보다 작게 그려지는" 패턴이 그대로 남아있다**(Confidence 0.298) — 애초에 겨냥했던 문제 자체가 해결되지 않았다.

미탐(false_negative) 사례 `RT_AL_02_14487914_001`을 확인한 결과, 이미지 배경에 **뚜렷한 청회색 색조 얼룩과 수평 경계선(밝기 구간이 갈라지는 띠)**이 보였다 — CLAHE를 LAB L 채널에만 적용했음에도 원본 이미지의 미세한 색 편차(JPEG 압축 아티팩트 등)가 대비 강화 과정에서 두드러지게 나타난 것으로 보인다. 이런 인위적인 명암 패턴이 실제 결함 신호와 섞이면서 모델이 진짜 결함(작은 porosity)을 놓치는 데 영향을 줬을 가능성이 있다.

# 14. 원인 분석

## 14.1 오류 유형 집계

| 오류 유형 | EXP-005 | EXP-006 |
| --- | ---: | ---: |
| 미탐(false_negative) | 63 | 75 |
| 오탐(false_positive) | 38 | 28 |
| 위치 오류(localization_error) | 11 | 10 |
| 클래스 오류(wrong_class) | 1 | 1 |

미탐이 63→75건으로 늘고 오탐이 38→28건으로 줄었다 — Recall 하락·Precision 소폭 상승과 일치한다. 위치 오류는 11→10건으로 사실상 변화 없다(겨냥했던 문제가 개선되지 않았음을 다시 보여준다).

## 14.2 원인 판단

- **CLAHE 대비 강조 가설은 이번 실험으로 반증됐다.** 위치 오류 건수·정성 사례 모두 개선되지 않았고, 오히려 전체 Recall·mAP가 하락했다.
- **추정 원인 1 — 사전학습 가중치와의 불일치**: `yolo26n.pt`는 일반 자연 이미지 통계로 사전학습됐다. CLAHE로 전체 데이터셋의 픽셀 분포를 균일하게 바꾸면, 사전학습된 저수준 특징(에지·텍스처 필터)이 이 변경된 분포에 맞지 않아 전이 학습 효과가 줄어들 수 있다.
- **추정 원인 2 — CLAHE의 부작용(아티팩트)**: 13절에서 확인했듯 CLAHE 적용 후 인위적인 색조·경계 패턴이 나타난 사례가 있다. 이미 대비가 충분한 영역까지 균일하게 강화하면서 원본에 없던 노이즈성 패턴을 만들어낸 것으로 보인다.
- 두 가설 모두 이번 실험 하나로 확증할 수는 없다 — 원인을 분리하려면 별도 실험(예: CLAHE 강도를 낮추거나 저대비 이미지에만 선택적으로 적용)이 필요하지만, 이는 이번 PoC 범위를 벗어난다.

# 15. Baseline 비교

| 항목 | EXP-005(dataset_v3) | EXP-006(dataset_v4, CLAHE) | 변화 |
| --- | --- | --- | --- |
| 변경 변수 | - | Train/Val/Test 전체 이미지에 CLAHE 적용 | - |
| 학습 시간 | 02:10:53(50 epoch, 미발동) | 02:13:02(50 epoch, 미발동) | 거의 동일 |
| 전체 mAP50-95 | 0.131 | 0.103 | **-0.028** |
| localization_error 건수 | 11 | 10 | -1(사실상 동일) |
| slag_inclusion Recall | 0.487 | 0.359 | **-0.128** |
| porosity Recall | 0.405 | 0.262 | **-0.143** |

## 성공 기준 대비 판정 (`docs/13_next_experiment_plan.md` 기준)

| 기준 | 목표 | 실제 결과 | 충족 여부 |
| --- | --- | --- | --- |
| 주 지표: 전체 mAP50-95 | EXP-005(0.131) 대비 개선 | 0.103 | **미충족(오히려 하락)** |
| 보조 지표: localization_error 건수 | EXP-005(11건) 대비 감소 | 10건 | 형식상 감소지만 실질적 개선 아님(정성 평가에서 동일 패턴 확인) |
| 가드레일 1: slag_inclusion Recall | 0.40 이상 | 0.359 | **미충족** |
| 가드레일 2: porosity Recall | 0.30 이상 | 0.262 | **미충족** |

# 16. 결론

**CLAHE 대비 강조 전처리는 명확한 실패다.** 주 지표(mAP50-95)와 두 가드레일(porosity·slag_inclusion Recall)이 모두 목표를 충족하지 못했고, 애초에 겨냥했던 박스 위치 정밀도 문제도 정성적으로 전혀 개선되지 않았다. 사전학습 가중치와의 통계 불일치, CLAHE 자체의 아티팩트(14.2절)가 원인으로 추정된다.

**dataset_v4는 채택하지 않는다. dataset_v3(EXP-005)를 계속 최종 Baseline으로 유지한다.** 이로써 EXP-005 이후 시도한 두 가지 추가 개선(Threshold 재선정, CLAHE)이 모두 유의미한 개선을 만들지 못했다 — Threshold 재선정은 "개선 여지 없음"으로 결론났고(EXP-005 12.1절), 이번 CLAHE는 명확한 퇴보였다.

# 17. 다음 실험 계획

박스 위치 정밀도 문제에 대한 남은 후보는 모델 크기 확대(yolo26n→yolo26s)뿐이나, 학습 비용이 크고 지금까지 두 번의 targeted fix 시도가 모두 실패한 점을 감안하면 추가 실험보다는 **작업26(PoC 결과 문서화)으로 넘어가는 것을 권장한다.** 박스 위치 정밀도 문제는 5개 실험(EXP-001~005) 내내, 그리고 이번 CLAHE 시도에서도 개선되지 않은 "알려진 미해결 한계"로 최종 문서에 정직하게 기록한다.
