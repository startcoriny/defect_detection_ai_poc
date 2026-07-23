# 구현 지시서: Smoke Test

## 배경

`docs/context/02-task-list.md` 작업16(Smoke Test)과 `docs/context/03-deliverables.md` 3.7절(`smoke_test.py`)에 따라, 소량 데이터·짧은 Epoch로 학습→검증→체크포인트 생성→추론까지 전체 명령이 실제로 동작하는지 확인한다. 작업17(Baseline 학습) 전 마지막 관문이다.

**참고 — 실험 기록 체계와의 관계**: `docs/context/04-experiment-log-template.md`의 `experiments/EXP-P1-DET-XXX/` 전체 구조(실험 ID, YAML 메타데이터, `experiment_index.csv` 등)는 성능을 비교·추적할 "진짜 실험"을 위한 것이다. 같은 문서 20절의 예시도 `EXP-P1-DET-001`을 Baseline(작업17)으로 들고 있다. Smoke Test는 성능을 측정하거나 비교하지 않고 "학습 명령이 도는가"만 확인하는 일회성 점검이므로, 이번 작업은 `experiments/` 체계를 적용하지 않고 가벼운 `outputs/smoke_test/`에 결과를 남긴다(정식 실험 기록은 작업17부터 시작).

## 기능 및 요구사항

### `src/model/smoke_test.py` (신규)

#### 1. 스모크 데이터 구성 (15장, 복사 없이 경로 목록만 사용)

- `metadata/selected_dataset.csv`에서 `selected=="True"`이고 `split_group=="train"`인 이미지 중, `group` 값이 `normal`/`porosity`/`slag_inclusion`인 것을 각각 `image_name` 오름차순으로 5장씩 골라 총 15장을 구성한다(정상·두 대상 클래스가 모두 포함되도록 함, 무작위 추출 없음).
- 각 이미지의 실제 경로는 `data/processed/dataset_v1/images/train/{image_name}.jpg`(작업14 산출물, 이미 존재)를 그대로 사용한다 — 별도 복사를 하지 않는다.
- 위 15개 이미지의 **절대경로**를 한 줄씩 적은 `outputs/smoke_test/smoke_images.txt`를 생성한다. Ultralytics는 이미지 경로의 `images` 디렉터리를 `labels`로, 확장자를 `.txt`로 바꿔 라벨을 자동으로 찾으므로 별도 라벨 파일 준비가 필요 없다(작업14가 만든 `labels/train/*.txt`가 그대로 매칭됨).

#### 2. `outputs/smoke_test/smoke_data.yaml` 생성

```yaml
path: <프로젝트 루트 절대경로, 슬래시(/) 구분자>
train: outputs/smoke_test/smoke_images.txt
val: outputs/smoke_test/smoke_images.txt
names:
  0: crack
  1: incomplete_penetration
  2: lack_of_fusion
  3: porosity
  4: slag_inclusion
  5: undercut
```

(`names`는 `metadata/yolo_classes.txt`를 그대로 재사용 — 작업14와 동일하게 재계산하지 않는다. Train/Val이 같은 15장인 것은 의도적 — 성능을 측정하려는 게 아니라 학습·검증 두 단계가 실제로 실행되는지만 확인하기 위함이며, 이를 코드 주석으로 명시한다.)

#### 3. 학습 실행

`ultralytics.YOLO`로 프로젝트 루트의 `yolo26n.pt`(이미 존재, 작업1에서 확인됨)를 로드해 다음 설정으로 학습한다:

```
epochs=2
imgsz=640
batch=4
device="cpu"
workers=0          # Windows에서 DataLoader 멀티프로세싱 이슈 회피
seed=42
deterministic=True
patience=50        # 2 epoch에서는 절대 발동하지 않도록 충분히 크게(라이브러리 기본값)
project="outputs/smoke_test/runs"
name="smoke"
exist_ok=True
data="outputs/smoke_test/smoke_data.yaml"
```

학습 도중 예외가 발생하면 예외 메시지와 스택 정보를 그대로 로그에 남기고 실행을 실패시킨다(조용히 넘어가지 않는다 — "오류 해결 기록" 산출물의 근거가 되어야 함).

#### 4. 검증 (학습 결과물 기준으로 확인)

