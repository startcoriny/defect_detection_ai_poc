# 1. 실험 기본 정보

- 실험 ID: EXP-P1-DET-005
- 실험명: RT_AL_YOLO26N_960_SlagOversample
- 실험 상태: COMPLETED
- 작성자: 자동 기록
- 실험 시작 일시: 2026-07-28T12:33:16+09:00
- 실험 종료 일시: 2026-07-28T14:44:09+09:00
- 관련 단계: 작업17
- 실험 유형: DETECTION_TRAINING
- Git Branch: feature/exp005-slag-oversample
- Git Commit: 41316dcf046e784578f58f1f0d73b3922ee5b1e1
- 설정 파일 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-005\train_config.yaml
- 결과 폴더 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-005\runs\train

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
- 데이터 선정 목록: `metadata/v2/selected_dataset.csv`(선별 자체는 dataset_v2와 동일 — dataset_v3는 그 위에 Train만 오버샘플링한 것)
- 데이터 검증 보고서: `reports/dataset/v2/`(Val·Test는 dataset_v2와 동일), Train 오버샘플링 로그: `src/dataset/v3/oversample_slag.py` 실행 결과(아래 표에 반영)

**[정정]** 이 절의 자동 생성 값은 `reports/dataset/v2/split_distribution.csv`(dataset_v2 기준, Train 오버샘플링 반영 전)를 그대로 참조한다. 이미지 수(Train 482장)는 실제 폴더를 직접 세어 정확하지만, **객체 수는 오버샘플링 반영 전 수치**라 아래 표에서 실제 dataset_v3 값(`oversample_slag.py` 실행 로그 기준)으로 정정했다. 모델 성능(9~14절)에는 영향이 없다 — 학습 자체는 처음부터 실제 dataset_v3(Train 482장, porosity 382객체·slag_inclusion 336객체)로 정상 진행됐다.

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

- 학습 시작 일시: 2026-07-28T12:33:16+09:00
- 학습 종료 일시: 2026-07-28T14:44:09+09:00
- 총 실행 시간: 02:10:53
- 정상 종료 여부: 예
- Early Stopping 여부: 아니오
- 종료 Epoch: **50**(스크립트 자동 판정은 "51"로 잘못 기록됨 — 아래 "9.0 발견한 버그" 참조)
- Best Epoch: **37**(스크립트 자동 판정은 "48"로 잘못 기록됨 — 아래 참조)
- Best 모델 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-005\models\best.pt
- Last 모델 경로: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-005\models\last.pt
- 결과 폴더: C:\develop\widep\defect_detection_ai_test\experiments\EXP-P1-DET-005\runs\train

## 9.0 발견한 버그: `read_results()`의 Epoch 번호가 항상 1 많게 표시됨

`train_baseline.py`(exp1~exp5 전부 동일, EXP-001부터 있던 버그)의 `read_results()`가 `best_epoch = int(best_row["epoch"]) + 1`, `final_epoch = int(last_row["epoch"]) + 1`로 계산한다. 그런데 Ultralytics의 `results.csv` `epoch` 컬럼은 이미 1부터 시작하는 값이다(직접 확인: 50 epoch 학습 시 첫 행 `epoch=1`, 마지막 행 `epoch=50` — Ultralytics 로그의 "50 epochs completed"와 정확히 일치). 즉 `+1`을 더할 필요가 없는데 더하고 있어서, "종료 Epoch"·"Best Epoch"가 실제보다 항상 1 크게 표시된다.

**이번에도 실질적 영향은 없다** — `best.pt` 저장은 Ultralytics 자체 기준으로 이뤄지므로 지금까지의 모든 추론·평가는 문제없이 올바른 모델을 사용했다. 영향받는 건 `experiment.md`에 표시되는 Epoch 번호뿐이다. EXP-003의 fitness 공식 버그(별개 문제)와 달리, 이 버그는 EXP-001부터 전 실험에 동일하게 있었을 것으로 추정되나(스크립트가 계속 복사돼 왔으므로), 결과 수치나 결론에는 영향이 없어 이번 실험 문서만 정정하고 과거 실험 문서는 재정정하지 않는다(필요 시 사용자 확인 후 별도 진행).

