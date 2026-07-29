# 구현 지시서: GPU 학습 속도 비교 실험 스크립트 (EXP-P1-DET-008)

## 배경

`EXP-P1-DET-005`(CPU, YOLO26n, dataset_v3, SlagOversample)는 완료된 최종 Baseline이다. 이번 요청은 동일한 학습 설정을 GPU 장비에서 재실행해 CPU 대비 학습 속도를 비교하기 위한 새 실험 스크립트를 만드는 것이다.

사용자는 프로젝트 전체 폴더를 그대로 복사해 별도의 GPU 서버(Linux/Ubuntu, NVIDIA 드라이버는 이미 설치됨, Python·venv·패키지는 전혀 없는 빈 상태, Claude Code 없음)로 옮겨 혼자 수동으로 실행한다. 따라서 이번 지시서는 두 가지 산출물을 요구한다.

1. GPU 서버에서 Python 가상환경부터 GPU 지원 PyTorch까지 셋업하는 bash 스크립트
2. EXP-005와 `device`만 다르게 재현하는 학습 스크립트

비교 변수는 `device` 단 하나여야 한다. 그 외 하이퍼파라미터(dataset, epochs, patience, imgsz, batch, seed, deterministic 등)는 EXP-005와 동일하게 유지해 순수 하드웨어 비교가 되도록 한다.

## A. GPU 서버 부트스트랩 스크립트 (`setup_gpu_env.sh`, 저장소 루트에 신규 작성)

사용자가 프로젝트 폴더를 복사한 직후 GPU 서버(Ubuntu, NVIDIA 드라이버 설치됨, 그 외 아무것도 없음)에서 가장 먼저 실행할 bash 스크립트다. `#!/usr/bin/env bash`와 `set -euo pipefail`로 시작하고, 첫 줄에 스크립트 역할을 설명하는 한 줄 한국어 주석을 둔다. 아래 단계를 순서대로 수행한다.

1. **드라이버 확인 (정보 출력만)**
   - `nvidia-smi`를 실행해 그대로 출력한다. 실패하면(드라이버 없음) 즉시 에러 메시지와 함께 스크립트를 중단한다.
   - `nvidia-smi` 출력 상단의 `CUDA Version`은 사용자가 눈으로 읽고 스크립트 상단의 `CUDA_TAG` 변수를 스스로 맞추게 한다(자동 파싱하지 않는다 — 드라이버·wheel 호환 매핑은 시점에 따라 바뀌므로 자동화보다 사용자 확인이 안전하다).
   - 스크립트 최상단에 `CUDA_TAG="cu128"` 형태의 변수를 두고, 바로 위에 "nvidia-smi의 CUDA Version을 보고 필요하면 이 값을 cu121/cu124/cu126 등으로 바꾸세요"라는 주석을 남긴다. (실제 대상 서버는 `CUDA Version: 13.2` 드라이버로 확인됨 — 드라이버가 지원하는 상한이므로 이보다 낮은 CUDA 빌드 wheel은 모두 호환된다. `cu128`은 그 중 비교적 최신 wheel 기준의 기본값이며, 설치 시점에 해당 torch 버전의 wheel이 실제로 배포되는지 확인 후 조정한다.)

2. **Python 3.13 확인 및 설치**
   - `python3.13 --version`으로 존재 여부를 확인한다.
   - 없으면 `add-apt-repository ppa:deadsnakes/ppa`를 통해 `python3.13`, `python3.13-venv`를 설치한다(이 프로젝트의 검증된 Python 버전은 3.13이다 — `configs/environment/environment_info.txt` 참고). 대상 서버는 Ubuntu 22.04.5 LTS(jammy)로 확인됐고, deadsnakes PPA는 22.04를 공식 지원한다.

3. **가상환경 생성**
   - 저장소 루트에 `venv/`가 이미 있으면 생성을 건너뛰고, 없으면 `python3.13 -m venv venv`로 만든다(기존 CPU 머신과 동일하게 폴더명 `venv` 사용, `docs/context/02-task-list.md` 작업1 컨벤션과 일치).
   - 이후 모든 pip 명령은 이 venv 안에서 실행한다.

4. **GPU 지원 PyTorch 설치 (requirements.txt보다 먼저)**
   - `pip install torch==2.13.0 torchvision==0.28.0 --index-url https://download.pytorch.org/whl/${CUDA_TAG}` (버전은 `configs/environment/package_versions.txt`에 기록된 값과 동일하게 맞춰 재현성을 유지한다).
   - 이 설치가 requirements.txt 설치보다 반드시 먼저 실행되어야 한다는 점을 주석으로 남긴다(순서가 바뀌면 CPU 전용 wheel로 덮어써질 수 있다).

