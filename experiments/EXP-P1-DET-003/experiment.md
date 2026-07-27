# 1. 실험 기본 정보

- 실험 ID: EXP-P1-DET-003
- 실험명: RT_AL_YOLO26N_960_BoxGain15
- 실험 상태: COMPLETED
- 작성자: 자동 기록
- 실험 시작 일시: 2026-07-24T18:32:27+09:00
- 실험 종료 일시: 2026-07-24T22:33:16+09:00
- 관련 단계: 작업17
- 실험 유형: DETECTION_TRAINING
- Git Branch: feature/exp003-boxgain
- Git Commit: 2ea2381e17c791e18862021df226953519f610e9
- 설정 파일 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-003\train_config.yaml
- 결과 폴더 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-003\runs\train

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

- 학습 시작 일시: 2026-07-24T18:32:27+09:00
- 학습 종료 일시: 2026-07-24T22:33:16+09:00
- 총 실행 시간: 04:00:49
- 정상 종료 여부: 예
- Early Stopping 여부: **예**(스크립트 자동 판정은 "아니오"로 잘못 기록됨 — 아래 "9.0 발견한 버그" 참조)
- 종료 Epoch: 49(Ultralytics 로그: `49 epochs completed`, `EarlyStopping: ... Best results observed at epoch 34`)
- Best Epoch: **35**(스크립트 자동 판정은 "31"로 잘못 기록됨 — 아래 참조. 1-index 기준, Ultralytics 로그의 0-index "epoch 34"와 일치)
- Best 모델 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-003\models\best.pt
- Last 모델 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-003\models\last.pt
- 결과 폴더: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-003\runs\train

## 9.0 발견한 버그: `read_results()`의 fitness 공식이 처음부터 틀렸음

`train_baseline.py`(exp1/exp2/exp3 전부 동일)의 `read_results()`는 Best 행을 `0.1*mAP50 + 0.9*mAP50-95`로 계산해왔다. 이번에 Ultralytics 실제 소스(`venv/Lib/site-packages/ultralytics/utils/metrics.py:1004`, `Metric.fitness()`)를 직접 확인한 결과, 실제 공식은 다음과 같다.

```python
w = [0.0, 0.0, 0.0, 1.0]  # weights for [P, R, mAP@0.5, mAP@0.5:0.95]
fitness = mAP50-95  # 즉, mAP50-95 단독
```

`0.1*mAP50+0.9*mAP50-95`이라는 공식은 이 프로젝트 초기(작업17)에 검증 없이 가정한 값이었고, 지금까지(EXP-001·EXP-002) 발견되지 않다가 이번에 두 공식의 결과가 갈리는 지점(CSV epoch 30 vs 34)이 생기며 드러났다.

**실질적 영향은 없다** — `best.pt` 자체는 Ultralytics가 학습 중 자기 자신의 (올바른) fitness 기준으로 저장하므로, 지금까지의 모든 추론·평가·비교(작업19~25에 해당하는 모든 단계)는 전부 올바른 best 모델을 사용했다. 영향받는 건 오직 `experiment.md`의 "Best 결과" 표 값(우리가 CSV에서 다시 골라내 보여주는 참고용 수치)뿐이다. EXP-003은 위와 같이 정정했다. EXP-001·EXP-002는 재학습 없이도 이미 저장된 `results.csv`로 재확인 가능하지만, 두 실험 모두 원래 공식으로 고른 행과 진짜 best 행의 지표 차이가 미미해 결론에는 영향이 없음을 확인했다(재검토 결과는 15절 참조). 스크립트 코드 자체는 exp1/exp2/exp3 전부 이미 실행이 끝난 상태라 수정하지 않는다(같은 이유로 exp1은 "원본과 100% 동일"이라는 기존 약속을 지킨다).

## 9.1 학습 결과 요약 (정정됨 — 위 버그 반영)

| 지표 | Best 결과(정정) | Last 결과 |
| --- | ---: | ---: |
| Train Loss (Box+Class+L1) | 7.690680 | 7.953700 |
| Validation Loss (Box+Class+L1) | 9.016020 | 8.339090 |
| Precision | 0.308240 | 0.368750 |
| Recall | 0.321430 | 0.375000 |
| mAP50 | 0.246140 | 0.242630 |
| mAP50-95 | 0.103360 | 0.081210 |

