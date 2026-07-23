# 구현 지시서: 자동 라벨 재시각화

## 배경

`docs/context/02-task-list.md` 작업21(자동 라벨 재시각화), `docs/context/03-deliverables.md` 3.4절(시각화 코드)에 따라, 작업20이 만든 `auto-labels/yolo-labels/*.txt`(+ `auto-labels/prediction-metadata/`)를 다시 읽어 이미지에 그리고, 원본 Prediction(작업19의 `predictions/prediction_results.json`)과 정확히 일치하는지 왕복 검증한다.

**주의 — 이번 작업이 비교하는 대상**: "정답(Ground Truth) 라벨과 모델 예측을 비교"하는 게 아니다(그건 작업23/24의 범위). 이번 작업은 순수하게 **"작업19의 원본 JSON → 작업20의 TXT 변환 과정에서 정보가 손실되거나 왜곡되지 않았는가"**를 확인하는 포맷 왕복(round-trip) 검증이다.

**파일명 결정**: `docs/context/03-deliverables.md` 3.4절의 `src/visualization/` 목록 중 `visualize_prediction.py`(역할: "Prediction 표시")를 사용한다. `visualize_original_polygon.py`(작업7), `visualize_yolo_label.py`(작업11)는 이미 존재하고, `visualize_prediction.py`는 아직 없다 — 작업19(`run_inference.py`)는 Ultralytics 내장 기능으로 예측 시각화를 이미 처리했으므로, 이 파일명은 이번 작업(자동 라벨 재시각화)에 사용한다.

## 참고할 기존 코드

`src/visualization/visualize_yolo_label.py`(작업11)가 이번 작업과 거의 동일한 구조(왕복 검증 + 시각화 + 불일치 CSV 기록)를 이미 구현해뒀다. 아래 패턴을 그대로 재사용한다:

- `common.image_utils.read_image`로 이미지 읽기(Unicode 경로 안전)
- `cv2.imencode(".jpg", image)` + `Path.write_bytes`로 이미지 저장(Unicode 경로 안전, 직접 `cv2.imwrite` 쓰지 않음)
- 불일치를 리스트로 모아 CSV로 저장, 마지막에 `Counter`로 사유별 집계 로그 출력, 불일치 있으면 종료 코드 1

## 기능 및 요구사항

### `src/visualization/visualize_prediction.py` (신규)

#### 1. 입력

- `predictions/prediction_results.json`(작업19, 원본 — "정답"에 해당하는 왕복 검증 기준)
- `auto-labels/yolo-labels/*.txt`(작업20, 왕복 변환 결과)
- `auto-labels/prediction-metadata/export_metadata.json`(모델 버전 확인용)
- `metadata/yolo_classes.txt`(class_id → class_name 매핑, 재사용)
- `data/processed/dataset_v1/images/test/`(원본 이미지, 시각화 배경)

#### 2. 왕복 검증

Test 46장 전체에 대해 다음을 확인한다(이미지당):

- `auto-labels/yolo-labels/<stem>.txt`가 존재하는가(작업20에서 46장 전부 생성했으므로 없으면 불일치).
- TXT의 줄 수(=예측 객체 수)가 원본 JSON `images[].predictions`의 길이와 같은가.
- TXT 각 줄의 `class_id`가 원본 JSON의 `class_id`와 같은 순서로 일치하는가.
- TXT의 정규화 좌표(`center_x center_y width height`)가 원본 JSON의 `bbox_normalized_xywh`와 오차 허용치(절대오차 1e-4, TXT가 소수점 6자리로 저장되므로 이 정도 오차는 부동소수점 반올림만 반영해야 함) 이내로 일치하는가.
- `class_id`를 `metadata/yolo_classes.txt`로 변환한 이름이 원본 JSON의 `class_name`과 같은가.
- `auto-labels/prediction-metadata/export_metadata.json`의 `model_version`이 원본 JSON의 `model_version`과 같은가(전체 1회만 확인해도 됨, 이미지별 반복 불필요).

불일치를 발견하면 즉시 실패시키지 말고, 전부 수집해 `metadata/auto_label_roundtrip_mismatches.csv`(컬럼: `image_name, prediction_index, reason`)로 저장한다(작업11의 `yolo_roundtrip_mismatches.csv`와 동일한 관례).

#### 3. 시각화

