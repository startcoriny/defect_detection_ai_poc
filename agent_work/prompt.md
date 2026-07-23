# 구현 지시서: 자동 라벨 파일 생성

## 배경

`docs/context/02-task-list.md` 작업20(자동 라벨 파일 생성), `docs/context/03-deliverables.md` 3.7절(`export_auto_labels.py`)·5.4절(자동 라벨 결과 산출물)에 따라, 작업19에서 생성한 `predictions/prediction_results.json`(Test 46장 추론 원본 결과)을 표준 YOLO Detection TXT + 메타데이터 JSON + CVAT Import용 데이터로 정리한다.

이번 작업은 **새로운 추론을 하지 않는다**. 작업19가 이미 만든 `predictions/prediction_results.json`을 유일한 입력으로 읽어서 재가공만 한다(모델을 다시 로드하거나 이미지를 다시 추론하지 않는다).

## 기능 및 요구사항

### `src/model/export_auto_labels.py` (신규)

#### 1. 입력

- `predictions/prediction_results.json`(작업19 산출물, 유일한 입력)
- `metadata/yolo_classes.txt`(CVAT `obj.names`용 클래스 이름 목록, 재사용)

#### 2. `auto-labels/yolo-labels/` 생성

- Test 46장 **전부에 대해** 이미지 스템(확장자 제외 파일명)과 같은 이름의 `.txt` 파일을 만든다.
- 예측이 있으면 객체당 한 줄, `class_id center_x center_y width height`(정규화 좌표, `prediction_results.json`의 `bbox_normalized_xywh` 그대로 사용, 소수점 6자리) 형식으로 기록한다.
- 예측이 없는 이미지(정상 이미지, 미탐 이미지 포함)는 **빈 파일**(0바이트)을 만든다. 파일을 아예 안 만드는 것이 아니다 — 작업14(`build_yolo_dataset.py`)가 이미 "정상 이미지는 빈 라벨 파일"이라는 관례를 세워뒀으므로 그 관례를 따른다(Ultralytics의 `save_txt`가 예측 없는 이미지에 파일을 안 만드는 것과는 다른, 이 프로젝트의 의도적 선택이다).

#### 3. `auto-labels/prediction-metadata/` 생성

- `export_metadata.json`: `docs/context/02-task-list.md` 작업20의 예시 스키마를 따른다.
  ```json
  {
    "model_version": "EXP-P1-DET-001",
    "confidence_threshold": 0.25,
    "exported_at": "<ISO 8601, 이 스크립트 실행 시각>",
    "source": "predictions/prediction_results.json"
  }
  ```
  (`model_version`은 작업19와 동일하게 임의 문자열 `"baseline_v1"` 대신 실제 실험 ID `EXP-P1-DET-001`을 사용한다 — 작업19에서 이미 내린 결정과 일관성 유지.)
- `prediction_results.json`: 작업19가 만든 원본 파일을 **그대로 복사**한다(추론 시간, 픽셀 좌표, 실패 목록 등 원본 정보를 하나도 잃지 않기 위해 — 완료 조건 "원본 추론 결과를 잃지 않는다"를 문자 그대로 만족).

#### 4. `auto-labels/cvat-import/` 생성 (CVAT YOLO 1.1 / Darknet 형식)

- `obj.names`: `metadata/yolo_classes.txt`의 6개 클래스 이름을 줄 순서 그대로 복사(클래스 ID = 줄 번호, 프로젝트 전체에서 이미 쓰는 순서와 동일해야 함).
- `obj.data`:
  ```
  classes = 6
  train = train.txt
  names = obj.names
  backup = backup/
  ```
- `train.txt`: Test 46장의 상대경로(`obj_train_data/<파일명>`)를 한 줄씩, 파일명 순으로 기록.
- `obj_train_data/`: Test 46장 이미지(`data/processed/dataset_v1/images/test/`에서 복사, `shutil.copy2` 사용 — 원본은 읽기 전용) + 위 2번에서 만든 것과 동일한 내용의 라벨 TXT(이미지당 1개, 빈 파일 포함) 를 나란히 둔다.

