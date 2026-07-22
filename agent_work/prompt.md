# 구현 지시서: 클래스 분석 및 표준화 (작업 6)

## 배경

`docs/context/02-task-list.md` 작업6(클래스 분석 및 표준화)과 `docs/context/03-deliverables.md` 2.3절·3.2절에 따라, 원본 JSON의 결함 클래스명을 전부 수집하고 표준 클래스명·클래스 번호로 확정한다.

작업3(`docs/raw_data_structure.md`)에서 이미 확인했듯 결함 클래스는 `annotations[].case`에 있고(`class`가 아님), 정상은 `case: ""`다. 작업4(`metadata/raw_dataset_inventory.json`)의 `summary.by_class`를 통해 이미 6개의 서로 다른 원본 클래스 문자열(`crack`, `incomplete penetration`, `lack of fusion`, `porosity`, `slag inclusion`, `undercut`)만 존재하고, 대소문자·오탈자·한영 혼용 변형은 실제로 발견되지 않았다는 것도 알고 있다. 다만 이번 작업의 스크립트는 이 사실을 전제하지 말고 원본 JSON을 **독립적으로 다시 스캔**해서 스스로 검증해야 한다 (사전에 안다고 해서 코드가 하드코딩된 6개 값만 찾도록 짜면 안 된다 — 실제로 변형이 있었다면 놓치게 된다).

## 기능 및 요구사항

### `src/data/analyze_classes.py` (신규)

`data/raw/steel`의 3개 카테고리(`1. RTAL` → `2. RTST` → `3. VTST`, 고정 순서)를 `src/common/file_utils.get_sorted_file_stems`와 `src/common/json_utils.load_json`으로 순회한다 (작업4의 `build_inventory.py`와 같은 순회 패턴, JSON 파싱 실패 시 크래시하지 않고 `logging`으로 파일 경로와 사유를 남기고 건너뛴다).

각 JSON의 `annotations[]`에서 `case`가 빈 문자열이 아닌 값을 **원본 클래스 문자열 그대로** 수집한다 (정규화하지 않은 raw 값). 클래스별로 아래를 집계한다:

- `image_count`: 그 클래스가 1개 이상 등장한 이미지 수
- `object_count`: 그 클래스의 annotation 총 개수
- `rt_image_count` / `vt_image_count`: 위 image_count를 `info.type`(RT/VT) 기준으로 나눈 값 (완료 조건의 "RT·VT 간 동일 이름의 의미" 확인에 참고용으로 쓴다)

### 1. `metadata/original_class_list.csv`

발견된 모든 고유 원본 클래스 문자열 1행씩, `raw_class` 기준 알파벳 정렬. 컬럼: `raw_class, image_count, object_count, rt_image_count, vt_image_count`.

### 2. `metadata/class_mapping.json`

원본 클래스 문자열 → 표준 클래스명(또는 제외 표시)의 **평면(flat) 딕셔너리**. `docs/context/02-task-list.md`에 나온 예시와 같은 형식(`{"원본이름": "표준이름"}`).

표준화 규칙:
- 원본 문자열의 공백을 밑줄로 바꾸고 소문자로 통일한다 (예: `"lack of fusion"` → `"lack_of_fusion"`, `"incomplete penetration"` → `"incomplete_penetration"`, `"slag inclusion"` → `"slag_inclusion"`, `"crack"`→`"crack"`, `"porosity"`→`"porosity"`, `"undercut"`→`"undercut"`).
- 서로 다른 원본 문자열이 표준화 후 같은 이름이 되면(대소문자·공백 차이로 인한 동일 클래스), 하나의 표준 클래스로 합친다 — 즉 `class_mapping.json`의 값 기준으로 그룹핑해서 다음 단계(class_statistics)를 계산해야 한다. 지금 실제 데이터에는 이런 경우가 없을 수 있지만, 코드는 "여러 원본이 같은 표준명으로 매핑될 수 있다"는 전제로 짠다 (원본 1개 = 표준 1개라고 하드코딩하지 않는다).
- `"normal"` 키를 추가하고 값은 `null`로 둔다 — 정상(빈 case)은 YOLO 탐지 클래스가 아니라는 것을 명시적으로 표시한다 (완료 조건 "사용하지 않을 클래스" 대응).
- 이번 실제 데이터에서 그 외에 제외할 클래스는 없어 보이지만, 만약 이미지 수가 극단적으로 적은(예: 특정 임계값 이하) 클래스가 있다면 값으로 `null`을 넣어 제외 대상으로 표시할 수 있다 — 다만 이번 작업에서는 임의로 임계값을 만들어 제외하지 말고, 실제로 발견된 각 클래스의 `image_count`를 로그로 남겨서 사용자가 나중에 판단할 수 있게만 한다.

### 3. `metadata/class_statistics.csv`

`class_mapping.json`에서 값이 `null`이 아닌 표준 클래스명 기준으로 `original_class_list.csv`의 값을 그룹핑(합산)한 결과. 컬럼: `class_id, class_name, image_count, object_count, rt_image_count, vt_image_count`.

