# 구현 지시서: Polygon을 Bounding Box로 변환

## 배경

`docs/context/02-task-list.md` 작업9(Polygon을 Bounding Box로 변환)와 `docs/context/03-deliverables.md` 3.5절·6.2절에 따라, 원본 Polygon 좌표에서 Bounding Box(`x_min,y_min,x_max,y_max`)를 계산하고 원본 Polygon과 겹쳐 시각화한다.

**대상 범위**: 작업8에서 선별한 `metadata/selected_dataset.csv`의 `selected == True` 이미지 299장만 대상으로 한다 (RT+AL 전체 637장이나 2,250장 전체가 아니다 — 1차 PoC는 이미 선별된 데이터로만 진행한다).

## 기능 및 요구사항

### `src/conversion/polygon_to_box.py` (신규)

#### 1. 대상 이미지 구성

- `metadata/selected_dataset.csv`에서 `selected == "True"`인 행만 읽는다(299건).
- 각 `image_name`을 `metadata/raw_dataset_inventory.csv`와 조인해 `image_path`, `json_path`를 가져온다.
- `metadata/class_mapping.json`(원본 case → 표준 클래스명), `metadata/class_statistics.csv`(표준 클래스명 → 고정 `class_id`)를 읽어 클래스명↔ID 변환에 사용한다 — **작업6에서 정한 `class_id`를 그대로 재사용**하고 새로 계산하지 않는다.

#### 2. Polygon → Box 변환 (이미지별 원본 JSON을 직접 읽어서 처리)

각 이미지의 `annotations[]`를 순회하며, `case`가 빈 문자열(정상 placeholder)이면 건너뛴다. 그 외 annotation마다:

1. `coordinate.x`, `coordinate.y` 배열 길이가 다르면 → 오류로 기록하고 건너뛴다(`reason = "coordinate_count_mismatch"`).
2. `x_min = min(x)`, `x_max = max(x)`, `y_min = min(y)`, `y_max = max(y)` 계산.
3. 이미지 `width`/`height` 범위로 **클리핑**한다: `x_min = max(x_min, 0)`, `x_max = min(x_max, width)`, `y_min = max(y_min, 0)`, `y_max = min(y_max, height)` (완료 조건의 "좌표가 이미지 범위를 벗어나지 않는다"를 만족시키는 방식 — 이 프로젝트 RT+AL 선별 데이터에는 경계를 벗어나는 사례가 없을 것으로 보이지만, 코드는 일반적으로 클리핑을 적용해야 한다).
4. 클리핑 후 `x_min >= x_max` 또는 `y_min >= y_max`이면(박스가 찌그러짐) → 오류로 기록하고 건너뛴다(`reason = "degenerate_box_after_clipping"`).
5. 위를 모두 통과하면 표준 클래스명(`class_mapping.json`)과 `class_id`(`class_statistics.csv`)를 붙여 결과에 추가.

#### 3. 산출물

`metadata/bbox_annotations.csv`, 컬럼:

```
image_name, annotation_index, class_name, class_id, x_min, y_min, x_max, y_max, box_width, box_height, image_width, image_height
```

- `box_width = x_max - x_min`, `box_height = y_max - y_min`
- 정상 이미지(모든 annotation이 `case == ""`)는 이 CSV에 행이 없다 (변환할 Polygon 자체가 없음 — 작업10에서 `metadata/selected_dataset.csv`의 299장 목록과 대조해 이 CSV에 없는 이미지는 빈 라벨로 처리할 예정, 이번 작업 범위 아님).

`metadata/bbox_conversion_errors.csv`, 컬럼:

```
image_name, annotation_index, reason
```

#### 4. 시각화 (Polygon·Box 비교)

299장 전체에 대해(표본 추출 없음 — 이미 선별된 PoC 세트이므로 전부 시각화):

- 원본 Polygon: 얇은 폴리라인으로 표시.
- 변환된 Bounding Box: 다른 색, 두꺼운 사각형(`cv2.rectangle`)으로 표시.
- 클래스명을 박스 근처에 표시.
- `src/common/image_utils.read_image`로 이미지 읽기(한글 경로 대응), `cv2.imencode` + `Path.write_bytes`로 저장(작업7과 동일한 한글 경로 저장 패턴).
- 저장 위치: `outputs/polygon-box-comparison/{image_name}.jpg`
- 정상 이미지는 Polygon/Box 없이 원본 이미지만 저장(파일명 표시 정도만, 작업7과 동일 관례).

