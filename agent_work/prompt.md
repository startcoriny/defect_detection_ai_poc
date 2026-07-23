# 구현 지시서: Confidence Threshold 비교

## 배경

`docs/context/02-task-list.md` 작업22(Confidence Threshold 비교), `docs/context/03-deliverables.md` 3.7절(`compare_thresholds.py`)에 따라, 작업17의 Baseline `best.pt`와 Test 데이터셋을 그대로 두고 Confidence Threshold(0.10/0.25/0.50/0.75)만 바꿔가며 예측 객체 수·TP·FP·FN·Precision·Recall을 비교한다.

**사전 확인한 사실(실제로 실행해 확인함, 가정 아님)**:

- `model.val(data=..., split="test", conf=X, iou=0.70, imgsz=640, plots=True)`를 호출하면 Ultralytics가 자체 IoU 매칭 로직으로 정확한 Precision/Recall/mAP과 **Confusion Matrix**(`metrics.confusion_matrix.matrix`, `(클래스수+1) x (클래스수+1)` 배열, 마지막 행/열이 background)를 계산해준다. `plots=False`면 Confusion Matrix가 전부 0으로 채워진 빈 배열이 반환되므로 **반드시 `plots=True`로 호출**해야 한다.
- 이 방식을 쓰면 TP/FP/FN을 직접 IoU 매칭 코드로 재구현할 필요가 없다 — 이미 검증된 Ultralytics 로직을 그대로 재사용한다(원치 않는 재구현·버그 리스크 회피).
- `model.val(..., project=...)`도 `model.train()`/`model.predict()`와 동일하게 상대경로를 넘기면 `runs/detect/` 하위에 중첩 저장하는 문제가 있다. **반드시 절대경로**를 넘긴다.

## 기능 및 요구사항

### `src/model/compare_thresholds.py` (신규)

#### 1. 입력

- 모델: `experiments/EXP-P1-DET-001/models/best.pt`
- 데이터: `data/processed/dataset_v1/data.yaml`(`split="test"`로 평가)
- 비교할 Threshold: `[0.10, 0.25, 0.50, 0.75]`(다른 설정은 전부 고정 — `iou=0.70`, `imgsz=640`, `device="cpu"`, 작업19와 동일)

#### 2. Threshold별 지표 계산

각 Threshold `t`에 대해:

1. `model.val(data=..., split="test", conf=t, iou=0.70, imgsz=640, device="cpu", plots=True, project=<절대경로>/outputs/threshold-comparison/metrics, name=f"conf_{t}", exist_ok=True, verbose=False)` 호출.
2. `metrics.confusion_matrix.matrix`에서 활성 클래스(`porosity`=id 3, `slag_inclusion`=id 4)만 사용해 다음을 계산한다:
   - 클래스별 `TP = matrix[c][c]`
   - 클래스별 `FP = 그 클래스 행의 합 - TP`(다른 실제 클래스 또는 background를 그 클래스로 잘못 예측한 경우 전부 포함)
   - 클래스별 `FN = 그 클래스 열의 합 - TP`(background로 예측(미탐)됐거나 다른 클래스로 잘못 예측된 경우 전부 포함)
   - 전체 `TP_total = TP_porosity + TP_slag`, `FP_total`, `FN_total`도 같은 방식으로 합산(클래스 혼동 1건이 한쪽엔 FP, 다른 쪽엔 FN으로 동시에 반영되는 것이 의도된 동작이다 — 이중 계산 버그가 아니다).
   - `예측 객체 수 = TP_total + FP_total`
   - `Precision = TP_total / (TP_total + FP_total)`(분모 0이면 값은 `None`/공란으로 남긴다)
   - `Recall = TP_total / (TP_total + FN_total)`
   - `이미지당 평균 자동 라벨 수 = 예측 객체 수 / 46`
   - `삭제해야 하는 오탐 수 = FP_total`, `추가해야 하는 미탐 수 = FN_total`
3. 참고용으로 Ultralytics 자체 지표(`metrics.box.mp`, `metrics.box.mr`, `metrics.box.map50`, `metrics.box.map`)도 같은 행에 함께 기록한다(클래스 평균 기준이라 위 TP/FP/FN 기반 값과는 계산 방식이 다르다는 걸 컬럼명으로 구분).

