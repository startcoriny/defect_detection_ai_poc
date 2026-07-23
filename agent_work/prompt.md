# 구현 지시서: Baseline 모델 학습

## 배경

`docs/context/02-task-list.md` 작업17(Baseline 모델 학습), `docs/context/03-deliverables.md` 3.7절(`train_baseline.py`), `docs/context/04-experiment-log-template.md`에 따라, `data/processed/dataset_v1/`(작업14~15에서 만들고 검증한 데이터셋) 전체로 처음 진짜 성능을 측정하는 Baseline 학습을 실행하고, 이번 작업부터 정식 실험 기록 체계(`experiments/EXP-P1-DET-001/`)를 시작한다.

**실험 식별**: `docs/context/04-experiment-log-template.md`가 이미 예시로 제시한 `실험 ID: EXP-P1-DET-001`, `실험명: RT_AL_YOLO26N_640_Baseline`을 그대로 사용한다(새로 이름을 짓지 않는다).

**gitignore 정책(사용자 확인 완료)**: `.gitignore`에 이미 `*.pt`, `experiments/*/{logs,models,predictions,visualizations,errors}/`를 제외하는 규칙이 있다. 이 규칙을 그대로 유지한다 — `experiment.md`, `experiment.yaml`, `train_config.yaml`, `environment.txt`, `dataset_summary.csv`(experiment 폴더 최상위, 텍스트/CSV)만 git에 커밋되고, `logs/`, `models/`(`best.pt`/`last.pt` 포함), `visualizations/`는 재현 가능한 산출물로 남기되 커밋하지 않는다.

## 기능 및 요구사항

### `src/model/train_baseline.py` (신규)

#### 1. 실험 폴더 준비

```
experiments/EXP-P1-DET-001/
├── experiment.md
├── experiment.yaml
├── train_config.yaml
├── environment.txt
├── dataset_summary.csv
├── logs/
│   └── train.log
├── models/
│   ├── best.pt
│   └── last.pt
└── visualizations/
    ├── results.png
    └── confusion_matrix.png
```

#### 2. 학습 실행

`data/processed/dataset_v1/data.yaml`(작업14 산출물, 그대로 재사용)로 `yolo26n.pt`(프로젝트 루트, 이미 존재)를 다음 설정으로 학습한다:

```
epochs=50
patience=15
imgsz=640
batch=-1          # "자동 결정" 요구사항 — CPU에서는 Ultralytics가 WARNING과 함께 기본값 16으로 대체함(실제 로그로 확인됨). 이 동작을 그대로 둔다.
device="cpu"
workers=0         # Windows DataLoader 멀티프로세싱 이슈 회피(작업16과 동일 이유)
cache=True        # CPU 환경에서 반복 50 epoch 속도를 위해 이미지 캐싱
seed=42
deterministic=True
optimizer="auto"
project=<프로젝트 루트 기준 절대경로>/experiments/EXP-P1-DET-001/runs   # 반드시 절대경로로 넘길 것 — 상대경로를 넘기면 Ultralytics가 자체 기본 project 아래에 중첩시키는 문제가 실제로 발생함(확인됨)
name="train"
exist_ok=True
```

학습 콘솔 출력을 `experiments/EXP-P1-DET-001/logs/train.log`에도 그대로 남긴다(`logging.FileHandler` + `logging.StreamHandler`, 작업16과 동일 패턴).

학습 중 예외가 발생하면 로그에 스택과 함께 남기고 실행을 실패시킨다(조용히 넘어가지 않는다).

#### 3. 산출물 정리

- `experiments/EXP-P1-DET-001/runs/train/weights/{best.pt,last.pt}`를 `experiments/EXP-P1-DET-001/models/`로 복사.
- `experiments/EXP-P1-DET-001/runs/train/results.png`, `confusion_matrix.png`를 `experiments/EXP-P1-DET-001/visualizations/`로 복사(Ultralytics가 자동 생성 — 직접 그리지 않는다. `results.png`가 Loss 그래프와 평가 그래프를 함께 담고 있다).
- Ultralytics가 자동 생성하는 `experiments/EXP-P1-DET-001/runs/train/args.yaml`을 `experiments/EXP-P1-DET-001/train_config.yaml`로 복사(직접 손으로 작성하지 않는다 — 실제 사용된 전체 설정이 이미 여기 담겨 있음).

