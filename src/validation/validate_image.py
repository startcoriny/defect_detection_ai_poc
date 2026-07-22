from pathlib import Path
from typing import Any

from common.image_utils import read_image


# Validate that one image is readable and agrees with its label dimensions.
def validate_image(
    image_path: str | Path,
    expected_width: Any = None,
    expected_height: Any = None,
) -> list[dict[str, str]]:
    path = Path(image_path) if image_path else None
    if path is None or not path.is_file():
        return [{"severity": "ERROR", "code": "image_missing"}]

    image = read_image(path)
    if image is None:
        return [{"severity": "ERROR", "code": "image_corrupted"}]

    height, width = image.shape[:2]
    issues = []
    if width <= 0 or height <= 0:
        issues.append({"severity": "ERROR", "code": "invalid_image_dimensions"})

    if (
        expected_width is not None
        and expected_height is not None
        and (width, height) != (expected_width, expected_height)
    ):
        issues.append({"severity": "WARNING", "code": "dimension_mismatch"})

    return issues