#### 3. Threshold별 예측 이미지 저장

각 Threshold마다 Test 46장을 개별 파일 경로로 순회하며(작업19와 동일한 개별 처리 패턴 — 실패 격리 목적) `model.predict(source=<단일 이미지>, conf=t, iou=0.70, imgsz=640, device="cpu", save=True, project=<절대경로>/outputs/threshold-comparison/images, name=f"conf_{t}", exist_ok=True)`로 시각화 이미지를 생성한다.

#### 4. 비교표 저장

`reports/evaluation/threshold_comparison.csv` (신규 폴더, 컬럼: `threshold, predicted_count, tp, fp, fn, precision, recall, avg_labels_per_image, fp_to_remove, fn_to_add, ultra_mp, ultra_mr, ultra_map50, ultra_map50_95`), Threshold 오름차순 4행.

## 구현 범위 (In Scope)

- `src/model/compare_thresholds.py` 신규 작성
- `reports/evaluation/threshold_comparison.csv`, `outputs/threshold-comparison/{metrics,images}/conf_<threshold>/` 생성

## 구현 제외 범위 (Out of Scope)

- "오토라벨링 후보 Threshold" 최종 선정과 그 근거 서술 — 실제 수치를 보고 CLAUDE가 판단해 `experiments/EXP-P1-DET-001/experiment.md`의 "12. Threshold 비교" 절에 직접 기록한다(이 스크립트는 원시 비교표만 만든다).
- Ground Truth 없는 이미지 단위 정성 분석(오탐·미탐 사례 상세 검토)은 작업24의 범위.
- 새로운 모델 학습, 다른 Confidence 값 추가 — 지정된 4개 값만 비교한다.

## 작업 전 확인해야 하는 문서/코드

- `docs/context/02-task-list.md` 작업22
- `docs/context/03-deliverables.md` 3.7절
- `src/model/run_inference.py`(작업19 — 개별 이미지 순회·절대경로 `project=` 패턴 재사용)
- `experiments/EXP-P1-DET-001/models/best.pt`, `data/processed/dataset_v1/data.yaml`

## 완료 기준 (Definition of Done)

- `( )` 4개 Threshold 모두 다른 설정(모델·데이터·iou·imgsz·device)은 동일하게 유지된 채 비교됐다.
- `( )` `reports/evaluation/threshold_comparison.csv`에 4개 행(Threshold별 예측 객체 수·TP·FP·FN·Precision·Recall·이미지당 평균 라벨 수) 기록.
- `( )` Threshold별 예측 이미지가 저장된다(`outputs/threshold-comparison/images/conf_<threshold>/`, 각 46장).
- `( )` 코드가 PEP 8 / black 포맷을 따른다(ruff 통과).

## 제약사항

- `experiments/EXP-P1-DET-001/models/best.pt`, `data/processed/dataset_v1/`은 읽기만 하고 수정하지 않는다.
- `project=`에는 반드시 절대경로를 사용한다(상대경로 시 중첩 저장 버그, 사전 확인함).
- `model.val()`은 `plots=True`로 호출한다(그렇지 않으면 Confusion Matrix가 비어있음, 사전 확인함).
- 이 스크립트는 CODEX 샌드박스에서 직접 실행·검증할 수 없다(Python 실행 불가, 알려진 제약). 코드 작성까지만 CODEX가 담당하고, 실제 실행·결과 확인은 CLAUDE가 `venv/Scripts/python.exe`로 수행한다.

## 테스트 방법

1. `venv/Scripts/python.exe src/model/compare_thresholds.py` 실행
2. `reports/evaluation/threshold_comparison.csv` — 4행, Threshold가 커질수록 Precision은 오르고 Recall은 내려가는 일반적 경향을 보이는지 확인(반례가 있으면 왜 그런지 원인 확인 필요)
3. `outputs/threshold-comparison/images/conf_0.10/`, `conf_0.25/`, `conf_0.50/`, `conf_0.75/` — 각 46장 존재, Threshold가 높을수록 박스 수가 줄어드는지 육안 확인
4. `black --check src/model/compare_thresholds.py`, `ruff check src/model/compare_thresholds.py` 통과 확인