Best epoch loss:

- Box Loss: 3.617570
- Class Loss: 4.070490
- L1 Loss: 0.007320

## 9.2 학습 과정 해석

### 학습 시간 이상치

`results.csv`의 epoch별 누적 시간을 직접 뜯어본 결과, 20번째 epoch에서만 10985초(약 3시간)의 이상 정지가 있었고 나머지 48개 epoch는 전부 정상 속도(69~77초/epoch, EXP-002와 거의 동일)였다. box_gain 변경이 연산 속도에 영향을 줄 이유가 없으므로, 이 정지는 학습 외적 요인(컴퓨터 유휴/절전 추정)으로 판단한다. 이 구간을 제외한 실제 연산 시간은 약 58분으로 EXP-002와 사실상 동일하다.

### 학습 결과 요약

`train/box_loss`가 이전 실험들보다 훨씬 큰 값(5.5→3.3대)으로 시작해서 비슷한 범위로 수렴한다 — `box` gain을 7.5→15.0으로 올렸으니 손실에 곱해지는 가중치가 커진 것이 그대로 반영된 것으로, 설정이 의도대로 적용됐음을 보여준다. Recall은 EXP-002보다 더 뚜렷한 상승 추세를 보이며 0.35~0.4대까지 올라간다(Last 기준 0.375, EXP-002의 0.29보다 높음).

### Early Stopping 여부

발동했다(49 epoch에서 종료, 패치 15 기준 34번째 이후 개선 없음). EXP-002(50 epoch 전부 완주)와 달리 이번엔 조기 종료됐다.

### 과적합 가능성

낮음. Train/Val Loss가 끝까지 나란히 움직인다(EXP-002에서 봤던 후반부 val 상승 조짐은 이번엔 뚜렷하지 않음).

# 10. 추론 설정

Confidence 0.25, NMS IoU 0.70, imgsz 960(학습과 동일), 매칭(TP 판정) IoU 0.5 — EXP-001·EXP-002와 동일한 기준으로 비교 가능하게 유지했다. Test 46장 전체 추론.

# 11. 전체·클래스별 성능

## 11.1 전체 성능

| 지표 | EXP-002(imgsz 960) | EXP-003(box=15.0) |
| --- | ---: | ---: |
| Precision | 0.678 | 0.433 |
| Recall | 0.238 | 0.151 |
| mAP50 | 0.201 | 0.118 |
| mAP50-95 | 0.075 | 0.044 |

**전체 지표가 전부 뚜렷하게 악화됐다.** box loss gain을 7.5→15.0으로 올린 목적은 박스 위치 정밀도(mAP50-95)를 높이는 것이었는데, 실제로는 mAP50-95를 포함해 모든 지표가 나빠졌다.

참고로 학습 중 Validation 기준 Best 지표(9.1절, mAP50-95=0.10336)는 EXP-002의 Best 값(0.10914)과 큰 차이가 없다. 즉 **Validation에서는 EXP-002와 비슷한 수준을 유지했지만, Test셋에서는 성능 격차가 크게 벌어졌다.** Test셋 규모가 46장/58개체로 작아 val-test 간 괴리가 원래도 클 수 있는 조건이라, 이번 결과만으로 "box=15.0이 일반화를 악화시켰다"고 단정하기는 어렵다 — 표본 크기에 따른 통계적 노이즈일 가능성도 함께 열어둔다.

## 11.2 클래스별 성능

| 클래스 | Precision | Recall | AP50 | AP50-95 |
| --- | ---: | ---: | ---: | ---: |
| porosity | 0.333 | 0.036 | 0.018 | 0.005 |
| slag_inclusion | 0.533 | 0.267 | 0.219 | 0.083 |

porosity가 특히 크게 악화됐다(EXP-002 Recall 0.143 → 0.036, 28개 중 1개만 탐지). slag_inclusion은 상대적으로 덜 나빠졌다(Recall 0.333→0.267, AP50-95는 오히려 0.072→0.083으로 소폭 개선). 즉 **이번 악화는 두 클래스에 균등하지 않고 porosity에 집중됐다.**

