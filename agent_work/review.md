# 코드 리뷰: 원본 Polygon 시각화 (`src/visualization/visualize_original_polygon.py`)

## 요구사항 충족 여부

- 표본 선정(정상 50 + 표준 클래스 6개 × 50, 고정 시드) — 확인
- 강제 포함(최다 객체 이미지, 경계초과/음수좌표 이미지) — 확인
- Polygon 경계선·반투명 영역·클래스명·객체 번호·파일명·크기 표시 — 확인
- `coordinate_check.csv`, `error_files.csv` 생성 — 확인
- 재실행 시 동일 결과(표본 목록·CSV 해시 동일) — 확인

## 발견한 문제

### Minor — black 포맷 미준수

CODEX가 `black --check`를 로컬에서 실행하지 못했다(샌드박스의 `venv/pyvenv.cfg`가 한글 사용자 경로를 못 읽어 실패, 알려진 제약). 실제로 CLAUDE 쪽 venv로 `black --check` 해보니 1개 파일 리포맷 필요 상태였음. CLAUDE가 직접 `black`을 실행해 반영함.

### Suggestion — `out_of_bounds_coordinate` 판정 기준이 작업5(`validate_polygon.py`)와 다름 → 수정 완료

~~이 스크립트는 `x >= width`/`y >= height`를 초과로 판정하는데, 기존 `validate_polygon.py`(작업5)는 `x > width`/`y > height`를 기준으로 삼는다.~~ CODEX에게 scoped fix 요청해 `>=` → `>`로 통일함. 재실행 결과 `coordinate_check.csv`가 3건(`VT_ST_06_14623797`, `VT_ST_06_14625705`, `VT_ST_06_14625816`)으로, `reports/data-quality/warning_files.csv`의 `out_of_bounds_coordinate` 3건과 정확히 일치.

참고: `warning_files.csv`의 `negative_coordinate` 1건(`RT_AL_00_14483491`)은 이 스크립트에 안 잡히는데, 이건 버그가 아니라 그 좌표가 `case: ""`(정상 placeholder annotation)에 속해 있어서다 — 이 스크립트는 정상 annotation을 애초에 그리지 않도록 설계되어 있어(요구사항대로), 그 좌표를 검사 대상에서 제외한다.

## 심각도 없음(정상 확인)

- 다수 객체 이미지(`VT_ST_02_14600498`, 98개 annotation) 육안 확인 — 각 폴리곤이 실제 기공 위치에 정확히 그려짐.
- 경계초과 이미지(`VT_ST_06_14623797`) 육안 확인 — undercut 폴리곤이 이미지 우측 경계 밖으로 실제로 잘려나가는 모습이 보임.
- 정상 이미지(`RT_AL_00_14483464`) 육안 확인 — 폴리곤 없이 파일명·크기만 표시됨(의도대로 동작).

## 사용자가 직접 확인하는 방법

1. 스크립트 실행: `venv/Scripts/python.exe src/visualization/visualize_original_polygon.py` (실행 로그 마지막 줄에 `samples=353, images=353, coordinate_issues=24, errors=0` 확인)
2. 다수 객체 확인: `outputs/original-polygon/VT_ST_02_14600498.jpg` 열어서 폴리곤 98개가 각각 기공 위치에 그려졌는지 확인
3. 경계초과 확인: `outputs/original-polygon/VT_ST_06_14623797.jpg` 열어서 undercut 폴리곤이 이미지 우측 경계 밖으로 잘려나가는지 확인
4. 정상 이미지 확인: `outputs/original-polygon/RT_AL_00_14483464.jpg` 열어서 폴리곤 없이 파일명·크기만 표시되는지 확인
5. 좌표 검증 결과: `outputs/original-polygon/coordinate_check.csv` 열어서 `out_of_bounds_coordinate` 3건(`warning_files.csv`와 동일)만 남았는지 확인
6. 재현성 확인: 스크립트를 한 번 더 실행하고 `outputs/original-polygon/coordinate_check.csv`, `error_files.csv`가 그대로인지 확인 (`git diff` 없음이면 동일)
