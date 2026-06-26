from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

from .config import ProjectPaths

SUPPORTED_SUFFIXES = {".xlsx", ".xls", ".csv"}
SENSITIVE_COLUMN_PATTERNS = (
    "身分證",
    "身份證",
    "電話",
    "地址",
)
SUMMARY_KEYWORDS = ("合計", "總計", "subtotal", "total")
STANDARD_COLUMNS = [
    "patient_name",
    "sex",
    "medical_record_no",
    "birth_date",
    "age_at_diagnosis",
    "diagnosis_date",
    "case_date",
    "death_date",
    "last_followup_date",
    "survival_days",
    "case_id",
    "cancer_type",
    "icd10_code",
    "diagnosis_text",
    "clinical_tnm",
    "pathologic_tnm",
    "final_stage",
    "final_stage_source",
    "case_category_code",
    "case_category_label",
    "doctor",
    "manager",
    "chemotherapy",
    "chemotherapy_date",
    "targeted_therapy",
    "targeted_therapy_date",
    "immunotherapy",
    "immunotherapy_date",
    "hormone_therapy",
    "hormone_therapy_date",
    "radiation_therapy",
    "radiation_therapy_date",
    "surgery",
    "surgery_date",
    "tace",
    "tace_date",
    "rfa",
    "rfa_date",
    "treatment_status",
    "report_date",
    "location",
    "record_key",
    "patient_key",
    "report_name",
    "source_file",
    "report_period_start",
    "report_period_end",
]
PATIENT_MASTER_COLUMNS = [
    "patient_name",
    "sex",
    "medical_record_no",
    "birth_date",
    "age_at_diagnosis",
    "diagnosis_date",
    "case_date",
    "death_date",
    "last_followup_date",
    "survival_days",
    "case_id",
    "cancer_type",
    "icd10_code",
    "diagnosis_text",
    "clinical_tnm",
    "pathologic_tnm",
    "final_stage",
    "final_stage_source",
    "case_category_code",
    "case_category_label",
    "doctor",
    "manager",
    "chemotherapy",
    "chemotherapy_date",
    "targeted_therapy",
    "targeted_therapy_date",
    "immunotherapy",
    "immunotherapy_date",
    "hormone_therapy",
    "hormone_therapy_date",
    "radiation_therapy",
    "radiation_therapy_date",
    "surgery",
    "surgery_date",
    "tace",
    "tace_date",
    "rfa",
    "rfa_date",
    "patient_key",
    "report_period_start",
    "report_period_end",
]
PATIENT_LIST_COLUMNS = [
    "patient_name",
    "sex",
    "medical_record_no",
    "birth_date",
    "age_at_diagnosis",
    "diagnosis_date",
    "death_date",
    "last_followup_date",
    "survival_days",
    "case_id",
    "cancer_type",
    "icd10_code",
    "diagnosis_text",
    "clinical_tnm",
    "pathologic_tnm",
    "final_stage",
    "case_category_code",
    "case_category_label",
    "doctor",
    "manager",
    "chemotherapy",
    "chemotherapy_date",
    "targeted_therapy",
    "targeted_therapy_date",
    "immunotherapy",
    "immunotherapy_date",
    "hormone_therapy",
    "hormone_therapy_date",
    "radiation_therapy",
    "radiation_therapy_date",
    "surgery",
    "surgery_date",
    "tace",
    "tace_date",
    "rfa",
    "rfa_date",
]
PATIENT_LIST_ZH_HEADERS = {
    "patient_name": "病患姓名",
    "sex": "性別",
    "medical_record_no": "病歷號",
    "birth_date": "生日",
    "age_at_diagnosis": "年齡",
    "diagnosis_date": "診斷日",
    "death_date": "死亡日期",
    "last_followup_date": "最後回診日",
    "survival_days": "存活時間(天)",
    "case_id": "個案編號",
    "cancer_type": "癌別",
    "icd10_code": "ICD10",
    "diagnosis_text": "診斷名稱",
    "clinical_tnm": "臨床分期",
    "pathologic_tnm": "病理分期",
    "final_stage": "最終期別",
    "case_category_code": "個案分類代碼",
    "case_category_label": "個案分類",
    "doctor": "主責醫師",
    "manager": "個管師",
    "chemotherapy": "化學治療",
    "chemotherapy_date": "化學治療日期",
    "targeted_therapy": "標靶治療",
    "targeted_therapy_date": "標靶治療日期",
    "immunotherapy": "免疫治療",
    "immunotherapy_date": "免疫治療日期",
    "hormone_therapy": "抗荷爾蒙治療",
    "hormone_therapy_date": "抗荷爾蒙治療日期",
    "radiation_therapy": "放射治療",
    "radiation_therapy_date": "放射治療日期",
    "surgery": "手術",
    "surgery_date": "手術日期",
    "tace": "TACE",
    "tace_date": "TACE日期",
    "rfa": "RFA",
    "rfa_date": "RFA日期",
}
SPECIAL_CANCER_TYPE_LABELS = {
    "CL": "膽管癌",
    "LCA": "喉癌",
    "XX": "未分類",
}
COLUMN_ALIASES = {
    "姓名": ["patient_name", "姓名", "病人姓名", "病患姓名"],
    "病人姓名": ["patient_name", "姓名", "病人姓名", "病患姓名"],
    "病患姓名": ["patient_name", "姓名", "病人姓名", "病患姓名"],
    "性別": ["sex", "性別"],
    "病歷號": ["medical_record_no", "patient_id", "病歷號", "病歷編號", "病歷號碼"],
    "病歷編號": ["medical_record_no", "patient_id", "病歷號", "病歷編號", "病歷號碼"],
    "病歷號碼": ["medical_record_no", "patient_id", "病歷號", "病歷編號", "病歷號碼"],
    "出生日期": ["birth_date", "出生日期", "生日"],
    "生日": ["birth_date", "出生日期", "生日"],
    "年齡": ["age_at_diagnosis", "年齡"],
    "最初診斷日期": ["diagnosis_date", "最初診斷日期", "診斷日"],
    "診斷日": ["diagnosis_date", "最初診斷日期", "診斷日"],
    "死亡日期": ["death_date", "死亡日期"],
    "最近看診日": ["last_followup_date", "最近看診日", "最近追蹤日"],
    "最近追蹤日": ["last_followup_date", "最近看診日", "最近追蹤日"],
    "癌別": ["cancer_type", "癌別"],
    "癌別說明": ["癌別說明"],
    "主責醫師": ["doctor", "主責醫師", "醫師", "主治醫師"],
    "收案個管師": ["manager", "收案個管師"],
}


def run_cleaning(
    paths: ProjectPaths,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    list[str],
]:
    files = _collect_source_files(paths.raw_dir)
    if not files:
        raise FileNotFoundError("No source reports were found in raw/.")

    column_mapping = _load_column_mapping(paths.column_mapping_file)
    value_mapping = _load_value_mapping(paths.value_mapping_file)
    tnm_stage_mapping = _load_tnm_stage_mapping(paths.tnm_stage_mapping_file)
    manual_icd10_mapping = _load_manual_icd10_mapping(paths.icd10_mapping_file)
    drug_treatment_mapping = _load_drug_treatment_mapping(paths.drug_treatment_mapping_file)
    order_treatment_mapping = _load_order_treatment_mapping(paths.order_treatment_mapping_file)

    cleaned_frames: list[pd.DataFrame] = []
    standardized_frames: list[pd.DataFrame] = []
    processed_files: list[str] = []
    icd10_lookup: dict[str, tuple[str, str]] = {}
    patient_lookup: dict[str, dict[str, str]] = {}

    for source_file in files:
        frame, period_start, period_end = _read_report(source_file)
        frame = _normalize_columns(frame)
        icd10_lookup.update(_extract_icd10_lookup(frame))
        patient_lookup = _merge_patient_lookup(patient_lookup, _extract_patient_lookup(frame))
        frame = _drop_sensitive_columns(frame)
        frame = frame.rename(columns=column_mapping)
        frame = _drop_empty_and_summary_rows(frame)
        frame = _normalize_text_cells(frame)
        frame = _apply_value_mapping(frame, value_mapping)
        frame = _normalize_dates(frame)
        frame["report_name"] = source_file.stem
        frame["source_file"] = source_file.name
        frame["report_period_start"] = period_start
        frame["report_period_end"] = period_end

        cleaned_frames.append(frame)
        standardized_frames.append(
            _build_standardized_frame(
                frame,
                source_file.stem,
                source_file.name,
                period_start,
                period_end,
                drug_treatment_mapping,
                order_treatment_mapping,
            )
        )
        processed_files.append(source_file.name)

    combined = pd.concat(cleaned_frames, ignore_index=True, sort=False)
    combined = combined.drop_duplicates().reset_index(drop=True)
    combined = _reorder_columns(
        combined,
        [
            "report_date",
            "department",
            "doctor",
            "report_type",
            "result",
            "report_name",
            "source_file",
        ],
    )

    standardized = pd.concat(standardized_frames, ignore_index=True, sort=False)
    standardized = _enrich_from_icd10_lookup(standardized, icd10_lookup)
    standardized = _apply_manual_icd10_mapping(standardized, manual_icd10_mapping)
    standardized = _enrich_from_patient_lookup(standardized, patient_lookup)
    standardized = _apply_stage_mapping(standardized, tnm_stage_mapping)
    standardized = _add_record_keys(standardized)
    standardized = _deduplicate_standardized(standardized)
    standardized = _reorder_columns(standardized, STANDARD_COLUMNS)
    patient_master = _build_patient_master(standardized)
    patient_list = _build_patient_list(patient_master)
    unmatched_icd10 = _build_unmatched_icd10_report(standardized)
    stage_review = _build_stage_review_report(standardized)
    unmapped_drug_orders = _build_unmapped_drug_orders_report(standardized)
    unmapped_treatment_orders = _build_unmapped_treatment_orders_report(standardized)

    return (
        combined,
        standardized,
        patient_master,
        patient_list,
        unmatched_icd10,
        stage_review,
        unmapped_drug_orders,
        unmapped_treatment_orders,
        processed_files,
    )


def export_cleaned_report(
    cleaned_frame: pd.DataFrame,
    standardized_frame: pd.DataFrame,
    patient_master_frame: pd.DataFrame,
    patient_list_frame: pd.DataFrame,
    unmatched_icd10_frame: pd.DataFrame,
    stage_review_frame: pd.DataFrame,
    unmapped_drug_orders_frame: pd.DataFrame,
    unmapped_treatment_orders_frame: pd.DataFrame,
    output_file: Path,
) -> Path:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    target_file = _resolve_writable_output_path(output_file)
    patient_list_zh_frame = _build_patient_list_zh(patient_list_frame)
    summary_zh_frame = _build_summary_zh(patient_master_frame)
    summary_trend_zh_frame = _build_summary_trend_zh(patient_master_frame)
    with pd.ExcelWriter(target_file, engine="openpyxl") as writer:
        cleaned_frame.to_excel(writer, index=False, sheet_name="cleaned_data")
        standardized_frame.to_excel(writer, index=False, sheet_name="standardized_data")
        patient_master_frame.to_excel(writer, index=False, sheet_name="patient_master")
        patient_list_frame.to_excel(writer, index=False, sheet_name="patient_list")
        patient_list_zh_frame.to_excel(writer, index=False, sheet_name="patient_list_zh")
        summary_zh_frame.to_excel(writer, index=False, sheet_name="summary_zh")
        summary_trend_zh_frame.to_excel(writer, index=False, sheet_name="summary_trend_zh")
        unmatched_icd10_frame.to_excel(writer, index=False, sheet_name="unmatched_icd10")
        stage_review_frame.to_excel(writer, index=False, sheet_name="stage_review")
        unmapped_drug_orders_frame.to_excel(writer, index=False, sheet_name="unmapped_drug_orders")
        unmapped_treatment_orders_frame.to_excel(writer, index=False, sheet_name="unmapped_treatment_orders")
    return target_file


