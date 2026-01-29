import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AppConfig:
    directory: Path
    api: str = "gemini"
    output: Optional[Path] = None
    max_pages: int = 5
    output_format: str = "xlsx"
    ocr: str = "auto"  # on|off|auto
    max_chars: int = 20000
    verbose: bool = False
    cache_path: Path = Path(".cache/contracts_cache.json")

    @property
    def gemini_api_key(self) -> Optional[str]:
        return os.getenv("GEMINI_API_KEY")

    @property
    def openrouter_api_key(self) -> Optional[str]:
        return os.getenv("OPENROUTER_API_KEY")
