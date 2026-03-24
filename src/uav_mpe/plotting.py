from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


def _prepare_output_path(output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def plot_power_vs_speed(
    sweep_df: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    path = _prepare_output_path(output_path)

    plt.figure(figsize=(8, 5))
    plt.plot(sweep_df["airspeed_m_per_s"], sweep_df["air_power_w"], label="Air power")
    plt.plot(
        sweep_df["airspeed_m_per_s"],
        sweep_df["electrical_power_w"],
        label="Electrical power",
    )
    plt.xlabel("Airspeed [m/s]")
    plt.ylabel("Power [W]")
    plt.title("Power Required vs Airspeed")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()

    return path


def plot_endurance_vs_speed(
    sweep_df: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    path = _prepare_output_path(output_path)

    plt.figure(figsize=(8, 5))
    plt.plot(sweep_df["airspeed_m_per_s"], sweep_df["endurance_h"])
    plt.xlabel("Airspeed [m/s]")
    plt.ylabel("Endurance [h]")
    plt.title("Endurance vs Airspeed")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()

    return path


def plot_range_vs_speed(
    sweep_df: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    path = _prepare_output_path(output_path)

    plt.figure(figsize=(8, 5))
    plt.plot(
        sweep_df["airspeed_m_per_s"],
        sweep_df["still_air_range_km"],
        label="Still-air range",
    )
    plt.plot(
        sweep_df["airspeed_m_per_s"],
        sweep_df["wind_adjusted_range_km"],
        label="Wind-adjusted range",
    )
    plt.xlabel("Airspeed [m/s]")
    plt.ylabel("Range [km]")
    plt.title("Range vs Airspeed")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()

    return path