## 11.3 객체 크기별 성능

| 크기 | EXP-002 Recall | EXP-003 Recall |
| --- | ---: | ---: |
| Small(33개) | 0.121(TP 4) | **0.182(TP 6)** |
| Medium(24개) | 0.375(TP 9) | **0.125(TP 3)** |
| Large(1개) | 0.000 | 0.000(표본 1개) |

Small Recall만 놓고 보면 개선된 것처럼 보인다(0.121→0.182). 그러나 Medium Recall이 그보다 훨씬 크게 악화됐다(0.375→0.125, TP 9건→3건). 표본이 워낙 작아(Small 33개, Medium 24개) 각 구간의 TP 2~3건 차이가 Recall을 0.05~0.1씩 흔드는 상황이라, Small 쪽의 상승을 "box gain이 작은 객체 인식을 개선했다"는 근거로 보기는 어렵다 — 전체 지표가 이미 악화된 상태에서 나온 부분적 변동으로 판단한다.

# 12. Threshold 비교

| Threshold | EXP-002 Recall(평가기준) | EXP-003 Recall(평가기준) |
| --- | ---: | ---: |
| 0.10 | 0.414 | 0.293 |
| 0.25 | 0.241 | 0.155 |
| 0.50 | 0.052 | 0.017 |
| 0.75 | 0.017 | 0.000 |

모든 Threshold 구간에서 EXP-003의 Recall이 EXP-002보다 낮다 — 특정 구간의 우연이 아니라 전 구간에 걸친 일관된 하락이다. 예측 개수 자체도 줄었다(conf=0.25 기준 predicted_count 23→18). 오토라벨링 후보 Threshold는 기존과 동일하게 0.25를 유지한다(이번 실험은 Threshold 재선정이 목적이 아니었고, 성능 자체가 악화되어 재선정할 이유도 없다).

# 13. 정성 평가

이번 실험은 오류 유형 구성 자체가 크게 달라졌다(14.1절) — localization_error·wrong_class 사례가 0건이다. 원래 정성 평가로 확인하려던 것("박스 과소 추정 패턴이 box gain 증가로 개선됐는가")을 판단할 근거 자체가 사라졌다. 남은 오류 53건 중 49건(92%)이 미탐(false_negative)이고, 나머지 4건은 전부 slag_inclusion 오탐(Confidence 0.267~0.536, 박스 면적 비율 대부분 3% 이하의 작은 박스)이다. 즉 모델이 전반적으로 더 적게, 더 낮은 확신도로 예측하는 쪽으로 변한 것이지, 예측한 박스의 위치 자체가 더 정확해진 것도 부정확해진 것도 아니다 — "비교할 위치 오류 사례가 남아있지 않다"는 것 자체가 이번 실험의 정성적 결론이다.

# 14. 원인 분석

## 14.1 오류 유형 집계

| 오류 유형 | EXP-002 | EXP-003 |
| --- | ---: | ---: |
| 미탐(false_negative) | 42 | 49 |
| 오탐(false_positive) | 4 | 4 |
| 위치 오류(localization_error) | 2 | 0 |
| 클래스 오류(wrong_class) | 1 | 0 |

미탐이 42→49건으로 늘었다(주로 porosity, 11.2절). 오탐은 4건으로 동일. 위치 오류·클래스 오류는 이번엔 아예 발생하지 않았는데, 이는 "위치·클래스 판단이 정확해져서"가 아니라 **애초에 매칭 대상이 될 만한 예측(TP에 근접한 예측)이 크게 줄었기 때문**이다(threshold_comparison 기준 TP 14건→9건).

## 14.2 원인 판단