또한 EXP-003에서 발견했던 fitness 공식 버그(`0.1*mAP50+0.9*mAP50-95` vs 실제 `mAP50-95` 단독)도 이번엔 실제로 다른 epoch을 가리켰다(CSV epoch 37 vs 47) — 아래 9.1절은 진짜 Best(mAP50-95 기준 epoch 37)로 정정했다.

## 9.1 학습 결과 요약 (정정됨)

| 지표 | Best 결과(정정) | Last 결과 |
| --- | ---: | ---: |
| Train Loss (Box+Class+L1) | 3.664430 | 3.409300 |
| Validation Loss (Box+Class+L1) | 4.535380 | 4.028220 |
| Precision | 0.604040 | 0.569410 |
| Recall | 0.390990 | 0.439190 |
| mAP50 | 0.438130 | 0.421010 |
| mAP50-95 | 0.165570 | 0.154690 |

Best epoch loss:

- Box Loss: 1.729930
- Class Loss: 1.929150
- L1 Loss: 0.005350

참고로 정정 전(old-formula)이 골랐던 epoch 47의 mAP50-95(0.16528)와 진짜 Best(epoch 37, 0.16557)의 차이는 0.0003 수준으로 사실상 동률에 가깝다 — 어느 쪽을 Best로 봐도 실질적 결론(11~16절)에는 영향이 없다.

## 9.2 학습 과정 해석

Early Stopping 미발동(50 epoch 전부 완주). 총 학습 시간은 2.179시간으로 EXP-004(1.859시간)보다 김 — Train 이미지가 398장(중복 없음)→482장(slag_inclusion 84장 중복 포함)으로 늘어난 것과 대략 비례한다.

Best(epoch 37)와 Last(epoch 50) 지표가 서로 큰 차이 없이 비슷한 수준(mAP50-95 0.166 vs 0.155)이라 EXP-002·004에서 봤던 "중반 정점 후 후반 하락"의 폭이 이번엔 상대적으로 작다 — 오버샘플링으로 Train 데이터가 늘면서 후반 epoch까지도 비교적 안정적으로 유지된 것으로 보인다. Train/Val Loss는 끝까지 나란히 움직여 과적합 징후는 보이지 않는다.

# 10. 추론 설정

Confidence 0.25, NMS IoU 0.70, imgsz 960(학습과 동일), 매칭(TP 판정) IoU 0.5 — EXP-001~004와 동일한 기준으로 비교 가능하게 유지했다. Test 84장 전체 추론(dataset_v2·v3 공통 Test셋, EXP-004와 동일한 이미지).

# 11. 전체·클래스별 성능

## 11.1 전체 성능

| 지표 | EXP-004(dataset_v2) | EXP-005(dataset_v3, Train slag 오버샘플링) |
| --- | ---: | ---: |
| Precision | 0.798 | 0.535 |
| Recall | 0.239 | **0.446** |
| mAP50 | 0.210 | **0.342** |
| mAP50-95 | 0.082 | **0.131** |

Precision은 낮아졌지만(모델이 더 적극적으로 예측하게 됨) Recall·mAP50·mAP50-95 전부 뚜렷하게 개선됐다. mAP 계열 지표는 특정 Confidence 임계값에 의존하지 않는 지표라, 이 개선이 단순히 "더 많이 찍어서 우연히 맞은" 임계값 효과가 아니라 실질적인 랭킹·탐지 품질 개선임을 뒷받침한다.

## 11.2 클래스별 성능

