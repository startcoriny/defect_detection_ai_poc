# 코드 리뷰: YOLO 라벨 변환 결과 재시각화 (`src/visualization/visualize_yolo_label.py`)

## 요구사항 충족 여부

- 작업8 선별 299장 전체(정상 이미지 포함), 표본 없이 전수 검증 — 확인
- `outputs/yolo_labels/*.txt`를 픽셀 좌표로 복원, `bbox_annotations.csv`(작업9 정답값)와 이미지별 `annotation_index` 순서로 1:1 대조 — 확인
- 객체 수 일치·클래스 불변·좌표 반올림 오차(0.5px 허용)·원본 Polygon 포함 여부 4가지 검증 — 확인
- 정상 이미지의 빈 라벨 여부, 라벨 파일 존재 여부(연결 오류) 검증 — 확인
- 시각화는 **왕복 복원 Box**(작업9의 정답 Box가 아님)를 원본 Polygon과 겹쳐 그림 — 확인, 검증 취지에 맞게 구현됨
- 폴더명 `outputs/yolo-label-visualization/`(케밥케이스) 채택 — 확인

## 발견한 문제

없음. Blocker/Major/Minor/Suggestion 전부 해당 사항 없음.

## 실행 결과

```
대상 이미지 수: 299
검증한 객체 쌍 수: 439
발견된 불일치 건수: 0
관측된 최대 좌표 오차(px): 0.001913
전체 통과 여부: PASS
```

- `metadata/yolo_roundtrip_mismatches.csv` — 헤더만(0건)
- `outputs/yolo-label-visualization/` 299장 생성 확인
- 육안 확인: `RT_AL_02_14489189.jpg`(다중 porosity 객체 각각 자홍색 Box로 정확히 표시), `RT_AL_02_14483871.jpg`(폭넓은 단일 porosity, Box가 원본 Polygon을 정확히 감쌈), `RT_AL_00_14483440.jpg`(정상 이미지, Box/Polygon 없이 파일명·크기만 표시) — 모두 기대대로 동작
- 최대 좌표 오차 0.002px 수준 — YOLO 포맷의 소수점 6자리 정밀도를 고려하면 예상된 수준(실질적으로 오차 없음)
- black/ruff 통과, 재실행 2회 비교(`md5sum`) 결과 `outputs/yolo-label-visualization/` 299장 전부 동일(재현성 확인, 무작위 요소 없음)

## 사용자가 직접 확인하는 방법

1. `venv/Scripts/python.exe src/visualization/visualize_yolo_label.py` 실행 — 로그 마지막 줄 `전체 통과 여부: PASS` 확인
2. `metadata/yolo_roundtrip_mismatches.csv` — 헤더만 있고 데이터 행이 없는지 확인
3. `outputs/yolo-label-visualization/RT_AL_02_14489189.jpg` — 24개 다중 객체가 각각 자홍색 Box로 표시되는지 확인
4. `outputs/yolo-label-visualization/RT_AL_02_14483871.jpg` — 폭넓은 단일 porosity를 Box가 정확히 감싸는지 확인
5. `outputs/yolo-label-visualization/RT_AL_00_14483440.jpg` — 정상 이미지에 Box/Polygon 없는지 확인
6. 재실행 후 `outputs/yolo-label-visualization/`와 `metadata/yolo_roundtrip_mismatches.csv`가 동일한지 확인
