# 구현 지시서: Train·Validation·Test 분할

## 배경

`docs/context/02-task-list.md` 작업13(Train·Validation·Test 분할)과 `docs/context/03-deliverables.md` 3.6절에 따라, 작업8에서 선별한 299장을 70/15/15 비율로 분할한다.

**대상 범위**: `metadata/selected_dataset.csv`의 `selected == True` 299장.

**참고**: `metadata/selected_dataset.csv`에는 작업8에서 이미 채워진 `group` 컬럼(`normal`/`porosity`/`slag_inclusion`/`both`, 값: normal 100 / porosity 99 / slag_inclusion 99 / both 1)과, 작업8 당시 비워둔 `split_group` 컬럼이 있다("이후 `split_dataset.py`가 채울 예정"이라고 작업8에서 이미 명시됨). 이번 작업은 이 `group` 컬럼과 아래 정의할 객체 크기 기준을 함께 층화 기준으로 사용해 `split_group` 컬럼을 채운다.

`docs/context/02-task-list.md`의 분할 고려사항 중 "동일 그룹 데이터"는 이 프로젝트에 이미지 단위의 별도 물리적 그룹 메타데이터(예: 동일 용접부 연속 촬영본 식별자)가 없으므로, 작업8이 이미 정의한 `group` 컬럼(정상/porosity/slag_inclusion/both)을 층화 기준으로 삼는 것으로 해석한다(다른 2개 고려사항 — 클래스별 이미지·객체 수, 정상 이미지 비율 — 도 전부 이 `group` 층화로 자연히 충족됨).

**2단계 층화(그룹×크기)**: `group`만으로 층화한 1차 시도에서 분할 간 작은 객체 비율이 크게 벌어지는 문제(train 55.80% / val 62.32% / test 79.79%, 범위 24%p)가 실제로 발견되어, 이번 작업은 `group`에 더해 이미지 단위 크기 특성도 층화 기준에 포함한다(아래 3절 참고).

## 기능 및 요구사항

### `src/dataset/split_dataset.py` (신규)

#### 1. 입력 데이터

- `metadata/selected_dataset.csv`: `selected == "True"` 299장, `group`/`duplicate` 컬럼 재사용
- `metadata/bbox_annotations.csv`: 분할별 클래스 통계 계산용(작업9 결과, 재계산 없음)
- `metadata/class_statistics.csv`: 표준 클래스 6개 고정 목록

#### 2. 중복 이미지 사전 확인

선택된 299장 중 `duplicate == "True"`인 행이 있으면 실행을 중단하고 오류를 낸다(`ValueError`) — 이 프로젝트의 299장에는 실제로 0건이지만(작업5/8에서 이미 확인됨), 중복 이미지를 서로 다른 분할에 나누는 로직은 이번 구현에 없으므로 발생 시 조용히 진행하지 않고 명시적으로 실패시킨다.

#### 3. 그룹×크기 2단계 층화 분할 (Seed 42, 비율 70/15/15)

**이미지별 크기 특성(`size_class`) 계산** — `bbox_annotations.csv`에서 이미지별 객체들의 `relative_area = (box_width/image_width) * (box_height/image_height)`를 계산(작업12와 동일 정의)하고, 각 이미지에 대해:

- `relative_area < 0.01`인 객체 수가 그 이미지 전체 객체 수의 절반 이상이면 `size_class = "small_dominant"`
- 그렇지 않으면(객체가 있는데 절반 미만) `size_class = "mixed"`
- `group == "normal"`인 이미지(객체 없음)는 `size_class`를 매기지 않는다(크기 층화 대상이 아님).

**층화 키**: `group == "normal"`이면 층화 키는 `("normal",)` 그대로. 그 외(`porosity`, `slag_inclusion`, `both`)는 층화 키를 `(group, size_class)`로 세분화한다. 예상되는 층화 키와 실제 이미지 수(검증용, 실제 계산값과 비교):

```
("normal",)                        100
("porosity", "small_dominant")      77
("porosity", "mixed")               22
("slag_inclusion", "small_dominant") 30
("slag_inclusion", "mixed")          69
("both", "mixed")                    1
```

- 위 6개 층화 키를 문자열로 이어붙인 값(`"normal"`, `"porosity_mixed"` 등) 기준 **알파벳순**으로 고정 순회한다: `both_mixed` → `normal` → `porosity_mixed` → `porosity_small_dominant` → `slag_inclusion_mixed` → `slag_inclusion_small_dominant`.
- 각 층화 키 그룹마다 소속 `image_name`을 오름차순 정렬한 뒤, **하나의 `random.Random(42)` 인스턴스**로(전체 스크립트에서 단 하나의 인스턴스를 재사용) `rng.shuffle()`을 적용한다.
- 그룹 크기 `N`에 대해: `n_train = round(N * 0.70)`, `n_val = round(N * 0.15)`, `n_test = N - n_train - n_val`(나머지 전부, 반올림 오차를 test가 흡수).
- 셔플된 순서대로 앞에서부터 `n_train`개는 `train`, 다음 `n_val`개는 `val`, 나머지는 `test`로 배정한다.

#### 4. 산출물 갱신·생성

**`metadata/selected_dataset.csv`의 `split_group` 컬럼을 채워서 같은 파일에 덮어쓴다** — 이 컬럼은 작업8에서 이번 작업을 위해 의도적으로 비워둔 자리이므로, 다른 모든 컬럼과 값은 그대로 두고 `split_group`만 `train`/`val`/`test`로 채운다(다른 metadata 파일은 계속 읽기 전용).

