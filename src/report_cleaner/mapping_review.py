from __future__ import annotations

from pathlib import Path

import pandas as pd

from .cleaner import run_cleaning
from .config import CSV_ENCODING, ProjectPaths

PENDING_DRUG_MAPPING_FILE = "pending_drug_treatment_mapping.csv"
PENDING_ORDER_MAPPING_FILE = "pending_order_treatment_mapping.csv"
PENDING_STAGE_MAPPING_FILE = "pending_tnm_stage_mapping.csv"

DRUG_MAPPING_COLUMNS = [
    "treatment_type",
    "name_pattern",
    "order_code",
    "order_code_prefix",
    "notes",
]
ORDER_MAPPING_COLUMNS = [
    "treatment_type",
    "name_pattern",
    "order_code",
    "order_code_prefix",
    "cancer_type",
    "diagnosis_text",
    "notes",
]
STAGE_MAPPING_COLUMNS = [
    "cancer_type",
    "tnm_pattern",
    "final_stage",
    "notes",
]
DRUG_REVIEW_COLUMNS = DRUG_MAPPING_COLUMNS + [
    "order_name",
    "count",
    "report_names",
    "sample_diagnosis_texts",
]
ORDER_REVIEW_COLUMNS = ORDER_MAPPING_COLUMNS + [
    "order_name",
    "count",
    "report_names",
    "sample_diagnosis_texts",
]
STAGE_REVIEW_COLUMNS = STAGE_MAPPING_COLUMNS + [
    "clinical_tnm",
    "pathologic_tnm",
    "review_reason",
    "count",
]
DRUG_TREATMENT_TYPES = {
    "chemotherapy",
    "targeted_therapy",
    "immunotherapy",
    "hormone_therapy",
}
ORDER_TREATMENT_TYPES = {
    "chemotherapy",
    "radiation_therapy",
    "surgery",
    "tace",
    "rfa",
}


def export_mapping_review_files(paths: ProjectPaths) -> tuple[Path, Path, Path]:
    (
        _cleaned_frame,
        _standardized_frame,
        _patient_master_frame,
        _patient_list_frame,
        _unmatched_icd10_frame,
        stage_review_frame,
        unmapped_drug_orders_frame,
        unmapped_treatment_orders_frame,
        _processed_files,
    ) = run_cleaning(paths)

    paths.output_dir.mkdir(parents=True, exist_ok=True)
    drug_file = paths.output_dir / PENDING_DRUG_MAPPING_FILE
    order_file = paths.output_dir / PENDING_ORDER_MAPPING_FILE
    stage_file = paths.output_dir / PENDING_STAGE_MAPPING_FILE

    _build_pending_drug_mapping(unmapped_drug_orders_frame).to_csv(
        drug_file, index=False, encoding=CSV_ENCODING
    )
    _build_pending_order_mapping(unmapped_treatment_orders_frame).to_csv(
        order_file, index=False, encoding=CSV_ENCODING
    )
    _build_pending_stage_mapping(stage_review_frame).to_csv(
        stage_file, index=False, encoding=CSV_ENCODING
    )
    return drug_file, order_file, stage_file


def apply_mapping_review_files(paths: ProjectPaths) -> dict[str, int]:
    drug_pending_file = paths.output_dir / PENDING_DRUG_MAPPING_FILE
    order_pending_file = paths.output_dir / PENDING_ORDER_MAPPING_FILE
    drug_added = _append_confirmed_mapping_rows(
        pending_file=drug_pending_file,
        mapping_file=paths.drug_treatment_mapping_file,
        mapping_columns=DRUG_MAPPING_COLUMNS,
        valid_treatment_types=DRUG_TREATMENT_TYPES,
    )
    order_added = _append_confirmed_mapping_rows(
        pending_file=order_pending_file,
        mapping_file=paths.order_treatment_mapping_file,
        mapping_columns=ORDER_MAPPING_COLUMNS,
        valid_treatment_types=ORDER_TREATMENT_TYPES,
    )
    stage_added = _append_confirmed_stage_rows(
        pending_file=paths.output_dir / PENDING_STAGE_MAPPING_FILE,
        mapping_file=paths.tnm_stage_mapping_file,
    )
    return {"drug_rows_added": drug_added, "order_rows_added": order_added, "stage_rows_added": stage_added}


def _build_pending_drug_mapping(unmapped_frame: pd.DataFrame) -> pd.DataFrame:
    pending = _ensure_columns(unmapped_frame, DRUG_REVIEW_COLUMNS)
    pending = pending.copy()
    pending["name_pattern"] = pending["name_pattern"].where(
        pending["name_pattern"].astype(str).str.strip() != "", ""
    )
    return pending[DRUG_REVIEW_COLUMNS]


