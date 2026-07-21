## 1. 산출물 목적

1단계 PoC가 끝났다고 판단하려면 단순히 모델 파일 하나만 존재해서는 안 된다.

다음 결과가 모두 남아 있어야 한다.

```
원본 데이터 분석 결과
→ 검증된 변환 코드
→ 재현 가능한 학습 데이터셋
→ 학습된 Baseline 모델
→ 추론 및 자동 라벨 결과
→ 성능 평가
→ 실패 사례 분석
→ 다음 단계 판단 문서
```

산출물은 크게 다음 여섯 종류로 구분한다.

1. 데이터 산출물
2. 코드 산출물
3. 설정 및 환경 산출물
4. 모델·실험 산출물
5. 평가 및 시각화 산출물
6. 최종 문서 산출물

---

# 2. 데이터 산출물

## 2.1 원본 데이터 인벤토리

전체 AI-Hub 원본 데이터를 분석한 목록이다.

### 포함 정보

- 이미지 파일명
- 이미지 경로
- JSON 라벨 경로
- 검사 유형
- 소재
- 이미지 Width·Height
- 정상·불량 여부
- 포함된 결함 클래스
- Annotation 개수
- 클래스별 객체 수
- 이미지·라벨 연결 상태
- 파싱 성공 여부
- 데이터 품질 상태

### 파일 예시

```
metadata/
├── raw_dataset_inventory.csv
└── raw_dataset_inventory.json
```

### 완료 기준

- `( )` 전체 대상 데이터를 빠짐없이 순회했다.
- `( )` 이미지와 JSON 연결 상태를 확인할 수 있다.
- `( )` 검사 유형·소재·클래스별 통계를 생성할 수 있다.
- `( )` 오류 데이터가 별도로 표시된다.

---

## 2.2 데이터 품질 검사 결과

학습에 사용할 수 없는 데이터와 검토가 필요한 데이터를 구분한 결과다.

### 포함 오류

- 이미지 파일 없음
- JSON 파일 없음
- 손상 이미지
- JSON 파싱 실패
- 필수 필드 누락
- 클래스 정보 누락
- Polygon 점 개수 부족
- x·y 좌표 개수 불일치
- 음수 좌표
- 이미지 범위 초과 좌표
- 중복 이미지
- 중복 Annotation
- 실제 이미지 크기와 JSON 크기 불일치

### 파일 예시

```
reports/data-quality/
├── data_quality_report.csv
├── error_files.csv
├── warning_files.csv
└── excluded_files.csv
```

### 완료 기준

- `( )` 오류 유형과 파일명을 확인할 수 있다.
- `( )` 학습 포함·제외 여부가 결정되어 있다.
- `( )` 제외 사유가 기록되어 있다.
- `( )` 치명적 오류가 학습 데이터에 남아 있지 않다.

---

## 2.3 클래스 표준화 결과

원본 클래스명을 프로젝트 표준 클래스명으로 연결한 결과다.

### 파일 예시

```
metadata/
├── original_class_list.csv
├── class_mapping.json
└── class_statistics.csv
```

### 예시

```
{
  "기공":"porosity",
  "porosity":"porosity",
  "슬래그혼입":"slag_inclusion",
  "slag inclusion":"slag_inclusion"
}
```

### 완료 기준

- `( )` 모든 원본 클래스명이 표준 클래스 또는 제외 대상으로 연결된다.
- `( )` 클래스 번호가 고정된다.
- `( )` Train·Validation·Test에서 동일한 매핑을 사용한다.
- `( )` 표준화되지 않은 클래스가 남아 있지 않다.

---

## 2.4 1차 PoC 선정 데이터 목록

1차 실험에 실제로 포함된 데이터 목록이다.

### 포함 정보

- 이미지 파일명
- 정상·불량 상태
- 대상 클래스
- 객체 수
- 선정 여부
- 제외 사유
- 분할 그룹 ID
- 중복 여부
- 데이터 품질 상태

### 파일 예시

```
metadata/
├── selected_dataset.csv
├── included_files.txt
└── excluded_files.txt
```

### 완료 기준

- `( )` RT·AL 데이터만 포함된다.
- `( )` `porosity`, `slag_inclusion`만 사용한다.
- `( )` 정상 이미지가 포함된다.
- `( )` 대상 외 결함이 섞인 이미지 처리 기준이 적용된다.
- `( )` 실제 이미지·객체 수가 기록된다.

---

## 2.5 변환된 YOLO Detection 데이터셋

