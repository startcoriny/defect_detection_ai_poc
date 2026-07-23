# 구현 지시서: 데이터셋 최종 검증

## 배경

`docs/context/02-task-list.md` 작업15(데이터셋 최종 검증)와 `docs/context/03-deliverables.md` 3.3절(`validate_yolo_dataset.py`)에 따라, 작업14가 만든 `data/processed/dataset_v1/`을 학습 직전 마지막으로 독립 재검증한다.

**설계 원칙**: 이 작업은 작업9~14가 이미 계산·검증한 값(`metadata/*.csv`)을 다시 신뢰하지 않고, **`data/processed/dataset_v1/`에 실제로 존재하는 파일만을 근거로** 처음부터 다시 검사한다(학습 직전 최종 게이트라는 작업 취지에 맞음). `metadata/`는 참조하지 않는다.

**대상 범위**: `data/processed/dataset_v1/images/{train,val,test}/*.jpg`, `data/processed/dataset_v1/labels/{train,val,test}/*.txt`, `data/processed/dataset_v1/data.yaml`.

## 기능 및 요구사항

### `src/validation/validate_yolo_dataset.py` (신규)

#### 1. 입력

- `data/processed/dataset_v1/data.yaml`: `path`, `train`/`val`/`test` 상대경로, `names`(class_id→class_name, 0부터 연속) — 여기서 유효 `class_id` 범위(0~5)를 얻는다(재계산 없음, `data.yaml`에 이미 있는 값을 그대로 읽음).
- 위 경로가 가리키는 `images/`, `labels/` 폴더의 실제 파일 목록.

#### 2. 검증 항목(작업5의 ERROR/WARNING/INFO 어휘 체계를 그대로 적용)

**ERROR(치명적 — 1건이라도 있으면 학습 불가)**:

- `image_missing`: 라벨 파일은 있는데 대응하는 이미지가 없음
- `label_missing`: 이미지는 있는데 대응하는 라벨 파일이 없음(위 둘이 "이미지·라벨 파일명 일치" 항목도 함께 충족시킴)
- `image_unreadable`: 이미지 파일이 존재하지만 `src/common/image_utils.read_image`로 디코딩 실패
- `label_line_value_count_mismatch`: 라벨의 한 줄이 공백으로 나눴을 때 정확히 5개 값이 아님
- `class_id_out_of_range`: 라벨의 `class_id`가 `data.yaml`의 `names`에 없는 값
- `coordinate_out_of_range`: `center_x`/`center_y`/`width`/`height` 중 하나라도 `[0, 1]` 범위를 벗어남
- `cross_split_duplicate`: 같은 `image_name`이 `train`/`val`/`test` 중 둘 이상에 존재

**WARNING(검토 필요, 치명적은 아님)**:

- `class_missing_in_split`: 데이터셋 전체(3개 분할 합산)에는 등장하지만 특정 분할에는 한 번도 등장하지 않는 `class_id`가 있음(이번 데이터셋에서는 `porosity`/`slag_inclusion`만 대상 — 애초에 등장하지 않는 클래스는 검사하지 않는다)

**정상 처리(오류 아님, 그냥 집계)**:

- 라벨 파일 내용이 빈 문자열(공백만 있어도 빈 것으로 취급)이면 "정상 이미지"로 집계만 하고 오류로 기록하지 않는다("빈 라벨 처리" 항목).

#### 3. 산출물

`reports/dataset/final_dataset_validation_report.csv`, ERROR/WARNING 발견 건만 행으로 기록(정상 파일은 행을 만들지 않는다), 컬럼:

```
split, image_name, check, severity, detail
```

`reports/dataset/final_dataset_validation_summary.md`: 한글 서술 보고서. 다음을 포함한다:

