from __future__ import annotations

import argparse
from pathlib import Path
from datetime import date

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
        choices=["clean", "case-manager", "export-mapping-review", "apply-mapping-review", "check-env"],
        default="clean",
    )
    parser.add_argument("--source", type=Path, help="個管版來源資料夾（含子目錄），預設 raw")
    parser.add_argument("--output", type=Path, help="個管版輸出 Excel 路徑")
    parser.add_argument("--as-of", type=date.fromisoformat, help="個管版統計截止日 YYYY-MM-DD；預設來源涵蓋日")
    args = parser.parse_args(argv)
    paths = build_paths()

    if args.command != "case-manager" and any([args.source, args.output, args.as_of]):
        parser.error("--source、--output、--as-of 僅適用 case-manager")
    if args.command == "case-manager":
        from .case_manager_sources import load_sources
        from .case_manager import build_report
        from .case_manager_excel import export_report, sync_manual
        from .patient_stage_review import review_path, sync_review

        source = args.source or paths.raw_dir
        output = args.output or paths.output_dir / "癌症個案治療整合查詢表.xlsx"
        if source.resolve() == output.resolve().parent or source.resolve() in output.resolve().parents:
            parser.error("個管版輸出請放在來源資料夾之外，避免下次誤讀輸出。")
        try:
            print("正在讀取來源報表（含子資料夾），只在本機處理...")
            sources = load_sources(source, paths.mapping_dir)
            report = build_report(sources, paths.root, as_of=args.as_of)
            manual = paths.root / "review" / "個管人工確認.xlsx"
            records = sync_manual(report, manual)
            stage_file = sync_review(report.stages, review_path(paths.root))
            actual_output = export_report(report, output, records, manual)
        except (ValueError, PermissionError) as error:
            parser.exit(1, f"個管報表未完成：{error}\n請確認來源完整，並關閉輸出及確認Excel後重試。\n")
        print(f"統計截止日：{report.as_of}")
        print(f"收案個案：{len(report.actual)}；病人人數：{len({r['病歷號'] for r in report.actual})}")
        print(f"待辦項目：{len(report.tasks)}；未連結／測試病歷待核對：{len(report.pending)}")
        print(f"個管報表：{actual_output}")
        print(f"待辦確認檔：{manual}")
        print(f"期別確認檔：{stage_file}")
        return

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
    from .patient_stage_review import review_path, sync_review

    try:
        confirmation_file = sync_review(standardized_frame, review_path(paths.root))
    except PermissionError:
        print("報表已產生，但病人期別確認檔無法更新。請儲存並關閉該 Excel 後重新清洗。")
        raise SystemExit(1)

    print("報表清洗完成。")
    print(f"已處理來源檔：{len(processed_files)} 份")
    print(f"標準化明細：{len(standardized_frame)} 筆")
    print(f"病人主檔：{len(patient_master_frame)} 筆")
    print(f"病人總表：{len(patient_list_frame)} 筆")
    print(f"癌症資格待確認：{len(patient_master_frame) - len(patient_list_frame)} 人")
    print(f"ICD10 待確認：{len(unmatched_icd10_frame)} 筆")
    print(f"TNM／期別檢查：{len(stage_review_frame)} 筆")
    print(f"未分類藥物醫令：{len(unmapped_drug_orders_frame)} 筆")
    print(f"未分類治療醫令：{len(unmapped_treatment_orders_frame)} 筆")
    print(f"輸出檔案：{actual_output}")
    print(f"病人期別確認檔：{confirmation_file}")


if __name__ == "__main__":
    main()
