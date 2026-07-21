## 1. 작성 목적

실험 기록은 단순히 성능 수치만 남기는 문서가 아니다.

다음 내용을 다시 확인할 수 있어야 한다.

```
무엇을 검증하려 했는가
→ 어떤 데이터와 모델을 사용했는가
→ 이전 실험에서 무엇을 변경했는가
→ 어떤 결과가 나왔는가
→ 왜 그런 결과가 나왔다고 판단하는가
→ 다음에는 무엇을 검증할 것인가
```

실험 기록이 없으면 모델 성능이 좋아지거나 나빠져도 원인을 추적하기 어렵다.

---

# 2. 실험 기록 관리 원칙

## 2.1 실험마다 고유 ID를 부여한다

권장 형식:

```
EXP-단계-작업유형-순번

예시:
EXP-P1-DET-001
EXP-P1-DET-002
EXP-P1-SEG-001
```

의미:

```
P1
→ 1단계 Python PoC

DET
→ Object Detection

SEG
→ Segmentation

001
→ 해당 유형의 첫 번째 실험
```

---

## 2.2 실험 이름은 변경 사항이 드러나도록 작성한다

좋지 않은 예:

```
테스트 1
두 번째 학습
성능 개선 테스트
```

권장 예:

```
RT_AL_YOLO26N_640_Baseline
RT_AL_YOLO26N_960_ImageSize
RT_AL_YOLO26S_640_ModelSize
RT_AL_YOLO26N_640_Data600
```

---

## 2.3 한 실험에서는 하나의 변수만 변경한다

예시:

```
Baseline
- 모델: YOLO26n
- 이미지 크기: 640
- Epoch: 50

비교 실험
- 모델: YOLO26n
- 이미지 크기: 960
- Epoch: 50
```

변경 변수:

```
Image Size
640 → 960
```

나머지 조건은 동일하게 유지한다.

---

## 2.4 실패한 실험도 기록한다

다음 실험도 삭제하지 않는다.

- 학습이 중단된 실험
- CUDA 메모리 부족 실험
- 잘못된 라벨로 실행된 실험
- 성능이 낮아진 실험
- 설정 파일 오류가 발생한 실험
- 데이터 누수가 발견된 실험

실패 기록은 같은 문제의 반복을 방지한다.

---

## 2.5 수동 입력값과 자동 생성값을 구분한다

### 수동 입력

- 실험 목적
- 변경 변수
- 가설
- 결과 해석
- 다음 실험

### 자동 수집

- 실행 시간
- Git Commit
- 패키지 버전
- GPU 정보
- 실제 Batch Size
- best Epoch
- 학습 시간
- Precision
- Recall
- mAP

가능한 정보는 학습 코드에서 자동 저장하도록 설계한다.

---

# 3. 실험 기록 기본 양식

## 3.1 실험 기본 정보

```
실험 ID:
실험명:
실험 상태:
작성자:
실험 시작 일시:
실험 종료 일시:
관련 단계:
실험 유형:
Git Branch:
Git Commit:
설정 파일 경로:
결과 폴더 경로:
```

### 실험 상태

다음 값으로 관리한다.

```
PLANNED
→ 실행 예정

RUNNING
→ 실행 중

COMPLETED
→ 정상 완료

FAILED
→ 실행 실패

INVALID
→ 데이터 누수나 설정 오류 등으로 결과 무효

STOPPED
→ 사용자가 중단

ARCHIVED
→ 비교 대상에서 제외하고 보관
```

### 실험 유형

```
DATA_VALIDATION
DATA_CONVERSION
DETECTION_TRAINING
SEGMENTATION_TRAINING
INFERENCE
THRESHOLD_COMPARISON
MODEL_COMPARISON
ERROR_ANALYSIS
```

---

## 3.2 실험 목적과 가설

```
실험 목적:

검증할 핵심 질문:

현재 문제:

가설:

예상 결과:

성공 판단 기준:
```

예시:

