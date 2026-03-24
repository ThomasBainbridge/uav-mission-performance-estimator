from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _prepare_output_path(output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def plot_mission_scenario_energy_balance(
    comparison_df: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    path = _prepare_output_path(output_path)

    x = np.arange(len(comparison_df))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9.0, 5.5))
    ax.bar(
        x - width / 2,
        comparison_df["total_energy_used_wh"],
        width,
        label="Energy used",
    )
    ax.bar(
        x + width / 2,
        comparison_df["remaining_energy_wh"],
        width,
        label="Remaining energy",
    )

    ax.set_xticks(x)
    ax.set_xticklabels(comparison_df["scenario"], rotation=15, ha="right")
    ax.set_xlabel("Mission Scenario")
    ax.set_ylabel("Energy [Wh]")
    ax.set_title("Mission Scenario Comparison: Energy Balance")
    ax.grid(True, axis="y")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)

    return path