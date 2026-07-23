# 1. 실험 기본 정보

- 실험 ID: EXP-P1-DET-001
- 실험명: RT_AL_YOLO26N_640_Baseline
- 실험 상태: COMPLETED
- 작성자: 자동 기록
- 실험 시작 일시: 2026-07-23T15:58:58+09:00
- 실험 종료 일시: 2026-07-23T16:19:34+09:00
- 관련 단계: 작업17
- 실험 유형: DETECTION_TRAINING
- Git Branch: feature/baseline-training
- Git Commit: 8bddc53610750acfbd8d4c4b8173fbfa4b36d8a7
- 설정 파일 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-001\train_config.yaml
- 결과 폴더 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-001\runs\train

# 2. 목적과 가설

- 실험 목적: AI-Hub RT·AL 데이터에서 Polygon을 Bounding Box로 변환한
  YOLO Detection 파이프라인이 정상적으로 학습되는지 검증한다.
- 검증할 핵심 질문: 새로운 Test 이미지에서 porosity와 slag_inclusion의
  위치를 예측할 수 있는 Baseline 성능을 얻을 수 있는가?
- 현재 문제: 전체 데이터셋으로 측정한 최초의 실제 성능 기준이 없다.
- 가설: 변환·검증된 dataset_v1로 두 결함 클래스를 학습하면 재현 가능한 최초 Baseline 지표를 얻을 수 있다.
- 예상 결과: 학습이 정상 종료되고 best/last 모델 및 Precision·Recall·mAP 지표가 생성된다.
- 성공 판단 기준: 예외 없이 정상 종료되고 필수 모델·로그·설정·시각화 산출물이 모두 보존된다.

# 3. 기준 실험

없음. 최초 Baseline.

# 5. 데이터셋 정보

## 5.1 데이터셋 식별

- 데이터셋 이름: ai_hub_welding_rt_al
- 데이터셋 버전: dataset_v1
- 데이터 출처: AI-Hub
- 검사 유형: RT
- 소재: AL
- 원본 라벨 형식: AI-Hub JSON Polygon
- 학습 라벨 형식: YOLO Detection
- 클래스 매핑: `metadata/yolo_classes.txt`
- 데이터 선정 목록: `metadata/selected_dataset.csv`
- 데이터 검증 보고서: `reports/dataset/`

## 5.2 데이터 수

| 구분 | 이미지 수 | 객체 수 |
| --- | ---: | ---: |
| Train | 209 | 332 |
| Validation | 44 | 49 |
| Test | 46 | 58 |
| 전체 | 299 | 439 |

## 5.3 클래스별 객체 분포

| 클래스 | 클래스 ID | Train 객체 | Val 객체 | Test 객체 | 전체 객체 |
| --- | ---: | ---: | ---: | ---: | ---: |
| porosity | 3 | 185 | 28 | 28 | 241 |
| slag_inclusion | 4 | 147 | 21 | 30 | 198 |

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
- 학습 입력: `data/processed/dataset_v1/data.yaml`

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
| Image Size | 640 |
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

- 학습 시작 일시: 2026-07-23T15:58:58+09:00
- 학습 종료 일시: 2026-07-23T16:19:34+09:00
- 총 실행 시간: 00:20:38
- 정상 종료 여부: 예
- Early Stopping 여부: 예
- 종료 Epoch: 42
- Best Epoch: 27
- Best 모델 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-001\models\best.pt
- Last 모델 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-001\models\last.pt
- 결과 폴더: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-001\runs\train

## 9.1 학습 결과 요약

| 지표 | Best 결과 | Last 결과 |
| --- | ---: | ---: |
| Train Loss (Box+Class+L1) | 5.802590 | 5.223770 |
| Validation Loss (Box+Class+L1) | 6.186380 | 5.737610 |
| Precision | 0.294440 | 0.406030 |
| Recall | 0.316800 | 0.184750 |
| mAP50 | 0.273210 | 0.226970 |
| mAP50-95 | 0.115960 | 0.091680 |

Best epoch loss:

- Box Loss: 2.136330
- Class Loss: 3.658330
- L1 Loss: 0.007930

## 9.2 학습 과정 해석 (작업18)

### Baseline 학습 결과 요약

모델이 실제로 학습됐다. `train/cls_loss`가 9.87(epoch 1) → 2.8~3.4대(epoch 30대 이후)로 약 70% 감소했고, `train/box_loss`(2.98→1.8대)와 `train/l1_loss`(0.014→0.007대)도 각각 절반 수준으로 줄었다. `mAP50`은 0(epoch 1~2, 무작위 수준) → epoch 20 전후로 0.2~0.3대에 도달한 뒤 그 구간에서 등락하며 정체됐다.

### Best Epoch

`results.csv`에서 Ultralytics fitness(`0.1*mAP50 + 0.9*mAP50-95`) 기준 최고점은 27번째 epoch(precision 0.294 / recall 0.317 / mAP50 0.273 / mAP50-95 0.116)이며, 이 값이 `best.pt`로 저장됐다. 다만 21번째(fitness 0.1298)·23번째(0.1300)·25번째(0.1290) epoch도 27번째(0.1317)와 근소한 차이라, "최고점"이라기보다 노이즈가 큰 정체 구간의 최상단에 가깝다(아래 이상 징후 참고).

