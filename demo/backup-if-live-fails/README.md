# 백업 자료 — 라이브 시연이 안 될 때만 사용

이 폴더는 **라이브 데모 실행 자체가 실패했을 때(서버·환경 문제 등)** 대신 보여줄 백업 자료다. 정상적으로 라이브 데모가 진행된다면 이 폴더는 열 필요가 없다.

- `comparison-images/` — 2026-07-29 리허설 때 `python src/visualization/exp5/compare_gt_prediction.py`로 생성한 GT vs 예측 비교 이미지 4장(라이브 실행 결과와 동일한 케이스·내용). 각 이미지가 왼쪽(GT)·오른쪽(Prediction)으로 무엇을 보여주는지는 `../live_demo_script.md`의 "이미지 구성 (읽는 법)" 절 참고.
- `logs/` — 같은 리허설에서 `run_inference.py`, `visualize_prediction.py`, `compare_gt_prediction.py`를 순서대로 실행한 콘솔 로그(전체 통과 여부 `PASS` 포함).

라이브 실행 중 이 폴더의 자료를 대신 보여줘야 했다면, 발표 시작 전에 "환경 문제로 사전 리허설 결과를 보여드립니다"라고 먼저 알릴 것.
