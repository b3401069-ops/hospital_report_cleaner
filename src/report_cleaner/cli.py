from __future__ import annotations

import argparse

from .config import build_paths
from .environment import (
    build_environment_checks,
    environment_has_errors,
    format_environment_checks,
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Hospital report cleaner")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["clean", "export-mapping-review", "apply-mapping-review", "check-env"],
        default="clean",
    )
    args = parser.parse_args(argv)
    paths = build_paths()

    if args.command == "check-env":
        checks = build_environment_checks(paths)
        print(format_environment_checks(checks))
        if environment_has_errors(checks):
            raise SystemExit(1)
        return

    if args.command == "export-mapping-review":
        from .mapping_review import export_mapping_review_files

        drug_file, order_file, stage_file = export_mapping_review_files(paths)
        print("Mapping review CSV files generated.")
        print(f"Drug review: {drug_file}")
        print(f"Treatment order review: {order_file}")
        print(f"TNM stage review: {stage_file}")
        return

    if args.command == "apply-mapping-review":
        from .mapping_review import apply_mapping_review_files

        result = apply_mapping_review_files(paths)
        print("Mapping review CSV files applied.")
        print(f"Drug mapping rows added: {result['drug_rows_added']}")
        print(f"Treatment order mapping rows added: {result['order_rows_added']}")
        print(f"TNM stage mapping rows added: {result['stage_rows_added']}")
        return

    from .cleaner import export_cleaned_report, run_cleaning

    (
        cleaned_frame,
        standardized_frame,
        patient_master_frame,
        patient_list_frame,
        unmatched_icd10_frame,
        stage_review_frame,
        unmapped_drug_orders_frame,
        unmapped_treatment_orders_frame,
        processed_files,
    ) = run_cleaning(paths)
    actual_output = export_cleaned_report(
        cleaned_frame,
        standardized_frame,
        patient_master_frame,
        patient_list_frame,
        unmatched_icd10_frame,
        stage_review_frame,
        unmapped_drug_orders_frame,
        unmapped_treatment_orders_frame,
        paths.output_file,
    )

    print("Cleaned report generated successfully.")
    print(f"Processed files: {len(processed_files)}")
    print(f"Standardized rows: {len(standardized_frame)}")
    print(f"Patient master rows: {len(patient_master_frame)}")
    print(f"Patient list rows: {len(patient_list_frame)}")
    print(f"Unmatched ICD10 rows: {len(unmatched_icd10_frame)}")
    print(f"Stage review rows: {len(stage_review_frame)}")
    print(f"Unmapped drug order rows: {len(unmapped_drug_orders_frame)}")
    print(f"Unmapped treatment order rows: {len(unmapped_treatment_orders_frame)}")
    print(f"Output: {actual_output}")


if __name__ == "__main__":
    main()
