from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DATASET_PATH = PROJECT_ROOT / "data"
OUTPUT_PATH = PROJECT_ROOT / "outputs"


# 프로젝트 실행에 필요한 폴더를 준비하고 경로 정보를 출력한다.
def main() -> None:
    DATASET_PATH.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    print("Auto Labeling PoC v0.1")
    print()
    print(f"Project Root : {PROJECT_ROOT}")
    print(f"Dataset Path : {DATASET_PATH}")
    print(f"Output Path : {OUTPUT_PATH}")
    print()
    print("Ready.")


if __name__ == "__main__":
    main()
