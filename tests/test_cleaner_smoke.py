import pandas as pd

from report_cleaner.cleaner import (
    _apply_manual_icd10_mapping,
    _build_stage_review_report,
    _build_unmapped_drug_orders_report,
    _build_unmapped_treatment_orders_report,
    _build_unmatched_icd10_report,
    _classify_drug_treatment,
    _classify_order_treatment,
    _standardize_guideline_drug,
    _standardize_inpatient,
    _standardize_order_detail,
    _standardize_tnm,
    _standardize_treatment_plan,
    run_cleaning,
)
from report_cleaner.config import build_paths


def test_run_cleaning_reads_current_raw_reports() -> None:
    paths = build_paths()

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

    assert processed_files
    assert isinstance(cleaned_frame, pd.DataFrame)
    assert isinstance(standardized_frame, pd.DataFrame)
    assert isinstance(patient_master_frame, pd.DataFrame)
    assert isinstance(patient_list_frame, pd.DataFrame)
    assert isinstance(unmatched_icd10_frame, pd.DataFrame)
    assert isinstance(stage_review_frame, pd.DataFrame)
    assert isinstance(unmapped_drug_orders_frame, pd.DataFrame)
    assert isinstance(unmapped_treatment_orders_frame, pd.DataFrame)
    assert "source_file" in standardized_frame.columns
    assert "patient_key" in standardized_frame.columns


def test_standardize_inpatient_reads_mapped_patient_columns() -> None:
    frame = pd.DataFrame(
        {
            "住院序號": ["1140014876"],
            "patient_id": ["0002178423"],
            "patient_name": ["陳國眞"],
            "主診斷": ["C54.1"],
            "住院日": ["20251025000000"],
            "出院日": ["20260108235900"],
        }
    )

    standardized = _standardize_inpatient(frame, "癌症指標-住院人次人日", "inpatient.xls", "", "")

    assert standardized.loc[0, "medical_record_no"] == "0002178423"
    assert standardized.loc[0, "patient_name"] == "陳國眞"
    assert standardized.loc[0, "icd10_code"] == "C54.1"


def test_standardize_tnm_uses_d12_icd10_and_doctor_fields() -> None:
    frame = pd.DataFrame(
        {
            "收案日期": ["20260106"],
            "個案編號": ["2026010006"],
            "病歷號碼": ["0001541556"],
            "病患姓名": ["盧珊珊"],
            "癌別": ["BR_乳癌"],
            "癌別說明": ["C50.8 乳房重疊部位之惡性腫瘤"],
            "簡稱": ["乳癌"],
            "主責醫師": ["黃善鴻"],
            "最初診斷日期": ["20260105"],
            "組合": ["pT1ccN0cM0"],
            "期別": ["1"],
        }
    )

    standardized = _standardize_tnm(frame, "D1.2 癌症收案者基本資料及TNM相關資訊", "d12.xls", "", "")

    assert standardized.loc[0, "medical_record_no"] == "0001541556"
    assert standardized.loc[0, "icd10_code"] == "C50.8"
    assert standardized.loc[0, "diagnosis_text"] == "乳癌"
    assert standardized.loc[0, "doctor"] == "黃善鴻"


def test_unmatched_icd10_report_keeps_known_diagnosis_text() -> None:
    frame = pd.DataFrame(
        {
            "icd10_code": ["C71.9"],
            "cancer_type": [""],
            "diagnosis_text": [""],
            "report_name": ["癌症指標-住院人次人日"],
        }
    )
    enriched = _apply_manual_icd10_mapping(
        frame,
        {"C71.9": ("", "腦惡性腫瘤"), "C71": ("", "腦惡性腫瘤")},
    )

    report = _build_unmatched_icd10_report(enriched)

    assert report.loc[0, "icd10_code"] == "C71.9"
    assert report.loc[0, "cancer_type"] == ""
    assert report.loc[0, "diagnosis_text"] == "腦惡性腫瘤"


def test_unmatched_icd10_report_ignores_non_cancer_codes() -> None:
    frame = pd.DataFrame(
        {
            "icd10_code": ["Z51.11", "C78.00"],
            "cancer_type": ["", ""],
            "diagnosis_text": ["來院接受抗腫瘤化學治療", "肺續發性惡性腫瘤"],
            "report_name": ["指引藥物", "指引藥物"],
        }
    )

    report = _build_unmatched_icd10_report(frame)

    assert report["icd10_code"].tolist() == ["C78.00"]
    assert report["notes"].tolist() == ["secondary_or_metastatic_code_needs_primary_site_review"]


def test_stage_review_report_adds_review_reason() -> None:
    frame = pd.DataFrame(
        {
            "cancer_type": ["LC", "CR", "BR"],
            "clinical_tnm": ["cT2NxMx", "cT3N1M0", ""],
            "pathologic_tnm": ["", "", "pT1cN0M0"],
            "final_stage": ["", "", "1"],
            "final_stage_source": ["", "", "reported"],
        }
    )

    report = _build_stage_review_report(frame)

    reasons = set(report["review_reason"])
    assert "missing_final_stage_with_unknown_tnm" in reasons
    assert "missing_final_stage" in reasons
    assert "reported_stage" in reasons
    assert "primary_tnm" in report.columns


