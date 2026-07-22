# 코드 리뷰: Bounding Box를 YOLO Detection 라벨로 변환 (`src/conversion/box_to_yolo.py`)

## 요구사항 충족 여부

- 작업8 선별 299장 전체(정상 이미지 포함) 대상 — 확인
- `metadata/bbox_annotations.csv`만으로 변환(이미지·JSON 재오픈 없음) — 확인
- 픽셀 좌표 → YOLO 정규화 좌표 계산식 일치 — 확인 (아래 육안 검증 참고)
- 정상 이미지는 빈 라벨 파일 — 확인
- `metadata/yolo_classes.txt`(class_id 0~5 순서) 생성 — 확인
- 클래스 번호 완료 조건을 "0~5 정의 범위"로 판단(문서 574줄 "0 또는 1"은 6-클래스 체계와 안 맞는 문구라 지시서에서 대체) — 확인

## 발견한 문제

없음. Blocker/Major/Minor/Suggestion 전부 해당 사항 없음.

기계적 포맷 이슈 1건(줄바꿈 스타일) 발견 — black으로 CLAUDE가 직접 적용함(로직 변경 아님, CODEX 재작업 불필요).

## 실행 결과

```
대상 이미지 수: 299
생성된 라벨 파일 수: 299
빈 라벨 수: 100
객체가 있는 라벨 파일 수: 199
전체 객체 수: 439
클래스별 객체 수: class_id=3 class_name=porosity count=241
클래스별 객체 수: class_id=4 class_name=slag_inclusion count=198
```

- `outputs/yolo_labels/` 299개 `.txt` 생성 확인, 전체 줄 수 합계 439 — 작업9의 `bbox_annotations.csv` 439건과 일치
- `metadata/yolo_classes.txt` 6줄, `class_statistics.csv`의 `class_id` 순서와 동일(crack, incomplete_penetration, lack_of_fusion, porosity, slag_inclusion, undercut)
- 정상 이미지 `RT_AL_00_14483440.txt` — 0바이트(빈 파일) 확인
- 다중 객체 이미지 `RT_AL_02_14489189.txt` — 24줄(작업9의 24개 annotation과 일치)
- 좌표 역산 검증: `RT_AL_02_14483871`(단일 porosity, `x_min=33,y_min=207,x_max=3431,y_max=442,width=3451,height=943`) → YOLO 라인 `3 0.501884 0.344115 0.984642 0.249205` — 직접 계산한 값과 정확히 일치
- black 적용 후 재검사 통과, ruff 통과
- 재실행 2회 비교(`md5sum`) — `outputs/yolo_labels/` 299개 파일 + `metadata/yolo_classes.txt` 전부 동일(재현성 확인, 무작위 요소 없음)

## 사용자가 직접 확인하는 방법

1. `venv/Scripts/python.exe src/conversion/box_to_yolo.py` 실행 — 로그 마지막 줄들에서 `전체 객체 수: 439` 확인
2. `outputs/yolo_labels/RT_AL_00_14483440.txt` — 파일 크기 0바이트(정상 이미지 빈 라벨) 확인
3. `outputs/yolo_labels/RT_AL_02_14489189.txt` — 24줄인지 확인(원본 다중 객체 이미지)
4. `metadata/yolo_classes.txt` — 6줄, `crack~undercut` 순서가 `metadata/class_statistics.csv`의 `class_id` 순서와 같은지 확인
5. `metadata/bbox_annotations.csv`에서 임의의 한 행을 골라 직접 정규화 계산(`center_x=(x_min+x_max)/2/image_width` 등)한 값이 해당 이미지의 YOLO 라벨 라인과 일치하는지 확인
6. 재실행 후 `outputs/yolo_labels/`와 `metadata/yolo_classes.txt`가 동일한지 확인