def _resolve_writable_output_path(output_file: Path) -> Path:
    try:
        with open(output_file, "ab"):
            pass
        return output_file
    except PermissionError:
        stem = output_file.stem
        suffix = output_file.suffix
        for index in range(1, 100):
            candidate = output_file.with_name(f"{stem}_{index}{suffix}")
            try:
                with open(candidate, "ab"):
                    pass
                return candidate
            except PermissionError:
                continue
    return output_file


def _collect_source_files(raw_dir: Path) -> list[Path]:
    if not raw_dir.exists():
        return []
    return sorted(
        file_path
        for file_path in raw_dir.iterdir()
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_SUFFIXES
    )


def _read_report(file_path: Path) -> tuple[pd.DataFrame, str, str]:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(file_path, dtype=str, encoding="utf-8-sig")
        period_start, period_end = _extract_period_from_filename(file_path.name)
        return frame, period_start, period_end
    preview = pd.read_excel(file_path, header=None, dtype=str, nrows=8)
    header_row = _detect_header_row(preview)
    period_start, period_end = _extract_report_period(file_path.name, preview)
    frame = pd.read_excel(file_path, header=header_row, dtype=str)
    return frame, period_start, period_end


def _detect_header_row(preview: pd.DataFrame) -> int:
    best_index = 0
    best_score = -1

    for index, row in preview.iterrows():
        values = [str(value).strip() for value in row.fillna("")]
        non_empty = [value for value in values if value]
        if not non_empty:
            continue

        unnamed_count = sum(value.lower().startswith("unnamed:") for value in non_empty)
        metadata_hits = sum(
            value.startswith("&") or bool(re.fullmatch(r"\d{6,14}", value))
            for value in non_empty
        )
        score = (len(non_empty) * 10) - (unnamed_count * 3) - (metadata_hits * 4)

        if score > best_score:
            best_index = int(index)
            best_score = score

    return best_index


def _extract_report_period(file_name: str, preview: pd.DataFrame) -> tuple[str, str]:
    file_period = _extract_period_from_filename(file_name)
    if any(file_period):
        return file_period

    flattened = " ".join(
        str(value).strip()
        for row in preview.fillna("").values.tolist()
        for value in row
        if str(value).strip()
    )
    return _extract_period_from_text(flattened)


def _extract_period_from_filename(file_name: str) -> tuple[str, str]:
    normalized_name = file_name.replace("_", "").replace("-", "")

    range_match = re.search(r"(20\d{2}(?:0[1-9]|1[0-2])(?:[0-3]\d)?)\D*(20\d{2}(?:0[1-9]|1[0-2])(?:[0-3]\d)?)", normalized_name)
    if range_match:
        return (
            _normalize_period_token(range_match.group(1), is_end=False),
            _normalize_period_token(range_match.group(2), is_end=True),
        )

    month_match = re.search(r"(20\d{2}(?:0[1-9]|1[0-2]))", normalized_name)
    if month_match:
        token = month_match.group(1)
        return _normalize_period_token(token, is_end=False), _normalize_period_token(token, is_end=True)

    return "", ""


def _extract_period_from_text(text: str) -> tuple[str, str]:
    text = text.strip()
    if not text:
        return "", ""

    patterns = [
        (r"起日[:：]?\D*(\d{7,8})", r"迄日[:：]?\D*(\d{7,8})"),
        (r"西元年月起\D*(\d{6})", r"西元年月迄\D*(\d{6})"),
        (r"申報年月\D*(\d{6})", None),
        (r"西元年\D*(\d{4})", None),
    ]

    for start_pattern, end_pattern in patterns:
        start_match = re.search(start_pattern, text)
        if not start_match:
            continue
        start_token = start_match.group(1)

        if end_pattern:
            end_match = re.search(end_pattern, text)
            if end_match:
                end_token = end_match.group(1)
                return (
                    _normalize_period_token(start_token, is_end=False),
                    _normalize_period_token(end_token, is_end=True),
                )

        normalized = _normalize_period_token(start_token, is_end=False)
        normalized_end = _normalize_period_token(start_token, is_end=True)
        return normalized, normalized_end

    return "", ""


def _normalize_period_token(token: str, *, is_end: bool) -> str:
    digits = re.sub(r"\D", "", token)
    if len(digits) == 7:
        digits = str(int(digits[:3]) + 1911) + digits[3:]
    if len(digits) == 4:
        return f"{digits}-12-31" if is_end else f"{digits}-01-01"
    if len(digits) == 6:
        year = int(digits[:4])
        month = int(digits[4:6])
        if is_end:
            last_day = pd.Period(f"{year:04d}-{month:02d}", freq="M").days_in_month
            return f"{year:04d}-{month:02d}-{last_day:02d}"
        return f"{year:04d}-{month:02d}-01"
    if len(digits) == 8:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"
    return ""


def _load_column_mapping(mapping_file: Path) -> dict[str, str]:
    if not mapping_file.exists():
        return {}
    mapping_frame = pd.read_csv(mapping_file, dtype=str, encoding="utf-8-sig").fillna("")
    return {
        row["source_column"].strip(): row["target_column"].strip()
        for _, row in mapping_frame.iterrows()
        if row["source_column"].strip() and row["target_column"].strip()
    }


def _load_value_mapping(mapping_file: Path) -> dict[str, dict[str, str]]:
    if not mapping_file.exists():
        return {}
    mapping_frame = pd.read_csv(mapping_file, dtype=str, encoding="utf-8-sig").fillna("")
    mappings: dict[str, dict[str, str]] = {}
    for _, row in mapping_frame.iterrows():
        column = row["column"].strip()
        source_value = row["source_value"].strip()
        target_value = row["target_value"].strip()
        if not column or not source_value:
            continue
        mappings.setdefault(column, {})[source_value] = target_value
    return mappings


def _load_tnm_stage_mapping(mapping_file: Path) -> dict[tuple[str, str], str]:
    if not mapping_file.exists():
        return {}
    mapping_frame = pd.read_csv(mapping_file, dtype=str, encoding="utf-8-sig").fillna("")
    mapping: dict[tuple[str, str], str] = {}
    for _, row in mapping_frame.iterrows():
        cancer_type = row.get("cancer_type", "").strip()
        tnm_pattern = _normalize_tnm_text(row.get("tnm_pattern", ""))
        final_stage = row.get("final_stage", "").strip()
        if cancer_type and tnm_pattern and final_stage:
            mapping[(cancer_type, tnm_pattern)] = final_stage
    return mapping


def _load_manual_icd10_mapping(mapping_file: Path) -> dict[str, tuple[str, str]]:
    if not mapping_file.exists():
        return {}
    mapping_frame = pd.read_csv(mapping_file, dtype=str, encoding="utf-8-sig").fillna("")
    mapping: dict[str, tuple[str, str]] = {}
    for _, row in mapping_frame.iterrows():
        icd10_code = _normalize_icd10_code(row.get("icd10_code", ""))
        cancer_type = row.get("cancer_type", "").strip()
        diagnosis_text = row.get("diagnosis_text", "").strip()
        if icd10_code and (cancer_type or diagnosis_text):
            mapping[icd10_code] = (cancer_type, diagnosis_text)
            mapping.setdefault(icd10_code.split(".")[0], (cancer_type, diagnosis_text))
    return mapping


def _load_drug_treatment_mapping(mapping_file: Path) -> list[dict[str, str]]:
    if not mapping_file.exists():
        return []
    mapping_frame = pd.read_csv(mapping_file, dtype=str, encoding="utf-8-sig").fillna("")
    mappings: list[dict[str, str]] = []
    for _, row in mapping_frame.iterrows():
        treatment_type = row.get("treatment_type", "").strip()
        if treatment_type not in {
            "chemotherapy",
            "targeted_therapy",
            "immunotherapy",
            "hormone_therapy",
        }:
            continue
        mappings.append(
            {
                "treatment_type": treatment_type,
                "name_pattern": row.get("name_pattern", "").strip(),
                "order_code": row.get("order_code", "").strip().upper(),
                "order_code_prefix": row.get("order_code_prefix", "").strip().upper(),
            }
        )
    return mappings


def _load_order_treatment_mapping(mapping_file: Path) -> list[dict[str, str]]:
    if not mapping_file.exists():
        return []
    mapping_frame = pd.read_csv(mapping_file, dtype=str, encoding="utf-8-sig").fillna("")
    mappings: list[dict[str, str]] = []
    for _, row in mapping_frame.iterrows():
        treatment_type = row.get("treatment_type", "").strip()
        if treatment_type not in {
            "chemotherapy",
            "radiation_therapy",
            "surgery",
            "tace",
            "rfa",
        }:
            continue
        mappings.append(
            {
                "treatment_type": treatment_type,
                "name_pattern": row.get("name_pattern", "").strip(),
                "order_code": row.get("order_code", "").strip().upper(),
                "order_code_prefix": row.get("order_code_prefix", "").strip().upper(),
                "cancer_type": row.get("cancer_type", "").strip(),
                "diagnosis_text": row.get("diagnosis_text", "").strip(),
            }
        )
    return mappings


def _normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame.columns = [str(column).strip() for column in frame.columns]
    return frame


def _drop_sensitive_columns(frame: pd.DataFrame) -> pd.DataFrame:
    columns_to_keep = []
    for column in frame.columns:
        column_name = str(column).strip()
        if any(pattern in column_name for pattern in SENSITIVE_COLUMN_PATTERNS):
            continue
        columns_to_keep.append(column)
    return frame.loc[:, columns_to_keep].copy()


def _drop_empty_and_summary_rows(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.dropna(how="all").copy()
    if frame.empty:
        return frame

    first_column = frame.columns[0]
    mask = frame[first_column].fillna("").astype(str).str.strip().str.lower()
    is_summary = mask.apply(lambda value: any(keyword in value for keyword in SUMMARY_KEYWORDS))
    return frame.loc[~is_summary].reset_index(drop=True)


def _normalize_text_cells(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.apply(
        lambda column: column.map(
            lambda value: value.strip() if isinstance(value, str) else value
        )
    )


def _apply_value_mapping(
    frame: pd.DataFrame, value_mapping: dict[str, dict[str, str]]
) -> pd.DataFrame:
    frame = frame.copy()
    for column, column_map in value_mapping.items():
        if column not in frame.columns:
            continue
        frame[column] = frame[column].replace(column_map)
    return frame


def _normalize_dates(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    for column in frame.columns:
        if not _looks_like_date_column(column):
            continue
        frame[column] = frame[column].map(_normalize_date_value)
    return frame


def _looks_like_date_column(column: str) -> bool:
    column_name = str(column).lower()
    return "date" in column_name or "日期" in column_name or "日" in column_name


def _normalize_date_value(value: object) -> object:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return value
    if not isinstance(value, str):
        return value

    text = value.strip()
    if not text:
        return ""

    digits = re.sub(r"\D", "", text)
    if digits and digits[:3].isdigit():
        first_three = int(digits[:3])
        first_four = int(digits[:4]) if len(digits) >= 4 and digits[:4].isdigit() else 9999
        if first_three <= 300 and first_four < 1911 and len(digits) in (7, 11, 12, 13):
            digits = str(first_three + 1911) + digits[3:]
    if len(digits) == 8:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"
    if len(digits) == 11:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]} {digits[8:10]}:{digits[10:11]}0"
    if len(digits) == 12:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]} {digits[8:10]}:{digits[10:12]}"
    if len(digits) == 13:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]} {digits[8:10]}:{digits[10:12]}:{digits[12:13]}0"
    if len(digits) == 14:
        return (
            f"{digits[:4]}-{digits[4:6]}-{digits[6:8]} "
            f"{digits[8:10]}:{digits[10:12]}:{digits[12:14]}"
        )

    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return text
    if parsed.hour == 0 and parsed.minute == 0 and parsed.second == 0:
        return parsed.strftime("%Y-%m-%d")
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def _build_standardized_frame(
    frame: pd.DataFrame,
    report_name: str,
    source_file: str,
    period_start: str,
    period_end: str,
    drug_treatment_mapping: list[dict[str, str]] | None = None,
    order_treatment_mapping: list[dict[str, str]] | None = None,
) -> pd.DataFrame:
    if {"醫令代碼", "醫令名稱"}.issubset(frame.columns):
        return _standardize_order_detail(
            frame,
            report_name,
            source_file,
            period_start,
            period_end,
            order_treatment_mapping,
        )
    if {"醫令碼", "名稱"}.issubset(frame.columns):
        return _standardize_guideline_drug(
            frame,
            report_name,
            source_file,
            period_start,
            period_end,
            drug_treatment_mapping,
        )
    if "化療流程時間" in report_name:
        return _standardize_chemo_timeline(frame, report_name, source_file, period_start, period_end)
    if "化療名單" in report_name:
        return _standardize_chemo_list(frame, report_name, source_file, period_start, period_end)
    if "TNM" in report_name:
        return _standardize_tnm(frame, report_name, source_file, period_start, period_end)
    if "治療計畫書" in report_name or "計畫書" in report_name or "收案清單" in report_name:
        return _standardize_treatment_plan(frame, report_name, source_file, period_start, period_end)
    if "住院人次人日" in report_name:
        return _standardize_inpatient(frame, report_name, source_file, period_start, period_end)

    standardized = frame.copy()
    standardized["report_name"] = report_name
    standardized["source_file"] = source_file
    standardized["report_period_start"] = period_start
    standardized["report_period_end"] = period_end
    return _reorder_columns(standardized, STANDARD_COLUMNS)


