from __future__ import annotations

import argparse

from .config import build_paths
from .environment import (
    build_environment_checks,
    environment_has_errors,
    format_environment_checks,
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="醫院癌症報表清洗器")
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
        print("待確認對照規則 CSV 已產生。")
        print(f"藥物待確認：{drug_file}")
        print(f"治療醫令待確認：{order_file}")
        print(f"TNM／期別待確認：{stage_file}")
        return

    if args.command == "apply-mapping-review":
        from .mapping_review import apply_mapping_review_files

        result = apply_mapping_review_files(paths)
        print("待確認對照規則已套用。")
        print(f"新增藥物規則：{result['drug_rows_added']} 筆")
        print(f"新增治療醫令規則：{result['order_rows_added']} 筆")
        print(f"新增 TNM／期別規則：{result['stage_rows_added']} 筆")
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

    print("報表清洗完成。")
    print(f"已處理來源檔：{len(processed_files)} 份")
    print(f"標準化明細：{len(standardized_frame)} 筆")
    print(f"病人主檔：{len(patient_master_frame)} 筆")
    print(f"病人總表：{len(patient_list_frame)} 筆")
    print(f"ICD10 待確認：{len(unmatched_icd10_frame)} 筆")
    print(f"TNM／期別檢查：{len(stage_review_frame)} 筆")
    print(f"未分類藥物醫令：{len(unmapped_drug_orders_frame)} 筆")
    print(f"未分類治療醫令：{len(unmapped_treatment_orders_frame)} 筆")
    print(f"輸出檔案：{actual_output}")


if __name__ == "__main__":
    main()
