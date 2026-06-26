from pathlib import Path

import pandas as pd

from report_cleaner.config import CSV_ENCODING, build_paths


def test_mapping_csv_files_are_utf8_sig() -> None:
    paths = build_paths()

    for csv_file in sorted(paths.mapping_dir.glob("*.csv")):
        data = csv_file.read_bytes()
        assert data.startswith(b"\xef\xbb\xbf"), f"{csv_file.name} must use UTF-8 with BOM"
        pd.read_csv(csv_file, dtype=str, encoding=CSV_ENCODING).fillna("")

