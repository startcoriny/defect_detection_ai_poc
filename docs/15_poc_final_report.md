# PoC 최종 결과 보고서

작업26(`docs/context/02-task-list.md`) 산출물. 1차 PoC의 전체 사이클(EXP-P1-DET-001~007)을 종합해 성공·실패 사례, 현재 한계, 2단계 MVP 진입 가능 여부를 정리한다.

## 1. PoC 배경

용접 결함 검사(RT) 이미지에서 결함 위치를 자동으로 찾아 라벨을 만들어주는 도구가 있으면, 사람이 매번 전체 이미지를 처음부터 검수하지 않고 모델이 만든 초안을 확인·수정하는 방식으로 작업할 수 있다. 이 PoC는 그 자동 라벨링 도구가 AI-Hub 공개 데이터로 실제로 동작하는지, 어디까지 가능하고 어디서 막히는지를 검증하기 위해 시작했다.

## 2. PoC 목적

AI-Hub 용접 검사(RT) 이미지·Polygon 라벨을 YOLO Detection 형식으로 변환하고, 모델 학습·추론·자동 라벨 생성까지 전체 파이프라인이 실제 데이터에서 동작하는지 검증한다(`docs/context/01-experiment-scope.md`). 특정 성능 수치 달성이 아니라 **파이프라인 전체가 재현 가능하게 동작하는지**가 1차 목적이다(`docs/context/00-completion-criteria.md`).

## 3. 실험 범위

1차 실험은 의도적으로 좁게 잡았다(`docs/context/00-completion-criteria.md` 6절).

| 항목 | 1차 범위 | 2차(향후) 확장 대상 |
| --- | --- | --- |
| 검사 유형 | RT(방사선 투과 검사)만 | VT 등 다른 검사 유형 |
| 소재 | AL만 | - |
| 클래스 | porosity(기공), slag_inclusion(슬래그 혼입) 2개만 | 원본 6클래스 전체(crack, incomplete_penetration, lack_of_fusion, undercut 포함) |
| 라벨 형식 | Bounding Box만 | Segmentation |
| 모델 | YOLO Detection(yolo26n/s) | - |
| 실행 환경 | 로컬 CPU | GPU, 배포 인프라 |

7개 실험(EXP-P1-DET-001~007)을 통해 이 좁은 범위 안에서 데이터 확장, 클래스 균형, 대비 강조, 모델 크기 등 서로 다른 축을 반복 검증했다.

## 4. 사용 데이터

- 출처: AI-Hub 용접 검사 데이터셋, 원본 JSON 라벨 2,250개 전수 분석(`docs/raw_data_structure.md`). 카테고리 구조 `1. RTAL`/`2. RTST`/`3. VTST` 중 `RTAL`(RT·AL)만 사용.
- 원본 클래스 6개와 이미지·객체 수(`metadata/class_statistics.csv`): crack(225장/436개), incomplete_penetration(225/324), lack_of_fusion(452/680), porosity(452/5,179), slag_inclusion(226/463), undercut(225/541). 이 중 porosity·slag_inclusion 2개만 이번 PoC 대상이다.
- 1차 PoC 선별: 정상 100장 + 불량(porosity·slag_inclusion 포함) 199장 = **299장**(`dataset_v1`, `metadata/selected_dataset.csv` 637건 후보 중 채택). 이후 EXP-004에서 로컬 보유 RT/AL 원본 중 미사용분을 추가 투입해 **567장**(`dataset_v2`)으로 확장했다(`metadata/v2/selected_dataset.csv` 638건 후보 중 채택, 제외 70장).
- 데이터 부족 시 처리 원칙(`docs/context/01-experiment-scope.md` 4.3절)에 따라 추가 크롤링·외부 데이터 도입 대신 이미 보유한 로컬 원본을 우선 활용했다.

## 5. 데이터 분석 결과

`reports/dataset/dataset_analysis_report.md`(dataset_v1 기준) — 299장, 객체 439개, 이미지당 평균 객체 1.468개, 해상도 65종(최다 1280×720, 198장), 복수 클래스 이미지 1장.

