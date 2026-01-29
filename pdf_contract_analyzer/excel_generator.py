from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


def write_report(records: Iterable[dict], output_path: Path, output_format: str) -> Path:
    df = pd.DataFrame(records)
    if output_format == "csv":
        output_path = output_path.with_suffix(".csv")
        df.to_csv(output_path, index=False)
    else:
        output_path = output_path.with_suffix(".xlsx")
        df.to_excel(output_path, index=False)
    return output_path
