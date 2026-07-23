# 구현 지시서: 데이터셋 통계 분석

## 배경

`docs/context/02-task-list.md` 작업12(데이터셋 통계 분석)와 `docs/context/03-deliverables.md` 2.6절·3.2절에 따라, 작업8에서 선별한 299장 PoC 데이터셋의 이미지·객체·클래스·크기·해상도 통계를 생성한다. 이후 작업13(Train/Val/Test 분할)이 참조할 기초 통계를 준비하는 것이 목적이다.

**대상 범위**: `metadata/selected_dataset.csv`의 `selected == True` 299장. 원본 2,250장 전체가 아니다.

**참고**: `docs/context/03-deliverables.md` 2.6절 산출물 위치는 `reports/dataset/`(작업5의 `reports/data-quality/`와 동일 관례), 파일명 `dataset_summary.csv`이지만, `docs/context/02-task-list.md` 658줄은 같은 산출물을 `selected_dataset_statistics.csv`로 명명한다. 폴더 위치는 `03-deliverables.md`(기존 `reports/` 관례), 파일명은 `02-task-list.md`(더 구체적인 이름)를 따른다 — 즉 `reports/dataset/selected_dataset_statistics.csv`.

## 기능 및 요구사항

### `src/data/analyze_statistics.py` (신규)

#### 1. 입력 데이터 (모두 기존 산출물 재사용, 재계산 없음)

- `metadata/selected_dataset.csv`: `selected == "True"` 299장 목록
- `metadata/raw_dataset_inventory.csv`: 이미지별 `width`, `height` (정상 이미지 포함 299장 전체 해상도 확보용 — `bbox_annotations.csv`에는 정상 이미지 행이 없으므로)
- `metadata/bbox_annotations.csv`: 객체별 `class_name`, `class_id`, `box_width`, `box_height`, `image_width`, `image_height` (작업9 결과)
- `metadata/class_statistics.csv`: 표준 클래스 6개 고정 목록(0~5) — 이번 선별 데이터에 없는 클래스도 0건으로 표시하기 위해 사용

#### 2. 산출물 1 — `reports/dataset/selected_dataset_statistics.csv` (key,value 2컬럼)

다음 행을 순서대로 기록한다:

```
total_images        (299)
normal_images       (bbox_annotations.csv에 행이 없는 선택 이미지 수)
defect_images       (total_images - normal_images)
total_objects       (bbox_annotations.csv 선택 이미지 행 수 합)
avg_objects_per_image        (total_objects / total_images, 소수 6자리)
avg_objects_per_defect_image (total_objects / defect_images, 소수 6자리)
multi_object_images   (객체가 2개 이상인 이미지 수)
multi_class_images    (서로 다른 class_name이 2개 이상 등장하는 이미지 수)
distinct_resolutions  ((width,height) 조합 종류 수)
image_width_min / image_width_max
image_height_min / image_height_max
```

#### 3. 산출물 2 — `reports/dataset/class_distribution.csv`

`class_statistics.csv`의 6개 표준 클래스 전부(class_id 0~5 순서)에 대해:

```
class_id, class_name, image_count, object_count
```

- `image_count`: 해당 클래스 객체가 1개 이상 있는 선택 이미지 수(299장 기준, 중복 집계 금지)
- `object_count`: 해당 클래스 객체(annotation) 총수
- 이번 선별 데이터(299장)에 등장하지 않는 클래스는 `image_count=0, object_count=0`으로 표시(전체 6-클래스 체계와의 일관성 유지)

#### 4. 산출물 3 — `reports/dataset/object_size_distribution.csv`

각 객체의 `relative_area = (box_width / image_width) * (box_height / image_height)`를 계산해 3구간으로 분류한다:

- `Small`: `relative_area < 0.01`
- `Medium`: `0.01 <= relative_area < 0.05`
- `Large`: `relative_area >= 0.05`

(이 임계값은 실제 439개 객체의 `relative_area` 분포—중앙값 0.006, 90분위수 0.029, 최댓값 0.245—를 근거로 정한 값이다. Small/Medium/Large가 각각 전체의 약 62%/36%/2%로 나뉘어 "작은 결함이 다수"라는 실제 특성을 보여준다.)

컬럼:

```
class_name, size_bucket, count, percentage
```