def test_standardize_guideline_drug_classifies_drug_treatments() -> None:
    frame = pd.DataFrame(
        {
            "開單日期": ["20250101", "20250102", "20250103", "20250104"],
            "病歷號": ["001", "002", "003", "004"],
            "主治醫師": ["A", "B", "C", "D"],
            "醫令碼": ["I5FU2", "IKEY", "OFEM2", "OTEP1"],
            "名稱": [
                "Fluorouracil 50mg/ml 20ml",
                "Pembrolizumab 100mg/vial",
                "Letrozole 2.5mg",
                "Tepotinib 225mg",
            ],
            "主診斷": ["C18.9", "C34.9", "C50.9", "C34.9"],
            "診斷名稱": ["結腸惡性腫瘤", "肺惡性腫瘤", "乳癌", "肺惡性腫瘤"],
        }
    )

    standardized = _standardize_guideline_drug(frame, "11401-11505指引藥物測試", "drug.xls", "", "")

    assert standardized.loc[0, "chemotherapy"] == "Y"
    assert standardized.loc[1, "immunotherapy"] == "Y"
    assert standardized.loc[2, "hormone_therapy"] == "Y"
    assert standardized.loc[3, "targeted_therapy"] == "Y"
    assert standardized.loc[3, "order_name"] == "Tepotinib 225mg"


def test_drug_treatment_mapping_rules_can_classify_new_drug_names() -> None:
    order_code = pd.Series(["ONEW"])
    order_name = pd.Series(["Examplemab 100mg"])
    mapping = [
        {
            "treatment_type": "targeted_therapy",
            "name_pattern": "examplemab",
            "order_code": "",
            "order_code_prefix": "",
        }
    ]

    flags = _classify_drug_treatment(order_code, order_name, mapping)

    assert flags["targeted_therapy"].iloc[0] == "Y"
    assert flags["chemotherapy"].iloc[0] == ""


def test_standardize_treatment_plan_reads_case_list_treatment_columns() -> None:
    frame = pd.DataFrame(
        {
            "收案日期": ["1150101"],
            "個案編號": ["CASE1"],
            "病歷號": ["001"],
            "癌別": ["CR_結腸直腸癌"],
            "初次診斷日期": ["1141231"],
            "主治醫師": ["醫師A"],
            "化療填寫日期": ["1150201"],
            "電療填寫日期": ["1150301"],
            "賀爾蒙填寫日期": ["1150401"],
            "標靶填寫日期": ["1150501"],
            "手術填寫日期": ["1150601"],
        }
    )

    standardized = _standardize_treatment_plan(frame, "11401-11505收案清單", "case.xls", "", "")

    assert standardized.loc[0, "medical_record_no"] == "001"
    assert standardized.loc[0, "chemotherapy"] == "Y"
    assert standardized.loc[0, "radiation_therapy"] == "Y"
    assert standardized.loc[0, "hormone_therapy"] == "Y"
    assert standardized.loc[0, "targeted_therapy"] == "Y"
    assert standardized.loc[0, "surgery"] == "Y"


def test_standardize_order_detail_classifies_radiation_planning() -> None:
    frame = pd.DataFrame(
        {
            "病歷號碼": ["001"],
            "醫令代碼": ["36015B"],
            "醫令名稱": ["電腦治療規劃-複雜"],
            "執行日期-起": ["20250101"],
        }
    )

    standardized = _standardize_order_detail(frame, "11401-11505放腫醫囑", "rt.xls", "", "")

    assert standardized.loc[0, "radiation_therapy"] == "Y"
    assert standardized.loc[0, "radiation_therapy_date"] == "20250101"


def test_order_treatment_mapping_rules_can_classify_procedure_codes() -> None:
    order_code = pd.Series(["99999X"])
    order_name = pd.Series(["測試術式"])
    mapping = [
        {
            "treatment_type": "surgery",
            "name_pattern": "",
            "order_code": "99999X",
            "order_code_prefix": "",
            "cancer_type": "TS_測試癌",
            "diagnosis_text": "測試癌",
        }
    ]

    flags = _classify_order_treatment("測試報表", order_code, order_name, mapping)

    assert flags["surgery"].iloc[0] == "Y"
    assert flags["chemotherapy"].iloc[0] == ""


def test_standardize_order_detail_uses_mapping_cancer_type() -> None:
    frame = pd.DataFrame(
        {
            "病歷號碼": ["001"],
            "醫令代碼": ["99999X"],
            "醫令名稱": ["測試術式"],
            "執行日期-起": ["20250101"],
        }
    )
    mapping = [
        {
            "treatment_type": "surgery",
            "name_pattern": "",
            "order_code": "99999X",
            "order_code_prefix": "",
            "cancer_type": "TS_測試癌",
            "diagnosis_text": "測試癌",
        }
    ]

    standardized = _standardize_order_detail(frame, "測試手術", "surgery.xls", "", "", mapping)

    assert standardized.loc[0, "surgery"] == "Y"
    assert standardized.loc[0, "cancer_type"] == "TS_測試癌"
    assert standardized.loc[0, "diagnosis_text"] == "測試癌"


def test_unmapped_order_reports_list_only_unclassified_orders() -> None:
    frame = pd.DataFrame(
        {
            "report_name": ["11401-11505指引藥物99", "11401-11505測試醫囑", "11401-11505測試醫囑"],
            "order_code": ["ONEW", "99999X", "37038B"],
            "order_name": ["New drug 100mg", "新治療醫令", "靜脈血管內化學藥物注射一小時內"],
            "diagnosis_text": ["測試診斷", "測試診斷", "測試診斷"],
            "chemotherapy": ["", "", "Y"],
            "targeted_therapy": ["", "", ""],
            "immunotherapy": ["", "", ""],
            "hormone_therapy": ["", "", ""],
            "radiation_therapy": ["", "", ""],
            "surgery": ["", "", ""],
            "tace": ["", "", ""],
            "rfa": ["", "", ""],
        }
    )

    drug_report = _build_unmapped_drug_orders_report(frame)
    treatment_report = _build_unmapped_treatment_orders_report(frame)

    assert drug_report["order_code"].tolist() == ["ONEW"]
    assert treatment_report["order_code"].tolist() == ["99999X"]
