# 구현 지시서: 데이터 인벤토리 생성 (작업 4)

## 배경

`docs/context/02-task-list.md` 작업4(데이터 인벤토리 생성)와 `docs/context/03-deliverables.md` 2.1절·3.2절에 따라, `data/raw/steel` 전체를 순회하며 이미지·JSON 라벨의 연결 상태와 기본 정보를 집계하는 인벤토리 스크립트를 작성한다.

작업3(`docs/raw_data_structure.md`)에서 이미 아래 JSON 구조를 확인했다 — 이 구조를 그대로 신뢰하고 파싱하면 된다.

```json
{
  "info": { "id": 14483434, "type": "RT", "material": "AL" },
  "image_data": { "file_name": "RT_AL_00_14483434", "format": "jpg", "width": 3457, "height": 943 },
  "meta": { "is_crowd": 0, "annotation_case": ["normal"], "total_case": ["normal"] },
  "annotations": [
    { "tool": "polygon", "coordinate": { "x": [...], "y": [...] }, "class": "normal", "case": "" }
  ]
}
```

**중요**: 결함 클래스는 `annotations[].class`가 아니라 `annotations[].case`에 있다 (`class`는 `"normal"`/`"defect"` 두 값뿐). 정상 이미지도 `annotations`가 1개 존재하며 `case: ""`다. (`docs/raw_data_structure.md` 3·4절 참고)

## 기능 및 요구사항

### 1. `src/common/file_utils.py` (신규)

- 디렉터리 안의 특정 확장자 파일들의 stem(확장자 제외 파일명) 목록을 정렬된 상태로 반환하는 함수.
- 빌드 인벤토리에서 이미지 폴더와 JSON 폴더 각각에 대해 재사용한다.

### 2. `src/common/json_utils.py` (신규)

- JSON 파일을 읽어 파싱하는 함수. 파싱 실패 시 예외를 삼키지 않고 호출자가 실패 사실과 원인을 알 수 있도록 한다 (예: 결과와 예외를 함께 반환하거나 호출자가 try/except로 감싸기 쉬운 형태).

### 3. `src/data/build_inventory.py` (신규)

`data/raw/steel/01.원천데이터`와 `data/raw/steel/02.라벨링데이터` 아래 3개 카테고리(`1. RTAL`, `2. RTST`, `3. VTST`, 이 순서 고정)를 순회한다.

각 카테고리에서 이미지 stem 목록과 JSON stem 목록의 **합집합**을 정렬된 순서로 순회하며, stem마다 아래 필드를 갖는 레코드 1개를 만든다 (이미지만 있고 JSON이 없는 경우, 그 반대 경우도 레코드로 남겨서 누락을 검출한다).

| 필드 | 내용 |
| --- | --- |
| `image_id` | JSON `info.id` (파싱 실패/JSON 없음이면 빈 값) |
| `image_name` | stem |
| `image_path` | 이미지 파일의 프로젝트 루트 기준 상대경로 (슬래시 `/` 사용, 없으면 빈 문자열) |
| `json_path` | JSON 파일의 프로젝트 루트 기준 상대경로 (없으면 빈 문자열) |
| `image_exists` | bool |
| `json_exists` | bool |
| `parse_success` | JSON이 존재하고 `info`/`image_data`/`meta`/`annotations` 키를 모두 포함해 정상 파싱됐으면 true |
| `inspection_type` | JSON `info.type` (파싱 실패 시 빈 문자열) |
| `material` | JSON `info.material` (파싱 실패 시 빈 문자열) |
| `width`, `height` | JSON `image_data.width`/`height` (파싱 실패 시 빈 값) |
| `status` | `meta.annotation_case == ["normal"]`이면 `"normal"`, 그 외 결함 케이스가 있으면 `"defect"`, 파싱 실패면 빈 문자열 |
| `classes` | `annotations[].case` 중 빈 문자열이 아닌 값들의 중복 제거 목록을 세미콜론(`;`)으로 join (없으면 빈 문자열) |
| `num_annotations` | `len(annotations)` (파싱 실패 시 0) |
| `valid` | `image_exists and json_exists and parse_success` |

파싱 실패나 파일 누락이 발생하면 `logging` 모듈(표준 라이브러리)로 파일 경로와 사유를 남긴다 (조용히 넘어가지 않는다 — `CLAUDE.md` Error Handling 원칙).

### 4. 집계 요약 (완료 조건의 "클래스별 이미지 수와 객체 수를 집계할 수 있다"에 대응)

`valid=true`인 레코드만 대상으로 아래 요약을 계산한다.

- `total_images`: 이미지 파일이 존재하는 레코드 수
- `by_inspection_type`: `{"RT": n, "VT": n}`
- `by_material`: `{"AL": n, "ST": n}`
- `by_class`: 결함 클래스별로 `{"image_count": 그 클래스를 포함한 이미지 수, "object_count": 그 클래스의 annotation 총 개수}` (정상은 제외)
- `invalid_count`: `valid=false`인 레코드 수, 그리고 사유별 세부 카운트(`image_missing`, `json_missing`, `parse_failed`)

### 5. 출력 파일

- `metadata/raw_dataset_inventory.csv` — 레코드를 위 필드 순서(`image_id, image_name, image_path, json_path, image_exists, json_exists, parse_success, inspection_type, material, width, height, status, classes, num_annotations, valid`) 그대로 담은 표. UTF-8 인코딩.
- `metadata/raw_dataset_inventory.json` — `{"summary": {...위 4번 내용...}, "records": [...위 필드 그대로...]}` 구조. UTF-8, 한글 없이 전부 영문 필드이므로 `ensure_ascii` 여부는 상관없다.
- `metadata/` 폴더가 없으면 자동 생성한다.

