# 구현 지시서: 오탐·미탐 분석 — 사례 수집

## 배경

`docs/context/02-task-list.md` 작업24(오탐·미탐 분석), `docs/context/03-deliverables.md` 3.8절(`collect_error_cases.py`)·7.8절(`docs/08_error_analysis.md`)에 따라, 작업23의 평가 조건(conf=0.25, IoU 0.5, Test 46장)에서 실패 사례(오탐/미탐/클래스 오류/위치 오류)를 자동으로 분류하고 이미지와 함께 저장한다.

**이번 작업의 역할 분담**: 이 스크립트는 실패 사례를 **객관적으로 분류·저장**하는 것까지만 한다. "정상 패턴 오인"·"흐릿한 결함"처럼 이미지를 직접 보고 판단해야 하는 정성적 원인 분류는 스크립트가 하지 않는다 — CLAUDE가 저장된 사례 이미지를 직접 검토해 `docs/08_error_analysis.md`(작업24의 최종 보고서, deliverables.md 7.8절에 명시된 경로)에 작성한다.

## 기능 및 요구사항

### `src/evaluation/collect_error_cases.py` (신규)

#### 1. 입력

- 모델: `experiments/EXP-P1-DET-001/models/best.pt`, 설정: conf=0.25, iou=0.70, imgsz=640, device=cpu(작업19~23과 동일)
- GT: `data/processed/dataset_v1/labels/test/*.txt`(작업23과 동일한 방식으로 로드, 크기 버킷 포함)
- 이미지: `data/processed/dataset_v1/images/test/`
- 매칭 IoU 기준: 0.5(작업23과 동일)

#### 2. 4단계 매칭 (작업23보다 세분화— 클래스 오류·위치 오류를 별도로 구분)

작업23의 매칭은 "같은 클래스 + IoU 0.5 이상"만 TP로 보고 나머지는 전부 FP 또는 FN으로 뭉뚱그렸다. 이번엔 그 "나머지"를 아래처럼 세분화한다(이미지 1장 안에서 순서대로 처리):

1. **정답(TP)**: 같은 클래스 + IoU≥0.5로 매칭된 쌍. 저장 대상 아님(에러가 아니므로).
2. **wrong_class(클래스 오류)**: 1번에서 매칭 안 된 예측과 GT 중, 클래스가 달라도 IoU≥0.5인 쌍이 있으면 그 쌍을 매칭해 `wrong_class`로 분류(둘 다 소모).
3. **localization_error(위치 오류)**: 남은 것 중 같은 클래스이면서 0.1≤IoU<0.5인 쌍이 있으면 그 쌍을 매칭해 `localization_error`로 분류(둘 다 소모). (0.1이라는 하한은 문서에 없어 "전혀 안 겹침"과 "애매하게 겹침"을 구분하기 위해 임의로 정한 값 — `docs/08_error_analysis.md`에 이 기준을 명시한다.)
4. 그래도 안 남은 예측 → **false_positive**, 안 남은 GT → **false_negative**.

각 이미지 안에서 여러 후보가 있을 경우 Confidence 높은 예측부터, 그 예측이 매칭 가능한 후보 중 IoU가 가장 높은 것과 매칭한다(그리디, 작업23과 동일한 방식).

#### 3. 각 사례에 대해 객관적으로 계산 가능한 보조 정보(정성 판단 아님)

- `confidence`: 예측이 있으면 그 값, 없으면 공란(false_negative)
- `gt_size_bucket`: GT가 있으면 작업12 기준(Small/Medium/Large), 없으면 공란(false_positive)
- `box_area_ratio`: 예측이 있으면 예측 박스 면적/이미지 면적, 없으면 공란
- `near_edge`: GT 또는 예측 박스가 있고 그 박스 경계가 이미지 가장자리에서 5% 이내면 `True`(작업24 미탐 분류 항목 "경계 결함"을 사람이 판단할 때 참고할 객관적 신호일 뿐, 최종 분류는 아님)
- `duplicate_of_tp`: false_positive인 예측이 이미 매칭된 TP와 같은 클래스이고 IoU≥0.3이면 `True`(작업24 오탐 분류 항목 "중복 예측" 판단 참고용)

#### 4. 산출물

