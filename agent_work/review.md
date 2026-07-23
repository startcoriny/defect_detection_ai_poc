# 코드 리뷰: Smoke Test (`src/model/smoke_test.py`) — scoped fix 반영 후 최종

## 요구사항 충족 여부

- 스모크 데이터 15장(정상 5 + porosity 5 + slag_inclusion 5, train 분할, 이름순) — 확인
- `smoke_images.txt` + `smoke_data.yaml`(복사 없이 경로 목록 방식) — 확인
- 학습(2 epoch, imgsz 640, batch 4, CPU, seed 42) 오류 없이 완료 — 확인
- `best.pt`/`last.pt` 생성, `results.csv`에 Validation 지표 컬럼 존재 — 확인
- `best.pt`를 디스크에서 다시 로드해 3장 추론, 결과 이미지 3장 저장 확인(scoped fix로 개수 비교 방식으로 수정 후 정상 통과) — 확인
- 최종 판정 5개 항목 전부 로그에 "확인"으로 기록됨 — 확인

## 발견한 문제

없음(이전 Blocker는 scoped fix로 해결, 재실행 결과 정상 종료 확인). 기계적 포맷 이슈 1건(줄바꿈 스타일) — black으로 CLAUDE가 직접 적용함.

## 실행 결과

```
2 epochs completed in 0.002 hours.
Optimizer stripped from .../weights/last.pt, 5.4MB
Optimizer stripped from .../weights/best.pt, 5.4MB
                   all         15         23          0          0          0          0
              porosity          5         10          0          0          0          0
        slag_inclusion          5         13          0          0          0          0
Results saved to .../runs/smoke
Results saved to .../runs/predict
최종 판정 - 학습 오류 없이 완료: 확인
최종 판정 - Validation 실행됨: 확인
최종 판정 - 모델 파일 생성됨: 확인
최종 판정 - 추론 가능: 확인
최종 판정 - Baseline 학습 시작 가능: 확인
```

- `outputs/smoke_test/runs/smoke/weights/{best.pt,last.pt}` 실제 생성(각 5.4MB)
- `outputs/smoke_test/runs/smoke/results.csv`에 `metrics/precision(B)`, `metrics/recall(B)`, `metrics/mAP50(B)` 등 컬럼 존재, epoch별 loss 실제로 감소(box_loss 3.44→3.03)
- P/R/mAP는 전부 0 — 15장·2epoch 스모크 규모에서는 정상(성능 확인이 목적이 아니라 파이프라인 동작 확인이 목적)
- `outputs/smoke_test/runs/predict/{image0,image1,image2}.jpg` 3장 저장 확인
- black 적용 후 재검사 통과, ruff 통과

## 사용자가 직접 확인하는 방법

1. `venv/Scripts/python.exe src/model/smoke_test.py` 실행(CPU라 수 분 내 완료) — 로그 마지막 5줄 "최종 판정 - ...: 확인" 확인
2. `outputs/smoke_test/runs/smoke/weights/best.pt`, `last.pt` 존재 확인
3. `outputs/smoke_test/runs/smoke/results.csv` — Validation 지표 컬럼 존재 확인
4. `outputs/smoke_test/runs/predict/` — 이미지 3장 저장 확인
5. `outputs/smoke_test/smoke_test.log` — 스모크 데이터 구성 내역(정상/porosity/slag_inclusion 각 5장) 확인

## 결과

완료 조건 5개(학습 오류 없이 완료, Validation 실행, 모델 파일 생성, 추론 가능, Baseline 학습 시작 가능) 모두 충족.