| 클래스 | EXP-004 Precision | EXP-005 Precision | EXP-004 Recall | EXP-005 Recall | EXP-004 AP50-95 | EXP-005 AP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| porosity | 0.595 | 0.557 | 0.298 | **0.405** | 0.102 | 0.110 |
| slag_inclusion | 1.000 | 0.514 | 0.179 | **0.487** | 0.062 | 0.153 |

**주 목표였던 slag_inclusion Recall이 0.179→0.487로 완전히 회복됐고, EXP-002(0.333)보다도 높다.** 예상외로 **porosity Recall도 0.298→0.405로 함께 개선됐다** — slag_inclusion만 복제했는데 porosity까지 좋아진 것은, 단순히 "porosity 정보가 늘어서"라기보다 두 클래스 노출 비율이 균형에 가까워지면서 학습이 전반적으로 더 안정적으로 수렴했을 가능성을 시사한다(정확한 인과 관계는 이 실험 하나로 단정할 수 없다).

## 11.3 객체 크기별 성능

| 크기 | EXP-004 Recall(GT수) | EXP-005 Recall(GT수) |
| --- | ---: | ---: |
| Small | 0.241(87) | **0.356(87)** |
| Medium | 0.303(33) | **0.515(33)** |
| Large | 0.000(3) | 0.000(3) |

Small·Medium 모두 뚜렷하게 개선됐다(Large는 표본 3개로 여전히 판단하기 어렵다). EXP-002·003이 풀지 못했던 "작은 결함 미탐" 문제가 EXP-004(데이터 확장)에 이어 EXP-005(클래스 균형 재조정)에서도 계속 개선되고 있다.

# 12. Threshold 비교

| Threshold | EXP-004 Recall(평가기준) | EXP-005 Recall(평가기준) |
| --- | ---: | ---: |
| 0.10 | 0.463 | 0.585 |
| 0.25 | 0.276 | 0.446 |
| 0.50 | 0.065 | 0.130 |
| 0.75 | 0.016 | 0.008 |

0.10~0.50 전 구간에서 EXP-005의 Recall이 EXP-004보다 높다. 예측 개수 자체도 크게 늘었다(conf=0.25 기준 predicted_count 49→98). 오토라벨링 후보 Threshold는 기존과 동일하게 0.25를 유지한다(다만 Precision이 낮아진 만큼, 향후 실제 자동 라벨링 운영 단계에서는 Threshold를 다시 검토할 필요가 있다는 점을 남겨둔다).

## 12.1 Threshold 재선정 분석 (추가 분석, 재학습 없음)

Precision 하락(0.798→0.535)을 회복할 여지가 있는지 확인하기 위해, 기존 `best.pt`를 그대로 두고 0.25~0.50 구간을 세밀하게(0.05 간격) 재스캔했다(`src/model/exp5/select_threshold.py`, 결과: `reports/evaluation/EXP-P1-DET-005/threshold_selection.csv`). 새 실험이 아니라 기존 EXP-005 모델에 대한 평가 전용 분석이라 별도 실험 ID를 부여하지 않았다.

| Threshold | Precision | Recall | mAP50 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: |
| 0.25(현재) | 0.561 | 0.447 | 0.342 | 0.131 |
| 0.30 | 0.667 | 0.374 | 0.288 | 0.114 |
| 0.35 | 0.706 | 0.293 | 0.244 | 0.100 |
| 0.40 | 0.714 | 0.244 | 0.210 | 0.090 |
| 0.45 | 0.786 | 0.179 | 0.172 | 0.071 |
| 0.50 | 0.889 | 0.130 | 0.148 | 0.062 |

Threshold를 올릴수록 Precision과 Recall이 거의 1:1로 맞바꿔지는 단조 감소 형태로, 뚜렷하게 유리한 구간이 없다. mAP50·mAP50-95(threshold와 무관한 지표)도 threshold를 올릴수록 함께 하락해, 단순히 "덜 찍어서 우연히 맞은" 효과가 아니라 실제로 애매한 예측부터 걸러지는 정상적인 트레이드오프임을 뒷받침한다. 그나마 0.25→0.30 구간이 가장 나은 교환비(Precision +10.6%p 대 Recall −7.3%p)다.

