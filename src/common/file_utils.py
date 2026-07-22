from pathlib import Path


# 디렉터리에서 지정한 확장자를 가진 파일 stem을 정렬해 반환한다.
def get_sorted_file_stems(directory: Path, extension: str) -> list[str]:
    normalized_extension = extension.lower()
    if not normalized_extension.startswith("."):
        normalized_extension = f".{normalized_extension}"

    return sorted(
        path.stem
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() == normalized_extension
    )