def _standardize_chemo_list(
    frame: pd.DataFrame, report_name: str, source_file: str, period_start: str, period_end: str
) -> pd.DataFrame:
    standardized = pd.DataFrame(
        {
            "report_name": report_name,
            "source_file": source_file,
            "report_period_start": period_start,
            "report_period_end": period_end,
            "patient_name": _first_available_column(frame, ["姓名", "病人姓名", "病患姓名"]),
            "sex": _first_available_column(frame, ["性別"]),
            "medical_record_no": _first_available_column(frame, ["病歷號", "病歷編號", "病歷號碼"]),
            "diagnosis_date": "",
            "case_date": "",
            "death_date": "",
            "last_followup_date": "",
            "cancer_type": "",
            "icd10_code": "",
            "diagnosis_text": "",
            "clinical_tnm": "",
            "pathologic_tnm": "",
            "final_stage": "",
            "case_category_code": "",
            "case_category_label": "",
            "chemotherapy": "Y",
            "chemotherapy_date": _column_or_blank(frame, "醫囑開始執行日期"),
            "targeted_therapy": "",
            "targeted_therapy_date": "",
            "immunotherapy": "",
            "immunotherapy_date": "",
            "hormone_therapy": "",
            "hormone_therapy_date": "",
            "radiation_therapy": "",
            "radiation_therapy_date": "",
            "surgery": "",
            "surgery_date": "",
            "tace": "",
            "tace_date": "",
            "rfa": "",
            "rfa_date": "",
            "treatment_status": _column_or_blank(frame, "狀態"),
            "report_date": _column_or_blank(frame, "醫囑開始執行日期"),
            "location": _column_or_blank(frame, "病床"),
        }
    )
    standardized["birth_date"] = ""
    standardized["age_at_diagnosis"] = ""
    standardized["survival_days"] = ""
    return _reorder_columns(standardized, STANDARD_COLUMNS)


def _standardize_tnm(
    frame: pd.DataFrame, report_name: str, source_file: str, period_start: str, period_end: str
) -> pd.DataFrame:
    diagnosis_date = _first_non_blank_series(
        _column_or_blank(frame, "最初診斷日期"), _column_or_blank(frame, "收案日期")
    )
    case_date = _first_non_blank_series(
        _column_or_blank(frame, "收案日期"), _column_or_blank(frame, "最初診斷日期")
    )
    last_followup = _first_non_blank_series(
        _column_or_blank(frame, "最近看診日"), _column_or_blank(frame, "最近追蹤日")
    )
    standardized = pd.DataFrame(
        {
            "report_name": report_name,
            "source_file": source_file,
            "report_period_start": period_start,
            "report_period_end": period_end,
            "patient_name": _first_available_column(frame, ["姓名", "病人姓名", "病患姓名"]),
            "sex": _first_available_column(frame, ["性別"]),
            "medical_record_no": _first_available_column(frame, ["病歷號", "病歷編號", "病歷號碼"]),
            "case_id": _column_or_blank(frame, "個案編號"),
            "birth_date": _first_available_column(frame, ["出生日期", "生日"]),
            "diagnosis_date": diagnosis_date,
            "case_date": case_date,
            "death_date": _column_or_blank(frame, "死亡日期"),
            "last_followup_date": last_followup,
            "cancer_type": _column_or_blank(frame, "癌別"),
            "icd10_code": _first_non_blank_series(
                _extract_icd10_series(_column_or_blank(frame, "癌別說明")),
                _extract_icd10_from_cancer_type(_column_or_blank(frame, "癌別")),
            ),
            "diagnosis_text": _first_non_blank_series(
                _first_available_column(frame, ["簡稱"]),
                _extract_diagnosis_text_from_description(_column_or_blank(frame, "癌別說明")),
                _extract_text_from_cancer_type(_column_or_blank(frame, "癌別")),
            ),
            "clinical_tnm": _extract_clinical_tnm(_column_or_blank(frame, "組合")),
            "pathologic_tnm": _extract_pathologic_tnm(_column_or_blank(frame, "組合")),
            "final_stage": _column_or_blank(frame, "期別"),
            "case_category_code": _extract_case_category_code(_column_or_blank(frame, "個案分類")),
            "case_category_label": _extract_case_category_label(_column_or_blank(frame, "個案分類")),
            "doctor": _column_or_blank(frame, "主責醫師"),
            "manager": _column_or_blank(frame, "收案個管師"),
            "chemotherapy": _yes_if_any(frame, ["化學治療填寫日期"]),
            "chemotherapy_date": _column_or_blank(frame, "化學治療填寫日期"),
            "targeted_therapy": _yes_if_any(frame, ["標靶治療日期"]),
            "targeted_therapy_date": _column_or_blank(frame, "標靶治療日期"),
            "immunotherapy": "",
            "immunotherapy_date": "",
            "hormone_therapy": _yes_if_any(frame, ["荷爾蒙治療日期"]),
            "hormone_therapy_date": _column_or_blank(frame, "荷爾蒙治療日期"),
            "radiation_therapy": _yes_if_any(frame, ["放射線治療填寫日期"]),
            "radiation_therapy_date": _column_or_blank(frame, "放射線治療填寫日期"),
            "surgery": _yes_if_any(frame, ["手術填寫日期"]),
            "surgery_date": _column_or_blank(frame, "手術填寫日期"),
            "tace": "",
            "tace_date": "",
            "rfa": "",
            "rfa_date": "",
            "treatment_status": "",
            "report_date": case_date,
            "location": "",
        }
    )
    standardized["age_at_diagnosis"] = _calculate_age_series(
        standardized["birth_date"], standardized["diagnosis_date"]
    )
    standardized["survival_days"] = _calculate_day_diff_series(
        standardized["diagnosis_date"],
        _first_non_blank_series(standardized["death_date"], standardized["last_followup_date"]),
    )
    return _reorder_columns(standardized, STANDARD_COLUMNS)


def _standardize_treatment_plan(
    frame: pd.DataFrame, report_name: str, source_file: str, period_start: str, period_end: str
) -> pd.DataFrame:
    diagnosis_date = _first_non_blank_series(
        _column_or_blank(frame, "最初診斷日期"),
        _column_or_blank(frame, "初次診斷日期"),
        _column_or_blank(frame, "收案日期"),
    )
    case_date = _first_non_blank_series(
        _column_or_blank(frame, "收案日期"), _column_or_blank(frame, "最初診斷日期")
    )
    chemo_date = _first_non_blank_series(
        _column_or_blank(frame, "化學治療填寫日期1"),
        _column_or_blank(frame, "化學治療填寫日期2"),
        _column_or_blank(frame, "化學治療填寫日期"),
        _column_or_blank(frame, "化療填寫日期"),
        _column_or_blank(frame, "口服化療日期"),
        _column_or_blank(frame, "口服填寫日期"),
    )
    targeted_date = _first_non_blank_series(
        _column_or_blank(frame, "標靶治療日期"),
        _column_or_blank(frame, "標靶填寫日期"),
    )
    hormone_date = _first_non_blank_series(
        _column_or_blank(frame, "荷爾蒙治療日期"),
        _column_or_blank(frame, "賀爾蒙填寫日期"),
    )
    radiation_date = _first_non_blank_series(
        _column_or_blank(frame, "放射線治療填寫日期"),
        _column_or_blank(frame, "電療填寫日期"),
        _column_or_blank(frame, "CCRT填寫日期"),
    )
    standardized = pd.DataFrame(
        {
            "report_name": report_name,
            "source_file": source_file,
            "report_period_start": period_start,
            "report_period_end": period_end,
            "patient_name": _first_available_column(frame, ["姓名", "病人姓名", "病患姓名"]),
            "sex": _first_available_column(frame, ["性別"]),
            "medical_record_no": _first_available_column(frame, ["病歷號", "病歷編號", "病歷號碼"]),
            "case_id": _column_or_blank(frame, "個案編號"),
            "birth_date": _first_available_column(frame, ["出生日期", "生日"]),
            "diagnosis_date": diagnosis_date,
            "case_date": case_date,
            "death_date": _column_or_blank(frame, "死亡日期"),
            "last_followup_date": "",
            "cancer_type": _column_or_blank(frame, "癌別"),
            "icd10_code": _extract_icd10_series(_column_or_blank(frame, "癌別說明")),
            "diagnosis_text": _first_non_blank_series(
                _first_available_column(frame, ["簡稱"]),
                _extract_diagnosis_text_from_description(_column_or_blank(frame, "癌別說明")),
                _extract_text_from_cancer_type(_column_or_blank(frame, "癌別")),
            ),
            "clinical_tnm": "",
            "pathologic_tnm": "",
            "final_stage": "",
            "case_category_code": _extract_case_category_code(_column_or_blank(frame, "個案分類")),
            "case_category_label": _extract_case_category_label(_column_or_blank(frame, "個案分類")),
            "doctor": _first_available_column(frame, ["主責醫師", "主治醫師", "填表醫師"]),
            "manager": _column_or_blank(frame, "收案個管師"),
            "chemotherapy": chemo_date.map(lambda value: "Y" if str(value).strip() else ""),
            "chemotherapy_date": chemo_date,
            "targeted_therapy": targeted_date.map(lambda value: "Y" if str(value).strip() else ""),
            "targeted_therapy_date": targeted_date,
            "immunotherapy": _yes_if_any(frame, ["免疫治療填寫日期"]),
            "immunotherapy_date": _column_or_blank(frame, "免疫治療填寫日期"),
            "hormone_therapy": hormone_date.map(lambda value: "Y" if str(value).strip() else ""),
            "hormone_therapy_date": hormone_date,
            "radiation_therapy": radiation_date.map(lambda value: "Y" if str(value).strip() else ""),
            "radiation_therapy_date": radiation_date,
            "surgery": _yes_if_any(frame, ["手術填寫日期"]),
            "surgery_date": _column_or_blank(frame, "手術填寫日期"),
            "tace": _yes_if_any(frame, ["動脈栓塞"]),
            "tace_date": _column_or_blank(frame, "動脈栓塞"),
            "rfa": _yes_if_any(frame, ["RFA"]),
            "rfa_date": _column_or_blank(frame, "RFA"),
            "treatment_status": "",
            "report_date": case_date,
            "location": "",
        }
    )
    standardized["age_at_diagnosis"] = _calculate_age_series(
        standardized["birth_date"], standardized["diagnosis_date"]
    )
    standardized["survival_days"] = _calculate_day_diff_series(
        standardized["diagnosis_date"],
        _first_non_blank_series(standardized["death_date"], standardized["last_followup_date"]),
    )
    return _reorder_columns(standardized, STANDARD_COLUMNS)


