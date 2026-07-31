# 용접 결함 검출 자동 라벨링 AI — 1단계 Python PoC

AI-Hub 용접 검사(RT) 이미지·Polygon 라벨 데이터를 YOLO Detection 형식으로 변환하고, 모델 학습·추론·자동 라벨 생성까지 전체 파이프라인이 실제 데이터에서 동작하는지 검증하는 PoC 저장소입니다.

특정 성능 수치 달성이 아니라 **파이프라인 전체가 재현 가능하게 동작하는지**가 1차 목적입니다.

---

## 목차

- [프로젝트 개요](#프로젝트-개요)
- [실험 범위](#실험-범위)
- [결과 요약](#결과-요약)
- [기술 스택](#기술-스택)
- [디렉터리 구조](#디렉터리-구조)
- [개발 환경 구성](#개발-환경-구성)
- [파이프라인 실행 순서](#파이프라인-실행-순서)
- [실험 목록](#실험-목록)
- [문서 안내](#문서-안내)
- [개발 규칙](#개발-규칙)
- [데이터 취급 주의](#데이터-취급-주의)

---

## 프로젝트 개요

용접 결함 검사(RT) 이미지에서 결함 위치를 자동으로 찾아 라벨 초안을 만들어주면, 검수자가 전체 이미지를 처음부터 보는 대신 모델이 만든 초안을 확인·수정하는 방식으로 작업할 수 있습니다. 이 PoC는 그 자동 라벨링 흐름이 AI-Hub 공개 데이터에서 실제로 동작하는지, 어디까지 가능하고 어디서 막히는지를 확인하기 위한 것입니다.

전체 흐름은 다음과 같습니다.

```
AI-Hub 원본 JSON(Polygon)
  → 데이터 인벤토리·품질 검증
  → Polygon → Bounding Box 변환
  → YOLO Detection 라벨 변환
  → 데이터셋 선별·층화 분할(train/val/test)
  → YOLO 학습
  → Test 추론
  → 자동 라벨 export(CVAT Import 형식)
  → 성능 평가·오탐/미탐 분석
  → 다음 실험 설계
```

## 실험 범위

1차 범위는 의도적으로 좁게 잡았습니다.

| 항목 | 1차 범위 | 2차(향후) 확장 대상 |
| --- | --- | --- |
| 검사 유형 | RT(방사선 투과 검사)만 | VT 등 다른 검사 유형 |
| 소재 | AL만 | - |
| 클래스 | porosity(기공), slag_inclusion(슬래그 혼입) 2개 | 원본 6클래스 전체 |
| 라벨 형식 | Bounding Box | Segmentation |
| 모델 | YOLO26 Detection(yolo26n/s) | - |
| 실행 환경 | 로컬 CPU 중심(EXP-008부터 GPU 병행) | 배포 인프라 |

상세 정의는 [docs/context/01-experiment-scope.md](docs/context/01-experiment-scope.md), 완료 기준은 [docs/context/00-completion-criteria.md](docs/context/00-completion-criteria.md)를 참조하세요.

## 결과 요약

**최종 채택 설정** — yolo26n, imgsz=960, box gain 7.5(기본값), dataset_v3 (EXP-P1-DET-005).

Test셋 기준(Confidence 0.25) 주요 실험 성능 추이입니다.

| 실험 | Precision | Recall | mAP50 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: |
| EXP-001 (Baseline, v1, imgsz 640) | 0.675 | 0.188 | 0.175 | 0.043 |
| EXP-002 (imgsz 960) | 0.678 | 0.238 | 0.201 | 0.075 |
| EXP-004 (dataset_v2) | 0.798 | 0.239 | 0.210 | 0.082 |
| **EXP-005 (dataset_v3, 최종 채택)** | **0.535** | **0.446** | **0.342** | **0.131** |
| EXP-007 (yolo26s) | 0.621 | 0.293 | 0.210 | 0.089 |
| EXP-009 (imgsz 1280) | 0.620 | 0.288 | 0.217 | 0.088 |

- 전체 파이프라인(변환 → 학습 → 추론 → 자동 라벨 export → CVAT 라운드트립 검증 → 평가 → 오류 분석)이 7개 실험(EXP-001~007)에 걸쳐 반복 재현됐고, 이후 GPU 학습 환경(EXP-008)과 imgsz 확대(EXP-009)를 추가로 검증했습니다.
- 성공 사례(EXP-004, 005)와 실패 사례(EXP-003, 006, 009)가 모두 존재하며 각각 원인을 설명할 수 있었습니다.
- capability 기준으로는 2단계 MVP 진입이 가능하다고 판단했습니다. 다만 절대 성능(mAP50-95 0.131)과 미해결 박스 위치 정밀도 문제를 고려하면, MVP는 **"모델이 결함 후보를 표시하고 사람이 전수 검수·수정하는 보조 도구"** 로 시작하는 것을 전제해야 합니다.

전체 판단 근거와 한계·개선 방향은 [docs/reports/15_poc_final_report.md](docs/reports/15_poc_final_report.md)에 정리돼 있습니다.

## 기술 스택

- Python (가상환경 `venv`)
- Ultralytics YOLO26 (Detection)
- PyTorch / torchvision
- OpenCV, NumPy, pandas, matplotlib, PyYAML
- 포맷 black, 린트 ruff, 테스트 pytest

서버·DB·API는 1차 PoC 범위 밖이며, 배치 스크립트 기반 파이프라인입니다.

## 디렉터리 구조

```
├── main.py                 # 실행 폴더 준비 및 경로 확인용 엔트리
├── requirements.txt
├── configs/environment/    # 환경 정보·패키지 버전 스냅샷
├── src/
│   ├── check_environment.py
│   ├── common/             # 파일·이미지·JSON 공통 유틸
│   ├── data/               # 원본 인벤토리·클래스·통계 분석
│   ├── validation/         # 이미지·JSON·Polygon·데이터셋 검증
│   ├── conversion/         # Polygon → BBox → YOLO 라벨 변환
│   ├── dataset/            # 데이터 선별·분할·YOLO 데이터셋 구성(v1~v4)
│   ├── model/              # 실험별 학습·추론·자동 라벨 export
│   ├── evaluation/         # 실험별 성능 지표·오류 케이스 수집
│   └── visualization/      # 원본/변환 라벨·예측 결과 시각화
├── experiments/            # 실험별 기록(experiment.md, experiment.yaml, csv)
├── metadata/               # 선별 목록·클래스 매핑·변환 오류 기록
├── splits/                 # train/val/test 분할 목록
├── reports/                # 데이터 품질·데이터셋·평가 리포트
├── demo/                   # 시연용 자료
└── docs/                   # 설계·규칙·실험 문서 (아래 문서 안내 참조)
```

`data/`, `outputs/`, `predictions/`, `auto-labels/`, `errors/`, 모델 가중치(`*.pt`), 실험 산출물 중 용량이 큰 폴더는 Git에서 제외됩니다. 스크립트 실행으로 재생성 가능합니다. 제외 목록은 [.gitignore](.gitignore)를 참조하세요.

`src/` 하위의 `exp*`, `v2`~`v4` 디렉터리는 실험별·데이터셋 버전별 스크립트를 그대로 보존하기 위한 구조입니다. 각 실험 시점의 코드를 수정 없이 남겨 재현성을 확보하는 것이 목적입니다.

## 개발 환경 구성

```bash
# 가상환경 생성 및 활성화 (Windows PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# 의존성 설치
pip install -r requirements.txt

# 환경 확인 (Python·PyTorch·CUDA 가용성 등)
python src/check_environment.py

# 실행 폴더 준비
python main.py
```

Ubuntu GPU 서버용 부트스트랩 스크립트(`setup_gpu_env.sh`)는 드라이버 확인부터 가상환경 생성·CUDA 대응 torch 설치·검증까지 한 번에 처리합니다. 서버의 CUDA 버전에 따라 스크립트 상단 `CUDA_TAG` 값을 조정해야 합니다. 이 스크립트는 `feature/exp009-imgsz-small-object` 브랜치에 있으며 `main`에는 아직 병합되지 않았습니다.

원본 데이터는 저장소에 포함되지 않습니다. AI-Hub 용접 검사 데이터셋을 별도로 받아 `data/raw/` 아래에 배치해야 합니다.

## 파이프라인 실행 순서

각 단계는 독립 스크립트입니다. 아래는 최종 채택 실험(EXP-P1-DET-005, dataset_v3) 기준 실행 순서입니다.

```bash
# 1. 원본 데이터 분석
python src/data/build_inventory.py
python src/data/analyze_classes.py
python src/data/analyze_statistics.py

# 2. 원본 검증
python src/validation/validate_json.py
python src/validation/validate_image.py
python src/validation/validate_polygon.py

# 3. 라벨 변환 (Polygon → BBox → YOLO)
python src/conversion/v2/polygon_to_box.py
python src/conversion/v2/box_to_yolo.py

# 4. 변환 결과 시각 검증
python src/visualization/visualize_original_polygon.py
python src/visualization/visualize_yolo_label.py

# 5. 데이터셋 구성 (선별 → 분할 → YOLO 구조 → 오버샘플링)
python src/dataset/v2/select_poc_dataset.py
python src/dataset/v2/split_dataset.py
python src/dataset/v2/build_yolo_dataset.py
python src/dataset/v3/oversample_slag.py
python src/validation/validate_yolo_dataset.py

# 6. Smoke Test (소량 데이터·짧은 epoch로 파이프라인 확인)
python src/model/smoke_test.py

# 7. 학습
python src/model/exp5/train_baseline.py

# 8. Test 추론
python src/model/exp5/run_inference.py

# 9. 자동 라벨 export (CVAT Import 형식)
python src/model/exp5/export_auto_labels.py

# 10. 성능 평가 및 오류 분석
python src/evaluation/exp5/calculate_metrics.py
python src/evaluation/exp5/collect_error_cases.py
python src/visualization/exp5/visualize_prediction.py
```

전체 학습 전에는 반드시 6번 Smoke Test를 먼저 수행합니다.

## 실험 목록

| 실험 ID | 변경 변수 | 결과 |
| --- | --- | --- |
| EXP-P1-DET-001 | Baseline (yolo26n, imgsz 640, dataset_v1) | 기준선 확보 |
| EXP-P1-DET-002 | imgsz 640 → 960 | 부분 성공, 채택 |
| EXP-P1-DET-003 | box gain 7.5 → 15.0 | 전 지표 하락, 폐기 |
| EXP-P1-DET-004 | dataset_v1 → v2 (299장 → 567장) | porosity Recall·mAP50-95 개선, 채택 |
| EXP-P1-DET-005 | dataset_v3 (Train slag_inclusion 오버샘플링) | **최고 성능, 최종 채택** |
| EXP-P1-DET-006 | CLAHE 대비 강조 전처리 | 전 지표 하락, 폐기 |
| EXP-P1-DET-007 | yolo26n → yolo26s | 위치 정밀도는 개선, Recall 하락으로 미채택 |
| EXP-P1-DET-008 | device cpu → gpu (설정 동일) | GPU가 6.39배 빠름, 학습 환경으로 채택 |
| EXP-P1-DET-009 | imgsz 960 → 1280 | Small Recall도 악화(0.356 → 0.322), 가설 기각·미채택 |

실험별 상세 기록은 `experiments/<실험 ID>/experiment.md`에 있습니다. 기록 양식은 [docs/context/04-experiment-log-template.md](docs/context/04-experiment-log-template.md)를 따릅니다.

EXP-008·009의 기록과 스크립트는 `feature/exp009-imgsz-small-object` 브랜치에 있으며 `main`에는 아직 병합되지 않았습니다.

## 문서 안내

| 경로 | 내용 |
| --- | --- |
| [docs/context/](docs/context/) | 1단계 PoC 설계 문서 (범위, 작업 목록, 산출물, 완료 기준) |
| [docs/reports/](docs/reports/) | PoC 최종 보고서, 오류 분석, 원본 데이터 구조 |
| [docs/decisions/](docs/decisions/) | 기술 의사결정 및 다음 실험 설계 |
| [docs/rules/](docs/rules/) | 리뷰 에이전트 규칙, Work Log 작성 규칙 |
| [docs/onboarding/](docs/onboarding/) | AI 협업(CLAUDE·CODEX 역할 분리) 안내 |

처음 보는 경우 [docs/context/README.md](docs/context/README.md)부터 순서대로 읽는 것을 권장합니다.

## 개발 규칙

- 프로젝트 규칙은 [CLAUDE.md](CLAUDE.md), 구현 에이전트 규칙은 [AGENTS.md](AGENTS.md)에 정의돼 있습니다.
- 브랜치 전략은 `main` → `dev` → 기능별 브랜치이며, 브랜치 이름은 `<type>/<설명>` 패턴을 따릅니다.
- 커밋 메시지는 Conventional Commits를 사용합니다.
- 코드 변경 후에는 black·ruff·pytest로 검증합니다.

## 데이터 취급 주의

- AI-Hub 원본 데이터(`data/raw/`)는 스크립트 실행으로 수정하지 않습니다. 모든 변환 결과는 `data/work/`, `data/processed/`에 별도로 기록합니다.
- 원본 데이터와 모델 가중치는 저장소에 커밋하지 않습니다.
- 데이터 사용 조건은 AI-Hub의 이용 약관을 따릅니다.
