from __future__ import annotations

from math import isfinite

from uav_mpe.climb import (
    climb_energy_wh,
    climb_time_hours,
    climb_total_electrical_power_watts,
)
from uav_mpe.descent import (
    descent_energy_wh,
    descent_time_hours,
    descent_total_electrical_power_watts,
)
from uav_mpe.models import Config
from uav_mpe.operating_points import (
    get_best_endurance_operating_point,
    get_best_range_operating_point,
    get_best_wind_adjusted_range_operating_point,
)
from uav_mpe.performance import (
    battery_available_for_mission_wh,
    electrical_power_required_watts,
    hotel_load_watts,
    payload_load_watts,
    non_propulsive_electrical_load_watts,
    wind_adjusted_ground_speed_m_per_s,
)


def _config_with_flight_conditions(
    config: Config,
    airspeed_m_per_s: float,
    wind_speed_m_per_s: float,
    altitude_m: float | None = None,
) -> Config:
    updated = config.model_copy(deep=True)
    updated.mission.cruise_speed_m_per_s = airspeed_m_per_s
    updated.environment.wind_speed_m_per_s = wind_speed_m_per_s

    if altitude_m is not None:
        updated.environment.altitude_m = altitude_m
        updated.environment.air_density_kg_per_m3 = None

    return updated


def _segment_breakdown_fields(
    segment_config: Config,
    total_electrical_power_w: float,
    time_h: float,
) -> dict[str, float]:
    hotel_load_w = hotel_load_watts(segment_config)
    payload_load_w = payload_load_watts(segment_config)
    non_propulsive_load_w = non_propulsive_electrical_load_watts(segment_config)
    propulsion_electrical_power_w = total_electrical_power_w - non_propulsive_load_w

    return {
        "propulsion_electrical_power_w": propulsion_electrical_power_w,
        "hotel_load_w": hotel_load_w,
        "payload_load_w": payload_load_w,
        "non_propulsive_electrical_load_w": non_propulsive_load_w,
        "propulsion_energy_wh": propulsion_electrical_power_w * time_h,
        "hotel_energy_wh": hotel_load_w * time_h,
        "payload_energy_wh": payload_load_w * time_h,
        "non_propulsive_energy_wh": non_propulsive_load_w * time_h,
    }


def evaluate_climb_segment(
    config: Config,
    segment_name: str,
    climb_altitude_m: float,
    climb_rate_m_per_s: float,
) -> dict[str, float | str]:
    electrical_power_w = climb_total_electrical_power_watts(
        config,
        climb_rate_m_per_s=climb_rate_m_per_s,
    )
    time_h = climb_time_hours(
        climb_altitude_m=climb_altitude_m,
        climb_rate_m_per_s=climb_rate_m_per_s,
    )
    energy_used_wh = climb_energy_wh(
        config,
        climb_altitude_m=climb_altitude_m,
        climb_rate_m_per_s=climb_rate_m_per_s,
    )

    return {
        "segment_name": segment_name,
        "segment_type": "climb",
        "speed_mode": "fixed_climb",
        "climb_altitude_m": climb_altitude_m,
        "climb_rate_m_per_s": climb_rate_m_per_s,
        "electrical_power_w": electrical_power_w,
        "time_h": time_h,
        "energy_used_wh": energy_used_wh,
        **_segment_breakdown_fields(config, electrical_power_w, time_h),
    }