def _standardize_guideline_drug(
    frame: pd.DataFrame,
    report_name: str,
    source_file: str,
    period_start: str,
    period_end: str,
    drug_treatment_mapping: list[dict[str, str]] | None = None,
) -> pd.DataFrame:
    order_code = _column_or_blank(frame, "醫令碼")
    order_name = _column_or_blank(frame, "名稱")
    order_date = _column_or_blank(frame, "開單日期")
    treatment_flags = _classify_drug_treatment(order_code, order_name, drug_treatment_mapping)
    standardized = pd.DataFrame(
        {
            "report_name": report_name,
            "source_file": source_file,
            "report_period_start": period_start,
            "report_period_end": period_end,
            "patient_name": "",
            "sex": "",
            "medical_record_no": _column_or_blank(frame, "病歷號"),
            "case_id": "",
            "birth_date": "",
            "diagnosis_date": order_date,
            "case_date": order_date,
            "death_date": "",
            "last_followup_date": "",
            "survival_days": "",
            "cancer_type": "",
            "icd10_code": _extract_icd10_series(_column_or_blank(frame, "主診斷")),
            "diagnosis_text": _column_or_blank(frame, "診斷名稱"),
            "clinical_tnm": "",
            "pathologic_tnm": "",
            "final_stage": "",
            "case_category_code": "",
            "case_category_label": "",
            "doctor": _column_or_blank(frame, "主治醫師"),
            "manager": "",
            "chemotherapy": treatment_flags["chemotherapy"],
            "chemotherapy_date": order_date.where(treatment_flags["chemotherapy"] == "Y", ""),
            "targeted_therapy": treatment_flags["targeted_therapy"],
            "targeted_therapy_date": order_date.where(treatment_flags["targeted_therapy"] == "Y", ""),
            "immunotherapy": treatment_flags["immunotherapy"],
            "immunotherapy_date": order_date.where(treatment_flags["immunotherapy"] == "Y", ""),
            "hormone_therapy": treatment_flags["hormone_therapy"],
            "hormone_therapy_date": order_date.where(treatment_flags["hormone_therapy"] == "Y", ""),
            "radiation_therapy": "",
            "radiation_therapy_date": "",
            "surgery": "",
            "surgery_date": "",
            "tace": "",
            "tace_date": "",
            "rfa": "",
            "rfa_date": "",
            "treatment_status": "",
            "report_date": order_date,
            "location": _column_or_blank(frame, "床位"),
            "order_code": order_code,
            "order_name": order_name,
            "department_code": _column_or_blank(frame, "科別"),
        }
    )
    standardized["age_at_diagnosis"] = ""
    return _reorder_columns(standardized, STANDARD_COLUMNS)


def _standardize_chemo_timeline(
    frame: pd.DataFrame, report_name: str, source_file: str, period_start: str, period_end: str
) -> pd.DataFrame:
    standardized = pd.DataFrame(
        {
            "report_name": report_name,
            "source_file": source_file,
            "report_period_start": period_start,
            "report_period_end": period_end,
            "patient_name": _first_available_column(frame, ["姓名", "病人姓名", "病患姓名"]),
            "sex": _first_available_column(frame, ["性別"]),
            "medical_record_no": _first_available_column(frame, ["病歷號", "病歷編號", "病歷號碼"]),
            "case_id": "",
            "birth_date": _first_available_column(frame, ["出生日期", "生日"]),
            "diagnosis_date": _column_or_blank(frame, "看診日期"),
            "case_date": _column_or_blank(frame, "看診日期"),
            "death_date": "",
            "last_followup_date": "",
            "cancer_type": "",
            "icd10_code": "",
            "diagnosis_text": "",
            "clinical_tnm": "",
            "pathologic_tnm": "",
            "final_stage": "",
            "case_category_code": "",
            "case_category_label": "",
            "doctor": _column_or_blank(frame, "主治醫師"),
            "manager": "",
            "chemotherapy": "Y",
            "chemotherapy_date": _column_or_blank(frame, "化療日期"),
            "targeted_therapy": "",
            "targeted_therapy_date": "",
            "immunotherapy": "",
            "immunotherapy_date": "",
            "hormone_therapy": "",
            "hormone_therapy_date": "",
            "radiation_therapy": "",
            "radiation_therapy_date": "",
            "surgery": "",
            "surgery_date": "",
            "tace": "",
            "tace_date": "",
            "rfa": "",
            "rfa_date": "",
            "treatment_status": "",
            "report_date": _column_or_blank(frame, "化療日期"),
            "location": _column_or_blank(frame, "床號"),
        }
    )
    standardized["age_at_diagnosis"] = _calculate_age_series(
        standardized["birth_date"], standardized["diagnosis_date"]
    )
    standardized["survival_days"] = _calculate_day_diff_series(
        standardized["diagnosis_date"],
        _first_non_blank_series(standardized["death_date"], standardized["last_followup_date"]),
    )
    return _reorder_columns(standardized, STANDARD_COLUMNS)


def _standardize_order_detail(
    frame: pd.DataFrame,
    report_name: str,
    source_file: str,
    period_start: str,
    period_end: str,
    order_treatment_mapping: list[dict[str, str]] | None = None,
) -> pd.DataFrame:
    order_code = _column_or_blank(frame, "醫令代碼")
    order_name = _column_or_blank(frame, "醫令名稱")
    encounter_id = _first_non_blank_series(_column_or_blank(frame, "住院號"), _column_or_blank(frame, "就醫序號"))
    order_start = _first_non_blank_series(_column_or_blank(frame, "執行日期-起"), _column_or_blank(frame, "看診日期"))
    diagnosis_date = _first_non_blank_series(_column_or_blank(frame, "看診日期"), order_start)
    case_date = _first_non_blank_series(_column_or_blank(frame, "住院日"), _column_or_blank(frame, "看診日期"))
    last_followup = _first_non_blank_series(_column_or_blank(frame, "出院日"), _column_or_blank(frame, "切帳日"))
    cancer_type, diagnosis_text = _infer_cancer_from_report_name(report_name)
    treatment_flags = _classify_order_treatment(
        report_name, order_code, order_name, order_treatment_mapping
    )
    mapped_cancer_type = _map_order_rule_value(
        order_code, order_name, order_treatment_mapping, "cancer_type"
    )
    mapped_diagnosis_text = _map_order_rule_value(
        order_code, order_name, order_treatment_mapping, "diagnosis_text"
    )

    standardized = pd.DataFrame(
        {
            "report_name": report_name,
            "source_file": source_file,
            "report_period_start": period_start,
            "report_period_end": period_end,
            "patient_name": _first_available_column(frame, ["姓名", "病人姓名", "病患姓名"]),
            "sex": _first_available_column(frame, ["性別"]),
            "medical_record_no": _first_available_column(frame, ["病歷號", "病歷編號", "病歷號碼"]),
            "case_id": "",
            "birth_date": _first_available_column(frame, ["出生日期", "生日"]),
            "diagnosis_date": diagnosis_date,
            "case_date": case_date,
            "death_date": "",
            "last_followup_date": last_followup,
            "cancer_type": _first_non_blank_series(
                mapped_cancer_type,
                pd.Series(cancer_type, index=frame.index, dtype="object"),
            ),
            "icd10_code": "",
            "diagnosis_text": _first_non_blank_series(
                mapped_diagnosis_text,
                pd.Series(diagnosis_text, index=frame.index, dtype="object"),
            ),
            "clinical_tnm": "",
            "pathologic_tnm": "",
            "final_stage": "",
            "case_category_code": "",
            "case_category_label": "",
            "doctor": _first_non_blank_series(_column_or_blank(frame, "執行醫師"), _column_or_blank(frame, "業績醫師")),
            "manager": "",
            "chemotherapy": treatment_flags["chemotherapy"],
            "chemotherapy_date": order_start.where(treatment_flags["chemotherapy"] == "Y", ""),
            "targeted_therapy": "",
            "targeted_therapy_date": "",
            "immunotherapy": "",
            "immunotherapy_date": "",
            "hormone_therapy": "",
            "hormone_therapy_date": "",
            "radiation_therapy": treatment_flags["radiation_therapy"],
            "radiation_therapy_date": order_start.where(treatment_flags["radiation_therapy"] == "Y", ""),
            "surgery": treatment_flags["surgery"],
            "surgery_date": order_start.where(treatment_flags["surgery"] == "Y", ""),
            "tace": treatment_flags["tace"],
            "tace_date": order_start.where(treatment_flags["tace"] == "Y", ""),
            "rfa": treatment_flags["rfa"],
            "rfa_date": order_start.where(treatment_flags["rfa"] == "Y", ""),
            "treatment_status": _column_or_blank(frame, "報"),
            "report_date": order_start,
            "location": _column_or_blank(frame, "床號"),
            "encounter_id": encounter_id,
            "visit_type": _column_or_blank(frame, "類別"),
            "order_code": order_code,
            "order_name": order_name,
            "department_code": _column_or_blank(frame, "科別"),
            "department_name": _column_or_blank(frame, "科別名"),
            "admission_date": _column_or_blank(frame, "住院日"),
            "discharge_date": _column_or_blank(frame, "出院日"),
        }
    )
    standardized["age_at_diagnosis"] = _calculate_age_series(
        standardized["birth_date"], standardized["diagnosis_date"]
    )
    standardized["survival_days"] = _calculate_day_diff_series(
        standardized["diagnosis_date"],
        _first_non_blank_series(standardized["death_date"], standardized["last_followup_date"]),
    )
    return _reorder_columns(standardized, STANDARD_COLUMNS)


def _standardize_inpatient(
    frame: pd.DataFrame, report_name: str, source_file: str, period_start: str, period_end: str
) -> pd.DataFrame:
    standardized = pd.DataFrame(
        {
            "report_name": report_name,
            "source_file": source_file,
            "report_period_start": period_start,
            "report_period_end": period_end,
            "patient_name": _first_available_column(frame, ["姓名", "病人姓名", "病患姓名"]),
            "sex": _first_available_column(frame, ["性別"]),
            "medical_record_no": _first_available_column(frame, ["病歷號", "病歷編號", "病歷號碼"]),
            "case_id": _column_or_blank(frame, "住院序號"),
            "birth_date": _first_available_column(frame, ["出生日期", "生日"]),
            "diagnosis_date": _first_non_blank_series(
                _column_or_blank(frame, "住院日"), _column_or_blank(frame, "出院日")
            ),
            "case_date": _column_or_blank(frame, "住院日"),
            "death_date": "",
            "last_followup_date": _column_or_blank(frame, "出院日"),
            "cancer_type": "",
            "icd10_code": _first_non_blank_series(
                _column_or_blank(frame, "主診斷"),
                _column_or_blank(frame, "入院診斷"),
                _column_or_blank(frame, "次診斷"),
                _column_or_blank(frame, "出院診斷"),
            ),
            "diagnosis_text": "",
            "clinical_tnm": "",
            "pathologic_tnm": "",
            "final_stage": "",
            "case_category_code": "",
            "case_category_label": "",
            "doctor": "",
            "manager": "",
            "chemotherapy": "",
            "chemotherapy_date": "",
            "targeted_therapy": "",
            "targeted_therapy_date": "",
            "immunotherapy": "",
            "immunotherapy_date": "",
            "hormone_therapy": "",
            "hormone_therapy_date": "",
            "radiation_therapy": "",
            "radiation_therapy_date": "",
            "surgery": "",
            "surgery_date": "",
            "tace": "",
            "tace_date": "",
            "rfa": "",
            "rfa_date": "",
            "treatment_status": "",
            "report_date": _column_or_blank(frame, "住院日"),
            "location": "",
        }
    )
    standardized["age_at_diagnosis"] = _calculate_age_series(
        standardized["birth_date"], standardized["diagnosis_date"]
    )
    standardized["survival_days"] = _calculate_day_diff_series(
        standardized["diagnosis_date"],
        _first_non_blank_series(standardized["death_date"], standardized["last_followup_date"]),
    )
    return _reorder_columns(standardized, STANDARD_COLUMNS)


