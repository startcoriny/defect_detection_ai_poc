# 1. 실험 기본 정보

- 실험 ID: EXP-P1-DET-007
- 실험명: RT_AL_YOLO26S_960_SlagOversample
- 실험 상태: COMPLETED
- 작성자: 자동 기록
- 실험 시작 일시: 2026-07-28T22:05:42+09:00
- 실험 종료 일시: 2026-07-29T08:07:07+09:00
- 관련 단계: 작업17
- 실험 유형: DETECTION_TRAINING
- Git Branch: feature/exp007-model-size
- Git Commit: 695f820d43064a2e6d033f853acaa7f1ce8b11e3
- 설정 파일 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-007\train_config.yaml
- 결과 폴더 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-007\runs\train

# 2. 목적과 가설

- 실험 목적: AI-Hub RT·AL 데이터에서 Polygon을 Bounding Box로 변환한
  YOLO Detection 파이프라인이 정상적으로 학습되는지 검증한다.
- 검증할 핵심 질문: 새로운 Test 이미지에서 porosity와 slag_inclusion의
  위치를 예측할 수 있는 Baseline 성능을 얻을 수 있는가?
- 현재 문제: 전체 데이터셋으로 측정한 최초의 실제 성능 기준이 없다.
- 가설: 변환·검증된 dataset_v3로 두 결함 클래스를 학습하면 재현 가능한 최초 Baseline 지표를 얻을 수 있다.
- 예상 결과: 학습이 정상 종료되고 best/last 모델 및 Precision·Recall·mAP 지표가 생성된다.
- 성공 판단 기준: 예외 없이 정상 종료되고 필수 모델·로그·설정·시각화 산출물이 모두 보존된다.

# 3. 기준 실험

없음. 최초 Baseline.

# 5. 데이터셋 정보

## 5.1 데이터셋 식별

- 데이터셋 이름: ai_hub_welding_rt_al
- 데이터셋 버전: dataset_v3
- 데이터 출처: AI-Hub
- 검사 유형: RT
- 소재: AL
- 원본 라벨 형식: AI-Hub JSON Polygon
- 학습 라벨 형식: YOLO Detection
- 클래스 매핑: `metadata/yolo_classes.txt`
- 데이터 선정 목록: `metadata/v2/selected_dataset.csv`(선별 자체는 dataset_v2·v3와 동일 — EXP-005와 동일한 dataset_v3를 그대로 사용, 이번 실험의 변수는 모델 크기뿐)
- 데이터 검증 보고서: `reports/dataset/v2/`(Val·Test는 dataset_v2와 동일 구성), Train 구성: `src/dataset/v3/oversample_slag.py` 실행 결과(EXP-005와 완전히 동일)

**[정정]** EXP-005·EXP-006과 동일한 원인으로 이 절의 자동 생성 값이 stale하다(`reports/dataset/v2/split_distribution.csv` 참조, Train 오버샘플링 반영 전). dataset_v3를 그대로 쓰므로 EXP-005와 완전히 동일한 값으로 정정한다.

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
- 학습 입력: `data/processed/dataset_v3/data.yaml`

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
- 모델 크기: s
- 사전 학습 가중치: yolo26s.pt
- 사전 학습 사용 여부: 예
- 클래스 수: 2
- 모델 파일 경로: C:\develop\widep\defect_detection_ai_test\yolo26s.pt

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

- 학습 시작 일시: 2026-07-28T22:05:42+09:00
- 학습 종료 일시: 2026-07-29T08:07:07+09:00
- 총 실행 시간: 10:01:26
- 정상 종료 여부: 예
- Early Stopping 여부: 예(patience=15)
- 종료 Epoch: **39**(스크립트 자동 판정은 "40"으로 잘못 기록됨 — 아래 "9.0 발견한 버그" 참조)
- Best Epoch: **24**(스크립트 자동 판정은 "25"로 잘못 기록됨 — 아래 참조)
- Best 모델 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-007\models\best.pt
- Last 모델 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-007\models\last.pt
- 결과 폴더: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-007\runs\train

## 9.0 발견한 버그: `read_results()`의 Epoch 번호가 항상 1 많게 표시됨 (EXP-005·006에서 발견, 동일 재현)

EXP-005·EXP-006과 동일한 버그다(`results.csv`의 `epoch`가 이미 1부터 시작하는데 `+1`을 더 더함). 이번에도 fitness 신·구 공식이 같은 epoch(24)을 가리켜 9.1절 수치는 정정할 필요가 없고, Epoch 번호 표시만 정정했다.

## 9.1 학습 결과 요약

| 지표 | Best 결과 | Last 결과 |
| --- | ---: | ---: |
| Train Loss (Box+Class+L1) | 4.033570 | 3.236840 |
| Validation Loss (Box+Class+L1) | 3.050160 | 3.148420 |
| Precision | 0.605240 | 0.569260 |
| Recall | 0.456710 | 0.423870 |
| mAP50 | 0.469930 | 0.390250 |
| mAP50-95 | 0.186870 | 0.137450 |

Best epoch loss:

