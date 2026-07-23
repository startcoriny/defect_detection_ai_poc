# 코드 리뷰: 자동 라벨 재시각화 (`src/visualization/visualize_prediction.py`)

## 요구사항 충족 여부

- 새 추론 없이 `predictions/prediction_results.json`(원본) ↔ `auto-labels/yolo-labels/*.txt`(왕복 결과) 비교 — 확인
- Test 46장 전체 왕복 검증(파일 존재, 객체 수, class_id 순서, 정규화 좌표 오차 1e-4, class_name, Confidence 보존) — 확인
- 시각화: 박스+클래스명+Confidence, 파일명+모델버전 오버레이, 예측 없는 이미지도 저장 — 확인
- `metadata/auto_label_roundtrip_mismatches.csv`(작업11과 동일한 관례) — 확인
- CVAT Import 구조 확인(파일 존재·개수, 실제 서버 연결 없이) — 확인
- black/ruff 통과 — 확인(black은 CLAUDE가 재포맷 적용)

## 발견한 문제

없음. 기계적 포맷 이슈 1건(black 재포맷)만 CLAUDE가 직접 적용. 추가로 요청한 것 이상으로 원본↔보존 JSON 간 Confidence 값 자체까지 개별 비교하는 검증(`confidence_mismatch`)을 넣어둔 게 스펙보다 더 꼼꼼함(스코프 벗어나지 않음).

## 실행 결과

```
CVAT 구조: obj.names=True (6줄), obj.data=True, train.txt=True (46줄)
CVAT 구조: obj_train_data 이미지=46, 라벨=46, 전체=92
CVAT Import 구조 확인: PASS
대상 이미지 수: 46
시각화 이미지 수: 46
발견된 불일치 건수: 0
전체 통과 여부: PASS
```

- `outputs/auto-label-visualization/RT_AL_02_14488001.jpg` 육안 확인 — porosity 박스 + Confidence 0.363 표기, 작업19 JSON 값과 정확히 일치
- `metadata/auto_label_roundtrip_mismatches.csv` — 헤더만 있고 데이터 행 0개(불일치 없음)
- black `--check`, ruff `check` 통과

## 사용자가 직접 확인하는 방법

1. `venv/Scripts/python.exe src/visualization/visualize_prediction.py` 실행(1초 내외)
2. 로그 마지막 줄 "전체 통과 여부: PASS" 확인
3. `outputs/auto-label-visualization/` — 이미지 46장, 예측 있는 이미지에 박스+클래스명+Confidence 확인(예: `RT_AL_02_14488001.jpg`)
4. `metadata/auto_label_roundtrip_mismatches.csv` — 헤더만 있는지(불일치 0건) 확인

## 결과

완료 조건 5개(위치 일치, 클래스·객체 수 유지, Confidence·모델 버전 보존 확인, CVAT Import 형식 확인, black/ruff 통과) 모두 충족.
