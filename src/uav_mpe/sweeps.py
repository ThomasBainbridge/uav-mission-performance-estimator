from __future__ import annotations

import numpy as np
import pandas as pd

from uav_mpe.models import Config
from uav_mpe.performance import (
    air_power_required_watts,
    drag_coefficient,
    drag_force_newtons,
    electrical_power_required_watts,
    endurance_hours,
    induced_drag_factor,
    lift_coefficient,
    minimum_recommended_cruise_speed_m_per_s,
    still_air_range_km,
    wind_adjusted_ground_speed_m_per_s,
    wind_adjusted_range_km,
)


def build_speed_sweep(
    config: Config,
    max_speed_m_per_s: float,
    num_points: int = 100,
) -> pd.DataFrame:
    v_min = minimum_recommended_cruise_speed_m_per_s(config)

    if max_speed_m_per_s <= v_min:
        raise ValueError(
            f"max_speed_m_per_s must be greater than minimum recommended cruise speed "
            f"({v_min:.3f} m/s)."
        )

    if num_points < 2:
        raise ValueError("num_points must be at least 2.")

    sweep_config = config.model_copy(deep=True)
    speeds = np.linspace(v_min, max_speed_m_per_s, num_points)

    rows: list[dict[str, float]] = []

    for v in speeds:
        sweep_config.mission.cruise_speed_m_per_s = float(v)

        rows.append(
            {
                "airspeed_m_per_s": float(v),
                "lift_coefficient": lift_coefficient(sweep_config),
                "induced_drag_factor": induced_drag_factor(sweep_config),
                "drag_coefficient": drag_coefficient(sweep_config),
                "drag_force_n": drag_force_newtons(sweep_config),
                "air_power_w": air_power_required_watts(sweep_config),
                "electrical_power_w": electrical_power_required_watts(sweep_config),
                "endurance_h": endurance_hours(sweep_config),
                "still_air_range_km": still_air_range_km(sweep_config),
                "wind_adjusted_ground_speed_m_per_s": wind_adjusted_ground_speed_m_per_s(
                    sweep_config
                ),
                "wind_adjusted_range_km": wind_adjusted_range_km(sweep_config),
            }
        )

    return pd.DataFrame(rows)


def best_endurance_row(
    config: Config,
    max_speed_m_per_s: float,
    num_points: int = 100,
) -> pd.Series:
    df = build_speed_sweep(config, max_speed_m_per_s=max_speed_m_per_s, num_points=num_points)
    return df.loc[df["endurance_h"].idxmax()]


def best_still_air_range_row(
    config: Config,
    max_speed_m_per_s: float,
    num_points: int = 100,
) -> pd.Series:
    df = build_speed_sweep(config, max_speed_m_per_s=max_speed_m_per_s, num_points=num_points)
    return df.loc[df["still_air_range_km"].idxmax()]


def best_wind_adjusted_range_row(
    config: Config,
    max_speed_m_per_s: float,
    num_points: int = 100,
) -> pd.Series:
    df = build_speed_sweep(config, max_speed_m_per_s=max_speed_m_per_s, num_points=num_points)
    return df.loc[df["wind_adjusted_range_km"].idxmax()]