```
실험 목적:
입력 이미지 크기를 높이면 작은 기공의 Recall이 향상되는지 확인한다.

검증할 핵심 질문:
imgsz를 640에서 960으로 변경하면 Small 객체 Recall이 개선되는가?

현재 문제:
Baseline에서 작은 기공 12개 중 8개를 놓쳤다.

가설:
입력 해상도를 높이면 작은 기공의 특징이 더 많이 보존될 것이다.

예상 결과:
전체 Precision은 비슷하게 유지되면서 Small Recall이 상승한다.

성공 판단 기준:
Small Recall이 Baseline 대비 5%p 이상 향상되고 전체 Precision 하락이
3%p 이내일 것.
```

---

# 4. 기준 실험과 변경 사항

```
기준 실험 ID:

기준 실험명:

이번 실험에서 변경한 변수:

변경 전 값:

변경 후 값:

변경 이유:

동일하게 유지한 조건:
```

예시:

| 항목 | 기준 실험 | 현재 실험 | 변경 여부 |
| --- | --- | --- | --- |
| 데이터셋 | dataset_v1 | dataset_v1 | 동일 |
| 분할 | split_seed_42 | split_seed_42 | 동일 |
| 모델 | YOLO26n | YOLO26n | 동일 |
| 이미지 크기 | 640 | 960 | 변경 |
| Epoch | 50 | 50 | 동일 |
| Batch Size | 8 | 8 | 동일 |
| Seed | 42 | 42 | 동일 |

변경 변수가 두 개 이상이면 비교 실험으로 적절한지 다시 검토한다.

---

# 5. 데이터셋 정보

## 5.1 데이터셋 식별 정보

```
데이터셋 이름:
데이터셋 버전:
데이터 출처:
검사 유형:
소재:
라벨 원본 형식:
학습 라벨 형식:
클래스 매핑 파일:
데이터 선정 목록:
데이터 품질 보고서:
```

예시:

```
데이터셋 이름:
aihub_welding_rt_al_detection

데이터셋 버전:
dataset_v1

검사 유형:
RT

소재:
AL

라벨 원본 형식:
AI-Hub JSON Polygon

학습 라벨 형식:
YOLO Detection
```

---

## 5.2 데이터 수

| 구분 | 이미지 수 | 객체 수 | 정상 이미지 |
| --- | --- | --- | --- |
| Train |  |  |  |
| Validation |  |  |  |
| Test |  |  |  |
| 전체 |  |  |  |

---

## 5.3 클래스별 데이터 분포

| 클래스 | 클래스 ID | Train 이미지 | Train 객체 | Val 객체 | Test 객체 | 전체 객체 |
| --- | --- | --- | --- | --- | --- | --- |
| porosity | 0 |  |  |  |  |  |
| slag_inclusion | 1 |  |  |  |  |  |

추가 기록:

```
복수 객체 이미지 수:
복수 클래스 이미지 수:
Small 객체 수:
Medium 객체 수:
Large 객체 수:
제외 데이터 수:
제외 사유:
```

---

## 5.4 데이터 분할 정보

```
Train 비율:
Validation 비율:
Test 비율:
Random Seed:
분할 방법:
그룹 분할 기준:
중복 검사 여부:
분할 파일 경로:
```

분할 파일의 내용이 변경되면 같은 데이터셋 버전으로 취급하지 않는다.

---

# 6. 데이터 전처리 및 변환 정보

```
원본 이미지 형식:
원본 이미지 해상도:
이미지 Resize 방식:
Aspect Ratio 유지 여부:
Padding 여부:
정규화 방식:

원본 라벨:
변환 라벨:
변환 코드 버전:
좌표 검증 여부:
변환 후 재시각화 여부:
변환 실패 건수:
```

Polygon을 Bounding Box로 변환한 실험에서는 다음도 기록한다.

```
Bounding Box 계산 방식:
- x_min = Polygon x 최솟값
- y_min = Polygon y 최솟값
- x_max = Polygon x 최댓값
- y_max = Polygon y 최댓값

좌표 Clip 적용 여부:
너비 또는 높이 0 객체 처리:
이미지 밖 좌표 처리:
```

