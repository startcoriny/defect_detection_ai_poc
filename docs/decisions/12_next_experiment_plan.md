# 다음 실험 계획서 (EXP-P1-DET-005)

- 대상: EXP-P1-DET-004(데이터 확장, 성공) 다음 실험, 실험 ID(가안) `EXP-P1-DET-005`
- 근거 자료: `experiments/EXP-P1-DET-004/experiment.md`(11~17절), `docs/decisions/11_next_experiment_plan.md`

## 지금까지의 성과와 남은 문제

EXP-P1-DET-004(데이터 확장, dataset_v2)는 처음으로 사전 등록한 성공 기준을 전부 충족했다 — porosity Recall 0.143→0.298, Small Recall 0.121→0.241, mAP50-95 0.075→0.082. 다만 그 과정에서 **slag_inclusion Recall이 0.333→0.179로 회귀**했다.

원인으로 확인된 것: dataset_v1→v2 확장 시 porosity 객체는 약 2.4배(241→575) 늘었지만 slag_inclusion은 약 1.2배(198→237)만 늘어, Train 기준 두 클래스 객체 비율이 EXP-002(porosity 185 : slag 147 = 1.26:1)에서 EXP-004(porosity 380 : slag 168 = 2.26:1)로 벌어졌다.

## 검토했지만 채택하지 않은 다른 후보

| 후보 | 검토 결과 | 채택하지 않은 이유 |
| --- | --- | --- |
| RT/ST(철강)의 slag_inclusion 106건 추가 | 실제로 새로운 정보를 더할 수 있음 | 소재가 다름(AL→ST 혼입) — "클래스 비율"과 "소재"라는 변수 두 개가 동시에 바뀌어 이번 실험의 원인 규명이 어려워짐. RT/ST는 porosity가 2건뿐이라 클래스 불균형을 오히려 더 키울 수도 있음 |
| CLAHE 대비 강조 증강 | 박스 위치 정밀도·저대비 문제에 유효할 수 있음 | 이번에 고치려는 문제(slag_inclusion 회귀)와 직접 관련이 없음. `albumentations` 신규 의존성도 필요 — 별도 실험으로 유지 |
| 모델 크기 확대(yolo26n→yolo26s) | 표현력 부족 가설 검증 가능 | 이번 문제(클래스 불균형)의 직접적인 해법이 아님. 학습 시간 비용도 큼 — 별도 실험으로 유지 |

## 이번에 채택한 변경: Train 분할 내 slag_inclusion 오버샘플링

Validation·Test는 실제 분포를 그대로 반영해야 평가가 정직하므로 건드리지 않는다. **Train 분할에서만** slag_inclusion이 포함된 이미지(84장, `both_mixed` 1장 포함)를 그대로 1벌 복제해 2배로 늘린다. Train 객체 수 기준 porosity 380 : slag_inclusion 168(2.26:1) → porosity 380 : slag_inclusion 336(1.13:1)로, EXP-002 때의 비율(1.26:1)과 비슷한 수준까지 좁아진다.

복제는 이미지·라벨 파일을 새 이름(예: `<원본이름>_dup1.jpg/.txt`)으로 그대로 복사하는 방식이다 — 별도 증강(회전·반전 등)을 적용하지 않는다(순수하게 "노출 빈도"만 바꾸는 것이 이번 실험의 변수이므로, 증강까지 섞으면 변수가 두 개가 된다).

## 변경 범위

- **건드리지 않음**: `data/processed/dataset_v2/`, `src/dataset/v2/`, `src/conversion/v2/` — 그대로 둔다.
- **새로 생성**: `src/dataset/v3/oversample_slag.py` — dataset_v2를 원본으로 삼아 `data/processed/dataset_v3/`를 만드는 단일 스크립트.
  - Val·Test: `dataset_v2`에서 그대로 복사(오버샘플링 없음)
  - Train: `dataset_v2`의 Train 이미지·라벨을 전부 복사한 뒤, 라벨 파일에 `class_id == 4`(slag_inclusion)가 포함된 이미지만 골라 `_dup1` 접미사를 붙여 이미지·라벨을 한 벌 더 복사(총 2벌)
  - `data.yaml`은 dataset_v2와 동일한 클래스 매핑으로 새로 생성(`path: data/processed/dataset_v3`)
  - 복제 전후 Train 이미지 수, slag_inclusion 포함 이미지 수, 클래스별 객체 수를 로그로 남긴다
- **새로 생성**: `src/model/exp5/`, `src/evaluation/exp5/`, `src/visualization/exp5/` — exp4(EXP-004, imgsz=960·box=7.5) 스크립트를 복사해 `EXPERIMENT_ID="EXP-P1-DET-005"`, 데이터 경로만 `dataset_v3`로 변경. **Test 이미지 개수 하드코딩(exp4에서 84였던 것)은 dataset_v3도 Test는 dataset_v2와 동일(84장)이므로 그대로 84 유지.** 그 외 하이퍼파라미터는 exp4와 완전히 동일하게 유지한다.

## 고정할 조건

- Val·Test: dataset_v2와 완전히 동일(84장, 오버샘플링 없음)
- 학습 설정: imgsz=960, box=7.5, epochs=50, patience=15, batch=-1, optimizer="auto", device="cpu" — EXP-004와 완전히 동일
- 평가 조건: conf=0.25, NMS IoU=0.70, 매칭 IoU=0.5 — EXP-001~004와 동일 기준

## 성공 판단 기준

- **주 지표**: slag_inclusion Recall이 EXP-004(0.179) 대비 개선(목표: 0.30 이상, EXP-002 수준 0.333에 근접)
- **가드레일 1**: porosity Recall이 EXP-004(0.298) 대비 크게 낮아지지 않을 것(목표: 0.25 이상 유지 — EXP-004에서 얻은 개선분을 슬래그 회복 때문에 잃지 않아야 함)
- **가드레일 2**: 전체 mAP50-95가 EXP-004(0.082) 대비 낮아지지 않을 것
- 위 기준을 충족하면 dataset_v3(Train 오버샘플링)를 채택한다. 주 지표 미충족 시 "단순 노출 빈도 증가"만으로는 부족하다고 결론짓고, RT/ST 데이터 추가 또는 클래스별 손실 가중치 조정 같은 다음 후보로 넘어간다.

## 후속 실험 우선순위 (이번 실험 이후)

1. **Train slag_inclusion 오버샘플링(dataset_v3)** — 이번 실험, EXP-P1-DET-005
2. **대비 강조(CLAHE) 증강** — `albumentations` 추가 설치 필요, 박스 위치 정밀도 문제 대상
3. **모델 크기 확대(yolo26n→yolo26s)** — 표현력 부족 가설 검증
4. **RT/ST(철강) slag_inclusion 활용 등 소재 확장** — 도메인 시프트 리스크, 장기 과제로 유지
