# EXP-P1-DET-007 실험 계획: 모델 크기 확대 (yolo26n → yolo26s)

## 1. 문제 정의

EXP-001부터 EXP-006까지 6개 실험 내내 "예측 박스가 GT보다 작게 그려지는" 위치 오류 패턴이 해결되지 않았다. EXP-003(box loss gain 확대), EXP-006(CLAHE 대비 강조)이 각각 이 문제를 겨냥했으나 둘 다 실패했다(`experiments/EXP-P1-DET-006/experiment.md` 16절).

`docs/decisions/13_next_experiment_plan.md`에서 보류했던 마지막 후보인 **모델 크기 확대**를 이번 실험의 변수로 채택한다. 가설: yolo26n(2.5M 파라미터)은 용량이 작아 결함 경계의 미세한 형태를 정밀하게 회귀하기에 부족할 수 있다. yolo26s(10.0M 파라미터, 약 4배)로 용량을 키우면 박스 위치·크기 정밀도가 개선될 것이다.

## 2. 변경 변수 (In Scope)

- 모델: `yolo26n.pt` → `yolo26s.pt`(사전학습 가중치, 이미 다운로드 완료 확인)
- 그 외 모든 조건은 EXP-005(dataset_v3, imgsz=960, box=7.5, epochs=50, patience=15)와 완전히 동일

## 3. 고정 조건 (Out of Scope)

- 데이터셋: dataset_v3(EXP-005가 채택한 최종 Baseline) — dataset_v4(CLAHE, EXP-006에서 폐기됨)는 사용하지 않는다
- 학습 하이퍼파라미터, 증강 설정 변경 없음
- Threshold는 EXP-005 결론(0.25 유지)을 그대로 따름

## 4. 참고: 예상 학습 시간

yolo26s는 yolo26n 대비 파라미터 약 4배(10.0M vs 2.5M), GFLOPs 약 4배(22.8 vs 5.8)다. CPU 환경에서 EXP-005가 50 epoch에 2.2시간 걸렸으므로, 단순 비례 시 약 8~9시간이 예상된다(사용자 확인 후 진행 승인받음).

## 5. 성공 기준

| 기준 | 목표 | 판단 방식 |
| --- | --- | --- |
| 주 지표: 전체 mAP50-95 | EXP-005(0.131) 대비 개선 | Test셋 기준, 박스 위치·크기 정밀도에 가장 민감한 지표 |
| 보조 지표: localization_error 건수 | EXP-005(11건) 대비 감소 | `collect_error_cases.py` 오류 유형 집계 기준, 정성 평가로 실질 개선 여부 함께 확인 |
| 가드레일 1: slag_inclusion Recall | EXP-005(0.487) 대비 크게 하락하지 않음(0.40 이상) | 모델 용량 확대가 기존 클래스 균형 효과를 훼손하지 않는지 확인 |
| 가드레일 2: porosity Recall | EXP-005(0.405) 대비 크게 하락하지 않음(0.30 이상) | 상동 |

## 6. 후속 계획

이번 실험 결과와 무관하게, `docs/00-completion-criteria.md`·`02-task-list.md` 기준으로 반복 실험 사이클(작업25)은 이번 실험을 마지막으로 마무리하고 작업26(PoC 결과 문서화)으로 진입한다.
