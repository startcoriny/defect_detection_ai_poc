# 1. 실험 기본 정보

- 실험 ID: EXP-P1-DET-004
- 실험명: RT_AL_YOLO26N_960_DatasetV2
- 실험 상태: COMPLETED
- 작성자: 자동 기록
- 실험 시작 일시: 2026-07-27T15:01:24+09:00
- 실험 종료 일시: 2026-07-27T16:53:05+09:00
- 관련 단계: 작업17
- 실험 유형: DETECTION_TRAINING
- Git Branch: feature/exp004-data-expansion
- Git Commit: b7be176bb0513c3fb16d5261b24ede9266001950
- 설정 파일 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-004\train_config.yaml
- 결과 폴더 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-004\runs\train

# 2. 목적과 가설

- 실험 목적: AI-Hub RT·AL 데이터에서 Polygon을 Bounding Box로 변환한
  YOLO Detection 파이프라인이 정상적으로 학습되는지 검증한다.
- 검증할 핵심 질문: 새로운 Test 이미지에서 porosity와 slag_inclusion의
  위치를 예측할 수 있는 Baseline 성능을 얻을 수 있는가?
- 현재 문제: 전체 데이터셋으로 측정한 최초의 실제 성능 기준이 없다.
- 가설: 변환·검증된 dataset_v2로 두 결함 클래스를 학습하면 재현 가능한 최초 Baseline 지표를 얻을 수 있다.
- 예상 결과: 학습이 정상 종료되고 best/last 모델 및 Precision·Recall·mAP 지표가 생성된다.
- 성공 판단 기준: 예외 없이 정상 종료되고 필수 모델·로그·설정·시각화 산출물이 모두 보존된다.

# 3. 기준 실험

없음. 최초 Baseline.

# 5. 데이터셋 정보

## 5.1 데이터셋 식별

- 데이터셋 이름: ai_hub_welding_rt_al
- 데이터셋 버전: dataset_v2
- 데이터 출처: AI-Hub
- 검사 유형: RT
- 소재: AL
- 원본 라벨 형식: AI-Hub JSON Polygon
- 학습 라벨 형식: YOLO Detection
- 클래스 매핑: `metadata/yolo_classes.txt`
- 데이터 선정 목록: `metadata/v2/selected_dataset.csv`
- 데이터 검증 보고서: `reports/dataset/v2/`

**[정정]** 이 절은 학습 스크립트가 `reports/dataset/split_distribution.csv`(dataset_v1 경로)를 잘못 참조해 자동 생성 당시 dataset_v1의 수치가 기록됐었다. `train_baseline.py`(exp4)의 경로를 `reports/dataset/v2/split_distribution.csv`로 고치고, 아래 표는 실제 dataset_v2 산출물(`reports/dataset/v2/split_distribution.csv`)로 재작성했다. 실제 학습에 사용된 데이터(`data/processed/dataset_v2`)와 모델 성능(9~14절)에는 영향이 없다 — 학습 자체는 처음부터 dataset_v2로 정상 진행됐고, 이 버그는 문서화용 요약 파일에만 있었다.

## 5.2 데이터 수

| 구분 | 이미지 수 | 객체 수 |
| --- | ---: | ---: |
| Train | 398 | 548 |
| Validation | 85 | 141 |
| Test | 84 | 123 |
| 전체 | 567 | 812 |

## 5.3 클래스별 객체 분포

| 클래스 | 클래스 ID | Train 객체 | Val 객체 | Test 객체 | 전체 객체 |
| --- | ---: | ---: | ---: | ---: | ---: |
| porosity | 3 | 380 | 111 | 84 | 575 |
| slag_inclusion | 4 | 168 | 30 | 39 | 237 |

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
- 학습 입력: `data/processed/dataset_v2/data.yaml`

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

- 학습 시작 일시: 2026-07-27T15:01:24+09:00
- 학습 종료 일시: 2026-07-27T16:53:05+09:00
- 총 실행 시간: 01:51:42
- 정상 종료 여부: 예
- Early Stopping 여부: 아니오
- 종료 Epoch: 51
- Best Epoch: 42
- Best 모델 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-004\models\best.pt
- Last 모델 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-004\models\last.pt
- 결과 폴더: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-004\runs\train

## 9.1 학습 결과 요약

