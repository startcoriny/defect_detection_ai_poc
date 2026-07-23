# 구현 지시서: Test 데이터 추론

## 배경

`docs/context/02-task-list.md` 작업19(Test 데이터 추론), `docs/context/03-deliverables.md` 3.7절(`run_inference.py`)·5.3절(추론 결과 산출물)·6.4절(모델 예측 시각화)에 따라, 작업17에서 만든 Baseline `best.pt`로 Test 46장(정상 15장, porosity 15장, slag_inclusion 16장 — `metadata/selected_dataset.csv` 기준 실측치)을 추론하고 결과를 파일로 저장한다.

**사전 확인한 사실(가정 아님, 실제로 실행해 확인함)**:

- `model.predict(source=<디렉터리 경로>)`처럼 소스가 디렉터리(또는 단일 파일 경로)일 때는 원본 파일명이 그대로 보존된다(작업16 Smoke Test 때 겪은 "소스가 파일 경로 리스트일 때 `image0.jpg`로 저장되는" 문제와는 다른 경우). 따라서 이번 작업은 이미지 리스트가 아니라 **이미지 경로 하나씩** 또는 디렉터리를 소스로 넘긴다.
- `model.predict(..., save_txt=True)`는 예측이 하나도 없는 이미지(정상 이미지 등)에는 TXT 파일을 만들지 않는다(정상 동작, 버그 아님). 즉 "정상 이미지도 처리된다"는 완료 조건은 TXT 파일 존재 여부가 아니라 **JSON에 결과가 기록되는지**로 판단한다.
- `model.train()`과 마찬가지로 `model.predict(..., project=...)`도 상대경로를 넘기면 Ultralytics가 `runs/detect/<상대경로>/` 하위에 중첩 저장한다. **반드시 절대경로**를 넘긴다.

## 기능 및 요구사항

### `src/model/run_inference.py` (신규)

#### 1. 입력

- 모델: `experiments/EXP-P1-DET-001/models/best.pt` (작업17 Baseline의 best checkpoint)
- 대상 이미지: `data/processed/dataset_v1/images/test/` 전체(46장, 정상 15장 포함 — 전부 처리 대상)
- 클래스 이름 매핑: `metadata/yolo_classes.txt` 재사용(재계산 금지)

#### 2. 추론 실행

- **개별 이미지 파일 단위로 반복 처리한다**(디렉터리를 한 번에 넘기지 않고, 정렬된 파일 목록을 하나씩 순회). 이유: 한 이미지에서 예외가 나도 나머지 45장 처리를 계속하고 실패 파일만 별도로 기록해야 하는데(완료 조건), 디렉터리를 한 번에 넘기면 배치 중간에 예외가 나면 전체가 중단될 위험이 있다.
- 이미지 1장마다 `try/except`로 감싸고, 실패 시 파일명과 예외 메시지를 기록한 뒤 다음 이미지로 계속 진행한다(예외를 삼키지 않고 실패 파일명·원인을 함께 기록 — 프로젝트 공통 원칙).
- 추론 설정(고정값, 절대 다른 값으로 바꾸지 않는다):
  ```
  confidence(conf) = 0.25
  NMS IoU = 0.70
  imgsz = 640
  device = cpu
  ```
- Ultralytics 호출 시 `save=True, save_txt=True, save_conf=False`(YOLO TXT에는 confidence를 넣지 않는다 — 작업20에서 재사용할 표준 YOLO Detection TXT 형식과 일치시키기 위함), `project=<프로젝트 루트>/outputs/predictions`(절대경로), `name="test"`, `exist_ok=True`.
- 각 이미지의 추론 시간은 Ultralytics가 반환하는 `result.speed["inference"]`(ms)를 사용한다(콘솔에 이미 "Speed: Xms preprocess, Yms inference, ..." 형태로 출력되는 것과 같은 값 — 새로 계산하지 않는다).

#### 3. `predictions/prediction_results.json` 생성

`docs/context/03-deliverables.md` 5.3절의 "JSON 포함 정보"(원본 이미지명, 모델 버전, 클래스 ID, 클래스명, Confidence, Bounding Box, 정규화 좌표, 추론 시간, 추론 설정)를 전부 포함한다. 스키마:

```json
{
  "model_version": "EXP-P1-DET-001",
  "model_path": "<best.pt 절대경로>",
  "inference_config": {
    "confidence_threshold": 0.25,
    "iou_threshold": 0.70,
    "imgsz": 640,
    "device": "cpu"
  },
  "generated_at": "<ISO 8601 타임스탬프>",
  "summary": {
    "total_images": 46,
    "succeeded": <int>,
    "failed": <int>,
    "total_inference_time_ms": <float>,
    "avg_inference_time_ms": <float>,
    "min_inference_time_ms": <float>,
    "max_inference_time_ms": <float>
  },
  "images": [
    {
      "image_name": "RT_AL_00_xxxxxxxx.jpg",
      "status": "success",
      "inference_time_ms": <float>,
      "predictions": [
        {
          "class_id": 3,
          "class_name": "porosity",
          "confidence": 0.8123,
          "bbox_xyxy": [x1, y1, x2, y2],
          "bbox_normalized_xywh": [cx, cy, w, h]
        }
      ]
    }
  ],
  "failures": [
    {"image_name": "...", "error": "..."}
  ]
}
```