AI-Hub Polygon을 Bounding Box로 변환하여 만든 학습 데이터셋이다.

### 구조

```
data/processed/dataset_v1/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
├── labels/
│   ├── train/
│   ├── val/
│   └── test/
└── data.yaml
```

### 포함 항목

- 원본 이미지
- YOLO Detection TXT
- 정상 이미지용 빈 라벨
- 클래스 정보
- Train·Validation·Test 분할
- 데이터셋 버전

### 완료 기준

- `( )` 이미지와 라벨 파일명이 일치한다.
- `( )` 모든 좌표가 `0~1` 범위다.
- `( )` 클래스 번호가 정의 범위 안에 있다.
- `( )` 객체 수와 클래스가 원본 Annotation과 일치한다.
- `( )` 동일한 분할을 재생성할 수 있다.
- `( )` 데이터셋 검증을 통과했다.

---

## 2.6 데이터셋 통계 자료

### 포함 통계

- 전체 이미지 수
- 정상 이미지 수
- 불량 이미지 수
- 클래스별 이미지 수
- 클래스별 객체 수
- 이미지당 객체 수
- 객체 크기 분포
- 이미지 해상도 분포
- 복수 객체 이미지 수
- Train·Validation·Test별 분포

### 파일 예시

```
reports/dataset/
├── dataset_summary.csv
├── class_distribution.csv
├── object_size_distribution.csv
└── split_distribution.csv
```

### 완료 기준

- `( )` 이미지 수와 객체 수를 구분하여 볼 수 있다.
- `( )` 클래스 불균형 여부를 판단할 수 있다.
- `( )` 작은 결함의 비율을 확인할 수 있다.
- `( )` 분할별 클래스 누락 여부를 확인할 수 있다.

---

# 3. 코드 산출물

## 3.1 환경 및 공통 코드

```
src/
├── check_environment.py
└── common/
    ├── file_utils.py
    ├── image_utils.py
    ├── json_utils.py
    └── logging_utils.py
```

### 역할

- 실행 환경 확인
- 파일 목록 조회
- 이미지 읽기
- JSON 읽기
- 공통 로그 처리
- 출력 폴더 생성

---

## 3.2 데이터 분석 코드

```
src/data/
├── analyze_raw_structure.py
├── build_inventory.py
├── analyze_classes.py
├── analyze_statistics.py
└── find_duplicates.py
```

### 역할

- 원본 구조 분석
- 데이터 인벤토리 생성
- 클래스 목록 및 분포 확인
- 이미지·객체 통계 생성
- 중복 이미지 탐지

---

## 3.3 데이터 검증 코드

```
src/validation/
├── validate_image.py
├── validate_json.py
├── validate_polygon.py
├── validate_image_label_pair.py
└── validate_yolo_dataset.py
```

### 역할

- 이미지 손상 확인
- JSON 필드 확인
- Polygon 좌표 검증
- 이미지·JSON 연결 검사
- 변환된 YOLO 데이터셋 최종 검사

---

## 3.4 시각화 코드

```
src/visualization/
├── visualize_original_polygon.py
├── visualize_polygon_box.py
├── visualize_yolo_label.py
├── visualize_prediction.py
└── visualize_evaluation.py
```

### 역할

- 원본 Polygon 표시
- Polygon·Bounding Box 비교
- YOLO 라벨 복원
- Prediction 표시
- TP·FP·FN 시각화

---

## 3.5 변환 코드

```
src/conversion/
├── normalize_class_name.py
├── polygon_to_box.py
├── box_to_yolo.py
├── convert_aihub_to_yolo.py
└── write_yolo_label.py
```

### 역할

- 클래스 표준화
- Polygon → Bounding Box
- 픽셀 좌표 → YOLO 정규화 좌표
- AI-Hub JSON → YOLO 데이터셋
- TXT 라벨 생성

---

## 3.6 데이터 분할 코드

```
src/dataset/
├── select_poc_dataset.py
├── split_dataset.py
├── build_yolo_dataset.py
└── verify_split.py
```

### 역할

- PoC 대상 데이터 선별
- Train·Validation·Test 분할
- YOLO 폴더 구조 생성
- 분할 간 중복과 클래스 분포 검사

---

## 3.7 학습 및 추론 코드

```
src/model/
├── smoke_test.py
├── train_baseline.py
├── run_inference.py
├── export_auto_labels.py
└── compare_thresholds.py
```

### 역할

- 짧은 학습 실행 검증
- Baseline 학습
- Test 추론
- Prediction을 자동 라벨로 변환
- Confidence Threshold 비교