#### 5. 로그 출력

`logging`으로: 대상 이미지 수(299), 처리된 annotation 총수, 성공/오류 건수, 오류 사유별 건수, 이미지별 변환 전(=case가 빈 문자열이 아닌 annotation 수) vs 변환 후(성공한 box 수) 객체 수가 다른 이미지가 있으면 그 목록을 남긴다.

## 구현 범위 (In Scope)

- `src/conversion/polygon_to_box.py` 신규 생성
- `metadata/bbox_annotations.csv`, `metadata/bbox_conversion_errors.csv`, `outputs/polygon-box-comparison/*.jpg`는 스크립트 실행 결과물 — CODEX가 미리 만들지 않는다.

## 구현 제외 범위 (Out of Scope)

- `normalize_class_name.py`, `box_to_yolo.py`, `convert_aihub_to_yolo.py`, `write_yolo_label.py` — 이후 작업 범위(YOLO 정규화·라벨 생성).
- RT+AL 선별 299장 외 이미지 처리 — VT/ST 데이터나 작업8에서 제외된 이미지는 다루지 않는다.
- `class_id` 재계산 — `metadata/class_statistics.csv`의 기존 값을 그대로 조회해서 쓴다.

## 작업 전 반드시 확인해야 하는 문서

- `docs/context/02-task-list.md` 493~532줄 (작업9: 수행 작업, 검증 항목, 시각화, 산출물, 완료 조건)
- `docs/context/03-deliverables.md` 336~354줄(3.5 변환 코드), 699~711줄(6.2 Polygon·Bounding Box 비교)
- `metadata/selected_dataset.csv`, `metadata/class_mapping.json`, `metadata/class_statistics.csv`, `metadata/raw_dataset_inventory.csv` — 그대로 재사용
- `src/visualization/visualize_original_polygon.py` — Polygon 그리기·한글 경로 저장 패턴 재사용
- `src/common/image_utils.py`, `src/common/json_utils.py`

## 완료 기준 (Definition of Done)

- ( ) 정상 변환 가능한 모든 Polygon이 Box로 변환된다.
- ( ) 모든 Box 좌표가 이미지 범위 안에 있다(클리핑 적용).
- ( ) 이미지별 변환 전후 객체 수가 일치한다(불일치 시 오류 목록에 기록되어 확인 가능).
- ( ) 클래스가 작업6의 `class_id`를 그대로 유지한다.
- ( ) 변환 실패 데이터가 `bbox_conversion_errors.csv`에 별도로 기록된다.
- ( ) 재실행해도 동일한 결과가 나온다(재현성 — 이번 작업엔 무작위 요소가 없으므로 당연히 성립해야 함).
- ( ) 코드가 PEP 8 / black 포맷을 따른다.

## 제약사항

- 표준 라이브러리(`csv`, `json`, `logging`, `pathlib`) + `opencv-python`, `numpy` + 기존 `src/common/*` 유틸만 사용한다. 새 외부 패키지를 추가하지 않는다.
- `data/raw`, `metadata/` 아래 기존 파일은 읽기만 하고 수정하지 않는다.
- 함수/모듈 주석은 한글로 작성한다(프로젝트 관례).

## 테스트 방법 및 검증 기준 (CODEX 완료 후 CLAUDE가 이어서 수행)

1. `venv/Scripts/python.exe src/conversion/polygon_to_box.py` 실행
2. `metadata/bbox_annotations.csv`의 이미지별 객체 수가 원본(annotations 중 case가 빈 문자열이 아닌 것)과 일치하는지 표본 확인
3. `x_min < x_max`, `y_min < y_max`, `0 <= x_min`, `x_max <= image_width` 등 범위 조건이 전부 성립하는지 확인
4. `outputs/polygon-box-comparison/`에서 다중 객체 이미지, 정상 이미지 등을 직접 열어 Polygon이 Box 안에 포함되는지 육안 확인
5. 재실행 후 `bbox_annotations.csv`/`bbox_conversion_errors.csv`가 동일한지 확인
6. `docs/context/02-task-list.md` 작업9 완료 조건 5개 충족 여부 확인