- Box Loss: 1.957550
- Class Loss: 2.069670
- L1 Loss: 0.006350

## 9.2 학습 과정 해석

총 학습 시간 10:01:26으로 EXP-005(02:10:53)의 약 4.6배다 — yolo26s의 파라미터·GFLOPs가 yolo26n의 약 4배인 것과 대략 비례한다. Patience=15로 Early Stopping이 발동해 39 epoch에서 종료됐다(Best epoch 24). **Val 기준 Best mAP50-95(0.187)는 EXP-005의 Val 기준(0.166)보다 뚜렷이 높다** — 그러나 아래 11절에서 보듯 Test셋 성능은 오히려 하락했다. Val과 Test 간 성능 격차가 EXP-005(0.166→0.131, 격차 0.035)보다 EXP-007(0.187→0.089, 격차 0.098)에서 약 2.8배 크게 벌어진 것은 **모델 용량 확대로 인한 과적합**을 시사한다(14절 참고).

# 10. 추론 설정

- Confidence Threshold: 0.25(기존과 동일)
- IoU Threshold: 0.70
- Image Size: 960
- Device: cpu
- Test 이미지: 84장 전체 추론 성공(84/84), 자동 라벨 export 및 CVAT 라운드트립 검증 PASS

# 11. 전체·클래스별 성능

## 11.1 전체 성능

| 지표 | EXP-005(yolo26n) | EXP-007(yolo26s) |
| --- | ---: | ---: |
| Precision | 0.535 | 0.621 |
| Recall | 0.446 | **0.293**(↓) |
| mAP50 | 0.342 | **0.210**(↓) |
| **mAP50-95(주 지표)** | **0.131** | **0.089**(↓) |

## 11.2 클래스별 성능

| 클래스 | EXP-005 Recall | EXP-007 Recall | EXP-005 mAP50-95 | EXP-007 mAP50-95 |
| --- | ---: | ---: | ---: | ---: |
| porosity | 0.405 | 0.321(↓, 가드레일 0.30 근소 충족) | - | 0.099 |
| slag_inclusion | 0.487 | **0.179**(↓↓, 가드레일 0.40 미충족) | - | 0.079 |

slag_inclusion Recall이 EXP-004 회귀 수준(0.179)까지 다시 떨어졌다 — EXP-005가 오버샘플링으로 어렵게 회복시킨 효과가 모델 크기 확대로 무너졌다.

## 11.3 객체 크기별 성능

| 크기 | GT 수 | TP | FN | Recall(EXP-007) | Recall(EXP-005) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Small | 87 | 23 | 64 | 0.264 | 0.356(↓) |
| Medium | 33 | 7 | 26 | 0.212 | 0.515(↓↓) |
| Large | 3 | 0 | 3 | 0.000 | 0.000 |

# 12. Threshold 비교

| Threshold | Precision | Recall | mAP50 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: |
| 0.10 | 0.434 | 0.431 | 0.283 | 0.119 |
| 0.25(현재) | 0.621 | 0.293 | 0.210 | 0.089 |
| 0.50 | 0.773 | 0.138 | 0.107 | 0.049 |
| 0.75 | 1.000 | 0.008 | 0.008 | 0.004 |

가장 낮은 Threshold(0.10)에서도 mAP50-95 0.119로 EXP-005의 0.25 기준치(0.131)에 못 미친다 — Threshold 조정으로 만회할 수 있는 격차가 아니다.

# 13. 정성 평가

위치 오류(localization_error) 건수 자체는 11→5건으로 크게 줄었다. 사례 `RT_AL_02_14488048_001`을 확인한 결과, 예측 박스(신뢰도 0.553)가 GT와 상당히 가깝게 겹쳐 있었다 — 그동안 5개 실험 내내 반복됐던 "절반 크기로 축소된 박스" 패턴보다 확실히 개선된 형태다. 또한 EXP-005·EXP-006에서 계속 위치 오류로 잡히던 대표 사례(`RT_AL_02_14487829`)는 이번엔 **위치 오류·미탐·오탐 어디에도 나타나지 않았다** — 정상 탐지(TP)로 전환된 것으로 보인다.

다만 미탐(false_negative) 사례 `RT_AL_02_14487812_001`을 확인한 결과, 육안으로 거의 식별 불가능한 극히 옅은 GT 박스였다 — 모델이 이런 애매한 신호에 더 보수적으로 반응하게 된 것으로 보인다(미탐 63→86건 급증과 일치).

**요약**: 실제로 탐지에 성공한 경우의 박스 정밀도는 개선됐지만, 애매한 신호에 대해 아예 탐지를 포기하는 경향이 강해져 전체 Recall이 크게 희생됐다.

# 14. 원인 분석

## 14.1 오류 유형 집계

| 오류 유형 | EXP-005 | EXP-007 |
| --- | ---: | ---: |
| 미탐(false_negative) | 63 | **86**(↑↑) |
| 오탐(false_positive) | 38 | **12**(↓↓) |
| 위치 오류(localization_error) | 11 | **5**(↓, 목표 달성) |
| 클래스 오류(wrong_class) | 1 | 2 |

## 14.2 원인 판단