객체 크기 분포(Small=relative_area<1%, Medium=1~5%, Large=≥5%):

| 크기 | 전체 비율 | porosity 비율 | slag_inclusion 비율 |
| --- | ---: | ---: | ---: |
| Small | 61.96%(272개) | 83.40%(201개, 압도적) | - |
| Medium | 35.99%(158개) | - | 60.61%(120개, 압도적) |
| Large | 2.05%(9개) | - | - |

**이 클래스별 크기 분포 차이가 EXP-001부터 반복 인용된 핵심 근거다** — porosity는 대부분 Small(작고 저대비)이라 미탐이 많고, slag_inclusion은 Medium 위주라 상대적으로 잘 잡힌다는 설명이 여러 실험의 원인 분석에 등장한다.

## 6. 데이터 품질 결과

`reports/data-quality/data_quality_report.csv`(원본 JSON 2,250개 전수) 기준:

- error(치명적 오류): 5건, 전부 `insufficient_points`(Polygon 포인트 부족)
- warning(경고): 5건 — `out_of_bounds_coordinate`(이미지 범위 밖 좌표) 3건, `negative_coordinate`(음수 좌표) 등
- 최종 제외(`include=False`): 4건

전체 규모(2,250개) 대비 품질 문제 비율은 낮았고(1% 미만), Polygon→BBox 변환 단계에서 추가로 발생한 오류는 0건이었다(`metadata/bbox_conversion_errors.csv`, 헤더만 존재).

## 7. 라벨 변환 방식

- Polygon → Bounding Box: Polygon 좌표의 x/y 최솟값·최댓값을 취해 사각형 경계로 변환(작업9).
- Bounding Box → YOLO Detection 라벨: 중심좌표·너비·높이를 이미지 크기로 정규화한 `class_id x_center y_center width height` 형식(작업10).
- 변환 정확성 검증: 원본 라벨과 변환 결과를 재시각화해 육안 대조(작업11), 자동 라벨 왕복 검증(export→재import) 시 `metadata/auto_label_roundtrip_mismatches.csv`·`metadata/yolo_roundtrip_mismatches.csv`로 불일치 여부 기록 — 전 실험(EXP-004~007)에서 라운드트립 검증 PASS(불일치 0건) 확인됨.

## 8. 데이터셋 구성

| 버전 | 사용 실험 | 구성 | Train/Val/Test |
| --- | --- | --- | --- |
| dataset_v1 | EXP-001~003 | 최초 선별 299장 | 209/44/46 (69.90%/14.72%/15.38%) |
| dataset_v2 | EXP-004 | v1 + 로컬 미사용 RT/AL 추가 투입 567장 | 398/85/84 |
| dataset_v3 | EXP-005~007 | v2의 Train에서 slag_inclusion 포함 이미지 84장 1벌 복제(Val/Test는 v2와 동일) | 482/85/84 |
| dataset_v4 | EXP-006(폐기) | v3 전체 이미지에 CLAHE 대비 강조 적용(장수 변화 없음) | 482/85/84 |

분할은 그룹×크기 층화 방식(both_mixed/normal/porosity_mixed/porosity_small_dominant/slag_inclusion_mixed/slag_inclusion_small_dominant), seed 42 고정. dataset_v1 기준 Small 객체 비율 편차가 train/val/test 간 6.06%p로, 이전 group-only 층화(24.0%p 편차)보다 개선됐다(`reports/dataset/split_validation_report.md`). train∩val, train∩test, val∩test 중복 0건.

**최종 채택 데이터셋: dataset_v3**(Val/Test는 v2와 동일하게 유지해 전 실험 간 공정 비교가 가능하다).

## 9. 모델 및 학습 조건

- 라이브러리: Ultralytics YOLO26(Detection), 사전학습 가중치 사용
- 공통 학습 설정: epoch 50, patience 15, batch -1(auto), optimizer auto, device cpu, seed 42, deterministic True
- 실험별로 바뀐 변수:

