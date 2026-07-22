# 구현 지시서: 데이터 품질 검사 (작업 5)

## 배경

`docs/context/02-task-list.md` 작업5(데이터 품질 검사)와 `docs/context/03-deliverables.md` 2.2절·3.3절에 따라, `data/raw/steel` 전체에 대해 이미지·JSON·좌표·연결 4개 영역의 품질 검사를 수행하고 학습 포함/제외 여부를 결정하는 리포트를 생성한다.

이번 작업은 작업4(`metadata/raw_dataset_inventory.json`, 이미 생성됨)를 입력으로 사용한다. 새로 파일 목록을 스캔하지 않고 그 인벤토리를 읽어서 순회한다.

작업3(`docs/raw_data_structure.md`)과 작업2(`docs/data-inventory.md` 8절)에서 이미 확인한 사실을 그대로 신뢰한다:
- 결함 클래스는 `annotations[].case`에 있다 (`class`는 `"normal"`/`"defect"` 두 값뿐).
- `cv2.imread()`는 이 데이터의 한글 경로를 열지 못한다 (Windows + OpenCV 유니코드 경로 이슈). 반드시 `np.fromfile(path, dtype=np.uint8)` + `cv2.imdecode(...)`로 읽어야 한다.
- Polygon 좌표는 `{"x": [...], "y": [...]}` 형태의 분리된 배열이다.

## 기능 및 요구사항

### 1. `src/common/image_utils.py` (신규)

- 한글 경로에서도 안전하게 이미지를 읽는 함수 하나. `np.fromfile` + `cv2.imdecode(cv2.IMREAD_COLOR)`를 사용한다.
- 파일이 없거나 디코딩에 실패하면 예외를 던지지 않고 `None`을 반환한다 (호출자가 "손상/읽기 실패"로 판단할 수 있게).
- 성공하면 디코딩된 배열(`numpy.ndarray`)을 반환한다. 실제 width/height는 호출자가 `array.shape`에서 뽑는다 (`shape[1]`=width, `shape[0]`=height).

### 2. `src/validation/validate_image.py` (신규)

이미지 1개에 대해 검사하고 이슈 목록을 반환하는 함수.

입력: 이미지 경로, JSON에서 읽은 기대 width/height.

검사 및 등급:
- 이미지 파일 없음 → `ERROR`, 코드 `image_missing`
- 존재하지만 `image_utils`로 디코딩 실패(손상) → `ERROR`, 코드 `image_corrupted`
- 디코딩된 width 또는 height가 0 이하 → `ERROR`, 코드 `invalid_image_dimensions`
- 디코딩된 실제 (width, height)가 JSON의 (width, height)와 다름 → `WARNING`, 코드 `dimension_mismatch`

### 3. `src/validation/validate_json.py` (신규)

JSON 1개를 읽고 파싱 + 구조 검증해서 `(파싱된 dict 또는 None, 이슈 목록)`을 반환하는 함수.

검사 및 등급:
- JSON 파일 없음 → `ERROR`, 코드 `json_missing`
- JSON 파싱 실패(문법 오류 등) → `ERROR`, 코드 `json_parse_failed`
- `info`/`image_data`/`meta`/`annotations` 중 하나라도 없음 → `ERROR`, 코드 `missing_required_fields`
- `annotations`의 원소 중 `tool`/`coordinate`/`class`/`case` 키가 없거나 `coordinate`에 `x`/`y`가 없는 경우 → `ERROR`, 코드 `invalid_annotation_structure`
- `annotations[].class == "defect"`인데 해당 `annotations[].case`가 빈 문자열인 경우 (결함인데 클래스명이 없음) → `ERROR`, 코드 `missing_class_info`

구조가 위 필수 형태를 만족하지 못하면 이후 좌표 검사는 건너뛴다 (해당 항목에 대해 좌표 검사를 시도하지 않는다).

### 4. `src/validation/validate_polygon.py` (신규)

두 가지 함수:

**(a) 폴리곤 1개 검사** — 입력: `coordinate`(`{"x": [...], "y": [...]}`), 이미지 width/height.

- `x`, `y` 배열 길이가 다름 → `ERROR`, 코드 `coordinate_count_mismatch`
- 점 개수(=len(x), x/y 길이가 같다는 전제하에)가 0 → `ERROR`, 코드 `empty_polygon`
- 점 개수가 1개 이상 3개 미만 → `ERROR`, 코드 `insufficient_points`
- `x`/`y` 값 중 `int`/`float`가 아닌 값이 있음 → `ERROR`, 코드 `non_numeric_coordinate` (이 경우 아래 수치 비교 검사는 생략)
- 좌표 중 음수가 있음 → `WARNING`, 코드 `negative_coordinate`
- 좌표 중 이미지 width/height를 넘는 값이 있음 → `WARNING`, 코드 `out_of_bounds_coordinate`
- 폴리곤 변끼리 자기 교차 가능성이 있음 (인접하지 않은 두 변이 교차하는 경우, 표준 CCW 기반 선분 교차 판정으로 확인) → `INFO`, 코드 `possible_self_intersection`

