# 구현 지시서: YOLO 라벨 변환 결과 재시각화

## 배경

`docs/context/02-task-list.md` 작업11(변환 결과 재시각화)과 `docs/context/03-deliverables.md` 3.4절(`visualize_yolo_label.py`)·6.3절에 따라, 작업10에서 생성한 YOLO TXT 라벨을 다시 픽셀 좌표로 복원하고 원본 JSON Polygon과 비교해 "픽셀 → 정규화 → 픽셀" 왕복 과정에 오류가 없는지 검증한다.

**대상 범위**: 작업8에서 선별한 `metadata/selected_dataset.csv`의 `selected == True` 이미지 299장 전체(정상 이미지 포함), 표본 추출 없이 전수 검증한다.

**참고**: `docs/context/02-task-list.md` 609줄의 산출물 폴더명은 `outputs/yolo_visualization/`(스네이크케이스)이지만, `docs/context/03-deliverables.md` 6.3절은 같은 산출물을 `outputs/yolo-label-visualization/`(케밥케이스)로 표기한다. 작업7의 `outputs/original-polygon/`, 작업9의 `outputs/polygon-box-comparison/`와 동일하게 케밥케이스 관례를 따라 `outputs/yolo-label-visualization/`을 사용한다.

## 기능 및 요구사항

### `src/visualization/visualize_yolo_label.py` (신규)

#### 1. 입력 데이터

- `metadata/selected_dataset.csv`에서 `selected == "True"`인 `image_name` 299건.
- `metadata/raw_dataset_inventory.csv`: `image_path`, `json_path` 조인용.
- `metadata/bbox_annotations.csv`: 작업9가 계산한 "정답" 픽셀 Box(`annotation_index, class_name, class_id, x_min, y_min, x_max, y_max, image_width, image_height`) — 이번 작업의 비교 기준값으로 그대로 재사용(재계산하지 않음).
- `outputs/yolo_labels/{image_name}.txt`: 작업10이 생성한 YOLO 정규화 라벨(왕복 검증 대상).
- 원본 JSON(`json_path`): Polygon 좌표(`annotations[].coordinate.x/y`) — 시각화에 그릴 원본 Polygon과 포함 관계 검증에만 사용.

#### 2. 왕복 복원 및 검증 (이미지별)

각 선택된 `image_name`마다:

1. `metadata/bbox_annotations.csv`에서 해당 이미지의 행을 `annotation_index` 오름차순으로 정렬해 `expected` 목록으로 둔다.
2. `outputs/yolo_labels/{image_name}.txt`를 읽는다. **파일이 없으면** `reason="label_file_missing"`으로 기록하고 해당 이미지는 이후 단계를 건너뛴다(이미지·라벨 연결 오류 검증).
3. `len(expected) != 파일의 줄 수`이면 `reason="object_count_mismatch"`로 기록한다(객체 수 일치 검증). 이후 단계는 `min(len(expected), 줄 수)`까지만 비교한다.
4. 각 줄(`class_id cx cy w h`)을 `expected`의 같은 순번과 비교한다(같은 `annotation_index` 순서로 생성됐으므로 순번이 곧 대응 관계):
   - 픽셀 복원: `x_min = (cx - w/2) * image_width`, `x_max = (cx + w/2) * image_width`, `y_min`/`y_max`도 동일하게(`image_width`/`image_height`는 `expected`의 값 재사용).
   - `class_id`가 다르면 `reason="class_mismatch"`.
   - 좌표 반올림 오차: `max(|복원 x_min - expected x_min|, |복원 y_min - expected y_min|, |복원 x_max - expected x_max|, |복원 y_max - expected y_max|)`가 **0.5px 초과**면 `reason="coordinate_rounding_error_exceeded"`(YOLO 포맷이 소수점 6자리를 쓰므로 정상적으로는 발생하지 않아야 함).
   - Box 포함 관계: 원본 JSON에서 같은 `annotation_index`의 `coordinate.x`/`coordinate.y` 점들이 전부 `[복원 x_min - 0.5, 복원 x_max + 0.5] × [복원 y_min - 0.5, 복원 y_max + 0.5]` 안에 있는지 확인 — 벗어나면 `reason="polygon_not_contained"`.
5. 정상 이미지(=이번 이미지에 `expected` 행이 없음): 라벨 파일이 존재하고 **빈 파일**인지만 확인, 다르면 `reason="normal_image_label_not_empty"`.

#### 3. 시각화 (299장 전체, 표본 추출 없음)

