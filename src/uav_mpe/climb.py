from __future__ import annotations

from uav_mpe.models import Config
from uav_mpe.performance import electrical_power_required_watts, total_mass_kg


def climb_time_seconds(climb_altitude_m: float, climb_rate_m_per_s: float) -> float:
    if climb_altitude_m < 0.0:
        raise ValueError("climb_altitude_m must be non-negative.")
    if climb_rate_m_per_s <= 0.0:
        raise ValueError("climb_rate_m_per_s must be greater than 0.")
    return climb_altitude_m / climb_rate_m_per_s


def climb_time_hours(climb_altitude_m: float, climb_rate_m_per_s: float) -> float:
    return climb_time_seconds(climb_altitude_m, climb_rate_m_per_s) / 3600.0


def climb_extra_power_watts(config: Config, climb_rate_m_per_s: float) -> float:
    if climb_rate_m_per_s <= 0.0:
        raise ValueError("climb_rate_m_per_s must be greater than 0.")

    mass_kg = total_mass_kg(config)
    g = config.environment.g_m_per_s2
    eta_total = config.aircraft.eta_total

    return (mass_kg * g * climb_rate_m_per_s) / eta_total


def climb_total_electrical_power_watts(config: Config, climb_rate_m_per_s: float) -> float:
    level_power = electrical_power_required_watts(config)
    extra_power = climb_extra_power_watts(config, climb_rate_m_per_s)
    return level_power + extra_power


def climb_energy_wh(config: Config, climb_altitude_m: float, climb_rate_m_per_s: float) -> float:
    power_w = climb_total_electrical_power_watts(config, climb_rate_m_per_s)
    time_h = climb_time_hours(climb_altitude_m, climb_rate_m_per_s)
    return power_w * time_h