| 실험 | 모델 | imgsz | box gain | 데이터셋 | 비고 |
| --- | --- | --- | --- | --- | --- |
| EXP-001 | yolo26n | 640 | 7.5(기본) | v1 | 최초 Baseline |
| EXP-002 | yolo26n | **960** | 7.5 | v1 | imgsz만 변경 |
| EXP-003 | yolo26n | 960 | **15.0** | v1 | box gain만 변경, 실패 |
| EXP-004 | yolo26n | 960 | 7.5 | **v2** | 데이터 확장 |
| EXP-005 | yolo26n | 960 | 7.5 | **v3** | Train slag_inclusion 오버샘플링 |
| EXP-006 | yolo26n | 960 | 7.5 | **v4** | CLAHE 전처리, 실패 |
| EXP-007 | **yolo26s** | 960 | 7.5 | v3 | 모델 크기 확대(파라미터 약 4배) |

**최종 채택 설정: yolo26n, imgsz=960, box=7.5(기본값), dataset_v3(EXP-005).**

## 10. 추론 결과

전 실험 공통: Confidence Threshold 0.25, IoU 0.70, imgsz 960, device cpu로 Test 전량 추론. EXP-001(46장)·EXP-002~007(84장) 전부 추론 성공률 100%(실패 0건). 추론 속도는 yolo26n 기준 이미지당 약 20~40ms(CPU), yolo26s는 약 1.3~1.5배 느림.

## 11. 자동 라벨 생성 결과

Test 추론 결과를 자동 라벨 파일(CVAT Import 형식: `obj.names`, `obj.data`, `train.txt`, `obj_train_data/`)로 export하고, 재시각화·CVAT 구조 검증(이미지·라벨 파일 수, 클래스 수 일치)을 거쳤다. EXP-004~007 전 실험에서 라운드트립 검증 **PASS**(예측 메타데이터 불일치 0건, CVAT 구조 확인 통과) — 자동 라벨 생성→검수 흐름 자체는 안정적으로 재현됨을 확인했다.

## 12. 성능 평가

Test셋 기준 전체·클래스별 성능 추이(주요 실험, Confidence 0.25):

| 실험 | Precision | Recall | mAP50 | mAP50-95 | porosity Recall | slag_inclusion Recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| EXP-001(Baseline, v1, imgsz640) | 0.675 | 0.188 | 0.175 | 0.043 | 0.143 | 0.233 |
| EXP-002(imgsz960) | 0.678 | 0.238 | 0.201 | 0.075 | 0.143 | 0.333 |
| EXP-003(box=15.0, 폐기) | 0.433 | 0.151 | 0.118 | 0.044 | 0.036 | 0.267 |
| EXP-004(dataset_v2) | 0.798 | 0.239 | 0.210 | 0.082 | 0.298 | 0.179 |
| **EXP-005(dataset_v3, 최종 채택)** | **0.535** | **0.446** | **0.342** | **0.131** | **0.405** | **0.487** |
| EXP-006(CLAHE, 폐기) | 0.544 | 0.350 | 0.295 | 0.103 | 0.262 | 0.359 |
| EXP-007(yolo26s, 미채택) | 0.621 | 0.293 | 0.210 | 0.089 | 0.321 | 0.179 |

객체 크기별 Recall(최종 채택 EXP-005 기준): Small 0.356, Medium 0.515, Large 0.000(표본 3개뿐, 판단 불가).

**성공 사례**: EXP-002(부분 성공, 가드레일 충족), EXP-004(데이터 확장으로 porosity Recall·Small Recall·mAP50-95 목표 초과 충족), EXP-005(오버샘플링으로 slag_inclusion Recall을 EXP-002 수준 이상으로 회복, 5개 실험 중 최고 성능).
**실패 사례**: EXP-003(box gain 확대, 전 지표 하락으로 폐기), EXP-006(CLAHE, mAP50-95·양쪽 클래스 Recall 전부 하락으로 폐기), EXP-007(모델 크기 확대, 주 지표·slag_inclusion 가드레일 미충족이나 위치 정밀도는 부분 개선 — 순수 실패가 아닌 트레이드오프).