**(b) 한 이미지 안에서 중복 Annotation 검사** — 입력: 그 이미지의 `annotations` 리스트. 두 개 이상의 annotation이 `x`, `y` 좌표 리스트가 완전히 동일하면 → `WARNING`, 코드 `duplicate_annotation` (해당 이미지 레코드에 1회만 추가하면 된다, annotation마다 반복 추가하지 않는다).

### 5. `src/validation/validate_image_label_pair.py` (신규, 실행 진입점)

`python src/validation/validate_image_label_pair.py`로 실행하는 메인 스크립트.

절차:
1. `metadata/raw_dataset_inventory.json`을 읽는다. 없으면 "먼저 `python src/data/build_inventory.py`를 실행하라"는 메시지와 함께 오류 종료한다 (에러 코드 1).
2. 인벤토리의 각 레코드(`image_name`, `image_path`, `json_path`, `image_exists`, `json_exists` 등)를 순회하며:
   - `validate_json`으로 JSON을 다시 읽고 검증한다 (인벤토리의 `parse_success`를 그대로 신뢰하지 않고 다시 검증한다 — 이번 작업은 더 깊은 구조 검사를 하기 때문).
   - JSON이 정상 파싱됐으면 `image_data.width`/`height`를 기대값으로 `validate_image`를 실행한다. JSON이 없거나 파싱 실패했으면 기대 width/height 없이 이미지 존재 여부만 확인한다.
   - JSON이 정상 파싱됐으면 각 `annotations[]`에 대해 `validate_polygon`의 (a)를 실행하고, 이미지 전체에 대해 (b) 중복 Annotation 검사를 1회 실행한다.
   - 모든 이슈를 이미지 단위로 모은다.
3. 전체 레코드를 다 돈 뒤, 아래 두 가지 **레코드 간(cross-record) 검사**를 추가로 수행하고 관련된 모든 레코드에 이슈를 추가한다.
   - 동일한 `image_name`이 카테고리(RTAL/RTST/VTST)를 넘어 2번 이상 나오면 → `WARNING`, 코드 `duplicate_filename` (관련된 모든 레코드에 추가)
   - 이미지 파일 내용이 동일한 경우(파일 바이트의 `hashlib.sha256` 해시가 같은 이미지가 2개 이상) → `WARNING`, 코드 `duplicate_image` (관련된 모든 레코드에 추가). 이미지가 없는 레코드는 해시 계산에서 제외한다.
4. 레코드별로 `error_count`/`warning_count`/`info_count`를 집계하고 `include = (error_count == 0)`을 결정한다.
5. `reports/data-quality/` 아래에 4개 파일을 생성한다 (없으면 폴더 자동 생성).

## 출력 파일 스키마

공통 코드 등급 고정 어휘 (다른 이름을 만들지 않는다):

- ERROR: `image_missing`, `json_missing`, `image_corrupted`, `invalid_image_dimensions`, `json_parse_failed`, `missing_required_fields`, `invalid_annotation_structure`, `missing_class_info`, `coordinate_count_mismatch`, `insufficient_points`, `empty_polygon`, `non_numeric_coordinate`
- WARNING: `dimension_mismatch`, `negative_coordinate`, `out_of_bounds_coordinate`, `duplicate_filename`, `duplicate_image`, `duplicate_annotation`
- INFO: `possible_self_intersection`

**`reports/data-quality/data_quality_report.csv`** — 전체 레코드 1행씩. 컬럼: `image_name, image_path, json_path, error_codes, warning_codes, info_codes, error_count, warning_count, info_count, include` (코드가 여러 개면 세미콜론 `;`으로 join, 없으면 빈 문자열).

**`reports/data-quality/error_files.csv`** — `error_count > 0`인 행만. 컬럼: `image_name, image_path, json_path, error_codes`.

**`reports/data-quality/warning_files.csv`** — `error_count == 0` 이고 `warning_count > 0`인 행만. 컬럼: `image_name, image_path, json_path, warning_codes`.

**`reports/data-quality/excluded_files.csv`** — `include == False`인 행만 (= `error_files.csv`와 대상이 같다). 컬럼: `image_name, image_path, json_path, exclusion_reason` (`exclusion_reason`은 `error_codes`와 동일한 값).

실행 중 오류 유형별 집계(각 코드별 발생 건수)를 `logging`으로 표준출력에 요약 출력한다 (파일로 별도 저장하지 않아도 된다 — 완료 조건의 "오류 유형별 통계"는 이 로그 출력으로 충분하다).