### 학습 그래프 해석

- **Train/Validation Loss 변화**: `train`과 `val`의 `box_loss`·`cls_loss`·`l1_loss`가 처음부터 끝까지 거의 나란히 움직인다(`results.png` 1행·2행 비교). Train Loss만 계속 떨어지고 Val Loss는 정체·상승하는 전형적 과적합 패턴은 보이지 않는다.
- **Precision/Recall/mAP50/mAP50-95 변화**: epoch 1~2는 예측이 전혀 없어 전부 0이다. epoch 3부터 값이 나타나기 시작해 epoch 18~20 전후로 mAP50 0.2대에 도달한 뒤, 이후 20개 epoch(21~41) 동안 뚜렷한 추가 개선 없이 0.2~0.3 구간에서 등락한다. Precision·Recall은 인접 epoch 간에도 0.1~0.2p 이상 튀는 등 변동폭이 크다(예: epoch 4 recall 0.232 → epoch 5 recall 0.464 → epoch 7 recall 0.071).
- **Early Stopping 여부**: 발동했다. patience=15 기준으로 27번째 epoch 이후 15개 epoch(28~41... 정확히는 42번째 epoch 직전) 동안 fitness 개선이 없어 41 epoch(0-index 기준 로그상 "epoch 26")에서 자동 종료됐다. 의도한 대로 동작.
- **과적합 가능성**: 낮다. Train/Val Loss가 함께 움직이는 것이 근거다. 다만 후반부(특히 마지막 epoch 41)에서 Precision이 오르고(0.406) Recall이 크게 떨어지는(0.185) 현상이 있는데, 이 epoch은 Ultralytics가 마지막 구간에 Mosaic Augmentation을 끄는 시점(`Closing dataloader mosaic` 로그, epoch 41 직전)과 겹친다. Loss가 아니라 증강 설정 전환에 따른 단발성 변동일 가능성이 높아 보이며, 여러 epoch에 걸친 지속적 추세는 아니다.
- **클래스별 성능 차이**: `best.pt` 최종 검증 기준 porosity(15장/28개 객체) Precision 0.295·Recall 0.299·mAP50 0.250, slag_inclusion(14장/21개 객체) Precision 0.296·Recall 0.333·mAP50 0.299로, slag_inclusion이 조금 더 높다. `confusion_matrix.png` 확인 결과 정답 매칭(대각선)은 porosity 14건·slag_inclusion 15건이고, 클래스 간 상호 오분류는 slag_inclusion을 porosity로 예측한 경우 8건, 반대(porosity를 slag_inclusion으로) 3건으로 비대칭적이다. 작업12에서 확인한 대로 porosity가 작은 객체(Small) 위주라는 점이 mAP50이 더 낮게 나오는 방향과 일치한다.

### 이상 징후 목록

1. **배경 오탐(FP)이 클래스 간 혼동보다 압도적으로 많다.** `confusion_matrix.png`에서 "예측=porosity, 실제=background"가 1833건, "예측=slag_inclusion, 실제=background"가 926건으로, 정답 매칭(14건·15건)이나 클래스 간 혼동(8건·3건)과 비교가 안 될 정도로 크다. Confusion Matrix는 최종 리포트의 Precision/Recall과 계산 방식(임계값 처리)이 달라 이 절대 건수를 그대로 "실제 배포 시 오탐률"로 해석할 수는 없지만, 정성적으로는 "두 결함을 헷갈리는 것"보다 "배경을 결함으로 잘못 짚는 것"이 훨씬 더 큰 오차 원인임을 보여준다. 작업24(오탐·미탐 분석)에서 실제 오탐 이미지를 눈으로 확인해볼 필요가 있다.
2. **검증 지표의 epoch 간 변동폭이 매우 크다.** Validation이 44장·49개 객체뿐이라, 소수 이미지의 예측 결과가 바뀌는 것만으로 mAP50·Recall이 크게 흔들린다(예: epoch 39 recall 0.299 → epoch 40 recall 0.381 → epoch 41 recall 0.185). "Best epoch"이 통계적으로 유의미하게 더 나은 모델이라기보다, 노이즈가 큰 정체 구간에서 우연히 더 높게 나온 지점일 가능성을 감안해야 한다.
3. **cls_loss는 종료 시점에도 완만한 하락 추세가 남아있는 반면, box_loss·l1_loss는 epoch 15~20 근방에서 이미 정체됐다.** 즉 현재 병목은 위치 추정보다 분류 쪽일 가능성이 있다 — 작업25(다음 실험 후보 선정)에서 patience를 늘려 cls_loss 수렴 여지를 더 주는 방안도 고려할 만하다.

# 10. 추론 설정

실험 후 작성(작업18~25에서 채움)

# 11. 전체·클래스별 성능

실험 후 작성(작업18~25에서 채움)

# 12. Threshold 비교

실험 후 작성(작업18~25에서 채움)

# 13. 정성 평가

실험 후 작성(작업18~25에서 채움)

# 14. 원인 분석

실험 후 작성(작업18~25에서 채움)

# 15. Baseline 비교

실험 후 작성(작업18~25에서 채움)

# 16. 결론

실험 후 작성(작업18~25에서 채움)

# 17. 다음 실험 계획

실험 후 작성(작업18~25에서 채움)