- **box loss gain을 2배로 올린 것은 의도한 효과(박스 위치 정밀도 개선)를 내지 못했고, 오히려 전반적인 탐지 성능을 떨어뜨렸다.** 학습 손실 곡선(9.2절)을 보면 box_loss 자체는 gain에 비례해 커진 값으로 정상적으로 반영됐지만, 이것이 Recall·mAP 전체 하락으로 이어졌다 — 데이터가 300장 수준으로 적은 상황에서 box 회귀 손실 비중을 과도하게 높이면 분류·객체성(objectness) 학습에 배분되는 그래디언트가 상대적으로 줄어드는 부작용이 있었을 가능성이 크다.
- Val 지표는 EXP-002와 큰 차이가 없었는데 Test 지표만 크게 벌어진 점(11.1절)은, 이 변화가 "학습 자체의 실패"라기보다 "이 작은 데이터셋 규모에서 val 선택 기준(mAP50-95)이 Test 일반화를 보장하지 못한다"는 좀 더 근본적인 문제를 함께 시사한다.
- 데이터·라벨 관점의 결론은 이전 실험들과 동일하게 유지된다(라벨 오류 의심 사례 없음, 데이터 절대량 부족이 근본 배경). 이번 실험은 그 배경 위에서 "box gain 조정"이라는 후보가 이 데이터 규모에는 맞지 않았다는 것을 보여준다.

# 15. Baseline 비교

| 항목 | EXP-002(imgsz 960) | EXP-003(box=15.0) | 변화 |
| --- | --- | --- | --- |
| 변경 변수 | - | box loss gain 7.5→15.0 | - |
| 학습 시간(실연산 기준) | 00:58:44(50 epoch, 미발동) | 약 58분(49 epoch, Early Stop, epoch20 이상 정지 3시간 제외) | 거의 동일 |
| 전체 Recall | 0.238 | 0.151 | -0.087 |
| 전체 mAP50-95 | 0.075 | 0.044 | -0.031 |
| Small Recall | 0.121 | 0.182 | +0.061 |
| Medium Recall | 0.375 | 0.125 | -0.250 |
| 미탐 건수 | 42 | 49 | +7 |
| 오탐 건수 | 4 | 4 | 변화 없음 |

## 성공 기준 대비 판정 (`docs/10_next_experiment_plan.md` 후속 우선순위 2번 기준)

| 기준 | 목표 | 실제 결과 | 충족 여부 |
| --- | --- | --- | --- |
| 주 지표: 위치 정밀도(mAP50-95) | EXP-002 대비 개선(0.075 이상) | 0.044 | **미충족** |
| 가드레일1: 전체 Recall | EXP-002 대비 유지(0.238 이상) | 0.151 | **미충족** |
| 가드레일2: 학습 시간 | EXP-002와 비슷한 수준 유지 | 약 58분(실연산 기준, 동일) | 충족 |

# 16. 결론

**box loss gain 7.5→15.0 변경은 실패했다.** 애초 목표(박스 위치 정밀도 개선)는 달성되지 않았고, 주 지표(mAP50-95)와 가드레일(전체 Recall) 둘 다 EXP-002보다 뚜렷하게 나빠졌다. Small Recall만 소폭 상승했지만(0.121→0.182), 같은 크기 구간에 TP 2건 차이로 흔들릴 만큼 표본이 작고 Medium Recall이 그보다 훨씬 크게 악화됐다는 점을 함께 보면, 이를 "개선"으로 채택할 근거는 없다.

사전에 정의한 성공 기준(주 지표·가드레일 모두 미충족) 원칙에 따라, **box=15.0은 폐기하고 EXP-002(imgsz=960, box=7.5 기본값)를 현재까지의 최선 설정으로 유지한다.** `docs/08_error_analysis.md`의 후속 우선순위 3번(Hard Negative Mining) 또는 데이터 증강(대비 강조)·데이터 추가 확보 방향으로 다음 실험을 검토하는 것을 권장한다. 이번 실험은 "이 정도 규모(300장)의 데이터셋에서는 손실 가중치를 공격적으로 조정하는 것보다 데이터 자체를 늘리거나 증강하는 방향이 더 유효할 가능성"을 보여준 사례로 기록해둔다.

# 17. 다음 실험 계획

**차기 실험 제안**: imgsz=960·box=7.5(EXP-002 설정)를 기준으로 유지하고, `docs/08_error_analysis.md`에서 제시했던 후속 우선순위 3번(Hard Negative Mining) 또는 데이터 증강(대비 강조 augmentation)을 다음 변수로 검토한다. 상세 계획서는 필요 시 별도 작성한다.
