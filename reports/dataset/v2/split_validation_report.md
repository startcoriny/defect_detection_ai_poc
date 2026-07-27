# 데이터셋 분할 검증 보고서

## 분할 결과

| 분할 | 이미지 수 | 실제 비율 | 목표 비율 |
|---|---:|---:|---:|
| train | 398 | 70.19% | 70% |
| val | 85 | 14.99% | 15% |
| test | 84 | 14.81% | 15% |

## 필수 이미지 포함 검증

| 분할 | 정상 | porosity | slag_inclusion |
|---|---:|---:|---:|
| train | 158 | 157 | 84 |
| val | 34 | 34 | 17 |
| test | 33 | 32 | 19 |

모든 분할에 정상, porosity, slag_inclusion 이미지가 1장 이상 포함되었다.

## 그룹 × 크기 층화 분포

| 분할 | both_mixed | normal | porosity_mixed | porosity_small_dominant | slag_inclusion_mixed | slag_inclusion_small_dominant |
|---|---:|---:|---:|---:|---:|---:|
| train | 1 | 158 | 27 | 129 | 58 | 25 |
| val | 0 | 34 | 6 | 28 | 12 | 5 |
| test | 0 | 33 | 5 | 27 | 13 | 6 |

## 작은 객체 분포

작은 객체는 작업12와 동일하게 `relative_area < 0.01`로 정의했다.

| 분할 | 작은 객체 수 | 전체 객체 수 | 작은 객체 비율 |
|---|---:|---:|---:|
| train | 397 | 548 | 72.45% |
| val | 104 | 141 | 73.76% |
| test | 86 | 123 | 69.92% |

세 분할의 작은 객체 비율 범위는 3.84%p이다(상한 24.0%p 이내).

## 무결성 및 재현성 검증

- 선택 이미지 중 `duplicate == True`: 0건 확인
- Random Seed: 42
- train ∩ val: 0장
- train ∩ test: 0장
- val ∩ test: 0장
- 동일 이미지가 여러 분할에 속하지 않음: 확인(교집합 크기 0)
