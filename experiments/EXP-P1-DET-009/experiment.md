# 1. 실험 기본 정보

- 실험 ID: EXP-P1-DET-009
- 실험명: RT_AL_YOLO26N_1280_ImgszSmallObject
- 실험 상태: COMPLETED
- 작성자: 자동 기록
- 실험 시작 일시: 2026-07-29T21:25:10+09:00
- 실험 종료 일시: 2026-07-29T21:58:55+09:00
- 관련 단계: 작업17
- 실험 유형: DETECTION_TRAINING
- Git Branch: feature/exp008-gpu-device-comparison
- Git Commit: 7027cc1d13da9a1a3df1075155f05470d2aa14c4
- 설정 파일 경로: /home/widep_ollama/kjm/defect_detection_ai_test/experiments/EXP-P1-DET-009/train_config.yaml
- 결과 폴더 경로: /home/widep_ollama/kjm/defect_detection_ai_test/experiments/EXP-P1-DET-009/runs/train

# 2. 목적과 가설

- 실험 목적: EXP-P1-DET-008과 동일 설정(GPU, dataset_v3, YOLO26n, epochs=50 등)에서
  imgsz만 960에서 1280으로 키워 Small 객체 Recall 개선 여부를 검증한다.
- 검증할 핵심 질문: imgsz 외 모든 설정이 동일할 때 imgsz 1280이 960보다
  Small 객체(상대 면적 1% 미만) Recall을 유의미하게 개선하는가?
- 현재 문제: EXP-P1-DET-005부터 Small 객체 Recall이 낮은 문제가 반복되고 있다.
- 가설: imgsz 외 모든 설정이 동일할 때 imgsz 1280이 960보다
  Small 객체(상대 면적 1% 미만) Recall을 유의미하게 개선한다.
- 예상 결과: 후속 Test 추론과 크기별 평가에서 Small 객체 Recall이 개선된다.
- 성공 판단 기준: 예외 없이 정상 종료되고 총 실행 시간과 필수 산출물이 보존된다.

# 3. 기준 실험

`EXP-P1-DET-008` (동일 GPU, imgsz=960).

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
- 데이터 선정 목록: `metadata/v2/selected_dataset.csv`
- 데이터 검증 보고서: `reports/dataset/v2/`

## 5.2 데이터 수

| 구분 | 이미지 수 | 객체 수 |
| --- | ---: | ---: |
| Train | 482 | 548 |
| Validation | 85 | 141 |
| Test | 84 | 123 |
| 전체 | 651 | 812 |

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
- 학습 입력: `data/processed/dataset_v3/data.yaml`

# 7. 실행 환경

GPU 학습 실행 시점에 시스템과 연산 장치 정보를 직접 수집했다.

```text
System Information
  Python : 3.13.14
  OS     : Linux-6.8.0-124-generic-x86_64-with-glibc2.35
  CPU    : x86_64
  RAM    : 31.01 GiB

Package Versions
  torch       : 2.11.0+cu128
  ultralytics : 8.4.110

Compute Device
  CUDA Available : Yes
  Device         : GPU
  GPU            : Tesla T4
  VRAM           : 14.56 GiB
```

- 실행 장비: GPU 서버
- 실행 경로: /home/widep_ollama/kjm/defect_detection_ai_test
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
- 모델 파일 경로: /home/widep_ollama/kjm/defect_detection_ai_test/yolo26n.pt

## 8.2 학습 설정

| 설정 | 값 |
| --- | --- |
| Epoch | 50 |
| Patience | 15 |
| Image Size | 1280 |
| Batch Size 요청값 | -1 (auto) |
| 실제 Batch Size | 5 |
| Optimizer | auto |
| Initial Learning Rate | library default (0.01) |
| Weight Decay | library default (0.0005) |
| AMP | library default (True) |
| Device | 0 |
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

- 학습 시작 일시: 2026-07-29T21:25:10+09:00
- 학습 종료 일시: 2026-07-29T21:58:55+09:00
- 총 실행 시간: 00:33:45
- 정상 종료 여부: 예
- Early Stopping 여부: 예
- 종료 Epoch: 49
- Best Epoch: 34
- Best 모델 경로: /home/widep_ollama/kjm/defect_detection_ai_test/experiments/EXP-P1-DET-009/models/best.pt
- Last 모델 경로: /home/widep_ollama/kjm/defect_detection_ai_test/experiments/EXP-P1-DET-009/models/last.pt
- 결과 폴더: /home/widep_ollama/kjm/defect_detection_ai_test/experiments/EXP-P1-DET-009/runs/train

