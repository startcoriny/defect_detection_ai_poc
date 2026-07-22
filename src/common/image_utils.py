from pathlib import Path

import cv2
import numpy as np


# Read an image without losing support for Unicode paths on Windows.
def read_image(image_path: str | Path) -> np.ndarray | None:
    path = Path(image_path) if image_path else None
    if path is None or not path.is_file():
        return None

    try:
        encoded_image = np.fromfile(path, dtype=np.uint8)
        if encoded_image.size == 0:
            return None
        return cv2.imdecode(encoded_image, cv2.IMREAD_COLOR)
    except (OSError, ValueError, cv2.error):
        return None