---

## 3.8 평가 코드

```
src/evaluation/
├── calculate_iou.py
├── match_predictions.py
├── calculate_metrics.py
├── analyze_class_metrics.py
├── analyze_object_sizes.py
└── collect_error_cases.py
```

### 역할

- IoU 계산
- Ground Truth·Prediction 매칭
- TP·FP·FN 계산
- 클래스별 성능 분석
- 객체 크기별 분석
- 오탐·미탐 수집

---

## 3.9 코드 완료 기준

- `( )` 실행 파일별 역할이 명확하다.
- `( )` 경로가 코드 내부에 무분별하게 하드코딩되지 않는다.
- `( )` 입력·출력 위치를 설정으로 변경할 수 있다.
- `( )` 오류 발생 시 파일명과 원인이 기록된다.
- `( )` 같은 입력과 설정으로 결과를 재생성할 수 있다.
- `( )` 원본 데이터는 코드 실행으로 수정되지 않는다.

---

# 4. 설정 및 환경 산출물

## 4.1 패키지 목록

```
requirements.txt
```

또는:

```
pyproject.toml
```

### 포함 항목

- Python 패키지
- 사용 버전
- 학습 라이브러리
- 이미지 처리 라이브러리
- 데이터 처리 라이브러리

---

## 4.2 실행 환경 정보

```
configs/environment/
├── environment_info.txt
└── package_versions.txt
```

### 포함 정보

- OS
- CPU
- RAM
- GPU
- VRAM
- Python
- PyTorch
- CUDA
- Ultralytics
- OpenCV
- NumPy

---

## 4.3 클래스 설정

```
configs/class_mapping.json
```

예시:

```
{
  "0":"porosity",
  "1":"slag_inclusion"
}
```

---

## 4.4 데이터셋 설정

```
configs/data.yaml
```

### 포함 정보

- Dataset 경로
- Train 경로
- Validation 경로
- Test 경로
- 클래스 ID와 이름

---

## 4.5 학습 설정

```
configs/train_baseline.yaml
```

### 포함 정보

- 모델
- Epoch
- Patience
- Image Size
- Batch Size
- Device
- Seed
- Optimizer
- 증강 정책

---

## 4.6 추론 설정

```
configs/inference_baseline.yaml
```

### 포함 정보

- 모델 경로
- Image Size
- Confidence Threshold
- NMS IoU Threshold
- 결과 저장 위치
- 자동 라벨 출력 여부

---

## 4.7 설정 완료 기준

- `( )` 코드 수정 없이 주요 설정을 변경할 수 있다.
- `( )` Baseline 설정이 파일로 고정되어 있다.
- `( )` 실행 환경을 다시 구성할 수 있다.
- `( )` 학습과 추론에서 사용한 실제값이 기록된다.
- `( )` 자동 Batch Size가 결정한 실제값도 남아 있다.

---

# 5. 모델 및 실험 산출물

## 5.1 Smoke Test 결과

```
experiments/EXP-P1-DET-SMOKE-001/
```

### 포함 파일

- Smoke Test 설정
- 실행 로그
- 임시 모델
- 추론 결과 이미지
- 성공·실패 결과
- 오류 해결 기록

### 완료 기준

- `( )` 데이터셋을 정상적으로 읽었다.
- `( )` 1~3 Epoch 학습이 종료됐다.
- `( )` 모델 파일이 생성됐다.
- `( )` 생성 모델로 추론할 수 있다.

---

## 5.2 Baseline 실험 결과

```
experiments/EXP-P1-DET-001/
```

### 포함 파일

```
experiment.md
experiment.yaml
train_config.yaml
environment.txt
dataset_summary.csv
logs/
models/
reports/
visualizations/
```

### 모델 파일

```
models/
├── best.pt
└── last.pt
```

### 완료 기준

- `( )` Baseline 학습이 정상 종료됐다.
- `( )` `best.pt`와 `last.pt`가 생성됐다.
- `( )` 실제 학습 설정이 보존됐다.
- `( )` 학습 로그와 그래프를 확인할 수 있다.
- `( )` 실험 ID와 결과 폴더가 연결되어 있다.

---

## 5.3 추론 결과

```
predictions/
├── prediction_results.json
├── labels/
└── images/
```

### JSON 포함 정보

- 원본 이미지명
- 모델 버전
- 클래스 ID
- 클래스명
- Confidence
- Bounding Box
- 정규화 좌표
- 추론 시간
- 추론 설정

