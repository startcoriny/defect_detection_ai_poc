# 코드 리뷰: 라이브 데모용 GT vs 예측 비교 시각화

시연 시나리오는 `demo/live_demo_script.md`로 분리했다.

## 요구사항 충족 여부

- `src/visualization/exp5/compare_gt_prediction.py` 신규 작성 — 지시서의 4개 케이스를 `DEMO_CASES` 상수로 하드코딩.
- GT/예측 파싱은 `visualize_prediction.py`의 `parse_yolo_line`, `restore_box`를 import해 재사용(중복 정의 없음) — 확인 완료.
- 좌(GT, 초록 `(0,200,0)`)·우(예측, 빨강 `(0,0,255)`) 2패널을 `cv2.hconcat` + 흰색 구분선(4px)으로 연결, 각 패널 상단에 "GT"/"Prediction" 라벨, 전체 상단에 케이스 라벨 배너 — 지시서대로 구현.
- 누락 데이터(GT 라벨 파일 없음, 예측 레코드 없음, 이미지 읽기 실패)는 에러 로그 후 해당 케이스만 건너뛰고 나머지는 계속 처리 — `process_case`가 `bool` 반환, 예외를 삼키지 않음.
- `common.image_utils.read_image`, `common.json_utils.load_json` 재사용, 기존 `visualize_prediction.py`·`image_utils.py`·`json_utils.py`는 수정 없음.

## 실행 결과 (CLAUDE가 venv로 직접 실행)

- `python src/visualization/exp5/compare_gt_prediction.py` → `비교 이미지 생성 완료: 4/4`, 오류 없이 종료(exit 0).
- `demo/comparison-images/`에 4개 파일 모두 생성 확인.
- 4개 이미지를 육안으로 전수 확인 — GT·예측 박스 색상, 좌우 배치, 케이스 라벨 배너 모두 의도대로 표시됨. 특히 `RT_AL_05_14492954.jpg`(위치 오류 케이스)는 예측 박스가 GT보다 폭·높이 모두 눈에 띄게 작게 그려지는 모습이 명확히 드러나 최종보고서 13절이 지적한 패턴을 그대로 보여준다.

## 발견한 이슈 1건 (경미, 리뷰 반영 완료)

- 최초 구현본은 `black --check`에서 2건 실패(줄바꿈 스타일, `GT_LABEL_ROOT` 상수와 `label_text` f-string). CODEX에게 포맷 수정만 재요청 → 현재 `black --check`, `ruff check` 모두 통과. 로직 변경 없음(포맷 전후 diff가 개행뿐).

## 추가 반영: 출력 경로를 프로젝트 루트 `demo/`로 이동

발표용 산출물을 실험 파이프라인 산출물 폴더(`outputs/`)와 분리해 별도 관리하기 위해, `OUTPUT_ROOT`를 `outputs/EXP-P1-DET-005/demo-comparison` → `demo/comparison-images`로 변경(CODEX, 상수 한 줄만 수정, 다른 로직 변경 없음을 diff로 확인). 이후 재실행해 `demo/comparison-images/`에 4개 이미지가 직접 생성됨을 확인했고, black/ruff도 재통과했다. 기존 `outputs/EXP-P1-DET-005/demo-comparison/`는 더 이상 쓰이지 않으므로 삭제했다.

## 추가 반영: 스크립트 자체도 `demo/`로 이동

이 스크립트는 프로젝트 파이프라인 소스코드가 아니라 시연 전용 도구이므로, `src/visualization/exp5/compare_gt_prediction.py` → `demo/compare_gt_prediction.py`로 위치를 옮겼다(CODEX). 이동 깊이가 4단계(`src/visualization/exp5/`)에서 1단계(`demo/`)로 바뀌어 `PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent` → `.parent.parent`로 수정했고, 나머지 로직(`visualization.exp5.visualize_prediction` import, `OUTPUT_ROOT` 등)은 변경하지 않았다. 이동 후 재실행해 black/ruff 통과와 4개 이미지 생성을 다시 확인했다.

## 결론

4개 데모 이미지 모두 정상 생성·검증 완료. 리허설(전체 라이브 흐름 실행)까지 마쳤고, 결과물은 `demo/`에 정리했다. 시연 시나리오는 `demo/live_demo_script.md` 참고.
