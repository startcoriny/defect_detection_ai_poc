# 코드 리뷰: 1차 PoC 데이터 선별 (`src/dataset/select_poc_dataset.py`)

## 요구사항 충족 여부

- RT+AL 637건만 후보로 구성 — 확인
- 그룹 분류 우선순위(누락→품질→중복→대상외혼입→정상/porosity/slag/both→무관) 그대로 구현 — 확인
- `both` 그룹 강제 포함 — 확인
- 그룹별 목표 100장, 고정 시드 재현성 — 확인
- `selected_dataset.csv`(637행) / `included_files.txt` / `excluded_files.txt` 산출 — 확인

## 발견한 문제

없음. Blocker/Major/Minor/Suggestion 전부 해당 사항 없음.

## 실행 결과

```
RT+AL candidates: 637
Group normal: total=225, selected=100, selected_object_count=100
Group porosity: total=222, selected=99, selected_object_count=239
Group slag_inclusion: total=119, selected=99, selected_object_count=197
Group both: total=1, selected=1, selected_object_count=3
Target normal: planned=100, actual=100, difference=+0
Target porosity: planned=100, actual=100, difference=+0
Target slag_inclusion: planned=100, actual=100, difference=+0
Exclusion non_target_class: 68
Exclusion off_target_class_present: 2
Exclusion quota_not_selected: 268
```

- 검증: 100+99+99+1(선택 299) + 68+2+268(제외 338) = 637 — 정확히 일치
- `porosity`/`slag_inclusion` 목표는 `both`의 1장이 두 그룹 모두에 겹쳐 계산되어 실제로 정확히 100씩 달성됨
- `off_target_class_present` 2건 모두 `lack_of_fusion;porosity` 조합으로 확인 (설계 시 예상한 것과 결함 조합은 다르지만 처리 로직은 동일하게 정확히 동작)
- black/ruff 통과, 재실행 2회 비교 결과 동일(재현성 확인)

## 사용자가 직접 확인하는 방법

1. `venv/Scripts/python.exe src/dataset/select_poc_dataset.py` 실행 — 로그 마지막 줄들에서 `planned=100, actual=100, difference=+0`이 3개 클래스 모두 나오는지 확인
2. `metadata/selected_dataset.csv` 행 수 확인 (헤더 포함 638줄이어야 함): `wc -l metadata/selected_dataset.csv`
3. `both` 그룹 확인: `grep ",both," metadata/selected_dataset.csv` → `RT_AL_02_14488682` 1건, `selected=True`
4. 대상외 혼입 제외 확인: `grep "off_target_class_present" metadata/selected_dataset.csv` → 2건
5. `metadata/included_files.txt`(299줄) + `metadata/excluded_files.txt`(338줄) 합이 637인지 확인
6. 재실행 후 세 산출 파일이 동일한지 확인(재현성)
