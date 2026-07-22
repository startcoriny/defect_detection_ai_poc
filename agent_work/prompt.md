# 구현 지시서: 원본 Polygon 시각화

## 배경

`docs/context/02-task-list.md` 작업7(원본 Polygon 시각화)과 `docs/context/03-deliverables.md` 3.4절·6.1절에 따라, 원본 JSON의 Polygon 좌표를 이미지 위에 그려서 라벨 품질을 육안으로 확인할 수 있게 한다.

전체 2,250장을 다 그리는 대신, 클래스별로 정해진 수량만 뽑아 시각화한다. 다만 무작위 표본만으로는 완료 조건에 있는 "여러 객체가 각각 표시된다", "이미지 경계를 벗어난 Polygon을 발견할 수 있다"를 보장할 수 없으므로, 이미 만들어져 있는 `metadata/raw_dataset_inventory.csv`와 `reports/data-quality/warning_files.csv`를 참고해 해당 사례를 표본에 강제로 포함시킨다.

## 기능 및 요구사항

### `src/visualization/visualize_original_polygon.py` (신규)

#### 1. 표본 선정

- 입력: `metadata/raw_dataset_inventory.csv` (재사용 — `image_path`, `json_path`, `status`, `classes`, `num_annotations`, `valid` 컬럼 사용. `classes`는 세미콜론(`;`)으로 구분된 원본 case 값 목록이다).
- `valid == True`인 레코드만 대상으로 한다.
- 클래스별 표본: `status == "normal"` 레코드에서 50장, 그리고 `metadata/class_mapping.json`의 6개 표준 클래스 각각에 대해 — 원본 `classes` 값을 `class_mapping.json`으로 표준명으로 바꿨을 때 그 표준 클래스를 포함하는 레코드 중 50장. 뽑을 때는 `random.Random(42)`로 고정 시드를 사용해 재실행해도 같은 표본이 나오게 한다 (표준 라이브러리 `random`만 사용, 새 패키지 추가 금지).
- 강제 포함 표본(위에서 이미 뽑혔으면 중복 추가하지 않음):
  - `num_annotations`가 가장 큰 레코드 1개 (복수 객체 확인용).
  - `reports/data-quality/warning_files.csv`에서 `warning_codes`에 `out_of_bounds_coordinate` 또는 `negative_coordinate`가 포함된 레코드 전부 (이미지 경계를 벗어난 Polygon 확인용, 이 파일 기준 3~4건).
- 최종 표본 목록(중복 제거 후 image_name 기준 정렬)을 로그로 남긴다 (클래스별/강제포함 몇 장씩 뽑혔는지 포함).

#### 2. 시각화

표본으로 뽑힌 각 이미지에 대해:

- `src/common/image_utils.read_image`로 이미지를 읽는다 (한글 경로 대응, 실패 시 `logging.error`로 남기고 건너뛴다 — 크래시 금지).
- 같은 이미지의 JSON을 `src/common/json_utils.load_json`으로 읽어 `annotations[]`를 순회한다.
- 각 annotation의 Polygon(`coordinate.x`, `coordinate.y` 배열)을 OpenCV로 그린다:
  - 경계선: 채워지지 않은 폴리라인 (`cv2.polylines`).
  - 반투명 내부 영역: 별도 오버레이 이미지에 `cv2.fillPoly`로 채운 뒤 `cv2.addWeighted`로 원본과 합성 (투명도는 상수로 고정, 예: `alpha = 0.3`).
  - `case`가 빈 문자열이면(`정상` annotation) 폴리곤을 그리지 않고 건너뛴다.
  - `class_mapping.json`으로 변환한 표준 클래스명 + 객체 번호(해당 이미지 내 annotation 순번, 0부터)를 폴리곤 근처(첫 좌표 위치)에 `cv2.putText`로 표시한다.
- 이미지 좌상단에 파일명과 `f"{width}x{height}"` 크기를 `cv2.putText`로 표시한다 (`width`/`height`는 JSON의 `image_data`에서 읽는다).
- 결과를 `outputs/original-polygon/{image_name}.jpg`로 저장한다 (`cv2.imwrite`가 한글 경로에서 실패할 수 있으므로 `cv2.imencode` + `Path.write_bytes`로 저장 — `data/raw`의 한글 경로 이슈와 동일한 종류의 문제이니 같은 패턴으로 우회한다).

#### 3. 좌표 검증

폴리곤을 그리기 전, 각 annotation에 대해 아래를 확인하고 위반 시 `logging.warning`으로 남긴다 (`reports/data-quality/`의 검증 결과와 별개로, 이번 시각화 스크립트 자체의 판단):

- 좌표 개수 불일치(`len(x) != len(y)`) — 있으면 해당 annotation은 그리지 않고 건너뛴다.
- 좌표가 이미지 `width`/`height` 범위를 벗어남 — 그리기는 하되(잘리더라도 OpenCV가 처리) 경고 로그를 남긴다.

