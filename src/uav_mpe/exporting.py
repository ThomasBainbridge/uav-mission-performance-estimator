from __future__ import annotations

from pathlib import Path

import pandas as pd


def _prepare_output_path(output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_sweep_to_csv(
    sweep_df: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    path = _prepare_output_path(output_path)
    sweep_df.to_csv(path, index=False)
    return path


def save_comparison_to_csv(
    comparison_df: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    path = _prepare_output_path(output_path)
    comparison_df.to_csv(path, index=False)
    return path