## 13. 오탐·미탐 분석

분류 방법론(`docs/08_error_analysis.md`, `src/evaluation/collect_error_cases.py`): ①같은 클래스+IoU≥0.5=TP → ②남은 예측 중 다른 클래스+IoU≥0.5=**클래스 오류** → ③같은 클래스+0.1≤IoU<0.5=**위치 오류** → ④나머지 예측=**오탐**, 나머지 정답=**미탐**.

| 오류 유형 | EXP-001 | EXP-005(최종 채택) | EXP-006 | EXP-007 |
| --- | ---: | ---: | ---: | ---: |
| 미탐 | 48/58(83%) | 63 | 75 | 86 |
| 오탐 | 3 | 38 | 28 | 12 |
| 위치 오류 | 2 | 11 | 10 | 5 |
| 클래스 오류 | 0 | 1 | 1 | 2 |

EXP-001 초기에는 미탐이 압도적 다수(83%)였다. 데이터 확장·클래스 균형(EXP-004·005)으로 미탐이 줄고 오탐이 늘어나는(Recall-Precision 트레이드오프) 방향으로 이동했다. **"예측 박스가 GT보다 작게 그려지는" 위치 오류 패턴은 EXP-001부터 EXP-006까지 6개 실험 내내 시각적으로 동일하게 재현됐고, EXP-007(모델 크기 확대)에서 처음으로 건수·정성 양면에서 뚜렷이 줄었다** — 다만 그 대가로 전체 Recall이 크게 희생됐다(12절).

## 14. 현재 한계

- **박스 위치 정밀도 문제가 완전히 해결되지 않았다.** box loss gain 확대(EXP-003), CLAHE 대비 강조(EXP-006), 모델 크기 확대(EXP-007) 세 가지 접근을 모두 시도했다. 마지막 시도(EXP-007)에서 위치 정밀도 자체는 개선됐지만 과적합으로 전체 Recall이 크게 하락해 종합적으로는 채택하지 못했다.
- **데이터 규모가 작다.** 최종 Train 482장(오버샘플링 포함)은 딥러닝 기준으로 여전히 소규모이며, EXP-007에서 확인했듯 모델 용량을 조금만 키워도 과적합이 발생할 만큼 여유가 없다.
- **클래스 범위가 좁다.** 원본 6개 클래스 중 porosity·slag_inclusion 2개만 다뤘다. 나머지 4개 클래스(crack, incomplete_penetration, lack_of_fusion, undercut)와 RT 외 검사 유형(VT), Segmentation 라벨은 이번 PoC 범위 밖이다.
- **CPU 전용 환경**이라 실험당 학습 시간이 짧게는 1시간(EXP-001), 길게는 10시간(EXP-007, yolo26s)까지 소요돼 반복 실험 속도에 제약이 있었다.
- **절대 성능 수준**: 최종 채택 설정(EXP-005)의 mAP50-95는 0.131, slag_inclusion Recall 0.487, porosity Recall 0.405로, 사람 검수 없이 완전 자동화하기에는 아직 부족하다.
- 실험 스크립트에 사소한 표시 버그 2건이 있었다(모델 성능에는 영향 없음, 순수 표시 문제): ① `read_results()`의 Epoch 번호가 실제보다 항상 1 크게 표시(EXP-001부터 존재했을 것으로 추정, EXP-005부터 문서만 정정), ② 학습 스크립트의 fitness 계산식이 Ultralytics 실제 기준(`mAP50-95` 단독)과 달라(`0.1*mAP50+0.9*mAP50-95`) EXP-003에서 한 차례 "Best" 표시가 실제와 달랐음(발견 후 정정, `best.pt` 자체 선택에는 영향 없음).

## 15. 개선 방향