def evaluate_descent_segment(
    config: Config,
    segment_name: str,
    descent_altitude_m: float,
    descent_rate_m_per_s: float,
    descent_power_factor: float,
) -> dict[str, float | str]:
    electrical_power_w = descent_total_electrical_power_watts(
        config,
        descent_power_factor=descent_power_factor,
    )
    time_h = descent_time_hours(
        descent_altitude_m=descent_altitude_m,
        descent_rate_m_per_s=descent_rate_m_per_s,
    )
    energy_used_wh = descent_energy_wh(
        config,
        descent_altitude_m=descent_altitude_m,
        descent_rate_m_per_s=descent_rate_m_per_s,
        descent_power_factor=descent_power_factor,
    )

    return {
        "segment_name": segment_name,
        "segment_type": "descent",
        "speed_mode": "fixed_descent",
        "descent_altitude_m": descent_altitude_m,
        "descent_rate_m_per_s": descent_rate_m_per_s,
        "descent_power_factor": descent_power_factor,
        "electrical_power_w": electrical_power_w,
        "time_h": time_h,
        "energy_used_wh": energy_used_wh,
        **_segment_breakdown_fields(config, electrical_power_w, time_h),
    }


def evaluate_cruise_segment_fixed_speed(
    config: Config,
    segment_name: str,
    distance_km: float,
    wind_speed_m_per_s: float = 0.0,
    altitude_m: float | None = None,
) -> dict[str, float | str]:
    airspeed_m_per_s = config.mission.cruise_speed_m_per_s
    segment_config = _config_with_flight_conditions(
        config,
        airspeed_m_per_s=airspeed_m_per_s,
        wind_speed_m_per_s=wind_speed_m_per_s,
        altitude_m=altitude_m,
    )

    electrical_power_w = electrical_power_required_watts(segment_config)
    ground_speed_m_per_s = wind_adjusted_ground_speed_m_per_s(segment_config)

    if ground_speed_m_per_s <= 0.0:
        time_h = float("inf")
        energy_used_wh = float("inf")
    else:
        ground_speed_km_per_h = ground_speed_m_per_s * 3.6
        time_h = distance_km / ground_speed_km_per_h
        energy_used_wh = electrical_power_w * time_h

    return {
        "segment_name": segment_name,
        "segment_type": "cruise",
        "speed_mode": "fixed_speed",
        "distance_km": distance_km,
        "altitude_m": altitude_m,
        "airspeed_m_per_s": airspeed_m_per_s,
        "ground_speed_m_per_s": ground_speed_m_per_s,
        "electrical_power_w": electrical_power_w,
        "time_h": time_h,
        "energy_used_wh": energy_used_wh,
        **_segment_breakdown_fields(segment_config, electrical_power_w, time_h),
    }


def evaluate_cruise_segment_best_range(
    config: Config,
    segment_name: str,
    distance_km: float,
    wind_speed_m_per_s: float = 0.0,
    altitude_m: float | None = None,
    max_speed_m_per_s: float = 40.0,
    num_points: int = 100,
) -> dict[str, float | str]:
    config_for_selection = config.model_copy(deep=True)
    config_for_selection.environment.wind_speed_m_per_s = wind_speed_m_per_s
    if altitude_m is not None:
        config_for_selection.environment.altitude_m = altitude_m
        config_for_selection.environment.air_density_kg_per_m3 = None

    op = get_best_range_operating_point(
        config_for_selection,
        max_speed_m_per_s=max_speed_m_per_s,
        num_points=num_points,
    )

    airspeed_m_per_s = op["airspeed_m_per_s"]
    segment_config = _config_with_flight_conditions(
        config,
        airspeed_m_per_s=airspeed_m_per_s,
        wind_speed_m_per_s=wind_speed_m_per_s,
        altitude_m=altitude_m,
    )

    electrical_power_w = electrical_power_required_watts(segment_config)
    ground_speed_m_per_s = wind_adjusted_ground_speed_m_per_s(segment_config)

    if ground_speed_m_per_s <= 0.0:
        time_h = float("inf")
        energy_used_wh = float("inf")
    else:
        ground_speed_km_per_h = ground_speed_m_per_s * 3.6
        time_h = distance_km / ground_speed_km_per_h
        energy_used_wh = electrical_power_w * time_h

    return {
        "segment_name": segment_name,
        "segment_type": "cruise",
        "speed_mode": "best_range",
        "distance_km": distance_km,
        "altitude_m": altitude_m,
        "airspeed_m_per_s": airspeed_m_per_s,
        "ground_speed_m_per_s": ground_speed_m_per_s,
        "electrical_power_w": electrical_power_w,
        "time_h": time_h,
        "energy_used_wh": energy_used_wh,
        **_segment_breakdown_fields(segment_config, electrical_power_w, time_h),
    }


