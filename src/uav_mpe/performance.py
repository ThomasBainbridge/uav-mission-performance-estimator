from math import pi, sqrt

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


def lift_coefficient(config: Config) -> float:
    w = weight_newtons(config)
    rho = config.environment.air_density_kg_per_m3
    v = config.mission.cruise_speed_m_per_s
    s = config.aircraft.wing_area_m2

    return w / (0.5 * rho * v**2 * s)


def induced_drag_factor(config: Config) -> float:
    ar = config.aircraft.aspect_ratio
    e = config.aircraft.oswald_efficiency

    return 1.0 / (pi * e * ar)


def drag_coefficient(config: Config) -> float:
    cd0 = config.aircraft.cd0
    cl = lift_coefficient(config)
    k = induced_drag_factor(config)

    return cd0 + k * cl**2


def drag_force_newtons(config: Config) -> float:
    rho = config.environment.air_density_kg_per_m3
    v = config.mission.cruise_speed_m_per_s
    s = config.aircraft.wing_area_m2
    cd = drag_coefficient(config)

    return 0.5 * rho * v**2 * s * cd


def air_power_required_watts(config: Config) -> float:
    drag = drag_force_newtons(config)
    v = config.mission.cruise_speed_m_per_s

    return drag * v


def electrical_power_required_watts(config: Config) -> float:
    air_power = air_power_required_watts(config)
    eta_total = config.aircraft.eta_total

    return air_power / eta_total


def endurance_seconds(config: Config) -> float:
    available_energy_j = battery_available_for_mission_j(config)
    electrical_power_w = electrical_power_required_watts(config)

    return available_energy_j / electrical_power_w


def endurance_hours(config: Config) -> float:
    return endurance_seconds(config) / 3600.0


def still_air_range_m(config: Config) -> float:
    v = config.mission.cruise_speed_m_per_s
    return v * endurance_seconds(config)


def still_air_range_km(config: Config) -> float:
    return still_air_range_m(config) / 1000.0


def wind_adjusted_ground_speed_m_per_s(config: Config) -> float:
    v = config.mission.cruise_speed_m_per_s
    wind = config.environment.wind_speed_m_per_s  # positive = headwind

    ground_speed = v - wind
    return max(0.0, ground_speed)


def wind_adjusted_range_m(config: Config) -> float:
    ground_speed = wind_adjusted_ground_speed_m_per_s(config)
    return ground_speed * endurance_seconds(config)


def wind_adjusted_range_km(config: Config) -> float:
    return wind_adjusted_range_m(config) / 1000.0