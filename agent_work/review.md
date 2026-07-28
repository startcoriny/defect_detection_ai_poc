# 코드 리뷰: EXP-006 스크립트 생성 (dataset_v4 기반, CLAHE 전처리)

## 요구사항 충족 여부

- `src/dataset/v4/apply_clahe.py` 신규 생성 — Train/Val/Test 전체에 LAB L 채널 CLAHE 적용, 라벨은 `shutil.copy2`로 원본 그대로, split별 파일 구성이 dataset_v3와 정확히 일치하는지 검증. 지시대로 구현 확인.
- `src/model/exp6/`, `src/evaluation/exp6/`, `src/visualization/exp6/`에 7개 생성 — exp5 대비 `EXPERIMENT_ID`/`EXPERIMENT_NAME`, 데이터 경로(`dataset_v3`→`dataset_v4`) 지정된 대로 치환. `diff --strip-trailing-cr`로 확인.
- 학습 하이퍼파라미터는 exp5와 완전히 동일 — diff로 확인.
- black/ruff 전부 통과.

## 실행 결과 (전체 파이프라인)

- `apply_clahe.py` 실행: Train/Val/Test 전부 dataset_v3와 파일 구성 완전 일치 확인(diff 결과 캐시 파일 외 차이 없음). 표본 이미지 대비(std) 16.1→24.1로 CLAHE 효과 확인.
- 학습: 50 epoch 완주(Early Stopping 미발동), 2.213시간.
- 추론: Test 84장 전체 성공(84/84)
- 자동 라벨 export + 라운드트립 검증: PASS
- Threshold 비교, 전체 평가, 오류 사례 수집 정상 실행

## 발견한 버그 1건 (EXP-005와 동일 패턴, CLAUDE가 직접 정정)

- section 5.2/5.3 Train 객체 수가 dataset_v2(오버샘플링 전) 수치를 그대로 참조 — EXP-005와 동일한 원인(`reports/dataset/v2/split_distribution.csv` 참조 유지가 Val/Test에는 맞지만 Train에는 stale). `oversample_slag.py` 기준 실제 수치(718 = porosity 382 + slag_inclusion 336)로 정정.
- Epoch 번호 표시 버그(EXP-005에서 발견한 것과 동일) 재확인 — 이번엔 fitness 공식 신·구 버전이 같은 epoch(36)을 가리켜 9.1절 수치는 정정 불필요, Epoch 번호만 정정(51→50, 37→36).

## 핵심 결과: CLAHE는 실패 (EXP-005 대비)

- 전체 mAP50-95 0.131→0.103(주 지표, **미충족** — 오히려 하락)
- porosity Recall 0.405→0.262(가드레일 미충족)
- slag_inclusion Recall 0.487→0.359(가드레일 미충족)
- localization_error 11→10건(사실상 동일, 겨냥한 문제 미해결 — 정성 평가에서 동일한 "박스 축소" 패턴 재확인)
- 미탐 63→75건(↑), 오탐 38→28건(↓) — Recall 하락과 일치

## 원인 추정

1. yolo26n 사전학습 가중치가 일반 자연 이미지 통계 기반이라, CLAHE로 데이터셋 전체 픽셀 분포를 바꾸면 전이 학습 효과가 줄어들 수 있다.
2. CLAHE 자체의 아티팩트 — false_negative 사례(`RT_AL_02_14487914_001`) 확인 결과 인위적인 색조·경계 패턴이 관찰됨.

## 결과

`experiment.md`에 실패로 명확히 기록. dataset_v4는 채택하지 않고 dataset_v3(EXP-005)를 최종 Baseline으로 유지. Threshold 재선정(개선 없음)에 이어 CLAHE(퇴보)까지 두 번의 추가 개선 시도가 모두 실패해, 작업26(PoC 결과 문서화)으로 넘어갈 것을 권장.