def evaluate_cruise_segment_best_wind_adjusted_range(
    config: Config,
    segment_name: str,
    distance_km: float,
    wind_speed_m_per_s: float = 0.0,
    altitude_m: float | None = None,
    max_speed_m_per_s: float = 40.0,
    num_points: int = 100,
) -> dict[str, float | str]:
    config_for_selection = config.model_copy(deep=True)
    config_for_selection.environment.wind_speed_m_per_s = wind_speed_m_per_s
    if altitude_m is not None:
        config_for_selection.environment.altitude_m = altitude_m
        config_for_selection.environment.air_density_kg_per_m3 = None

    op = get_best_wind_adjusted_range_operating_point(
        config_for_selection,
        max_speed_m_per_s=max_speed_m_per_s,
        num_points=num_points,
    )

    airspeed_m_per_s = op["airspeed_m_per_s"]
    segment_config = _config_with_flight_conditions(
        config,
        airspeed_m_per_s=airspeed_m_per_s,
        wind_speed_m_per_s=wind_speed_m_per_s,
        altitude_m=altitude_m,
    )

    electrical_power_w = electrical_power_required_watts(segment_config)
    ground_speed_m_per_s = wind_adjusted_ground_speed_m_per_s(segment_config)

    if ground_speed_m_per_s <= 0.0:
        time_h = float("inf")
        energy_used_wh = float("inf")
    else:
        ground_speed_km_per_h = ground_speed_m_per_s * 3.6
        time_h = distance_km / ground_speed_km_per_h
        energy_used_wh = electrical_power_w * time_h

    return {
        "segment_name": segment_name,
        "segment_type": "cruise",
        "speed_mode": "best_wind_adjusted_range",
        "distance_km": distance_km,
        "altitude_m": altitude_m,
        "airspeed_m_per_s": airspeed_m_per_s,
        "ground_speed_m_per_s": ground_speed_m_per_s,
        "electrical_power_w": electrical_power_w,
        "time_h": time_h,
        "energy_used_wh": energy_used_wh,
        **_segment_breakdown_fields(segment_config, electrical_power_w, time_h),
    }


def evaluate_loiter_segment_best_endurance(
    config: Config,
    segment_name: str,
    loiter_duration_min: float,
    altitude_m: float | None = None,
    max_speed_m_per_s: float = 40.0,
    num_points: int = 100,
) -> dict[str, float | str]:
    config_for_selection = config.model_copy(deep=True)

    if altitude_m is not None:
        config_for_selection.environment.altitude_m = altitude_m
        config_for_selection.environment.air_density_kg_per_m3 = None

    if config_for_selection.aircraft.loiter_payload_load_w is not None:
        config_for_selection.aircraft.payload_load_w = (
            config_for_selection.aircraft.loiter_payload_load_w
        )

    op = get_best_endurance_operating_point(
        config_for_selection,
        max_speed_m_per_s=max_speed_m_per_s,
        num_points=num_points,
    )

    airspeed_m_per_s = op["airspeed_m_per_s"]
    electrical_power_w = op["electrical_power_w"]
    time_h = loiter_duration_min / 60.0
    energy_used_wh = electrical_power_w * time_h

    config_for_breakdown = config_for_selection.model_copy(deep=True)
    config_for_breakdown.mission.cruise_speed_m_per_s = airspeed_m_per_s

    return {
        "segment_name": segment_name,
        "segment_type": "loiter",
        "speed_mode": "best_endurance",
        "duration_min": loiter_duration_min,
        "altitude_m": altitude_m,
        "airspeed_m_per_s": airspeed_m_per_s,
        "electrical_power_w": electrical_power_w,
        "time_h": time_h,
        "energy_used_wh": energy_used_wh,
        **_segment_breakdown_fields(config_for_breakdown, electrical_power_w, time_h),
    }