## 구현 범위 (In Scope)

- `src/model/export_auto_labels.py` 신규 작성
- `auto-labels/{yolo-labels, prediction-metadata, cvat-import}/` 전체 생성

## 구현 제외 범위 (Out of Scope)

- 실제 CVAT 서버에 Import해서 검증하는 것(작업21의 범위, "가능하면" 수행하는 선택 사항이며 1차 PoC 필수 범위 밖).
- 새로운 모델 추론, Confidence Threshold 비교(작업22), 시각화 재생성(작업21) — 전부 이번 작업 범위가 아니다.
- `predictions/prediction_results.json` 자체를 수정하는 것 — 읽기 전용으로 참조만 한다.

## 작업 전 확인해야 하는 문서/코드

- `docs/context/02-task-list.md` 작업20
- `docs/context/03-deliverables.md` 5.4절
- `predictions/prediction_results.json`(작업19 산출물 — 스키마: `model_version`, `model_path`, `inference_config`, `generated_at`, `summary`, `images`(image_name/status/inference_time_ms/predictions[]), `failures`)
- `src/dataset/build_yolo_dataset.py`(정상 이미지 빈 라벨 파일 관례 참고)
- `metadata/yolo_classes.txt`

## 완료 기준 (Definition of Done)

- `( )` 예측 객체가 TXT에 저장된다(`auto-labels/yolo-labels/*.txt`).
- `( )` 객체당 한 줄로 생성된다.
- `( )` 클래스 번호와 좌표가 유효하다(0~5 범위, 정규화 좌표 0~1 범위 — `prediction_results.json`에서 그대로 가져오므로 재계산 없이 값 자체는 이미 유효함을 전제).
- `( )` Confidence와 모델 정보가 별도로 보존된다(`auto-labels/prediction-metadata/`에 원본 JSON 그대로 + 메타데이터).
- `( )` 원본 추론 결과를 잃지 않는다(`prediction_results.json` 원본 그대로 복사 보존).
- `( )` `auto-labels/cvat-import/`가 CVAT YOLO 1.1 Import 형식(`obj.names`, `obj.data`, `train.txt`, `obj_train_data/`)을 갖춘다.
- `( )` 코드가 PEP 8 / black 포맷을 따른다(ruff 통과).

## 제약사항

- `predictions/prediction_results.json`, `data/processed/dataset_v1/`, `metadata/`는 읽기만 하고 수정하지 않는다.
- 이미지 복사는 `shutil.copy2`를 사용한다(심볼릭 링크 금지 — 작업14에서 이미 정한 원칙과 동일).
- 이 스크립트는 모델을 로드하거나 추론을 실행하지 않는다(순수 파일 재가공). 따라서 CODEX 샌드박스에서도 원칙적으로 실행 가능하지만, 다른 스크립트들과의 일관성을 위해 실제 실행·결과 확인은 CLAUDE가 `venv/Scripts/python.exe`로 수행한다.

## 테스트 방법

1. `venv/Scripts/python.exe src/model/export_auto_labels.py` 실행
2. `auto-labels/yolo-labels/` — 파일 46개(이미지 수와 동일), 예측 있는 11개는 내용 있음, 나머지 35개는 0바이트인지 확인
3. `auto-labels/prediction-metadata/export_metadata.json` — `model_version == "EXP-P1-DET-001"` 확인
4. `auto-labels/prediction-metadata/prediction_results.json` — 작업19 원본과 내용 동일한지(`diff`) 확인
5. `auto-labels/cvat-import/obj.names` — 6줄(6클래스), `train.txt` — 46줄, `obj_train_data/` — 이미지 46장 + 라벨 46개 존재 확인
6. `black --check src/model/export_auto_labels.py`, `ruff check src/model/export_auto_labels.py` 통과 확인
