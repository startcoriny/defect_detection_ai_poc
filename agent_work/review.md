# 코드 리뷰: YOLO 학습 데이터셋 구성 (`src/dataset/build_yolo_dataset.py`)

## 요구사항 충족 여부

- `data/processed/dataset_v1/{images,labels}/{train,val,test}/` 표준 YOLO 폴더 구조 생성 — 확인
- 원본 `.jpg` 복사 + `outputs/yolo_labels/*.txt` 복사, 각 파일 크기·SHA-256 해시 대조로 무결성 검증 — 확인
- `data.yaml`(`path`, `train/val/test`, 6클래스 `names` — `yolo_classes.txt` 순서 그대로 재사용) — 확인
- 정상 이미지(빈 라벨) 포함 여부 검증 — 확인
- 임시 스테이징 디렉터리에서 전부 빌드·검증 후 원자적으로 교체(`STAGING_ROOT.replace(DATASET_ROOT)`) — 지시서 요구보다 더 견고하게 구현(중간 실패 시 부분 완성된 데이터셋이 남지 않음)

## 발견한 문제

없음. 기계적 포맷 이슈 1건(줄바꿈 스타일) — black으로 CLAUDE가 직접 적용함(로직 변경 아님).

## 실행 결과

```
train 분할: 이미지 209개, 라벨 209개
val 분할: 이미지 44개, 라벨 44개
test 분할: 이미지 46개, 라벨 46개
data.yaml 검증 완료: 경로 유효, 클래스 6개 일치
전체 복사 파일 수: 598개
정상 이미지 수: 100장
```

- `data.yaml` 내용 확인: `path: data/processed/dataset_v1`, `train/val/test` 상대경로, `names` 0~5(crack~undercut) 정확히 `yolo_classes.txt`와 일치
- 정상 이미지 표본(`RT_AL_00_14483440`) 확인: `labels/val/`에 0바이트 라벨, `images/val/`에 683,208바이트 이미지 — 원본(`data/raw/.../RT_AL_00_14483440.jpg`)과 파일 크기 완전 일치
- black/ruff 통과, 재실행 결과 599개 파일(598+`data.yaml`) 전부 md5 동일(재현성 확인)

## 사용자가 직접 확인하는 방법

1. `venv/Scripts/python.exe src/dataset/build_yolo_dataset.py` 실행 — `전체 복사 파일 수: 598개`, `정상 이미지 수: 100장` 확인
2. `find data/processed/dataset_v1/images -type f | wc -l` → 299, `labels` 동일
3. `cat data/processed/dataset_v1/data.yaml` — `names`가 `metadata/yolo_classes.txt`와 순서·내용 일치하는지 확인
4. `data/processed/dataset_v1/labels/val/RT_AL_00_14483440.txt` — 0바이트인지 확인
5. 재실행 후 산출물이 동일한지 확인(md5)

## 결과

완료 조건 5개(이미지·라벨 수 일치, YOLO 표준 폴더 구조, 클래스 매핑 일치, `data.yaml` 경로 유효, 정상 이미지 포함) 모두 충족.
