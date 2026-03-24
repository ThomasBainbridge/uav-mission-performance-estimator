from __future__ import annotations

from math import isfinite

from uav_mpe.models import Config
from uav_mpe.operating_points import (
    get_best_endurance_operating_point,
    get_best_range_operating_point,
    get_best_wind_adjusted_range_operating_point,
)
from uav_mpe.performance import (
    battery_available_for_mission_wh,
    electrical_power_required_watts,
    wind_adjusted_ground_speed_m_per_s,
)


def _config_with_flight_conditions(
    config: Config,
    airspeed_m_per_s: float,
    wind_speed_m_per_s: float,
) -> Config:
    updated = config.model_copy(deep=True)
    updated.mission.cruise_speed_m_per_s = airspeed_m_per_s
    updated.environment.wind_speed_m_per_s = wind_speed_m_per_s
    return updated


def evaluate_cruise_segment_fixed_speed(
    config: Config,
    segment_name: str,
    distance_km: float,
    wind_speed_m_per_s: float = 0.0,
) -> dict[str, float | str]:
    airspeed_m_per_s = config.mission.cruise_speed_m_per_s
    segment_config = _config_with_flight_conditions(
        config,
        airspeed_m_per_s=airspeed_m_per_s,
        wind_speed_m_per_s=wind_speed_m_per_s,
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
        "airspeed_m_per_s": airspeed_m_per_s,
        "ground_speed_m_per_s": ground_speed_m_per_s,
        "electrical_power_w": electrical_power_w,
        "time_h": time_h,
        "energy_used_wh": energy_used_wh,
    }


def evaluate_cruise_segment_best_range(
    config: Config,
    segment_name: str,
    distance_km: float,
    wind_speed_m_per_s: float = 0.0,
    max_speed_m_per_s: float = 40.0,
    num_points: int = 100,
) -> dict[str, float | str]:
    config_for_selection = config.model_copy(deep=True)
    config_for_selection.environment.wind_speed_m_per_s = wind_speed_m_per_s

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
        "airspeed_m_per_s": airspeed_m_per_s,
        "ground_speed_m_per_s": ground_speed_m_per_s,
        "electrical_power_w": electrical_power_w,
        "time_h": time_h,
        "energy_used_wh": energy_used_wh,
    }


def evaluate_cruise_segment_best_wind_adjusted_range(
    config: Config,
    segment_name: str,
    distance_km: float,
    wind_speed_m_per_s: float = 0.0,
    max_speed_m_per_s: float = 40.0,
    num_points: int = 100,
) -> dict[str, float | str]:
    config_for_selection = config.model_copy(deep=True)
    config_for_selection.environment.wind_speed_m_per_s = wind_speed_m_per_s

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
        "airspeed_m_per_s": airspeed_m_per_s,
        "ground_speed_m_per_s": ground_speed_m_per_s,
        "electrical_power_w": electrical_power_w,
        "time_h": time_h,
        "energy_used_wh": energy_used_wh,
    }


def evaluate_loiter_segment_best_endurance(
    config: Config,
    segment_name: str,
    loiter_duration_min: float,
    max_speed_m_per_s: float = 40.0,
    num_points: int = 100,
) -> dict[str, float | str]:
    op = get_best_endurance_operating_point(
        config,
        max_speed_m_per_s=max_speed_m_per_s,
        num_points=num_points,
    )

    airspeed_m_per_s = op["airspeed_m_per_s"]
    electrical_power_w = op["electrical_power_w"]
    time_h = loiter_duration_min / 60.0
    energy_used_wh = electrical_power_w * time_h

    return {
        "segment_name": segment_name,
        "segment_type": "loiter",
        "speed_mode": "best_endurance",
        "duration_min": loiter_duration_min,
        "airspeed_m_per_s": airspeed_m_per_s,
        "electrical_power_w": electrical_power_w,
        "time_h": time_h,
        "energy_used_wh": energy_used_wh,
    }


def evaluate_simple_mission_profile(
    config: Config,
    outbound_distance_km: float,
    loiter_duration_min: float | None = None,
    return_distance_km: float | None = None,
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

    if cruise_mode == "fixed_speed":
        outbound = evaluate_cruise_segment_fixed_speed(
            config,
            segment_name="outbound",
            distance_km=outbound_distance_km,
            wind_speed_m_per_s=outbound_wind_speed_m_per_s,
        )
    elif cruise_mode == "best_range":
        outbound = evaluate_cruise_segment_best_range(
            config,
            segment_name="outbound",
            distance_km=outbound_distance_km,
            wind_speed_m_per_s=outbound_wind_speed_m_per_s,
            max_speed_m_per_s=max_speed_m_per_s,
            num_points=num_points,
        )
    elif cruise_mode == "best_wind_adjusted_range":
        outbound = evaluate_cruise_segment_best_wind_adjusted_range(
            config,
            segment_name="outbound",
            distance_km=outbound_distance_km,
            wind_speed_m_per_s=outbound_wind_speed_m_per_s,
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
            )
        elif cruise_mode == "best_range":
            return_leg = evaluate_cruise_segment_best_range(
                config,
                segment_name="return",
                distance_km=return_distance_km,
                wind_speed_m_per_s=return_wind_speed_m_per_s,
                max_speed_m_per_s=max_speed_m_per_s,
                num_points=num_points,
            )
        else:
            return_leg = evaluate_cruise_segment_best_wind_adjusted_range(
                config,
                segment_name="return",
                distance_km=return_distance_km,
                wind_speed_m_per_s=return_wind_speed_m_per_s,
                max_speed_m_per_s=max_speed_m_per_s,
                num_points=num_points,
            )

        add_segment(return_leg)

    total_time_h = 0.0
    total_energy_used_wh = 0.0

    for segment in segments:
        segment_time_h = segment["time_h"]
        segment_energy_wh = segment["energy_used_wh"]

        if not isinstance(segment_time_h, float) or not isinstance(segment_energy_wh, float):
            raise TypeError("Segment time_h and energy_used_wh must be floats.")

        total_time_h += segment_time_h
        total_energy_used_wh += segment_energy_wh

    mission_feasible = isfinite(total_time_h) and isfinite(total_energy_used_wh) and remaining_energy_wh >= 0.0

    return {
        "available_energy_wh": available_energy_wh,
        "total_time_h": total_time_h,
        "total_energy_used_wh": total_energy_used_wh,
        "remaining_energy_wh": remaining_energy_wh,
        "mission_feasible": mission_feasible,
        "segments": segments,
    }