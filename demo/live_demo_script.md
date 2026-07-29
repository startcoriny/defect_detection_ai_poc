# 오토 라벨링 PoC 라이브 데모 시나리오

내부 기술팀 대상, 라이브 데모(실시간 추론 실행), 15~20분.

## 준비물

- 터미널(프로젝트 루트, venv 활성화 상태 — `venv/Scripts/python.exe` 사용)
- 이미지 뷰어 3벌을 바로 열 수 있게 준비: ① 원본(라벨 없음) ② 예측 전용(정답 없음) ③ GT vs 예측 비교(정답 공개) — 순서대로 열어야 "판단 → 확인" 흐름이 산다
- 화면 공유 시 최종보고서(`docs/reports/15_poc_final_report.md`) 12절 성능 표를 바로 띄울 수 있게 준비

## 데모 컨셉

이미 학습이 끝난 모델(`experiments/EXP-P1-DET-005/models/best.pt`)에 **아무 표시도 없는 원본 이미지**를 넣고, 나온 예측 결과만 보고 청중이 먼저 "잘 됐는지 / 잘못됐는지 / 판단이 안 되는지"를 판단해본 다음, 정답(GT)을 공개해서 맞았는지 확인하는 방식으로 진행한다. 정답을 먼저 보여주고 설명하는 방식이 아니다.

## 순서

| # | 내용 | 시간 | 진행 방법 |
| --- | --- | ---: | --- |
| 1 | 문제 정의 & 배경 | 2분 | 구두: "용접 RT 검사 라벨링을 매번 처음부터 전수 검수하는 대신, 모델이 만든 초안을 확인·수정하는 방식이 가능한지 검증했다"(최종보고서 1절) |
| 2 | 파이프라인 개요 | 2분 | 구두 + 화이트보드/슬라이드 1장: 원본 JSON→BBox 변환→YOLO 라벨→학습→추론→자동 라벨 export→CVAT 라운드트립 검증. "7개 실험 내내 동일 절차로 재현됐다"를 강조 |
| 3 | 라이브 추론 실행 | 2~3분 | 터미널에서 발표자가 직접 순서대로 실행: ① `python src/model/exp5/run_inference.py` (이미 학습된 `best.pt`로 Test 84장 추론, CPU 20~40ms/장 → 수 초 내 종료) ② `python src/visualization/exp5/visualize_prediction.py` (예측 전용 오버레이 생성 + CVAT 라운드트립 검증 `PASS` 로그 확인) ③ `python demo/compare_gt_prediction.py` (GT 포함 비교 이미지 생성 — 정답 공개용, 아직 열지 않는다) |
| 4 | 케이스별 판단 (원본→예측→정답) | 8~9분 | 아래 "케이스별 진행 순서" 참고. 4개 케이스를 하나씩 원본 → 예측 전용 → 정답 공개 순으로 열며 진행 |
| 5 | 지표 요약 & 실험 여정 | 2분 | 최종보고서 12절 표: EXP-001(mAP50 0.175)→EXP-005(mAP50 0.342, 최종 채택) 개선 곡선, EXP-003/006(실패)·EXP-007(트레이드오프)도 한 줄씩 언급 |
| 6 | 한계 & 다음 단계 | 2분 | 최종보고서 14~16절: 박스 위치 정밀도 미해결, Train 482장 소규모, 클래스 2개뿐, CPU 환경 → "모델이 후보를 표시하고 사람이 전수 검수·수정하는 보조 도구"로 MVP 시작 제안 |
| 7 | Q&A | 자유 | - |

## 케이스별 진행 순서 (핵심)

케이스마다 아래 3단계를 순서대로 밟는다. 미리 정답(GT)이 그려진 이미지를 먼저 보여주지 않는다.

1. **원본 공개** — `data/processed/dataset_v3/images/test/{이미지}`를 연다(박스 없음). "여기에 결함이 있을까요?"
2. **예측 결과만 공개** — `outputs/EXP-P1-DET-005/auto-label-visualization/{이미지}`를 연다(모델이 그린 박스 + confidence만, 정답 없음). 청중에게 묻는다: **잘 검출된 것 같은가 / 잘못된 것 같은가 / 이것만 보고는 판단이 안 되는가?**
3. **정답 공개** — `demo/comparison-images/{이미지}`(왼쪽 GT·오른쪽 Prediction)를 연다. 청중의 판단이 맞았는지 확인하고 설명한다.

4개 케이스는 "잘됨 / 잘못됨 / 판단 어려움"의 서로 다른 사례가 되도록 골랐다.

| 이미지 | 2단계(예측만 봤을 때) 청중이 보게 되는 것 | 3단계 정답 공개 후 실제 결과 |
| --- | --- | --- |
| `RT_AL_02_14489691.jpg` | 박스 2개, confidence 0.518·0.373 — 뚜렷하게 검출됨 | **잘됨**: GT 2건과 정확히 일치(IoU 0.83, 0.7대) |
| `RT_AL_05_14492165.jpg` | 박스 1개, confidence 0.251(임계값 0.25에 턱걸이) | **잘됨(다만 아슬아슬)**: GT와 IoU 0.80으로 일치하지만, confidence가 낮아 "이게 진짜 맞는 건지" 애매하게 느껴질 수 있는 사례 |
| `RT_AL_02_14488212.jpg` | 박스가 **하나도 없음** — "결함이 없다"고 예측한 것처럼 보임 | **잘못됨(미탐)**: 실제로는 Small porosity 1건이 있었다. "Small 객체가 83% 저대비"라는 데이터 특성으로 설명 |
| `RT_AL_05_14492954.jpg` | 박스 1개, confidence 0.433 — 언뜻 보면 그럴듯하게 검출된 것처럼 보임 | **판단 어려움 → 확인해보니 위치 오류**: 예측 박스가 GT보다 폭·높이 모두 작게 그려짐. 예측 결과만 봐서는 맞았는지 틀렸는지 알 수 없고, 정답과 대조해야만 드러나는 유형 — 6개 실험 내내 반복된 고질적 패턴 |