1. **박스 위치 정밀도**: 이번 PoC에서 시도한 세 방법(box gain, CLAHE, 모델 크기) 모두 단독으로는 부족했다. 다음 단계에서는 (a) EXP-007의 과적합 문제를 정규화(weight decay 조정, dropout)나 더 강한 데이터 증강과 함께 재시도하거나, (b) Segmentation 라벨(2차 실험 범위)로 전환해 픽셀 단위 경계를 직접 학습하는 방향을 검토할 수 있다.
2. **데이터 규모 확대**: AI-Hub의 다른 검사 유형(VT)이나 추가 소재 데이터를 확보해 Train 규모를 늘리면, 모델 용량 확대(yolo26s 이상)의 이점을 과적합 없이 살릴 수 있을 가능성이 있다.
3. **클래스 확장**: 2차 실험에서 원본 6개 클래스 전체로 확장할 때, 이번 실험에서 확인한 "클래스별 노출 빈도 균형이 성능에 큰 영향을 준다"(EXP-005)는 교훈을 데이터 구성 단계부터 반영해야 한다.
4. **Threshold 운영**: EXP-005 이후 별도 분석(threshold_selection.csv)에서 0.25~0.50 구간을 세밀히 스캔했으나 뚜렷이 유리한 지점이 없었다 — 자동 라벨링(사람 검수 전제) 특성상 미탐 비용이 오탐 비용보다 크므로 현재 0.25를 유지하되, 실제 검수 비용이 측정되면 재검토가 필요하다.

## 16. MVP 진입 판단

`docs/context/00-completion-criteria.md`가 정의한 PoC 성공 기준은 특정 성능 수치가 아니라 **능력(capability) 체크리스트**다(재현 가능성, 변환·검증·학습·추론·자동 라벨·CVAT 확인·평가 해석·원인 분석·실험 비교 기록·MVP 흐름 확인). 이 기준으로 보면:

- 전체 파이프라인(원본 JSON→BBox 변환→YOLO 라벨→학습→추론→자동 라벨 export→CVAT 라운드트립 검증→성능 평가→오류 분석→다음 실험 설계)이 **7개 실험에 걸쳐 반복 재현**됐고, 매번 동일한 절차로 실행 가능함을 확인했다.
- **성공 사례(EXP-004, 005)와 실패 사례(EXP-003, 006, 007)가 모두 존재**하며, 각각 원인을 데이터·전처리·모델 설정 관점에서 설명할 수 있었다(14절).
- 자동 라벨 생성→CVAT 확인 흐름이 안정적으로 동작함을 확인했다(11절).

**결론: capability 기준으로는 2단계 MVP 진입이 가능하다.** 다만 절대 성능(mAP50-95 0.131, 클래스별 Recall 0.40~0.49)과 미해결 박스 위치 정밀도 문제(14절)를 고려하면, MVP는 **"모델이 결함 후보를 자동으로 표시하고 사람이 전수 검수·수정하는 보조 도구"**로 시작하는 것을 전제해야 한다 — 사람 검수 없는 완전 자동화 단계로 바로 진입하는 것은 시기상조다. 또한 MVP 범위를 이번 PoC와 동일하게(RT·AL, porosity·slag_inclusion, Box) 좁게 시작하고, 15절의 개선 방향을 통해 클래스·데이터·라벨 형식을 단계적으로 확장하는 것을 권장한다.

## 참고 문서

- 데이터 분석: `reports/dataset/dataset_analysis_report.md`, `docs/raw_data_structure.md`
- 데이터 품질: `reports/data-quality/data_quality_report.csv`
- 분할 검증: `reports/dataset/split_validation_report.md`
- 오류 분석 방법론: `docs/08_error_analysis.md`
- 실험별 상세 기록: `experiments/EXP-P1-DET-00{1..7}/experiment.md`
- 실험 설계 문서: `docs/10_next_experiment_plan.md` ~ `docs/14_next_experiment_plan.md`
- 완료 기준·범위 정의: `docs/context/00-completion-criteria.md`, `docs/context/01-experiment-scope.md`, `docs/context/03-deliverables.md`
