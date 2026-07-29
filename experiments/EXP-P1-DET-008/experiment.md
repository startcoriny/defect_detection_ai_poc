# 1. 실험 기본 정보

- 실험 ID: EXP-P1-DET-008
- 실험명: RT_AL_YOLO26N_960_GPUDeviceComparison
- 실험 상태: COMPLETED
- 작성자: 자동 기록
- 실험 시작 일시: 2026-07-29T20:24:04+09:00
- 실험 종료 일시: 2026-07-29T20:44:33+09:00
- 관련 단계: 작업17
- 실험 유형: DETECTION_TRAINING
- Git Branch: feature/exp008-gpu-device-comparison
- Git Commit: 7027cc1d13da9a1a3df1075155f05470d2aa14c4
- 설정 파일 경로: /home/widep_ollama/kjm/defect_detection_ai_test/experiments/EXP-P1-DET-008/train_config.yaml
- 결과 폴더 경로: /home/widep_ollama/kjm/defect_detection_ai_test/experiments/EXP-P1-DET-008/runs/train

# 2. 목적과 가설

- 실험 목적: EXP-P1-DET-005와 동일 설정(dataset_v3, YOLO26n, epochs=50 등)을
  GPU에서 재학습해 CPU 대비 학습 속도를 비교한다.
- 검증할 핵심 질문: device 외 모든 설정이 동일할 때 GPU 학습이
  CPU 학습(EXP-P1-DET-005)보다 얼마나 빠르게 완료되는가?
- 현재 문제: 동일 학습 설정에 대한 CPU와 GPU의 총 실행 시간 비교값이 없다.
- 가설: device 외 모든 설정이 동일할 때 GPU 학습이 CPU 학습
  (EXP-P1-DET-005)보다 유의미하게 빠르게 완료된다.
- 예상 결과: GPU 학습이 정상 종료되고 CPU Baseline 대비 배속이 기록된다.
- 성공 판단 기준: 예외 없이 정상 종료되고 총 실행 시간과 필수 산출물이 보존된다.

# 3. 기준 실험

`EXP-P1-DET-005` (동일 설정, device=cpu).

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
| Image Size | 960 |
| Batch Size 요청값 | -1 (auto) |
| 실제 Batch Size | 9 |
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

- 학습 시작 일시: 2026-07-29T20:24:04+09:00
- 학습 종료 일시: 2026-07-29T20:44:33+09:00
- 총 실행 시간: 00:20:29
- 정상 종료 여부: 예
- Early Stopping 여부: 아니오
- 종료 Epoch: 51
- Best Epoch: 36
- Best 모델 경로: /home/widep_ollama/kjm/defect_detection_ai_test/experiments/EXP-P1-DET-008/models/best.pt
- Last 모델 경로: /home/widep_ollama/kjm/defect_detection_ai_test/experiments/EXP-P1-DET-008/models/last.pt
- 결과 폴더: /home/widep_ollama/kjm/defect_detection_ai_test/experiments/EXP-P1-DET-008/runs/train

## 9.1 학습 결과 요약

| 지표 | Best 결과 | Last 결과 |
| --- | ---: | ---: |
| Train Loss (Box+Class+L1) | 3.927710 | 3.575560 |
| Validation Loss (Box+Class+L1) | 4.098210 | 3.996480 |
| Precision | 0.604740 | 0.595770 |
| Recall | 0.389640 | 0.365320 |
| mAP50 | 0.467530 | 0.420830 |
| mAP50-95 | 0.192370 | 0.171700 |

Best epoch loss:

- Box Loss: 1.812000
- Class Loss: 2.109680
- L1 Loss: 0.006030

# 9.2 CPU Baseline 대비 비교

| 실험 | Device | 총 실행 시간 | 초 |
| --- | --- | ---: | ---: |
| EXP-P1-DET-005 | cpu | 02:10:53 | 7853 |
| EXP-P1-DET-008 | 0 | 00:20:29 | 1229.16 |

- CPU 시간(초) / GPU 시간(초): 6.39배

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
