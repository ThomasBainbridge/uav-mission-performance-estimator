from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from uav_mpe.mission_profile import evaluate_simple_mission_profile
from uav_mpe.models import Config


def load_config(path: str | Path) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Config.model_validate(data)


def compare_mission_scenarios(
    config_paths: list[str | Path],
    max_speed_m_per_s: float = 40.0,
    num_points: int = 120,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for path in config_paths:
        config = load_config(path)

        if config.mission.profile is None:
            raise ValueError(f"Mission profile is not defined in config: {path}")

        profile = config.mission.profile

        mission_profile = evaluate_simple_mission_profile(
            config,
            outbound_distance_km=profile.outbound_distance_km,
            loiter_duration_min=profile.loiter_duration_min,
            return_distance_km=profile.return_distance_km,
            outbound_wind_speed_m_per_s=profile.outbound_wind_speed_m_per_s,
            return_wind_speed_m_per_s=profile.return_wind_speed_m_per_s,
            cruise_mode=profile.cruise_mode,
            max_speed_m_per_s=max_speed_m_per_s,
            num_points=num_points,
        )

        rows.append(
            {
                "scenario": Path(path).stem,
                "mission_feasible": bool(mission_profile["mission_feasible"]),
                "available_energy_wh": float(mission_profile["available_energy_wh"]),
                "total_time_h": float(mission_profile["total_time_h"]),
                "total_energy_used_wh": float(mission_profile["total_energy_used_wh"]),
                "remaining_energy_wh": float(mission_profile["remaining_energy_wh"]),
                "number_of_segments": len(mission_profile["segments"]),
                "outbound_distance_km": float(profile.outbound_distance_km),
                "loiter_duration_min": (
                    None if profile.loiter_duration_min is None else float(profile.loiter_duration_min)
                ),
                "return_distance_km": (
                    None if profile.return_distance_km is None else float(profile.return_distance_km)
                ),
                "cruise_mode": profile.cruise_mode,
            }
        )

    return pd.DataFrame(rows)