5. **나머지 의존성 설치**
   - `pip install -r requirements.txt` (torch/torchvision은 버전 제약이 없으므로 이미 설치된 GPU 빌드가 유지된다).

6. **GPU 인식 검증 (fail-fast)**
   - `python src/check_environment.py`를 실행하고 출력에서 `CUDA Available : Yes`를 확인한다.
   - `No`이거나 스크립트가 실패하면, "CUDA_TAG를 확인하고 다시 실행하라"는 안내 메시지와 함께 0이 아닌 코드로 종료한다. 조용히 넘어가지 않는다.

7. **다음 단계 안내**
   - 마지막에 `echo`로 "다음: python src/model/smoke_test.py 로 스모크 테스트 → python src/model/exp8/train_baseline.py 실행"을 출력한다.

## B. 학습 스크립트 (`src/model/exp8/train_baseline.py`)

`src/model/exp5/train_baseline.py`를 새 폴더 `src/model/exp8/train_baseline.py`로 복사한 뒤 아래 사항만 변경한다.

1. **실험 식별자**
   - `EXPERIMENT_ID = "EXP-P1-DET-008"`
   - `EXPERIMENT_NAME = "RT_AL_YOLO26N_960_GPUDeviceComparison"`
   - 모듈 docstring은 그대로 두되(YOLO26n Baseline), 필요시 "GPU 비교" 문구를 덧붙여도 된다.

2. **device 변경 및 fail-fast 검증**
   - `model.train(...)` 호출의 `device="cpu"`를 `device="0"`으로 변경한다.
   - 학습 시작 전 `torch.cuda.is_available()`을 확인하고, `False`이면 즉시 `RuntimeError`로 중단한다(메시지: GPU를 찾을 수 없어 이 실험을 CPU로 대체 실행하면 비교 목적이 무효화된다는 취지). 조용히 CPU로 폴백되는 상황을 반드시 막아야 한다.
   - `main()`의 실패 처리 흐름(`except Exception` 블록에서 `experiment.yaml`을 `status="failed"`로 기록)은 기존 그대로 재사용한다.

3. **실행 환경 정보를 실행 시점에 캡처(기존 정적 파일 복사 방식 대체)**
   - 기존 `prepare_experiment_files()`는 `configs/environment/environment_info.txt`, `package_versions.txt`를 그대로 복사한다. 이 두 파일은 작업1 때 CPU 머신에서 캡처된 값이라 GPU 머신에는 맞지 않는다.
   - `src/check_environment.py`의 `print_system_information`/`print_device_information`과 동일한 조회 로직(Python 버전, OS, CPU, RAM, CUDA 사용 가능 여부, GPU 이름/VRAM, torch/ultralytics 버전)을 재사용해 실행 시점 환경 텍스트를 만들고 `experiment_dir / "environment.txt"`에 직접 쓴다. 정적 파일 복사 코드는 제거한다.
   - `dataset_summary.csv` 복사 로직(`reports/dataset/v2/split_distribution.csv` → `experiment_dir/dataset_summary.csv`)은 그대로 유지한다(dataset_v3는 동일).

4. **목적/가설/기준실험 서술 변경**
   - `build_experiment_data()`의 `purpose` 딕셔너리와 `write_experiment_markdown()`의 "# 2. 목적과 가설", "# 3. 기준 실험" 절 텍스트를 GPU/CPU 속도 비교 취지로 수정한다.
     - 목적: EXP-P1-DET-005와 동일 설정(dataset_v3, YOLO26n, epochs=50 등)을 GPU에서 재학습해 CPU 대비 학습 속도를 비교한다.
     - 가설: device 외 모든 설정이 동일할 때 GPU 학습이 CPU 학습(EXP-005)보다 유의미하게 빠르게 완료된다.
     - 기준 실험: `EXP-P1-DET-005` (동일 설정, device=cpu).
   - `build_experiment_data()`의 `"training": {"device": "cpu", ...}` 리터럴을 `"device": "0"`으로 변경한다.
   - `"9.1 학습 결과 요약"` 표와 총 실행 시간(`format_duration`) 출력 로직은 그대로 유지한다(이 실험의 핵심 산출물이 실행 시간이다).

5. **문서에 EXP-005 대비 비교 섹션 추가**
   - `write_experiment_markdown()` 끝부분(기존 `DEFERRED_SECTIONS` 앞)에 짧은 절 하나를 추가한다: `# 9.2 CPU Baseline 대비 비교` — `EXP-P1-DET-005`의 총 실행 시간을 하드코딩 상수로 두고(experiments/EXP-P1-DET-005/experiment.md의 "총 실행 시간" 값을 그대로 가져와 상수화), 이번 GPU 실행 시간과 나란히 표로 비교한다. 배속(倍速) 계산은 `CPU 시간(초) / GPU 시간(초)`로 표시한다.

