# 원본 데이터 인벤토리

`docs/context/02-task-list.md` 작업2(원본 데이터 확보 및 보존)의 산출물 문서.

---

## 1. 원본 데이터 저장 위치

- `data/raw/steel/` — AI-Hub 용접 검사 데이터
- `data/raw/mvtec_anomaly_detection/` — MVTec AD 데이터 (선택 산출물, 비교용)

둘 다 `.gitignore`의 `data/` 규칙으로 git 추적에서 제외된다.

---

## 2. 데이터 출처

### AI-Hub 용접 검사 데이터 (`steel/`)

- 데이터셋명: 창원 지역 특화산업 고도화 및 디지털 전환 촉진을 위한 용접 AI 학습 데이터 구축
- 데이터셋 번호: 71761
- 제공기관: (재)경남테크노파크(주관), 경남대학교 산학협력단·(주)위미르·(주)제이엔이웍스(참여)
- 출처 링크: https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=71761
- 구성: RT(방사선투과검사)·VT(육안검사) 용접 이미지, 원본 데이터셋 전체 규모 144,019장

### MVTec AD (`mvtec_anomaly_detection/`)

- 공식 출처: https://www.mvtec.com/company/research/datasets/mvtec-ad
- `docs/context/03-deliverables.md` 10절 "선택 산출물"에 명시된 비교용 데이터셋
- 표준 15개 카테고리 구조 그대로 보유 확인

---

## 3. 데이터 버전 / 다운로드 일자

- 다운로드 일자: 2026-07-22
- 버전 정보: AI-Hub 페이지에 별도 버전 표기 없음

---

## 4. 로컬 보유 데이터 현황

| 구분 | 경로 | 이미지 | JSON 라벨 |
| --- | --- | ---: | ---: |
| RT / AL | `01.원천데이터/1. RTAL`, `02.라벨링데이터/1. RTAL` | 637 | 637 |
| RT / ST | `01.원천데이터/2. RTST`, `02.라벨링데이터/2. RTST` | 488 | 488 |
| VT / ST | `01.원천데이터/3. VTST`, `02.라벨링데이터/3. VTST` | 1,125 | 1,125 |
| 합계 | | 2,250 | 2,250 |

이미지와 JSON 라벨 개수가 카테고리별로 정확히 1:1로 일치한다.

**참고**: AI-Hub 원본 데이터셋 전체 규모(144,019장) 대비 로컬 보유량(2,250장)이 훨씬 적다. PoC 범위에 맞춘 샘플/부분 다운로드로 보이나, 전체 데이터를 추가로 받아야 하는지는 확인되지 않았다 — 필요 시 사용자 확인 필요.

`mvtec_anomaly_detection/`은 표준 15개 카테고리(bottle, cable, capsule, carpet, grid, hazelnut, leather, metal_nut, pill, screw, tile, toothbrush, transistor, wood, zipper)를 그대로 보유하고 있다.

---

## 5. RT/VT·소재 구분 확인

샘플 JSON 구조 (`info` 블록):

```json
{
  "info": { "id": 14483434, "type": "RT", "material": "AL" },
  "image_data": { "file_name": "RT_AL_00_14483434", "format": "jpg", "width": 3457, "height": 943 },
  "meta": { "is_crowd": 0, "annotation_case": ["normal"], "total_case": ["normal"] },
  "annotations": [ { "tool": "polygon", "coordinate": { "x": [...], "y": [...] } } ]
}
```

- `info.type` (RT/VT), `info.material` (AL/ST) 필드로 검사 유형과 소재를 구분할 수 있다.
- 폴더명(RTAL/RTST/VTST)과 JSON 필드 값이 일치함을 각 카테고리 샘플에서 확인했다.
- 최상위 폴더명은 "Steel"이지만 실제로는 AL(알루미늄)·ST(철강) 두 소재가 모두 포함되어 있다.

---

## 6. 원본 디렉터리 구조

```
data/raw/
├── steel/
│   ├── 01.원천데이터/
│   │   ├── 1. RTAL/   (*.jpg, 637장)
│   │   ├── 2. RTST/   (*.jpg, 488장)
│   │   └── 3. VTST/   (*.jpg, 1125장)
│   └── 02.라벨링데이터/
│       ├── 1. RTAL/   (*.json, 637개)
│       ├── 2. RTST/   (*.json, 488개)
│       └── 3. VTST/   (*.json, 1125개)
└── mvtec_anomaly_detection/
    ├── bottle/ ~ zipper/  (15개 카테고리, 각 train/test/ground_truth/license.txt/readme.txt)
```

---

## 7. 원본 데이터 보존 원칙

- `data/raw`는 원본 그대로 두고 코드로 수정하지 않는다 (`docs/context/02-task-list.md` 작업2, `CLAUDE.md` 개발 원칙).
- 분석·선별·변환 작업은 `data/work`, 변환 결과는 `data/processed`에 둔다. 아직 실제 작업이 없어 두 폴더는 생성하지 않았다 — 해당 작업(작업3 이후) 시점에 생성한다.

---

## 8. 알려진 이슈

- `cv2.imread()`가 이 데이터의 한글 경로(`01.원천데이터` 등)를 열지 못한다. 파일 손상이 아니라 **OpenCV가 Windows에서 비-ASCII(유니코드) 경로를 제대로 열지 못하는 알려진 이슈**다. Pillow(`PIL.Image.open`)로는 정상적으로 열린다.
- 이후 이미지 관련 코드(작업3 `src/common/image_utils.py` 등)에서는 `cv2.imread` 대신 `np.fromfile(path, dtype=np.uint8)` + `cv2.imdecode(...)` 조합을 사용해야 한다.

---

## 9. 작업2 완료 조건 확인

- (v) 이미지와 JSON 파일을 열 수 있다 — Pillow로 확인 (cv2는 8절 이슈로 우회 필요)
- (v) RT와 VT 데이터를 구분할 수 있다 — JSON `info.type` 필드
- (v) 소재 정보를 확인할 수 있다 — JSON `info.material` 필드
- (v) 원본과 작업용 데이터가 분리되어 있다 — `data/raw`만 존재, `data/work`는 실제 작업 시점에 생성
- (v) 원본 파일이 수정되지 않는 구조다 — 읽기만 수행, 수정 없음
