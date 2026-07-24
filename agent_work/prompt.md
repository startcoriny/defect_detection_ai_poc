# 구현 지시서: 모델 성능 평가

## 배경

`docs/context/02-task-list.md` 작업23(모델 성능 평가), `docs/context/03-deliverables.md`(`src/evaluation/` 모듈, `docs/commands.md` 예시 `python src/evaluation/calculate_metrics.py`)에 따라, Baseline `best.pt`를 Confidence 0.25(작업22에서 유지하기로 한 후보값)로 고정해 Test 46장에 대한 공식 평가를 수행한다.

**평가 IoU 기준**: 문서에 구체적 숫자가 없어, mAP50이 이미 이 프로젝트 전체에서 핵심 지표로 계속 쓰여온 점(작업17~22)과 일관되게 **IoU 0.5**를 매칭 기준으로 사용한다(새 값을 임의로 만들지 않는다).

**"객체 크기별 성능"은 Ultralytics가 기본 제공하지 않는다** — `model.val()`은 전체·클래스별 지표는 주지만 객체 크기(Small/Medium/Large)로 나눈 지표는 없다. 이 부분만 직접 IoU 매칭을 구현해야 한다(그 외 전체·클래스별 지표는 기존처럼 Ultralytics를 그대로 재사용한다).

## 기능 및 요구사항

### `src/evaluation/calculate_metrics.py` (신규)

#### 1. 전체·클래스별 지표 (Ultralytics 재사용, 재구현 금지)

`model.val(data="data/processed/dataset_v1/data.yaml", split="test", conf=0.25, iou=0.70, imgsz=640, device="cpu", plots=True, project=<절대경로>, name="evaluation", exist_ok=True)` 1회 호출로 다음을 얻는다:

- 전체: `metrics.box.mp`(Precision), `metrics.box.mr`(Recall), `metrics.box.map50`, `metrics.box.map`(=mAP50-95)
- 클래스별: `metrics.box.p`, `metrics.box.r`, `metrics.box.ap50`, `metrics.box.ap`(배열, `metrics.ap_class_index`로 클래스 ID와 매칭 — 활성 클래스만 포함되므로 `metadata/yolo_classes.txt`로 이름 변환)
- Confusion Matrix: `metrics.confusion_matrix`(작업22와 동일한 방식), 이미지는 `model.val()`이 `plots=True`일 때 `<project>/evaluation/confusion_matrix.png`에 자동 저장하므로 그대로 둔다(다시 그리지 않는다).

#### 2. 객체 크기별 성능 (직접 구현)

작업12에서 이미 정한 기준을 그대로 재사용한다: `Small: relative_area<0.01`, `Medium: 0.01~0.05`, `Large: >=0.05`(`relative_area = 정규화 width * height`, 새로 정의하지 않는다).

절차:

1. `data/processed/dataset_v1/labels/test/*.txt`(YOLO 형식, 46개 — 없는 파일은 없어야 함)를 읽어 이미지별 GT 객체 목록(class_id, 정규화 xywh, `relative_area = w*h`, 크기 버킷)을 만든다.
2. Test 이미지 46장을 개별 파일 경로로 순회하며(작업19~22와 동일한 개별 처리 패턴) `model.predict(source=<단일 이미지>, conf=0.25, iou=0.70, imgsz=640, device="cpu")`로 예측을 얻는다(실제 배포 경로와 동일한 single-label 방식 — 작업22에서 확인한 `val()`의 multi-label 방식과 섞지 않는다).
3. 이미지마다 GT와 Prediction을 IoU 0.5·클래스 일치 기준으로 매칭한다(그리디: Confidence 높은 예측부터, 같은 클래스의 아직 안 매칭된 GT 중 IoU가 가장 높고 0.5 이상인 것과 매칭 → TP, 매칭 실패 → FP). IoU는 픽셀 좌표로 변환해 계산한다(예측은 `result.boxes.xyxy`로 이미 픽셀 좌표, GT는 `result.orig_shape`(이미지 높이·너비, 이미 예측 결과에 포함되어 있으므로 이미지를 다시 읽지 않는다)로 정규화 좌표를 픽셀로 변환).
4. 매칭된 GT(TP)는 그 GT의 크기 버킷에 집계하고, 매칭 안 된 GT(FN)도 그 GT의 크기 버킷에 집계한다. 버킷별 `Recall = TP / (TP + FN)`을 계산한다(FP는 배경에 대한 오탐이라 크기 버킷이 없으므로, 버킷별 결과는 Recall 위주로 보고한다 — Precision을 억지로 버킷에 끼워 맞추지 않는다).
5. `reports/evaluation/object_size_performance.csv`(컬럼: `size_bucket, gt_count, tp, fn, recall`)로 저장.

