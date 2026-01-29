from __future__ import annotations

from pathlib import Path
from typing import Iterable

try:
    import pandas as pd
except ImportError:  # pragma: no cover - optional dependency
    pd = None


def write_report(records: Iterable[dict], output_path: Path, output_format: str) -> Path:
    records = list(records)
    if output_format == "csv":
        output_path = output_path.with_suffix(".csv")
        if pd is None:
            import csv

            with output_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=records[0].keys() if records else [])
                writer.writeheader()
                for record in records:
                    writer.writerow(record)
        else:
            df = pd.DataFrame(records)
            df.to_csv(output_path, index=False)
    else:
        if pd is None:
            raise RuntimeError("pandas is required for xlsx output")
        output_path = output_path.with_suffix(".xlsx")
        df = pd.DataFrame(records)
        df.to_excel(output_path, index=False)
    return output_path