#### 4. `environment.txt` 생성

`configs/environment/environment_info.txt`와 `configs/environment/package_versions.txt`(작업1 산출물, 재사용)를 이어붙여 `experiments/EXP-P1-DET-001/environment.txt`로 저장한다. 새로 환경을 스캔하지 않는다(동일 머신·동일 venv이므로 재사용).

#### 5. `dataset_summary.csv` 생성

`reports/dataset/split_distribution.csv`(작업13/14, 재사용)를 그대로 복사해 `experiments/EXP-P1-DET-001/dataset_summary.csv`로 저장한다(분할×표준클래스 6개, 재계산 없음).

#### 6. `experiment.yaml` 생성

`docs/context/04-experiment-log-template.md` 19절 YAML 스키마를 따라 다음 값을 실제 값으로 채운다:

- `experiment.id`: `EXP-P1-DET-001`, `experiment.name`: `RT_AL_YOLO26N_640_Baseline`, `status`: 학습 성공 시 `completed`(실패 시 `failed`), `type`: `detection_training`
- `experiment.started_at`/`ended_at`: 학습 시작·종료 시각(ISO 8601)
- `experiment.git_commit`: `git rev-parse HEAD`로 실행 시점의 커밋 해시를 얻어 기록(subprocess 사용)
- `dataset.image_count`: `data/processed/dataset_v1/images/{train,val,test}/*.jpg` 개수를 직접 세어 채운다(작업14/15와 같은 값이어야 하지만, 이 스크립트도 독립적으로 다시 셈)
- `dataset.classes`: `metadata/class_statistics.csv`에서 이번 데이터셋에 실제 객체가 있는 클래스만(=`porosity`: 3, `slag_inclusion`: 4) 기재
- `training.actual_batch`: `experiments/EXP-P1-DET-001/runs/train/args.yaml`에서 실제 사용된 `batch` 값을 읽어 채운다(자동 결정 결과)
- `metrics`: `experiments/EXP-P1-DET-001/runs/train/results.csv`의 마지막 행에서 `metrics/precision(B)`, `metrics/recall(B)`, `metrics/mAP50(B)`, `metrics/mAP50-95(B)` 값을 읽어 채운다
- `inference`: 이번 작업 범위 밖이므로 `confidence`/`iou`/`imgsz`는 전부 `null`로 남긴다(작업19에서 채움)
- `artifacts`: `best_model`/`last_model`/`results_directory`를 실제 경로로 채우고, `prediction_json`/`evaluation_report`는 `null`
- `conclusion`: 전부 `null`/`false`(이번 작업 범위 밖, 작업18 이후에서 채움)

#### 7. `experiment.md` 생성

`docs/context/04-experiment-log-template.md` 3~9절 구조를 따라 다음 섹션을 실제 값으로 채운다(23절의 Baseline 예시 문구를 뼈대로 재사용해도 좋다):

- 1절(실험 기본 정보), 2절(목적과 가설 — 예시 문구 그대로 사용 가능), 3절(기준 실험: 없음, 최초 Baseline), 5절(데이터셋 정보 — `dataset_summary.csv`/`environment.txt`와 일치해야 함), 6절(전처리·변환 정보 — Polygon→Box는 작업9, YOLO 변환은 작업10 참조, 이미지 Resize는 Ultralytics 기본 letterbox·라이브러리 기본값이라고 명시), 7절(실행 환경 — `environment.txt` 값 재사용), 8절(모델 및 학습 설정 — 이번 학습에 실제 사용한 값, 증강 설정은 커스터마이징하지 않았으므로 표 전체에 "library default"라고 명시하되 `args.yaml`에서 실제 값도 함께 적음), 9절(학습 실행 결과 — 시작/종료 시각, 총 소요시간, Early Stopping 발동 여부, best/최종 Epoch, 모델 경로, Best/Last의 Precision/Recall/mAP50/mAP50-95)
- 10절 이후(추론 설정, 전체·클래스별 성능, Threshold 비교, 정성 평가, 원인 분석, Baseline 비교, 결론, 다음 실험 계획)는 이번 작업 범위가 아니므로 각 섹션 제목만 남기고 본문은 `실험 후 작성(작업18~25에서 채움)`이라고 명시한다 — 파일을 나중에 다시 열어 이어 쓸 수 있도록 섹션 골격은 미리 만들어 둔다.

