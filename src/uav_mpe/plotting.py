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


def _add_speed_markers(
    ax,
    v_stall_m_per_s: float | None = None,
    v_min_recommended_m_per_s: float | None = None,
) -> None:
    if v_stall_m_per_s is not None:
        ax.axvline(
            v_stall_m_per_s,
            linestyle="--",
            linewidth=1.5,
            label="Stall speed",
        )

    if v_min_recommended_m_per_s is not None:
        ax.axvline(
            v_min_recommended_m_per_s,
            linestyle=":",
            linewidth=1.8,
            label="Min recommended cruise",
        )


def _add_legend_if_needed(ax) -> None:
    handles, labels = ax.get_legend_handles_labels()
    if labels:
        ax.legend()


def plot_power_vs_speed(
    sweep_df: pd.DataFrame,
    output_path: str | Path,
    v_stall_m_per_s: float | None = None,
    v_min_recommended_m_per_s: float | None = None,
) -> Path:
    path = _prepare_output_path(output_path)

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.plot(sweep_df["airspeed_m_per_s"], sweep_df["air_power_w"], label="Air power")
    ax.plot(
        sweep_df["airspeed_m_per_s"],
        sweep_df["electrical_power_w"],
        label="Electrical power",
    )
    _add_speed_markers(ax, v_stall_m_per_s, v_min_recommended_m_per_s)

    ax.set_xlabel("Airspeed [m/s]")
    ax.set_ylabel("Power [W]")
    ax.set_title("Power Required vs Airspeed")
    ax.set_ylim(bottom=0.0)
    ax.grid(True)
    _add_legend_if_needed(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)

    return path


def plot_endurance_vs_speed(
    sweep_df: pd.DataFrame,
    output_path: str | Path,
    v_stall_m_per_s: float | None = None,
    v_min_recommended_m_per_s: float | None = None,
) -> Path:
    path = _prepare_output_path(output_path)

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.plot(
        sweep_df["airspeed_m_per_s"],
        sweep_df["endurance_h"],
        label="Endurance",
    )
    _add_speed_markers(ax, v_stall_m_per_s, v_min_recommended_m_per_s)

    ax.set_xlabel("Airspeed [m/s]")
    ax.set_ylabel("Endurance [h]")
    ax.set_title("Endurance vs Airspeed")
    ax.set_ylim(bottom=0.0)
    ax.grid(True)
    _add_legend_if_needed(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)

    return path


def plot_range_vs_speed(
    sweep_df: pd.DataFrame,
    output_path: str | Path,
    v_stall_m_per_s: float | None = None,
    v_min_recommended_m_per_s: float | None = None,
) -> Path:
    path = _prepare_output_path(output_path)

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.plot(
        sweep_df["airspeed_m_per_s"],
        sweep_df["still_air_range_km"],
        label="Still-air range",
    )
    ax.plot(
        sweep_df["airspeed_m_per_s"],
        sweep_df["wind_adjusted_range_km"],
        label="Wind-adjusted range",
    )
    _add_speed_markers(ax, v_stall_m_per_s, v_min_recommended_m_per_s)

    ax.set_xlabel("Airspeed [m/s]")
    ax.set_ylabel("Range [km]")
    ax.set_title("Range vs Airspeed")
    ax.set_ylim(bottom=0.0)
    ax.grid(True)
    _add_legend_if_needed(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)

    return path


def plot_comparison_ranges(
    comparison_df: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    path = _prepare_output_path(output_path)

    fig, ax = plt.subplots(figsize=(9.0, 5.5))

    x = np.arange(len(comparison_df))
    width = 0.35

    ax.bar(
        x - width / 2,
        comparison_df["maximum_still_air_range_km"],
        width,
        label="Still-air range",
    )
    ax.bar(
        x + width / 2,
        comparison_df["maximum_wind_adjusted_range_km"],
        width,
        label="Wind-adjusted range",
    )

    ax.set_xticks(x)
    ax.set_xticklabels(comparison_df["configuration"], rotation=15, ha="right")
    ax.set_xlabel("Configuration")
    ax.set_ylabel("Maximum range [km]")
    ax.set_title("Configuration Comparison: Maximum Range")
    ax.set_ylim(bottom=0.0)
    ax.grid(True, axis="y")
    _add_legend_if_needed(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)

    return path