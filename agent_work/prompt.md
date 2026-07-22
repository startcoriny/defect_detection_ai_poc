# 구현 지시서: Bounding Box를 YOLO Detection 라벨로 변환

## 배경

`docs/context/02-task-list.md` 작업10(YOLO Detection 라벨 생성)과 `docs/context/03-deliverables.md` 3.5절(`box_to_yolo.py`/`write_yolo_label.py` 역할)에 따라, 작업9에서 생성한 픽셀 좌표 Bounding Box(`metadata/bbox_annotations.csv`)를 YOLO Detection TXT 라벨로 변환한다.

**대상 범위**: 작업8에서 선별한 `metadata/selected_dataset.csv`의 `selected == True` 이미지 299장 전체(정상 이미지 포함). 이미지·JSON 파일을 다시 열 필요는 없다 — `metadata/bbox_annotations.csv`에 이미 픽셀 좌표와 `image_width`/`image_height`가 들어있으므로 이 CSV만으로 변환한다.

**참고**: `docs/context/02-task-list.md` 574번째 줄의 완료 조건 "클래스 번호가 `0` 또는 `1`이다"는 이 프로젝트의 6개 표준 클래스(작업6, `class_id` 0~5) 체계와 맞지 않는 문서상 예시 문구다. `docs/context/03-deliverables.md` 2.5절의 "클래스 번호가 정의 범위 안에 있다"를 실제 완료 조건으로 따른다(아래 완료 기준에 반영).

## 기능 및 요구사항

### `src/conversion/box_to_yolo.py` (신규)

#### 1. 입력

- `metadata/selected_dataset.csv`에서 `selected == "True"`인 `image_name` 299건을 대상 목록으로 읽는다.
- `metadata/bbox_annotations.csv`를 읽어 `image_name` 기준으로 그룹핑한다(정상 이미지는 이 CSV에 행이 없음 — 작업9 결과, 이번 작업 범위에서 재검증하지 않는다).
- `metadata/class_statistics.csv`를 읽어 `class_id` 오름차순으로 정렬된 클래스 목록을 만든다(0~5, 6개 전부 — 이번 선별 데이터에는 `porosity`/`slag_inclusion`만 등장하지만 클래스 목록 파일은 프로젝트 전체 표준 클래스 6개를 그대로 담는다).

#### 2. 픽셀 좌표 → YOLO 정규화 좌표 변환

`bbox_annotations.csv`의 각 행(`x_min, y_min, x_max, y_max, image_width, image_height, class_id`)마다:

```
center_x = (x_min + x_max) / 2 / image_width
center_y = (y_min + y_max) / 2 / image_height
box_width = (x_max - x_min) / image_width
box_height = (y_max - y_min) / image_height
```

한 줄 형식: `f"{class_id} {center_x:.6f} {center_y:.6f} {box_width:.6f} {box_height:.6f}"`

- 계산된 4개 정규화 값이 모두 `0.0 이상 1.0 이하` 범위인지 확인한다. 벗어나면 작업9의 클리핑이 깨진 것이므로(정상적으로는 발생 불가) `ValueError`를 발생시켜 실패로 처리한다(조용히 무시하지 않는다).

#### 3. 이미지별 TXT 라벨 생성

- 선별된 299개 `image_name` 전체에 대해 `{image_name}.txt` 파일을 만든다.
- 해당 이미지에 `bbox_annotations.csv` 행이 있으면 객체당 한 줄씩 기록(순서는 `annotation_index` 오름차순).
- 해당 이미지에 행이 없으면(정상 이미지) **빈 파일**을 만든다.
- 저장 위치: `outputs/yolo_labels/{image_name}.txt` (작업7·9와 동일하게 `outputs/`는 재생성 가능한 산출물 디렉터리).
- 파일 인코딩: UTF-8, 줄바꿈 `\n`, 마지막 줄 개행 포함.

#### 4. 클래스 매핑 파일

- `metadata/yolo_classes.txt` 생성: `class_id` 오름차순으로 한 줄에 클래스명 하나씩(YOLO/Ultralytics 관례상 줄 번호 = `class_id`).

#### 5. 로그 출력

`logging`으로 다음을 남긴다:

