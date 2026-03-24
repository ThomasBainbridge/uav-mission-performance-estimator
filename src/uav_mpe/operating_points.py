from __future__ import annotations

from uav_mpe.models import Config
from uav_mpe.sweeps import (
    best_endurance_row,
    best_still_air_range_row,
    best_wind_adjusted_range_row,
)


def get_best_endurance_operating_point(
    config: Config,
    max_speed_m_per_s: float,
    num_points: int = 100,
) -> dict[str, float]:
    row = best_endurance_row(
        config,
        max_speed_m_per_s=max_speed_m_per_s,
        num_points=num_points,
    )

    return {
        "airspeed_m_per_s": float(row["airspeed_m_per_s"]),
        "electrical_power_w": float(row["electrical_power_w"]),
        "endurance_h": float(row["endurance_h"]),
        "still_air_range_km": float(row["still_air_range_km"]),
        "wind_adjusted_range_km": float(row["wind_adjusted_range_km"]),
    }


def get_best_range_operating_point(
    config: Config,
    max_speed_m_per_s: float,
    num_points: int = 100,
) -> dict[str, float]:
    row = best_still_air_range_row(
        config,
        max_speed_m_per_s=max_speed_m_per_s,
        num_points=num_points,
    )

    return {
        "airspeed_m_per_s": float(row["airspeed_m_per_s"]),
        "electrical_power_w": float(row["electrical_power_w"]),
        "endurance_h": float(row["endurance_h"]),
        "still_air_range_km": float(row["still_air_range_km"]),
        "wind_adjusted_range_km": float(row["wind_adjusted_range_km"]),
    }


def get_best_wind_adjusted_range_operating_point(
    config: Config,
    max_speed_m_per_s: float,
    num_points: int = 100,
) -> dict[str, float]:
    row = best_wind_adjusted_range_row(
        config,
        max_speed_m_per_s=max_speed_m_per_s,
        num_points=num_points,
    )

    return {
        "airspeed_m_per_s": float(row["airspeed_m_per_s"]),
        "electrical_power_w": float(row["electrical_power_w"]),
        "endurance_h": float(row["endurance_h"]),
        "still_air_range_km": float(row["still_air_range_km"]),
        "wind_adjusted_range_km": float(row["wind_adjusted_range_km"]),
    }