스크립트는 `python src/data/build_inventory.py` (인자 없이) 실행 가능해야 한다. `PROJECT_ROOT`는 `Path(__file__).resolve().parent.parent.parent`로 이 파일 안에서 독립적으로 계산한다.

## 구현 범위 (In Scope)

- `src/common/file_utils.py`, `src/common/json_utils.py` 신규 생성
- `src/data/build_inventory.py` 신규 생성
- `metadata/raw_dataset_inventory.csv`, `metadata/raw_dataset_inventory.json`은 스크립트가 실행될 때 생성하는 결과물 — 이 파일들 자체를 CODEX가 미리 손으로 만들지 않는다 (아래 "제외 범위" 참고).

## 구현 제외 범위 (Out of Scope)

- `src/common/image_utils.py`, `src/common/logging_utils.py` — 이번 작업은 이미지를 실제로 디코딩하지 않고 존재 여부만 확인하므로 image_utils가 필요 없고, logging은 표준 `logging` 모듈을 `build_inventory.py`에서 직접 설정해서 쓰면 충분하다 (아직 로깅 설정을 공유해야 할 스크립트가 하나뿐). 두 번째 스크립트가 로깅 설정을 공유해야 하는 시점에 다시 판단한다.
- `data/raw/mvtec_anomaly_detection` 스캔 — 이 작업은 `docs/context/03-deliverables.md` 2.1절이 명시한 "AI-Hub 원본 데이터" 인벤토리이며, MVTec AD는 완전히 다른 라벨 형식(폴리곤 JSON이 아니라 PNG 마스크)이라 이번 스크립트 범위가 아니다.
- 이미지 손상 여부, OpenCV 실제 읽기 가능 여부, Polygon 좌표 유효성(좌표 개수 불일치·범위 초과 등), 중복 이미지 탐지 — 전부 작업5(데이터 품질 검사)의 범위이며 이번 작업에서 다루지 않는다. 이번 작업은 파일 존재 여부와 JSON 파싱 성공 여부까지만 확인한다.
- `analyze_classes.py`, `analyze_statistics.py`, `find_duplicates.py` — `docs/context/02-task-list.md`의 이후 작업(작업5 이후) 범위이며 이번에 만들지 않는다.

## 작업 전 반드시 확인해야 하는 문서

- `docs/context/02-task-list.md` 210~257줄 (작업4: 수집 항목, 결과 예시, 산출물, 완료 조건)
- `docs/context/03-deliverables.md` 29~66줄(2.1 원본 데이터 인벤토리), 273~291줄(3.2 데이터 분석 코드)
- `docs/raw_data_structure.md` — JSON 필드 구조, 특히 3절(class vs case 주의사항)과 4절(정상 이미지 구조)
- `docs/data-inventory.md` 8절 — `cv2.imread`가 한글 경로를 못 여는 이슈 (이번 작업은 이미지를 디코딩하지 않으므로 직접 해당하지는 않지만, 혹시 파일 존재 확인에 `pathlib.Path.exists()`를 쓰면 문제 없음 — `cv2` 관련 함수를 쓰지 않도록 주의)
- `src/check_environment.py` — 기존 코드 스타일(주석, 함수 분리, PROJECT_ROOT 계산 패턴) 참고

## 완료 기준 (Definition of Done)

- ( ) 3개 카테고리(RTAL/RTST/VTST) 전체를 빠짐없이 순회하고 중단 없이 끝난다.
- ( ) 이미지만 있고 JSON이 없는 경우, JSON만 있고 이미지가 없는 경우 모두 레코드로 남아 `valid=false`로 표시된다.
- ( ) `metadata/raw_dataset_inventory.csv`와 `.json`이 지정된 필드/구조로 생성된다.
- ( ) `by_class`에 클래스별 `image_count`와 `object_count`가 모두 들어있다.
- ( ) 파싱 실패나 파일 누락 시 `logging`으로 파일 경로와 사유가 기록된다.
- ( ) 동일한 데이터로 다시 실행하면 행 순서와 값이 동일하다 (정렬 기준 고정).
- ( ) 코드가 PEP 8 / black 포맷을 따른다.

## 제약사항

- 표준 라이브러리 + 이미 설치된 패키지(요청 시 `requirements.txt` 참고, 이번 작업엔 표준 라이브러리인 `csv`/`json`/`logging`/`pathlib`만 있으면 충분하며 새 외부 패키지를 추가하지 않는다)만 사용한다.
- `data/raw` 아래 원본 파일은 읽기만 하고 절대 수정하지 않는다.
- 카테고리 순회 순서(`1. RTAL` → `2. RTST` → `3. VTST`)와 각 카테고리 내 stem 정렬 순서를 고정해 재실행 시 동일한 결과가 나오게 한다.

## 테스트 방법 및 검증 기준 (CODEX 완료 후 CLAUDE가 이어서 수행)

1. `venv/Scripts/python.exe src/data/build_inventory.py` 실행
2. `metadata/raw_dataset_inventory.csv`, `.json` 생성 확인, 행 수가 이미지/JSON 합집합 개수와 일치하는지 확인
3. `by_class`, `by_inspection_type`, `by_material` 합계가 `docs/raw_data_structure.md`에 이미 기록된 전수 분포(예: normal 450, lack of fusion 449, porosity 447, crack 225 등)와 일치하는지 대조
4. 재실행 후 결과가 동일한지 확인 (재현성)
5. `docs/context/02-task-list.md` 작업4 완료 조건 5개 충족 여부 확인
