from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt


def _prepare_output_path(output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def plot_mission_energy_by_segment(
    mission_profile: dict[str, object],
    output_path: str | Path,
) -> Path:
    path = _prepare_output_path(output_path)

    segments = mission_profile["segments"]
    if not isinstance(segments, list):
        raise TypeError("mission_profile['segments'] must be a list.")

    segment_names = [str(segment["segment_name"]) for segment in segments]
    energy_used_wh = [float(segment["energy_used_wh"]) for segment in segments]

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.bar(segment_names, energy_used_wh)
    ax.set_xlabel("Mission Segment")
    ax.set_ylabel("Energy Used [Wh]")
    ax.set_title("Mission Profile: Energy Used by Segment")
    ax.set_ylim(bottom=0.0)
    ax.grid(True, axis="y")
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)

    return path


def plot_remaining_energy_by_segment(
    mission_profile: dict[str, object],
    output_path: str | Path,
) -> Path:
    path = _prepare_output_path(output_path)

    segments = mission_profile["segments"]
    if not isinstance(segments, list):
        raise TypeError("mission_profile['segments'] must be a list.")

    available_energy_wh = float(mission_profile["available_energy_wh"])

    x_labels = ["start"]
    remaining_energy_wh = [available_energy_wh]

    for segment in segments:
        x_labels.append(str(segment["segment_name"]))
        remaining_energy_wh.append(float(segment["remaining_energy_wh_after_segment"]))

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.plot(x_labels, remaining_energy_wh, marker="o")
    ax.set_xlabel("Mission Progress")
    ax.set_ylabel("Remaining Energy [Wh]")
    ax.set_title("Mission Profile: Remaining Energy by Segment")
    ax.grid(True)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)

    return path