#### 3. 산출물 저장

- `reports/evaluation/model_performance.csv`(컬럼: `scope, class_name, precision, recall, ap50, ap50_95` — `scope`는 `overall` 1행 + 활성 클래스별 행)
- `reports/evaluation/object_size_performance.csv`(2번 결과)
- Confusion Matrix는 `model.val()`이 자동 저장한 파일 경로를 로그로 남긴다(복사만 하고 다시 그리지 않는다).

## 구현 범위 (In Scope)

- `src/evaluation/calculate_metrics.py` 신규 작성
- `reports/evaluation/{model_performance.csv, object_size_performance.csv}` 생성

## 구현 제외 범위 (Out of Scope)

- "평가 보고서 초안"(정성적 해석·결론 서술)은 실제 수치를 보고 CLAUDE가 판단해 `experiments/EXP-P1-DET-001/experiment.md`의 "11. 전체·클래스별 성능" 절에 직접 작성한다(이 스크립트는 원시 수치만 만든다).
- 오탐·미탐 개별 사례 조사(작업24의 범위).
- 새로운 모델 학습, Threshold 변경(작업22에서 이미 확정한 0.25 고정).

## 작업 전 확인해야 하는 문서/코드

- `docs/context/02-task-list.md` 작업23
- `src/model/compare_thresholds.py`(작업22 — `model.val()` Confusion Matrix 재사용 패턴)
- `src/model/run_inference.py`(작업19 — 개별 이미지 순회 패턴)
- `src/data/analyze_statistics.py`(작업12 — 객체 크기 버킷 기준 원출처)
- `data/processed/dataset_v1/labels/test/`, `metadata/yolo_classes.txt`

## 완료 기준 (Definition of Done)

- `( )` 전체 지표(Precision/Recall/mAP50/mAP50-95)가 저장된다.
- `( )` 클래스별 지표(Precision/Recall/AP50/AP50-95)가 저장된다.
- `( )` 객체 크기별(Small/Medium/Large) Recall이 저장된다.
- `( )` Confusion Matrix 이미지 경로가 로그에 남는다.
- `( )` 코드가 PEP 8 / black 포맷을 따른다(ruff 통과).

## 제약사항

- `experiments/EXP-P1-DET-001/models/best.pt`, `data/processed/dataset_v1/`은 읽기만 하고 수정하지 않는다.
- `project=`에는 반드시 절대경로를 사용한다(기존에 반복 확인된 상대경로 버그).
- 객체 크기별 매칭에 쓰는 `model.predict()`는 반드시 개별 이미지 단위로 호출한다(multi-label 평가 방식과 섞이지 않도록, 작업22에서 확인한 차이를 반영).
- 이 스크립트는 CODEX 샌드박스에서 직접 실행·검증할 수 없다(Python 실행 불가). 코드 작성까지만 CODEX가 담당하고, 실제 실행·결과 확인은 CLAUDE가 `venv/Scripts/python.exe`로 수행한다.

## 테스트 방법

1. `venv/Scripts/python.exe src/evaluation/calculate_metrics.py` 실행
2. `reports/evaluation/model_performance.csv` — `overall` 행 + 활성 클래스(porosity, slag_inclusion) 행 확인
3. `reports/evaluation/object_size_performance.csv` — Small/Medium/Large 3행, `gt_count` 합이 58(Test 전체 객체 수)과 같은지 확인
4. 로그에서 Confusion Matrix 이미지 경로 확인
5. `black --check src/evaluation/calculate_metrics.py`, `ruff check src/evaluation/calculate_metrics.py` 통과 확인
