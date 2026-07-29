# 코드 리뷰: EXP-007 스크립트 생성 (모델 크기 확대, yolo26n→yolo26s)

## 요구사항 충족 여부

- `src/model/exp7/`, `src/evaluation/exp7/`, `src/visualization/exp7/`에 7개 생성 — exp5 대비 `EXPERIMENT_ID`/`EXPERIMENT_NAME`, 모델 파일(`yolo26n.pt`→`yolo26s.pt`)만 지정된 대로 치환, 데이터셋 경로(`dataset_v3`)는 그대로 유지. `diff --strip-trailing-cr`로 전체 7개 파일 확인.
- 학습 하이퍼파라미터(imgsz, box, epochs, patience 등)는 exp5와 완전히 동일 — diff로 확인.
- black/ruff 전부 통과.

## 실행 결과 (전체 파이프라인)

- 학습: Early Stopping 발동(patience=15), 39 epoch에서 종료(Best epoch 24), 10:01:26 소요(EXP-005 대비 약 4.6배, GFLOPs 비율과 대략 비례).
- 추론: Test 84장 전체 성공(84/84)
- 자동 라벨 export + 라운드트립 검증: PASS
- Threshold 비교, 전체 평가, 오류 사례 수집 정상 실행

## 발견한 버그 1건 (EXP-005·006과 동일 패턴)

- Epoch 번호 표시 버그 재확인 — 이번에도 fitness 신·구 공식이 같은 epoch(24)을 가리켜 9.1절 수치는 정정 불필요, Epoch 번호만 정정(40→39, 25→24).
- section 5.2/5.3 Train 객체 수 stale 문제도 EXP-005·006과 동일 원인으로 재현, 동일하게 정정(718 = porosity 382 + slag_inclusion 336).

## 핵심 결과: 부분 성공 + 전체 실패가 공존하는 트레이드오프

- 전체 mAP50-95 0.131→0.089(주 지표, **미충족**)
- slag_inclusion Recall 0.487→0.179(가드레일 미충족, EXP-004 회귀 수준으로 복귀)
- porosity Recall 0.405→0.321(가드레일 근소 충족)
- **localization_error 건수 11→5건(보조 지표 충족)** — 정성 평가에서도 EXP-005·006 내내 위치 오류였던 대표 사례가 이번엔 정상 탐지(TP)로 전환됨을 확인
- 미탐 63→86건(↑↑), 오탐 38→12건(↓↓) — 모델이 애매한 신호에 더 보수적으로 반응하는 쪽으로 이동

## 원인 추정

Val-Test 성능 격차가 EXP-005(0.035) 대비 EXP-007(0.098)에서 약 2.8배 벌어짐 — 모델 용량 확대(파라미터 약 4배)가 Train 482장 규모의 데이터셋에서 과적합을 유발한 것으로 추정. 박스 정밀도 자체는 개선됐지만 그 대가로 전체 Recall이 크게 희생됨.

## 결과

`experiment.md`에 부분 성공/전체 실패 트레이드오프로 정직하게 기록. dataset_v3+yolo26n(EXP-005)을 최종 Baseline으로 유지, yolo26s는 미채택. 박스 위치 정밀도의 세 가지 후보(box gain, CLAHE, 모델 크기)를 모두 시도했으므로 작업26(PoC 결과 문서화)으로 진입할 것을 권장.