- **모델 크기 확대는 "박스 정밀도"라는 좁은 목표에는 부분적으로 성공했다.** 위치 오류 건수가 절반 이하로 줄었고, 정성적으로도 박스가 더 정확하게 그려지는 사례를 확인했다.
- **그러나 전체 지표(mAP50-95, Recall)는 명확히 악화됐다 — 과적합이 원인으로 추정된다.** yolo26s는 yolo26n 대비 파라미터가 약 4배(10.0M vs 2.5M)인데, Train 데이터는 482장으로 동일하다. 9.2절에서 확인했듯 Val-Test 성능 격차가 EXP-005보다 약 2.8배 크게 벌어졌다 — 모델이 Val 성능은 높게 달성했지만 그 개선분이 Test로 일반화되지 못했다.
- **미탐 급증(63→86)이 Recall 하락의 직접 원인이다.** 정성 사례(13절)에서 보듯 극히 애매한 신호에 대해 모델이 더 보수적으로(예측을 포기하는 쪽으로) 반응하는 경향이 늘었다 — 큰 모델이 작은 데이터셋에서 오히려 "자신 있는 것만 예측"하는 방향으로 수렴했을 가능성이 있다.
- slag_inclusion Recall이 EXP-004 회귀 수준으로 되돌아간 것은, 오버샘플링으로 만든 클래스 균형 효과가 모델 용량이 커지면서 상대적으로 약해졌기 때문일 수 있다(더 큰 모델이 여전히 상대적으로 적은 slag_inclusion 노출을 다시 과소적합했을 가능성).

# 15. Baseline 비교

| 항목 | EXP-005(yolo26n) | EXP-007(yolo26s) | 변화 |
| --- | --- | --- | --- |
| 변경 변수 | - | 모델 크기 확대(yolo26n→yolo26s) | - |
| 학습 시간 | 02:10:53(50 epoch, 미발동) | 10:01:26(39 epoch, Early Stop 발동) | 약 4.6배 |
| 전체 mAP50-95 | 0.131 | 0.089 | **-0.042** |
| localization_error 건수 | 11 | 5 | **-6(개선)** |
| slag_inclusion Recall | 0.487 | 0.179 | **-0.308** |
| porosity Recall | 0.405 | 0.321 | -0.084 |

## 성공 기준 대비 판정 (`docs/decisions/14_next_experiment_plan.md` 기준)

| 기준 | 목표 | 실제 결과 | 충족 여부 |
| --- | --- | --- | --- |
| 주 지표: 전체 mAP50-95 | EXP-005(0.131) 대비 개선 | 0.089 | **미충족(오히려 하락)** |
| 보조 지표: localization_error 건수 | EXP-005(11건) 대비 감소 | 5건 | **충족**(정성 평가로도 실질 개선 확인) |
| 가드레일 1: slag_inclusion Recall | 0.40 이상 | 0.179 | **미충족(EXP-004 회귀 수준)** |
| 가드레일 2: porosity Recall | 0.30 이상 | 0.321 | 충족(근소) |

# 16. 결론

**모델 크기 확대는 목표를 기준으로는 실패다.** 주 지표(mAP50-95)와 slag_inclusion 가드레일이 미충족됐고, 특히 slag_inclusion Recall이 EXP-004 회귀 수준으로 되돌아간 것은 EXP-005의 성과를 사실상 무효화하는 수준이다.

다만 이번 실험은 완전한 무효 실험은 아니다 — **애초에 겨냥했던 "박스 위치 정밀도" 자체는 정량(localization_error 11→5건)·정성(대표 사례가 TP로 전환) 양쪽에서 실질적으로 개선됐다.** 문제는 그 대가로 모델이 애매한 신호에 더 보수적으로 반응하게 되면서 전체 Recall이 크게 희생된 것이다 — 이는 "모델 용량 부족" 가설이 부분적으로는 맞았지만, 동시에 "이 데이터셋 규모(Train 482장)에서 더 큰 모델은 과적합 위험이 recall 이득보다 크다"는 트레이드오프를 함께 보여준다.

**dataset_v3 + yolo26n(EXP-005)을 최종 Baseline으로 유지한다.** yolo26s는 채택하지 않는다.

# 17. 다음 실험 계획

`docs/decisions/13_next_experiment_plan.md`·`14_next_experiment_plan.md`에서 제시했던 박스 위치 정밀도 후보(box loss gain 확대·CLAHE·모델 크기 확대)를 모두 시도했고, 각각 실패하거나(EXP-003, EXP-006) 부분적 개선과 전체 성능 하락이 공존하는 트레이드오프(EXP-007)로 끝났다. `docs/context/00-completion-criteria.md`·`02-task-list.md` 기준으로 반복 실험 사이클(작업25)은 이번 실험을 마지막으로 마무리하고, **작업26(PoC 결과 문서화)으로 진입한다.** 박스 위치 정밀도 문제는 "데이터 균형·전처리·모델 크기 중 어느 하나만으로는 해결되지 않았고, 더 큰 모델은 과적합 트레이드오프를 동반한다"는 것을 최종 문서에 정직하게 기록한다.