---

# 7. 실행 환경 정보

## 7.1 하드웨어

```
OS:
CPU:
RAM:
GPU:
GPU VRAM:
Storage:
```

## 7.2 소프트웨어

```
Python:
PyTorch:
CUDA:
cuDNN:
Ultralytics:
OpenCV:
NumPy:
Pandas:
```

## 7.3 실행 환경

```
실행 장비:
실행 경로:
가상환경:
Docker 사용 여부:
인터넷 연결 여부:
```

장비가 달라지면 Batch Size와 학습 시간이 달라질 수 있으므로 반드시 남긴다.

---

# 8. 모델 및 학습 설정

## 8.1 모델 정보

```
라이브러리:
작업 유형:
모델 계열:
모델 크기:
사전 학습 가중치:
사전 학습 사용 여부:
클래스 수:
모델 파일 경로:
```

---

## 8.2 학습 설정

| 설정 | 값 |
| --- | --- |
| Epoch |  |
| Patience |  |
| Image Size |  |
| Batch Size 요청값 |  |
| 실제 Batch Size |  |
| Optimizer |  |
| Initial Learning Rate |  |
| Weight Decay |  |
| AMP |  |
| Device |  |
| Workers |  |
| Seed |  |
| Deterministic |  |
| Cache |  |

직접 설정하지 않은 값은 다음과 같이 기록한다.

```
auto
library default
not configured
```

빈칸으로 두지 않는다.

---

## 8.3 데이터 증강 설정

| 증강 | 값 | 기본값/변경 |
| --- | --- | --- |
| HSV Hue |  |  |
| HSV Saturation |  |  |
| HSV Value |  |  |
| Rotation |  |  |
| Translation |  |  |
| Scale |  |  |
| Horizontal Flip |  |  |
| Vertical Flip |  |  |
| Mosaic |  |  |
| MixUp |  |  |

Baseline에서는 라이브러리 기본값을 사용하더라도 실제 저장된 설정을 기록한다.

---

# 9. 학습 실행 결과

```
학습 시작 일시:
학습 종료 일시:
총 실행 시간:
정상 종료 여부:
Early Stopping 여부:
종료 Epoch:
Best Epoch:
Best 모델 경로:
Last 모델 경로:
결과 폴더:
```

## 9.1 학습 결과 요약

| 지표 | Best 결과 | Last 결과 |
| --- | --- | --- |
| Train Loss |  |  |
| Validation Loss |  |  |
| Precision |  |  |
| Recall |  |  |
| mAP50 |  |  |
| mAP50-95 |  |  |

Detection Loss가 여러 개 제공되면 구분하여 작성한다.

```
Box Loss:
Class Loss:
DFL Loss:
```

---

## 9.2 학습 과정 해석

```
Train Loss 변화:

Validation Loss 변화:

Precision 변화:

Recall 변화:

mAP 변화:

과적합 가능성:

과소적합 가능성:

학습 중 특이사항:
```

---

# 10. 추론 설정

```
사용 모델:
추론 데이터:
Image Size:
Confidence Threshold:
NMS IoU Threshold:
Device:
Batch Size:
결과 저장 여부:
예측 TXT 저장 여부:
예측 JSON 저장 여부:
```

## 추론 시간

| 항목 | 값 |
| --- | --- |
| 처리 이미지 수 |  |
| 전체 처리 시간 |  |
| 이미지당 평균 시간 |  |
| 최소 시간 |  |
| 최대 시간 |  |

학습 속도와 추론 속도를 혼동하지 않도록 분리해서 기록한다.

---

# 11. 전체 성능 결과

## 11.1 전체 지표

| 지표 | 결과 |
| --- | --- |
| Precision |  |
| Recall |  |
| F1 Score |  |
| mAP50 |  |
| mAP50-95 |  |
| TP |  |
| FP |  |
| FN |  |