- 원본 이미지를 읽어(`src/common/image_utils.read_image`), 원본 Polygon(얇은 폴리라인)과 **YOLO 라벨에서 복원한 Box**(굵은 사각형, 작업9와 다른 색)를 함께 그린다 — 정답 `bbox_annotations.csv`의 Box가 아니라 **왕복 복원값**을 그려야 이번 검증의 의미가 있다.
- 클래스명(`expected`의 `class_name` 재사용)을 Box 근처에 표시.
- 파일명·이미지 크기를 좌상단에 표시.
- 정상 이미지는 Polygon/Box 없이 원본 이미지만 저장(작업7·9와 동일 관례).
- 저장: `cv2.imencode(".jpg", image)` + `Path.write_bytes(...)`(한글 경로 우회, 기존 패턴 재사용).
- 저장 위치: `outputs/yolo-label-visualization/{image_name}.jpg`

#### 4. 산출물

`metadata/yolo_roundtrip_mismatches.csv`, 컬럼:

```
image_name, annotation_index, reason
```

(`annotation_index`는 해당 안 되는 경우—예: `label_file_missing`, `object_count_mismatch`, `normal_image_label_not_empty`—빈 문자열로 남긴다.)

#### 5. 로그 출력

`logging`으로: 대상 이미지 수(299), 검증한 객체 쌍 수, 발견된 불일치 건수(사유별), 관측된 최대 좌표 오차(px), 전체 통과 여부(불일치 0건이면 "PASS").

## 구현 범위 (In Scope)

- `src/visualization/visualize_yolo_label.py` 신규 생성

## 구현 제외 범위 (Out of Scope)

- `analyze_statistics.py`(작업12 데이터셋 통계) — 이번 작업 범위 아님.
- `bbox_annotations.csv`/`outputs/yolo_labels/` 재계산 — 두 산출물 모두 기존 값을 읽기만 한다.
- VT/ST 데이터나 작업8에서 제외된 이미지 처리.

## 작업 전 반드시 확인해야 하는 문서

- `docs/context/02-task-list.md` 581~623줄(작업11: 수행 작업, 확인할 내용, 산출물, 완료 조건)
- `docs/context/03-deliverables.md` 713~724줄(6.3 YOLO 라벨 재시각화)
- `metadata/selected_dataset.csv`, `metadata/raw_dataset_inventory.csv`, `metadata/bbox_annotations.csv`, `outputs/yolo_labels/*.txt` — 그대로 재사용
- `src/conversion/polygon_to_box.py`의 `draw_comparison`/`save_image` — Polygon·Box 시각화·한글 경로 저장 패턴 재사용
- `src/common/image_utils.py`, `src/common/json_utils.py`

## 완료 기준 (Definition of Done)

- ( ) 원본 객체 수(=`bbox_annotations.csv` 기준)와 YOLO 라벨의 객체 수가 이미지별로 일치한다.
- ( ) 클래스(`class_id`)가 변하지 않는다.
- ( ) 복원한 Box가 원본 Polygon을 포함한다.
- ( ) 이미지·라벨 파일 연결 오류가 없다(299장 전부 라벨 파일 존재).
- ( ) 샘플이 아니라 299장/439객체 전체가 검증된다.
- ( ) 좌표 반올림 오차가 관측되면 정량적으로 기록된다(0.5px 초과 시 불일치로 기록).
- ( ) 코드가 PEP 8 / black 포맷을 따른다.

## 제약사항

- 표준 라이브러리(`csv`, `json`, `logging`, `pathlib`) + `opencv-python`, `numpy` + 기존 `src/common/*` 유틸만 사용한다.
- `metadata/`, `outputs/yolo_labels/` 아래 기존 파일은 읽기만 하고 수정하지 않는다.
- 함수/모듈 주석은 한글로 작성한다(프로젝트 관례).

## 테스트 방법 및 검증 기준 (CODEX 완료 후 CLAUDE가 이어서 수행)

1. `venv/Scripts/python.exe src/visualization/visualize_yolo_label.py` 실행 — 로그 마지막 줄에서 불일치 0건("PASS") 확인
2. `metadata/yolo_roundtrip_mismatches.csv`가 헤더만 있는지(0건) 확인
3. `outputs/yolo-label-visualization/` 299장 생성 확인
4. 다중 객체 이미지(`RT_AL_02_14489189.jpg`), 폭넓은 단일 객체(`RT_AL_02_14483871.jpg`), 정상 이미지(`RT_AL_00_14483440.jpg`) 육안 확인 — 복원된 Box가 원본 Polygon을 포함하는지
5. 재실행 후 `metadata/yolo_roundtrip_mismatches.csv`가 동일한지 확인
6. `docs/context/02-task-list.md` 작업11 완료 조건 충족 여부 확인