## 9.1 학습 결과 요약

| 지표 | Best 결과 | Last 결과 |
| --- | ---: | ---: |
| Train Loss (Box+Class+L1) | 4.456530 | 3.901310 |
| Validation Loss (Box+Class+L1) | 3.665420 | 3.359180 |
| Precision | 0.592150 | 0.456550 |
| Recall | 0.389190 | 0.436040 |
| mAP50 | 0.435740 | 0.419010 |
| mAP50-95 | 0.171820 | 0.153270 |

Best epoch loss:

- Box Loss: 1.733170
- Class Loss: 2.717270
- L1 Loss: 0.006090

## 9.2 학습 과정 해석

정량·정성 해석은 후속 평가 작업18~25에서 작성한다. 본 작업에서는 학습 완료 여부와 원시 학습 지표를 기록한다.

# 10. 추론 설정

Confidence 0.25, NMS IoU 0.70, imgsz 1280(학습과 동일), 매칭(TP 판정) IoU 0.5 — EXP-005~008과 동일한 기준으로 비교 가능하게 유지했다. Test 84장 전체 추론(dataset_v3 Test셋, EXP-005와 동일한 이미지). Device는 GPU(0).

# 11. 전체·클래스별 성능

## 11.1 전체 성능

| 지표 | EXP-005(imgsz 960, CPU) | EXP-009(imgsz 1280, GPU) |
| --- | ---: | ---: |
| Precision | 0.535 | **0.620** |
| Recall | **0.446** | 0.288 |
| mAP50 | **0.342** | 0.217 |
| mAP50-95 | **0.131** | 0.088 |

Precision만 오르고 Recall·mAP50·mAP50-95는 모두 하락했다. mAP 계열은 특정 Confidence 임계값에 의존하지 않는 지표인데도 함께 떨어졌으므로, 단순히 "임계값 0.25 기준으로 덜 잡힌 것"이 아니라 실질적인 랭킹·탐지 품질 저하로 봐야 한다.

## 11.2 클래스별 성능

| 클래스 | EXP-005 Precision | EXP-009 Precision | EXP-005 Recall | EXP-009 Recall | EXP-005 AP50-95 | EXP-009 AP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| porosity | 0.557 | 0.547 | 0.405 | 0.345 | 0.110 | 0.108 |
| slag_inclusion | 0.514 | **0.692** | 0.487 | **0.231** | 0.153 | **0.067** |

두 클래스 모두 Recall이 하락했지만 정도가 다르다. porosity는 소폭 하락(0.405→0.345)한 반면, **slag_inclusion은 Recall이 절반 이하로(0.487→0.231), AP50-95도 절반 이하로(0.153→0.067) 떨어졌다.** slag_inclusion이 imgsz 확대에 유독 취약했다 — 정확한 원인은 이 실험 하나로 단정할 수 없지만, 14절에서 가능성을 짚는다.

## 11.3 객체 크기별 성능

| 크기 | EXP-005 Recall(GT수) | EXP-009 Recall(GT수) |
| --- | ---: | ---: |
| Small | **0.356**(87) | 0.322(87) |
| Medium | **0.515**(33) | 0.273(33) |
| Large | 0.000(3) | 0.000(3) |

애초 가설(imgsz 확대가 Small 객체 Recall을 개선한다)과 반대로 Small도 악화됐고, Medium은 더 큰 폭으로 악화됐다(Large는 표본 3개라 판단 보류). "해상도를 키우면 작은 객체를 더 잘 잡는다"는 일반적 통념이 이번 데이터셋·환경 조합에서는 성립하지 않았다.

# 12. Threshold 비교

수행하지 않음. 11절에서 이미 mAP(임계값 무관 지표)까지 하락해 가설이 명확히 기각됐으므로, Threshold 스윕까지 진행할 실익이 없다고 판단했다. 필요 시 후속 요청으로 진행 가능하다.

# 13. 정성 평가

수행하지 않음(오류 사례 시각화 스크립트는 이번 실험 범위 밖). 12절과 같은 이유로 생략했다.

# 14. 원인 분석