- `class_name`은 `"all"`(전체 439건 기준)과 이번 데이터에 실제로 등장하는 각 클래스명(`porosity`, `slag_inclusion`)별로 각각 3행(Small/Medium/Large)씩, 총 9행.
- `percentage`는 해당 `class_name` 그룹 내 비율(소수점 2자리, `%` 기호 없이 숫자만).

#### 5. 산출물 4 — `reports/dataset/dataset_analysis_report.md`

한글로 작성하는 서술형 보고서. 다음 내용을 포함한다:

- 전체/정상/불량 이미지 수, 전체 객체 수, 이미지당 평균 객체 수
- 클래스별 이미지 수·객체 수 표(위 CSV 요약)
- 객체 크기 분포 표(위 CSV 요약)와 "작은 결함 비중" 해석 한 문단
- 이미지 해상도 분포: 등장 빈도 상위 5개 해상도(내림차순)와 각 건수, 전체 서로 다른 해상도 종류 수, 최소/최대 width·height
- 복수 객체 이미지 수, 복수 클래스 이미지 수와 그 의미(예: 복수 클래스 이미지는 작업8에서 강제 포함한 1장과 일치해야 함)

## 구현 범위 (In Scope)

- `src/data/analyze_statistics.py` 신규 생성
- `reports/dataset/` 아래 4개 산출물

## 구현 제외 범위 (Out of Scope)

- `split_distribution.csv` — 작업13(Train/Val/Test 분할) 이후에나 존재할 수 있는 산출물이라 이번 작업 범위가 아니다.
- 원본 2,250장 전체 통계 — 이번 작업은 선별된 299장만 다룬다.
- `class_statistics.csv`/`bbox_annotations.csv`/`raw_dataset_inventory.csv` 재계산 — 전부 읽기만 한다.

## 작업 전 반드시 확인해야 하는 문서

- `docs/context/02-task-list.md` 626~669줄(작업12: 수행 작업, 객체 크기, 산출물, 완료 조건)
- `docs/context/03-deliverables.md` 214~246줄(2.6 데이터셋 통계 자료), 273~292줄(3.2 데이터 분석 코드)
- `metadata/selected_dataset.csv`, `metadata/raw_dataset_inventory.csv`, `metadata/bbox_annotations.csv`, `metadata/class_statistics.csv` — 그대로 재사용

## 완료 기준 (Definition of Done)

- ( ) 이미지 수와 객체 수가 각 산출물에서 명확히 구분되어 집계된다.
- ( ) 클래스별 이미지 수·객체 수로 클래스 불균형을 확인할 수 있다(6개 클래스 전부 표시, 미등장 클래스는 0).
- ( ) 객체 크기 분포(Small/Medium/Large)로 작은 결함의 비중을 확인할 수 있다.
- ( ) `reports/dataset/` 4개 산출물이 생성되어 작업13의 데이터 분할에 참고할 수 있다.
- ( ) 재실행해도 동일한 결과가 나온다(재현성 — 무작위 요소 없음).
- ( ) 코드가 PEP 8 / black 포맷을 따른다.

## 제약사항

- 표준 라이브러리(`csv`, `logging`, `pathlib`) + 기존 `src/common/*` 유틸만 사용한다. 이미지를 다시 열 필요는 없다(치수는 `raw_dataset_inventory.csv`에 이미 있음).
- `metadata/` 아래 기존 파일은 읽기만 하고 수정하지 않는다.
- 함수/모듈 주석은 한글로 작성한다(프로젝트 관례).

## 테스트 방법 및 검증 기준 (CODEX 완료 후 CLAUDE가 이어서 수행)

1. `venv/Scripts/python.exe src/data/analyze_statistics.py` 실행
2. `reports/dataset/selected_dataset_statistics.csv`의 `total_images=299`, `total_objects=439`, `normal_images=100` 확인
3. `class_distribution.csv`에서 `porosity`/`slag_inclusion` 외 4개 클래스가 0건으로 표시되는지 확인
4. `object_size_distribution.csv`의 9행(`all`/`porosity`/`slag_inclusion` × 3구간) 합계가 각 그룹별로 100%(반올림 오차 감안)인지 확인
5. `multi_class_images`가 1(작업8에서 강제 포함한 "둘 다" 이미지)과 일치하는지 확인
6. 재실행 후 4개 산출물이 모두 동일한지 확인
7. `docs/context/02-task-list.md` 작업12 완료 조건 4개 충족 여부 확인