- 원본 이미지 위에 TXT에서 복원한 Bounding Box(픽셀 좌표로 역변환)를 그린다.
- 각 박스 옆에 클래스명과 Confidence(`prediction-metadata/prediction_results.json`에서 가져옴 — TXT엔 없으므로)를 함께 표기한다.
- 이미지 좌상단에 파일명과 모델 버전을 표기한다.
- 예측이 없는 이미지(빈 TXT)도 원본 이미지 그대로 저장한다(박스 없이 파일명만 표기).
- 저장 위치: `outputs/auto-label-visualization/`(작업11의 `outputs/yolo-label-visualization/`과 동일한 명명 관례).

#### 4. CVAT Import 데이터 구조 확인 (완료 조건 중 "CVAT Import 가능 형식" 항목)

실제 CVAT 서버에 연결해서 Import하는 것은 1차 PoC 범위 밖이므로 하지 않는다(이전에 이미 확인한 결정 사항). 대신 `auto-labels/cvat-import/`가 아래 구조를 갖췄는지만 파일 존재 여부로 확인한다:

- `obj.names`(6줄), `obj.data`, `train.txt`(46줄)
- `obj_train_data/`에 46장 이미지 + 46개 라벨 TXT(92개 파일)

이 결과도 로그에 남긴다(별도 파일 생성 불필요, `visualize_prediction.py` 실행 로그로 충분).

## 구현 범위 (In Scope)

- `src/visualization/visualize_prediction.py` 신규 작성
- `outputs/auto-label-visualization/`(시각화 이미지 46장), `metadata/auto_label_roundtrip_mismatches.csv`(불일치 기록) 생성
- CVAT Import 데이터 구조 확인(파일 존재 여부 체크, 로그로만 보고)

## 구현 제외 범위 (Out of Scope)

- 실제 CVAT 서버 연결·Import 실행(1차 PoC 범위 밖).
- Ground Truth(정답 결함 위치)와 모델 예측의 비교(작업23/24의 범위) — 이번 작업은 "원본 JSON ↔ TXT 왕복"만 검증한다.
- 새로운 모델 추론, `predictions/`·`auto-labels/` 내용 수정 — 전부 읽기 전용.

## 작업 전 확인해야 하는 문서/코드

- `docs/context/02-task-list.md` 작업21
- `docs/context/03-deliverables.md` 3.4절, 6.3절(비슷한 시각화 패턴)
- `src/visualization/visualize_yolo_label.py`(작업11 — 재사용할 왕복 검증·시각화·CSV 기록 패턴)
- `predictions/prediction_results.json`, `auto-labels/{yolo-labels, prediction-metadata, cvat-import}/`
- `src/common/image_utils.py`의 `read_image`

## 완료 기준 (Definition of Done)

- `( )` 저장된 라벨(TXT)이 이미지에서 원본 예측과 같은 위치에 표시된다.
- `( )` 클래스와 객체 수가 원본과 동일하게 유지된다(46장 전체 검증).
- `( )` Confidence와 모델 버전이 별도로(메타데이터에) 보존돼 있음을 확인했다.
- `( )` `auto-labels/cvat-import/`가 CVAT에서 불러올 수 있는 형식(파일 구조)인지 확인했다.
- `( )` 코드가 PEP 8 / black 포맷을 따른다(ruff 통과).

## 제약사항

- `predictions/`, `auto-labels/`, `data/processed/dataset_v1/`, `metadata/yolo_classes.txt`는 읽기만 하고 수정하지 않는다.
- 이미지 읽기/쓰기는 `visualize_yolo_label.py`와 동일하게 Unicode 안전 방식(`read_image`, `cv2.imencode`+`write_bytes`)을 쓴다.
- 모델을 로드하거나 추론을 실행하지 않는다(순수 파일 비교·시각화). CODEX 샌드박스에서 Python을 실행할 수 없는 기존 제약은 동일하게 적용되므로, 코드 작성까지는 CODEX가, 실제 실행·검증은 CLAUDE가 `venv/Scripts/python.exe`로 수행한다.

## 테스트 방법

1. `venv/Scripts/python.exe src/visualization/visualize_prediction.py` 실행
2. `outputs/auto-label-visualization/` — 이미지 46장 존재, 예측 있는 이미지(예: `RT_AL_02_14488001.jpg`)에 박스+클래스명+Confidence 표기 확인
3. `metadata/auto_label_roundtrip_mismatches.csv` — 불일치 0건인지 확인(헤더만 있어야 정상)
4. 로그에서 CVAT Import 구조 확인 결과(`obj.names`/`obj.data`/`train.txt`/`obj_train_data/` 파일 수) 확인
5. `black --check src/visualization/visualize_prediction.py`, `ruff check src/visualization/visualize_prediction.py` 통과 확인
