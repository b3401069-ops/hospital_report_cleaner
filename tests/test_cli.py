from report_cleaner import cli
from report_cleaner.config import build_paths


def test_build_paths_points_to_project_directories() -> None:
    paths = build_paths()

    assert paths.raw_dir.name == "raw"
    assert paths.mapping_dir.name == "mapping"
    assert paths.output_dir.name == "output"
    assert paths.column_mapping_file.name == "column_mapping.csv"
    assert paths.drug_treatment_mapping_file.name == "drug_treatment_mapping.csv"
    assert paths.order_treatment_mapping_file.name == "order_treatment_mapping.csv"


def test_cli_main_is_importable() -> None:
    assert callable(cli.main)
