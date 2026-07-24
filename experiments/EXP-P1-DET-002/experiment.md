# 1. 실험 기본 정보

- 실험 ID: EXP-P1-DET-002
- 실험명: RT_AL_YOLO26N_960_ImgszUp
- 실험 상태: COMPLETED
- 작성자: 자동 기록
- 실험 시작 일시: 2026-07-24T16:36:43+09:00
- 실험 종료 일시: 2026-07-24T17:35:27+09:00
- 관련 단계: 작업17
- 실험 유형: DETECTION_TRAINING
- Git Branch: feature/exp002-imgsz960
- Git Commit: cc378040196144ca9d4f787fdc1def0c55a26201
- 설정 파일 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-002\train_config.yaml
- 결과 폴더 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-002\runs\train

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

- 학습 시작 일시: 2026-07-24T16:36:43+09:00
- 학습 종료 일시: 2026-07-24T17:35:27+09:00
- 총 실행 시간: 00:58:44
- 정상 종료 여부: 예
- Early Stopping 여부: 아니오
- 종료 Epoch: 51
- Best Epoch: 39
- Best 모델 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-002\models\best.pt
- Last 모델 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-002\models\last.pt
- 결과 폴더: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-002\runs\train

## 9.1 학습 결과 요약

| 지표 | Best 결과 | Last 결과 |
| --- | ---: | ---: |
| Train Loss (Box+Class+L1) | 5.681490 | 5.655440 |
| Validation Loss (Box+Class+L1) | 6.917190 | 6.524970 |
| Precision | 0.409540 | 0.291970 |
| Recall | 0.286700 | 0.291670 |
| mAP50 | 0.264760 | 0.229230 |
| mAP50-95 | 0.109140 | 0.097430 |

Best epoch loss:

- Box Loss: 1.742210
- Class Loss: 3.932450
- L1 Loss: 0.006830

## 9.2 학습 과정 해석

### 학습 결과 요약

모델이 정상적으로 학습됐다. `train/cls_loss`가 15.40(epoch 1) → 4.1~4.8대(epoch 40 이후)로 약 70% 감소했고, `train/box_loss`(2.75→1.5~1.7대), `train/l1_loss`(0.0117→0.006대)도 유사하게 감소했다. EXP-001과 달리 **Early Stopping이 발동하지 않고 50 epoch를 전부 소진**했다(총 58분 44초 소요 — 성공 기준의 가드레일인 63분 이내).

### Best Epoch

Ultralytics fitness 기준 최고점은 39번째 epoch(precision 0.410 / recall 0.287 / mAP50 0.265 / mAP50-95 0.109)이며 `best.pt`로 저장됐다. EXP-001의 Best(27번째 epoch)보다 훨씬 늦게 나타났다 — Early Stopping이 발동하지 않은 것과 일관된다(patience=15 기준으로 39번째 이후에도 15 epoch를 채우지 못한 채(50번째까지 11 epoch만 남음) 학습이 끝났다).

### 학습 그래프 해석 (`results.png`)

- **Train/Validation Loss 변화**: `cls_loss`는 EXP-001과 마찬가지로 Train/Val이 끝까지 나란히 움직인다. 다만 `box_loss`와 `l1_loss`는 epoch 35 전후부터 **Val이 Train보다 다시 살짝 올라가는 경향**이 보인다(EXP-001에서는 없었던 패턴) — 약한 과적합 신호일 수 있으나, 폭이 크지 않고 `cls_loss`에는 나타나지 않아 확정적이지는 않다.
- **Precision/Recall/mAP50/mAP50-95 변화**: EXP-001보다 노이즈가 적고 추세가 뚜렷하다. Recall이 epoch 25 전후부터 0.25~0.35 구간으로 비교적 꾸준히 상승하는 모습을 보이며, mAP50-95도 같은 구간에서 0.09~0.11대로 완만히 상승한다.
- **Early Stopping 여부**: 발동하지 않음(50 epoch 전부 완주) — EXP-001(41 epoch에서 조기 종료)과의 뚜렷한 차이. 더 큰 입력 해상도가 학습을 더 오래 지속적으로 개선시킨 것으로 보인다.
- **과적합 가능성**: 낮음~보통. `cls_loss`는 과적합 신호 없음, `box_loss`/`l1_loss`의 후반부 Val 상승은 경미한 수준.
- **Confusion Matrix(`confusion_matrix.png`) 참고 시 주의**: 이 그래프는 학습 내부 검증(Val 44장, 낮은 Confidence까지 전부 포함하는 mAP 계산용 스윕)에서 나온 것이라 절대 건수(예: background 1260/1297)가 실제 배포 조건과 다르다 — EXP-001의 작업18/23 사례와 동일한 주의사항이 적용된다. 실제 배포 조건(conf=0.25) 기준 비교는 이후 Test 평가(작업23에 해당하는 단계)에서 별도로 확인한다.

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
