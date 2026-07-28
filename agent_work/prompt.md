# 구현 지시서: dataset_v3 구축 스크립트 생성 (EXP-005용 Train slag_inclusion 오버샘플링)

## 배경

EXP-P1-DET-004(데이터 확장, dataset_v2)는 porosity Recall·Small Recall·mAP50-95를 개선했지만, 그 과정에서 slag_inclusion Recall이 0.333→0.179로 떨어졌다. 원인은 dataset_v1→v2 확장 시 porosity 객체는 약 2.4배(241→575) 늘었는데 slag_inclusion은 약 1.2배(198→237)만 늘어, Train 기준 클래스 객체 비율이 1.26:1(dataset_v1)에서 2.26:1(dataset_v2)로 벌어졌기 때문으로 추정된다(`docs/12_next_experiment_plan.md` 참조).

이번 작업은 **Validation·Test는 건드리지 않고 Train 분할에서만** slag_inclusion이 포함된 이미지를 그대로 1벌 복제(총 2벌)해 `dataset_v3`를 만드는 스크립트를 작성한다. 별도 회전·반전 등 증강은 적용하지 않는다 — "노출 빈도"만 바꾸는 것이 이번 실험의 유일한 변수다.

## 기능 및 요구사항

`src/dataset/v3/oversample_slag.py` 파일 하나를 새로 작성한다(원본 스크립트를 복사하는 게 아니라 새로 작성).

### 입력

- `data/processed/dataset_v2/`(이미지: `images/{train,val,test}/*.jpg`, 라벨: `labels/{train,val,test}/*.txt`, `data.yaml`)

### 출력

- `data/processed/dataset_v3/`(dataset_v2와 동일한 구조: `images/{train,val,test}/`, `labels/{train,val,test}/`, `data.yaml`)

### 처리 로직

1. `data/processed/dataset_v2/images/val`, `images/test`, `labels/val`, `labels/test`의 모든 파일을 `data/processed/dataset_v3/`의 대응 위치로 **그대로 복사**한다(오버샘플링 없음, 파일명도 그대로).
2. `data/processed/dataset_v2/images/train`, `labels/train`의 모든 이미지·라벨 쌍을 `data/processed/dataset_v3/images/train`, `labels/train`으로 **그대로 복사**한다(원본 1벌).
3. 각 Train 라벨 파일(`.txt`)을 읽어서 **한 줄 이상이 `4 `(공백 포함, slag_inclusion의 class_id)로 시작하는 경우**, 그 이미지·라벨 쌍을 파일명에 `_dup1` 접미사를 붙여(`<원본이름>_dup1.jpg`, `<원본이름>_dup1.txt`) 한 번 더 복사한다(라벨 내용은 원본과 완전히 동일하게, class_id 등 변경 없음). 즉 slag_inclusion이 포함된 이미지는 최종적으로 원본 1벌 + `_dup1` 1벌 = 총 2벌이 된다.
4. `data.yaml`을 새로 생성한다 — dataset_v2의 `data.yaml`과 `names`(클래스 매핑)는 동일하게 유지하고, `path`만 `"data/processed/dataset_v3"`로 바꾼다.
5. 처리 완료 후 다음을 로그로 남긴다: Train 원본 이미지 수, slag_inclusion 포함(복제 대상) 이미지 수, 복제 후 Train 전체 이미지 수, 복제 전/후 클래스별(porosity/slag_inclusion) Train 객체 수(라벨 파일의 각 줄에서 class_id를 세어 계산).

### 검증

- 복사 전 대상 디렉터리(`data/processed/dataset_v3`)가 이미 있으면 삭제 후 새로 만든다(재실행 가능하게).
- 복사한 모든 이미지·라벨 쌍의 basename이 서로 일치하는지 확인한다(이미지는 있는데 라벨이 없거나 그 반대인 경우 예외 발생).
- Val·Test 이미지 수가 dataset_v2와 정확히 같은지 확인한다(84장 각각 — 다만 하드코딩된 상수로 만들지 말고, `dataset_v2`에서 실제로 센 개수와 `dataset_v3`에 복사된 개수를 비교하는 방식으로 검증한다).

## 구현 범위 (In Scope)

- `src/dataset/v3/oversample_slag.py` 생성

## 구현 제외 범위 (Out of Scope)

- `data/processed/dataset_v2/`, `src/dataset/v2/`, `src/conversion/v2/` 수정 — 절대 건드리지 않는다.
- `src/model/exp5/`, `src/evaluation/exp5/`, `src/visualization/exp5/` 생성 — 이번 작업 범위 아님(dataset_v3가 만들어진 뒤 별도로 진행).
- 실제 스크립트 실행 — CLAUDE가 수행한다.
- 회전·반전·색상 변경 등 이미지 증강 — 이번 작업 범위 아니다. 순수 파일 복제만 한다.

## 완료 기준 (Definition of Done)

- `( )` `src/dataset/v3/oversample_slag.py`가 생성됐다.
- `( )` Val·Test는 오버샘플링 없이 그대로 복사하는 로직이다.
- `( )` Train에서 slag_inclusion 포함 이미지만 식별해 `_dup1` 접미사로 복제하는 로직이다(class_id 4 판별 방식이 라벨 파일 각 줄의 첫 토큰을 확인하는 방식으로 구현돼 있다).
- `( )` `data.yaml`의 `path`가 `data/processed/dataset_v3`이고 나머지 클래스 매핑은 dataset_v2와 동일하다.
- `( )` 코드가 PEP 8 / black 포맷을 따른다(ruff 통과).

## 제약사항

- `data/processed/dataset_v2/`는 읽기만 하고 수정하지 않는다.
- 이 작업은 CODEX 샌드박스에서 Python을 실행해 검증할 수 없다. 코드 작성까지만 CODEX가 담당하고, 실제 실행·검증은 CLAUDE가 수행한다.
- 이 스크립트는 새로 작성하는 것이라 기존 스크립트의 특정 파일 구조를 그대로 복사할 필요는 없지만, 프로젝트의 기존 스타일(로깅에 `logging` 모듈 사용, `PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent`로 경로 계산 — `src/dataset/v3/oversample_slag.py`는 프로젝트 루트 기준 3단계 깊이이므로 `parent.parent.parent.parent`가 맞다, `main()` 함수 + `if __name__ == "__main__": sys.exit(main())` 패턴)을 따른다.

## 테스트 방법 (CLAUDE가 이어서 수행)

1. `black --check`, `ruff check`를 새 파일에 실행
2. `venv/Scripts/python.exe src/dataset/v3/oversample_slag.py` 실행 → 로그로 Train 복제 전/후 개수 확인
3. `data/processed/dataset_v3/images/{train,val,test}`, `labels/{train,val,test}` 파일 수 직접 세어 검증(Val·Test는 각각 84장 그대로, Train은 원본+복제분)
4. Train 라벨 전체에서 class_id별 객체 수를 다시 세어 슬래그 비율이 개선됐는지 확인
