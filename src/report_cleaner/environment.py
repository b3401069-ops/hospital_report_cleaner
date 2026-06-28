from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path

from .config import ProjectPaths


REQUIRED_RUNTIME_PACKAGES = {
    "pandas": "pandas",
    "openpyxl": "openpyxl",
    "xlrd": "xlrd",
    "python-dateutil": "dateutil",
}

REQUIRED_MAPPING_FILES = (
    "column_mapping_file",
    "value_mapping_file",
    "tnm_stage_mapping_file",
    "icd10_mapping_file",
    "drug_treatment_mapping_file",
    "order_treatment_mapping_file",
)


@dataclass(frozen=True)
class EnvironmentCheck:
    name: str
    status: str
    message: str


def build_environment_checks(paths: ProjectPaths) -> list[EnvironmentCheck]:
    checks: list[EnvironmentCheck] = []

    checks.append(
        EnvironmentCheck(
            name="python",
            status="ok" if sys.version_info >= (3, 10) else "error",
            message=f"{sys.executable} ({sys.version.split()[0]})",
        )
    )

    for package_name, import_name in REQUIRED_RUNTIME_PACKAGES.items():
        checks.append(
            EnvironmentCheck(
                name=f"package:{package_name}",
                status="ok" if importlib.util.find_spec(import_name) else "error",
                message=f"import {import_name}",
            )
        )

    checks.extend(
        [
            _directory_check("project_root", paths.root, must_exist=True),
            _directory_check("raw_dir", paths.raw_dir, must_exist=True),
            _directory_check("mapping_dir", paths.mapping_dir, must_exist=True),
            _directory_check("output_dir", paths.output_dir, must_exist=False),
        ]
    )

    excel_files = _find_excel_files(paths.raw_dir)
    checks.append(
        EnvironmentCheck(
            name="raw_reports",
            status="ok" if excel_files else "warning",
            message=f"{len(excel_files)} Excel file(s) found in raw/",
        )
    )

    for attr in REQUIRED_MAPPING_FILES:
        mapping_file = getattr(paths, attr)
        checks.append(
            EnvironmentCheck(
                name=f"mapping:{mapping_file.name}",
                status="ok" if mapping_file.exists() else "error",
                message=str(mapping_file),
            )
        )

    checks.append(_output_writable_check(paths.output_dir))
    checks.append(_gitignore_safety_check(paths.root / ".gitignore"))
    return checks


def environment_has_errors(checks: list[EnvironmentCheck]) -> bool:
    return any(check.status == "error" for check in checks)


def format_environment_checks(checks: list[EnvironmentCheck]) -> str:
    lines = ["Environment check:"]
    for check in checks:
        marker = {"ok": "[OK]", "warning": "[WARN]", "error": "[ERROR]"}.get(
            check.status, "[INFO]"
        )
        lines.append(f"{marker} {check.name}: {check.message}")
    if environment_has_errors(checks):
        lines.append("Result: environment has errors.")
    else:
        lines.append("Result: environment is ready.")
    return "\n".join(lines)


def _directory_check(name: str, path: Path, *, must_exist: bool) -> EnvironmentCheck:
    if path.exists() and path.is_dir():
        return EnvironmentCheck(name=name, status="ok", message=str(path))
    if must_exist:
        return EnvironmentCheck(name=name, status="error", message=f"missing: {path}")
    return EnvironmentCheck(name=name, status="warning", message=f"will be created: {path}")


def _find_excel_files(raw_dir: Path) -> list[Path]:
    if not raw_dir.exists() or not raw_dir.is_dir():
        return []
    suffixes = {".xls", ".xlsx", ".xlsm"}
    return [path for path in raw_dir.iterdir() if path.is_file() and path.suffix.lower() in suffixes]


def _output_writable_check(output_dir: Path) -> EnvironmentCheck:
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        probe = output_dir / ".write_test.tmp"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        return EnvironmentCheck(
            name="output_writable",
            status="error",
            message=f"cannot write to output/: {exc}",
        )
    return EnvironmentCheck(name="output_writable", status="ok", message=str(output_dir))


def _gitignore_safety_check(gitignore_file: Path) -> EnvironmentCheck:
    if not gitignore_file.exists():
        return EnvironmentCheck(
            name="gitignore_safety",
            status="warning",
            message=".gitignore not found",
        )
    text = gitignore_file.read_text(encoding="utf-8", errors="ignore")
    raw_ignored = "raw/*" in text
    output_ignored = "output/*" in text
    status = "ok" if raw_ignored and output_ignored else "warning"
    message = "raw/ and output/ are ignored" if status == "ok" else "check raw/output ignore rules"
    return EnvironmentCheck(name="gitignore_safety", status=status, message=message)