def _build_pending_order_mapping(unmapped_frame: pd.DataFrame) -> pd.DataFrame:
    pending = _ensure_columns(unmapped_frame, ORDER_REVIEW_COLUMNS)
    return pending[ORDER_REVIEW_COLUMNS]


def _build_pending_stage_mapping(stage_review_frame: pd.DataFrame) -> pd.DataFrame:
    pending = _ensure_columns(stage_review_frame, STAGE_REVIEW_COLUMNS + ["primary_tnm"])
    pending = pending.copy()
    pending["tnm_pattern"] = pending["tnm_pattern"].where(
        pending["tnm_pattern"].astype(str).str.strip() != "",
        pending["primary_tnm"].astype(str).str.strip(),
    )
    pending["notes"] = pending["notes"].where(
        pending["notes"].astype(str).str.strip() != "",
        pending["review_reason"].astype(str).str.strip(),
    )
    missing_stage = pending["final_stage"].astype(str).str.strip() == ""
    has_tnm = pending["tnm_pattern"].astype(str).str.strip() != ""
    not_reported = pending["review_reason"].astype(str).str.strip() != "reported_stage"
    pending = pending[missing_stage & has_tnm & not_reported].copy()
    return pending[STAGE_REVIEW_COLUMNS]


def _append_confirmed_mapping_rows(
    *,
    pending_file: Path,
    mapping_file: Path,
    mapping_columns: list[str],
    valid_treatment_types: set[str],
) -> int:
    if not pending_file.exists():
        return 0

    pending = pd.read_csv(pending_file, dtype=str, encoding=CSV_ENCODING).fillna("")
    pending = _ensure_columns(pending, mapping_columns)
    pending = pending[mapping_columns].copy()
    pending = pending.apply(lambda column: column.map(lambda value: str(value).strip()))
    pending = pending[pending["treatment_type"] != ""].copy()
    if pending.empty:
        return 0

    invalid = sorted(set(pending["treatment_type"]) - valid_treatment_types)
    if invalid:
        raise ValueError(f"Invalid treatment_type values: {', '.join(invalid)}")

    has_match_rule = (
        (pending.get("name_pattern", "") != "")
        | (pending.get("order_code", "") != "")
        | (pending.get("order_code_prefix", "") != "")
    )
    pending = pending[has_match_rule].copy()
    if pending.empty:
        return 0

    if mapping_file.exists():
        existing = pd.read_csv(mapping_file, dtype=str, encoding=CSV_ENCODING).fillna("")
        existing = _ensure_columns(existing, mapping_columns)
        existing = existing[mapping_columns].copy()
    else:
        existing = pd.DataFrame(columns=mapping_columns)

    combined = pd.concat([existing, pending], ignore_index=True)
    before = len(existing.drop_duplicates(subset=mapping_columns))
    combined = combined.drop_duplicates(subset=mapping_columns, keep="first").reset_index(drop=True)
    after = len(combined)

    mapping_file.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(mapping_file, index=False, encoding=CSV_ENCODING)
    return after - before


def _append_confirmed_stage_rows(*, pending_file: Path, mapping_file: Path) -> int:
    if not pending_file.exists():
        return 0

    pending = pd.read_csv(pending_file, dtype=str, encoding=CSV_ENCODING).fillna("")
    pending = _ensure_columns(pending, STAGE_MAPPING_COLUMNS)
    pending = pending[STAGE_MAPPING_COLUMNS].copy()
    pending = pending.apply(lambda column: column.map(lambda value: str(value).strip()))
    pending = pending[
        (pending["cancer_type"] != "")
        & (pending["tnm_pattern"] != "")
        & (pending["final_stage"] != "")
    ].copy()
    if pending.empty:
        return 0

    if mapping_file.exists():
        existing = pd.read_csv(mapping_file, dtype=str, encoding=CSV_ENCODING).fillna("")
        existing = _ensure_columns(existing, STAGE_MAPPING_COLUMNS)
        existing = existing[STAGE_MAPPING_COLUMNS].copy()
    else:
        existing = pd.DataFrame(columns=STAGE_MAPPING_COLUMNS)

    combined = pd.concat([existing, pending], ignore_index=True)
    before = len(existing.drop_duplicates(subset=STAGE_MAPPING_COLUMNS))
    combined = combined.drop_duplicates(subset=STAGE_MAPPING_COLUMNS, keep="first").reset_index(drop=True)
    after = len(combined)

    mapping_file.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(mapping_file, index=False, encoding=CSV_ENCODING)
    return after - before


def _ensure_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    ensured = frame.copy()
    for column in columns:
        if column not in ensured.columns:
            ensured[column] = ""
    return ensured[columns]
