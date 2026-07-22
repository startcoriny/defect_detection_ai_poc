import json
from pathlib import Path
from typing import Any


# JSON 파일을 읽고 파싱하며 오류는 호출자에게 그대로 전달한다.
def load_json(json_path: Path) -> Any:
    with json_path.open("r", encoding="utf-8") as json_file:
        return json.load(json_file)
