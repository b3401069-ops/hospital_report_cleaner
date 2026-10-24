from __future__ import annotations

import pandas as pd


PATHOLOGY_SHEET = "病理紀錄"
ELIGIBILITY_SHEET = "癌症資格待確認"
REGISTRY = "有癌症收案依據"
PATHOLOGY = "有病理惡性紀錄"
BOTH = "有收案及病理惡性依據"
PENDING = "癌症資格待確認"
PATIENT_FIELDS = ["cohort_eligible", "cancer_evidence", "evidence_sources"]
PATHOLOGY_FIELDS = [
    "pathology_id", "pathology_report_time", "pathology_result",
    "pathology_agreement", "pathology_level", "pathology_item", "pathology_order",
]


def texts(frame: pd.DataFrame, column: str) -> pd.Series:
    return frame.get(column, pd.Series("", index=frame.index, dtype="object")).fillna("").astype(str).str.strip()


def mark_registry_source(frame: pd.DataFrame, report_name: str) -> pd.DataFrame:
    """Record direct case-list evidence before any patient lookup enrichment."""
    result = frame.copy()
    is_case_report = any(tag in report_name for tag in (
        "D1.2", "TNM", "治療計畫書", "癌症個案", "收案清單", "收案名單", "個案清單",
    ))
    result["registry_evidence"] = ""
    if is_case_report and not texts(result, "order_category").eq("pathology").any():
        valid = texts(result, "case_id").ne("") & texts(result, "cancer_type").ne("")
        result.loc[valid, "registry_evidence"] = "Y"
    return result


def annotate_evidence(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    keys = texts(result, "patient_key")
    pathology = texts(result, "order_category").eq("pathology")
    outcomes = texts(result, "pathology_result")
    # Different results for the same specimen remain unresolved; do not let a
    # positive keyword or an arbitrary row order decide which version is final.
    specimen = pd.DataFrame({"patient": keys, "specimen": texts(result, "pathology_id"), "result": outcomes})
    conflicts = specimen.loc[pathology & specimen["specimen"].ne("") & outcomes.ne("")].groupby(
        ["patient", "specimen"]
    )["result"].nunique()
    conflict_keys = set(conflicts[conflicts.gt(1)].index)
    conflict = pd.Series([(p, s) in conflict_keys for p, s in zip(keys, specimen["specimen"])], index=result.index)
    result["pathology_review_note"] = ""
    result.loc[pathology & conflict, "pathology_review_note"] = "同病理編號有不同結果，需核對完整報告"
    final = texts(result, "pathology_level").isin(["完整報告", "最終報告"])
    result.loc[pathology & ~final, "pathology_review_note"] = "報告層級未確認，需核對完整報告"
    valid_pathology = (
        pathology & outcomes.eq("惡性") & final & ~conflict
        & texts(result, "pathology_id").ne("") & texts(result, "medical_record_no").ne("")
    )
    registry = texts(result, "registry_evidence").eq("Y")
    registry_keys = set(keys[registry & keys.ne("")])
    pathology_keys = set(keys[valid_pathology & keys.ne("")])
    registered, malignant = keys.isin(registry_keys), keys.isin(pathology_keys)
    result["cohort_eligible"] = ""
    result.loc[registered | malignant, "cohort_eligible"] = "Y"
    result["cancer_evidence"] = PENDING
    result.loc[registered, "cancer_evidence"] = REGISTRY
    result.loc[malignant, "cancer_evidence"] = PATHOLOGY
    result.loc[registered & malignant, "cancer_evidence"] = BOTH
    evidence = result.loc[registry | valid_pathology].copy()
    sources = evidence.groupby("patient_key")["source_file"].agg(
        lambda values: " | ".join(dict.fromkeys(str(v) for v in values if str(v).strip()))
    ) if not evidence.empty else pd.Series(dtype="object")
    result["evidence_sources"] = keys.map(sources).fillna("")
    return result


def eligible_rows(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.loc[texts(frame, "cohort_eligible").eq("Y")].copy()


def pathology_output(frame: pd.DataFrame) -> pd.DataFrame:
    headers = {
        "patient_name": "病患姓名", "medical_record_no": "病歷號", "pathology_id": "病理編號",
        "case_date": "看診日", "pathology_report_time": "報告時間", "pathology_result": "病理結果（原文）",
        "pathology_level": "報告層級", "pathology_agreement": "診斷比對（原文）",
        "pathology_item": "病理項目", "pathology_order": "病理醫令",
        "pathology_review_note": "待核對事項", "cancer_evidence": "病人納入依據", "source_file": "來源檔案",
    }
    working = frame.loc[texts(frame, "order_category").eq("pathology")]
    return pd.DataFrame({label: texts(working, column) for column, label in headers.items()})


def eligibility_output(master: pd.DataFrame, standardized: pd.DataFrame) -> pd.DataFrame:
    pending = master.loc[~texts(master, "cohort_eligible").eq("Y")]
    headers = {
        "patient_name": "病患姓名", "medical_record_no": "病歷號", "case_id": "個案編號",
        "cancer_type": "來源癌別線索", "icd10_code": "來源診斷碼", "diagnosis_text": "來源診斷文字",
        "latest_activity_date": "最後資料日期",
    }
    output = pd.DataFrame({label: texts(pending, column) for column, label in headers.items()})
    keys = texts(pending, "patient_key")
    files = standardized.groupby("patient_key")["source_file"].agg(
        lambda values: " | ".join(dict.fromkeys(str(v) for v in values if str(v).strip()))
    ) if not standardized.empty else pd.Series(dtype="object")
    output["待確認原因"] = "未找到符合條件的收案或病理惡性依據；不代表非癌症"
    output["來源檔案"] = keys.map(files).fillna("")
    return output
