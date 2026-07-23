# 데이터셋 분할 검증 보고서

## 분할 결과

| 분할 | 이미지 수 | 실제 비율 | 목표 비율 |
|---|---:|---:|---:|
| train | 209 | 69.90% | 70% |
| val | 44 | 14.72% | 15% |
| test | 46 | 15.38% | 15% |

## 필수 이미지 포함 검증

| 분할 | 정상 | porosity | slag_inclusion |
|---|---:|---:|---:|
| train | 70 | 70 | 70 |
| val | 15 | 15 | 14 |
| test | 15 | 15 | 16 |

모든 분할에 정상, porosity, slag_inclusion 이미지가 1장 이상 포함되었다.

## 그룹 × 크기 층화 분포

| 분할 | both_mixed | normal | porosity_mixed | porosity_small_dominant | slag_inclusion_mixed | slag_inclusion_small_dominant |
|---|---:|---:|---:|---:|---:|---:|
| train | 1 | 70 | 15 | 54 | 48 | 21 |
| val | 0 | 15 | 3 | 12 | 10 | 4 |
| test | 0 | 15 | 4 | 11 | 11 | 5 |

## 작은 객체 분포

작은 객체는 작업12와 동일하게 `relative_area < 0.01`로 정의했다.

| 분할 | 작은 객체 수 | 전체 객체 수 | 작은 객체 비율 |
|---|---:|---:|---:|
| train | 209 | 332 | 62.95% |
| val | 30 | 49 | 61.22% |
| test | 33 | 58 | 56.90% |

세 분할의 작은 객체 비율 범위는 6.06%p이다. 이전 group 단독 층화의 train 55.80%, val 62.32%, test 79.79%와 그 범위 24.0%p보다 감소했다.

## 무결성 및 재현성 검증

- 선택 이미지 중 `duplicate == True`: 0건 확인
- Random Seed: 42
- train ∩ val: 0장
- train ∩ test: 0장
- val ∩ test: 0장
- 동일 이미지가 여러 분할에 속하지 않음: 확인(교집합 크기 0)