---

## 11.2 클래스별 성능

| 클래스 | Precision | Recall | AP50 | AP50-95 | TP | FP | FN |
| --- | --- | --- | --- | --- | --- | --- | --- |
| porosity |  |  |  |  |  |  |  |
| slag_inclusion |  |  |  |  |  |  |  |

---

## 11.3 객체 크기별 성능

| 크기 | 객체 수 | Recall | 미탐 수 | 평균 Confidence |
| --- | --- | --- | --- | --- |
| Small |  |  |  |  |
| Medium |  |  |  |  |
| Large |  |  |  |  |

객체 크기 기준도 함께 기록한다.

```
Small 기준:
Medium 기준:
Large 기준:
```

---

# 12. Confidence Threshold 비교 양식

| Confidence | 예측 객체 | TP | FP | FN | Precision | Recall | 이미지당 수정 예상 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.10 |  |  |  |  |  |  |  |
| 0.25 |  |  |  |  |  |  |  |
| 0.50 |  |  |  |  |  |  |  |
| 0.75 |  |  |  |  |  |  |  |

분석 항목:

```
Precision이 가장 높은 Threshold:

Recall이 가장 높은 Threshold:

오탐 삭제가 가장 적은 Threshold:

미탐 추가가 가장 적은 Threshold:

오토라벨링 후보 Threshold:

선정 이유:
```

---

# 13. 정성 평가 기록

## 13.1 성공 사례

| 파일명 | 클래스 | Confidence | IoU | 성공 이유 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

확인할 사례:

- 클래스와 위치가 모두 정확한 결과
- 작은 결함을 성공적으로 찾은 결과
- 한 이미지의 여러 객체를 모두 찾은 결과
- 정상 이미지에서 오탐이 없는 결과

---

## 13.2 오탐 사례

| 파일명 | 예측 클래스 | Confidence | 오탐 유형 | 원인 가설 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

오탐 유형:

```
정상 무늬 오인
클래스 오분류
중복 예측
지나치게 큰 Box
Ground Truth 오류 의심
기타
```

---

## 13.3 미탐 사례

| 파일명 | 실제 클래스 | 객체 크기 | 미탐 유형 | 원인 가설 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

미탐 유형:

```
작은 결함
낮은 대비
흐릿한 경계
학습 데이터 부족
이미지 축소 영향
라벨 문제
기타
```

---

## 13.4 클래스 오류 사례

| 파일명 | 실제 클래스 | 예측 클래스 | Confidence | 원인 가설 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

---

## 13.5 위치 오류 사례

| 파일명 | 클래스 | IoU | 오류 내용 | 원인 가설 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

---

# 14. 데이터·라벨·모델 관점 원인 분석

결과가 좋거나 나쁜 이유를 다음 관점으로 분리한다.

## 데이터 관점

```
클래스별 데이터가 충분한가:
정상·불량 비율은 적절한가:
작은 객체가 충분한가:
촬영 조건이 다양한가:
중복 데이터가 있는가:
Train과 Test 분포가 다른가:
```

## 라벨 관점

```
누락 라벨이 있는가:
클래스 오류가 있는가:
Polygon 경계가 일관적인가:
Bounding Box 변환 시 배경이 과도하게 포함되는가:
작업자별 기준 차이가 있는가:
```

## 모델 관점

```
모델 크기가 충분한가:
입력 해상도가 적절한가:
학습 Epoch가 충분한가:
과적합이 발생했는가:
증강이 적절한가:
Confidence 설정이 적절한가:
```

## 환경 및 구현 관점

```
좌표 변환 오류가 있는가:
클래스 매핑 오류가 있는가:
데이터 분할 오류가 있는가:
모델 파일을 잘못 사용했는가:
추론 설정이 학습 설정과 다른가:
```

---

# 15. Baseline 비교 양식