| 지표 | Best 결과 | Last 결과 |
| --- | ---: | ---: |
| Train Loss (Box+Class+L1) | 4.654500 | 4.102920 |
| Validation Loss (Box+Class+L1) | 5.277850 | 4.738030 |
| Precision | 0.533850 | 0.389890 |
| Recall | 0.415770 | 0.490090 |
| mAP50 | 0.440550 | 0.366380 |
| mAP50-95 | 0.170780 | 0.145500 |

Best epoch loss:

- Box Loss: 1.853580
- Class Loss: 2.794550
- L1 Loss: 0.006370

## 9.2 학습 과정 해석

Early Stopping 미발동(50 epoch 전부 완주, EXP-002와 동일). 총 학습 시간은 1.859시간(약 111분)으로 EXP-002(58분 44초)의 약 1.9배 — Train 이미지가 209장→398장으로 약 1.9배 늘어난 것과 거의 정비례한다. box=15.0을 시도했던 EXP-003과 달리 이번엔 외부 정지 없이 처음부터 끝까지 안정적인 속도(epoch당 약 2분 내외)로 진행됐다.

fitness(=mAP50-95) 기준 Best는 epoch 41(0-index, 표시 기준 42)로, 이후 epoch 46~50 구간의 mAP50-95(0.145~0.152)가 Best(0.171)보다 오히려 낮다 — Recall은 후반부에 더 높아지는 반면(0.46~0.50) Precision은 낮아지는(0.39~0.44) 상충 관계가 나타난다. EXP-002에서도 비슷하게 중반 epoch(38)에서 정점을 찍고 후반부는 정체·소폭 하락하는 패턴이 있었다 — 데이터가 늘어도 이 패턴 자체는 반복된다.

Train/Val Loss는 끝까지 나란히 움직여 뚜렷한 과적합 징후는 보이지 않는다.

# 10. 추론 설정

Confidence 0.25, NMS IoU 0.70, imgsz 960(학습과 동일), 매칭(TP 판정) IoU 0.5 — EXP-001~003과 동일한 기준으로 비교 가능하게 유지했다. Test 84장 전체 추론.

**주의**: dataset_v2는 dataset_v1과 별개로 새로 선별·분할한 데이터셋이라, EXP-004의 Test 84장은 EXP-002의 Test 46장과 겹치지 않는 별개의 이미지 집합이다. 즉 아래 비교는 "완전히 동일한 이미지에 대한 재평가"가 아니라 "같은 방법론으로 각자의 held-out Test셋에서 측정한 결과 간 비교"다 — 데이터 확장이라는 변수의 실제 효과(일반화 성능)를 보는 데는 유효하지만, 개별 이미지 단위로 EXP-002와 1:1 대조는 할 수 없다.

# 11. 전체·클래스별 성능

## 11.1 전체 성능

| 지표 | EXP-002(dataset_v1) | EXP-004(dataset_v2) |
| --- | ---: | ---: |
| Precision | 0.678 | 0.798 |
| Recall | 0.238 | 0.239 |
| mAP50 | 0.201 | 0.210 |
| mAP50-95 | 0.075 | 0.082 |

Precision·mAP50·mAP50-95는 개선됐지만, 전체 Recall은 0.238→0.239로 사실상 변화가 없다. 다만 이는 클래스별로 상반된 변화가 상쇄된 결과다(11.2절 참조) — 전체 Recall만 보면 "데이터를 늘려도 효과가 없다"고 오독하기 쉽지만, 실제로는 porosity가 크게 개선되고 slag_inclusion이 악화되며 서로를 상쇄했다.

## 11.2 클래스별 성능

| 클래스 | EXP-002 Precision | EXP-004 Precision | EXP-002 Recall | EXP-004 Recall | EXP-002 AP50-95 | EXP-004 AP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| porosity | 0.800 | 0.595 | 0.143 | **0.298** | 0.078 | 0.102 |
| slag_inclusion | 0.556 | 1.000 | 0.333 | **0.179** | 0.072 | 0.062 |

**porosity Recall이 0.143→0.298로 2배 이상 개선됐다** — 이번 실험의 주 목표(가장 데이터가 부족했던 클래스 개선)가 뚜렷하게 달성됐다. 반면 **slag_inclusion Recall은 0.333→0.179로 오히려 절반 가까이 떨어졌다**(Precision은 1.0으로 개선됐지만, 이는 예측을 더 보수적으로 하게 됐다는 뜻이기도 하다). dataset_v2에서 slag_inclusion 객체 수 자체는 늘었지만(147→237) porosity(185→575)만큼 압도적으로 늘지는 않아, 두 클래스의 학습 데이터 비율이 EXP-002 대비 porosity 쪽으로 더 치우치면서(약 1.26:1 → 약 2.43:1) 모델이 상대적으로 porosity에 더 강하게 적응했을 가능성이 있다.

