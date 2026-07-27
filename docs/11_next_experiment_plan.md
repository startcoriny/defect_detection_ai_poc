# 다음 실험 계획서 (EXP-P1-DET-004)

- 대상: EXP-P1-DET-003(box loss gain 7.5→15.0, 실패) 다음 실험, 실험 ID(가안) `EXP-P1-DET-004`
- 근거 자료: `experiments/EXP-P1-DET-003/experiment.md`(11~17절), `docs/08_error_analysis.md`, `docs/10_next_experiment_plan.md`, `docs/context/01-experiment-scope.md` 4.3절, `docs/data-inventory.md`

## 지금까지의 문제

세 실험 모두 "저대비·Small 결함 미탐"을 풀지 못했다.

- EXP-001(Baseline): Small Recall 0.121, 미탐 48/58건(83%)
- EXP-002(imgsz 640→960): Small Recall 0.121로 **변화 없음**(Medium은 개선)
- EXP-003(box gain 7.5→15.0): 전체 지표 전부 악화, Small Recall 소폭 상승(0.182)은 표본 노이즈로 판단(15~16절)

세 실험 모두 미탐 사례를 육안 검토할 때마다 공통 패턴이 반복됐다 — GT 박스 안의 명암 대비가 사람 눈으로도 거의 안 보일 만큼 낮다. **해상도를 올려도(EXP-002), 박스 손실 가중치를 올려도(EXP-003) 이 문제는 풀리지 않았다** — 모델 구조·손실 함수 쪽 변경으로는 한계에 도달했다고 판단한다.

## 검토했지만 채택하지 않은 다른 후보

| 후보 | 검토 결과 | 채택하지 않은 이유 |
| --- | --- | --- |
| Hard Negative Mining | 오탐(FP)이 EXP-002·003 모두 4건뿐 | 보강할 오탐 표본 자체가 너무 적어 효과가 제한적 |
| 대비 강조(CLAHE) 증강 | Ultralytics는 `albumentations` 설치 시에만 자동 적용, 현재 미설치 | 새 의존성 추가가 필요해 보류(후속 후보로 유지) |
| Copy-Paste 증강 | Ultralytics `CopyPaste`는 segmentation mask(`instances.segments`)가 없으면 무시하는 것을 소스에서 확인 | 이 프로젝트는 Polygon을 Box로만 변환했고 세그멘테이션 마스크를 유지하지 않아 적용 불가 |
| MixUp / Multi-scale 학습 | 새 의존성 없이 바로 시도 가능 | 데이터 절대량 문제를 직접 해결하지 않는 간접적 방법이라 후순위로 유지 |
| 모델 크기 확대(yolo26n→yolo26s) | 표현력 부족 가설은 유효할 수 있음 | CPU 학습 시간이 2~3배로 늘어나는 비용 대비, 데이터 확장을 먼저 시도하는 것이 근거가 더 강함 |

## 이번에 채택한 변경: 데이터 확장 (dataset_v2)

`docs/context/01-experiment-scope.md` 4.3절 "데이터 부족 시 처리" 순서의 마지막 단계("전체 RT 데이터로 확장")를 적용한다.

### 근거

- 로컬에 이미 RT/AL(현재 dataset_v1과 동일 소재) 원본 637장을 보유하고 있으나, dataset_v1은 그중 약 300장만 사용했다(`select_poc_dataset.py`의 `TARGET_COUNT=100` 정책).
- RT/AL 원본 전체의 클래스별 분포(`meta.annotation_case` 기준): porosity 225건, slag_inclusion 120건, normal 225건 — 특히 porosity(가장 성능이 낮은 클래스, EXP-003 Recall 0.036)의 미사용 표본이 많다.
- RT/ST(철강, 488장)도 검토했으나 porosity가 2건뿐이고 소재가 달라(알루미늄→철강) "데이터량"과 "소재"라는 변수 두 개가 동시에 바뀌므로 이번엔 채택하지 않는다. RT/AL만 확장해 변수를 하나로 유지한다.
- 새로 다운로드가 필요 없다(이미 `data/raw/steel/`에 보유 중인 원본을 더 활용하는 것) — 외부 서비스 접근이나 비용 발생 없음.

### 변경 범위