**결론: 현재 Threshold 0.25를 유지한다.** 이 프로젝트는 자동 라벨링(사람이 CVAT로 검수·수정) 파이프라인이므로, 오탐(사람이 박스 하나를 지우면 되는 비용)보다 미탐(놓친 결함을 처음부터 새로 찾아 그려야 하는 비용)이 더 크다고 판단된다. Threshold를 높여 Precision을 개선하면 EXP-005의 핵심 성과인 Recall 회복을 도로 깎아먹게 되므로, 이번 분석 결과로는 Threshold를 바꾸지 않는 쪽을 권장한다. (다만 이는 검수 비용을 실측한 것이 아니라 도메인 상식에 근거한 판단이다.)

# 13. 정성 평가

위치 오류(localization_error) 사례(대표: `RT_AL_02_14487829_001`, Confidence 0.407)를 확인한 결과, EXP-001부터 반복돼온 "예측 박스가 GT보다 작게 나온다"는 패턴이 그대로 남아있다 — 오버샘플링은 이 문제를 겨냥한 변수가 아니었으므로 예상된 결과다.

오탐(false_positive) 38건 중 35건은 `duplicate_of_tp=False`(기존 TP와 겹치지 않는 독립적인 오탐)로, EXP-004까지 오탐의 상당수를 차지했던 "근접 중복 박스" 패턴과는 다르다. 대표 사례(`RT_AL_02_14488600_001`, Confidence 0.488)를 직접 확인한 결과, 육안으로는 결함이라 보기 어려운 매우 옅은 얼룩 위에 가늘고 작은 박스가 예측돼 있었다 — Precision 하락이 실제로는 "모델이 애매한 신호에도 더 적극적으로 예측을 내는 쪽으로 이동했다"는 정성적 관찰과 일치한다.

# 14. 원인 분석

## 14.1 오류 유형 집계

| 오류 유형 | EXP-004 | EXP-005 |
| --- | ---: | ---: |
| 미탐(false_negative) | 84 | 63 |
| 오탐(false_positive) | 9 | 38 |
| 위치 오류(localization_error) | 7 | 11 |
| 클래스 오류(wrong_class) | 1 | 1 |

미탐이 84→63건으로 줄었다(Recall 개선과 일치). 오탐은 9→38건으로 크게 늘었다(Precision 하락과 일치) — Recall-Precision 트레이드오프가 오류 유형 집계에도 그대로 드러난다. 위치 오류도 7→11건으로 늘었는데, 이는 예측 자체가 늘어난 결과(분모가 커짐)로 보인다.

## 14.2 원인 판단

- **Train 분할에서 slag_inclusion을 오버샘플링한 것은 의도한 효과(slag_inclusion Recall 회복)를 냈고, 부가적으로 porosity Recall과 전체 mAP까지 개선시켰다.** 가설(클래스 간 노출 빈도 불균형이 slag_inclusion 악화의 원인)이 사실로 확인됐다.
- **Precision 하락은 예상된 트레이드오프다.** 오버샘플링으로 두 클래스에 대한 모델의 전반적인 "탐지 적극성"이 높아지면서, 진짜 결함뿐 아니라 애매한 신호에 대해서도 더 많이 예측하게 됐다. 자동 라벨링 실무에 적용하려면 이 Precision-Recall 트레이드오프를 감안한 Threshold 재검토가 필요하다(12절 참고).
- **박스 위치 정밀도 문제는 여전히 미해결이다.** 위치 오류 사례를 봐도 EXP-001부터 반복된 "박스 축소" 패턴이 그대로다 — 데이터 균형이나 양과는 무관한, 별도로 접근해야 할 축이다.

