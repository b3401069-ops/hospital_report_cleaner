#!/usr/bin/env python3
"""醫院報表清洗工具 - 主程式入口

使用方式：
  python main.py
  
將報表放入 raw/ 資料夾，執行後結果在 output/cleaned_reports.xlsx
"""
from __future__ import annotations

import sys
import os

# 確保 src 目錄在 Python 路徑中
project_root = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(project_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from report_cleaner.cleaner import export_cleaned_report, run_cleaning
from report_cleaner.config import build_paths


def main() -> None:
    paths = build_paths()
    (
        cleaned_frame,
        standardized_frame,
        patient_master_frame,
        patient_list_frame,
        unmatched_icd10_frame,
        stage_review_frame,
        processed_files,
    ) = run_cleaning(paths)
    actual_output = export_cleaned_report(
        cleaned_frame,
        standardized_frame,
        patient_master_frame,
        patient_list_frame,
        unmatched_icd10_frame,
        stage_review_frame,
        paths.output_file,
    )

    print("Cleaned report generated successfully.")
    print(f"Processed files: {len(processed_files)}")
    print(f"Standardized rows: {len(standardized_frame)}")
    print(f"Patient master rows: {len(patient_master_frame)}")
    print(f"Patient list rows: {len(patient_list_frame)}")
    print(f"Unmatched ICD10 rows: {len(unmatched_icd10_frame)}")
    print(f"Stage review rows: {len(stage_review_frame)}")
    print(f"Output: {actual_output}")


if __name__ == "__main__":
    main()