## 11.3 객체 크기별 성능

| 크기 | EXP-002 Recall(GT수) | EXP-004 Recall(GT수) |
| --- | ---: | ---: |
| Small | 0.121(33) | **0.241(87)** |
| Medium | 0.375(24) | 0.303(33) |
| Large | 0.000(1) | 0.000(3) |

**Small 객체 Recall이 0.121→0.241로 2배 개선됐다** — 세 실험(imgsz 확대, box gain 조정) 모두 풀지 못했던 문제가 데이터 확장으로 처음 뚜렷하게 개선됐다. 다만 Medium Recall은 0.375→0.303으로 다소 낮아졌다(11.2절의 slag_inclusion 악화와 연결 — Medium 객체는 slag_inclusion 비중이 높다). GT 표본 수 자체도 늘어(Small 33→87, Medium 24→33) 통계적으로 더 안정적인 추정치가 됐다.

# 12. Threshold 비교

| Threshold | EXP-002 Recall(평가기준) | EXP-004 Recall(평가기준) |
| --- | ---: | ---: |
| 0.10 | 0.414 | 0.463 |
| 0.25 | 0.241 | 0.276 |
| 0.50 | 0.052 | 0.065 |
| 0.75 | 0.017 | 0.016 |

0.10~0.50 구간에서 EXP-004의 Recall이 EXP-002보다 높다(0.75에서는 표본이 극소수라 오차 범위). 오토라벨링 후보 Threshold는 기존과 동일하게 0.25를 유지한다(이번 실험 목적이 Threshold 재선정이 아니었음).

# 13. 정성 평가

위치 오류(localization_error) 사례가 이번엔 7건 발생했다(EXP-002는 2건, EXP-001부터 반복된 "예측 박스가 GT보다 작게 나온다"는 패턴 — 예: `RT_AL_02_14487812_001`, Confidence 0.395, GT 박스 안쪽에 축소된 예측 박스). **데이터를 늘려도 박스 위치 정밀도 문제 자체는 해소되지 않았다** — 이 실험의 변수(데이터 양)가 애초에 겨냥한 문제가 아니었으므로 예상된 결과다.

오탐(false_positive) 9건은 전부 porosity로, 이 중 4건은 `duplicate_of_tp=True`(이미 인정된 TP 예측과 겹치는 근접 중복 박스)이고 나머지 5건은 독립적인 오탐이다. 대표 사례(`RT_AL_05_14491963_001`, Confidence 0.481)를 직접 확인한 결과 예측 위치에 실제로 미세한 어두운 얼룩이 있었다 — 라벨링에서 누락된 경계선 케이스일 가능성과, 정상 텍스처를 결함으로 오인했을 가능성을 둘 다 배제할 수 없다.

# 14. 원인 분석

## 14.1 오류 유형 집계

| 오류 유형 | EXP-002 | EXP-004 |
| --- | ---: | ---: |
| 미탐(false_negative) | 42 | 84 |
| 오탐(false_positive) | 4 | 9 |
| 위치 오류(localization_error) | 2 | 7 |
| 클래스 오류(wrong_class) | 1 | 1 |

절대 건수는 대부분 늘었지만, Test 이미지·객체 수 자체가 크게 늘었다는 점(46장/58개체 → 84장/123개체, 약 1.8~2.1배)을 감안해야 한다. 미탐 42→84건(2.0배)은 Test 규모 증가와 거의 비례하고, 오탐 4→9건(2.25배)·위치 오류 2→7건(3.5배)은 그보다 더 늘어 실질적인 악화로 보이지만, 절대 건수 자체가 워낙 작아(원래 2~4건 수준) 비율 해석에 주의가 필요하다.

## 14.2 원인 판단