**가장 유력한 원인: imgsz 확대와 함께 실제 Batch Size가 자동으로 줄었다(9 → 5).** `batch=-1`(auto)이 GPU 메모리(Tesla T4, 14.56GiB) 제약 때문에 더 작은 값을 선택했다. 즉 이번 실험은 순수하게 "imgsz만" 바뀐 게 아니라 "imgsz 확대 + batch size 축소"가 동시에 일어났다 — batch가 작아지면 gradient 추정이 더 노이즈해져 일반화 성능이 떨어질 수 있고, 이것이 imgsz 자체의 효과와 뒤섞여 있을 가능성이 있다.

**Val 기준(9.1절, EXP-008과 동일 방식)으로 보면 하락 폭이 더 작다.** EXP-008(imgsz 960) Best: Precision 0.605 / Recall 0.390 / mAP50 0.468 / mAP50-95 0.192. EXP-009(imgsz 1280) Best: Precision 0.592 / Recall 0.389 / mAP50 0.436 / mAP50-95 0.172. Recall은 거의 그대로(0.390→0.389)이고 mAP50-95 하락도 완만하다(0.192→0.172). 반면 11.1절의 Test 기준 비교(EXP-005 대비)는 훨씬 큰 낙폭을 보인다(Recall 0.446→0.288). Test셋은 84장/123개 객체로 표본이 작아 노이즈 폭이 크다는 점을 감안하면, "imgsz 자체의 완만한 하락"에 "작은 Test 표본의 변동성"이 겹쳐 증폭됐을 가능성이 있다 — 다만 이는 추정이며 이 실험 하나로 정확한 기여도를 분리할 수는 없다.

**slag_inclusion만 유독 크게 나빠진 이유는 확인하지 못했다.** slag_inclusion 객체가 porosity보다 가늘고 긴 형태가 많아 고해상도에서 Mosaic·Scale 등 기본 증강과 상호작용이 나빠졌을 가능성을 의심해볼 수 있으나, 이번 실험 데이터만으로는 추측 수준이다.

# 15. Baseline 비교

| 비교 기준 | 대상 | Precision | Recall | mAP50 | mAP50-95 |
| --- | --- | ---: | ---: | ---: | ---: |
| Val(9.1, GPU 동일) | EXP-008(imgsz 960) | 0.605 | 0.390 | 0.468 | 0.192 |
| Val(9.1, GPU 동일) | EXP-009(imgsz 1280) | 0.592 | 0.389 | 0.436 | 0.172 |
| Test(11.1, calculate_metrics) | EXP-005(imgsz 960, CPU) | 0.535 | 0.446 | 0.342 | 0.131 |
| Test(11.1, calculate_metrics) | EXP-009(imgsz 1280, GPU) | 0.620 | 0.288 | 0.217 | 0.088 |

어느 기준으로 봐도 EXP-009가 더 낫다고 할 근거는 없다. Val 기준으로는 완만한 하락, Test 기준으로는 뚜렷한 하락이다.

# 16. 결론

**가설 기각. imgsz 1280은 채택하지 않는다.** Precision은 소폭 개선됐지만 Recall·mAP50·mAP50-95가 전 지표에서 하락했고, 애초 목표였던 Small 객체 Recall도 개선되지 않고 오히려 악화됐다(0.356→0.322). 이 프로젝트가 EXP-001부터 겪어온 "박스 위치 정밀도" 문제(위치 오류, mAP50 대비 mAP50-95 격차)도 이번 실험으로 해결되지 않았다 — 즉 그 문제의 원인은 입력 해상도가 아닐 가능성이 높아졌다.

# 17. 다음 실험 계획

- imgsz 확대를 다시 시도한다면, batch size 축소를 먼저 해결해야 한다(gradient accumulation으로 유효 batch를 유지하거나, VRAM이 더 큰 장비를 사용).
- EXP-001부터 반복돼온 박스 위치 정밀도 문제는 해상도·모델 크기·전처리(CLAHE)·데이터 균형 어느 쪽으로도 해결되지 않았다(EXP-006 실패, EXP-007 트레이드오프, EXP-009 실패). 다음 우선순위는 이 문제의 근본 원인(라벨 품질, loss 함수/anchor 설정 등)을 직접 조사하는 쪽을 권장한다.
- 추가 실험보다, 지금까지 5개 이상의 실험에서 반복 재현된 이 한계를 원인 조사 단계로 전환하는 것을 제안한다.
