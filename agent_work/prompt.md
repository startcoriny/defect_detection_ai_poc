# 구현 지시서: dataset_v4 구축 스크립트 생성 (CLAHE 대비 강조 전처리)

## 배경

`docs/13_next_experiment_plan.md`에 따라 EXP-P1-DET-006은 `dataset_v3`의 모든 이미지(Train/Val/Test)에 CLAHE(Contrast Limited Adaptive Histogram Equalization)를 적용한 `dataset_v4`를 사용한다. 라벨(YOLO 좌표)은 기하 변형이 없으므로 그대로 복사한다. 오버샘플링(dataset_v3)과 달리 이번엔 이미지 장수·이름이 그대로 유지되고 픽셀 값만 바뀐다(1:1 변환, 복제 없음).

## 기능 및 요구사항

`src/dataset/v3/oversample_slag.py`를 참고해 같은 스타일로 `src/dataset/v4/apply_clahe.py`를 새로 작성한다.

1. `PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent` (경로 깊이는 `src/dataset/v3/oversample_slag.py`와 동일)
2. `SOURCE_ROOT = PROJECT_ROOT / "data" / "processed" / "dataset_v3"`, `TARGET_ROOT = PROJECT_ROOT / "data" / "processed" / "dataset_v4"`, `DATASET_PATH = "data/processed/dataset_v4"`
3. `SPLITS = ("train", "val", "test")` 전부 처리 (Train만이 아니라 Train/Val/Test 전부에 CLAHE 적용)
4. 각 이미지에 대해 다음 순서로 CLAHE를 적용한다 (색상 왜곡 방지를 위해 LAB 색공간의 L 채널에만 적용):
   ```python
   image = cv2.imread(str(source_path))
   if image is None:
       raise ValueError(f"이미지를 읽을 수 없습니다: {source_path}")
   lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
   l_channel, a_channel, b_channel = cv2.split(lab)
   clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
   l_enhanced = clahe.apply(l_channel)
   enhanced_lab = cv2.merge((l_enhanced, a_channel, b_channel))
   result = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
   cv2.imwrite(str(target_path), result)
   ```
   `clahe = cv2.createCLAHE(...)` 객체는 함수 최상단이나 모듈 상수로 한 번만 생성해 재사용해도 된다(매 이미지마다 새로 만들 필요 없음).
5. 라벨(`.txt`)은 `shutil.copy2`로 원본 그대로 복사한다(내용 변경 없음).
6. `data.yaml`은 `oversample_slag.py`의 `write_data_yaml()`과 동일한 방식으로 생성한다(원본 `dataset_v3/data.yaml`을 읽어 `path`만 `dataset_v4`로 변경, 나머지는 그대로 유지).
7. 검증: 각 split에서 대상 이미지·라벨 basename 집합이 `dataset_v3`의 동일 split과 **정확히 일치**해야 한다(오버샘플링이 아니므로 장수·이름이 절대 늘거나 줄면 안 됨). `oversample_slag.py`의 `validate_image_label_pairs()` 로직을 재사용하거나 동일하게 구현한다.
8. 로그: split별 처리한 이미지 수, 전체 완료 메시지를 `LOGGER.info`로 남긴다.

## 구현 범위 (In Scope)

- `src/dataset/v4/apply_clahe.py` 신규 생성 1개 파일

## 구현 제외 범위 (Out of Scope)

- `src/dataset/v3/oversample_slag.py` 및 `dataset_v3` 수정 — 절대 건드리지 않는다(읽기 전용 원본)
- `src/model/exp6/` 등 학습·평가 스크립트 — 이번 작업 범위 아님(다음 단계에서 별도 진행)
- 스크립트 실행 — CLAUDE가 수행

## 완료 기준 (Definition of Done)

- `( )` `src/dataset/v4/apply_clahe.py`가 존재하고, Train/Val/Test 전체에 CLAHE를 적용한다.
- `( )` 라벨은 원본과 바이트 단위로 동일하게 복사된다(내용 변경 없음).
- `( )` 각 split의 이미지·라벨 basename 집합이 `dataset_v3`와 정확히 일치하는지 검증하는 로직이 있다(불일치 시 예외 발생).
- `( )` `data.yaml`이 생성되고 `path`가 `data/processed/dataset_v4`로 설정된다.
- `( )` black/ruff 통과.

## 제약사항

- `dataset_v3`는 읽기만 하고 수정하지 않는다.
- 이 작업은 CODEX 샌드박스에서 Python을 실행해 검증할 수 없다. 코드 작성까지만 CODEX가 담당하고, 실제 실행·검증은 CLAUDE가 수행한다.

## 테스트 방법 (CLAUDE가 이어서 수행)

1. `black --check`, `ruff check`를 `src/dataset/v4/apply_clahe.py`에 실행
2. `venv/Scripts/python.exe src/dataset/v4/apply_clahe.py` 실행 후 로그의 처리 이미지 수 확인
3. `diff <(cd data/processed/dataset_v3 && find images labels -type f | sort) <(cd data/processed/dataset_v4 && find images labels -type f | sort)` — 파일 이름 목록이 완전히 동일한지 확인 (경로만 다르고 목록은 같아야 함)
4. `diff data/processed/dataset_v3/labels/train/<임의파일>.txt data/processed/dataset_v4/labels/train/<임의파일>.txt` — 라벨 내용이 그대로인지 샘플 확인
5. `cat data/processed/dataset_v4/data.yaml`로 `path` 값 확인