`splits/train.txt`, `splits/val.txt`, `splits/test.txt` (신규 폴더): 각 파일에 해당 분할의 `image_name`을 오름차순 한 줄씩 기록(파일당 이미지 수 예상값: train209/val44/test46, 위 6개 층화 키에 대한 반올림 배분 합계).

`reports/dataset/split_distribution.csv`: 분할×표준 클래스 6개 전부(18행), 컬럼:

```
split, class_id, class_name, image_count, object_count
```

(작업12의 `class_distribution.csv`와 동일한 집계 방식을 분할별로 반복 — 미등장 클래스는 0,0)

`reports/dataset/split_validation_report.md`: 한글 서술 보고서. 다음을 포함한다:

- 분할별 이미지 수·비율(목표 70/15/15 대비 실제 값)
- 분할별 정상 이미지 수(0이면 안 됨)
- 분할별 대상 클래스(`porosity`, `slag_inclusion`) 이미지 수(0이면 안 됨)
- **분할×층화 키(그룹×크기) 이미지 수 표** — 6개 층화 키가 각 분할에 어떻게 배분됐는지 표로 표시
- 분할별 작은 객체(작업12 기준 `relative_area < 0.01`) **객체 단위** 비율과, 세 분할 간 비율 범위(최댓값-최솟값). 이전 `group`만으로 층화했을 때의 범위(24.0%p, train 55.80%/val 62.32%/test 79.79%)를 함께 적어 이번 그룹×크기 층화로 범위가 줄었는지 비교 서술한다.
- 중복 이미지 검사 결과(0건 확인)
- Random Seed(42) 명시
- "동일 이미지가 여러 분할에 속하지 않음"을 코드로 재확인한 결과(교집합 크기 0)

## 구현 범위 (In Scope)

- `src/dataset/split_dataset.py` 신규 생성
- `metadata/selected_dataset.csv`의 `split_group` 컬럼 갱신(유일하게 허용되는 기존 파일 수정)
- `splits/{train,val,test}.txt`, `reports/dataset/{split_distribution.csv, split_validation_report.md}` 신규 생성

## 구현 제외 범위 (Out of Scope)

- `build_yolo_dataset.py`(작업14, `data/processed/dataset_v1/` 폴더 구조·이미지 파일 복사) — 이번 작업은 텍스트 목록만 생성한다.
- `verify_split.py` — 별도 스크립트로 만들지 않는다. 검증은 이번 스크립트 안에서 수행하고 결과를 `split_validation_report.md`에 기록한다(작업7·9·11과 동일하게 한 작업은 한 스크립트로 구현).
- `metadata/selected_dataset.csv`의 `split_group` 외 다른 컬럼 변경, 다른 metadata 파일 수정.

## 작업 전 반드시 확인해야 하는 문서

- `docs/context/02-task-list.md` 672~721줄(작업13: 수행 작업, 분할 고려사항, 산출물, 완료 조건)
- `docs/context/03-deliverables.md` 356~373줄(3.6 데이터 분할 코드)
- `metadata/selected_dataset.csv`(특히 `group`, `duplicate`, `split_group` 컬럼), `metadata/bbox_annotations.csv`, `metadata/class_statistics.csv`
- `src/data/analyze_statistics.py` — 클래스별 이미지·객체 수 집계 로직 재사용

## 완료 기준 (Definition of Done)

- ( ) 동일 이미지가 여러 분할에 없다(교집합 0, 코드로 검증).
- ( ) 중복 이미지가 없음을 확인했다(있었다면 실행이 실패해야 함).
- ( ) 각 분할(train/val/test)에 정상 이미지가 1장 이상 포함된다.
- ( ) 각 분할에 `porosity`, `slag_inclusion` 이미지가 1장 이상 존재한다.
- ( ) 동일 Seed(42)로 재실행하면 동일한 분할이 나온다(재현성).
- ( ) 그룹×크기 2단계 층화 결과, 분할 간 작은 객체 비율 범위가 이전(24.0%p)보다 줄었다.
- ( ) 코드가 PEP 8 / black 포맷을 따른다.

## 제약사항

- 표준 라이브러리(`csv`, `random`, `logging`, `pathlib`) + 기존 `src/common/*` 유틸만 사용한다.
- **예외적으로 `metadata/selected_dataset.csv`의 `split_group` 컬럼만 갱신을 허용한다.** 그 외 모든 metadata 파일과 `selected_dataset.csv`의 다른 컬럼은 읽기 전용으로 취급한다.
- 함수/모듈 주석은 한글로 작성한다(프로젝트 관례).

## 테스트 방법 및 검증 기준 (CODEX 완료 후 CLAUDE가 이어서 수행)

1. `venv/Scripts/python.exe src/dataset/split_dataset.py` 실행
2. `wc -l splits/train.txt splits/val.txt splits/test.txt` → 예상 209/44/46 (그룹×크기 6개 층화 키 반올림 배분 합계)
3. `metadata/selected_dataset.csv`에서 `split_group` 값이 `selected=True`인 299행 전부 채워졌는지, `selected=False` 행은 그대로 빈 값인지 확인
4. `reports/dataset/split_distribution.csv`에서 `porosity`/`slag_inclusion`이 3개 분할 모두 `image_count > 0`인지 확인
5. `splits/train.txt` ∩ `splits/val.txt` ∩ `splits/test.txt` 교집합이 빈 집합인지 확인
6. `split_validation_report.md`의 작은 객체 비율 범위가 이전 24.0%p보다 줄었는지 확인
7. 재실행 후 `splits/*.txt`, `selected_dataset.csv`의 `split_group` 컬럼, `reports/dataset/*`가 모두 동일한지 확인
8. `docs/context/02-task-list.md` 작업13 완료 조건 5개 충족 여부 확인
