from __future__ import annotations

from pathlib import Path

import pandas as pd


def _prepare_output_path(output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_mission_profile_segments_to_csv(
    mission_profile: dict[str, object],
    output_path: str | Path,
) -> Path:
    path = _prepare_output_path(output_path)

    segments = mission_profile["segments"]
    if not isinstance(segments, list):
        raise TypeError("mission_profile['segments'] must be a list.")

    df = pd.DataFrame(segments)
    df.to_csv(path, index=False)
    return path


def save_mission_profile_summary_to_csv(
    mission_profile: dict[str, object],
    output_path: str | Path,
) -> Path:
    path = _prepare_output_path(output_path)

    summary = {
        "available_energy_wh": mission_profile["available_energy_wh"],
        "total_time_h": mission_profile["total_time_h"],
        "total_energy_used_wh": mission_profile["total_energy_used_wh"],
        "total_propulsion_energy_wh": mission_profile["total_propulsion_energy_wh"],
        "total_hotel_energy_wh": mission_profile["total_hotel_energy_wh"],
        "total_payload_energy_wh": mission_profile["total_payload_energy_wh"],
        "total_non_propulsive_energy_wh": mission_profile["total_non_propulsive_energy_wh"],
        "remaining_energy_wh": mission_profile["remaining_energy_wh"],
        "mission_feasible": mission_profile["mission_feasible"],
        "number_of_segments": len(mission_profile["segments"]),
    }

    df = pd.DataFrame([summary])
    df.to_csv(path, index=False)
    return path