# 15. Baseline 비교

| 항목 | EXP-004(dataset_v2) | EXP-005(dataset_v3) | 변화 |
| --- | --- | --- | --- |
| 변경 변수 | - | Train slag_inclusion 오버샘플링(84장 1벌 복제) | - |
| 학습 시간 | 01:51:34(50 epoch, 미발동) | 02:10:53(50 epoch, 미발동) | +약 19분(Train 398→482장에 비례) |
| 전체 Recall | 0.239 | 0.446 | +0.207 |
| 전체 mAP50-95 | 0.082 | 0.131 | +0.049 |
| **slag_inclusion Recall(주 지표)** | **0.179** | **0.487** | **+0.308** |
| porosity Recall(가드레일) | 0.298 | 0.405 | +0.107 |
| Small Recall | 0.241 | 0.356 | +0.115 |

## 성공 기준 대비 판정 (`docs/decisions/12_next_experiment_plan.md` 기준)

| 기준 | 목표 | 실제 결과 | 충족 여부 |
| --- | --- | --- | --- |
| 주 지표: slag_inclusion Recall | EXP-004(0.179) 대비 개선, 0.30 이상 | 0.487 | **충족(목표 크게 초과)** |
| 가드레일 1: porosity Recall | EXP-004(0.298) 대비 유지, 0.25 이상 | 0.405 | **충족(오히려 개선)** |
| 가드레일 2: 전체 mAP50-95 | EXP-004(0.082) 이상 유지 | 0.131 | **충족** |

# 16. 결론

**Train 분할 slag_inclusion 오버샘플링은 명확한 성공이다 — 세 가지 성공 기준을 전부, 그것도 여유 있게 충족했다.** EXP-004에서 생긴 slag_inclusion Recall 회귀(0.333→0.179)를 완전히 회복했을 뿐 아니라(0.487, EXP-002보다도 높음), porosity Recall(0.405)과 Small 객체 Recall(0.356)까지 지금까지의 5개 실험 중 가장 높은 수준으로 끌어올렸다. 단순한 파일 복제만으로(새로운 데이터·증강·하이퍼파라미터 변경 없이) 이런 개선을 얻었다는 점에서, "클래스 간 노출 빈도 균형"이 이 데이터셋 규모에서 매우 중요한 요인이었음을 확인했다.

다만 Precision이 낮아진 트레이드오프(오탐 9→38건)가 있다 — 실제 자동 라벨링 운영에는 Threshold 재조정이 필요할 수 있다. 또한 박스 위치 정밀도 문제(위치 오류, mAP50 대비 mAP50-95 격차)는 5개 실험 내내 개선되지 않은 채 남아있다.

**dataset_v3(Train 오버샘플링)를 이후 실험의 기본 데이터셋으로 채택한다.** 다음 실험은 (a) Precision 회복을 위한 Threshold 재선정, 또는 (b) 여전히 미해결인 박스 위치 정밀도 문제(CLAHE 증강, 모델 크기 확대)를 검토할 것을 권장한다.

# 17. 다음 실험 계획

**차기 실험 제안**: dataset_v3·imgsz=960을 기준으로 유지한다. Confidence Threshold 재선정은 12.1절에서 완료했고(결론: 0.25 유지), 남은 후보는 `docs/decisions/12_next_experiment_plan.md`의 후속 우선순위 2번(CLAHE 대비 강조 증강)·3번(모델 크기 확대) — 5개 실험 내내 미해결인 박스 위치 정밀도 문제를 겨냥한 변수다. 다만 `docs/context/00-completion-criteria.md`·`02-task-list.md` 기준으로 보면 반복 실험 사이클(작업25)은 이미 목표를 충족하는 실험(EXP-005)을 확보했으므로, 추가 실험 없이 작업26(PoC 결과 문서화)으로 넘어가는 것도 함께 검토할 시점이다.