- `outputs/smoke_test/runs/smoke/weights/best.pt`, `last.pt`가 실제로 생성됐는지 확인.
- `outputs/smoke_test/runs/smoke/results.csv`에 Validation 지표 컬럼(`metrics/precision(B)`, `metrics/recall(B)` 등 Ultralytics가 기록하는 컬럼)이 있는지 확인해 "Validation이 실행됨"을 검증.
- `best.pt`를 **디스크에서 다시 로드**해(학습 직후 메모리의 모델 객체를 재사용하지 않고, 실제 저장된 파일이 동작하는지 확인하기 위함) 15장 중 3장으로 `model.predict(..., save=True, project="outputs/smoke_test/runs", name="predict")`를 실행하고, 추론 결과 이미지가 저장됐는지 확인한다.

#### 5. 로그 및 오류 기록

`logging`으로: 스모크 데이터 15장 구성 내역(정상/porosity/slag_inclusion 각 5장), 학습 시작·종료, 각 검증 단계 결과, 최종 판정(`학습 오류 없이 완료 / Validation 실행됨 / 모델 파일 생성됨 / 추론 가능 / Baseline 학습 시작 가능` 5개 항목을 각각 확인·기록).

## 구현 범위 (In Scope)

- `src/model/smoke_test.py` 신규 생성
- `outputs/smoke_test/` 전체(스크립트 실행 결과물 — CODEX가 미리 만들지 않는다)

## 구현 제외 범위 (Out of Scope)

- `experiments/EXP-P1-DET-*/` 전체 구조, `experiment_index.csv` — 작업17(Baseline)부터 적용.
- `train_baseline.py`, `run_inference.py` 등 다른 `src/model/*.py` — 이후 작업 범위.
- `data/processed/dataset_v1/` 수정 — 읽기 전용, 이미지·라벨 복사 없이 경로 목록만 사용.

## 작업 전 반드시 확인해야 하는 문서

- `docs/context/02-task-list.md` 808~844줄(작업16: 수행 작업, 확인할 내용, 산출물, 완료 조건)
- `docs/context/03-deliverables.md` 376~394줄(3.7 학습 및 추론 코드)
- `docs/context/04-experiment-log-template.md` 1~50줄, 1032~1057줄(실험 ID·폴더 구조 — 이번 작업엔 적용하지 않는 이유 확인용)
- `metadata/selected_dataset.csv`(`group`, `split_group` 컬럼), `metadata/yolo_classes.txt`
- `data/processed/dataset_v1/data.yaml`(작업14, 참고용 — 이번엔 새 스모크 전용 yaml을 만든다)
- 프로젝트 루트의 `yolo26n.pt`

## 완료 기준 (Definition of Done)

- ( ) 학습이 오류 없이 끝난다(2 epoch).
- ( ) Validation이 실행된다(`results.csv`에 검증 지표 존재).
- ( ) 모델 파일(`best.pt`, `last.pt`)이 생성된다.
- ( ) 생성된 모델 파일을 다시 로드해 이미지 추론이 가능하다.
- ( ) 위 4가지가 전부 확인되면 "전체 Baseline 학습을 시작할 수 있다"고 로그에 명시한다.
- ( ) 코드가 PEP 8 / black 포맷을 따른다.

## 제약사항

- `ultralytics`, `pyyaml`, 표준 라이브러리만 사용한다(이미 `requirements.txt`에 있음).
- `data/processed/dataset_v1/`, `metadata/`, `yolo26n.pt`는 읽기만 하고 수정하지 않는다.
- 함수/모듈 주석은 한글로 작성한다(프로젝트 관례).
- 이 실행은 CODEX 샌드박스에서 직접 검증할 수 없다(Python 실행 불가 환경) — 코드 작성까지만 CODEX가 담당하고, 실제 실행·결과 확인은 CLAUDE가 `venv/Scripts/python.exe`로 수행한다.

## 테스트 방법 및 검증 기준 (CODEX 완료 후 CLAUDE가 이어서 수행)

1. `venv/Scripts/python.exe src/model/smoke_test.py` 실행(CPU 학습이라 다소 시간이 걸릴 수 있음)
2. 로그에서 학습이 오류 없이 2 epoch를 마쳤는지 확인
3. `outputs/smoke_test/runs/smoke/weights/{best.pt,last.pt}` 존재 확인
4. `outputs/smoke_test/runs/smoke/results.csv`에 Validation 지표 컬럼이 있는지 확인
5. `outputs/smoke_test/runs/predict/`에 추론 결과 이미지가 저장됐는지 확인
6. 로그의 최종 판정 5개 항목이 전부 충족됐는지 확인
7. `docs/context/02-task-list.md` 작업16 완료 조건 5개 충족 여부 확인
