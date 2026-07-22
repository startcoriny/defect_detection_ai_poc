# 구현 지시서: 1차 PoC 데이터 선별

## 배경

`docs/context/02-task-list.md` 작업8(1차 PoC 데이터 선별)과 `docs/context/03-deliverables.md` 2.4절에 따라, RT·AL 데이터 중 정상/`porosity`/`slag_inclusion` 이미지를 각각 약 100장씩 선별한다.

이미 계산해 둔 실제 후보 수(재사용할 `metadata/raw_dataset_inventory.csv`, `metadata/class_mapping.json`, `reports/data-quality/data_quality_report.csv` 기준):

- RT+AL 전체: 637장 (전부 `valid==True`, 전부 품질검사 `include==True` — 이 두 필터로 걸러지는 이미지는 이번 데이터셋엔 없지만 코드는 일반적으로 처리해야 함)
- 정상: 225장
- `porosity`만 있음: 222장
- `slag_inclusion`만 있음: 119장
- `porosity`와 `slag_inclusion`이 둘 다 있고 다른 클래스는 없음: 1장 (`복수 클래스 이미지 처리` 대상)
- 대상 클래스(`porosity`/`slag_inclusion`) + 대상 외 클래스가 섞임: 2장 (`crack`+`porosity` 등 — 1차 PoC에서는 제외 대상)
- 그 외 대상 외 클래스만 있음(`crack`만 38장, `lack_of_fusion`만 30장 등): 68장 (대상과 무관해 제외)

## 기능 및 요구사항

### `src/dataset/select_poc_dataset.py` (신규)

#### 1. 후보 구성

- `metadata/raw_dataset_inventory.csv`에서 `inspection_type == "RT"` 그리고 `material == "AL"`인 레코드만 후보로 삼는다 (그 외 레코드는 애초에 후보 목록에도 넣지 않는다 — VT/ST 데이터까지 나열해 표를 부풀리지 않는다).
- 각 후보의 원본 `classes`(세미콜론 구분)를 `metadata/class_mapping.json`으로 표준 클래스 집합으로 바꾼다(`normal`은 매핑값이 `null`이라 제외됨 — 정상 이미지의 클래스 집합은 빈 집합이 된다).
- `reports/data-quality/data_quality_report.csv`를 `image_name` 기준으로 조인해 `include` 컬럼(품질검사 통과 여부)과 `warning_codes`(중복 탐지용, `duplicate_filename`/`duplicate_image` 포함 여부)를 가져온다.

#### 2. 그룹 분류와 제외 사유

각 후보를 아래 우선순위로 하나의 상태로 분류한다 (먼저 해당하는 조건 하나만 적용):

1. `valid != True` → `exclusion_reason = "image_or_json_missing"`
2. `include != True` (품질검사 미통과) → `exclusion_reason = "quality_check_failed"`
3. `warning_codes`에 `duplicate_filename` 또는 `duplicate_image`가 있음 → `exclusion_reason = "duplicate"`
4. 표준 클래스 집합이 `{"porosity", "slag_inclusion"}`의 부분집합이 아니면서(즉 대상 외 클래스가 하나라도 섞여 있으면서) `porosity`/`slag_inclusion` 중 하나라도 포함 → `exclusion_reason = "off_target_class_present"` (완료 조건의 "대상 외 결함이 섞인 데이터 처리 기준" — 1차 PoC에서는 제외하는 쪽으로 처리)
5. `status == "normal"` → `group = "normal"`
6. 표준 클래스 집합이 `{"porosity"}` → `group = "porosity"`
7. 표준 클래스 집합이 `{"slag_inclusion"}` → `group = "slag_inclusion"`
8. 표준 클래스 집합이 `{"porosity", "slag_inclusion"}` (둘 다, 다른 클래스 없음) → `group = "both"`
9. 그 외(대상 클래스가 전혀 없는 다른 단일/복합 결함) → `exclusion_reason = "non_target_class"`

1~4, 9번에 해당하면 `selected = False`로 확정하고 아래 5번 표본 추출 대상에서 제외한다.

#### 3. 표본 추출 (그룹 5~8에 해당하는, 아직 `exclusion_reason`이 없는 후보만 대상)

- `TARGET_COUNT = 100` (상수로 선언).
- `random.Random(42)`로 고정 시드 사용.
- `both` 그룹(1장)은 항상 선택한다(`selected = True`) — "복수 클래스 이미지도 포함할 수 있다"는 요구사항을 실제로 확인 가능하게 만들기 위해 강제 포함한다.
- `normal` 그룹: `image_name` 기준 정렬 후 `min(TARGET_COUNT, len(그룹))`개를 무작위 추출해 `selected = True`, 나머지는 `selected = False`, `exclusion_reason = "quota_not_selected"`.
- `porosity` 그룹: `both`가 이미 1장을 채우므로 `porosity`(순수) 그룹에서 `min(TARGET_COUNT - 1, len(그룹))`개를 무작위 추출해 `selected = True`, 나머지는 `quota_not_selected`.
- `slag_inclusion` 그룹도 동일하게 `min(TARGET_COUNT - 1, len(그룹))`개 추출.
- 선택 안 된 나머지(그룹 5~8 중 표본에서 빠진 것)는 `selected = False`, `exclusion_reason = "quota_not_selected"`.

