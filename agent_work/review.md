# 코드 리뷰: Train·Validation·Test 분할 — 그룹×크기 2단계 층화 재작업 (`src/dataset/split_dataset.py`)

## 요구사항 충족 여부

- 이미지별 `size_class`(작업12 기준 `relative_area<0.01` 객체가 절반 이상이면 `small_dominant`) 계산 — 확인
- 층화 키 6개(`normal`, `porosity_mixed`, `porosity_small_dominant`, `slag_inclusion_mixed`, `slag_inclusion_small_dominant`, `both_mixed`), 실제 이미지 수가 사전 계산값(100/22/77/69/30/1)과 정확히 일치 — 확인(코드에도 `EXPECTED_STRATUM_COUNTS`로 하드코딩 검증되어 있어, 값이 달라지면 실행이 실패하도록 방어)
- Seed 42, 알파벳순 층화 키 순회, 반올림 배분(70/15/15) — 확인
- `split_group` 컬럼만 갱신, 다른 컬럼·다른 metadata 파일은 그대로 — 확인
- 분할×표준클래스 6개(`split_distribution.csv` 18행), 검증 보고서(`split_validation_report.md`, 그룹×크기 분포 표 추가됨) 생성 — 확인
- 이전 대비 작은 객체 비율 범위 개선을 보고서에 명시 + **코드 자체가 24.0%p 미만인지 런타임에 검증(위반 시 실행 실패)** — 확인, 지시서 요구보다 한 단계 더 엄격하게 구현됨(단순 보고가 아니라 강제 조건화)

## 발견한 문제

없음. 이전 리뷰에서 발견했던 "작은 객체 비율 불균등" 이슈가 이번 재작업으로 실제 해결되었습니다.

## 실행 결과

```
데이터셋 분할 완료: train 209장, val 44장, test 46장
```

- **작은 객체 비율 범위: 24.0%p → 6.06%p로 개선** (train 62.95%, val 61.22%, test 56.90% — 이전 train 55.80%/val 62.32%/test 79.79%보다 훨씬 균등)
- `splits/{train,val,test}.txt`: 209/44/46, 교집합 전부 0
- `metadata/selected_dataset.csv`: `split_group` 299행 정상 채워짐
- `reports/dataset/split_distribution.csv`: `porosity`/`slag_inclusion` 3개 분할 모두 `image_count > 0`(porosity 70/15/15, slag_inclusion 70/14/16), 객체 수 합계 439와 일치
- `reports/dataset/split_validation_report.md`에 새로 추가된 "그룹 × 크기 층화 분포" 표로 6개 층화 키가 3개 분할에 비례 배분됐음을 확인
- black/ruff 통과, 재실행 결과 `selected_dataset.csv`/`splits/*`/`reports/dataset/split_*` 전부 완전 동일(재현성 확인)

## 사용자가 직접 확인하는 방법

1. `venv/Scripts/python.exe src/dataset/split_dataset.py` 실행 — `train 209장, val 44장, test 46장` 확인(층화 키 수가 예상과 다르면 실행 자체가 실패하도록 되어 있음)
2. `reports/dataset/split_validation_report.md`의 "작은 객체 분포" 표 — 범위가 6.06%p로 이전(24.0%p)보다 줄었는지 확인
3. 같은 보고서의 "그룹 × 크기 층화 분포" 표 — 6개 층화 키가 세 분할에 고르게 나뉘었는지 확인
4. `metadata/selected_dataset.csv`에서 `selected=True` 행의 `split_group`이 전부 채워졌는지 확인
5. `wc -l splits/train.txt splits/val.txt splits/test.txt` → 209/44/46
6. 재실행 후 위 산출물 전부 동일한지 확인

## 결과

완료 조건 6개(동일 이미지 중복 없음, 중복 이미지 없음 확인, 각 분할 정상 이미지 포함, 각 분할 대상 클래스 존재, 재현성, 작은 객체 비율 범위 개선) 모두 충족.