### 완료 기준

- `( )` 모든 Test 이미지의 처리 결과가 남아 있다.
- `( )` 예측이 없는 정상 이미지도 결과가 기록된다.
- `( )` 실패한 이미지가 별도로 기록된다.
- `( )` 모델과 설정을 추적할 수 있다.

---

## 5.4 자동 라벨 결과

```
auto-labels/
├── yolo-labels/
├── prediction-metadata/
└── cvat-import/
```

### 포함 내용

- YOLO Detection TXT
- Confidence가 포함된 JSON
- 모델 버전
- 자동 라벨 생성 시간
- Confidence Threshold
- CVAT Import용 파일

### 완료 기준

- `( )` Prediction을 YOLO TXT로 저장할 수 있다.
- `( )` Confidence와 모델 정보가 별도로 보존된다.
- `( )` 저장한 라벨을 다시 시각화할 수 있다.
- `( )` CVAT에서 Import 가능한지 검증했다.

---

# 6. 평가 및 시각화 산출물

## 6.1 원본 Polygon 시각화

```
outputs/original-polygon/
```

필수 사례:

- 정상 이미지
- 기공 이미지
- 슬래그 혼입 이미지
- 복수 객체 이미지
- 작은 결함 이미지
- 경계가 복잡한 이미지

---

## 6.2 Polygon·Bounding Box 비교

```
outputs/polygon-box-comparison/
```

### 확인 목적

- 결함이 Box 내부에 포함되는지
- 배경이 얼마나 함께 포함되는지
- 가늘거나 불규칙한 결함에서 정보 손실이 얼마나 생기는지

---

## 6.3 YOLO 라벨 재시각화

```
outputs/yolo-label-visualization/
```

### 확인 목적

- 정규화 좌표 변환이 올바른지
- 클래스 ID가 올바른지
- 객체 수가 유지되는지
- 이미지와 TXT가 제대로 연결되는지

---

## 6.4 모델 예측 시각화

```
outputs/predictions/
```

### 표시 정보

- Bounding Box
- 클래스명
- Confidence
- 모델 버전
- 파일명

---

## 6.5 평가 시각화

```
outputs/evaluation/
├── true-positive/
├── false-positive/
├── false-negative/
├── wrong-class/
└── localization-error/
```

### 완료 기준

- `( )` TP·FP·FN을 이미지에서 구분할 수 있다.
- `( )` 오탐과 미탐 사례가 각각 보존된다.
- `( )` 클래스 오류와 위치 오류가 분리된다.
- `( )` 실패 원인을 육안으로 검토할 수 있다.

---

## 6.6 성능 지표 파일

```
reports/evaluation/
├── overall_metrics.csv
├── class_metrics.csv
├── object_size_metrics.csv
├── confidence_comparison.csv
└── confusion_matrix.png
```

### 필수 지표

- Precision
- Recall
- mAP50
- mAP50-95
- 클래스별 Precision
- 클래스별 Recall
- 클래스별 AP
- TP
- FP
- FN
- 객체 크기별 Recall

---

# 7. 문서 산출물

## 7.1 데이터 구조 분석 문서

파일:

```
docs/01_raw_data_structure.md
```

### 포함 내용

- AI-Hub 데이터 출처
- 데이터 디렉터리 구조
- 이미지와 JSON 연결 방법
- 주요 JSON 필드
- Polygon 좌표 구조
- 정상·불량 데이터 구조 차이
- 다중 객체 저장 방식

---

## 7.2 데이터 품질 보고서

파일:

```
docs/02_data_quality_report.md
```

### 포함 내용

- 전체 데이터 수
- 검사 성공·실패 수
- 오류 유형
- 제외 데이터
- Warning 데이터
- 원본 데이터 한계
- 품질 개선 필요 사항

---

## 7.3 클래스 정의서

파일:

```
docs/03_class_definition.md
```

### 포함 내용

- 원본 클래스명
- 표준 클래스명
- 영문명
- 클래스 ID
- 결함 설명
- 유사 클래스
- 대상 포함 여부
- 제외 이유

---

## 7.4 데이터 변환 설계서

파일:

```
docs/04_data_conversion.md
```

### 포함 내용

- AI-Hub JSON 파싱
- Polygon 좌표 추출
- Polygon → Bounding Box 계산
- YOLO 좌표 정규화
- 정상 이미지 처리
- 클래스 매핑
- 오류 처리
- 변환 검증 방법

---

## 7.5 데이터셋 구성 보고서

