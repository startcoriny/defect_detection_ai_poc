# 데이터셋 최종 검증 요약

## 분할별 집계

| 분할 | 이미지 수 | 정상(빈 라벨) 이미지 수 | 검증 성공 파일 수 | 검증 실패 파일 수 |
|---|---:|---:|---:|---:|
| train | 209 | 70 | 209 | 0 |
| val | 44 | 15 | 44 | 0 |
| test | 46 | 15 | 46 | 0 |

## 체크 항목별 건수

| 체크 항목 | 심각도 | 건수 |
|---|---|---:|
| image_missing | ERROR | 0 |
| label_missing | ERROR | 0 |
| image_unreadable | ERROR | 0 |
| label_line_value_count_mismatch | ERROR | 0 |
| class_id_out_of_range | ERROR | 0 |
| coordinate_out_of_range | ERROR | 0 |
| cross_split_duplicate | ERROR | 0 |
| class_missing_in_split | WARNING | 0 |

## 학습 가능 여부

**학습 가능**

## 데이터셋 버전 고정

- 데이터셋 매니페스트 해시(SHA-256): `12f1a115df80df62ef1d4ef5898a595334c564ce0a70a63345e92df931be9e71`
- 계산 범위: `data/processed/dataset_v1/`의 모든 파일
- 계산 방식: 상대경로 오름차순으로 각 파일의 SHA-256 해시를 이어붙인 뒤 다시 SHA-256 계산
