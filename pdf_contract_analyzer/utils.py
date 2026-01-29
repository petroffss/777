import json
import logging
from pathlib import Path
from typing import Any, Dict


def setup_logging(verbose: bool) -> logging.Logger:
    logger = logging.getLogger("pdf_contract_analyzer")
    logger.setLevel(logging.DEBUG)

    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler("errors.log", encoding="utf-8")
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def load_cache(cache_path: Path) -> Dict[str, Any]:
    if not cache_path.exists():
        return {}
    try:
        with cache_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        return {}


def save_cache(cache_path: Path, cache_data: Dict[str, Any]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w", encoding="utf-8") as handle:
        json.dump(cache_data, handle, ensure_ascii=False, indent=2)


def build_cache_key(path: Path) -> str:
    stat = path.stat()
    return f"{path.resolve()}::{stat.st_size}::{stat.st_mtime}"