- 예측이 없는 이미지(정상 이미지 포함)도 `images` 배열에 `"predictions": []`로 반드시 포함한다(빠뜨리지 않는다).
- `model_version`은 `docs/context/02-task-list.md` 작업20 예시의 `"baseline_v1"` 같은 임의 문자열 대신, 이미 구축된 실험 추적 체계의 실제 식별자인 `EXP-P1-DET-001`을 사용한다(추적 가능성을 위해 실제 실험 기록과 연결).
- 저장 위치: 프로젝트 루트 기준 `predictions/prediction_results.json`(`docs/context/03-deliverables.md` 5.3절의 최상위 `predictions/` 폴더 관례를 따름 — `experiments/` 하위가 아니다. 이미 `.gitignore`에 `predictions/`가 등록돼 있어 자동으로 커밋에서 제외된다).

#### 4. 산출물 정리

- `predictions/prediction_results.json` — 위 스키마
- `outputs/predictions/test/` — Ultralytics가 저장한 예측 시각화 이미지(Bounding Box·클래스명·Confidence가 그려진 이미지) + `labels/`(표준 YOLO 형식 TXT, 예측 없는 이미지는 파일 없음 — 정상 동작)
- 로그 파일: `outputs/predictions/inference.log`(콘솔 + 파일 동시 기록, 기존 스크립트들의 `configure_logging` 패턴과 동일하게)

## In Scope

- `src/model/run_inference.py` 신규 작성
- Test 46장 전체 추론, `prediction_results.json` 생성, Ultralytics 예측 시각화 이미지·TXT 생성, 로그 기록
- 실패 이미지 처리(try/except, `failures` 배열 기록) — 실제로 실패가 발생하지 않더라도 이 처리 경로 자체는 반드시 구현

## Out of Scope

- 자동 라벨 파일(YOLO TXT + 메타데이터 JSON을 `auto-labels/`로 정리하는 것)은 작업20의 범위이며 이번 작업에서 만들지 않는다.
- Confidence Threshold 비교(작업22), 성능 평가/Confusion Matrix(작업23), 오탐·미탐 분석(작업24)은 이번 작업 범위가 아니다.
- `configs/inference_baseline.yaml` 같은 별도 설정 파일은 만들지 않는다(작업17의 `train_baseline.py`도 하이퍼파라미터를 스크립트에 직접 하드코딩했고, 1회성 스크립트에 설정 파일을 분리하는 것은 이번 규모에서 불필요한 추상화 — `CLAUDE.md` Simplicity First 원칙).

## 작업 전 확인해야 하는 문서/코드

- `docs/context/02-task-list.md` 작업19
- `docs/context/03-deliverables.md` 5.3절, 6.4절
- `src/model/smoke_test.py`의 `run_prediction()` (list-source 저장 파일명 버그 사례 — 이번엔 개별 파일 경로를 쓰므로 해당 없음을 확인하는 참고용)
- `metadata/yolo_classes.txt`, `experiments/EXP-P1-DET-001/models/best.pt`

## 완료 기준 (Definition of Done)

- `( )` Test 46장 전체가 처리된다(성공 또는 실패로 기록, 누락 없음).
- `( )` 정상 이미지(15장)도 `predictions: []`로 JSON에 기록된다.
- `( )` 예측 좌표(픽셀 xyxy, 정규화 xywh)와 클래스(ID+이름)가 추출된다.
- `( )` 예측 결과가 `predictions/prediction_results.json`, `outputs/predictions/test/`(이미지+TXT)로 파일 저장된다.
- `( )` 실패한 파일이 있으면 `failures` 배열에 파일명·원인과 함께 별도로 기록된다(예외를 삼키지 않는다).
- `( )` 코드가 PEP 8 / black 포맷을 따른다(ruff 통과).

## 제약사항

- `project=`에는 반드시 절대경로를 사용한다(상대경로 시 `runs/detect/` 하위 중첩 버그, 사전 확인함).
- 이미지는 리스트가 아니라 **개별 경로 하나씩** 소스로 넘긴다(디렉터리 일괄 처리 시 예외 발생하면 전체 중단 위험).
- `data/raw`, `data/processed`, `metadata/`, `experiments/EXP-P1-DET-001/models/best.pt`는 읽기만 하고 수정하지 않는다.
- 이 스크립트는 CODEX 샌드박스에서 직접 실행·검증할 수 없다(Python 실행 불가, 알려진 제약). 코드 작성까지만 CODEX가 담당하고, 실제 추론 실행·결과 확인은 CLAUDE가 `venv/Scripts/python.exe`로 수행한다.

## 테스트 방법

1. `venv/Scripts/python.exe src/model/run_inference.py` 실행
2. `predictions/prediction_results.json` — `summary.total_images == 46`, `images` 배열 길이 46, 정상 이미지 항목의 `predictions == []`인지 확인
3. `outputs/predictions/test/` — 예측이 있는 이미지에 Bounding Box가 그려진 이미지 파일 존재 확인
4. `outputs/predictions/test/labels/` — 예측이 있는 이미지만 TXT 존재(개수가 `summary`의 성공+예측 있는 이미지 수와 일치하는지)
5. `outputs/predictions/inference.log` — 46장 처리 로그, 실패 발생 시 실패 로그 확인
6. `black --check src/model/run_inference.py`, `ruff check src/model/run_inference.py` 통과 확인
