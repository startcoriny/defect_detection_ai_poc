# 코드 리뷰: 실험별 스크립트 폴더 분리 + EXP-002 스크립트 생성

## 요구사항 충족 여부

- 기존 7개 스크립트 `src/{model,evaluation,visualization}/exp1/`로 이동 — 확인
- exp1: 경로 깊이(`parents[2]→3`, `.parent×3→4`)와 `collect_error_cases.py` import만 변경, 그 외 로직·산출물 경로 100% 동일 — `diff --strip-trailing-cr`로 원본과 라인 단위 대조해 확인(각 파일 1~2줄만 차이)
- exp2: `EXPERIMENT_ID`(`EXP-P1-DET-002`), `imgsz`/`IMAGE_SIZE`(960), `export_auto_labels.py`의 `MODEL_VERSION`, `train_baseline.py`의 `EXPERIMENT_NAME`("RT_AL_YOLO26N_960_ImgszUp") 전부 반영 확인
- exp2: 산출물 경로(`predictions/EXP-P1-DET-002/`, `auto-labels/EXP-P1-DET-002/`, `outputs/EXP-P1-DET-002/...`, `reports/evaluation/EXP-P1-DET-002/...`, `errors/EXP-P1-DET-002/`) 전부 실험별로 분리됨, exp1 경로와 안 겹침 — grep으로 전수 확인
- black/ruff 통과(exp2 4개 파일은 CLAUDE가 black 재포맷 적용)

## 발견한 문제

없음.

## 실행 결과 (회귀 테스트)

- `venv/Scripts/python.exe src/model/exp1/run_inference.py` 재실행 — `total=46, succeeded=46, failed=0`, 기존과 동일한 결과 재현 확인(새 위치에서도 원본과 동일하게 동작)
- `grep -rn "EXP-P1-DET-001\|imgsz=640" src/*/exp2` — 0건(exp2에 EXP-001 잔재 없음)
- `black --check`, `ruff check` — 14개 파일(exp1 7 + exp2 7) 전부 통과

## 사용자가 직접 확인하는 방법

1. `diff --strip-trailing-cr <(git show HEAD:src/model/train_baseline.py) src/model/exp1/train_baseline.py` 등으로 exp1이 원본과 경로 깊이만 다른지 확인
2. `grep -rn "EXP-P1-DET-002" src/model/exp2 src/evaluation/exp2 src/visualization/exp2` — 값 반영 확인
3. `venv/Scripts/python.exe src/model/exp1/run_inference.py` 재실행 — 기존과 동일 결과 확인

## 결과

완료 조건 4개(exp1 이동·동작 불변, exp2 값 반영, 산출물 경로 비충돌, black/ruff 통과) 모두 충족.
