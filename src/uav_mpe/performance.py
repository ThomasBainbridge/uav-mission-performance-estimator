from math import sqrt

from uav_mpe.models import Config


def total_mass_kg(config: Config) -> float:
    aircraft = config.aircraft
    return aircraft.empty_mass_kg + aircraft.payload_mass_kg + aircraft.battery_mass_kg


def weight_newtons(config: Config) -> float:
    return total_mass_kg(config) * config.environment.g_m_per_s2


def battery_nominal_energy_wh(config: Config) -> float:
    aircraft = config.aircraft
    return aircraft.battery_mass_kg * aircraft.battery_specific_energy_wh_per_kg


def battery_usable_energy_wh(config: Config) -> float:
    return battery_nominal_energy_wh(config) * config.mission.usable_battery_fraction


def battery_available_for_mission_wh(config: Config) -> float:
    usable = battery_usable_energy_wh(config)
    reserve_fraction = config.mission.reserve_fraction
    return usable * (1.0 - reserve_fraction)


def battery_available_for_mission_j(config: Config) -> float:
    return battery_available_for_mission_wh(config) * 3600.0


def stall_speed_m_per_s(config: Config) -> float:
    w = weight_newtons(config)
    rho = config.environment.air_density_kg_per_m3
    s = config.aircraft.wing_area_m2
    cl_max = config.aircraft.cl_max

    return sqrt((2.0 * w) / (rho * s * cl_max))


def minimum_recommended_cruise_speed_m_per_s(
    config: Config,
    stall_margin: float = 1.3,
) -> float:
    return stall_margin * stall_speed_m_per_s(config)