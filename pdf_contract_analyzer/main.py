from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    def load_dotenv() -> bool:
        return False

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover - optional dependency
    class _SimpleProgress:
        def __init__(self, iterable):
            self._iterable = iterable

        def __iter__(self):
            return iter(self._iterable)

        def set_postfix(self, **kwargs):
            return None

        def write(self, message: str):
            print(message)

    def tqdm(iterable, **kwargs):  # type: ignore[override]
        return _SimpleProgress(iterable)

from config import AppConfig
from excel_generator import write_report
from file_scanner import scan_pdfs
from llm_analyzer import LlmAnalyzer
from pdf_processor import PdfProcessor
from utils import build_cache_key, load_cache, save_cache, setup_logging


def parse_args() -> AppConfig:
    parser = argparse.ArgumentParser(description="PDF contract analyzer")
    parser.add_argument("-d", "--directory", required=True, help="Directory to scan")
    parser.add_argument("--api", choices=["gemini", "openrouter"], default="gemini")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--output-format", choices=["xlsx", "csv"], default="xlsx")
    parser.add_argument("--ocr", choices=["on", "off", "auto"], default="auto")
    parser.add_argument("--max-chars", type=int, default=20000)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    output = Path(args.output) if args.output else None
    return AppConfig(
        directory=Path(args.directory),
        api=args.api,
        output=output,
        max_pages=args.max_pages,
        output_format=args.output_format,
        ocr=args.ocr,
        max_chars=args.max_chars,
        verbose=args.verbose,
    )


def default_output_path(output_format: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path(f"contracts_analysis_{timestamp}.{output_format}")


def main() -> None:
    load_dotenv()
    config = parse_args()
    logger = setup_logging(config.verbose)

    scanner = scan_pdfs(config.directory)
    pdf_paths = list(scanner)
    total_files = len(pdf_paths)

    processor = PdfProcessor(max_pages=config.max_pages, ocr_mode=config.ocr)
    analyzer = LlmAnalyzer(config.api, config.gemini_api_key if config.api == "gemini" else config.openrouter_api_key)

    cache_data = load_cache(config.cache_path)
    results = []

    progress = tqdm(pdf_paths, desc="Processing PDFs", unit="file")

    for index, pdf_path in enumerate(progress, start=1):
        status = "OK"
        error_message = ""
        contract_number = "Не найдено"
        contract_date = "Не найдено"
        subject = "Не найдено"
        ocr_used = False
        pages = 0

        progress.set_postfix(found=f"{index}/{total_files}")

        try:
            cache_key = build_cache_key(pdf_path)
            cached = cache_data.get(cache_key)
            if cached:
                results.append(cached)
                progress.write(f"{pdf_path.name}: OK (cached)")
                continue

            pdf_result = processor.extract_text(pdf_path)
            pages = pdf_result.pages
            ocr_used = pdf_result.ocr_used

            llm_result = analyzer.analyze(pdf_result.text, config.max_chars)
            contract_number = llm_result.contract_number
            contract_date = llm_result.contract_date
            subject = llm_result.subject

            if pdf_result.ocr_available is False and config.ocr in {"auto", "on"}:
                logger.info("OCR not available; processed without OCR for %s", pdf_path)

        except Exception as exc:  # noqa: BLE001
            status = "ERROR"
            error_message = str(exc)
            logger.error("Failed processing %s", pdf_path, exc_info=True)

        record = {
            "file_name": pdf_path.name,
            "file_path": str(pdf_path),
            "pages": pages,
            "contract_number": contract_number,
            "contract_date": contract_date,
            "subject": subject,
            "status": status,
            "error_message": error_message,
            "ocr_used": ocr_used,
        }
        cache_data[build_cache_key(pdf_path)] = record
        results.append(record)

        progress.write(f"{pdf_path.name}: {status}")

    save_cache(config.cache_path, cache_data)

    output_path = config.output or default_output_path(config.output_format)
    report_path = write_report(results, output_path, config.output_format)
    logger.info("Report written to %s", report_path)


if __name__ == "__main__":
    main()
