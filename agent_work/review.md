# 코드 리뷰: 오탐·미탐 분석 (`src/evaluation/collect_error_cases.py`)

## 요구사항 충족 여부

- TP → wrong_class → localization_error → FP/FN 4단계 그리디 매칭 — 확인
- 객관적 보조 정보(Confidence, 크기 버킷, 박스 면적비, 경계 근접, 중복 예측 여부)만 산출, 정성 판단 없음 — 확인
- `errors/{false_positive,false_negative,wrong_class,localization_error}/` 사례 이미지(GT 초록+Prediction 자홍) 저장 — 확인
- `reports/evaluation/{error_cases.csv, error_type_counts.csv}` 생성 — 확인
- black/ruff 통과 — 확인(ruff는 미사용 import 자동 수정, black은 CLAUDE가 재포맷 적용)

## 발견한 사항

1. **긍정적 발견 — 산술 검증 완벽히 일치**: TP(8, 작업23의 single-label 매칭과 동일 기준) + wrong_class(0) + localization_error(2) + false_negative(48) = 58 = Test 전체 GT 수와 정확히 일치. 예측 쪽도 TP(8)+wrong_class(0)+localization_error(2)+false_positive(3)=13=실제 배포 기준 전체 예측 수와 정확히 일치. 구현이 정확함을 강하게 뒷받침.
2. **설계상 알려진 한계(버그 아님, `docs/08_error_analysis.md`에 명시)**: 클래스가 다르고 IoU가 0.1~0.5인 애매한 경우, "클래스 오류"(cross-class, IoU≥0.5 요구)에도 "위치 오류"(same-class 요구)에도 해당하지 않아 별도의 FP+FN 쌍으로 기록된다. 실제로 2건(`RT_AL_02_14488786`, `RT_AL_02_14489318`) 발생 — 둘 다 리뷰 시 확인하고 보고서에 "복합 실패"로 명시함.
3. **CODEX가 요청보다 더 나은 설계 선택**: `calculate_metrics.py`(작업23)의 `GroundTruth`/`Prediction`/`calculate_iou`/`extract_predictions` 등을 직접 import해서 재사용(요청서는 "각 스크립트가 독립적으로 작은 헬퍼를 재구현"하는 기존 관례를 언급했으나, 이번엔 임포트가 더 합리적인 선택 — 로직이 완전히 동일해 재구현하면 오히려 두 파일이 어긋날 리스크가 있음). 실행 확인 결과 정상 동작, 문제 없음.
4. **`errors/`는 gitignore 대상으로 추가함(CLAUDE 직접 처리)**: 다른 모든 시각화 산출물(outputs/, auto-labels/, predictions/, reports/evaluation/evaluation/)과 동일한 정책 — 이미지는 재생성 가능하므로 제외하고, `error_cases.csv`/`error_type_counts.csv`/`docs/08_error_analysis.md`만 커밋한다.

## 실행 결과

```
전체 53건: false_negative 48(porosity 23, slag_inclusion 25), false_positive 3(porosity 1, slag_inclusion 2),
localization_error 2(porosity 2), wrong_class 0
```

- 대표 사례 육안 확인 6건(오탐 3건 전수, 위치 오류 1건, 미탐 2건) — `docs/08_error_analysis.md`에 상세 기록
- black `--check`, ruff `check` 통과

## 사용자가 직접 확인하는 방법

1. `venv/Scripts/python.exe src/evaluation/collect_error_cases.py` 실행(수십 초)
2. `reports/evaluation/error_type_counts.csv` 확인
3. `errors/false_positive/`(3장), `errors/localization_error/`(2장) 육안 확인
4. `docs/08_error_analysis.md` — 오탐/미탐/위치오류 유형 분석과 원인·개선 후보 확인

## 결과

완료 조건 5개(오탐·미탐 구분, 클래스·위치 오류 구분, 사례 이미지 저장, CSV 생성, black/ruff 통과) 모두 충족. `docs/08_error_analysis.md` 작성 완료.