파일:

```
docs/05_dataset_preparation.md
```

### 포함 내용

- PoC 데이터 선정 기준
- 선정 데이터 수
- 제외 기준
- 클래스 분포
- 객체 수
- 객체 크기 분포
- Train·Validation·Test 분할
- Random Seed
- 데이터 누수 검사

---

## 7.6 Baseline 실험 보고서

파일:

```
docs/06_baseline_experiment.md
```

### 포함 내용

- 실험 ID
- 실험 목적
- 데이터셋 버전
- 모델
- 학습 조건
- 실행 환경
- 학습 결과
- best Epoch
- 학습 시간
- 과적합·과소적합 분석
- 주요 결과

---

## 7.7 모델 평가 보고서

파일:

```
docs/07_model_evaluation.md
```

### 포함 내용

- 전체 지표
- 클래스별 지표
- Confusion Matrix
- 객체 크기별 성능
- Confidence Threshold 비교
- 성공 사례
- 성능 해석

---

## 7.8 오탐·미탐 분석 보고서

파일:

```
docs/08_error_analysis.md
```

### 포함 내용

- 오탐 유형
- 미탐 유형
- 클래스 오류
- 위치 오류
- 데이터 관점 원인
- 라벨 관점 원인
- 모델 관점 원인
- 개선 후보

---

## 7.9 자동 라벨 검증 보고서

파일:

```
docs/09_auto_label_validation.md
```

### 포함 내용

- Prediction → YOLO TXT 변환
- 재시각화 검증
- 모델·Confidence 메타데이터
- CVAT Import 결과
- 작업자가 수정 가능한지
- 자동 라벨 품질
- 수동 라벨링 대비 차이

---

## 7.10 다음 실험 계획서

파일:

```
docs/10_next_experiment_plan.md
```

### 포함 내용

- Baseline의 가장 큰 문제
- 근거 지표
- 원인 가설
- 변경할 변수 하나
- 고정 조건
- 성공 판단 기준
- 후속 실험 우선순위

---

## 7.11 PoC 최종 결과 보고서

파일:

```
docs/11_poc_final_report.md
```

### 포함 내용

```
1. PoC 배경
2. PoC 목적
3. 실험 범위
4. 사용 데이터
5. 데이터 분석 결과
6. 데이터 품질 결과
7. 라벨 변환 방식
8. 데이터셋 구성
9. 모델 및 학습 조건
10. 추론 결과
11. 자동 라벨 생성 결과
12. 성능 평가
13. 오탐·미탐 분석
14. 현재 한계
15. 개선 방향
16. MVP 진입 판단
```

---

# 8. 실행 및 재현 문서

## 8.1 README

파일:

```
README.md
```

### 포함 내용

- 프로젝트 설명
- 폴더 구조
- 환경 설치
- 데이터 준비
- 분석 실행
- 변환 실행
- 학습 실행
- 추론 실행
- 평가 실행
- 결과 위치
- 주의사항

---

## 8.2 실행 명령 정리

파일:

```
docs/commands.md
```

예시:

```
환경 확인
→ python src/check_environment.py

데이터 인벤토리 생성
→ python src/data/build_inventory.py

데이터 변환
→ python src/conversion/convert_aihub_to_yolo.py

Baseline 학습
→ python src/model/train_baseline.py

Test 추론
→ python src/model/run_inference.py

성능 평가
→ python src/evaluation/calculate_metrics.py
```

---

## 8.3 재현성 체크리스트

파일:

```
docs/reproducibility_checklist.md
```

### 확인 항목

- Git Commit
- 패키지 버전
- 데이터셋 버전
- 클래스 매핑
- 분할 파일
- Random Seed
- 모델 가중치
- 학습 설정
- 추론 설정
- 평가 설정

### 완료 기준

- `( )` 다른 환경에서 설치 순서를 확인할 수 있다.
- `( )` 같은 데이터와 설정으로 학습을 다시 실행할 수 있다.
- `( )` 사용한 모델과 결과 파일을 추적할 수 있다.
- `( )` Baseline 실험을 재현할 수 있다.

---

# 9. 권장 최종 프로젝트 구조

