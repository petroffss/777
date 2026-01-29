from pathlib import Path
from typing import Iterable


def scan_pdfs(directory: Path) -> Iterable[Path]:
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() == ".pdf":
            yield path
