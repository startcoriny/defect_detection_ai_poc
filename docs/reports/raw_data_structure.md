# 원본 데이터 구조 분석

`docs/context/02-task-list.md` 작업3(데이터 구조 분석)의 산출물 문서. `data/raw/steel/02.라벨링데이터`의 JSON 2,250개 전수를 읽어 확인했다 (읽기 전용 분석, 원본 데이터 변경 없음).

---

## 1. 이미지·JSON 연결 규칙

- 확장자를 제외한 파일명이 동일하다: `01.원천데이터/1. RTAL/RT_AL_00_14483434.jpg` ↔ `02.라벨링데이터/1. RTAL/RT_AL_00_14483434.json`
- 두 최상위 폴더 하위의 카테고리 구조(`1. RTAL` / `2. RTST` / `3. VTST`)도 동일하다.
- JSON 내부 `image_data.file_name` 필드도 같은 값(확장자 제외)을 갖는다.

---

## 2. JSON 최상위 구조 및 필드 정의

```json
{
  "info": { "id": 14483434, "type": "RT", "material": "AL" },
  "image_data": { "file_name": "RT_AL_00_14483434", "format": "jpg", "width": 3457, "height": 943, "information": "..." },
  "meta": { "is_crowd": 0, "annotation_case": ["normal"], "total_case": ["normal"] },
  "annotations": [
    { "tool": "polygon", "coordinate": { "x": [...], "y": [...] }, "class": "normal", "case": "" }
  ]
}
```

| 필드 | 위치 | 설명 |
| --- | --- | --- |
| 이미지 파일명 | `image_data.file_name` | 확장자 제외, 실제 이미지 파일명과 일치 |
| 이미지 확장자 | `image_data.format` | 예: `jpg` |
| Width / Height | `image_data.width` / `image_data.height` | 샘플 확인 결과 Pillow로 연 실제 이미지 크기와 일치 (3457×943 사례로 검증) |
| 검사 유형 | `info.type` | `RT`(방사선투과) / `VT`(육안검사) |
| 소재 | `info.material` | `AL`(알루미늄) / `ST`(철강) |
| 정상·불량 정보 | `meta.annotation_case`, `meta.total_case` | 아래 4절 참고 |
| 결함 클래스 | `annotations[].case` | **주의: `annotations[].class`가 아니다.** 아래 3절 참고 |
| Annotation 목록 | `annotations` | 리스트, 원소 수 = 객체(폴리곤) 개수 |
| Polygon x/y 좌표 | `annotations[].coordinate.x`, `.y` | 아래 5절 참고 |
| 객체 개수 | `len(annotations)` | 아래 6절 참고 |

---

## 3. ⚠️ 클래스명 필드 주의사항

`annotations[].class`는 클래스명이 아니라 **`"normal"` 또는 `"defect"` 두 값만 갖는다.** 실제 결함 종류(클래스)는 `annotations[].case` 필드에 영문으로 들어있다.

- 클래스명은 **영문**을 사용한다: `crack`, `porosity`, `lack of fusion`, `incomplete penetration`, `undercut`, `slag inclusion`, 정상은 빈 문자열(`""`).
- 이후 클래스 매핑/YOLO 변환 작업(작업5 이후)에서는 `annotations[].case`를 클래스 기준으로 사용해야 한다. `class` 필드를 클래스로 오인하면 안 된다.

---

## 4. 정상 vs 불량 데이터 구조 차이

**정상 이미지도 `annotations`가 비어 있지 않다.** 정상 이미지는 `class: "normal"`, `case: ""`인 polygon이 1개 존재한다 (전체 용접부 영역으로 추정). 즉 "정상 = annotation 없음"이 아니라 "정상 = 결함 없음을 나타내는 polygon 1개"다.

- 정상: `meta.annotation_case == ["normal"]`, `annotations` 길이 1, `case: ""`
- 불량: `meta.annotation_case`에 결함명이 들어감, `annotations[].case`에 결함명 반복

---

## 5. Polygon 좌표 구조

```json
"coordinate": { "x": [288, 563, 1077, ...], "y": [240, 295, 321, ...] }
```

x, y가 **별도 배열**이다 (예: `[[x1,y1],[x2,y2],...]` 형태의 좌표쌍 리스트가 아니다). 같은 인덱스의 `x[i]`, `y[i]`가 한 점을 이룬다.

---

## 6. 다중 객체(Annotation) 구조

한 이미지에 Annotation이 여러 개 들어갈 수 있다. 2,250건 전체 분포(요약):

| annotations 개수 | 건수 |
| ---: | ---: |
| 1개 | 1,286 |
| 2개 | 433 |
| 3개 | 181 |
| 4개 | 92 |
| 5개 | 31 |
| 6~10개 | 89 |
| 11개 이상 | 138 (최대 98개) |

- **동일 결함 다수 예시**: `data/raw/steel/02.라벨링데이터/1. RTAL/RT_AL_01_14487633.json` — 6개 annotation, 전부 같은 case.
- **여러 클래스 혼합 예시**: `data/raw/steel/02.라벨링데이터/1. RTAL/RT_AL_02_14488185.json` — `porosity` 2개 + `lack of fusion` 2개, `meta.is_crowd: 1`.
- `meta.is_crowd`가 1이면 여러 클래스가 섞여 있음을 미리 알려주는 플래그로 보인다(교차검증 필요).

**annotation_case 조합별 전수 분포** (2,250건):

| 조합 | 건수 |
| --- | ---: |
| normal | 450 |
| lack of fusion | 449 |
| porosity | 447 |
| crack | 225 |
| incomplete penetration | 225 |
| undercut | 225 |
| slag inclusion | 224 |
| lack of fusion + porosity | 3 |
| porosity + slag inclusion | 2 |

---

## 7. "확인할 핵심 질문" 답변 정리

- **이미지와 JSON은 어떤 값으로 연결되는가?** → 파일명(확장자 제외)이 동일. `image_data.file_name`도 동일 값.
- **한 이미지에 Annotation이 여러 개 들어갈 수 있는가?** → 가능하다. 최대 98개까지 확인됨 (6절).
- **한 객체의 Polygon 좌표는 어떤 구조인가?** → `{"x": [...], "y": [...]}` 형태의 분리된 배열 (5절).
- **클래스명은 한글과 영문 중 무엇을 사용하는가?** → 영문. 단 `class` 필드가 아니라 `case` 필드에 들어있다 (3절).
- **정상 이미지는 Annotation이 비어 있는가?** → 아니다. `class: "normal", case: ""`인 polygon 1개가 존재한다 (4절).
- **이미지 크기 정보가 실제 이미지와 일치하는가?** → 일치한다 (샘플 검증, 2절).

---

## 8. 작업3 완료 조건 확인

- (v) JSON에서 클래스와 좌표를 추출할 경로를 설명할 수 있다 — `annotations[].case`(클래스), `annotations[].coordinate.x/.y`(좌표)
- (v) 이미지와 JSON의 연결 규칙이 확인되었다 — 1절
- (v) 정상 데이터와 불량 데이터 구조 차이가 확인되었다 — 4절
- (v) 다중 객체 구조가 확인되었다 — 6절
- (v) 데이터 파싱 규칙을 코드로 작성할 수 있다 — 2·3·5절의 필드 경로로 파싱 가능

---

## 9. 참고

- 이미지 파일을 코드로 열 때는 `docs/reports/data-inventory.md` 8절에 기록된 대로 `cv2.imread` 대신 `np.fromfile + cv2.imdecode`를 사용해야 한다 (한글 경로 이슈).