- **건드리지 않음**: `metadata/{selected_dataset.csv, included_files.txt, excluded_files.txt}`, `data/processed/dataset_v1/`, `src/dataset/{select_poc_dataset.py, build_yolo_dataset.py, split_dataset.py}` — dataset_v1과 EXP-001~003의 재현성을 그대로 보존한다.
- **새로 생성**: `src/dataset/v2/{select_poc_dataset.py, build_yolo_dataset.py, split_dataset.py}` — 기존 3개 스크립트를 복사해 다음만 바꾼다.
  1. `select_poc_dataset.py`: `TARGET_COUNT`를 그룹별 전체 후보 수보다 크게(예: 1000) 설정해, 품질 검사(`quality_status`)·중복 제거·`off_target_class_present` 필터를 통과한 RT/AL 후보를 사실상 전량 선택한다(무작위 표본 추출이 아니라 전수 포함). 출력 경로를 `metadata/v2/{selected_dataset.csv, included_files.txt, excluded_files.txt}`로 분리한다.
  2. `build_yolo_dataset.py`: 입력을 `metadata/v2/selected_dataset.csv`로, 출력을 `data/processed/dataset_v2/`로 변경한다.
  3. `split_dataset.py`: 입력을 `metadata/v2/selected_dataset.csv`로, 출력을 `splits/v2/`, `reports/dataset/v2/`로 변경한다. `SEED=42`, `TARGET_RATIOS`(0.70/0.15/0.15)는 동일하게 유지한다(분할 방식 자체는 변수가 아님).
- **새로 생성**: `src/model/exp4/`, `src/evaluation/exp4/`, `src/visualization/exp4/` — exp2(EXP-002, imgsz=960·box=7.5 기본값) 스크립트를 복사해 `EXPERIMENT_ID="EXP-P1-DET-004"`, `EXPERIMENT_NAME="RT_AL_YOLO26N_960_DatasetV2"`로, 데이터 경로만 `data/processed/dataset_v2`로 바꾼다. 그 외 하이퍼파라미터(imgsz=960, box=7.5, epochs=50, patience=15 등)는 EXP-002와 완전히 동일하게 유지한다(변수는 "데이터 양" 하나로 한정).

### 고정할 조건

- 소재: RT/AL만(RT/ST 미포함)
- 클래스: porosity, slag_inclusion, normal 3개 그룹 선정 로직 자체는 동일(품질 검사·중복 제거·`off_target_class_present` 제외 기준 그대로 적용) — 다만 목표 수량 상한만 사실상 해제
- 분할 비율 0.70/0.15/0.15, seed=42 — dataset_v1과 동일 기준으로 비교 가능하게 유지
- 학습 설정: imgsz=960, box=7.5(기본값), epochs=50, patience=15, batch=-1, optimizer="auto", device="cpu" — EXP-002와 완전히 동일
- 평가 조건: conf=0.25, NMS IoU=0.70, 매칭 IoU=0.5 — EXP-001~003과 동일 기준

## 성공 판단 기준

- **주 지표**: porosity Recall이 EXP-002(0.143) 대비 뚜렷이 개선(목표: 0.25 이상) — porosity가 가장 데이터가 부족하고 가장 성능이 낮은 클래스이므로, 데이터 확장의 효과를 가장 직접적으로 보여줄 지표로 선정
- **가드레일 1**: 전체 mAP50-95가 EXP-002(0.075) 대비 낮아지지 않을 것
- **가드레일 2**: Small 객체 Recall이 EXP-002(0.121) 대비 낮아지지 않을 것(데이터를 늘렸는데 특정 크기대에서 퇴보하면 순개선이라 보기 어려움)
- **참고 지표(가드레일 아님)**: 학습 시간 — 이미지 수가 늘어나므로 EXP-002(58분)보다 길어지는 것은 예상된 트레이드오프이며 실패 기준으로 삼지 않는다
- 위 기준을 충족하면 dataset_v2를 이후 실험의 기본 데이터셋으로 채택한다. 주 지표 미충족 시 "데이터 절대량"이 아니라 "결함 자체의 시각적 저대비 특성"이 근본 원인이라고 결론짓고, 후속 우선순위였던 CLAHE 증강 또는 모델 크기 확대로 넘어간다.

## 후속 실험 우선순위 (이번 실험 이후)

1. **데이터 확장(RT/AL 전체, dataset_v2)** — 이번 실험, EXP-P1-DET-004
2. **대비 강조(CLAHE) 증강** — `albumentations` 추가 설치 필요, dataset_v2로도 저대비 미탐이 남으면 검토
3. **모델 크기 확대(yolo26n→yolo26s)** — 표현력 부족 가설 검증, CPU 학습 시간 비용 감안
4. **RT/ST(철강) 포함 등 소재 확장** — 도메인 시프트 리스크가 있어 장기 과제로 유지
