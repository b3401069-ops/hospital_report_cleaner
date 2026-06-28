from report_cleaner import cli
from report_cleaner.config import build_paths
from report_cleaner.environment import build_environment_checks, environment_has_errors


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


def test_environment_check_runs_on_project_root() -> None:
    checks = build_environment_checks(build_paths())

    check_names = {check.name for check in checks}
    assert "python" in check_names
    assert "package:pandas" in check_names
    assert "mapping:column_mapping.csv" in check_names
    assert "output_writable" in check_names


def test_environment_check_reports_missing_mapping_file(tmp_path) -> None:
    paths = build_paths(tmp_path)
    paths.raw_dir.mkdir()
    paths.mapping_dir.mkdir()
    paths.output_dir.mkdir()

    checks = build_environment_checks(paths)

    assert environment_has_errors(checks)
    assert any(
        check.name == "mapping:column_mapping.csv" and check.status == "error"
        for check in checks
    )


def test_cli_check_env_command_runs(capsys) -> None:
    cli.main(["check-env"])

    captured = capsys.readouterr()
    assert "Environment check:" in captured.out
    assert "Result: environment is ready." in captured.out
