# 구현 지시서: YOLO 학습 데이터셋 구성

## 배경

`docs/context/02-task-list.md` 작업14(YOLO 학습 데이터셋 구성)와 `docs/context/03-deliverables.md` 2.5절·3.6절에 따라, 작업13에서 확정한 분할(`train`/`val`/`test`)대로 이미지·라벨 파일을 YOLO 표준 폴더 구조로 배치하고 `data.yaml`을 생성한다.

**대상 범위**: `metadata/selected_dataset.csv`의 `selected == True` 299장 전체(정상 이미지 포함, `split_group` 컬럼은 작업13에서 이미 채워짐: train 209 / val 44 / test 46).

**참고 1 — 저장 위치**: `docs/context/02-task-list.md`는 예시로 `dataset/`(저장소 루트)를 보여주지만, `docs/context/03-deliverables.md` 2.5절과 `CLAUDE.md`의 Storage 정의(`data/processed`: 변환 결과)는 `data/processed/dataset_v1/`을 사용한다. 기존 프로젝트 구조 관례를 따라 `data/processed/dataset_v1/`을 사용한다(`.gitignore`에 이미 `/data/`가 등록되어 있어 별도 gitignore 수정 없이 자동으로 커밋 제외됨).

**참고 2 — 클래스 매핑**: `docs/context/02-task-list.md`의 `data.yaml` 예시는 `0: porosity, 1: slag_inclusion` 2-클래스이지만, 이 프로젝트는 작업6에서 6개 표준 클래스(`class_id` 0~5)를 확정했고 이후 모든 산출물(`class_statistics.csv`, `bbox_annotations.csv`, `yolo_classes.txt`)이 이 6-클래스 체계를 그대로 써왔다. `data.yaml`의 `names`도 `metadata/yolo_classes.txt`(class_id 0~5 순서)를 그대로 재사용해 6개 클래스 전부를 담는다 — 재계산·재배정하지 않는다.

**참고 3 — 파일 배치 방식**: task-list는 "복사 또는 Symbolic Link 둘 다 가능"이라고 하지만, 이번 구현은 **복사(copy)** 를 사용한다. Windows에서 심볼릭 링크는 개발자 모드/관리자 권한이 필요해 팀원 환경마다 동작이 다를 수 있고, 이 PoC 규모(299장)에서는 복사에 따른 디스크 사용량 증가가 감수할 만하다.

## 기능 및 요구사항

### `src/dataset/build_yolo_dataset.py` (신규)

#### 1. 입력 데이터

- `metadata/selected_dataset.csv`: `selected == "True"` 299장의 `image_name`, `split_group`(train/val/test)
- `metadata/raw_dataset_inventory.csv`: `image_path`(원본 이미지 경로, 전부 `.jpg`)
- `outputs/yolo_labels/{image_name}.txt`: 작업10이 생성한 YOLO 라벨(정상 이미지는 빈 파일 포함, 299개 전부 존재해야 함)
- `metadata/yolo_classes.txt`: `data.yaml`의 `names`에 그대로 사용(재계산 없음)

#### 2. 폴더 구조 생성 및 파일 배치

```
data/processed/dataset_v1/
├── images/
│   ├── train/  (209장)
│   ├── val/    (44장)
│   └── test/   (46장)
├── labels/
│   ├── train/  (209개)
│   ├── val/    (44개)
│   └── test/   (46개)
└── data.yaml
```

- 각 선택 이미지를 `split_group` 값에 따라 `images/{split}/{image_name}.jpg`로 복사(원본은 전부 `.jpg`).
- 대응하는 `outputs/yolo_labels/{image_name}.txt`를 `labels/{split}/{image_name}.txt`로 복사.
- 복사 후 각 파일 쌍을 원본과 대조해 무결성을 확인한다(파일 크기 또는 해시 비교 — 내용이 원본과 다르면 오류로 기록하고 실행을 실패시킨다).
- 소스 라벨 파일이 없는 선택 이미지가 있으면(작업10 미실행 등) 명확한 오류 메시지와 함께 실행을 중단한다.

#### 3. `data.yaml` 생성 (PyYAML 사용, `sort_keys=False`로 순서 보존)

```yaml
path: data/processed/dataset_v1
train: images/train
val: images/val
test: images/test

names:
  0: crack
  1: incomplete_penetration
  2: lack_of_fusion
  3: porosity
  4: slag_inclusion
  5: undercut
```

(`names`는 `metadata/yolo_classes.txt`를 순서대로 읽어 `{index: class_name}`으로 채운다.)

#### 4. 검증 및 로그

다음을 코드로 확인하고 위반 시 실행을 실패시킨다:

- 각 분할에서 `images/{split}/`와 `labels/{split}/`의 파일 수가 정확히 같다(확장자만 다른 동일 basename 쌍).
- 분할별 합계가 209/44/46(작업13 결과)과 일치한다.
- `data.yaml`의 `names` 6개가 `metadata/yolo_classes.txt`의 순서·내용과 정확히 같다.
- `data.yaml`에 적힌 `path`/`train`/`val`/`test` 경로를 프로젝트 루트 기준으로 조합했을 때 실제로 존재하는 디렉터리인지 확인한다.
- 정상 이미지(라벨 파일이 빈 파일인 것)가 배치된 데이터셋에도 그대로 포함되어 있는지 확인한다(제외되지 않았는지).

`logging`으로: 분할별 이미지·라벨 파일 수, 전체 복사 파일 수, `data.yaml` 검증 결과, 정상 이미지 수를 남긴다.

## 구현 범위 (In Scope)

- `src/dataset/build_yolo_dataset.py` 신규 생성
- `data/processed/dataset_v1/` 전체(스크립트 실행 결과물 — CODEX가 미리 만들지 않는다)

## 구현 제외 범위 (Out of Scope)

- `verify_split.py` — 별도 스크립트로 만들지 않는다(작업13과 동일하게 검증은 이번 스크립트 안에서 수행).
- `data/raw`, `outputs/yolo_labels/`, `metadata/*.csv` 등 기존 입력 파일 수정 — 전부 읽기 전용.
- 심볼릭 링크 지원 — 이번 구현은 복사만 한다.
- 작업15(데이터셋 최종 검증) 이후 단계.

## 작업 전 반드시 확인해야 하는 문서

- `docs/context/02-task-list.md` 724~770줄(작업14: 수행 작업, 산출물, 완료 조건)
- `docs/context/03-deliverables.md` 175~211줄(2.5 변환된 YOLO Detection 데이터셋), 356~373줄(3.6 데이터 분할 코드)
- `metadata/selected_dataset.csv`(`split_group` 컬럼), `metadata/raw_dataset_inventory.csv`, `metadata/yolo_classes.txt`, `outputs/yolo_labels/*.txt`

## 완료 기준 (Definition of Done)

- ( ) 각 분할의 이미지 수와 라벨 수가 정확히 같다(209/44/46).
- ( ) 폴더 구조가 `images/{train,val,test}`, `labels/{train,val,test}` YOLO 표준 형식에 맞는다.
- ( ) `data.yaml`의 클래스 매핑이 `yolo_classes.txt`와 정확히 일치한다.
- ( ) `data.yaml`의 `path`/`train`/`val`/`test` 경로가 실제 존재하는 디렉터리를 가리킨다.
- ( ) 정상 이미지도 배치된 데이터셋에 포함된다(제외되지 않음).
- ( ) 재실행해도 동일한 결과가 나온다(재현성 — 무작위 요소 없음, 파일 복사이므로 내용 동일).
- ( ) 코드가 PEP 8 / black 포맷을 따른다.

## 제약사항

- 표준 라이브러리(`csv`, `shutil`, `logging`, `pathlib`) + `pyyaml`(이미 `requirements.txt`에 있음) + 기존 `src/common/*` 유틸만 사용한다. 이미지를 디코딩할 필요가 없으므로 `opencv-python`은 사용하지 않는다.
- `metadata/`, `outputs/`, `data/raw` 아래 기존 파일은 읽기만 하고 수정하지 않는다.
- 함수/모듈 주석은 한글로 작성한다(프로젝트 관례).

## 테스트 방법 및 검증 기준 (CODEX 완료 후 CLAUDE가 이어서 수행)

1. `venv/Scripts/python.exe src/dataset/build_yolo_dataset.py` 실행
2. `find data/processed/dataset_v1/images -type f | wc -l` → 299, `labels` 동일 → 299
3. 분할별 개수(`images/train`, `images/val`, `images/test`) → 209/44/46
4. `data/processed/dataset_v1/data.yaml` 내용이 `names` 6개(`metadata/yolo_classes.txt`와 순서 일치) 포함하는지 확인
5. 정상 이미지 하나(`RT_AL_00_14483440`)가 `images/{split}/`와 `labels/{split}/`(빈 파일)에 실제로 존재하는지 확인
6. 임의 이미지 하나를 골라 `data/processed/dataset_v1/images/{split}/{name}.jpg`가 원본(`data/raw/...`)과 파일 크기가 같은지 확인
7. 재실행 후 산출물이 동일한지 확인
8. `docs/context/02-task-list.md` 작업14 완료 조건 5개 충족 여부 확인