def evaluate_simple_mission_profile(
    config: Config,
    outbound_distance_km: float,
    climb_altitude_m: float | None = None,
    climb_rate_m_per_s: float | None = None,
    loiter_duration_min: float | None = None,
    return_distance_km: float | None = None,
    descent_altitude_m: float | None = None,
    descent_rate_m_per_s: float | None = None,
    descent_power_factor: float = 0.7,
    outbound_altitude_m: float | None = None,
    loiter_altitude_m: float | None = None,
    return_altitude_m: float | None = None,
    outbound_wind_speed_m_per_s: float = 0.0,
    return_wind_speed_m_per_s: float = 0.0,
    cruise_mode: str = "best_range",
    max_speed_m_per_s: float = 40.0,
    num_points: int = 100,
) -> dict[str, object]:
    if outbound_distance_km <= 0.0:
        raise ValueError("outbound_distance_km must be greater than 0.")
    if return_distance_km is not None and return_distance_km <= 0.0:
        raise ValueError("return_distance_km must be greater than 0 if provided.")
    if loiter_duration_min is not None and loiter_duration_min <= 0.0:
        raise ValueError("loiter_duration_min must be greater than 0 if provided.")

    available_energy_wh = battery_available_for_mission_wh(config)
    remaining_energy_wh = available_energy_wh
    segments: list[dict[str, float | str]] = []

    if (climb_altitude_m is None) ^ (climb_rate_m_per_s is None):
        raise ValueError(
            "climb_altitude_m and climb_rate_m_per_s must both be provided, or both be None."
        )

    if (descent_altitude_m is None) ^ (descent_rate_m_per_s is None):
        raise ValueError(
            "descent_altitude_m and descent_rate_m_per_s must both be provided, or both be None."
        )

    def add_segment(segment: dict[str, float | str]) -> None:
        nonlocal remaining_energy_wh

        energy_used_wh = segment["energy_used_wh"]

        if not isinstance(energy_used_wh, float):
            raise TypeError("Segment energy_used_wh must be a float.")

        if isfinite(energy_used_wh):
            remaining_energy_wh -= energy_used_wh
        else:
            remaining_energy_wh = float("-inf")

        segment["remaining_energy_wh_after_segment"] = remaining_energy_wh
        segments.append(segment)

    if climb_altitude_m is not None and climb_rate_m_per_s is not None:
        climb_segment = evaluate_climb_segment(
            config,
            segment_name="climb",
            climb_altitude_m=climb_altitude_m,
            climb_rate_m_per_s=climb_rate_m_per_s,
        )
        add_segment(climb_segment)

    if cruise_mode == "fixed_speed":
        outbound = evaluate_cruise_segment_fixed_speed(
            config,
            segment_name="outbound",
            distance_km=outbound_distance_km,
            wind_speed_m_per_s=outbound_wind_speed_m_per_s,
            altitude_m=outbound_altitude_m,
        )
    elif cruise_mode == "best_range":
        outbound = evaluate_cruise_segment_best_range(
            config,
            segment_name="outbound",
            distance_km=outbound_distance_km,
            wind_speed_m_per_s=outbound_wind_speed_m_per_s,
            altitude_m=outbound_altitude_m,
            max_speed_m_per_s=max_speed_m_per_s,
            num_points=num_points,
        )
    elif cruise_mode == "best_wind_adjusted_range":
        outbound = evaluate_cruise_segment_best_wind_adjusted_range(
            config,
            segment_name="outbound",
            distance_km=outbound_distance_km,
            wind_speed_m_per_s=outbound_wind_speed_m_per_s,
            altitude_m=outbound_altitude_m,
            max_speed_m_per_s=max_speed_m_per_s,
            num_points=num_points,
        )
    else:
        raise ValueError(
            "cruise_mode must be 'fixed_speed', 'best_range', or "
            "'best_wind_adjusted_range'."
        )

    add_segment(outbound)

    if loiter_duration_min is not None:
        loiter = evaluate_loiter_segment_best_endurance(
            config,
            segment_name="loiter",
            loiter_duration_min=loiter_duration_min,
            altitude_m=loiter_altitude_m,
            max_speed_m_per_s=max_speed_m_per_s,
            num_points=num_points,
        )
        add_segment(loiter)

    if return_distance_km is not None:
        if cruise_mode == "fixed_speed":
            return_leg = evaluate_cruise_segment_fixed_speed(
                config,
                segment_name="return",
                distance_km=return_distance_km,
                wind_speed_m_per_s=return_wind_speed_m_per_s,
                altitude_m=return_altitude_m,
            )
        elif cruise_mode == "best_range":
            return_leg = evaluate_cruise_segment_best_range(
                config,
                segment_name="return",
                distance_km=return_distance_km,
                wind_speed_m_per_s=return_wind_speed_m_per_s,
                altitude_m=return_altitude_m,
                max_speed_m_per_s=max_speed_m_per_s,
                num_points=num_points,
            )
        else:
            return_leg = evaluate_cruise_segment_best_wind_adjusted_range(
                config,
                segment_name="return",
                distance_km=return_distance_km,
                wind_speed_m_per_s=return_wind_speed_m_per_s,
                altitude_m=return_altitude_m,
                max_speed_m_per_s=max_speed_m_per_s,
                num_points=num_points,
            )

        add_segment(return_leg)

    if descent_altitude_m is not None and descent_rate_m_per_s is not None:
        descent_segment = evaluate_descent_segment(
            config,
            segment_name="descent",
            descent_altitude_m=descent_altitude_m,
            descent_rate_m_per_s=descent_rate_m_per_s,
            descent_power_factor=descent_power_factor,
        )
        add_segment(descent_segment)

    total_time_h = 0.0
    total_energy_used_wh = 0.0
    total_propulsion_energy_wh = 0.0
    total_hotel_energy_wh = 0.0
    total_payload_energy_wh = 0.0
    total_non_propulsive_energy_wh = 0.0

    for segment in segments:
        segment_time_h = segment["time_h"]
        segment_energy_wh = segment["energy_used_wh"]
        segment_propulsion_energy_wh = segment["propulsion_energy_wh"]
        segment_hotel_energy_wh = segment["hotel_energy_wh"]
        segment_payload_energy_wh = segment["payload_energy_wh"]
        segment_non_propulsive_energy_wh = segment["non_propulsive_energy_wh"]

        if not isinstance(segment_time_h, float) or not isinstance(segment_energy_wh, float):
            raise TypeError("Segment time_h and energy_used_wh must be floats.")

        total_time_h += segment_time_h
        total_energy_used_wh += segment_energy_wh
        total_propulsion_energy_wh += float(segment_propulsion_energy_wh)
        total_hotel_energy_wh += float(segment_hotel_energy_wh)
        total_payload_energy_wh += float(segment_payload_energy_wh)
        total_non_propulsive_energy_wh += float(segment_non_propulsive_energy_wh)

    mission_feasible = (
        isfinite(total_time_h)
        and isfinite(total_energy_used_wh)
        and remaining_energy_wh >= 0.0
    )

    return {
        "available_energy_wh": available_energy_wh,
        "total_time_h": total_time_h,
        "total_energy_used_wh": total_energy_used_wh,
        "total_propulsion_energy_wh": total_propulsion_energy_wh,
        "total_hotel_energy_wh": total_hotel_energy_wh,
        "total_payload_energy_wh": total_payload_energy_wh,
        "total_non_propulsive_energy_wh": total_non_propulsive_energy_wh,
        "remaining_energy_wh": remaining_energy_wh,
        "mission_feasible": mission_feasible,
        "segments": segments,
    }