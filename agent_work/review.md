# 코드 리뷰: Test 데이터 추론 (`src/model/run_inference.py`)

## 요구사항 충족 여부

- Test 46장(정상 15/porosity 15/slag_inclusion 16) 전체를 개별 파일 경로로 순회하며 추론 — 확인
- 고정 추론 설정(conf=0.25, iou=0.70, imgsz=640, device=cpu) 정확히 적용 — 확인
- `project=`에 절대경로 사용(사전 확인한 상대경로 버그 회피) — 확인
- 이미지별 `try/except`로 실패를 개별 격리, 실패해도 나머지 이미지 계속 처리 — 확인(구조상 확인, 실제 실행에서는 실패 0건)
- `predictions/prediction_results.json`: `model_version`(`EXP-P1-DET-001`), `model_path`, `inference_config`, `generated_at`, `summary`(총/성공/실패/추론시간 통계), `images`(46개 전부, 정상 이미지도 `predictions: []`로 포함), `failures` 전부 포함 — 확인
- `outputs/predictions/test/`(시각화 이미지 46장) + `labels/`(표준 YOLO TXT, 예측 있는 이미지만) — 확인
- `outputs/predictions/inference.log` 콘솔+파일 동시 기록 — 확인

## 발견한 문제

없음. 기계적 포맷 이슈 1건(black 재포맷)만 CLAUDE가 직접 적용.

## 실행 결과

```
Test 이미지 46장 처리: succeeded=46, failed=0
총 추론 시간 814.6ms, 평균 17.7ms, 최소 11.5ms, 최대 30.0ms (image당, CPU)
예측 있는 이미지 11장(총 13개 박스: porosity 4장, slag_inclusion 5장, 2건씩 예측된 이미지 2장)
```

- `predictions/prediction_results.json` — `images` 배열 길이 46, `failures` 빈 배열, 정상 이미지(예: `RT_AL_00_14483499.jpg`) `predictions: []`로 정확히 기록
- `outputs/predictions/test/` — 이미지 46장 + `labels/` 하위 TXT 11개(JSON의 "예측 있는 이미지 11장"과 정확히 일치, 교차 검증)
- `outputs/predictions/test/labels/`의 TXT는 confidence 없이 표준 YOLO 형식(class_id cx cy w h)으로 저장됨(`save_conf=False`)
- black 적용 후 재검사 통과, ruff 통과

## 사용자가 직접 확인하는 방법

1. `venv/Scripts/python.exe src/model/run_inference.py` 실행(CPU, 1초 내외)
2. `predictions/prediction_results.json` — `summary.total_images == 46`, `summary.failed == 0` 확인
3. `outputs/predictions/test/` — 이미지 46장 존재, Bounding Box가 그려진 이미지 육안 확인(예: `RT_AL_02_14488001.jpg`)
4. `outputs/predictions/test/labels/` — 파일 11개, 예측 없는 이미지는 파일이 없는 게 정상(Ultralytics 기본 동작)
5. `outputs/predictions/inference.log` — 46장 처리 로그 전부 "처리 완료" 확인

## 결과

완료 조건 6개(46장 전체 처리, 정상 이미지 포함 기록, 좌표·클래스 추출, 파일 저장, 실패 파일 별도 기록 구조, black/ruff 통과) 모두 충족.