## 구현 범위 (In Scope)

- `src/model/train_baseline.py` 신규 생성
- `experiments/EXP-P1-DET-001/` 전체(스크립트 실행 결과물 — CODEX가 미리 만들지 않는다)

## 구현 제외 범위 (Out of Scope)

- `run_inference.py`, `export_auto_labels.py`, `compare_thresholds.py` — 이후 작업 범위.
- `experiment_index.csv`(전체 실험 목록 관리) — 실험이 1개뿐인 지금 단계에서는 과잉이므로 만들지 않는다. 두 번째 실험이 생길 때(비교 실험 시작 시) 도입 여부를 다시 판단한다.
- `data/processed/dataset_v1/`, `metadata/`, `reports/dataset/`, `configs/environment/` 등 기존 산출물 수정 — 전부 읽기 전용.

## 작업 전 반드시 확인해야 하는 문서

- `docs/context/02-task-list.md` 848~891줄(작업17: 수행 조건, 기록 항목, 산출물, 완료 조건)
- `docs/context/03-deliverables.md` 376~394줄(3.7 학습 및 추론 코드)
- `docs/context/04-experiment-log-template.md` 전체(특히 3~9절 양식, 19절 YAML 스키마, 20절 폴더 구조, 23절 Baseline 예시)
- `.gitignore`(실험 폴더 관련 규칙)
- `data/processed/dataset_v1/data.yaml`, `metadata/yolo_classes.txt`, `metadata/class_statistics.csv`, `reports/dataset/split_distribution.csv`
- `configs/environment/{environment_info.txt,package_versions.txt}`
- `src/model/smoke_test.py`(작업16) — 로깅·경로 처리 패턴 재사용

## 완료 기준 (Definition of Done)

- ( ) 학습이 정상 종료됐다(50 epoch 완주 또는 Early Stopping으로 정상 종료 — 예외로 인한 비정상 종료가 아님).
- ( ) `best.pt`와 `last.pt`가 생성됐다.
- ( ) 전체 학습 설정이 기록됐다(`train_config.yaml` = Ultralytics `args.yaml` 그대로).
- ( ) 학습 로그를 다시 확인할 수 있다(`logs/train.log`).
- ( ) 결과 폴더가 실험 ID(`EXP-P1-DET-001`) 기준으로 보존된다.
- ( ) 코드가 PEP 8 / black 포맷을 따른다.

## 제약사항

- `ultralytics`, `pyyaml`, 표준 라이브러리만 사용한다.
- `data/processed/dataset_v1/`, `metadata/`, `reports/`, `configs/` 아래 기존 파일은 읽기만 하고 수정하지 않는다.
- 함수/모듈 주석은 한글로 작성한다(프로젝트 관례).
- 이 실행은 CODEX 샌드박스에서 직접 검증할 수 없다(Python 실행 불가) — 코드 작성까지만 CODEX가 담당하고, 실제 학습 실행·결과 확인은 CLAUDE가 `venv/Scripts/python.exe`로 수행한다. **CPU로 50 epoch·209장을 학습하므로 상당한 시간이 걸릴 수 있음을 감안한다.**

## 테스트 방법 및 검증 기준 (CODEX 완료 후 CLAUDE가 이어서 수행)

1. `venv/Scripts/python.exe src/model/train_baseline.py` 실행(백그라운드, 장시간 소요 가능)
2. 로그에서 학습이 오류 없이 끝났는지, 몇 epoch에서 종료됐는지(Early Stopping 여부) 확인
3. `experiments/EXP-P1-DET-001/models/{best.pt,last.pt}` 존재 확인
4. `experiments/EXP-P1-DET-001/train_config.yaml`(=`args.yaml`)에 실제 설정이 그대로 담겼는지 확인
5. `experiments/EXP-P1-DET-001/logs/train.log`로 학습 과정을 다시 확인할 수 있는지 확인
6. `experiments/EXP-P1-DET-001/experiment.yaml`의 `metrics`/`training.actual_batch`/`git_commit` 값이 실제 결과와 일치하는지 확인
7. `experiments/EXP-P1-DET-001/experiment.md`가 9절까지 채워지고 10절 이후는 "실험 후 작성"으로 골격만 있는지 확인
8. `docs/context/02-task-list.md` 작업17 완료 조건 5개 충족 여부 확인
