import pandas as pd

from report_cleaner.config import CSV_ENCODING, ProjectPaths
from report_cleaner.mapping_review import (
    PENDING_DRUG_MAPPING_FILE,
    PENDING_ORDER_MAPPING_FILE,
    PENDING_STAGE_MAPPING_FILE,
    apply_mapping_review_files,
)


def test_apply_mapping_review_files_appends_only_confirmed_rows(tmp_path) -> None:
    mapping_dir = tmp_path / "mapping"
    output_dir = tmp_path / "output"
    raw_dir = tmp_path / "raw"
    mapping_dir.mkdir()
    output_dir.mkdir()
    raw_dir.mkdir()
    paths = ProjectPaths(
        root=tmp_path,
        raw_dir=raw_dir,
        mapping_dir=mapping_dir,
        output_dir=output_dir,
        output_file=output_dir / "cleaned_reports.xlsx",
        column_mapping_file=mapping_dir / "column_mapping.csv",
        value_mapping_file=mapping_dir / "value_mapping.csv",
        tnm_stage_mapping_file=mapping_dir / "tnm_stage_mapping.csv",
        icd10_mapping_file=mapping_dir / "icd10_mapping.csv",
        drug_treatment_mapping_file=mapping_dir / "drug_treatment_mapping.csv",
        order_treatment_mapping_file=mapping_dir / "order_treatment_mapping.csv",
    )

    pd.DataFrame(
        [
            {
                "treatment_type": "targeted_therapy",
                "name_pattern": "examplemab",
                "order_code": "",
                "order_code_prefix": "",
                "notes": "confirmed",
                "order_name": "Examplemab 100mg",
                "count": "3",
                "report_names": "drug report",
                "sample_diagnosis_texts": "",
            },
            {
                "treatment_type": "",
                "name_pattern": "ignored",
                "order_code": "",
                "order_code_prefix": "",
                "notes": "",
                "order_name": "Ignored 100mg",
                "count": "1",
                "report_names": "drug report",
                "sample_diagnosis_texts": "",
            },
        ]
    ).to_csv(output_dir / PENDING_DRUG_MAPPING_FILE, index=False, encoding=CSV_ENCODING)
    pd.DataFrame(
        [
            {
                "treatment_type": "surgery",
                "name_pattern": "",
                "order_code": "99999X",
                "order_code_prefix": "",
                "cancer_type": "TS_測試癌",
                "diagnosis_text": "測試癌",
                "notes": "confirmed",
                "order_name": "測試術式",
                "count": "2",
                "report_names": "order report",
                "sample_diagnosis_texts": "",
            }
        ]
    ).to_csv(output_dir / PENDING_ORDER_MAPPING_FILE, index=False, encoding=CSV_ENCODING)
    pd.DataFrame(
        [
            {
                "cancer_type": "CR_結腸直腸癌",
                "tnm_pattern": "cT3N1M0",
                "final_stage": "3",
                "notes": "confirmed",
                "clinical_tnm": "cT3N1M0",
                "pathologic_tnm": "",
                "review_reason": "missing_final_stage",
                "count": "2",
            },
            {
                "cancer_type": "LC_肺癌",
                "tnm_pattern": "cT2NxMx",
                "final_stage": "",
                "notes": "needs review",
                "clinical_tnm": "cT2NxMx",
                "pathologic_tnm": "",
                "review_reason": "missing_final_stage_with_unknown_tnm",
                "count": "2",
            },
        ]
    ).to_csv(output_dir / PENDING_STAGE_MAPPING_FILE, index=False, encoding=CSV_ENCODING)

    result = apply_mapping_review_files(paths)
    result_again = apply_mapping_review_files(paths)

    assert result == {"drug_rows_added": 1, "order_rows_added": 1, "stage_rows_added": 1}
    assert result_again == {"drug_rows_added": 0, "order_rows_added": 0, "stage_rows_added": 0}
    drug_mapping = pd.read_csv(paths.drug_treatment_mapping_file, dtype=str, encoding=CSV_ENCODING).fillna("")
    order_mapping = pd.read_csv(paths.order_treatment_mapping_file, dtype=str, encoding=CSV_ENCODING).fillna("")
    stage_mapping = pd.read_csv(paths.tnm_stage_mapping_file, dtype=str, encoding=CSV_ENCODING).fillna("")
    assert drug_mapping["treatment_type"].tolist() == ["targeted_therapy"]
    assert order_mapping["order_code"].tolist() == ["99999X"]
    assert stage_mapping["tnm_pattern"].tolist() == ["cT3N1M0"]
    assert stage_mapping["final_stage"].tolist() == ["3"]
    assert paths.drug_treatment_mapping_file.read_bytes().startswith(b"\xef\xbb\xbf")
    assert paths.order_treatment_mapping_file.read_bytes().startswith(b"\xef\xbb\xbf")
    assert paths.tnm_stage_mapping_file.read_bytes().startswith(b"\xef\xbb\xbf")