| 항목 | Baseline | 현재 실험 | 차이 |
| --- | --- | --- | --- |
| Precision |  |  |  |
| Recall |  |  |  |
| mAP50 |  |  |  |
| mAP50-95 |  |  |  |
| Small Recall |  |  |  |
| FP |  |  |  |
| FN |  |  |  |
| 학습 시간 |  |  |  |
| 평균 추론 시간 |  |  |  |
| GPU 메모리 |  |  |  |

## 비교 결과

```
향상된 항목:

저하된 항목:

변화가 거의 없는 항목:

변경 변수의 효과:

가설과 결과 일치 여부:

현재 실험 채택 여부:
```

채택 상태:

```
ADOPT
→ 다음 기준 실험으로 채택

REJECT
→ 기존 Baseline 유지

RETEST
→ 오류 또는 표본 부족으로 재실험

PARTIAL
→ 일부 조건에서만 사용
```

---

# 16. 실행 오류 기록 양식

실험 도중 오류가 발생하면 별도로 기록한다.

```
오류 발생 일시:

실험 ID:

작업 단계:

오류 메시지:

재현 조건:

원인:

해결 방법:

변경된 파일:

결과에 미친 영향:

실험 재실행 여부:

재발 방지 방법:
```

예시 오류:

- CUDA Out of Memory
- 이미지·라벨 개수 불일치
- 클래스 번호 범위 초과
- 잘못된 YAML 경로
- 손상 이미지
- Polygon 좌표 오류
- Batch Size 자동 결정 실패
- 학습 프로세스 중단

오류 해결 과정에서 학습 설정을 변경했다면 기존 실행과 같은 실험으로 취급하지 않고 새 실행 번호를 부여한다.

---

# 17. 실험 결과 결론

```
실험 결과 요약:

가설 검증 결과:

성공 기준 충족 여부:

가장 중요한 발견:

현재 한계:

실제 오토라벨링에 미치는 영향:

결과 채택 여부:
```

결론은 다음처럼 작성한다.

좋지 않은 예:

```
성능이 조금 좋아졌다.
```

권장 예:

```
이미지 크기를 640에서 960으로 높인 결과 Small 객체 Recall이
0.42에서 0.55로 13%p 상승했다.

전체 Precision은 0.76에서 0.74로 2%p 감소하여 사전에 정의한
허용 범위 안에 있었다.

따라서 작은 결함 탐지 개선에는 효과가 있다고 판단한다.
다만 평균 추론 시간이 증가했으므로 MVP 적용 시 처리 속도를 추가로
검증해야 한다.
```

---

# 18. 다음 실험 계획

```
다음 실험 ID:

다음에 해결할 문제:

근거:

다음 가설:

변경할 변수:

변경 전 값:

변경 후 값:

고정할 조건:

성공 판단 기준:

우선순위:
```

다음 실험은 현재 실험 결과에서 직접 이어져야 한다.

---

# 19. 자동 저장용 실험 메타데이터 형식

실험별로 사람이 읽는 Markdown 문서와 기계가 읽는 YAML 또는 JSON을 함께 저장한다.

## YAML 예시

```
experiment:
  id: EXP-P1-DET-001
  name: RT_AL_YOLO26N_640_Baseline
  status: completed
  type: detection_training
  started_at:""
  ended_at:""
  git_commit:""

purpose:
  problem:""
  hypothesis:""
  success_criteria:""

dataset:
  name: ai_hub_welding_rt_al
  version: dataset_v1
  inspection_type: RT
  material: AL
  classes:
    0: porosity
    1: slag_inclusion
  split:
    train: 0.70
    val: 0.15
    test: 0.15
    seed: 42
  image_count:
    train: 0
    val: 0
    test: 0

model:
  library: ultralytics
  task: detect
  weights: yolo26n.pt
  pretrained: true

training:
  epochs: 50
  patience: 15
  imgsz: 640
  requested_batch: -1
  actual_batch: null
  optimizer: auto
  device: auto
  seed: 42
  deterministic: true

inference:
  confidence: 0.25
  iou: 0.70
  imgsz: 640

metrics:
  precision: null
  recall: null
  map50: null
  map50_95: null

artifacts:
  best_model:""
  last_model:""
  results_directory:""
  prediction_json:""
  evaluation_report:""

conclusion:
  hypothesis_result:""
  adopted: false
  next_experiment:""
```

