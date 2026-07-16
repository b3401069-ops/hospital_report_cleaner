from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from report_cleaner.cleaner import (
    PATIENT_LIST_COLUMNS,
    PATIENT_MASTER_COLUMNS,
    export_cleaned_report,
)


def _row(columns: list[str], **values: str) -> dict[str, str]:
    row = {column: "" for column in columns}
    row.update(values)
    return row


def test_export_creates_chinese_first_page_and_readable_patient_table(
    tmp_path: Path,
) -> None:
    patient_master = pd.DataFrame(
        [
            _row(
                PATIENT_MASTER_COLUMNS,
                patient_name="測試個案",
                sex="女",
                medical_record_no="TEST001",
                age_at_diagnosis="65",
                diagnosis_date="2025-02-03",
                cancer_type="BR_乳癌",
                diagnosis_text="乳房惡性腫瘤",
                final_stage="IIA",
                doctor="測試醫師",
                chemotherapy="Y",
                surgery="Y",
                patient_key="MRN:TEST001",
            )
        ]
    )
    patient_list = pd.DataFrame(
        [
            _row(
                PATIENT_LIST_COLUMNS,
                patient_name="測試個案",
                sex="女",
                medical_record_no="TEST001",
                age_at_diagnosis="65",
                diagnosis_date="2025-02-03",
                cancer_type="BR_乳癌",
                diagnosis_text="乳房惡性腫瘤",
                final_stage="IIA",
                doctor="測試醫師",
                chemotherapy="Y",
                surgery="Y",
            )
        ]
    )
    standardized = patient_master.assign(
        report_name="測試來源",
        source_file="sample.xlsx",
        record_key="R1",
    )
    empty = pd.DataFrame()
    stage_review = pd.DataFrame(
        [
            {
                "cancer_type": "LC_肺癌",
                "clinical_tnm": "cT3N1M0",
                "pathologic_tnm": "",
                "primary_tnm": "cT3N1M0",
                "final_stage": "",
                "final_stage_source": "",
                "review_reason": "missing_final_stage",
                "count": 1,
            }
        ]
    )

    output = export_cleaned_report(
        standardized,
        standardized,
        patient_master,
        patient_list,
        empty,
        stage_review,
        empty,
        empty,
        tmp_path / "cleaned_reports.xlsx",
    )

    workbook = load_workbook(output, data_only=False)
    assert workbook.sheetnames[:4] == ["使用說明", "病人總表", "統計摘要", "月趨勢"]
    assert workbook.active.title == "使用說明"
    assert workbook["使用說明"]["A1"].value == "癌症報表清洗結果"
    assert workbook["使用說明"]["B13"].value == 1

    patient_sheet = workbook["病人總表"]
    assert patient_sheet.freeze_panes == "E2"
    assert patient_sheet.auto_filter.ref == f"A1:AK{patient_sheet.max_row}"
    headers = [cell.value for cell in patient_sheet[1]]
    assert headers[:10] == [
        "病患姓名",
        "病歷號",
        "性別",
        "年齡",
        "癌別",
        "診斷名稱",
        "診斷日",
        "最終期別",
        "治療摘要",
        "主責醫師",
    ]
    assert patient_sheet["I2"].value == "化療、手術"
    assert patient_sheet["P2"].value == "有"

    assert workbook["TNM期別待確認"]["G1"].value == "待確認原因"
    assert workbook["TNM期別待確認"]["G2"].value == "有 TNM，缺最終期別"
    for technical_sheet in (
        "cleaned_data",
        "standardized_data",
        "patient_master",
        "patient_list",
        "stage_review",
    ):
        assert workbook[technical_sheet].sheet_state == "hidden"
