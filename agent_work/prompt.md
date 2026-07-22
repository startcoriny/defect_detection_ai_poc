# 구현 지시서: 프로젝트 스켈레톤 실행 확인 (main.py)

## 배경

현재 저장소에는 설계 문서(`docs/`)와 규칙 문서(`CLAUDE.md`, `AGENTS.md`)만 있고 실행 가능한 코드가 없다. 본격적인 PoC 작업(`docs/context/02-task-list.md`)을 시작하기 전에, 저장소가 실제로 실행 가능한 상태인지 확인할 수 있는 최소 스켈레톤을 만든다. AI/ML 로직은 포함하지 않는다.

## 기능 및 요구사항

`python main.py`를 실행하면 표준출력에 정확히 아래 형식이 출력되어야 한다.

```
Auto Labeling PoC v0.1

Project Root : <절대경로>
Dataset Path : <절대경로>
Output Path : <절대경로>

Ready.
```

- `Project Root`는 `main.py` 파일이 위치한 디렉터리의 절대경로다. (실행 시점의 현재 작업 디렉터리가 아니라 파일 위치 기준으로 계산한다. 즉 다른 디렉터리에서 `python /경로/main.py`로 실행해도 항상 같은 값이 나와야 한다.)
- `Dataset Path`는 `<Project Root>/data`, `Output Path`는 `<Project Root>/outputs`다.
- `Dataset Path`, `Output Path` 폴더가 없으면 자동으로 생성한다. 이미 있으면 에러 없이 통과한다.

## 구현 범위 (In Scope)

- 저장소 루트에 `main.py` 신규 생성
- `PROJECT_ROOT`, `DATASET_PATH`, `OUTPUT_PATH`를 `main.py` 상단에 상수로 직접 정의 (별도 config 파일 없이)
- `Dataset Path`, `Output Path` 폴더 자동 생성 로직
- 지정된 포맷으로 콘솔에 출력하는 로직

## 구현 제외 범위 (Out of Scope)

- `configs/*.yaml` 등 별도 설정 파일 도입 (지금은 파일이 `main.py` 하나뿐이라 과잉 설계. 스크립트가 여러 개로 늘어나는 시점에 다시 판단한다.)
- `requirements.txt`, 가상환경(venv) 생성, PyTorch/Ultralytics/OpenCV 등 패키지 설치 — `docs/context/02-task-list.md` 작업1의 나머지 범위이며 이번 작업 범위가 아니다.
- `src/` 하위 모듈 구조 생성 — 아직 실제 기능이 없으므로 만들지 않는다.
- 데이터 분석/변환/학습/평가 등 실제 PoC 로직 일체.

## 작업 전 반드시 확인해야 하는 문서

- `CLAUDE.md` — 코딩 규칙(Naming Convention: PEP 8 등), 개발 원칙(경로 하드코딩 지양 원칙과 이번 작업에서의 예외 사유)
- `docs/context/03-deliverables.md` 9절 — 향후 프로젝트 구조 참고 (지금은 그 구조 전체를 만들지 않고 `data/`, `outputs/`만 다룬다)

## 완료 기준 (Definition of Done)

- `( )` 저장소 루트에서 `python main.py` 실행 시 에러 없이 종료된다.
- `( )` 저장소 루트가 아닌 다른 디렉터리에서 절대경로로 `python <경로>/main.py`를 실행해도 동일한 `Project Root` 값이 출력된다.
- `( )` 출력이 위에 명시한 포맷과 정확히 일치한다 (빈 줄 위치 포함, "Ready."로 끝남).
- `( )` `data/`, `outputs/` 폴더가 없던 경우 자동으로 생성된다.
- `( )` 이미 `data/`, `outputs/` 폴더가 있는 상태에서 재실행해도 에러가 발생하지 않는다.
- `( )` 표준 라이브러리만 사용하여, 별도 `pip install` 없이 실행된다.

## 제약사항

- 표준 라이브러리만 사용한다 (예: `pathlib`, `os`). 외부 패키지를 추가하지 않는다.
- `PROJECT_ROOT`는 `Path(__file__).resolve().parent` 방식으로 계산한다 (실행 시점의 현재 작업 디렉터리를 기준으로 계산하지 않는다).
- 이번 작업에서는 `main.py` 외 다른 파일(설정 파일, `src/` 모듈 등)을 추가하지 않는다.

## 테스트 방법

1. 저장소 루트에서 `python main.py` 실행 → 출력 포맷 확인, `data/`·`outputs/` 폴더 생성 확인.
2. 저장소 루트가 아닌 다른 디렉터리로 이동한 뒤 `python <저장소 절대경로>/main.py` 실행 → `Project Root` 값이 1번과 동일한지 확인.
3. `data/`, `outputs/` 폴더가 이미 있는 상태에서 다시 `python main.py` 실행 → 에러 없이 동일한 출력이 나오는지 확인.
