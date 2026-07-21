# Project Context

프로젝트를 시작하기 전에 반드시 확인해야 하는 프로젝트별 설정입니다.

## 목차

- [프로젝트 개요](#프로젝트-개요)
- [기술 스택 & 아키텍처](#기술-스택--아키텍처)
- [AI 협업 체계](#ai-협업-체계)
- [개발 프로세스 규칙](#개발-프로세스-규칙)
- [코딩 규칙](#코딩-규칙)
- [Git & PR 규칙](#git--pr-규칙)
- [문서화 규칙](#문서화-규칙)
- [개발 원칙](#개발-원칙)
- [기타](#기타)

---

# 프로젝트 개요

## Project Information

- Project: 용접 결함 검출 자동 라벨링 AI (Weld Defect Detection Auto-Labeling) — 1단계 Python PoC
- Description: AI-Hub 용접 검사(RT) 이미지·Polygon 라벨 데이터를 YOLO Detection 형식으로 변환하고, 모델 학습·추론·자동 라벨 생성까지 전체 파이프라인이 실제 데이터에서 동작하는지 검증하는 PoC. 세부 범위는 `docs/context/01-experiment-scope.md` 참조.
- Repository: https://github.com/startcoriny/defect_detection_ai_poc.git
- Environment: 로컬 개발 환경(Windows), Python 가상환경, CPU 또는 GPU(CUDA) 겸용

---

# 기술 스택 & 아키텍처

## Technology Stack

- Language: Python (버전 미지정, 개발 환경 구성 시 확정 — `docs/context/02-task-list.md` 작업1)
- Framework: Ultralytics YOLO (YOLO26n Detection, `docs/context/02-task-list.md`/`docs/context/04-experiment-log-template.md` 참조)
- Runtime: 서버 런타임 없음, PyTorch 기반 로컬/배치 스크립트 실행
- Package Manager: pip (`requirements.txt`)
- Database: 없음 (1차 PoC 범위 제외 — `docs/context/01-experiment-scope.md` 9절)
- ORM: 해당 없음
- Cache: 해당 없음
- Message Queue: 해당 없음
- Storage: 로컬 파일시스템 (`data/raw` 원본, `data/work` 작업용, `data/processed` 변환 결과 — `docs/context/02-task-list.md` 작업2)
- Infrastructure: 로컬 CPU/GPU 환경, 클라우드·배포 인프라는 1차 PoC 범위 제외

## Architecture

- Architecture: 배치 스크립트 기반 파이프라인 (데이터 분석 → 변환 → 학습 → 추론 → 자동 라벨 생성 → 평가). 서버/API 아키텍처 아님.
- Directory Structure: `docs/context/03-deliverables.md` 9절 "권장 최종 프로젝트 구조" 참조
- Module Strategy: `src/` 하위를 역할별로 분리 — `common`(공통 유틸), `data`(데이터 분석), `validation`(검증), `conversion`(라벨 변환), `visualization`(시각화), `dataset`(분할·구성), `model`(학습·추론), `evaluation`(성능 평가). `docs/context/03-deliverables.md` 3절 참조
- API Style: 해당 없음 (Backend API는 1차 PoC 범위 제외 — `docs/context/01-experiment-scope.md` 9절)

## Development Configuration

### Verification

- Format: black
- Lint: ruff
- Type Check: 생략 (필요 시 mypy 추가 검토)
- Test: pytest
- Build: 별도 빌드 없음 (Python 스크립트 실행 기반)

### Code Quality

- Formatter: black
- Linter: ruff
- Static Analysis: 생략 (필요 시 mypy 추가 검토)

### CI/CD

- CI: 미구성 (1차 PoC 범위 제외)
- CD: 미구성 (모델 배포·운영은 1차 PoC 범위 제외 — `docs/context/01-experiment-scope.md` 9절)

---

# AI 협업 체계

## AI Configuration

### Agent Roles

- Planning Agent: Claude
- Implementation Agent: Codex
- Review Agent: Claude

### Agent Rules

- Planning Agent Rule: `CLAUDE.md`의 AI 역할 분리 규칙 / 구현 지시서 작성 규칙
- Implementation Agent Rule: `AGENTS.md`
- Review Agent Rule: `docs/rules/review-agent-rule.md`

## AI 역할 분리 규칙

반드시 `docs/onboarding/ai-orchestration.md`를 참조하세요.

프로젝트에서는 AI Agent의 역할을 명확하게 분리합니다.

- CLAUDE: 요구사항 분석, 설계, 명세 작성, 코드 리뷰, 문서화, PR 초안 작성
- CODEX: 코드 구현, 테스트 작성, 리뷰 반영, 리팩터링 수행

### 역할 원칙

- CLAUDE는 구현 계획과 명세를 작성합니다.
- CODEX는 명세를 기반으로 구현을 수행합니다.
- CLAUDE는 CODEX의 구현 결과를 리뷰합니다.
- 각 Agent는 자신의 역할 범위를 벗어나는 작업을 수행하지 않습니다.

### 구현 요청 처리

사용자가 구현을 요청한 경우 CLAUDE는 직접 구현하지 않습니다.

대신 다음을 수행합니다.

- 요구사항을 정리합니다.
- 구현 명세를 작성합니다.
- 구현에 필요한 작업 지시서를 준비합니다.
- CODEX에게 작업을 전달합니다.

### 예시

사용자:
> 스케줄러 구현해줘.

CLAUDE:
> 구현은 CODEX의 역할입니다.
> 구현에 필요한 작업 지시서를 작성하여 전달하겠습니다.

## 구현 지시서(Implementation Prompt) 작성 규칙

구현 지시서는 CLAUDE가 CODEX에게 전달하거나,
AI Agent가 실제 구현 작업을 수행하기 위한 작업 명세 문서입니다.

구현 지시서는 `agent_work/prompt.md`에 작성합니다.

### 반드시 포함해야 하는 내용

- CODEX가 구현해야 하는 기능 및 요구사항
- 구현 범위(In Scope)
- 구현 제외 범위(Out of Scope)
- 작업 전 반드시 확인해야 하는 문서 및 코드 목록
- 완료 기준(Definition of Done)
- 구현 시 반드시 따라야 하는 제약사항
- 필요한 경우 테스트 방법 및 검증 기준

### 포함하지 말아야 하는 내용

- 긴급 이슈 또는 임시 메모
- 아직 결정되지 않은 기술 선택 사항
- MVP 이후 고려할 기능이나 아이디어
- 프로젝트 전반의 개발 규칙
(공통 규칙은 별도의 프로젝트 규칙 문서에서 관리)

### 작성 원칙

- 구현 가능한 수준으로 요구사항을 구체적으로 작성합니다.
- 구현자가 추가 추측을 하지 않아도 될 정도의 정보를 제공합니다.
- 구현 범위와 제외 범위를 명확하게 구분합니다.
- 여러 구현 방식이 가능한 경우에는 선택해야 하는 방향을 명시합니다.
- 완료 여부를 객관적으로 판단할 수 있도록 완료 기준을 작성합니다.

### CLAUDE 동작 원칙

CLAUDE는 구현 지시서를 작성하기 전에 다음 사항을 반드시 확인합니다.

- 요구사항이 충분히 정의되어 있는가
- 구현 범위가 명확한가
- 완료 기준이 정의되어 있는가
- 필요한 참고 문서가 준비되어 있는가

위 조건이 충족되지 않은 경우에는 구현 지시서를 작성하거나 CODEX에게 작업을 전달하지 않습니다.
먼저 부족한 요구사항을 사용자와 함께 정리한 후 구현 지시서를 작성합니다.

---

# 개발 프로세스 규칙

## AI 작업 기본 순서

작업은 가능한 한 아래 순서를 따릅니다.

1. 목표를 확인합니다.
2. 현재 구조와 관련 정보를 확인합니다.
3. 작업 범위와 영향을 받는 대상을 파악합니다.
4. 작업 계획을 수립합니다.
5. 작업을 수행합니다.
6. 필요한 경우 결과를 검증합니다.
7. 변경 사항을 요약합니다.
8. 후속 작업이나 남은 TODO를 기록합니다.

작업의 성격에 따라 일부 단계는 생략할 수 있습니다.

## 질문 최소화 규칙

작업을 진행하는 데 필요한 정보가 프로젝트 컨텍스트, 기존 코드베이스 또는 프로젝트 문서에 정의되어 있다면 이를 기준으로 작업합니다.

다음 우선순위에 따라 판단합니다.

1. 사용자의 명시적인 요구사항
2. 프로젝트 컨텍스트
3. 프로젝트 문서 및 규칙
4. 기존 코드베이스의 패턴과 컨벤션

위 기준으로도 판단할 수 없는 경우에만 사용자에게 질문합니다.

## 반드시 사용자 확인이 필요한 작업

아래 작업은 임의로 진행하지 않고 반드시 사용자의 확인을 받은 후 진행합니다.

- 비용이 발생하거나 비용 증가가 예상되는 작업
- 보안 정보(API Key, Secret, Token, 인증 정보 등)를 생성, 변경 또는 사용하는 작업
- 운영 환경 또는 운영 데이터에 영향을 주는 작업
- 되돌리기 어려운 데이터 또는 스키마 변경
- 외부 서비스나 조직의 정책을 위반할 가능성이 있는 작업
- 인증, 결제, 개인정보 등 민감한 기능과 관련된 작업
- Git 브랜치, 배포 또는 릴리스에 영향을 주는 작업
- 그 외 복구가 어렵거나 영향 범위가 큰 작업
- 외부 시스템 또는 다른 팀에 영향을 주는 작업

## 테스트 및 검증 규칙

코드나 설정을 변경한 뒤에는 가능한 범위에서 결과를 검증합니다.

검증은 프로젝트에 정의된 명령어와 기준을 우선 따릅니다.

일반적인 확인 순서는 다음과 같습니다.

1. 정적 검사 실행
   - 타입 체크
   - 린트
   - 포맷 검사

2. 테스트 실행
   - 단위 테스트
   - 통합 테스트
   - E2E 테스트

3. 빌드 또는 실행 확인

테스트가 아직 없거나 일부 검증만 가능한 경우에는
가능한 검증을 우선 실행합니다.

검증을 실행할 수 없는 환경이라면
실행하지 못한 이유와 대신 확인한 내용을 명확히 기록합니다.

## 작업 완료 보고

작업이 완료되면 아래 내용을 함께 보고합니다.

- 수행한 작업 요약
- 변경된 파일
- 테스트 및 검증 결과
- 구현하지 못한 항목과 이유
- 남은 TODO

---

# 코딩 규칙

## Coding Convention

- Naming Convention: PEP 8 (함수·변수 snake_case, 클래스 PascalCase, 상수 UPPER_CASE)
- Branch Strategy: `main` → `dev` → 기능별 브랜치. 기능별 브랜치는 `dev`로 PR 머지하고, `dev`가 안정화되면 `main`으로 머지한다.
- Branch Naming: `<type>/<설명>` 패턴 (예: `feature/data-inventory`, `fix/polygon-bbox`)
- Commit Convention: Conventional Commits (아래 "Git Commit Message Rules" 참조)
- Code Review: Review Agent(Claude) 기준, `docs/rules/review-agent-rule.md` 참조
- Error Handling: 예외를 삼키지 않고 실패한 파일명·원인을 함께 기록한다 (`docs/context/02-task-list.md` 작업5 원칙 적용)
- Logging: Python 표준 `logging` 모듈 사용. 실험·실행별 로그는 `experiments/<실험ID>/logs/`에 저장 (`docs/context/04-experiment-log-template.md` 폴더 구조 참조)
- Authentication: 해당 없음 (1차 PoC 범위 제외 — `docs/context/01-experiment-scope.md` 9절)
- Authorization: 해당 없음 (1차 PoC 범위 제외 — `docs/context/01-experiment-scope.md` 9절)
- File Header: `AGENTS.md` 참조
- Comment Style: `AGENTS.md` 참조

코드 작성 시 지켜야 하는 코딩 규칙, 파일 헤더 규칙, 주석 규칙은 `AGENTS.md`를 참조하세요.
Implementation Agent(codex)가 자동으로 읽는 문서이며, Review Agent는 코드 리뷰 시 동일한 기준으로 검토합니다.

---

# Git & PR 규칙

## Branch Naming Rules

브랜치 전략은 `main` → `dev` → 기능별 브랜치 구조를 따릅니다.

- `main`: 배포·안정 브랜치
- `dev`: 통합 브랜치
- 기능별 브랜치: `dev`에서 분기하여 작업 후 `dev`로 PR 머지
- `dev`가 안정화되면 `dev` → `main`으로 머지

브랜치 이름은 `<type>/<설명>` 패턴을 따릅니다.

```
feature/data-inventory
fix/polygon-bbox
docs/experiment-log-template
```

- 브랜치 이름은 작업 내용을 명확하게 표현합니다.
- 내부 계획 번호나 임시 식별자는 포함하지 않습니다.
- 일관된 네이밍 규칙을 유지합니다.

## Git Commit Message Rules

커밋 메시지는 프로젝트에서 정의한 커밋 컨벤션을 따릅니다.

프로젝트에 별도 규칙이 없는 경우에는 Conventional Commits를 기본으로 사용합니다.

커밋 메시지는 다음 원칙을 따릅니다.

- 변경 내용을 명확하게 작성합니다.
- 하나의 커밋은 하나의 목적을 갖도록 작성합니다.
- 모호한 표현은 사용하지 않습니다.
- 커밋 메시지는 변경 내용을 간결하게 설명합니다.

## Pull Request Rules

PR은 코드 리뷰를 위한 문서입니다.

상세한 기술 의사결정과 작업 회고는 기술 의사결정 문서 또는 Work Log에 기록합니다.

PR에는 아래 항목만 포함합니다.

- Summary
- Changes
- Test
- Related Docs
- Checklist

PR 생성 전 아래 항목을 확인합니다.

- 테스트 통과
- 빌드 성공
- 변경 파일 검토
- Work Log 업데이트
- 관련 문서 연결 (필요한 경우)

PR 초안은 사용자에게 먼저 보여주고 승인을 받은 뒤 생성합니다.

승인 없이 직접 생성하지 않습니다.

금지 사항은 다음과 같습니다.

- 테스트 없이 PR 생성
- 빌드 실패 상태에서 PR 생성
- 여러 기능이 섞인 PR 생성
- Work Log 수준의 장문 설명 작성

---

# 문서화 규칙

## Documentation

- Onboarding: `docs/onboarding/ai-orchestration.md`
- Specification: `docs/specs` (1단계 PoC 설계 문서는 `docs/context` 참조)
- API Documentation: 해당 없음 (API 없음)
- Architecture: `docs/architecture`
- Decision: `docs/decisions`
- Work Log: Notion (`docs/rules/worklog-rules.md` 참조)
- Issue Tracker: GitHub Issues

## 문서 관리 규칙

프로젝트 문서는 `docs` 아래에서 관리합니다.

예시
```text
docs/architecture
docs/specs
docs/api
docs/decisions
```

### 기능 명세

다음과 같은 작업은 구현 전에 기능 명세를 작성합니다.

- 새로운 기능 개발
- 기존 기능의 큰 변경
- 다른 개발자와 협업하는 작업
- 요구사항이 복잡하거나 구현 범위가 큰 작업

### 기술 의사결정

기술적인 선택이 필요한 경우에는
`docs/decisions`에 기술 의사결정 문서를 작성합니다.

기술 의사결정 문서에는 다음 내용을 포함합니다.

- 해결하려는 문제
- 고려한 선택지
- 각 선택지의 장점
- 각 선택지의 단점
- 최종 결정
- 결정한 이유
- 트레이드오프

### 작업 기록

작업 과정과 결과는 Work Log에 기록합니다.
Work Log 작성 규칙은 별도의 Work Log Rules를 따릅니다.

## 기술 판단 기준

기술을 선택하거나 비교할 때는 다음 기준을 종합적으로 고려합니다.

- 성능
- 확장성
- 유지보수성
- 개발 생산성
- 운영 안정성
- 프로젝트 요구사항과의 적합성

프로젝트 특성에 따라 추가 기준을 함께 고려할 수 있습니다.

예시

- AI 협업 친화성
- 개발팀 규모
- 운영 인력
- 개발 기간
- 비용
- 학습 비용

기술을 평가할 때는 단순히 "좋다", "빠르다", "효율적이다"와 같은 표현을 사용하지 않습니다.

다음 내용을 함께 설명합니다.

- 어떤 문제를 해결하는가
- 어떤 장점과 단점이 있는가
- 어떤 비용이나 제약이 있는가
- 어떤 상황에서 적합한가
- 다른 선택지와 비교했을 때의 차이점

## Work Log Rules

상세 작성 규칙과 출력 템플릿은 `docs/rules/worklog-rules.md`를 참조하세요.

Work Log는 NOTION에 기록하는 작업 기록 문서입니다.

단순히 무엇을 만들었는지 나열하지 않습니다.

작업 내용을 재사용할 수 있도록
문제 해결 과정과 기술 선택 이유를 함께 기록합니다.

Work Log에는 아래 항목을 포함합니다.

- 날짜
- 작업 목표
- 문제 정의
- 검토한 후보
- 최종 선택
- 선택 이유
- 트레이드오프
- 구현 내용
- 변경 파일
- 테스트 결과
- 결과
- 남은 TODO
- 참고 문서 (관련 Spec, Decision, PR 등, 필요한 경우)

Work Log는 사용자에게 먼저 보여주고 승인을 받은 뒤 NOTION에 등록합니다.

승인 없이 직접 등록하지 않습니다.

---

# 개발 원칙

- Readability: 경로·설정값을 코드에 무분별하게 하드코딩하지 않고 설정 파일로 분리 — `docs/context/03-deliverables.md` 3.9절
- Performance: 1차 PoC에서는 성능 최적화보다 전체 파이프라인 동작 검증을 우선한다 — `docs/context/01-experiment-scope.md` 1절
- Security: 원본 데이터(`data/raw`)는 코드 실행으로 수정하지 않는다 — `docs/context/02-task-list.md` 작업2. 인증·개인정보 관련 항목은 1차 PoC 범위 제외.
- Testing: 전체 학습 전 소량 데이터·짧은 Epoch로 Smoke Test를 먼저 수행한다 — `docs/context/02-task-list.md` 작업16
- Documentation: 실험마다 고유 ID를 부여하고 조건·결과를 기록해 재현 가능하게 한다 — `docs/context/04-experiment-log-template.md`

---

# 기타

- Notes: 1단계 PoC의 상세 설계 근거는 `docs/context/README.md`부터 순서대로 확인한다.