#### 4. 산출물

`metadata/selected_dataset.csv` (전체 RT+AL 후보 637건, 선택/제외 모두 포함), 컬럼:

```
image_name, status, classes, object_count, group, selected, exclusion_reason, duplicate, quality_status, split_group
```

- `classes`: 표준 클래스 세미콜론 join (정상이면 빈 문자열)
- `object_count`: `raw_dataset_inventory.csv`의 `num_annotations` 그대로
- `group`: 위 2절에서 정한 그룹(`normal`/`porosity`/`slag_inclusion`/`both`/`excluded`) — 제외 사유가 있으면 `"excluded"`
- `duplicate`: `True`/`False`
- `quality_status`: `include` 값을 그대로 `"pass"`/`"fail"` 문자열로
- `split_group`: 항상 빈 문자열(추후 `split_dataset.py`가 채울 자리, 이번 작업 범위 아님)

`metadata/included_files.txt`: `selected == True`인 `image_name`을 한 줄에 하나씩, 정렬해서.

`metadata/excluded_files.txt`: `selected == False`인 후보를 `image_name,exclusion_reason` 형식으로 한 줄에 하나씩(헤더 없이), `image_name` 기준 정렬.

#### 5. 로그 출력

`logging`으로 아래를 남긴다: 후보 총원(637), 그룹별 전체 인원과 선택된 인원(`normal`/`porosity`/`slag_inclusion`/`both`), 그룹별 계획 수량(100) 대비 실제 선택 수량 차이, `exclusion_reason`별 건수, 선택된 이미지들의 그룹별 `object_count` 합계(클래스별 이미지·객체 수 요구사항).

## 구현 범위 (In Scope)

- `src/dataset/select_poc_dataset.py` 신규 생성
- `metadata/selected_dataset.csv`, `metadata/included_files.txt`, `metadata/excluded_files.txt`는 스크립트 실행 결과물 — CODEX가 미리 만들지 않는다.

## 구현 제외 범위 (Out of Scope)

- `split_dataset.py`, `build_yolo_dataset.py`, `verify_split.py` — 이후 작업 범위.
- `split_group` 값 실제 배정 — 이번 작업은 컬럼만 만들고 빈 값으로 둔다.
- VT/ST 데이터에 대한 어떤 처리도 하지 않는다 (후보 목록 자체가 RT+AL로 한정됨).
- `reports/dataset/` 아래 통계 파일(`dataset_summary.csv` 등) — 이후 작업(데이터셋 통계) 범위.

## 작업 전 반드시 확인해야 하는 문서

- `docs/context/02-task-list.md` 424~490줄 (작업8: 수행 작업, 복수 클래스 이미지 처리, 산출물, 완료 조건)
- `docs/context/03-deliverables.md` 140~172줄(2.4 1차 PoC 선정 데이터 목록)
- `metadata/raw_dataset_inventory.csv`, `metadata/class_mapping.json`, `reports/data-quality/data_quality_report.csv` — 그대로 재사용(재스캔하지 않음)

## 완료 기준 (Definition of Done)

- ( ) `metadata/selected_dataset.csv`에 RT·AL 데이터만 포함된다(637행).
- ( ) `selected == True`인 행은 `porosity`/`slag_inclusion`만 대상 클래스로 갖거나 정상이다.
- ( ) 대상 외 결함이 섞인 데이터가 `off_target_class_present` 사유로 제외 처리된다(2건).
- ( ) 정상·`porosity`·`slag_inclusion` 이미지가 각각 선별된다.
- ( ) 그룹별 계획 수량(100)과 실제 선택 수량의 차이가 로그와 `selected_dataset.csv`로 확인 가능하다.
- ( ) 재실행해도 동일한 선택 결과가 나온다(고정 시드 재현성).
- ( ) 코드가 PEP 8 / black 포맷을 따른다.

## 제약사항

- 표준 라이브러리(`csv`, `json`, `logging`, `random`, `pathlib`) 외 새 패키지를 추가하지 않는다.
- `metadata/raw_dataset_inventory.csv`, `class_mapping.json`, `reports/data-quality/data_quality_report.csv`를 그대로 재사용하고 원본 JSON을 다시 스캔하지 않는다.
- 함수/모듈 주석은 한글로 작성한다(프로젝트 관례).

## 테스트 방법 및 검증 기준 (CODEX 완료 후 CLAUDE가 이어서 수행)

1. `venv/Scripts/python.exe src/dataset/select_poc_dataset.py` 실행
2. `metadata/selected_dataset.csv` 총 행 수가 637인지, `selected_dataset.csv`의 그룹별 `selected==True` 건수가 로그와 일치하는지 확인
3. `both` 그룹(1건)이 항상 `selected==True`인지 확인
4. `off_target_class_present` 사유 건수가 2건인지 확인
5. `included_files.txt`/`excluded_files.txt` 줄 수 합이 637인지 확인
6. 재실행 후 선택 결과 동일한지 확인
7. `docs/context/02-task-list.md` 작업8 완료 조건 5개 충족 여부 확인
