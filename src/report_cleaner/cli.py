from __future__ import annotations

from .cleaner import export_cleaned_report, run_cleaning
from .config import build_paths


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