- `errors/{false_positive, false_negative, wrong_class, localization_error}/<이미지스템>_<순번>.jpg`: 원본 이미지에 GT(초록, 있으면)와 Prediction(자홍, 있으면) 박스를 그리고 각각 클래스명(+Prediction은 Confidence)을 표기한 시각화. 이미지 좌상단에 파일명·오류 유형을 표기.
- `reports/evaluation/error_cases.csv`(컬럼: `case_id, image_name, error_type, gt_class, gt_size_bucket, pred_class, confidence, box_area_ratio, near_edge, duplicate_of_tp, case_image_path`) — 4번 항목의 이미지 경로를 포함해 사람이 파일명으로 바로 찾아갈 수 있게 한다.
- `reports/evaluation/error_type_counts.csv`(컬럼: `error_type, class_name, count`) — 오류 유형×클래스별 건수 집계(이건 객관적 집계이므로 스크립트가 만든다. "원인별" 통계는 사람이 사례를 보고 판단하는 것이므로 스크립트 범위가 아니다).

## 구현 범위 (In Scope)

- `src/evaluation/collect_error_cases.py` 신규 작성
- `errors/{false_positive,false_negative,wrong_class,localization_error}/`, `reports/evaluation/{error_cases.csv, error_type_counts.csv}` 생성

## 구현 제외 범위 (Out of Scope)

- `docs/08_error_analysis.md`(정성적 원인 분석·개선 후보 서술) — CLAUDE가 실제 사례 이미지를 검토한 뒤 직접 작성한다.
- Ground Truth 라벨 자체의 오류 여부 재검증(이미 작업15에서 검증됨) — 이번 작업은 예측·GT 매칭 결과만 다룬다.
- 새로운 모델 학습·Threshold 변경.

## 작업 전 확인해야 하는 문서/코드

- `docs/context/02-task-list.md` 작업24
- `docs/context/03-deliverables.md` 3.8절, 7.8절
- `src/evaluation/calculate_metrics.py`(작업23 — GT 로드, IoU 계산, 크기 버킷, 개별 이미지 순회 패턴 재사용)
- `src/visualization/visualize_yolo_label.py`(GT+Prediction 동시 시각화 패턴 참고)

## 완료 기준 (Definition of Done)

- `( )` 오탐(false_positive)과 미탐(false_negative)이 구분되어 저장된다.
- `( )` wrong_class(클래스 오류), localization_error(위치 오류)도 별도로 구분된다.
- `( )` 모든 실패 사례가 이미지와 함께 저장된다(`errors/<유형>/`).
- `( )` `reports/evaluation/error_cases.csv`, `error_type_counts.csv`가 생성된다.
- `( )` 코드가 PEP 8 / black 포맷을 따른다(ruff 통과).

## 제약사항

- `experiments/EXP-P1-DET-001/models/best.pt`, `data/processed/dataset_v1/`은 읽기만 하고 수정하지 않는다.
- 이미지 읽기/쓰기는 기존 시각화 스크립트와 동일하게 Unicode 안전 방식(`common.image_utils.read_image`, `cv2.imencode`+`write_bytes`)을 쓴다.
- `errors/`는 프로젝트 루트 최상위에 생성한다(`docs/context/02-task-list.md`·`03-deliverables.md`가 명시한 폴더 구조).
- 이 스크립트는 CODEX 샌드박스에서 직접 실행·검증할 수 없다(Python 실행 불가). 코드 작성까지만 CODEX가 담당하고, 실제 실행·결과 확인 및 `docs/08_error_analysis.md` 작성은 CLAUDE가 수행한다.

## 테스트 방법

1. `venv/Scripts/python.exe src/evaluation/collect_error_cases.py` 실행
2. `reports/evaluation/error_type_counts.csv` — `false_negative` 합이 45(작업23에서 확인한 미탐 수)와 대략 일치하는지 확인(localization_error로 일부 재분류되면 정확히 45는 아닐 수 있음 — 그 경우 왜 그런지 확인)
3. `errors/false_positive/`, `errors/wrong_class/` — 각각 3장, 1장 내외 존재 확인(작업23에서 확인한 배경 오탐 3건, 클래스 오류 1건)
4. 시각화 이미지 하나를 열어 GT·Prediction 박스와 라벨이 올바르게 표시되는지 육안 확인
5. `black --check src/evaluation/collect_error_cases.py`, `ruff check src/evaluation/collect_error_cases.py` 통과 확인