def _column_or_blank(frame: pd.DataFrame, column: str) -> pd.Series:
    for candidate in _column_candidates(column):
        if candidate in frame.columns:
            return frame[candidate].fillna("").astype(str).str.strip()
    return pd.Series([""] * len(frame), index=frame.index, dtype="object")


def _first_available_column(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    for column in columns:
        for candidate in _column_candidates(column):
            if candidate in frame.columns:
                return _column_or_blank(frame, candidate)
    return pd.Series([""] * len(frame), index=frame.index, dtype="object")


def _column_candidates(column: str) -> list[str]:
    candidates = [column]
    for candidate in COLUMN_ALIASES.get(column, []):
        if candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _first_non_blank_series(*series_list: pd.Series) -> pd.Series:
    if not series_list:
        return pd.Series(dtype="object")
    result = series_list[0].fillna("").astype(str).str.strip()
    for series in series_list[1:]:
        candidate = series.fillna("").astype(str).str.strip()
        result = result.where(result != "", candidate)
    return result


def _labelled(label: str, values: pd.Series) -> pd.Series:
    cleaned = values.fillna("").astype(str).str.strip()
    return cleaned.map(lambda value: f"{label}:{value}" if value else "")


def _filled_label(label: str, values: pd.Series) -> pd.Series:
    cleaned = values.fillna("").astype(str).str.strip()
    return cleaned.map(lambda value: label if value else "")


def _concat_text(parts: list[pd.Series]) -> pd.Series:
    if not parts:
        return pd.Series(dtype="object")

    combined = parts[0].astype(str)
    for part in parts[1:]:
        combined = combined.str.cat(part.astype(str), sep=" | ")

    return combined.map(
        lambda value: " | ".join(segment for segment in value.split(" | ") if segment)
    )


def _extract_case_category_code(values: pd.Series) -> pd.Series:
    return values.fillna("").astype(str).str.extract(r"^\s*(\d+)")[0].fillna("")


def _extract_case_category_label(values: pd.Series) -> pd.Series:
    cleaned = values.fillna("").astype(str).str.strip()
    labels = cleaned.str.extract(r"^\s*\d+[_-]?(.*)$")[0].fillna("")
    codes = _extract_case_category_code(values)
    fallback = codes.map(lambda code: f"Class {code}" if code else "")
    return labels.where(labels != "", fallback)


def _yes_if_any(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    result = pd.Series([""] * len(frame), index=frame.index, dtype="object")
    for column in columns:
        if column not in frame.columns:
            continue
        values = _column_or_blank(frame, column)
        result = result.where(values == "", "Y")
    return result


def _extract_icd10_series(values: pd.Series) -> pd.Series:
    return values.fillna("").astype(str).str.extract(r"([A-Z]\d{2}(?:\.\d{1,2})?)")[0].fillna("")


def _extract_icd10_from_cancer_type(values: pd.Series) -> pd.Series:
    return _extract_icd10_series(values)


def _extract_diagnosis_text_from_description(values: pd.Series) -> pd.Series:
    cleaned = values.fillna("").astype(str).str.strip()
    text = cleaned.str.replace(r"^[A-Z]\d{2}(?:\.\d{1,2})?\s*", "", regex=True).str.strip()
    return text.where(text != cleaned, text)


def _extract_text_from_cancer_type(values: pd.Series) -> pd.Series:
    cleaned = values.fillna("").astype(str).str.strip()
    return cleaned.str.replace(r"^[A-Z]{2,3}_", "", regex=True)


def _infer_cancer_from_report_name(report_name: str) -> tuple[str, str]:
    if "乳房" in report_name:
        return "BR_乳癌", "乳癌"
    if "膀胱" in report_name:
        return "UB_膀胱癌", "膀胱癌"
    if "肝癌" in report_name:
        return "HC_肝癌", "肝癌"
    if "腸癌" in report_name:
        return "CR_結腸直腸癌", "結腸直腸癌"
    return "", ""


def _classify_order_treatment(
    report_name: str,
    order_code: pd.Series,
    order_name: pd.Series,
    order_treatment_mapping: list[dict[str, str]] | None = None,
) -> dict[str, pd.Series]:
    report_series = pd.Series(report_name, index=order_code.index, dtype="object").fillna("")
    code_series = order_code.fillna("").astype(str)
    name_series = order_name.fillna("").astype(str)
    categories = {
        "chemotherapy": pd.Series(False, index=order_code.index, dtype="bool"),
        "radiation_therapy": pd.Series(False, index=order_code.index, dtype="bool"),
        "surgery": pd.Series(False, index=order_code.index, dtype="bool"),
        "tace": pd.Series(False, index=order_code.index, dtype="bool"),
        "rfa": pd.Series(False, index=order_code.index, dtype="bool"),
    }

    for rule in order_treatment_mapping or []:
        treatment_type = rule["treatment_type"]
        categories[treatment_type] = categories[treatment_type] | _order_rule_mask(
            order_code, order_name, rule
        )

    already_classified = (
        categories["chemotherapy"]
        | categories["radiation_therapy"]
        | categories["surgery"]
        | categories["tace"]
        | categories["rfa"]
    )

    chemotherapy = (
        report_series.str.contains("化療", na=False)
        | name_series.str.contains("化學藥物", na=False)
        | code_series.isin(["37038B", "37039B", "37040B", "37041B"])
    ) & ~already_classified
    rfa = (
        report_series.str.contains("RFA", na=False)
        | name_series.str.contains("無線頻率電熱療法|射頻燒灼|RFA", na=False)
        | code_series.isin(["37042C", "37043C", "37044C"])
    ) & ~already_classified
    tace = (
        report_series.str.contains("TAE|TACE", na=False)
        | name_series.str.contains("血管阻塞術|動脈栓塞", na=False)
        | code_series.isin(["33075BR", "33144BR"])
    ) & ~rfa & ~already_classified
    surgery = (
        report_series.str.contains("手術", na=False)
        | name_series.str.contains("切除術|摘除術|手術", na=False)
    ) & ~rfa & ~tace & ~chemotherapy & ~already_classified
    radiation = (
        report_series.str.contains("^RT|放腫|放射|電療", na=False)
        | name_series.str.contains("放射|電療|治療規劃", na=False)
    ) & ~tace & ~already_classified

    categories["chemotherapy"] = categories["chemotherapy"] | chemotherapy
    categories["radiation_therapy"] = categories["radiation_therapy"] | radiation
    categories["surgery"] = categories["surgery"] | surgery
    categories["tace"] = categories["tace"] | tace
    categories["rfa"] = categories["rfa"] | rfa

    return {
        "chemotherapy": categories["chemotherapy"].map({True: "Y", False: ""}),
        "radiation_therapy": categories["radiation_therapy"].map({True: "Y", False: ""}),
        "surgery": categories["surgery"].map({True: "Y", False: ""}),
        "tace": categories["tace"].map({True: "Y", False: ""}),
        "rfa": categories["rfa"].map({True: "Y", False: ""}),
    }


def _order_rule_mask(
    order_code: pd.Series, order_name: pd.Series, rule: dict[str, str]
) -> pd.Series:
    code_series = order_code.fillna("").astype(str).str.upper()
    name_series = order_name.fillna("").astype(str)
    mask = pd.Series(False, index=order_code.index, dtype="bool")
    order_code_exact = rule.get("order_code", "")
    order_code_prefix = rule.get("order_code_prefix", "")
    name_pattern = rule.get("name_pattern", "")
    if order_code_exact:
        mask = mask | (code_series == order_code_exact)
    if order_code_prefix:
        mask = mask | code_series.str.startswith(order_code_prefix)
    if name_pattern:
        mask = mask | name_series.str.contains(name_pattern, case=False, regex=True, na=False)
    return mask


def _map_order_rule_value(
    order_code: pd.Series,
    order_name: pd.Series,
    order_treatment_mapping: list[dict[str, str]] | None,
    target_column: str,
) -> pd.Series:
    result = pd.Series([""] * len(order_code), index=order_code.index, dtype="object")
    for rule in order_treatment_mapping or []:
        value = rule.get(target_column, "")
        if not value:
            continue
        mask = _order_rule_mask(order_code, order_name, rule) & (result == "")
        result = result.where(~mask, value)
    return result


def _classify_drug_treatment(
    order_code: pd.Series,
    order_name: pd.Series,
    drug_treatment_mapping: list[dict[str, str]] | None = None,
) -> dict[str, pd.Series]:
    name_series = order_name.fillna("").astype(str).str.lower()
    code_series = order_code.fillna("").astype(str).str.upper()
    categories = {
        "chemotherapy": pd.Series(False, index=order_code.index, dtype="bool"),
        "targeted_therapy": pd.Series(False, index=order_code.index, dtype="bool"),
        "immunotherapy": pd.Series(False, index=order_code.index, dtype="bool"),
        "hormone_therapy": pd.Series(False, index=order_code.index, dtype="bool"),
    }

    for rule in drug_treatment_mapping or []:
        treatment_type = rule["treatment_type"]
        mask = pd.Series(False, index=order_code.index, dtype="bool")
        order_code_exact = rule.get("order_code", "")
        order_code_prefix = rule.get("order_code_prefix", "")
        name_pattern = rule.get("name_pattern", "")
        if order_code_exact:
            mask = mask | (code_series == order_code_exact)
        if order_code_prefix:
            mask = mask | code_series.str.startswith(order_code_prefix)
        if name_pattern:
            mask = mask | name_series.str.contains(name_pattern, case=False, regex=True, na=False)
        categories[treatment_type] = categories[treatment_type] | mask

    already_classified = (
        categories["chemotherapy"]
        | categories["targeted_therapy"]
        | categories["immunotherapy"]
        | categories["hormone_therapy"]
    )

    hormone = name_series.str.contains(
        "letrozole|anastrozole|exemestane|tamoxifen|fulvestrant",
        na=False,
    ) & ~already_classified
    immunotherapy = name_series.str.contains(
        "pembrolizumab|nivolumab|atezolizumab|durvalumab|ipilimumab|tremelimumab",
        na=False,
    ) & ~already_classified
    targeted = name_series.str.contains(
        "bevacizumab|brentuximab|everolimus|alectinib|afatinib|zanubrutinib|"
        "cabozantinib|gefitinib|ruxolitinib|palbociclib|ibrutinib|ribociclib|"
        "lorlatinib|olaparib|erlotinib|sorafenib|entrectinib|lenalidomide|"
        "tepotinib|abemaciclib|dacomitinib|lapatinib|ramucirumab|cetuximab|"
        "trastuzumab|rituximab|pertuzumab|bortezomib",
        na=False,
    ) & ~hormone & ~immunotherapy & ~already_classified
    chemotherapy = (
        name_series.str.contains(
            "fluorouracil|pemetrexed|doxorubicin|vinblastine|etoposide|"
            "lurbinectedin|cyclophosphamide|methotrexate|chlorambucil|"
            "vinorelbine|capecitabine|azacitidine|bleomycin|carboplatin|"
            "oxaliplatin|dacarbazine|epirubicin|gemcitabine|ifosfamide|"
            "irinotecan|cisplatin|topotecan|vincristine|paclitaxel|docetaxel",
            na=False,
        )
        | code_series.str.startswith(("I5FU", "IALI", "IADR", "IVIN", "IVEP", "OMET", "OXEL"))
    ) & ~hormone & ~immunotherapy & ~targeted & ~already_classified

    categories["hormone_therapy"] = categories["hormone_therapy"] | hormone
    categories["immunotherapy"] = categories["immunotherapy"] | immunotherapy
    categories["targeted_therapy"] = categories["targeted_therapy"] | targeted
    categories["chemotherapy"] = categories["chemotherapy"] | chemotherapy

    return {
        "chemotherapy": categories["chemotherapy"].map({True: "Y", False: ""}),
        "targeted_therapy": categories["targeted_therapy"].map({True: "Y", False: ""}),
        "immunotherapy": categories["immunotherapy"].map({True: "Y", False: ""}),
        "hormone_therapy": categories["hormone_therapy"].map({True: "Y", False: ""}),
    }


def _normalize_tnm_series(values: pd.Series) -> pd.Series:
    cleaned = values.fillna("").astype(str).map(_normalize_tnm_text)
    return cleaned


def _normalize_tnm_text(value: str) -> str:
    text = str(value).strip().replace(" ", "")
    if not text:
        return ""
    if text.lower().startswith("p") and "Mx" in text:
        text = text.replace("Mx", "M0")
    return text


def _extract_clinical_tnm(values: pd.Series) -> pd.Series:
    normalized = _normalize_tnm_series(values)
    return normalized.map(lambda value: value if value.lower().startswith("c") else "")


def _extract_pathologic_tnm(values: pd.Series) -> pd.Series:
    normalized = _normalize_tnm_series(values)
    return normalized.map(
        lambda value: value if value.lower().startswith("p") or value.lower().startswith("yp") else ""
    )


def _primary_tnm_series(frame: pd.DataFrame) -> pd.Series:
    clinical = frame.get("clinical_tnm", pd.Series("", index=frame.index)).fillna("").astype(str).str.strip()
    pathologic = frame.get("pathologic_tnm", pd.Series("", index=frame.index)).fillna("").astype(str).str.strip()
    return pathologic.where(pathologic != "", clinical).map(_normalize_tnm_text)


def _extract_icd10_lookup(frame: pd.DataFrame) -> dict[str, tuple[str, str]]:
    if "癌別" not in frame.columns or "癌別說明" not in frame.columns:
        return {}

    cancer_type = _column_or_blank(frame, "癌別")
    icd10 = _extract_icd10_series(_column_or_blank(frame, "癌別說明"))
    diagnosis_text = _extract_text_from_cancer_type(cancer_type)

    lookup: dict[str, tuple[str, str]] = {}
    for code, cancer, text in zip(icd10, cancer_type, diagnosis_text):
        normalized = _normalize_icd10_code(code)
        if not normalized or not str(cancer).strip():
            continue
        lookup[normalized] = (str(cancer).strip(), str(text).strip())
        prefix = normalized.split(".")[0]
        lookup.setdefault(prefix, (str(cancer).strip(), str(text).strip()))
    return lookup


def _extract_patient_lookup(frame: pd.DataFrame) -> dict[str, dict[str, str]]:
    if "個案編號" not in frame.columns:
        return {}

    case_id = _column_or_blank(frame, "個案編號")
    medical_record_no = _first_available_column(frame, ["病歷號", "病歷編號", "病歷號碼"])
    patient_name = _first_available_column(frame, ["姓名", "病人姓名", "病患姓名"])
    birth_date = _first_available_column(frame, ["出生日期", "生日"])
    sex = _first_available_column(frame, ["性別"])
    diagnosis_date = _first_available_column(frame, ["最初診斷日期", "診斷日", "收案日期"])
    death_date = _first_available_column(frame, ["死亡日期"])
    last_followup_date = _first_available_column(frame, ["最近看診日", "最近追蹤日"])
    age_text = _first_available_column(frame, ["年齡"])
    cancer_type = _first_available_column(frame, ["癌別"])
    icd10_code = _first_non_blank_series(
        _extract_icd10_series(_first_available_column(frame, ["癌別說明"])),
        _extract_icd10_series(_first_available_column(frame, ["主診斷"])),
        _extract_icd10_series(_first_available_column(frame, ["入院診斷"])),
    )
    diagnosis_text = _first_non_blank_series(
        _extract_text_from_cancer_type(cancer_type),
        _first_available_column(frame, ["癌別說明"]),
    )

    lookup: dict[str, dict[str, str]] = {}
    for idx, raw_case_id in case_id.items():
        key = str(raw_case_id).strip()
        if not key:
            continue
        lookup[key] = {
            "medical_record_no": str(medical_record_no.loc[idx]).strip(),
            "patient_name": str(patient_name.loc[idx]).strip(),
            "sex": str(sex.loc[idx]).strip(),
            "birth_date": str(_normalize_date_value(birth_date.loc[idx])).strip(),
            "diagnosis_date": str(_normalize_date_value(diagnosis_date.loc[idx])).strip(),
            "death_date": str(_normalize_date_value(death_date.loc[idx])).strip(),
            "last_followup_date": str(_normalize_date_value(last_followup_date.loc[idx])).strip(),
            "age_at_diagnosis": str(age_text.loc[idx]).strip(),
            "cancer_type": str(cancer_type.loc[idx]).strip(),
            "icd10_code": str(icd10_code.loc[idx]).strip(),
            "diagnosis_text": str(diagnosis_text.loc[idx]).strip(),
        }
    return lookup


def _merge_patient_lookup(
    base_lookup: dict[str, dict[str, str]], new_lookup: dict[str, dict[str, str]]
) -> dict[str, dict[str, str]]:
    merged = {key: value.copy() for key, value in base_lookup.items()}
    for key, incoming in new_lookup.items():
        current = merged.get(key, {}).copy()
        for field, value in incoming.items():
            if str(value).strip():
                current[field] = value
            else:
                current.setdefault(field, value)
        merged[key] = current
    return merged


def _enrich_from_icd10_lookup(
    frame: pd.DataFrame, lookup: dict[str, tuple[str, str]]
) -> pd.DataFrame:
    enriched = frame.copy()
    if "icd10_code" not in enriched.columns:
        return enriched

    normalized_codes = enriched["icd10_code"].fillna("").astype(str).map(_normalize_icd10_code)
    mapped = normalized_codes.map(lambda code: lookup.get(code) or lookup.get(code.split(".")[0], ("", "")))

    mapped_cancer = mapped.map(lambda item: item[0] if item else "")
    mapped_text = mapped.map(lambda item: item[1] if item else "")

    if "cancer_type" in enriched.columns:
        current = enriched["cancer_type"].fillna("").astype(str).str.strip()
        enriched["cancer_type"] = current.where(current != "", mapped_cancer)
    else:
        enriched["cancer_type"] = mapped_cancer

    if "diagnosis_text" in enriched.columns:
        current = enriched["diagnosis_text"].fillna("").astype(str).str.strip()
        enriched["diagnosis_text"] = current.where(current != "", mapped_text)
    else:
        enriched["diagnosis_text"] = mapped_text

    return enriched


def _apply_manual_icd10_mapping(
    frame: pd.DataFrame, mapping: dict[str, tuple[str, str]]
) -> pd.DataFrame:
    if not mapping:
        return frame
    return _enrich_from_icd10_lookup(frame, mapping)


def _normalize_icd10_code(code: str) -> str:
    if not code:
        return ""
    match = re.search(r"([A-Z]\d{2}(?:\.\d{1,2})?)", str(code).upper())
    return match.group(1) if match else ""


def _enrich_from_patient_lookup(
    frame: pd.DataFrame, lookup: dict[str, dict[str, str]]
) -> pd.DataFrame:
    enriched = frame.copy()
    if "case_id" not in enriched.columns or not lookup:
        return enriched

    mrn_index: dict[str, str] = {}
    name_birth_index: dict[str, str] = {}
    unique_name_index: dict[str, str | None] = {}
    for case_id, payload in lookup.items():
        mrn = str(payload.get("medical_record_no", "")).strip()
        name = str(payload.get("patient_name", "")).strip()
        birth = str(payload.get("birth_date", "")).strip()
        if mrn:
            mrn_index.setdefault(mrn, case_id)
        if name and birth:
            name_birth_index.setdefault(f"{name}|{birth}", case_id)
        if name:
            if name in unique_name_index and unique_name_index[name] != case_id:
                unique_name_index[name] = None
            else:
                unique_name_index.setdefault(name, case_id)

    resolved_keys: list[str] = []
    current_case_ids = enriched["case_id"].fillna("").astype(str).str.strip()
    current_mrns = enriched.get("medical_record_no", pd.Series("", index=enriched.index)).fillna("").astype(str).str.strip()
    current_names = enriched.get("patient_name", pd.Series("", index=enriched.index)).fillna("").astype(str).str.strip()
    current_births = enriched.get("birth_date", pd.Series("", index=enriched.index)).fillna("").astype(str).str.strip()

    for idx in enriched.index:
        case_id = current_case_ids.loc[idx]
        if case_id and case_id in lookup:
            resolved_keys.append(case_id)
            continue
        mrn = current_mrns.loc[idx]
        if mrn and mrn in mrn_index:
            resolved_keys.append(mrn_index[mrn])
            continue
        name = current_names.loc[idx]
        birth = current_births.loc[idx]
        if name and birth and f"{name}|{birth}" in name_birth_index:
            resolved_keys.append(name_birth_index[f"{name}|{birth}"])
            continue
        if name and unique_name_index.get(name):
            resolved_keys.append(str(unique_name_index[name]))
            continue
        resolved_keys.append("")

    keys = pd.Series(resolved_keys, index=enriched.index, dtype="object")

    existing_case_ids = enriched["case_id"].fillna("").astype(str).str.strip()
    enriched["case_id"] = existing_case_ids.where(existing_case_ids != "", keys)

    for target_column in [
        "medical_record_no",
        "patient_name",
        "sex",
        "birth_date",
        "diagnosis_date",
        "death_date",
        "last_followup_date",
        "age_at_diagnosis",
        "cancer_type",
        "icd10_code",
        "diagnosis_text",
    ]:
        mapped = keys.map(lambda key: lookup.get(key, {}).get(target_column, ""))
        if target_column in enriched.columns:
            current = enriched[target_column].fillna("").astype(str).str.strip()
            enriched[target_column] = current.where(current != "", mapped)
        else:
            enriched[target_column] = mapped

    if "age_at_diagnosis" in enriched.columns:
        current_age = enriched["age_at_diagnosis"].fillna("").astype(str).str.strip()
        calculated_age = _calculate_age_series(
            enriched["birth_date"].fillna("").astype(str),
            enriched["diagnosis_date"].fillna("").astype(str),
        )
        enriched["age_at_diagnosis"] = current_age.where(current_age != "", calculated_age)

    if "survival_days" in enriched.columns:
        recalculated = _calculate_day_diff_series(
            enriched["diagnosis_date"].fillna("").astype(str),
            _first_non_blank_series(
                enriched["death_date"].fillna("").astype(str),
                enriched["last_followup_date"].fillna("").astype(str),
            ),
        )
        current = enriched["survival_days"].fillna("").astype(str).str.strip()
        enriched["survival_days"] = current.where(current != "", recalculated)

    return enriched


def _apply_stage_mapping(
    frame: pd.DataFrame, stage_mapping: dict[tuple[str, str], str]
) -> pd.DataFrame:
    enriched = frame.copy()
    if "final_stage_source" not in enriched.columns:
        enriched["final_stage_source"] = ""

    reported_stage = enriched.get("final_stage", pd.Series("", index=enriched.index)).fillna("").astype(str).str.strip()
    enriched["final_stage"] = reported_stage
    enriched["final_stage_source"] = reported_stage.map(lambda value: "reported" if value else "")

    if not stage_mapping:
        return enriched

    normalized_tnm = _primary_tnm_series(enriched)
    cancer_type = enriched.get("cancer_type", pd.Series("", index=enriched.index)).fillna("").astype(str).str.strip()

    inferred_stage = pd.Series("", index=enriched.index, dtype="object")
    for idx in enriched.index:
        key = (cancer_type.loc[idx], normalized_tnm.loc[idx])
        inferred_stage.loc[idx] = stage_mapping.get(key, "")

    needs_fill = (enriched["final_stage"].fillna("").astype(str).str.strip() == "") & (inferred_stage != "")
    enriched.loc[needs_fill, "final_stage"] = inferred_stage.loc[needs_fill]
    enriched.loc[needs_fill, "final_stage_source"] = "tnm_mapping"
    return enriched


def _deduplicate_standardized(frame: pd.DataFrame) -> pd.DataFrame:
    enriched = frame.copy()
    enriched["record_key"] = _build_record_key_series(enriched)
    enriched["_quality_score"] = _calculate_patient_row_quality(enriched)
    enriched = enriched.sort_values(
        by=["record_key", "_quality_score", "report_period_end", "report_date", "source_file"],
        ascending=[True, False, False, False, True],
        na_position="last",
    )
    enriched = enriched.drop_duplicates(subset=["record_key"], keep="first").reset_index(drop=True)
    return enriched.drop(columns=["_quality_score"], errors="ignore")


def _build_record_key_series(frame: pd.DataFrame) -> pd.Series:
    keys = []
    for idx in frame.index:
        report_name = _safe_cell(frame, idx, "report_name")
        if _safe_cell(frame, idx, "order_code"):
            key_parts = [
                report_name,
                _safe_cell(frame, idx, "medical_record_no"),
                _safe_cell(frame, idx, "order_code"),
                _safe_cell(frame, idx, "report_date"),
                _safe_cell(frame, idx, "location"),
            ]
        elif "化療流程時間" in report_name:
            key_parts = [report_name, _safe_cell(frame, idx, "order_id"), _safe_cell(frame, idx, "report_date")]
        elif "化療名單" in report_name:
            key_parts = [report_name, _safe_cell(frame, idx, "medical_record_no"), _safe_cell(frame, idx, "report_date"), _safe_cell(frame, idx, "treatment_status"), _safe_cell(frame, idx, "location")]
        elif "住院人次人日" in report_name:
            key_parts = [report_name, _safe_cell(frame, idx, "case_id"), _safe_cell(frame, idx, "report_date"), _safe_cell(frame, idx, "icd10_code")]
        else:
            key_parts = [
                report_name,
                _safe_cell(frame, idx, "case_id"),
                _safe_cell(frame, idx, "medical_record_no"),
                _safe_cell(frame, idx, "diagnosis_date"),
                _safe_cell(frame, idx, "clinical_tnm"),
                _safe_cell(frame, idx, "pathologic_tnm"),
                _safe_cell(frame, idx, "final_stage"),
            ]
        normalized = [part for part in key_parts if part]
        keys.append(" | ".join(normalized))
    return pd.Series(keys, index=frame.index, dtype="object")


def _safe_cell(frame: pd.DataFrame, idx: object, column: str) -> str:
    if column not in frame.columns:
        return ""
    return str(frame.at[idx, column]).strip() if pd.notna(frame.at[idx, column]) else ""


def _build_unmatched_icd10_report(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["icd10_code", "cancer_type", "diagnosis_text", "count", "report_names", "notes"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    working = frame.copy()
    working["icd10_code_norm"] = working.get("icd10_code", pd.Series("", index=working.index)).fillna("").astype(str).map(_normalize_icd10_code)
    working["diagnosis_text"] = working.get("diagnosis_text", pd.Series("", index=working.index)).fillna("").astype(str).str.strip()
    unmatched = working[
        (working["icd10_code_norm"] != "")
        & (working["icd10_code_norm"].str.startswith("C"))
        & (working.get("cancer_type", pd.Series("", index=working.index)).fillna("").astype(str).str.strip() == "")
    ]
    if unmatched.empty:
        return pd.DataFrame(columns=columns)
    summary = (
        unmatched.groupby("icd10_code_norm", dropna=False)
        .agg(
            diagnosis_text=("diagnosis_text", lambda values: next((str(value).strip() for value in values if str(value).strip()), "")),
            count=("icd10_code_norm", "size"),
            report_names=("report_name", lambda values: " | ".join(sorted(set(v for v in values if str(v).strip())))),
        )
        .reset_index()
        .rename(columns={"icd10_code_norm": "icd10_code"})
        .sort_values(by=["count", "icd10_code"], ascending=[False, True])
        .reset_index(drop=True)
    )
    summary.insert(1, "cancer_type", "")
    summary["notes"] = summary["icd10_code"].map(_icd10_review_note)
    return summary[columns]


def _icd10_review_note(icd10_code: str) -> str:
    normalized = _normalize_icd10_code(icd10_code)
    if normalized.startswith(("C77", "C78", "C79")):
        return "secondary_or_metastatic_code_needs_primary_site_review"
    return ""


def _build_stage_review_report(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "cancer_type",
        "clinical_tnm",
        "pathologic_tnm",
        "primary_tnm",
        "final_stage",
        "final_stage_source",
        "review_reason",
        "count",
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    working = frame.copy()
    clinical = working.get("clinical_tnm", pd.Series("", index=working.index)).fillna("").astype(str).str.strip()
    pathologic = working.get("pathologic_tnm", pd.Series("", index=working.index)).fillna("").astype(str).str.strip()
    has_tnm = (clinical != "") | (pathologic != "")
    review = working.loc[has_tnm, ["cancer_type", "clinical_tnm", "pathologic_tnm", "final_stage", "final_stage_source"]].copy()
    if review.empty:
        return pd.DataFrame(columns=columns)
    review["primary_tnm"] = _primary_tnm_series(review)
    review["review_reason"] = review.apply(_stage_review_reason, axis=1)
    summary = (
        review.groupby(
            [
                "cancer_type",
                "clinical_tnm",
                "pathologic_tnm",
                "primary_tnm",
                "final_stage",
                "final_stage_source",
                "review_reason",
            ],
            dropna=False,
        )
        .size()
        .reset_index(name="count")
        .sort_values(by=["review_reason", "cancer_type", "clinical_tnm", "pathologic_tnm", "count"], ascending=[True, True, True, True, False])
        .reset_index(drop=True)
    )
    return summary[columns]


def _stage_review_reason(row: pd.Series) -> str:
    final_stage = str(row.get("final_stage", "")).strip()
    final_stage_source = str(row.get("final_stage_source", "")).strip()
    primary_tnm = _normalize_tnm_text(str(row.get("primary_tnm", "")).strip())
    primary_tnm_upper = primary_tnm.upper()

    if final_stage:
        if final_stage_source == "tnm_mapping":
            return "mapped_from_tnm"
        return "reported_stage"
    if primary_tnm_upper in {"", "CTNM", "PTNM", "TNM"}:
        return "missing_final_stage_with_non_specific_tnm"
    if "X" in primary_tnm_upper:
        return "missing_final_stage_with_unknown_tnm"
    return "missing_final_stage"


def _build_unmapped_drug_orders_report(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "order_code",
        "order_name",
        "count",
        "report_names",
        "sample_diagnosis_texts",
        "treatment_type",
        "name_pattern",
        "order_code_prefix",
        "notes",
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    unmapped = _unmapped_order_rows(frame)
    if unmapped.empty:
        return pd.DataFrame(columns=columns)
    drug_rows = unmapped[
        unmapped.get("report_name", pd.Series("", index=unmapped.index)).fillna("").astype(str).str.contains("指引藥物", na=False)
    ].copy()
    if drug_rows.empty:
        return pd.DataFrame(columns=columns)
    return _summarize_unmapped_orders(drug_rows, include_cancer_columns=False)


def _build_unmapped_treatment_orders_report(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "order_code",
        "order_name",
        "count",
        "report_names",
        "sample_diagnosis_texts",
        "treatment_type",
        "name_pattern",
        "order_code_prefix",
        "cancer_type",
        "diagnosis_text",
        "notes",
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    unmapped = _unmapped_order_rows(frame)
    if unmapped.empty:
        return pd.DataFrame(columns=columns)
    treatment_rows = unmapped[
        ~unmapped.get("report_name", pd.Series("", index=unmapped.index)).fillna("").astype(str).str.contains("指引藥物", na=False)
    ].copy()
    if treatment_rows.empty:
        return pd.DataFrame(columns=columns)
    return _summarize_unmapped_orders(treatment_rows, include_cancer_columns=True)


def _unmapped_order_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if "order_code" not in frame.columns and "order_name" not in frame.columns:
        return pd.DataFrame()
    working = frame.copy()
    order_code = working.get("order_code", pd.Series("", index=working.index)).fillna("").astype(str).str.strip()
    order_name = working.get("order_name", pd.Series("", index=working.index)).fillna("").astype(str).str.strip()
    has_order = (order_code != "") | (order_name != "")
    treatment_columns = [
        "chemotherapy",
        "targeted_therapy",
        "immunotherapy",
        "hormone_therapy",
        "radiation_therapy",
        "surgery",
        "tace",
        "rfa",
    ]
    has_treatment = pd.Series(False, index=working.index, dtype="bool")
    for column in treatment_columns:
        if column not in working.columns:
            continue
        has_treatment = has_treatment | (
            working[column].fillna("").astype(str).str.strip() == "Y"
        )
    return working.loc[has_order & ~has_treatment].copy()


def _summarize_unmapped_orders(
    frame: pd.DataFrame, *, include_cancer_columns: bool
) -> pd.DataFrame:
    working = frame.copy()
    working["order_code_norm"] = working.get("order_code", pd.Series("", index=working.index)).fillna("").astype(str).str.strip()
    working["order_name_norm"] = working.get("order_name", pd.Series("", index=working.index)).fillna("").astype(str).str.strip()
    summary = (
        working.groupby(["order_code_norm", "order_name_norm"], dropna=False)
        .agg(
            count=("order_code_norm", "size"),
            report_names=("report_name", lambda values: " | ".join(sorted(set(v for v in values if str(v).strip())))),
            sample_diagnosis_texts=("diagnosis_text", lambda values: " | ".join(list(dict.fromkeys(str(v).strip() for v in values if str(v).strip()))[:5])),
        )
        .reset_index()
        .rename(columns={"order_code_norm": "order_code", "order_name_norm": "order_name"})
        .sort_values(by=["count", "order_code", "order_name"], ascending=[False, True, True])
        .reset_index(drop=True)
    )
    summary["treatment_type"] = ""
    summary["name_pattern"] = ""
    summary["order_code_prefix"] = ""
    if include_cancer_columns:
        summary["cancer_type"] = ""
        summary["diagnosis_text"] = ""
    summary["notes"] = ""
    ordered = [
        "order_code",
        "order_name",
        "count",
        "report_names",
        "sample_diagnosis_texts",
        "treatment_type",
        "name_pattern",
        "order_code_prefix",
    ]
    if include_cancer_columns:
        ordered.extend(["cancer_type", "diagnosis_text"])
    ordered.append("notes")
    return summary[ordered]


def _add_record_keys(frame: pd.DataFrame) -> pd.DataFrame:
    enriched = frame.copy()
    patient_key = _build_patient_key_series(enriched)
    enriched.insert(0, "patient_key", patient_key)
    return enriched


def _build_patient_master(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=PATIENT_MASTER_COLUMNS)

    working = frame.copy()
    working["patient_key"] = _build_patient_key_series(working)
    working["_quality_score"] = _calculate_patient_row_quality(working)
    working = working.sort_values(
        by=["patient_key", "_quality_score", "last_followup_date", "report_date"],
        ascending=[True, False, False, False],
        na_position="last",
    )

    groups: list[dict[str, str]] = []
    for patient_key, group in working.groupby("patient_key", dropna=False, sort=False):
        if not str(patient_key).strip():
            continue
        groups.append(_merge_patient_group(patient_key, group))

    patient_master = pd.DataFrame(groups)
    if patient_master.empty:
        return pd.DataFrame(columns=PATIENT_MASTER_COLUMNS)
    return _reorder_columns(patient_master, PATIENT_MASTER_COLUMNS)


def _build_patient_list(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=PATIENT_LIST_COLUMNS)
    patient_list = frame.copy()
    return _reorder_columns(patient_list, PATIENT_LIST_COLUMNS)


def _build_patient_list_zh(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=list(PATIENT_LIST_ZH_HEADERS.values()))
    renamed = frame.rename(columns=PATIENT_LIST_ZH_HEADERS)
    ordered_columns = [
        PATIENT_LIST_ZH_HEADERS[column]
        for column in PATIENT_LIST_COLUMNS
        if column in PATIENT_LIST_ZH_HEADERS
    ]
    return renamed[ordered_columns]


def _build_summary_zh(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["分類", "項目", "人數"])

    working = frame.copy()
    if "cancer_type" in working.columns:
        working["cancer_type_display"] = working["cancer_type"].fillna("").astype(str).map(
            _format_cancer_type_display
        )
    if "age_at_diagnosis" in working.columns:
        working["age_group"] = working["age_at_diagnosis"].fillna("").astype(str).map(
            _age_group_label
        )

    sections: list[pd.DataFrame] = []

    sections.append(_build_count_section(working, "癌別", "cancer_type_display"))
    sections.append(_build_count_section(working, "最終期別", "final_stage"))
    sections.append(_build_count_section(working, "個案分類", "case_category_label"))
    sections.append(_build_count_section(working, "性別", "sex"))
    sections.append(_build_count_section(working, "年齡區間", "age_group"))
    sections.append(_build_yesno_section(working, "治療別", {
        "化學治療": "chemotherapy",
        "標靶治療": "targeted_therapy",
        "免疫治療": "immunotherapy",
        "抗荷爾蒙治療": "hormone_therapy",
        "放射治療": "radiation_therapy",
        "手術": "surgery",
        "TACE": "tace",
        "RFA": "rfa",
    }))

    summary = pd.concat(sections, ignore_index=True)
    return summary


def _build_summary_trend_zh(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "diagnosis_date" not in frame.columns:
        return pd.DataFrame(columns=["月份", "分類", "項目", "人數"])

    working = frame.copy()
    diagnosis_dates = pd.to_datetime(working["diagnosis_date"].replace("", pd.NA), errors="coerce")
    working["月份"] = diagnosis_dates.dt.strftime("%Y-%m").fillna("")
    working = working[working["月份"] != ""].copy()
    if working.empty:
        return pd.DataFrame(columns=["月份", "分類", "項目", "人數"])

    working["癌別顯示"] = working["cancer_type"].fillna("").astype(str).map(_format_cancer_type_display)

    monthly_total = (
        working.groupby("月份")
        .size()
        .reset_index(name="人數")
        .assign(分類="診斷月份", 項目="總人數")
    )

    monthly_cancer = (
        working[working["癌別顯示"] != ""]
        .groupby(["月份", "癌別顯示"])
        .size()
        .reset_index(name="人數")
        .rename(columns={"癌別顯示": "項目"})
        .assign(分類="診斷月份癌別")
    )

    treatment_rows: list[dict[str, object]] = []
    treatment_columns = {
        "化學治療": "chemotherapy",
        "標靶治療": "targeted_therapy",
        "免疫治療": "immunotherapy",
        "抗荷爾蒙治療": "hormone_therapy",
        "放射治療": "radiation_therapy",
        "手術": "surgery",
        "TACE": "tace",
        "RFA": "rfa",
    }
    for month, month_group in working.groupby("月份", sort=True):
        for label, column in treatment_columns.items():
            if column not in month_group.columns:
                continue
            count = (month_group[column].fillna("").astype(str).str.strip() == "Y").sum()
            if count == 0:
                continue
            treatment_rows.append(
                {"月份": month, "分類": "診斷月份治療別", "項目": label, "人數": int(count)}
            )

    monthly_treatment = pd.DataFrame(
        treatment_rows, columns=["月份", "分類", "項目", "人數"]
    )

    result = pd.concat([monthly_total, monthly_cancer, monthly_treatment], ignore_index=True)
    return result[["月份", "分類", "項目", "人數"]].sort_values(
        by=["月份", "分類", "人數", "項目"], ascending=[True, True, False, True]
    ).reset_index(drop=True)


def _build_count_section(frame: pd.DataFrame, section_name: str, column: str) -> pd.DataFrame:
    if column not in frame.columns:
        return pd.DataFrame(columns=["分類", "項目", "人數"])
    working = frame[column].fillna("").astype(str).str.strip()
    working = working[working != ""]
    if working.empty:
        return pd.DataFrame(columns=["分類", "項目", "人數"])
    counts = (
        working.value_counts()
        .rename_axis("項目")
        .reset_index(name="人數")
        .sort_values(by=["人數", "項目"], ascending=[False, True])
        .reset_index(drop=True)
    )
    counts.insert(0, "分類", section_name)
    return counts


def _build_yesno_section(
    frame: pd.DataFrame, section_name: str, column_map: dict[str, str]
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for label, column in column_map.items():
        if column not in frame.columns:
            continue
        count = (frame[column].fillna("").astype(str).str.strip() == "Y").sum()
        rows.append({"分類": section_name, "項目": label, "人數": int(count)})
    return pd.DataFrame(rows)


def _format_cancer_type_display(value: str) -> str:
    text = str(value).strip()
    if not text:
        return ""
    if text in SPECIAL_CANCER_TYPE_LABELS:
        return f"{SPECIAL_CANCER_TYPE_LABELS[text]} ({text})"
    if "_" in text:
        code, label = text.split("_", 1)
        return f"{label} ({code})"
    return text


def _age_group_label(value: str) -> str:
    text = str(value).strip()
    if not text:
        return ""
    try:
        age = int(float(text))
    except ValueError:
        return ""
    if age < 20:
        return "0-19歲"
    if age < 40:
        return "20-39歲"
    if age < 50:
        return "40-49歲"
    if age < 60:
        return "50-59歲"
    if age < 70:
        return "60-69歲"
    if age < 80:
        return "70-79歲"
    return "80歲以上"


def _build_patient_key_series(frame: pd.DataFrame) -> pd.Series:
    keys = []
    for idx in frame.index:
        keys.append(_build_patient_key_for_row(frame, idx))
    return pd.Series(keys, index=frame.index, dtype="object")


def _build_patient_key_for_row(frame: pd.DataFrame, idx: object) -> str:
    report_name = _safe_cell(frame, idx, "report_name")
    case_id = _safe_cell(frame, idx, "case_id")
    mrn = _safe_cell(frame, idx, "medical_record_no")
    patient_name = _safe_cell(frame, idx, "patient_name")
    birth_date = _safe_cell(frame, idx, "birth_date")
    order_code = _safe_cell(frame, idx, "order_code")

    # Cancer case reports use 個案編號 as the most stable patient-level key.
    if any(tag in report_name for tag in ("D1.1", "D1.2", "D1.4")) and case_id:
        return f"CASE:{case_id}"

    # Order-detail rows may have case_id backfilled from the cancer-case lookup.
    if order_code and case_id:
        return f"CASE:{case_id}"

    # Event-style reports often use case_id for encounter/order numbers, so prefer MRN.
    if mrn:
        return f"MRN:{mrn}"

    if case_id:
        return f"CASE:{case_id}"
    if patient_name and birth_date:
        return f"NAME_BIRTH:{patient_name}|{birth_date}"
    if patient_name:
        return f"NAME:{patient_name}"
    return ""


def _calculate_patient_row_quality(frame: pd.DataFrame) -> pd.Series:
    score = pd.Series(0, index=frame.index, dtype="int64")
    weighted_columns = {
        "patient_name": 5,
        "medical_record_no": 5,
        "case_id": 5,
        "birth_date": 4,
        "diagnosis_date": 3,
        "last_followup_date": 3,
        "cancer_type": 2,
        "icd10_code": 2,
        "clinical_tnm": 2,
        "pathologic_tnm": 2,
        "final_stage": 2,
    }
    for column, weight in weighted_columns.items():
        if column not in frame.columns:
            continue
        present = frame[column].fillna("").astype(str).str.strip() != ""
        score = score + present.astype("int64") * weight
    return score


def _merge_patient_group(patient_key: str, group: pd.DataFrame) -> dict[str, str]:
    merged: dict[str, str] = {"patient_key": patient_key}
    for column in PATIENT_MASTER_COLUMNS:
        if column == "patient_key":
            continue
        if column not in group.columns:
            merged[column] = ""
            continue
        values = group[column].fillna("").astype(str).str.strip()
        non_blank = values[values != ""]
        if non_blank.empty:
            merged[column] = ""
            continue

        if column in {"diagnosis_date", "case_date", "birth_date", "report_period_start"}:
            merged[column] = non_blank.min()
        elif column in {"death_date", "last_followup_date", "report_date", "report_period_end"}:
            merged[column] = non_blank.max()
        elif column == "survival_days":
            numeric = pd.to_numeric(non_blank, errors="coerce").dropna()
            merged[column] = str(int(numeric.max())) if not numeric.empty else non_blank.iloc[0]
        elif column in {
            "chemotherapy",
            "targeted_therapy",
            "immunotherapy",
            "hormone_therapy",
            "radiation_therapy",
            "surgery",
            "tace",
            "rfa",
        }:
            merged[column] = "Y" if (non_blank == "Y").any() else ""
        else:
            merged[column] = non_blank.iloc[0]

    if not merged.get("age_at_diagnosis") and merged.get("birth_date") and merged.get("diagnosis_date"):
        age_series = _calculate_age_series(
            pd.Series([merged["birth_date"]]), pd.Series([merged["diagnosis_date"]])
        )
        merged["age_at_diagnosis"] = age_series.iloc[0]

    if (
        (not merged.get("survival_days"))
        and merged.get("diagnosis_date")
        and (merged.get("death_date") or merged.get("last_followup_date"))
    ):
        diff_series = _calculate_day_diff_series(
            pd.Series([merged["diagnosis_date"]]),
            pd.Series([merged["death_date"] or merged["last_followup_date"]]),
        )
        merged["survival_days"] = diff_series.iloc[0]

    return merged


def _calculate_age_series(birth_dates: pd.Series, diagnosis_dates: pd.Series) -> pd.Series:
    birth = pd.to_datetime(birth_dates.replace("", pd.NA), errors="coerce")
    diagnosis = pd.to_datetime(diagnosis_dates.replace("", pd.NA), errors="coerce")
    years = diagnosis.dt.year - birth.dt.year
    had_birthday = (
        (diagnosis.dt.month > birth.dt.month)
        | ((diagnosis.dt.month == birth.dt.month) & (diagnosis.dt.day >= birth.dt.day))
    )
    age = years - (~had_birthday).astype("Int64")
    return age.astype("string").fillna("")


def _calculate_day_diff_series(start_dates: pd.Series, end_dates: pd.Series) -> pd.Series:
    start = pd.to_datetime(start_dates.replace("", pd.NA), errors="coerce")
    end = pd.to_datetime(end_dates.replace("", pd.NA), errors="coerce")
    days = (end.dt.normalize() - start.dt.normalize()).dt.days.astype("Int64")
    return days.astype("string").fillna("")


def _reorder_columns(frame: pd.DataFrame, preferred_order: list[str]) -> pd.DataFrame:
    existing_first = [column for column in preferred_order if column in frame.columns]
    remaining = [column for column in frame.columns if column not in existing_first]
    return frame[existing_first + remaining]
