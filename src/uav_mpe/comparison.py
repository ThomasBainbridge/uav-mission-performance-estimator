from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from uav_mpe.models import Config
from uav_mpe.performance import (
    electrical_power_required_watts,
    hotel_load_watts,
    minimum_recommended_cruise_speed_m_per_s,
    non_propulsive_electrical_load_watts,
    payload_load_watts,
    propulsion_electrical_power_required_watts,
    stall_speed_m_per_s,
    total_mass_kg,
)
from uav_mpe.sweeps import (
    best_endurance_row,
    best_still_air_range_row,
    best_wind_adjusted_range_row,
)


def load_config(path: str | Path) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Config.model_validate(data)


def compare_configurations(
    config_paths: list[str | Path],
    max_speed_m_per_s: float,
    num_points: int = 100,
) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []

    for path in config_paths:
        config = load_config(path)
        name = Path(path).stem

        best_endurance = best_endurance_row(
            config,
            max_speed_m_per_s=max_speed_m_per_s,
            num_points=num_points,
        )
        best_still_air_range = best_still_air_range_row(
            config,
            max_speed_m_per_s=max_speed_m_per_s,
            num_points=num_points,
        )
        best_wind_range = best_wind_adjusted_range_row(
            config,
            max_speed_m_per_s=max_speed_m_per_s,
            num_points=num_points,
        )

        rows.append(
            {
                "configuration": name,
                "total_mass_kg": total_mass_kg(config),
                "stall_speed_m_per_s": stall_speed_m_per_s(config),
                "minimum_recommended_cruise_speed_m_per_s": (
                    minimum_recommended_cruise_speed_m_per_s(config)
                ),
                "propulsion_electrical_power_at_nominal_cruise_w": (
                    propulsion_electrical_power_required_watts(config)
                ),
                "hotel_load_w": hotel_load_watts(config),
                "payload_load_w": payload_load_watts(config),
                "non_propulsive_electrical_load_w": non_propulsive_electrical_load_watts(config),
                "electrical_power_at_nominal_cruise_w": (
                    electrical_power_required_watts(config)
                ),
                "best_endurance_speed_m_per_s": best_endurance["airspeed_m_per_s"],
                "maximum_endurance_h": best_endurance["endurance_h"],
                "best_still_air_range_speed_m_per_s": (
                    best_still_air_range["airspeed_m_per_s"]
                ),
                "maximum_still_air_range_km": (
                    best_still_air_range["still_air_range_km"]
                ),
                "best_wind_adjusted_range_speed_m_per_s": (
                    best_wind_range["airspeed_m_per_s"]
                ),
                "maximum_wind_adjusted_range_km": (
                    best_wind_range["wind_adjusted_range_km"]
                ),
            }
        )

    return pd.DataFrame(rows)