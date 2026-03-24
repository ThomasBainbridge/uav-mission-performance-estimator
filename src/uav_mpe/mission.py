from uav_mpe.models import Config
from uav_mpe.performance import (
    battery_available_for_mission_wh,
    electrical_power_required_watts,
    wind_adjusted_ground_speed_m_per_s,
    wind_adjusted_range_km,
)


def required_distance_km(config: Config) -> float:
    value = config.mission.required_distance_km
    if value is None:
        raise ValueError("Mission required_distance_km is not set in the config.")
    return value


def required_mission_time_hours(config: Config) -> float:
    ground_speed_m_per_s = wind_adjusted_ground_speed_m_per_s(config)

    if ground_speed_m_per_s <= 0.0:
        return float("inf")

    ground_speed_km_per_h = ground_speed_m_per_s * 3.6
    return required_distance_km(config) / ground_speed_km_per_h


def required_mission_energy_wh(config: Config) -> float:
    time_h = required_mission_time_hours(config)
    power_w = electrical_power_required_watts(config)

    return power_w * time_h


def range_margin_km(config: Config) -> float:
    return wind_adjusted_range_km(config) - required_distance_km(config)


def energy_margin_wh(config: Config) -> float:
    return battery_available_for_mission_wh(config) - required_mission_energy_wh(config)


def is_mission_feasible(config: Config) -> bool:
    if wind_adjusted_ground_speed_m_per_s(config) <= 0.0:
        return False

    return range_margin_km(config) >= 0.0 and energy_margin_wh(config) >= 0.0