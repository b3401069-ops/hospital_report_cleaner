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


def run_cleaning(
    paths: ProjectPaths,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    files = _collect_source_files(paths.raw_dir)
    if not files:
        raise FileNotFoundError("No source reports were found in raw/.")

    column_mapping = _load_column_mapping(paths.column_mapping_file)
    value_mapping = _load_value_mapping(paths.value_mapping_file)
    tnm_stage_mapping = _load_tnm_stage_mapping(paths.tnm_stage_mapping_file)
    manual_icd10_mapping = _load_manual_icd10_mapping(paths.icd10_mapping_file)

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
                frame, source_file.stem, source_file.name, period_start, period_end
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

    return (
        combined,
        standardized,
        patient_master,
        patient_list,
        unmatched_icd10,
        stage_review,
        processed_files,
    )


def export_cleaned_report(
    cleaned_frame: pd.DataFrame,
    standardized_frame: pd.DataFrame,
    patient_master_frame: pd.DataFrame,
    patient_list_frame: pd.DataFrame,
    unmatched_icd10_frame: pd.DataFrame,
    stage_review_frame: pd.DataFrame,
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
    mapping_frame = pd.read_csv(mapping_file, dtype=str).fillna("")
    return {
        row["source_column"].strip(): row["target_column"].strip()
        for _, row in mapping_frame.iterrows()
        if row["source_column"].strip() and row["target_column"].strip()
    }


def _load_value_mapping(mapping_file: Path) -> dict[str, dict[str, str]]:
    if not mapping_file.exists():
        return {}
    mapping_frame = pd.read_csv(mapping_file, dtype=str).fillna("")
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
    mapping_frame = pd.read_csv(mapping_file, dtype=str).fillna("")
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
    mapping_frame = pd.read_csv(mapping_file, dtype=str).fillna("")
    mapping: dict[str, tuple[str, str]] = {}
    for _, row in mapping_frame.iterrows():
        icd10_code = _normalize_icd10_code(row.get("icd10_code", ""))
        cancer_type = row.get("cancer_type", "").strip()
        diagnosis_text = row.get("diagnosis_text", "").strip()
        if icd10_code and (cancer_type or diagnosis_text):
            mapping[icd10_code] = (cancer_type, diagnosis_text)
            mapping.setdefault(icd10_code.split(".")[0], (cancer_type, diagnosis_text))
    return mapping


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
    if len(digits) == 7:
        digits = str(int(digits[:3]) + 1911) + digits[3:]
    if len(digits) == 8:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"
    if len(digits) == 12:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]} {digits[8:10]}:{digits[10:12]}"
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
) -> pd.DataFrame:
    if "化療流程時間" in report_name:
        return _standardize_chemo_timeline(frame, report_name, source_file, period_start, period_end)
    if "化療名單" in report_name:
        return _standardize_chemo_list(frame, report_name, source_file, period_start, period_end)
    if "TNM" in report_name:
        return _standardize_tnm(frame, report_name, source_file, period_start, period_end)
    if "治療計畫書" in report_name:
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
            "icd10_code": _extract_icd10_from_cancer_type(_column_or_blank(frame, "癌別")),
            "diagnosis_text": _extract_text_from_cancer_type(_column_or_blank(frame, "癌別")),
            "clinical_tnm": _extract_clinical_tnm(_column_or_blank(frame, "組合")),
            "pathologic_tnm": _extract_pathologic_tnm(_column_or_blank(frame, "組合")),
            "final_stage": _column_or_blank(frame, "期別"),
            "case_category_code": _extract_case_category_code(_column_or_blank(frame, "個案分類")),
            "case_category_label": _extract_case_category_label(_column_or_blank(frame, "個案分類")),
            "doctor": "",
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
        _column_or_blank(frame, "最初診斷日期"), _column_or_blank(frame, "收案日期")
    )
    case_date = _first_non_blank_series(
        _column_or_blank(frame, "收案日期"), _column_or_blank(frame, "最初診斷日期")
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
            "diagnosis_text": _extract_text_from_cancer_type(_column_or_blank(frame, "癌別")),
            "clinical_tnm": "",
            "pathologic_tnm": "",
            "final_stage": "",
            "case_category_code": _extract_case_category_code(_column_or_blank(frame, "個案分類")),
            "case_category_label": _extract_case_category_label(_column_or_blank(frame, "個案分類")),
            "doctor": "",
            "manager": "",
            "chemotherapy": _yes_if_any(frame, ["化學治療填寫日期1", "化學治療填寫日期2", "口服化療日期"]),
            "chemotherapy_date": _first_non_blank_series(
                _column_or_blank(frame, "化學治療填寫日期1"),
                _column_or_blank(frame, "化學治療填寫日期2"),
                _column_or_blank(frame, "口服化療日期"),
            ),
            "targeted_therapy": _yes_if_any(frame, ["標靶治療日期"]),
            "targeted_therapy_date": _column_or_blank(frame, "標靶治療日期"),
            "immunotherapy": _yes_if_any(frame, ["免疫治療填寫日期"]),
            "immunotherapy_date": _column_or_blank(frame, "免疫治療填寫日期"),
            "hormone_therapy": _yes_if_any(frame, ["荷爾蒙治療日期"]),
            "hormone_therapy_date": _column_or_blank(frame, "荷爾蒙治療日期"),
            "radiation_therapy": _yes_if_any(frame, ["放射線治療填寫日期", "CCRT填寫日期"]),
            "radiation_therapy_date": _first_non_blank_series(
                _column_or_blank(frame, "放射線治療填寫日期"),
                _column_or_blank(frame, "CCRT填寫日期"),
            ),
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
    if column in frame.columns:
        return frame[column].fillna("").astype(str).str.strip()
    return pd.Series([""] * len(frame), index=frame.index, dtype="object")


def _first_available_column(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    for column in columns:
        if column in frame.columns:
            return _column_or_blank(frame, column)
    return pd.Series([""] * len(frame), index=frame.index, dtype="object")


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


def _extract_text_from_cancer_type(values: pd.Series) -> pd.Series:
    cleaned = values.fillna("").astype(str).str.strip()
    return cleaned.str.replace(r"^[A-Z]{2,3}_", "", regex=True)


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

    keys = enriched["case_id"].fillna("").astype(str).str.strip()

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
        if "化療流程時間" in report_name:
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
    if frame.empty:
        return pd.DataFrame(
            columns=["icd10_code", "cancer_type", "diagnosis_text", "count", "report_names", "notes"]
        )
    working = frame.copy()
    working["icd10_code_norm"] = working.get("icd10_code", pd.Series("", index=working.index)).fillna("").astype(str).map(_normalize_icd10_code)
    unmatched = working[
        (working["icd10_code_norm"] != "")
        & (working.get("cancer_type", pd.Series("", index=working.index)).fillna("").astype(str).str.strip() == "")
    ]
    if unmatched.empty:
        return pd.DataFrame(
            columns=["icd10_code", "cancer_type", "diagnosis_text", "count", "report_names", "notes"]
        )
    summary = (
        unmatched.groupby("icd10_code_norm", dropna=False)
        .agg(
            count=("icd10_code_norm", "size"),
            report_names=("report_name", lambda values: " | ".join(sorted(set(v for v in values if str(v).strip())))),
        )
        .reset_index()
        .rename(columns={"icd10_code_norm": "icd10_code"})
        .sort_values(by=["count", "icd10_code"], ascending=[False, True])
        .reset_index(drop=True)
    )
    summary.insert(1, "cancer_type", "")
    summary.insert(2, "diagnosis_text", "")
    summary["notes"] = ""
    return summary


def _build_stage_review_report(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["cancer_type", "clinical_tnm", "pathologic_tnm", "final_stage", "final_stage_source", "count"])
    working = frame.copy()
    clinical = working.get("clinical_tnm", pd.Series("", index=working.index)).fillna("").astype(str).str.strip()
    pathologic = working.get("pathologic_tnm", pd.Series("", index=working.index)).fillna("").astype(str).str.strip()
    has_tnm = (clinical != "") | (pathologic != "")
    review = working.loc[has_tnm, ["cancer_type", "clinical_tnm", "pathologic_tnm", "final_stage", "final_stage_source"]].copy()
    if review.empty:
        return pd.DataFrame(columns=["cancer_type", "clinical_tnm", "pathologic_tnm", "final_stage", "final_stage_source", "count"])
    summary = (
        review.groupby(["cancer_type", "clinical_tnm", "pathologic_tnm", "final_stage", "final_stage_source"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(by=["cancer_type", "clinical_tnm", "pathologic_tnm", "count"], ascending=[True, True, True, False])
        .reset_index(drop=True)
    )
    return summary


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

    # Cancer case reports use 個案編號 as the most stable patient-level key.
    if any(tag in report_name for tag in ("D1.1", "D1.2", "D1.4")) and case_id:
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