이 검증에서 발견한 문제를 `outputs/original-polygon/coordinate_check.csv`에 기록한다. 컬럼: `image_name, annotation_index, issue`.

#### 4. 오류 이미지 목록

이미지 읽기 실패, JSON 파싱 실패 등으로 시각화를 건너뛴 이미지를 `outputs/original-polygon/error_files.csv`에 기록한다. 컬럼: `image_name, reason`.

## 구현 범위 (In Scope)

- `src/visualization/visualize_original_polygon.py` 신규 생성
- `outputs/original-polygon/*.jpg`, `coordinate_check.csv`, `error_files.csv`는 스크립트 실행 결과물 — CODEX가 미리 만들지 않는다.
- `src/visualization/__init__.py`가 없다면 함께 생성한다 (다른 `src/*` 하위 패키지와의 일관성 확인 후, 없는 패턴이면 만들지 않아도 됨 — 기존 `src/data/`, `src/validation/` 디렉터리에 `__init__.py`가 있는지 먼저 확인하고 그 관례를 따른다).

## 구현 제외 범위 (Out of Scope)

- `visualize_polygon_box.py`, `visualize_yolo_label.py`, `visualize_prediction.py`, `visualize_evaluation.py` — 이후 작업 범위.
- "작은 결함 이미지", "경계가 복잡한 이미지" 표본을 자동으로 판별하는 로직 — 기하학적 복잡도·면적 계산은 이번 작업 범위가 아니다. 무작위 표본(클래스별 10장, 다수 annotation 존재로 자연히 다양한 크기가 섞임) 안에서 CLAUDE가 육안으로 확인한다.
- 전체 2,250장 시각화 — 위 표본 선정 로직대로만 생성한다.
- `src/common/image_utils.py`의 영문 주석 수정 — 이번 작업과 무관한 기존 파일이므로 손대지 않는다.

## 작업 전 반드시 확인해야 하는 문서

- `docs/context/02-task-list.md` 379~421줄 (작업7: 수행 작업, 최소 확인 대상, 산출물, 완료 조건)
- `docs/context/03-deliverables.md` 315~333줄(3.4 시각화 코드), 680~696줄(6.1 원본 Polygon 시각화)
- `docs/raw_data_structure.md` (JSON 스키마, `coordinate.x`/`y` 형식, `annotations[].case`)
- `metadata/raw_dataset_inventory.csv`, `metadata/class_mapping.json`, `reports/data-quality/warning_files.csv` — 표본 선정에 그대로 재사용
- `src/common/image_utils.py`, `src/common/json_utils.py` — 기존 유틸 재사용

## 완료 기준 (Definition of Done)

- ( ) Polygon이 실제 결함 위치에 표시된다.
- ( ) 클래스명이 올바르게 표시된다.
- ( ) 여러 객체가 각각 표시된 이미지가 최소 1건 포함된다 (`num_annotations` 최댓값 이미지).
- ( ) 이미지 경계를 벗어난 Polygon 사례가 최소 1건 포함된다 (`warning_files.csv`의 `out_of_bounds_coordinate`/`negative_coordinate` 이미지).
- ( ) 정상 이미지, 6개 표준 클래스 이미지가 각각 최소 1장씩 포함된다.
- ( ) 재실행해도 동일한 표본·결과가 나온다 (고정 시드 재현성).
- ( ) 코드가 PEP 8 / black 포맷을 따른다.

## 제약사항

- 표준 라이브러리(`csv`, `json`, `logging`, `random`, `pathlib`) + `opencv-python`, `numpy` + 기존 `src/common/*` 유틸만 사용한다. 새 외부 패키지를 추가하지 않는다.
- `data/raw`, `metadata/`, `reports/` 아래 기존 파일은 읽기만 하고 수정하지 않는다.
- 함수/모듈 주석은 한글로 작성한다 (프로젝트 관례).

## 테스트 방법 및 검증 기준 (CODEX 완료 후 CLAUDE가 이어서 수행)

1. `venv/Scripts/python.exe src/visualization/visualize_original_polygon.py` 실행
2. `outputs/original-polygon/`에 이미지가 생성됐는지, 개수가 로그에 남긴 표본 수와 일치하는지 확인
3. 생성된 이미지 중 정상/6개 클래스/다수 객체/경계 초과 사례를 직접 열어 육안으로 확인 (Polygon 위치, 클래스명 표시, 파일명·크기 표시)
4. `coordinate_check.csv`, `error_files.csv` 내용 확인
5. 재실행 후 표본과 결과가 동일한지 확인
6. `docs/context/02-task-list.md` 작업7 완료 조건 5개 충족 여부 확인
