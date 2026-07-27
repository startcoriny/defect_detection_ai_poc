# 코드 리뷰: dataset_v2 구축 스크립트 생성

## 요구사항 충족 여부

- `src/dataset/v2/{select_poc_dataset.py, split_dataset.py, build_yolo_dataset.py}`, `src/conversion/v2/{polygon_to_box.py, box_to_yolo.py}` 5개 생성 — 확인
- 5개 파일 전부 `PROJECT_ROOT`가 `parent.parent.parent.parent`로 수정됨 — `grep`으로 확인
- `TARGET_COUNT = 1000`(select_poc_dataset.py v2) — 확인
- 입출력 경로 전부 v2 전용 경로로 분리(`metadata/v2/`, `data/processed/dataset_v2/`, `outputs/{polygon-box-comparison-v2, yolo_labels_v2}/`, `splits/v2/`, `reports/dataset/v2/`) — `diff --strip-trailing-cr`로 원본과 라인 단위 대조해 확인, 지정 외 변경 없음
- `EXPECTED_STRATUM_COUNTS`(split_dataset.py), `EXPECTED_SPLIT_COUNTS`(build_yolo_dataset.py) 하드코딩 제거 및 로그 대체 — 확인
- 과거 dataset_v1 비교 문구("이전 group 단독 층화의 train 55.80%...") 제거 — 확인
- `metadata/class_statistics.csv` 등 공용 산출물 참조는 원본과 동일하게 유지됨 — 확인
- 기존 원본 5개 스크립트는 `git diff` 결과 변경 없음 — 확인

## 발견한 문제 및 수정

- `black --check` 결과 `src/conversion/v2/polygon_to_box.py` 1개 파일에서 재포맷 필요(CODEX가 `BBOX_ERRORS_PATH` 대입을 불필요하게 여러 줄로 나눔) — CLAUDE가 `black` 직접 적용해 수정. 그 외 4개 파일은 처음부터 통과.
- `ruff check` — 5개 파일 전부 처음부터 통과.

## 실행 결과 (5단계 파이프라인 전체 실행)

1. `select_poc_dataset.py` — RT/AL 637장 중 567장 선택(normal 225, porosity 222, slag_inclusion 119, both 1). 제외 70건(non_target_class 68, off_target_class_present 2)은 목표 클래스 외 결함이 섞인 이미지라 정상적인 제외.
2. `polygon_to_box.py` — 567장 전량 변환 성공, annotations=812, errors=0.
3. `box_to_yolo.py` — 라벨 567개 생성(선택 이미지 수와 일치). porosity 575개 객체, slag_inclusion 237개 객체.
4. `split_dataset.py` — 예외 없이 완료. train 398 / val 85 / test 84(70.19%/14.99%/14.81%, 목표 70/15/15와 근접). 작은 객체 비율 범위 3.84%p(상한 24.0%p 이내, dataset_v1보다 오히려 더 균형 잡힘). 모든 분할에 normal·porosity·slag_inclusion 최소 1장 이상 포함 확인.
5. `build_yolo_dataset.py` — `data/processed/dataset_v2/` 생성 완료, `data.yaml` 검증 통과, 각 분할 이미지·라벨 개수 일치(398/85/84).

## dataset_v1 대비 규모 비교

| 항목 | dataset_v1 | dataset_v2 |
| --- | ---: | ---: |
| 전체 이미지 | 299 | 567 |
| Train/Val/Test | 209/44/46 | 398/85/84 |
| porosity 객체 수(전체) | 약 185(train 기준) | 575 |
| slag_inclusion 객체 수(전체) | 약 147(train 기준) | 237 |

## 사용자가 직접 확인하는 방법

1. `diff --strip-trailing-cr src/dataset/select_poc_dataset.py src/dataset/v2/select_poc_dataset.py` 등으로 지정된 변경만 있는지 확인
2. `cat reports/dataset/v2/split_validation_report.md` — 분할·층화·무결성 검증 결과 확인
3. `cat data/processed/dataset_v2/data.yaml` — 클래스 매핑·경로 확인

## 결과

완료 조건 전부 충족. dataset_v2가 정상적으로 구축됐고, dataset_v1은 전혀 건드리지 않았다.
