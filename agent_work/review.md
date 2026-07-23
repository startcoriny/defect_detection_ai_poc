# 코드 리뷰: 자동 라벨 파일 생성 (`src/model/export_auto_labels.py`)

## 요구사항 충족 여부

- 새 추론 없이 `predictions/prediction_results.json`만 입력으로 사용 — 확인(모델 로드·추론 코드 없음)
- `auto-labels/yolo-labels/`: Test 46장 전체에 라벨 TXT 생성, 예측 없는 35장은 0바이트 빈 파일, 11장은 내용 있음 — 확인
- `auto-labels/prediction-metadata/export_metadata.json`: `model_version`/`confidence_threshold`/`exported_at`/`source` 스키마 정확 — 확인
- `auto-labels/prediction-metadata/prediction_results.json`: 작업19 원본과 `diff` 결과 완전 동일 — 확인(원본 추론 결과 무손실 보존)
- `auto-labels/cvat-import/`: `obj.names`(6줄), `obj.data`(classes/train/names/backup), `train.txt`(46줄), `obj_train_data/`(이미지 46+라벨 46=92개) — 확인
- 클래스 ID·정규화 좌표 범위 검증(`validate_prediction`), Test 이미지 수·클래스 수 하드코딩 검증(46/6) — 확인
- 스테이징 디렉터리(`.auto-labels-staging`)에 전체를 만든 뒤 원자적으로 `auto-labels/`로 교체 — 요청하지 않았지만 작업14의 원자적 교체 패턴과 일관된 견고성 개선, 스코프 벗어나지 않음

## 발견한 문제

없음. black/ruff 별도 조치 불필요(CODEX가 이미 통과 상태로 작성, CLAUDE가 재확인).

## 실행 결과

```
자동 라벨 생성 완료: 이미지 46장, 예측 포함 11장, 빈 라벨 35개
```

- `auto-labels/yolo-labels/`: 파일 46개(빈 파일 35 + 내용 있는 파일 11, 정확히 일치)
- `RT_AL_02_14488001.txt` 내용: `3 0.495183 0.503817 0.057178 0.077485` — `prediction_results.json`의 `bbox_normalized_xywh`와 소수점까지 정확히 일치(교차 검증)
- `auto-labels/prediction-metadata/prediction_results.json` — 원본과 `diff` 무차이 확인
- `auto-labels/cvat-import/obj_train_data/` — 92개 파일(이미지 46 + 라벨 46) 확인
- black `--check`, ruff `check` 통과

## 사용자가 직접 확인하는 방법

1. `venv/Scripts/python.exe src/model/export_auto_labels.py` 실행(1초 내외)
2. `auto-labels/yolo-labels/` 파일 수 46개, 예측 있는 11개만 내용 있는지 확인
3. `auto-labels/prediction-metadata/export_metadata.json`의 `model_version` 확인
4. `diff predictions/prediction_results.json auto-labels/prediction-metadata/prediction_results.json` — 차이 없음 확인
5. `auto-labels/cvat-import/{obj.names,obj.data,train.txt}` 내용과 `obj_train_data/` 파일 수(92개) 확인

## 결과

완료 조건 7개(TXT 저장, 객체당 한 줄, 클래스·좌표 유효, Confidence·모델 정보 별도 보존, 원본 결과 무손실, CVAT Import 형식, black/ruff 통과) 모두 충족.
