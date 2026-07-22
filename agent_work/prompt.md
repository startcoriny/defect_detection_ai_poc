# 구현 지시서: 개발 환경 구성 (작업 1)

## 배경

현재 저장소에는 실행 가능한 최소 스켈레톤(`main.py`)만 있고, 실제 파이프라인 코드를 작성하기 위한 Python 패키지 목록과 환경 확인 스크립트가 없다. `docs/context/02-task-list.md` 작업1(개발 환경 구성)을 기준으로, 이후 모든 데이터/모델 작업의 전제가 되는 실행 환경 구성 코드를 작성한다.

이 저장소가 개발되는 머신에는 이미 Python 3.13.14가 설치되어 있다 (새 버전 설치 불필요).

## 기능 및 요구사항

1. `requirements.txt` (저장소 루트) — 아래 패키지를 이름만 명시한다 (버전 고정 없음. 실제 설치된 버전은 이후 `package_versions.txt`에 기록된다).
   - torch
   - torchvision
   - ultralytics
   - opencv-python
   - numpy
   - pandas
   - matplotlib
   - pyyaml

2. `src/check_environment.py` — 실행하면 아래 정보를 사람이 읽을 수 있는 텍스트로 표준출력에 출력한다.
   - Python 버전
   - OS, CPU, RAM 정보
   - GPU 사용 가능 여부(`torch.cuda.is_available()`) — 가능하면 GPU 이름과 VRAM, 불가능하면 "CPU"로 표시
   - 주요 패키지 import 성공 여부 (torch, ultralytics, cv2, numpy, pandas, matplotlib, yaml) — 하나라도 import 실패 시 어떤 패키지가 실패했는지 표준에러에 명확히 남기고 exit code 1로 종료
   - Ultralytics 사전 학습 모델(`yolo26n.pt`, `docs/context/02-task-list.md`/`04-experiment-log-template.md`에서 이미 확정된 기준 모델명) 로드 시도 결과 (성공/실패와 실패 사유)
   - 실행 시 `configs/environment/` 폴더가 없으면 자동 생성한다 (`main.py`가 `data/`, `outputs/`를 자동 생성하는 것과 동일한 패턴). `PROJECT_ROOT`는 `Path(__file__).resolve().parent.parent`로 이 파일 안에서 독립적으로 계산한다 (아직 공통 유틸 모듈이 없으므로 `main.py`를 import하지 않는다).
   - 이 스크립트가 직접 `environment_info.txt`/`package_versions.txt` 파일을 쓰지는 않는다 (아래 "구현 제외 범위" 참고).

## 구현 범위 (In Scope)

- `requirements.txt` 신규 생성
- `src/check_environment.py` 신규 생성 (실행 시 `configs/environment/` 폴더 자동 생성 포함)

## 구현 제외 범위 (Out of Scope)

- 가상환경(`venv`) 생성, `pip install` 실행, `check_environment.py` 실제 실행 — CODEX 샌드박스에는 이 프로젝트에 맞는 실행 환경이 없을 수 있으므로, 실행 검증은 CLAUDE가 별도로 수행한다 (`docs/onboarding/ai-orchestration.md` "CODEX 실행 방식" 참고).
- `configs/environment/environment_info.txt`, `configs/environment/package_versions.txt` 실제 파일 생성 — 실행 결과물이므로 CLAUDE가 실행 후 생성한다. 가짜 값이나 빈 값으로 미리 채워두지 않는다.
- `src/common/*.py` (file_utils, image_utils, json_utils, logging_utils 등) — 작업2/3 범위이며 이번 작업 범위가 아니다.
- `data/`, `models/`, `outputs/`, `reports/`, `experiments/`, `tests/` 폴더 생성 — `data/`, `outputs/`는 이미 `main.py` 실행 시 자동 생성되고, 나머지는 실제 내용물이 생기는 작업 시점에 만든다. git은 빈 폴더를 추적하지 않으므로 지금 미리 만들 이유가 없다.
- Python 버전 자체 설치, pyenv 등 버전 관리 도구 도입.
- `logging` 모듈 사용 — `check_environment.py`는 1회성 진단 스크립트이므로 `experiments/*/logs/` 규칙을 적용하지 않고 단순 `print()`로 출력한다.

## 작업 전 반드시 확인해야 하는 문서

- `docs/context/02-task-list.md` 58~107줄 (작업1: 수행 작업, 기본 폴더 구조, 산출물, 완료 조건)
- `docs/context/03-deliverables.md` 4.2절 (실행 환경 정보 — `configs/environment/environment_info.txt`, `package_versions.txt` 구조)
- `CLAUDE.md` — Naming Convention(PEP 8), Formatter(black)/Linter(ruff), Error Handling 원칙(예외를 삼키지 않고 원인을 기록)
- `main.py` — 기존 경로 상수 계산 방식(`Path(__file__).resolve()...`)과 폴더 자동 생성 패턴 참고

## 완료 기준 (Definition of Done)

- ( ) `requirements.txt`에 위 8개 패키지가 모두 포함되어 있다.
- ( ) `src/check_environment.py`가 Python 버전, OS/CPU/RAM, GPU/CPU 여부, 주요 패키지 import 결과, YOLO 모델 로드 결과를 모두 출력하는 로직을 포함한다.
- ( ) 패키지 import 실패 시 어떤 패키지가 실패했는지 표준에러에 명확히 남고, 예외를 조용히 삼키지 않는다.
- ( ) `configs/environment/` 폴더가 없을 때 자동 생성하는 로직이 포함되어 있다.
- ( ) 코드가 PEP 8 / black 포맷을 따른다.
- ( ) 실제 venv 생성·설치·실행 검증은 이번 CODEX 작업의 완료 기준에 포함하지 않는다 (CLAUDE가 이어서 수행).

## 제약사항

- 표준 라이브러리 + 위에 나열된 8개 패키지 외의 새로운 외부 패키지를 임의로 추가하지 않는다.
- `check_environment.py`는 인자 없이 `python src/check_environment.py` 형태로 실행 가능해야 한다.
- `requirements.txt`, `src/check_environment.py` 외의 파일은 추가하지 않는다.

## 테스트 방법 및 검증 기준 (CODEX 완료 후 CLAUDE가 이어서 수행)

1. `python -m venv venv` 생성 후 활성화
2. `pip install -r requirements.txt`
3. `python src/check_environment.py` 실행 → 출력을 `configs/environment/environment_info.txt`로 저장
4. `pip freeze > configs/environment/package_versions.txt`
5. `docs/context/02-task-list.md` 작업1 완료 조건 5개 항목이 모두 충족되는지 확인