```
auto-labeling-poc/
├── README.md
├── requirements.txt
├── configs/
│   ├── class_mapping.json
│   ├── data.yaml
│   ├── train_baseline.yaml
│   ├── inference_baseline.yaml
│   └── environment/
├── data/
│   ├── raw/
│   ├── work/
│   └── processed/
│       └── dataset_v1/
├── metadata/
│   ├── raw_dataset_inventory.csv
│   ├── selected_dataset.csv
│   └── class_statistics.csv
├── src/
│   ├── data/
│   ├── validation/
│   ├── conversion/
│   ├── visualization/
│   ├── dataset/
│   ├── model/
│   ├── evaluation/
│   └── common/
├── experiments/
│   ├── EXP-P1-DET-SMOKE-001/
│   └── EXP-P1-DET-001/
├── models/
├── predictions/
├── auto-labels/
├── outputs/
│   ├── original-polygon/
│   ├── polygon-box-comparison/
│   ├── yolo-label-visualization/
│   ├── predictions/
│   └── evaluation/
├── reports/
│   ├── data-quality/
│   ├── dataset/
│   └── evaluation/
├── docs/
└── tests/
```

---

# 10. 필수 산출물과 선택 산출물 구분

## 필수 산출물

1단계 완료를 위해 반드시 필요하다.

- `( )` 데이터 인벤토리
- `( )` 데이터 품질 검사 결과
- `( )` 클래스 매핑 파일
- `( )` PoC 선정 데이터 목록
- `( )` 변환된 YOLO Detection 데이터셋
- `( )` Train·Validation·Test 분할
- `( )` 데이터 변환 코드
- `( )` 데이터 검증 코드
- `( )` Baseline 학습 코드
- `( )` 추론 코드
- `( )` 자동 라벨 생성 코드
- `( )` 성능 평가 코드
- `( )` Baseline `best.pt`
- `( )` Baseline 실험 기록
- `( )` 예측 결과 JSON
- `( )` 자동 라벨 TXT
- `( )` Polygon·Box·Prediction 시각화
- `( )` 전체 및 클래스별 성능 지표
- `( )` 오탐·미탐 사례
- `( )` PoC 최종 결과 보고서
- `( )` 다음 실험 계획서
- `( )` README 및 실행 방법

## 선택 산출물

시간과 필요에 따라 추가한다.

- `( )` 간단한 CLI
- `( )` HTML 형식 결과 리포트
- `( )` 모델 추론 시간 그래프
- `( )` GPU 자원 사용 그래프
- `( )` 데이터 통계 대시보드
- `( )` Docker 실행 환경
- `( )` 간단한 테스트용 API
- `( )` Segmentation 변환 샘플
- `( )` MVTec AD 데이터 구조 비교

선택 산출물이 없어도 1단계 PoC 완료에는 영향을 주지 않는다.

---

# 11. PoC 산출물 완료 판정

다음 질문에 모두 `예`라고 답할 수 있어야 한다.

## 데이터

- `( )` 어떤 데이터를 사용했는지 목록이 남아 있는가?
- `( )` 제외한 데이터와 이유를 확인할 수 있는가?
- `( )` 데이터 품질 문제가 기록되어 있는가?
- `( )` 클래스 매핑과 데이터 분할을 재현할 수 있는가?

## 코드

- `( )` 원본 데이터를 YOLO로 다시 변환할 수 있는가?
- `( )` 변환 결과를 자동 검증할 수 있는가?
- `( )` 학습·추론·평가를 다시 실행할 수 있는가?
- `( )` 자동 라벨을 다시 생성할 수 있는가?

## 모델

- `( )` Baseline 모델과 학습 설정이 보존되어 있는가?
- `( )` 어떤 데이터셋 버전으로 학습했는지 알 수 있는가?
- `( )` `best.pt`와 `last.pt`를 구분할 수 있는가?

## 평가

- `( )` 전체 및 클래스별 성능을 확인할 수 있는가?
- `( )` 오탐과 미탐 사례가 이미지로 남아 있는가?
- `( )` Confidence Threshold에 따른 차이를 확인할 수 있는가?
- `( )` 모델의 주요 한계를 설명할 수 있는가?

## 오토라벨링

- `( )` Prediction을 YOLO 자동 라벨로 저장할 수 있는가?
- `( )` 자동 라벨을 다시 시각화할 수 있는가?
- `( )` CVAT에서 검수 가능한 형식인지 확인했는가?
- `( )` 사람이 수정해야 하는 주요 오류를 파악했는가?

## 문서

- `( )` 다른 사람이 실행 과정을 이해할 수 있는가?
- `( )` 동일한 실험을 다시 수행할 수 있는가?
- `( )` 현재 PoC의 성공과 한계가 명확한가?
- `( )` 다음 실험 또는 MVP 진입 여부를 판단할 수 있는가?