## 라이브 실행 시 유의점

- 세 스크립트(`run_inference.py`, `visualize_prediction.py`, `compare_gt_prediction.py`) 모두 venv(`venv/Scripts/python.exe`)로 실행해야 한다(시스템 python에는 `cv2`, `ultralytics` 등이 없음 — 리허설 중 동일 문제로 한 번 막혔다).
- 한글 로그가 콘솔에서 깨지면 `PYTHONIOENCODING=utf-8` 환경변수를 설정하고 실행할 것(리허설에서 확인됨).
- `visualize_prediction.py`는 CVAT 구조 검증까지 포함해 마지막에 "전체 통과 여부: PASS" 로그를 출력한다 — 발표 중 이 로그가 뜨는 순간이 "자동 라벨 생성 흐름이 실제로 안정적으로 재현된다"는 것을 보여주는 핵심 포인트이므로 놓치지 말고 짚어줄 것.
- `compare_gt_prediction.py`는 `demo/comparison-images/`에 있는 기존 4개 파일을 실행할 때마다 덮어쓴다 — 매번 새로 생성되는 게 맞고, 케이스 목록(`DEMO_CASES`)이 고정돼 있어 항상 같은 4개 파일명으로 나온다.
- 세 스크립트 다 수 초 내 종료하지만(리허설 기준 `run_inference.py` 약 6초, `visualize_prediction.py` 약 1.4초, `compare_gt_prediction.py` 1초 미만), 혹시 서버·환경 문제로 라이브 실행 자체가 안 될 경우를 대비해 `demo/backup-if-live-fails/`(리허설 때 만들어둔 비교 이미지 4장 + 실행 로그 3개)를 열어둘 수 있게 준비해 갈 것. **이 폴더는 라이브가 정말 안 될 때만 열고, 정상 진행되면 사용하지 않는다** — 자세한 안내는 `demo/backup-if-live-fails/README.md` 참고.

## 이미지 구성 (읽는 법)

케이스마다 세 종류의 이미지를 순서대로 사용한다.

1. **원본** (`data/processed/dataset_v3/images/test/{이미지}`): 아무 표시 없는 순수 원본 사진.
2. **예측 전용** (`outputs/EXP-P1-DET-005/auto-label-visualization/{이미지}`): `visualize_prediction.py`가 만든다. 모델이 예측한 박스만 자홍색(magenta)으로 그려지고 `클래스명 confidence`(예: `slag_inclusion 0.433`)가 표시된다 — **정답(GT)은 전혀 없다.** 판단 단계에서 쓰는 이미지.
3. **GT vs 예측 비교** (`demo/comparison-images/{이미지}`): `compare_gt_prediction.py`가 만든다. 왼쪽 "GT" 패널(초록 박스, 클래스명만, 사람이 라벨링한 정답)과 오른쪽 "Prediction" 패널(빨간 박스, 클래스명+confidence)을 나란히 붙이고 맨 위에 케이스 라벨 배너를 넣은 정답 공개용 이미지. 미탐 케이스는 오른쪽 Prediction 패널에 박스가 하나도 없다 — 모델이 아무것도 못 찾았다는 뜻.

## 케이스 선정 근거

`reports/evaluation/EXP-P1-DET-005/error_cases.csv`, `predictions/EXP-P1-DET-005/prediction_results.json`, `data/processed/dataset_v3/labels/test/*.txt`를 대조해 선정했다. 이미지 전체가 오탐 없이 깔끔한 "오탐 단독" 케이스는 찾지 못해(대부분 다른 GT 박스와 섞여 있음) 4건으로 확정했다.

| 이미지 | 케이스 |
| --- | --- |
| `RT_AL_02_14489691.jpg` | 성공: porosity 2건 모두 정확히 검출 (IoU 0.83, 0.7대) |
| `RT_AL_05_14492165.jpg` | 성공: slag_inclusion 정확히 검출 (IoU 0.80) |
| `RT_AL_02_14488212.jpg` | 실패(미탐): Small porosity 놓침 |
| `RT_AL_05_14492954.jpg` | 실패(위치 오류): 예측 박스가 GT보다 작게 그려짐 |

## 관련 산출물

- 원본 이미지: `data/processed/dataset_v3/images/test/` — 원본 데이터, 수정하지 않음
- 예측 전용 이미지: `outputs/EXP-P1-DET-005/auto-label-visualization/` — `visualize_prediction.py` 실행 시 Test 84장 전체가 매번 재생성된다
- GT vs 예측 비교 이미지: `demo/comparison-images/` — 라이브 데모 중 `compare_gt_prediction.py` 실행 결과가 매번 여기 생성된다(고정된 파일명 4개, 실행할 때마다 덮어씀). 발표 전에는 비어 있거나 이전 실행 결과가 남아 있을 수 있다.
- 라이브 실패 시 백업: `demo/backup-if-live-fails/`(비교 이미지 4장 + 실행 로그 3개, 리허설 시점 고정본) — `README.md` 참고
- 비교 이미지 생성 스크립트: `demo/compare_gt_prediction.py`
- 코드 리뷰: `agent_work/review.md`