## 구현 범위 (In Scope)

- `src/common/image_utils.py`
- `src/validation/validate_image.py`
- `src/validation/validate_json.py`
- `src/validation/validate_polygon.py`
- `src/validation/validate_image_label_pair.py` (실행 진입점)
- `reports/data-quality/` 아래 4개 CSV는 스크립트 실행 결과물이며 CODEX가 미리 만들지 않는다.

## 구현 제외 범위 (Out of Scope)

- `src/validation/validate_yolo_dataset.py` — YOLO 변환 이후(작업이 훨씬 뒤) 사용할 검증이며 이번 작업 범위가 아니다.
- `src/data/analyze_classes.py`, `analyze_statistics.py`, `find_duplicates.py` — 작업6 이후 범위. 단, "중복 파일명"/"중복 이미지"는 `docs/context/02-task-list.md` 작업5의 "연결 검사" 항목에 명시되어 있으므로 이번 `validate_image_label_pair.py`에서 다룬다(위 5절 참고). 별도의 정교한 지각적(perceptual) 중복 이미지 탐지는 하지 않는다 — 파일 바이트 해시가 완전히 같은 경우만 "중복 이미지"로 본다.
- `metadata/raw_dataset_inventory.json`을 다시 스캔하거나 재생성하지 않는다 — 있는 그대로 입력으로만 읽는다.
- `data/raw/mvtec_anomaly_detection` — 이번 작업도 작업4와 동일하게 AI-Hub steel 데이터만 대상으로 한다.
- 실제로 파일을 학습셋에서 물리적으로 삭제/이동하는 동작 — 이번 작업은 "제외 대상 목록"을 만드는 것까지이며, 실제 분할/제외 반영은 이후 작업(작업7 이후)의 몫이다.

## 작업 전 반드시 확인해야 하는 문서

- `docs/context/02-task-list.md` 260~324줄 (작업5: 수행 작업 4개 영역, 오류 등급, 산출물, 완료 조건)
- `docs/context/03-deliverables.md` 68~104줄(2.2 데이터 품질 검사 결과), 294~311줄(3.3 데이터 검증 코드)
- `docs/raw_data_structure.md`, `docs/data-inventory.md` 8절
- `metadata/raw_dataset_inventory.json`의 실제 필드 구성 (작업4 결과물, 이번 작업의 입력)
- `src/data/build_inventory.py`, `src/common/file_utils.py`, `src/common/json_utils.py` — 기존 코드 스타일과 `PROJECT_ROOT` 계산 패턴(`Path(__file__).resolve().parent.parent.parent`, `src/validation/`도 동일 깊이) 참고

## 완료 기준 (Definition of Done)

- ( ) 손상 이미지를 찾을 수 있다 (`image_corrupted`).
- ( ) 이미지·JSON 누락을 찾을 수 있다 (`image_missing`/`json_missing`).
- ( ) 잘못된 좌표를 찾을 수 있다 (`coordinate_count_mismatch`/`insufficient_points`/`empty_polygon`/`non_numeric_coordinate`/`negative_coordinate`/`out_of_bounds_coordinate`).
- ( ) 학습 제외 대상을 구분할 수 있다 (`include` 컬럼, `excluded_files.csv`).
- ( ) 오류 원인이 파일 단위로 기록된다 (`data_quality_report.csv`의 `error_codes`/`warning_codes`/`info_codes`).
- ( ) 코드가 PEP 8 / black 포맷을 따른다.

## 제약사항

- 표준 라이브러리(`csv`, `json`, `logging`, `hashlib`, `pathlib`) + 이미 설치된 `numpy`, `opencv-python`(`cv2`)만 사용한다. 새 외부 패키지(예: shapely)를 추가하지 않는다.
- `data/raw` 아래 원본 파일은 읽기만 하고 절대 수정하지 않는다.
- 카테고리·레코드 순회 순서를 고정해 재실행 시 같은 결과가 나오게 한다 (인벤토리 JSON의 `records` 순서를 그대로 따르면 된다).
- 이미지 하나당 디코딩은 1회만 한다 (검사마다 다시 읽지 않는다).

## 테스트 방법 및 검증 기준 (CODEX 완료 후 CLAUDE가 이어서 수행)

1. `venv/Scripts/python.exe src/validation/validate_image_label_pair.py` 실행
2. `reports/data-quality/` 아래 4개 CSV 생성 확인, 행 수와 합계(`error_count`/`warning_count` 합)가 로그 요약과 일치하는지 확인
3. 재실행 후 결과가 동일한지 확인 (재현성)
4. `docs/context/02-task-list.md` 작업5 완료 조건 5개 충족 여부 확인
