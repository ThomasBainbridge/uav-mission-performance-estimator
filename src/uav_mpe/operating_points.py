from __future__ import annotations

from uav_mpe.models import Config
from uav_mpe.sweeps import (
    best_endurance_row,
    best_still_air_range_row,
    best_wind_adjusted_range_row,
)


def _operating_point_from_row(row) -> dict[str, float]:
    return {
        "airspeed_m_per_s": float(row["airspeed_m_per_s"]),
        "air_power_w": float(row["air_power_w"]),
        "propulsion_electrical_power_w": float(row["propulsion_electrical_power_w"]),
        "hotel_load_w": float(row["hotel_load_w"]),
        "payload_load_w": float(row["payload_load_w"]),
        "non_propulsive_electrical_load_w": float(row["non_propulsive_electrical_load_w"]),
        "electrical_power_w": float(row["electrical_power_w"]),
        "endurance_h": float(row["endurance_h"]),
        "still_air_range_km": float(row["still_air_range_km"]),
        "wind_adjusted_range_km": float(row["wind_adjusted_range_km"]),
    }


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
    return _operating_point_from_row(row)


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
    return _operating_point_from_row(row)


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
    return _operating_point_from_row(row)