- `class_id`는 **표준 클래스명(`class_name`)을 알파벳 순으로 정렬**해서 0부터 고정 배정한다. 이 번호는 이후 모든 작업(YOLO 변환, 학습)에서 동일하게 재사용되는 고정값이므로, 정렬 기준(알파벳 순)을 코드 주석으로 명시한다.
- `image_count`/`object_count`/`rt_image_count`/`vt_image_count`는 같은 표준 클래스로 매핑된 원본 클래스들의 값을 합산한다.

### 4. 로그 출력

실행 시 `logging`으로 아래를 표준출력에 남긴다: 발견된 원본 클래스 개수, 표준 클래스 개수, 클래스별(`class_id: class_name`) `image_count`/`object_count`, 그리고 `rt_image_count`/`vt_image_count`가 둘 다 0보다 큰(RT와 VT 모두에 등장하는) 클래스와 한쪽에서만 등장하는 클래스를 구분해서 표시한다 (완료 조건 "RT·VT 간 동일 이름의 의미" 확인을 사람이 판단할 수 있게 돕는 정보이며, 의미가 같은지 자체를 코드가 판정하지는 않는다).

## 구현 범위 (In Scope)

- `src/data/analyze_classes.py` 신규 생성
- `metadata/original_class_list.csv`, `metadata/class_mapping.json`, `metadata/class_statistics.csv`는 스크립트 실행 결과물 — CODEX가 미리 만들지 않는다.

## 구현 제외 범위 (Out of Scope)

- `src/data/analyze_statistics.py`, `find_duplicates.py` — 이후 작업 범위.
- RT/VT 간 클래스 의미가 실제로 같은지에 대한 최종 판단 — 이건 용접 검사 도메인 지식이 필요한 사람의 판단 영역이다. 스크립트는 참고 통계(4절)만 제공하고 자동으로 결론 내리지 않는다.
- 클래스 제외 여부를 자동으로 결정하는 임계값 로직 — 위 2절에서 설명한 대로, 실제 데이터에 근거 없는 제외 기준을 임의로 만들지 않는다.
- `metadata/raw_dataset_inventory.json`을 입력으로 재사용하지 않는다 — 이번 스크립트는 "원본 JSON에서 클래스명을 직접 수집한다"는 작업6의 요구사항대로 독립적으로 원본을 다시 스캔한다 (작업5가 작업4의 인벤토리를 재사용한 것과 다른 선택이며, 이유는 위 "배경" 문단 참고).

## 작업 전 반드시 확인해야 하는 문서

- `docs/context/02-task-list.md` 327~376줄 (작업6: 수행 작업, 확인할 내용, 산출물, 완료 조건)
- `docs/context/03-deliverables.md` 107~137줄(2.3 클래스 표준화 결과)
- `docs/raw_data_structure.md` 3절(class vs case), `metadata/raw_dataset_inventory.json`의 `summary.by_class` (참고용 — 이미 알려진 값과 대조하되 재사용하지는 않는다)
- `src/data/build_inventory.py`, `src/common/file_utils.py`, `src/common/json_utils.py` — 기존 순회 패턴과 스타일

## 완료 기준 (Definition of Done)

- ( ) 모든 원본 클래스가 표준 클래스 또는 제외 대상(`null`)으로 `class_mapping.json`에 연결된다.
- ( ) `porosity`와 `slag_inclusion`이 서로 다른 클래스 번호로 안정적으로 구분된다.
- ( ) `class_statistics.csv`의 `class_id`가 알파벳 순으로 고정 배정된다.
- ( ) 재실행해도 동일한 `class_mapping.json`/`class_statistics.csv`가 나온다 (재현성).
- ( ) 코드가 PEP 8 / black 포맷을 따른다.

## 제약사항

- 표준 라이브러리(`csv`, `json`, `logging`, `pathlib`) + 이미 있는 `src/common/file_utils.py`, `json_utils.py`만 사용한다. 새 외부 패키지를 추가하지 않는다.
- `data/raw` 아래 원본 파일은 읽기만 하고 수정하지 않는다.
- 카테고리 순회 순서, 클래스 정렬 기준을 고정해 재실행 시 동일한 결과가 나오게 한다.

## 테스트 방법 및 검증 기준 (CODEX 완료 후 CLAUDE가 이어서 수행)

1. `venv/Scripts/python.exe src/data/analyze_classes.py` 실행
2. `metadata/original_class_list.csv`의 클래스별 `image_count`/`object_count`가 `metadata/raw_dataset_inventory.json`의 `summary.by_class`(이미 알려진 값: crack 225/436, incomplete penetration 225/324, lack of fusion 452/680, porosity 452/5179, slag inclusion 226/463, undercut 225/541)와 정확히 일치하는지 대조
3. `class_mapping.json`에 6개 원본 클래스 + `"normal": null`이 들어있는지 확인
4. `class_statistics.csv`의 `class_id`가 알파벳 순(0=crack ... )으로 고정되어 있는지 확인
5. 재실행 후 결과 동일한지 확인
6. `docs/context/02-task-list.md` 작업6 완료 조건 4개 충족 여부 확인
