from __future__ import annotations

import sys
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


def _is_pyinstaller_bundle() -> bool:
    """检测是否在 PyInstaller 打包环境中运行"""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def build_paths(project_root: Path | None = None) -> ProjectPaths:
    if _is_pyinstaller_bundle():
        # 在打包环境中，使用临时目录作为根目录（包含资源文件）
        root = Path(sys._MEIPASS)
        # 但 raw 和 output 目录应该在可执行文件所在目录
        exe_dir = Path(sys.executable).parent
        raw_dir = exe_dir / "raw"
        output_dir = exe_dir / "output"
        mapping_dir = root / "mapping"  # mapping 文件在打包资源中
    else:
        # 在开发环境中，使用项目根目录
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
    )