- 대상 이미지 수(299)
- 생성된 라벨 파일 수(299 — 정상 이미지 포함 전부)
- 빈 라벨(정상 이미지) 수
- 객체가 있는 라벨 파일 수
- 전체 객체 수(YOLO 라인 총수, 작업9의 439와 일치해야 함)
- 클래스별 객체 수

## 구현 범위 (In Scope)

- `src/conversion/box_to_yolo.py` 신규 생성
- `metadata/yolo_classes.txt`, `outputs/yolo_labels/*.txt`는 스크립트 실행 결과물 — CODEX가 미리 만들지 않는다.

## 구현 제외 범위 (Out of Scope)

- `convert_aihub_to_yolo.py`, `write_yolo_label.py`를 별도 파일로 분리하는 것 — 작업7·9와 동일하게 한 작업은 한 스크립트로 구현하는 기존 관례를 따른다(파일을 나누지 않는다).
- `split_dataset.py`, `build_yolo_dataset.py` — Train/Validation/Test 분할과 `data/processed/dataset_v1/` 폴더 구조 생성은 작업13·작업14 범위다. 이번 작업은 분할 없이 299장 전체를 대상으로 라벨만 생성한다.
- `validate_yolo_dataset.py`(작업10 산출물 최종 검사) — 작업15 범위.
- 이미지 파일 복사/이동 — 이번 작업은 라벨 텍스트 파일만 생성한다.

## 작업 전 반드시 확인해야 하는 문서

- `docs/context/02-task-list.md` 536~578줄(작업10: 수행 작업, 파일 규칙, 산출물, 완료 조건)
- `docs/context/03-deliverables.md` 175~211줄(2.5 변환된 YOLO Detection 데이터셋), 336~354줄(3.5 변환 코드)
- `metadata/bbox_annotations.csv`, `metadata/selected_dataset.csv`, `metadata/class_statistics.csv` — 그대로 재사용
- `src/conversion/polygon_to_box.py` — CSV 로딩/조인 패턴 재사용

## 완료 기준 (Definition of Done)

- ( ) 모든 좌표가 `0~1` 범위다.
- ( ) 클래스 번호가 정의된 범위(0~5) 안에 있다.
- ( ) 객체당 한 줄로 저장된다.
- ( ) 이미지와 라벨 파일명이 일치한다(확장자만 다름).
- ( ) 정상 이미지의 라벨이 빈 파일로 생성된다.
- ( ) 전체 객체 수(YOLO 라인 총수)가 작업9의 439건과 일치한다.
- ( ) 재실행해도 동일한 결과가 나온다(재현성 — 무작위 요소 없음).
- ( ) 코드가 PEP 8 / black 포맷을 따른다.

## 제약사항

- 표준 라이브러리(`csv`, `logging`, `pathlib`) + 기존 `src/common/*` 유틸만 사용한다. 이미지/JSON을 다시 읽지 않으므로 `opencv-python`이 필요 없다면 추가하지 않는다.
- `metadata/`, `outputs/` 아래 기존 파일(작업9 산출물 등)은 읽기만 하고 수정하지 않는다.
- 함수/모듈 주석은 한글로 작성한다(프로젝트 관례).

## 테스트 방법 및 검증 기준 (CODEX 완료 후 CLAUDE가 이어서 수행)

1. `venv/Scripts/python.exe src/conversion/box_to_yolo.py` 실행
2. `outputs/yolo_labels/` 파일 수가 299개인지 확인
3. 정상 이미지로 알려진 파일(예: `RT_AL_00_14483440.txt`)이 빈 파일인지 확인
4. `outputs/yolo_labels/*.txt`의 전체 줄 수 합이 439와 일치하는지 확인
5. 임의의 몇 개 라벨 파일을 열어 좌표를 역산(픽셀 복원)해 `bbox_annotations.csv` 원본 값과 비교
6. `metadata/yolo_classes.txt`가 6줄이고 순서가 `class_statistics.csv`의 `class_id` 순서와 같은지 확인
7. 재실행 후 `outputs/yolo_labels/`와 `metadata/yolo_classes.txt`가 동일한지 확인
8. `docs/context/02-task-list.md` 작업10 완료 조건 충족 여부 확인(단, 클래스 번호 조건은 위 "완료 기준"에 명시한 대로 0~5 범위로 판단)
