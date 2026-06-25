from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    raw_dir: Path
    mapping_dir: Path
    output_dir: Path
    output_file: Path
    column_mapping_file: Path
    value_mapping_file: Path
    tnm_stage_mapping_file: Path
    icd10_mapping_file: Path
    drug_treatment_mapping_file: Path
    order_treatment_mapping_file: Path


def build_paths(project_root: Path | None = None) -> ProjectPaths:
    root = project_root or Path(__file__).resolve().parents[2]
    raw_dir = root / "raw"
    mapping_dir = root / "mapping"
    output_dir = root / "output"

    return ProjectPaths(
        root=root,
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