- **데이터 확장은 가설대로 작동했다.** porosity Recall(주 목표)과 Small 객체 Recall(부가 목표)이 모두 뚜렷하게 개선됐고, 이는 "데이터 절대량 부족"이 저대비·작은 결함 미탐의 실질적 원인 중 하나였음을 보여준다.
- **다만 클래스 간 데이터 비율 변화가 부작용을 낳았다.** porosity 객체가 slag_inclusion보다 훨씬 많이 늘면서(약 2.4배 vs 1.2배) 클래스 간 학습 데이터 비율이 벌어졌고, slag_inclusion Recall이 눈에 띄게 떨어졌다. "데이터를 늘리면 무조건 좋아진다"가 아니라 "어떤 클래스가 얼마나 늘었는가"가 중요하다는 것을 보여준다.
- **박스 위치 정밀도 문제(위치 오류, mAP50 대비 mAP50-95 격차)는 데이터 양과 무관하게 남아있다.** 이는 EXP-003에서 이미 시도했던 손실 가중치 조정으로도 풀리지 않았던 문제와 같은 축이며, 별도 개선 축(box 회귀 방식 자체, 또는 Polygon 정보를 더 활용하는 방향)이 필요함을 재확인한다.

# 15. Baseline 비교

| 항목 | EXP-002(dataset_v1) | EXP-004(dataset_v2) | 변화 |
| --- | --- | --- | --- |
| 변경 변수 | - | 데이터 확장(299장→567장) | - |
| 학습 시간 | 00:58:44(50 epoch, 미발동) | 01:51:34(50 epoch, 미발동) | +약 53분(데이터 약 1.9배에 비례) |
| 전체 Recall | 0.238 | 0.239 | +0.001(사실상 동일) |
| 전체 mAP50-95 | 0.075 | 0.082 | +0.007 |
| **porosity Recall(주 지표)** | **0.143** | **0.298** | **+0.155** |
| slag_inclusion Recall | 0.333 | 0.179 | -0.154 |
| Small Recall | 0.121 | 0.241 | +0.120 |

## 성공 기준 대비 판정 (`docs/decisions/11_next_experiment_plan.md` 기준)

| 기준 | 목표 | 실제 결과 | 충족 여부 |
| --- | --- | --- | --- |
| 주 지표: porosity Recall | EXP-002(0.143) 대비 0.25 이상 | 0.298 | **충족** |
| 가드레일 1: 전체 mAP50-95 | EXP-002(0.075) 이상 유지 | 0.082 | 충족 |
| 가드레일 2: Small Recall | EXP-002(0.121) 이상 유지 | 0.241 | 충족 |

# 16. 결론

**데이터 확장(dataset_v2)은 성공이다 — EXP-001~003 세 번의 시도 중 처음으로 사전 등록한 모든 성공 기준(주 지표·가드레일 2개)을 충족했다.** 주 목표였던 porosity Recall이 2배 이상(0.143→0.298) 개선됐고, 부가적으로 Small 객체 Recall도 2배(0.121→0.241) 개선됐다. 이는 "저대비·작은 결함 미탐"의 근본 원인 중 하나가 실제로 데이터 절대량 부족이었음을 뒷받침한다.

다만 무비판적으로 채택하기 전에 짚어야 할 점이 있다: (1) slag_inclusion Recall이 0.333→0.179로 눈에 띄게 떨어졌다 — porosity 객체 수는 약 2.4배(241→575) 늘어난 반면 slag_inclusion은 약 1.2배(198→237)만 늘어, 클래스별 데이터 증가 비율이 불균등했기 때문으로 추정된다. (2) 박스 위치 정밀도 문제(위치 오류 7건, mAP50-95가 mAP50보다 훨씬 낮음)는 전혀 개선되지 않았다 — 데이터 양과는 별개의 축이다. (3) EXP-002와 EXP-004의 Test셋은 서로 다른 이미지 집합이라 완전한 통제 비교는 아니다.

**dataset_v2를 이후 실험의 기본 데이터셋으로 채택한다.** 다음 실험은 (a) slag_inclusion 회귀를 보완하는 방향(클래스별 데이터 비율 재조정, 또는 RT/ST의 slag_inclusion 106건 활용 재검토) 또는 (b) 여전히 미해결인 박스 위치 정밀도 문제(대비 강조 증강, 모델 크기 확대 등)를 우선순위로 검토할 것을 권장한다.

# 17. 다음 실험 계획

**차기 실험 제안**: dataset_v2·imgsz=960·box=7.5를 기준으로 유지한다. slag_inclusion Recall 회귀를 되돌리는 방향(클래스 균형 재검토)과, `docs/decisions/11_next_experiment_plan.md`의 후속 우선순위 2번(CLAHE 대비 강조 증강)·3번(모델 크기 확대) 중 하나를 다음 변수로 검토한다. 상세 계획은 필요 시 별도 문서로 작성한다.