- 분할별 이미지 수, 정상(빈 라벨) 이미지 수
- 검증 성공(오류 없음) 파일 수 vs 실패(ERROR 있음) 파일 수
- 체크 항목별 ERROR/WARNING 건수
- **학습 가능 여부**: ERROR 0건이면 "학습 가능", 1건 이상이면 "학습 불가 — 아래 오류 확인 필요"
- **데이터셋 버전 고정**: `data/processed/dataset_v1/`의 모든 파일(이미지+라벨+`data.yaml`)을 상대경로 오름차순으로 정렬해 각 파일의 SHA-256 해시를 이어붙인 뒤 다시 SHA-256을 계산한 "데이터셋 매니페스트 해시" 1개 값을 기록한다(재실행 시 같은 값이 나와야 "버전이 고정"됨을 확인할 수 있음).

#### 4. 로그

`logging`으로: 분할별 이미지/라벨 수, 체크 항목별 ERROR/WARNING 건수, 데이터셋 매니페스트 해시, 최종 "학습 가능"/"학습 불가" 판정.

## 구현 범위 (In Scope)

- `src/validation/validate_yolo_dataset.py` 신규 생성
- `reports/dataset/{final_dataset_validation_report.csv, final_dataset_validation_summary.md}` 신규 생성

## 구현 제외 범위 (Out of Scope)

- `metadata/*.csv`, `outputs/`, `data/raw` 등 다른 산출물과의 교차 검증 — 이번 작업은 `data/processed/dataset_v1/`만 독립적으로 검사한다.
- 발견된 오류의 자동 수정 — 검증만 하고 수정하지 않는다(오류가 있으면 그대로 보고).
- 작업16(Smoke Test) 이후 단계.

## 작업 전 반드시 확인해야 하는 문서

- `docs/context/02-task-list.md` 774~805줄(작업15: 수행 작업, 검증 항목, 산출물, 완료 조건)
- `docs/context/03-deliverables.md` 293~312줄(3.3 데이터 검증 코드)
- `data/processed/dataset_v1/data.yaml`, `data/processed/dataset_v1/{images,labels}/{train,val,test}/`
- `src/validation/validate_polygon.py`(작업5) — ERROR/WARNING 어휘 체계·CSV 산출물 패턴 참고
- `src/common/image_utils.py`(`read_image`)

## 완료 기준 (Definition of Done)

- ( ) 치명적(ERROR) 오류가 0건이다.
- ( ) WARNING 항목이 있다면 보고서에 남아 검토할 수 있다(0건이어도 무방).
- ( ) Train·Val·Test 모두 이미지·라벨 파일명이 1:1로 일치하고 읽기 가능해 학습 가능한 구조임이 확인된다.
- ( ) 데이터셋 매니페스트 해시로 버전이 고정되어, 재실행해도 동일한 해시가 나온다(재현성).
- ( ) 코드가 PEP 8 / black 포맷을 따른다.

## 제약사항

- 표준 라이브러리(`csv`, `hashlib`, `logging`, `pathlib`) + `opencv-python`, `numpy`, `pyyaml` + 기존 `src/common/*` 유틸만 사용한다.
- `data/processed/dataset_v1/` 아래 기존 파일은 읽기만 하고 수정하지 않는다.
- 함수/모듈 주석은 한글로 작성한다(프로젝트 관례).

## 테스트 방법 및 검증 기준 (CODEX 완료 후 CLAUDE가 이어서 수행)

1. `venv/Scripts/python.exe src/validation/validate_yolo_dataset.py` 실행 — 로그에서 ERROR 0건, "학습 가능" 확인
2. `reports/dataset/final_dataset_validation_report.csv`가 헤더만 있는지(오류 0건) 확인
3. `reports/dataset/final_dataset_validation_summary.md`에서 분할별 이미지 수(209/44/46), 정상 이미지 수(100)가 기존 작업13·14 결과와 일치하는지 확인
4. 매니페스트 해시를 기록해두고, 재실행 후 동일한 해시가 나오는지 확인(재현성 = 버전 고정 확인)
5. `docs/context/02-task-list.md` 작업15 완료 조건 4개 충족 여부 확인
