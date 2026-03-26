from __future__ import annotations

from uav_mpe.models import Config
from uav_mpe.performance import (
    air_power_required_watts,
    non_propulsive_electrical_load_watts,
)


def descent_time_seconds(descent_altitude_m: float, descent_rate_m_per_s: float) -> float:
    if descent_altitude_m < 0.0:
        raise ValueError("descent_altitude_m must be non-negative.")
    if descent_rate_m_per_s <= 0.0:
        raise ValueError("descent_rate_m_per_s must be greater than 0.")
    return descent_altitude_m / descent_rate_m_per_s


def descent_time_hours(descent_altitude_m: float, descent_rate_m_per_s: float) -> float:
    return descent_time_seconds(descent_altitude_m, descent_rate_m_per_s) / 3600.0


def descent_total_electrical_power_watts(
    config: Config,
    descent_power_factor: float,
) -> float:
    if descent_power_factor <= 0.0 or descent_power_factor > 1.0:
        raise ValueError("descent_power_factor must be in the interval (0, 1].")

    propulsion_level_power_w = air_power_required_watts(config) / config.aircraft.eta_total
    non_propulsive_power_w = non_propulsive_electrical_load_watts(config)

    return descent_power_factor * propulsion_level_power_w + non_propulsive_power_w


def descent_energy_wh(
    config: Config,
    descent_altitude_m: float,
    descent_rate_m_per_s: float,
    descent_power_factor: float,
) -> float:
    power_w = descent_total_electrical_power_watts(config, descent_power_factor)
    time_h = descent_time_hours(descent_altitude_m, descent_rate_m_per_s)
    return power_w * time_h