---

# 20. 실험 폴더 구조

```
experiments/
├── EXP-P1-DET-001/
│   ├── experiment.md
│   ├── experiment.yaml
│   ├── train_config.yaml
│   ├── environment.txt
│   ├── dataset_summary.csv
│   ├── class_metrics.csv
│   ├── threshold_comparison.csv
│   ├── logs/
│   ├── models/
│   │   ├── best.pt
│   │   └── last.pt
│   ├── predictions/
│   ├── visualizations/
│   ├── errors/
│   │   ├── false_positive/
│   │   ├── false_negative/
│   │   ├── wrong_class/
│   │   └── localization_error/
│   └── reports/
└── experiment_index.csv
```

실험 폴더 내부 파일을 덮어쓰지 않는다.

재실행할 경우 다음처럼 구분한다.

```
EXP-P1-DET-001-R01
EXP-P1-DET-001-R02
```

설정 변경이 있다면 재실행 번호가 아니라 새로운 실험 ID를 부여한다.

---

# 21. 전체 실험 목록 관리 양식

`experiment_index.csv`에서 모든 실험을 한눈에 비교한다.

| 실험 ID | 실험명 | 변경 변수 | 상태 | Precision | Recall | mAP50 | mAP50-95 | 채택 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EXP-P1-DET-001 | Baseline | 없음 | COMPLETED |  |  |  |  | 기준 |
| EXP-P1-DET-002 | Image 960 | imgsz | PLANNED |  |  |  |  |  |
| EXP-P1-DET-003 | Model Small | model size | PLANNED |  |  |  |  |  |

추가 열 후보:

- 데이터셋 버전
- 모델
- 이미지 크기
- Epoch
- 학습 시간
- Small Recall
- FP
- FN
- 결과 문서 경로

---

# 22. 실험 기록 최소 필수 항목

실험마다 모든 내용을 장문으로 작성하기 어렵다면 아래 항목은 반드시 남긴다.

```
1. 실험 ID와 실험명
2. 실험 목적
3. 기준 실험
4. 변경한 변수 하나
5. 데이터셋 버전과 분할
6. 모델과 학습 설정
7. 실행 환경
8. Precision·Recall·mAP
9. 클래스별 결과
10. 오탐·미탐 주요 사례
11. 결과 해석
12. 채택 여부
13. 다음 실험
```

이 중 하나라도 빠지면 실험 간 정확한 비교가 어려울 수 있다.

---

# 23. Baseline 실험 기록 예시

```
실험 ID:
EXP-P1-DET-001

실험명:
RT_AL_YOLO26N_640_Baseline

실험 목적:
AI-Hub RT·AL 데이터에서 Polygon을 Bounding Box로 변환한 YOLO
Detection 파이프라인이 정상적으로 동작하는지 검증한다.

검증 질문:
새로운 Test 이미지에서 porosity와 slag_inclusion의 클래스와 위치를
예측하고 자동 라벨 파일로 저장할 수 있는가?

기준 실험:
없음

변경 변수:
없음. 최초 Baseline.

데이터:
RT + AL
정상 이미지 포함
porosity, slag_inclusion
약 300장

모델:
YOLO26n Detection

학습 조건:
Epoch 50
Image Size 640
Seed 42
Patience 15
Batch Auto

기준 추론:
Confidence 0.25
NMS IoU 0.70

성공 기준:
학습과 추론이 재현 가능하고 자동 라벨 TXT를 생성할 수 있을 것.
Precision·Recall·mAP와 오탐·미탐을 클래스별로 확인할 수 있을 것.

결과:
실험 후 작성

결론:
실험 후 작성

다음 실험:
Baseline의 가장 큰 실패 원인을 확인한 뒤 결정
```