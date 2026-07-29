# 구현 지시서: 라이브 데모용 GT vs 예측 나란히 비교 시각화 스크립트

## 배경

내부 기술팀 대상 오토 라벨링 라이브 데모를 준비 중이다. 기존 산출물(`outputs/EXP-P1-DET-005/auto-label-visualization/`)은 예측 박스만 그려진 이미지라, 실제 정답(GT)과 비교하며 성공/실패 사례를 설명하기 어렵다. 미리 선정한 케이스 4건에 한해 GT 박스와 예측 박스를 나란히(좌: GT / 우: 예측) 비교할 수 있는 이미지를 생성한다.

케이스는 `predictions/EXP-P1-DET-005/prediction_results.json`(예측)과 `data/processed/dataset_v3/labels/test/*.txt`(GT, YOLO 정규화 좌표)를 대조해 이미 선정을 마쳤다:

| image_name | 케이스 라벨 |
| --- | --- |
| `RT_AL_02_14489691.jpg` | `성공 사례: porosity 2건 모두 정확히 검출` |
| `RT_AL_05_14492165.jpg` | `성공 사례: slag_inclusion 정확히 검출` |
| `RT_AL_02_14488212.jpg` | `실패 사례(미탐): Small porosity 놓침` |
| `RT_AL_05_14492954.jpg` | `실패 사례(위치 오류): 예측 박스가 GT보다 작게 그려짐` |

## 기능 및 요구사항

`src/visualization/exp5/visualize_prediction.py`와 동일한 컨벤션(PROJECT_ROOT 기준 경로 상수, `common.image_utils.read_image`, `common.json_utils.load_json`, cv2 기반 그리기, `cv2.imencode`로 저장, 함수별 한 줄 한국어 주석, logging 모듈)을 따라 새 스크립트 `src/visualization/exp5/compare_gt_prediction.py`를 작성한다.

1. 위 표의 4개 이미지를 `(image_name, case_label)` 튜플의 모듈 상수 리스트로 하드코딩한다(이번 데모 전용 1회성 스크립트이므로 CLI 인자·설정 파일 불필요).
2. 각 이미지에 대해:
   - 원본 이미지를 `data/processed/dataset_v3/images/test/{image_name}`에서 읽는다(`common.image_utils.read_image`).
   - GT 박스를 `data/processed/dataset_v3/labels/test/{stem}.txt`에서 읽는다. YOLO 정규화 좌표 파싱과 픽셀 좌표 복원은 `visualize_prediction.py`의 `parse_yolo_line`, `restore_box` 함수를 import해서 재사용한다(로직 중복 작성 금지).
   - 예측 박스는 `predictions/EXP-P1-DET-005/prediction_results.json`을 로드해 `image_name`이 일치하는 레코드의 `predictions` 목록(`bbox_normalized_xywh`, `class_name`, `confidence`)을 사용한다.
   - 클래스명은 `metadata/yolo_classes.txt`(6줄, 순서대로 class_id 0~5)를 그대로 사용한다.
3. GT 박스는 초록색(BGR `(0, 200, 0)`), 예측 박스는 빨간색(BGR `(0, 0, 255)`)으로 그리고, 각 박스 위에 라벨 텍스트를 표시한다(GT: `클래스명`만, 예측: `클래스명 confidence`).
4. 좌(GT 패널)·우(예측 패널) 2개 패널을 만들어 `cv2.hconcat`으로 이어 붙이고, 두 패널 사이에 얇은 구분선(예: 흰색 세로 바 4px)을 넣는다. 각 패널 상단에 패널 이름("GT" / "Prediction")을 흰색 텍스트로 표시한다.
5. 합쳐진 이미지 맨 위에 케이스 라벨(위 표의 `case_label`)을 한 줄로 표시한다(배경이 있는 텍스트 박스 또는 굵은 흰색 텍스트로, 원본 이미지 내용을 가리지 않는 선에서).
6. 결과 이미지를 `outputs/EXP-P1-DET-005/demo-comparison/{image_name}`에 저장한다(디렉터리 없으면 생성).
7. 4개 이미지 모두 처리한 뒤, 처리 성공 개수를 `logging`으로 출력한다(GT 라벨 파일이나 예측 레코드가 없으면 에러 로그를 남기고 해당 케이스는 건너뛴다 — 예외를 삼키지 않는다).

## 구현 범위 (In Scope)

- `src/visualization/exp5/compare_gt_prediction.py` 신규 작성
- `outputs/EXP-P1-DET-005/demo-comparison/`에 4개 비교 이미지 생성(스크립트 실행은 CLAUDE가 수행)

## 구현 제외 범위 (Out of Scope)

- `visualize_prediction.py` 등 기존 exp5 스크립트 수정 — 함수 import만 하고 원본은 건드리지 않는다
- 다른 실험(exp1~exp4, exp6, exp7)용 유사 스크립트 작성 — 이번 데모는 EXP-P1-DET-005 전용
- 4개 케이스 외 이미지에 대한 일반화(CLI 인자, 설정 파일 등) — 하드코딩 리스트로 충분
- 실제 스크립트 실행 — CLAUDE가 수행

## 완료 기준 (Definition of Done)

- `( )` `src/visualization/exp5/compare_gt_prediction.py` 파일이 존재하고 `python src/visualization/exp5/compare_gt_prediction.py` 실행 시 오류 없이 종료한다.
- `( )` `outputs/EXP-P1-DET-005/demo-comparison/`에 4개 이미지(`RT_AL_02_14489691.jpg`, `RT_AL_05_14492165.jpg`, `RT_AL_02_14488212.jpg`, `RT_AL_05_14492954.jpg`)가 생성된다.
- `( )` 각 이미지가 좌(GT, 초록 박스)·우(예측, 빨간 박스) 2분할 구조이고, 상단에 케이스 라벨이 표시된다.
- `( )` `parse_yolo_line`, `restore_box`는 `visualize_prediction.py`에서 import해 재사용하고 중복 정의하지 않는다.
- `( )` 코드가 PEP 8 / black 포맷을 따르고 ruff를 통과한다.

## 제약사항

- `src/visualization/exp5/visualize_prediction.py`, `src/common/image_utils.py`, `src/common/json_utils.py`는 읽기만 하고 수정하지 않는다.
- 이 작업은 CODEX 샌드박스에서 Python을 실행해 검증할 수 없다. 코드 작성까지만 CODEX가 담당하고, 실제 실행·결과 확인은 CLAUDE가 수행한다.

## 테스트 방법 (CLAUDE가 이어서 수행)

1. `python src/visualization/exp5/compare_gt_prediction.py` 실행해 오류 없이 종료하는지 확인
2. `outputs/EXP-P1-DET-005/demo-comparison/`에 4개 파일이 생성됐는지 확인
3. 이미지를 열어 GT·예측 박스 색상, 좌우 배치, 케이스 라벨 텍스트가 의도대로 표시되는지 육안 확인
4. `ruff check src/visualization/exp5/compare_gt_prediction.py`로 린트 확인