## 참고해야 할 문서/코드

- `src/model/exp5/train_baseline.py` (복사 원본, 전체 구조와 실패 처리 흐름 그대로 따를 것)
- `src/check_environment.py` (환경 캡처 로직 재사용, 부트스트랩 스크립트의 검증 단계에서도 그대로 실행)
- `configs/environment/environment_info.txt`, `package_versions.txt` (CPU 머신에서 검증된 Python/torch/torchvision 버전 — GPU 설치 시 동일 버전 유지)
- `experiments/EXP-P1-DET-005/experiment.md` (기존 baseline 실행 시간, 비교 텍스트 작성 시 참조)
- `data/processed/dataset_v3/data.yaml` (데이터 경로, 변경 없음)
- `docs/context/02-task-list.md` 작업1 (가상환경 폴더명·설치 패키지 목록 컨벤션)

## 구현 제외 범위 (Out of Scope)

- `src/evaluation/exp8/*`, `src/model/exp8/run_inference.py`, `compare_thresholds.py` 등 추론·임계값·오류사례 분석 스크립트는 만들지 않는다. 이번 요청은 학습 속도 비교까지가 범위다.
- `src/model/smoke_test.py`는 수정하지 않는다.
- `configs/environment/environment_info.txt`, `package_versions.txt` 등 기존 정적 파일은 수정하지 않는다(참조만 하고, exp8 학습 스크립트가 복사하지 않게 코드만 바꾼다).
- `setup_gpu_env.sh`는 CUDA_TAG 자동 판별을 시도하지 않는다(사용자가 `nvidia-smi` 출력을 보고 직접 값을 맞춘다).
- Docker, conda 등 다른 환경 관리 도구는 다루지 않는다. venv + pip만 사용한다.
- EXP-009(이후 GPU 활용 개선 실험)는 이번 지시서 범위가 아니다.

## 완료 기준 (Definition of Done)

- `setup_gpu_env.sh`가 저장소 루트에 존재하고 `bash -n setup_gpu_env.sh`(문법 검사)를 통과한다. `shellcheck`이 있으면 함께 통과한다.
- `src/model/exp8/train_baseline.py`가 존재하고 `python -m py_compile`(또는 동등한 문법 검사)을 통과한다.
- `black`, `ruff` 검사를 통과한다(`train_baseline.py`에 한함, 셸 스크립트는 대상 아님).
- 이 저장소(CPU 전용, Windows)에서는 GPU도 Linux 셸도 없어 실제 실행으로 검증할 수 없다. 대신 다음을 정적으로 확인한다.
  - `setup_gpu_env.sh`가 A절 1~7 단계를 순서대로 포함하고, GPU 미검증 시 0이 아닌 코드로 종료하는 분기가 있다.
  - `device="0"`으로 변경되었고, CUDA 미탐지 시 즉시 예외를 던지는 코드 경로가 있다.
  - 환경 캡처 로직이 정적 파일 복사가 아니라 실행 시점 조회로 바뀌었다.
  - exp5와 diff했을 때 위 1~5 항목 외의 의도치 않은 변경이 없다(`diff src/model/exp5/train_baseline.py src/model/exp8/train_baseline.py`로 확인).
- 실제 실행 검증(부트스트랩 + 학습)은 사용자가 GPU 서버에서 직접 수행한다. 사용자에게는 다음을 안내한다.
  - `bash setup_gpu_env.sh` 실행 → `CUDA Available : Yes` 확인.
  - 전체 실행 전 `python src/model/smoke_test.py`(또는 exp8 스크립트를 짧은 epoch로) 먼저 돌려 파이프라인이 정상 동작하는지 확인할 것.
  - `data/processed/dataset_v3/`, `yolo26n.pt`는 프로젝트 폴더를 그대로 복사했다면 이미 포함되어 있어야 한다(별도 다운로드 불필요).

## 제약사항

- `docs/context/03-deliverables.md`의 모듈 구조(실험별 `src/model/expN/`)를 따른다.
- 파일 헤더/주석 스타일은 exp5와 동일한 컨벤션(함수별 한 줄 한국어 주석, 상단 모듈 docstring)을 유지한다.
- `setup_gpu_env.sh`도 첫 줄(shebang 다음)에 스크립트 역할을 설명하는 한 줄 한국어 주석을 둔다. `set -euo pipefail`을 사용해 중간 실패 시 조용히 넘어가지 않는다.
- 예외를 삼키지 않는다(기존 exp5의 `except Exception` 처리 방식 유지, 실패 원인이 로그와 `experiment.yaml`에 남도록 한다).
