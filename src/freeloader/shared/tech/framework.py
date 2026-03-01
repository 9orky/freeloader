import re
from typing import Protocol


class Framework(Protocol):
    name: str
    file_line_pattern: str

    def detect(self, file_content: str) -> bool:
        return bool(re.search(self.file_line_pattern, file_content, re.IGNORECASE | re.MULTILINE))
