from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import streamlit as st
import yaml

from uav_mpe.atmosphere import get_air_density_kg_per_m3
from uav_mpe.comparison import compare_configurations
from uav_mpe.mission import (
    energy_margin_wh,
    is_mission_feasible,
    range_margin_km,
    required_mission_energy_wh,
    required_mission_time_hours,
)
from uav_mpe.mission_profile import evaluate_simple_mission_profile
from uav_mpe.mission_scenario_comparison import compare_mission_scenarios
from uav_mpe.models import Config
from uav_mpe.operating_points import (
    get_best_endurance_operating_point,
    get_best_range_operating_point,
    get_best_wind_adjusted_range_operating_point,
)
from uav_mpe.performance import (
    air_power_required_watts,
    battery_available_for_mission_wh,
    battery_nominal_energy_wh,
    battery_usable_energy_wh,
    electrical_power_required_watts,
    endurance_hours,
    hotel_load_watts,
    minimum_recommended_cruise_speed_m_per_s,
    non_propulsive_electrical_load_watts,
    payload_load_watts,
    reserve_energy_wh,
    stall_speed_m_per_s,
    still_air_range_km,
    total_mass_kg,
    weight_newtons,
    wind_adjusted_range_km,
)
from uav_mpe.sweeps import build_speed_sweep


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
CONFIG_DIR = PROJECT_ROOT / "configs"

DEFAULT_MISSION_SCENARIO_FILES = [
    str(CONFIG_DIR / "mission_baseline.yaml"),
    str(CONFIG_DIR / "mission_windy.yaml"),
    str(CONFIG_DIR / "mission_loiter.yaml"),
]

TRADE_PARAMETER_OPTIONS = [
    "battery_mass_kg",
    "payload_mass_kg",
    "wing_area_m2",
    "cd0",
    "altitude_m",
    "cruise_speed_m_per_s",
]

TRADE_PARAMETER_LABELS = {
    "battery_mass_kg": "Battery mass [kg]",
    "payload_mass_kg": "Payload mass [kg]",
    "wing_area_m2": "Wing area [m²]",
    "cd0": "Cd0 [-]",
    "altitude_m": "Altitude [m]",
    "cruise_speed_m_per_s": "Cruise speed [m/s]",
}


@st.cache_data
def list_yaml_configs(config_dir: str) -> list[str]:
    return sorted(str(path) for path in Path(config_dir).glob("*.yaml"))


@st.cache_data
def load_config_dict(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config(path: str) -> Config:
    data = load_config_dict(path)
    return Config.model_validate(data)


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def config_to_yaml_bytes(config: Config) -> bytes:
    return yaml.dump(config.model_dump(mode="python"), sort_keys=False).encode("utf-8")


def sanitize_scenario_name(name: str) -> str:
    cleaned = name.strip().lower()
    cleaned = re.sub(r"[^a-z0-9_\- ]", "", cleaned)
    cleaned = cleaned.replace(" ", "_")
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_-")


def save_config_yaml(config: Config, scenario_name: str, config_dir: Path) -> Path:
    safe_name = sanitize_scenario_name(scenario_name)
    if not safe_name:
        raise ValueError("Scenario name must contain at least one letter or number.")

    config_dir.mkdir(parents=True, exist_ok=True)
    output_path = config_dir / f"{safe_name}.yaml"

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(config.model_dump(mode="python"), f, sort_keys=False)

    return output_path


def mission_profile_summary_df(mission_profile: dict[str, object]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "available_energy_wh": float(mission_profile["available_energy_wh"]),
                "total_time_h": float(mission_profile["total_time_h"]),
                "total_energy_used_wh": float(mission_profile["total_energy_used_wh"]),
                "total_propulsion_energy_wh": float(mission_profile["total_propulsion_energy_wh"]),
                "total_hotel_energy_wh": float(mission_profile["total_hotel_energy_wh"]),
                "total_payload_energy_wh": float(mission_profile["total_payload_energy_wh"]),
                "total_non_propulsive_energy_wh": float(mission_profile["total_non_propulsive_energy_wh"]),
                "remaining_energy_wh": float(mission_profile["remaining_energy_wh"]),
                "mission_feasible": bool(mission_profile["mission_feasible"]),
                "number_of_segments": len(mission_profile["segments"]),
            }
        ]
    )


def make_performance_summary(config: Config) -> dict[str, float]:
    return {
        "total_mass_kg": total_mass_kg(config),
        "weight_n": weight_newtons(config),
        "resolved_air_density_kg_per_m3": get_air_density_kg_per_m3(config),
        "stall_speed_m_per_s": stall_speed_m_per_s(config),
        "minimum_recommended_cruise_speed_m_per_s": minimum_recommended_cruise_speed_m_per_s(config),
        "battery_nominal_energy_wh": battery_nominal_energy_wh(config),
        "battery_usable_energy_wh": battery_usable_energy_wh(config),
        "reserve_energy_wh": reserve_energy_wh(config),
        "battery_available_for_mission_wh": battery_available_for_mission_wh(config),
        "hotel_load_w": hotel_load_watts(config),
        "payload_load_w": payload_load_watts(config),
        "non_propulsive_electrical_load_w": non_propulsive_electrical_load_watts(config),
        "electrical_power_required_w": electrical_power_required_watts(config),
        "air_power_required_w": air_power_required_watts(config),
        "endurance_h": endurance_hours(config),
        "still_air_range_km": still_air_range_km(config),
        "wind_adjusted_range_km": wind_adjusted_range_km(config),
    }


def make_operating_points_summary(config: Config) -> pd.DataFrame:
    best_endurance = get_best_endurance_operating_point(
        config,
        max_speed_m_per_s=40.0,
        num_points=120,
    )
    best_range = get_best_range_operating_point(
        config,
        max_speed_m_per_s=40.0,
        num_points=120,
    )
    best_wind = get_best_wind_adjusted_range_operating_point(
        config,
        max_speed_m_per_s=40.0,
        num_points=120,
    )

    rows = [
        {"operating_point": "best_endurance", **best_endurance},
        {"operating_point": "best_still_air_range", **best_range},
        {"operating_point": "best_wind_adjusted_range", **best_wind},
    ]
    return pd.DataFrame(rows)


def make_mission_profile_result(config: Config) -> dict[str, object] | None:
    if config.mission.profile is None:
        return None

    profile = config.mission.profile

    return evaluate_simple_mission_profile(
        config,
        outbound_distance_km=profile.outbound_distance_km,
        climb_altitude_m=profile.climb_altitude_m,
        climb_rate_m_per_s=profile.climb_rate_m_per_s,
        loiter_duration_min=profile.loiter_duration_min,
        return_distance_km=profile.return_distance_km,
        descent_altitude_m=profile.descent_altitude_m,
        descent_rate_m_per_s=profile.descent_rate_m_per_s,
        descent_power_factor=profile.descent_power_factor,
        outbound_altitude_m=profile.outbound_altitude_m,
        loiter_altitude_m=profile.loiter_altitude_m,
        return_altitude_m=profile.return_altitude_m,
        outbound_wind_speed_m_per_s=profile.outbound_wind_speed_m_per_s,
        return_wind_speed_m_per_s=profile.return_wind_speed_m_per_s,
        cruise_mode=profile.cruise_mode,
        max_speed_m_per_s=40.0,
        num_points=120,
    )


def mission_profile_segments_df(mission_profile: dict[str, object]) -> pd.DataFrame:
    segments = mission_profile["segments"]
    if not isinstance(segments, list):
        raise TypeError("mission_profile['segments'] must be a list.")
    return pd.DataFrame(segments)


def mission_profile_display_df(mission_profile: dict[str, object]) -> pd.DataFrame:
    segments = mission_profile["segments"]
    if not isinstance(segments, list):
        raise TypeError("mission_profile['segments'] must be a list.")

    df = pd.DataFrame(segments)

    preferred_columns = [
        "segment_name",
        "segment_type",
        "speed_mode",
        "altitude_m",
        "distance_km",
        "duration_min",
        "airspeed_m_per_s",
        "ground_speed_m_per_s",
        "electrical_power_w",
        "energy_used_wh",
        "remaining_energy_wh_after_segment",
    ]

    available_columns = [col for col in preferred_columns if col in df.columns]
    return df[available_columns]


def make_sweep_df(config: Config) -> pd.DataFrame:
    return build_speed_sweep(
        config,
        max_speed_m_per_s=40.0,
        num_points=120,
        min_speed_m_per_s=stall_speed_m_per_s(config),
    )


def make_mission_energy_df(mission_profile: dict[str, object]) -> pd.DataFrame:
    segments = mission_profile["segments"]
    if not isinstance(segments, list):
        raise TypeError("mission_profile['segments'] must be a list.")

    df = pd.DataFrame(
        {
            "segment_name": [str(segment["segment_name"]) for segment in segments],
            "energy_used_wh": [float(segment["energy_used_wh"]) for segment in segments],
        }
    )
    return df.set_index("segment_name")


def make_mission_energy_breakdown_df(mission_profile: dict[str, object]) -> pd.DataFrame:
    segments = mission_profile["segments"]
    if not isinstance(segments, list):
        raise TypeError("mission_profile['segments'] must be a list.")

    return pd.DataFrame(
        {
            "segment_name": [str(segment["segment_name"]) for segment in segments],
            "propulsion_energy_wh": [float(segment["propulsion_energy_wh"]) for segment in segments],
            "hotel_energy_wh": [float(segment["hotel_energy_wh"]) for segment in segments],
            "payload_energy_wh": [float(segment["payload_energy_wh"]) for segment in segments],
        }
    ).set_index("segment_name")


def make_remaining_energy_df(mission_profile: dict[str, object]) -> pd.DataFrame:
    ...
    segments = mission_profile["segments"]
    if not isinstance(segments, list):
        raise TypeError("mission_profile['segments'] must be a list.")

    available_energy_wh = float(mission_profile["available_energy_wh"])

    labels = ["start"]
    values = [available_energy_wh]

    for segment in segments:
        labels.append(str(segment["segment_name"]))
        values.append(float(segment["remaining_energy_wh_after_segment"]))

    return pd.DataFrame(
        {
            "mission_stage": labels,
            "remaining_energy_wh": values,
        }
    ).set_index("mission_stage")

def make_scenario_display_df(scenario_df: pd.DataFrame) -> pd.DataFrame:
    preferred_columns = [
        "scenario",
        "mission_feasible",
        "available_energy_wh",
        "total_energy_used_wh",
        "remaining_energy_wh",
        "total_time_h",
        "total_propulsion_energy_wh",
        "total_hotel_energy_wh",
        "total_payload_energy_wh",
        "total_non_propulsive_energy_wh",
        "number_of_segments",
        "outbound_distance_km",
        "loiter_duration_min",
        "return_distance_km",
        "cruise_mode",
    ]
    available_columns = [col for col in preferred_columns if col in scenario_df.columns]
    return scenario_df[available_columns]


def make_scenario_energy_balance_chart_df(scenario_df: pd.DataFrame) -> pd.DataFrame:
    cols = [col for col in ["total_energy_used_wh", "remaining_energy_wh"] if col in scenario_df.columns]
    return scenario_df.set_index("scenario")[cols]


def make_scenario_energy_source_chart_df(scenario_df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        col
        for col in [
            "total_propulsion_energy_wh",
            "total_hotel_energy_wh",
            "total_payload_energy_wh",
        ]
        if col in scenario_df.columns
    ]
    return scenario_df.set_index("scenario")[cols]


def make_scenario_time_chart_df(scenario_df: pd.DataFrame) -> pd.DataFrame:
    cols = [col for col in ["total_time_h"] if col in scenario_df.columns]
    return scenario_df.set_index("scenario")[cols]


def make_configuration_display_df(config_df: pd.DataFrame) -> pd.DataFrame:
    preferred_columns = [
        "configuration",
        "total_mass_kg",
        "stall_speed_m_per_s",
        "minimum_recommended_cruise_speed_m_per_s",
        "electrical_power_at_nominal_cruise_w",
        "best_endurance_speed_m_per_s",
        "maximum_endurance_h",
        "best_still_air_range_speed_m_per_s",
        "maximum_still_air_range_km",
        "best_wind_adjusted_range_speed_m_per_s",
        "maximum_wind_adjusted_range_km",
    ]
    available_columns = [col for col in preferred_columns if col in config_df.columns]
    return config_df[available_columns]


def make_configuration_range_chart_df(config_df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        col
        for col in [
            "maximum_still_air_range_km",
            "maximum_wind_adjusted_range_km",
        ]
        if col in config_df.columns
    ]
    return config_df.set_index("configuration")[cols]


def make_configuration_endurance_chart_df(config_df: pd.DataFrame) -> pd.DataFrame:
    cols = [col for col in ["maximum_endurance_h"] if col in config_df.columns]
    return config_df.set_index("configuration")[cols]


def make_sweep_chart_df(sweep_df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return sweep_df[["airspeed_m_per_s", *cols]].set_index("airspeed_m_per_s")


def set_trade_study_parameter(config: Config, parameter_name: str, value: float) -> Config:
    updated = config.model_copy(deep=True)

    if parameter_name == "battery_mass_kg":
        updated.aircraft.battery_mass_kg = value
    elif parameter_name == "payload_mass_kg":
        updated.aircraft.payload_mass_kg = value
    elif parameter_name == "wing_area_m2":
        updated.aircraft.wing_area_m2 = value
    elif parameter_name == "cd0":
        updated.aircraft.cd0 = value
    elif parameter_name == "altitude_m":
        updated.environment.altitude_m = value
        updated.environment.air_density_kg_per_m3 = None
    elif parameter_name == "cruise_speed_m_per_s":
        updated.mission.cruise_speed_m_per_s = value
    else:
        raise ValueError(f"Unsupported trade study parameter: {parameter_name}")

    return updated


def build_trade_study_df(
    base_config: Config,
    parameter_name: str,
    min_value: float,
    max_value: float,
    num_points: int,
) -> pd.DataFrame:
    values = pd.Series(
        [min_value + i * (max_value - min_value) / (num_points - 1) for i in range(num_points)]
    )

    rows: list[dict[str, float]] = []

    for value in values:
        config = set_trade_study_parameter(base_config, parameter_name, float(value))
        summary = make_performance_summary(config)
        mission_profile = make_mission_profile_result(config)

        remaining_energy_wh_value = float("nan")
        mission_feasible_flag = float("nan")

        if mission_profile is not None:
            remaining_energy_wh_value = float(mission_profile["remaining_energy_wh"])
            mission_feasible_flag = 1.0 if bool(mission_profile["mission_feasible"]) else 0.0

        rows.append(
            {
                "parameter_value": float(value),
                "still_air_range_km": summary["still_air_range_km"],
                "wind_adjusted_range_km": summary["wind_adjusted_range_km"],
                "endurance_h": summary["endurance_h"],
                "stall_speed_m_per_s": summary["stall_speed_m_per_s"],
                "electrical_power_required_w": summary["electrical_power_required_w"],
                "remaining_energy_wh": remaining_energy_wh_value,
                "mission_feasible_flag": mission_feasible_flag,
            }
        )

    return pd.DataFrame(rows)


def init_state_from_config(config: Config) -> None:
    st.session_state["payload_mass_kg"] = float(config.aircraft.payload_mass_kg)
    st.session_state["battery_mass_kg"] = float(config.aircraft.battery_mass_kg)
    st.session_state["battery_specific_energy_wh_per_kg"] = float(config.aircraft.battery_specific_energy_wh_per_kg)
    st.session_state["wing_area_m2"] = float(config.aircraft.wing_area_m2)
    st.session_state["aspect_ratio"] = float(config.aircraft.aspect_ratio)
    st.session_state["cd0"] = float(config.aircraft.cd0)
    st.session_state["cl_max"] = float(config.aircraft.cl_max)
    st.session_state["eta_total"] = float(config.aircraft.eta_total)
    st.session_state["hotel_load_w"] = float(config.aircraft.hotel_load_w)
    st.session_state["payload_load_w"] = float(config.aircraft.payload_load_w)
    st.session_state["use_loiter_payload_override"] = config.aircraft.loiter_payload_load_w is not None
    st.session_state["loiter_payload_load_w"] = (
        float(config.aircraft.loiter_payload_load_w)
        if config.aircraft.loiter_payload_load_w is not None
        else float(config.aircraft.payload_load_w)
    )

    st.session_state["altitude_m"] = float(config.environment.altitude_m or 0.0)
    st.session_state["general_wind_speed_m_per_s"] = float(config.environment.wind_speed_m_per_s)

    st.session_state["cruise_speed_m_per_s"] = float(config.mission.cruise_speed_m_per_s)
    st.session_state["use_required_distance"] = config.mission.required_distance_km is not None
    st.session_state["required_distance_km"] = (
        float(config.mission.required_distance_km) if config.mission.required_distance_km is not None else 100.0
    )
    st.session_state["reserve_fraction"] = float(config.mission.reserve_fraction)
    st.session_state["use_fixed_reserve_energy"] = config.mission.reserve_energy_wh is not None
    st.session_state["reserve_energy_wh"] = (
        float(config.mission.reserve_energy_wh) if config.mission.reserve_energy_wh is not None else 25.0
    )

    if config.mission.profile is not None:
        st.session_state["climb_altitude_m"] = (
            float(config.mission.profile.climb_altitude_m)
            if config.mission.profile.climb_altitude_m is not None
            else 500.0
        )
        st.session_state["climb_rate_m_per_s"] = (
            float(config.mission.profile.climb_rate_m_per_s)
            if config.mission.profile.climb_rate_m_per_s is not None
            else 2.0
        )
        st.session_state["use_climb_segment"] = (
            config.mission.profile.climb_altitude_m is not None
            and config.mission.profile.climb_rate_m_per_s is not None
        )

        st.session_state["outbound_distance_km"] = float(config.mission.profile.outbound_distance_km)
        st.session_state["outbound_altitude_m"] = (
            float(config.mission.profile.outbound_altitude_m)
            if config.mission.profile.outbound_altitude_m is not None
            else float(config.environment.altitude_m or 0.0)
        )

        st.session_state["use_loiter"] = config.mission.profile.loiter_duration_min is not None
        st.session_state["loiter_duration_min"] = (
            float(config.mission.profile.loiter_duration_min)
            if config.mission.profile.loiter_duration_min is not None
            else 15.0
        )
        st.session_state["loiter_altitude_m"] = (
            float(config.mission.profile.loiter_altitude_m)
            if config.mission.profile.loiter_altitude_m is not None
            else float(config.environment.altitude_m or 0.0)
        )

        st.session_state["use_return"] = config.mission.profile.return_distance_km is not None
        st.session_state["return_distance_km"] = (
            float(config.mission.profile.return_distance_km)
            if config.mission.profile.return_distance_km is not None
            else 25.0
        )
        st.session_state["return_altitude_m"] = (
            float(config.mission.profile.return_altitude_m)
            if config.mission.profile.return_altitude_m is not None
            else float(config.environment.altitude_m or 0.0)
        )

        st.session_state["use_descent_segment"] = (
            config.mission.profile.descent_altitude_m is not None
            and config.mission.profile.descent_rate_m_per_s is not None
        )
        st.session_state["descent_altitude_m"] = (
            float(config.mission.profile.descent_altitude_m)
            if config.mission.profile.descent_altitude_m is not None
            else 500.0
        )
        st.session_state["descent_rate_m_per_s"] = (
            float(config.mission.profile.descent_rate_m_per_s)
            if config.mission.profile.descent_rate_m_per_s is not None
            else 2.5
        )
        st.session_state["descent_power_factor"] = float(config.mission.profile.descent_power_factor)

        st.session_state["outbound_wind_speed_m_per_s"] = float(config.mission.profile.outbound_wind_speed_m_per_s)
        st.session_state["return_wind_speed_m_per_s"] = float(config.mission.profile.return_wind_speed_m_per_s)
        st.session_state["cruise_mode"] = config.mission.profile.cruise_mode


st.set_page_config(
    page_title="UAV Mission Performance Estimator",
    layout="wide",
)

st.title("UAV Mission Performance Estimator")


config_options = list_yaml_configs(str(CONFIG_DIR))

with st.sidebar:
    st.header("Configuration")
    selected_config = st.selectbox("Select YAML config", options=config_options)

base_config = load_config(selected_config)

config_changed = st.session_state.get("loaded_config_path") != selected_config
if config_changed:
    st.session_state["loaded_config_path"] = selected_config
    init_state_from_config(base_config)

with st.sidebar:
    st.markdown("### Case controls")
    if st.button("Reset all edits to selected base config"):
        init_state_from_config(base_config)
        st.rerun()

    st.caption("Edits below affect the active case only until you save a named scenario.")

    st.subheader("Aircraft")
    st.number_input("Payload mass [kg]", min_value=0.0, step=0.1, key="payload_mass_kg")
    st.number_input("Battery mass [kg]", min_value=0.1, step=0.1, key="battery_mass_kg")
    st.number_input("Battery specific energy [Wh/kg]", min_value=50.0, step=10.0, key="battery_specific_energy_wh_per_kg")
    st.number_input("Wing area [m²]", min_value=0.1, step=0.05, key="wing_area_m2")
    st.number_input("Aspect ratio [-]", min_value=1.0, step=0.5, key="aspect_ratio")
    st.number_input("Cd0 [-]", min_value=0.001, step=0.001, format="%.3f", key="cd0")
    st.number_input("Cl_max [-]", min_value=0.1, step=0.05, key="cl_max")
    st.number_input("Total propulsion efficiency [-]", min_value=0.05, max_value=1.0, step=0.01, format="%.2f", key="eta_total")
    st.number_input("Hotel load [W]", min_value=0.0, step=1.0, key="hotel_load_w")
    st.number_input("Payload load [W]", min_value=0.0, step=1.0, key="payload_load_w")
    st.checkbox("Use loiter payload override", key="use_loiter_payload_override")
    st.number_input(
        "Loiter payload override [W]",
        min_value=0.0,
        step=1.0,
        key="loiter_payload_load_w",
        disabled=not st.session_state["use_loiter_payload_override"],
    )

    st.subheader("Environment")
    st.number_input("Global/base altitude [m]", min_value=0.0, step=100.0, key="altitude_m", help="Used as the default altitude when a segment-specific altitude is not set.")
    st.number_input("General wind speed [m/s]", step=1.0, key="general_wind_speed_m_per_s")

    st.subheader("Mission")
    st.number_input("Cruise speed [m/s]", min_value=1.0, step=0.5, key="cruise_speed_m_per_s")
    st.checkbox("Use required mission distance", key="use_required_distance")
    st.number_input("Required mission distance [km]", min_value=1.0, step=5.0, key="required_distance_km", disabled=not st.session_state["use_required_distance"])

    st.number_input("Reserve fraction [-]", min_value=0.0, max_value=0.95, step=0.01, format="%.2f", key="reserve_fraction")
    st.checkbox("Use fixed reserve energy override", key="use_fixed_reserve_energy")
    st.number_input("Reserve energy [Wh]", min_value=0.0, step=5.0, key="reserve_energy_wh", disabled=not st.session_state["use_fixed_reserve_energy"])

    if base_config.mission.profile is not None:
        st.subheader("Mission profile")

        st.checkbox("Use climb segment", key="use_climb_segment")
        st.number_input("Climb altitude [m]", min_value=0.0, step=100.0, key="climb_altitude_m", disabled=not st.session_state["use_climb_segment"])
        st.number_input("Climb rate [m/s]", min_value=0.1, step=0.1, key="climb_rate_m_per_s", disabled=not st.session_state["use_climb_segment"])

        st.number_input("Outbound distance [km]", min_value=1.0, step=1.0, key="outbound_distance_km")
        st.number_input("Outbound altitude [m]", min_value=0.0, step=100.0, key="outbound_altitude_m")
        st.number_input("Outbound segment wind [m/s]", step=1.0, key="outbound_wind_speed_m_per_s")

        st.checkbox("Use loiter segment", key="use_loiter")
        st.number_input("Loiter duration [min]", min_value=1.0, step=5.0, key="loiter_duration_min", disabled=not st.session_state["use_loiter"])
        st.number_input("Loiter altitude [m]", min_value=0.0, step=100.0, key="loiter_altitude_m")

        st.checkbox("Use return segment", key="use_return")
        st.number_input("Return distance [km]", min_value=1.0, step=1.0, key="return_distance_km", disabled=not st.session_state["use_return"])
        st.number_input("Return altitude [m]", min_value=0.0, step=100.0, key="return_altitude_m")
        st.number_input("Return segment wind [m/s]", step=1.0, key="return_wind_speed_m_per_s")

        st.checkbox("Use descent segment", key="use_descent_segment")
        st.number_input("Descent altitude [m]", min_value=0.0, step=100.0, key="descent_altitude_m", disabled=not st.session_state["use_descent_segment"])
        st.number_input("Descent rate [m/s]", min_value=0.1, step=0.1, key="descent_rate_m_per_s", disabled=not st.session_state["use_descent_segment"])
        st.number_input("Descent power factor [-]", min_value=0.05, max_value=1.0, step=0.05, format="%.2f", key="descent_power_factor", disabled=not st.session_state["use_descent_segment"])

        st.selectbox(
            "Cruise mode",
            options=["fixed_speed", "best_range", "best_wind_adjusted_range"],
            key="cruise_mode",
        )

working_config = base_config.model_copy(deep=True)

working_config.aircraft.payload_mass_kg = float(st.session_state["payload_mass_kg"])
working_config.aircraft.battery_mass_kg = float(st.session_state["battery_mass_kg"])
working_config.aircraft.battery_specific_energy_wh_per_kg = float(st.session_state["battery_specific_energy_wh_per_kg"])
working_config.aircraft.wing_area_m2 = float(st.session_state["wing_area_m2"])
working_config.aircraft.aspect_ratio = float(st.session_state["aspect_ratio"])
working_config.aircraft.cd0 = float(st.session_state["cd0"])
working_config.aircraft.cl_max = float(st.session_state["cl_max"])
working_config.aircraft.eta_total = float(st.session_state["eta_total"])
working_config.aircraft.hotel_load_w = float(st.session_state["hotel_load_w"])
working_config.aircraft.payload_load_w = float(st.session_state["payload_load_w"])
working_config.aircraft.loiter_payload_load_w = (
    float(st.session_state["loiter_payload_load_w"])
    if st.session_state["use_loiter_payload_override"]
    else None
)

working_config.environment.altitude_m = float(st.session_state["altitude_m"])
working_config.environment.air_density_kg_per_m3 = None
working_config.environment.wind_speed_m_per_s = float(st.session_state["general_wind_speed_m_per_s"])

working_config.mission.cruise_speed_m_per_s = float(st.session_state["cruise_speed_m_per_s"])
working_config.mission.required_distance_km = (
    float(st.session_state["required_distance_km"]) if st.session_state["use_required_distance"] else None
)
working_config.mission.reserve_fraction = float(st.session_state["reserve_fraction"])
working_config.mission.reserve_energy_wh = (
    float(st.session_state["reserve_energy_wh"]) if st.session_state["use_fixed_reserve_energy"] else None
)

if working_config.mission.profile is not None:
    working_config.mission.profile.climb_altitude_m = (
        float(st.session_state["climb_altitude_m"]) if st.session_state["use_climb_segment"] else None
    )
    working_config.mission.profile.climb_rate_m_per_s = (
        float(st.session_state["climb_rate_m_per_s"]) if st.session_state["use_climb_segment"] else None
    )

    working_config.mission.profile.outbound_distance_km = float(st.session_state["outbound_distance_km"])
    working_config.mission.profile.outbound_altitude_m = float(st.session_state["outbound_altitude_m"])

    working_config.mission.profile.loiter_duration_min = (
        float(st.session_state["loiter_duration_min"]) if st.session_state["use_loiter"] else None
    )
    working_config.mission.profile.loiter_altitude_m = float(st.session_state["loiter_altitude_m"])

    working_config.mission.profile.return_distance_km = (
        float(st.session_state["return_distance_km"]) if st.session_state["use_return"] else None
    )
    working_config.mission.profile.return_altitude_m = float(st.session_state["return_altitude_m"])

    working_config.mission.profile.descent_altitude_m = (
        float(st.session_state["descent_altitude_m"]) if st.session_state["use_descent_segment"] else None
    )
    working_config.mission.profile.descent_rate_m_per_s = (
        float(st.session_state["descent_rate_m_per_s"]) if st.session_state["use_descent_segment"] else None
    )
    working_config.mission.profile.descent_power_factor = float(st.session_state["descent_power_factor"])

    working_config.mission.profile.outbound_wind_speed_m_per_s = float(st.session_state["outbound_wind_speed_m_per_s"])
    working_config.mission.profile.return_wind_speed_m_per_s = float(st.session_state["return_wind_speed_m_per_s"])
    working_config.mission.profile.cruise_mode = st.session_state["cruise_mode"]

config = working_config

summary = make_performance_summary(config)
sweep_df = make_sweep_df(config)
operating_points_df = make_operating_points_summary(config)
mission_profile = make_mission_profile_result(config)
selected_stem = Path(selected_config).stem

top1, top2 = st.columns([2, 1])

with top1:
    st.subheader("Selected base configuration")
    st.code(selected_config)

with top2:
    st.subheader("Model scope")
    with st.expander("Assumptions and limits", expanded=False):
        st.markdown(
            """
- Fixed-wing, steady level-flight core model  
- Preliminary battery-electric mission estimation  
- Simple drag-polar approach  
- Along-track wind treatment only  
- ISA altitude-based density option  
- Segmented missions can now include climb, cruise, loiter, return, and descent  
- Reserve can be defined by fraction or fixed energy  
- This remains a preliminary engineering tool, not a high-fidelity flight dynamics solver
"""
        )

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total mass [kg]", f"{summary['total_mass_kg']:.2f}")
m2.metric("Stall speed [m/s]", f"{summary['stall_speed_m_per_s']:.2f}")
m3.metric("Min recommended cruise [m/s]", f"{summary['minimum_recommended_cruise_speed_m_per_s']:.2f}")
m4.metric("Resolved air density [kg/m³]", f"{summary['resolved_air_density_kg_per_m3']:.3f}")

m5, m6, m7, m8 = st.columns(4)
m5.metric("Electrical power [W]", f"{summary['electrical_power_required_w']:.1f}")
m6.metric("Endurance [h]", f"{summary['endurance_h']:.2f}")
m7.metric("Still-air range [km]", f"{summary['still_air_range_km']:.1f}")
m8.metric("Wind-adjusted range [km]", f"{summary['wind_adjusted_range_km']:.1f}")

m9, m10, m11 = st.columns(3)
m9.metric("Usable battery energy [Wh]", f"{summary['battery_usable_energy_wh']:.1f}")
m10.metric("Reserve energy [Wh]", f"{summary['reserve_energy_wh']:.1f}")
m11.metric("Available mission energy [Wh]", f"{summary['battery_available_for_mission_wh']:.1f}")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    [
        "Performance",
        "Operating points",
        "Mission",
        "Default comparisons",
        "Saved scenario comparison",
        "Config and scenario management",
        "Trade study",
    ]
)

with tab1:
    st.subheader("Speed sweep results")
    st.dataframe(sweep_df.round(3), width="stretch")
    st.download_button(
        "Download speed sweep CSV",
        data=dataframe_to_csv_bytes(sweep_df),
        file_name=f"{selected_stem}_speed_sweep.csv",
        mime="text/csv",
    )

    st.markdown("**Power vs airspeed**")
    st.line_chart(
        make_sweep_chart_df(sweep_df, ["air_power_w", "electrical_power_w"]),
        width="stretch",
    )

    st.markdown("**Endurance vs airspeed**")
    st.line_chart(
        make_sweep_chart_df(sweep_df, ["endurance_h"]),
        width="stretch",
    )

    st.markdown("**Range vs airspeed**")
    st.line_chart(
        make_sweep_chart_df(sweep_df, ["still_air_range_km", "wind_adjusted_range_km"]),
        width="stretch",
    )

with tab2:
    st.subheader("Operating-point summary")
    st.dataframe(operating_points_df.round(3), width="stretch")
    st.download_button(
        "Download operating points CSV",
        data=dataframe_to_csv_bytes(operating_points_df),
        file_name=f"{selected_stem}_operating_points.csv",
        mime="text/csv",
    )

with tab3:
    st.subheader("Mission assessment")

    if config.mission.required_distance_km is not None:
        st.markdown("### Mission feasibility summary")

        a1, a2, a3 = st.columns(3)
        a1.metric("Mission feasible", str(is_mission_feasible(config)))
        a2.metric("Range margin [km]", f"{range_margin_km(config):.2f}")
        a3.metric("Energy margin [Wh]", f"{energy_margin_wh(config):.2f}")

        a4, a5 = st.columns(2)
        a4.metric("Required mission time [h]", f"{required_mission_time_hours(config):.2f}")
        a5.metric("Required mission energy [Wh]", f"{required_mission_energy_wh(config):.2f}")

    if mission_profile is not None:
        st.markdown("---")
        st.markdown("### Segmented mission profile")

        c1, c2, c3 = st.columns(3)
        c1.metric("Profile feasible", str(mission_profile["mission_feasible"]))
        c2.metric("Total mission time [h]", f"{float(mission_profile['total_time_h']):.2f}")
        c3.metric("Remaining energy [Wh]", f"{float(mission_profile['remaining_energy_wh']):.2f}")

        c4, c5, c6 = st.columns(3)
        c4.metric("Available mission energy [Wh]", f"{float(mission_profile['available_energy_wh']):.2f}")
        c5.metric("Total mission energy used [Wh]", f"{float(mission_profile['total_energy_used_wh']):.2f}")
        c6.metric("Number of segments", f"{len(mission_profile['segments'])}")

        st.markdown("#### Energy source breakdown")
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Propulsion energy [Wh]", f"{float(mission_profile['total_propulsion_energy_wh']):.2f}")
        d2.metric("Hotel energy [Wh]", f"{float(mission_profile['total_hotel_energy_wh']):.2f}")
        d3.metric("Payload energy [Wh]", f"{float(mission_profile['total_payload_energy_wh']):.2f}")
        d4.metric("Non-propulsive energy [Wh]", f"{float(mission_profile['total_non_propulsive_energy_wh']):.2f}")

        mission_summary_df = mission_profile_summary_df(mission_profile)
        segments_df = mission_profile_segments_df(mission_profile)
        display_segments_df = mission_profile_display_df(mission_profile)

        st.markdown("#### Mission totals")
        st.dataframe(mission_summary_df.round(3), width="stretch")

        st.markdown("#### Segment results")
        st.dataframe(display_segments_df.round(3), width="stretch")

        with st.expander("Show detailed segment table", expanded=False):
            st.dataframe(segments_df.round(3), width="stretch")

        e1, e2 = st.columns(2)
        with e1:
            st.download_button(
                "Download mission summary CSV",
                data=dataframe_to_csv_bytes(mission_summary_df),
                file_name=f"{selected_stem}_mission_summary.csv",
                mime="text/csv",
            )
        with e2:
            st.download_button(
                "Download mission segments CSV",
                data=dataframe_to_csv_bytes(segments_df),
                file_name=f"{selected_stem}_mission_segments.csv",
                mime="text/csv",
            )

        st.markdown("#### Charts")
        st.markdown("**Total energy used by segment**")
        st.bar_chart(make_mission_energy_df(mission_profile), width="stretch")

        st.markdown("**Energy source breakdown by segment**")
        st.bar_chart(make_mission_energy_breakdown_df(mission_profile), width="stretch")

        st.markdown("**Remaining mission energy by stage**")
        st.line_chart(make_remaining_energy_df(mission_profile), width="stretch")
    else:
        st.info("No segmented mission profile is defined in this config.")

with tab4:
    st.subheader("Default mission scenario comparison")

    scenario_df = compare_mission_scenarios(
        config_paths=DEFAULT_MISSION_SCENARIO_FILES,
        max_speed_m_per_s=40.0,
        num_points=120,
    )
    scenario_display_df = make_scenario_display_df(scenario_df)

    feasible_count = int(scenario_df["mission_feasible"].sum())
    best_margin_row = scenario_df.sort_values("remaining_energy_wh", ascending=False).iloc[0]
    lowest_energy_row = scenario_df.sort_values("total_energy_used_wh", ascending=True).iloc[0]
    fastest_row = scenario_df.sort_values("total_time_h", ascending=True).iloc[0]

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Feasible scenarios", f"{feasible_count}/{len(scenario_df)}")
    a2.metric(
        f"Best energy margin: {str(best_margin_row['scenario'])}",
        f"{float(best_margin_row['remaining_energy_wh']):.2f} Wh",
    )
    a3.metric(
        f"Lowest mission energy: {str(lowest_energy_row['scenario'])}",
        f"{float(lowest_energy_row['total_energy_used_wh']):.2f} Wh",
    )
    a4.metric(
        f"Shortest mission time: {str(fastest_row['scenario'])}",
        f"{float(fastest_row['total_time_h']):.2f} h",
    )

    st.markdown("#### Comparison table")
    st.dataframe(scenario_display_df.round(3), width="stretch")
    st.download_button(
        "Download mission scenario comparison CSV",
        data=dataframe_to_csv_bytes(scenario_df),
        file_name="mission_scenario_comparison.csv",
        mime="text/csv",
    )

    st.markdown("#### Charts")
    st.markdown("**Mission energy balance**")
    st.bar_chart(make_scenario_energy_balance_chart_df(scenario_df), width="stretch")

    st.markdown("**Mission energy source breakdown**")
    st.bar_chart(make_scenario_energy_source_chart_df(scenario_df), width="stretch")

    st.markdown("**Mission time by scenario**")
    st.bar_chart(make_scenario_time_chart_df(scenario_df), width="stretch")

    st.markdown("---")
    st.subheader("Default configuration comparison")

    config_df = compare_configurations(
        config_paths=[
            str(CONFIG_DIR / "example_fixed_wing.yaml"),
            str(CONFIG_DIR / "example_fixed_wing_long_range.yaml"),
            str(CONFIG_DIR / "example_fixed_wing_fast.yaml"),
        ],
        max_speed_m_per_s=40.0,
        num_points=120,
    )
    config_display_df = make_configuration_display_df(config_df)

    best_still_air_row = config_df.sort_values("maximum_still_air_range_km", ascending=False).iloc[0]
    best_wind_row = config_df.sort_values("maximum_wind_adjusted_range_km", ascending=False).iloc[0]
    best_endurance_row = config_df.sort_values("maximum_endurance_h", ascending=False).iloc[0]

    b1, b2, b3 = st.columns(3)
    b1.metric(
        f"Best still-air range: {str(best_still_air_row['configuration'])}",
        f"{float(best_still_air_row['maximum_still_air_range_km']):.2f} km",
    )
    b2.metric(
        f"Best wind-adjusted range: {str(best_wind_row['configuration'])}",
        f"{float(best_wind_row['maximum_wind_adjusted_range_km']):.2f} km",
    )
    b3.metric(
        f"Best endurance: {str(best_endurance_row['configuration'])}",
        f"{float(best_endurance_row['maximum_endurance_h']):.2f} h",
    )

    st.markdown("#### Configuration table")
    st.dataframe(config_display_df.round(3), width="stretch")
    st.download_button(
        "Download configuration comparison CSV",
        data=dataframe_to_csv_bytes(config_df),
        file_name="configuration_comparison.csv",
        mime="text/csv",
    )

    st.markdown("#### Charts")
    st.markdown("**Maximum range by configuration**")
    st.bar_chart(make_configuration_range_chart_df(config_df), width="stretch")

    st.markdown("**Maximum endurance by configuration**")
    st.bar_chart(make_configuration_endurance_chart_df(config_df), width="stretch")

with tab5:
    st.subheader("Compare saved scenarios")

    saved_config_options = list_yaml_configs(str(CONFIG_DIR))
    selected_saved_configs = st.multiselect(
        "Select saved YAML scenarios to compare",
        options=saved_config_options,
        default=[],
    )

    if len(selected_saved_configs) < 2:
        st.info("Select at least two saved scenarios to compare.")
    else:
        saved_scenario_df = compare_mission_scenarios(
            config_paths=selected_saved_configs,
            max_speed_m_per_s=40.0,
            num_points=120,
        )
        saved_display_df = make_scenario_display_df(saved_scenario_df)

        feasible_count = int(saved_scenario_df["mission_feasible"].sum())
        best_margin_row = saved_scenario_df.sort_values("remaining_energy_wh", ascending=False).iloc[0]
        lowest_energy_row = saved_scenario_df.sort_values("total_energy_used_wh", ascending=True).iloc[0]
        fastest_row = saved_scenario_df.sort_values("total_time_h", ascending=True).iloc[0]

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Feasible scenarios", f"{feasible_count}/{len(saved_scenario_df)}")
        s2.metric(
            f"Best energy margin: {str(best_margin_row['scenario'])}",
            f"{float(best_margin_row['remaining_energy_wh']):.2f} Wh",
        )
        s3.metric(
            f"Lowest mission energy: {str(lowest_energy_row['scenario'])}",
            f"{float(lowest_energy_row['total_energy_used_wh']):.2f} Wh",
        )
        s4.metric(
            f"Shortest mission time: {str(fastest_row['scenario'])}",
            f"{float(fastest_row['total_time_h']):.2f} h",
        )

        st.markdown("#### Comparison table")
        st.dataframe(saved_display_df.round(3), width="stretch")
        st.download_button(
            "Download saved scenario comparison CSV",
            data=dataframe_to_csv_bytes(saved_scenario_df),
            file_name="saved_scenario_comparison.csv",
            mime="text/csv",
        )

        st.markdown("#### Charts")
        st.markdown("**Saved scenario energy balance**")
        st.bar_chart(make_scenario_energy_balance_chart_df(saved_scenario_df), width="stretch")

        st.markdown("**Saved scenario energy source breakdown**")
        st.bar_chart(make_scenario_energy_source_chart_df(saved_scenario_df), width="stretch")

        st.markdown("**Saved scenario mission time**")
        st.bar_chart(make_scenario_time_chart_df(saved_scenario_df), width="stretch")

with tab6:
    st.subheader("Config inspection and scenario management")

    st.markdown("**Base YAML**")
    st.code(yaml.dump(load_config_dict(selected_config), sort_keys=False), language="yaml")

    st.markdown("**Active configuration after sidebar edits**")
    st.code(yaml.dump(config.model_dump(mode="python"), sort_keys=False), language="yaml")

    st.download_button(
        "Download active config YAML",
        data=config_to_yaml_bytes(config),
        file_name=f"{selected_stem}_edited.yaml",
        mime="text/yaml",
    )

    st.markdown("**Save named scenario**")
    scenario_name = st.text_input(
        "Scenario name",
        value=f"{selected_stem}_custom",
        help="This will save a new YAML file into the configs folder.",
    )

    if st.button("Save scenario to configs/"):
        try:
            saved_path = save_config_yaml(config, scenario_name, CONFIG_DIR)
            list_yaml_configs.clear()
            load_config_dict.clear()
            st.success(f"Scenario saved: {saved_path.resolve()}")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

with tab7:
    st.subheader("Trade study")

    trade_parameter = st.selectbox(
        "Parameter to sweep",
        options=TRADE_PARAMETER_OPTIONS,
        format_func=lambda x: TRADE_PARAMETER_LABELS[x],
    )

    default_values = {
        "battery_mass_kg": float(config.aircraft.battery_mass_kg),
        "payload_mass_kg": float(config.aircraft.payload_mass_kg),
        "wing_area_m2": float(config.aircraft.wing_area_m2),
        "cd0": float(config.aircraft.cd0),
        "altitude_m": float(config.environment.altitude_m or 0.0),
        "cruise_speed_m_per_s": float(config.mission.cruise_speed_m_per_s),
    }

    default_value = default_values[trade_parameter]

    if trade_parameter == "cd0":
        min_default = max(0.001, 0.8 * default_value)
        max_default = 1.2 * default_value
        step_value = 0.001
    elif trade_parameter == "altitude_m":
        min_default = max(0.0, default_value)
        max_default = max(1000.0, default_value + 3000.0)
        step_value = 100.0
    elif trade_parameter == "cruise_speed_m_per_s":
        min_default = max(1.0, 0.7 * default_value)
        max_default = 1.3 * default_value
        step_value = 0.5
    else:
        min_default = max(0.1, 0.7 * default_value)
        max_default = 1.3 * default_value
        step_value = 0.1

    trade_min = st.number_input("Minimum value", value=float(min_default), step=float(step_value), key="trade_min")
    trade_max = st.number_input("Maximum value", value=float(max_default), step=float(step_value), key="trade_max")
    trade_points = st.number_input("Number of points", min_value=3, max_value=100, value=15, step=1)

    if trade_max <= trade_min:
        st.error("Maximum value must be greater than minimum value.")
    else:
        trade_df = build_trade_study_df(
            config,
            parameter_name=trade_parameter,
            min_value=float(trade_min),
            max_value=float(trade_max),
            num_points=int(trade_points),
        )

        st.dataframe(trade_df.round(3), width="stretch")
        st.download_button(
            "Download trade study CSV",
            data=dataframe_to_csv_bytes(trade_df),
            file_name=f"{selected_stem}_{trade_parameter}_trade_study.csv",
            mime="text/csv",
        )

        st.markdown("**Range and endurance response**")
        st.line_chart(
            trade_df.set_index("parameter_value")[
                ["still_air_range_km", "wind_adjusted_range_km", "endurance_h"]
            ],
            width="stretch",
        )

        st.markdown("**Stall speed and power response**")
        st.line_chart(
            trade_df.set_index("parameter_value")[
                ["stall_speed_m_per_s", "electrical_power_required_w"]
            ],
            width="stretch",
        )

        if not trade_df["remaining_energy_wh"].isna().all():
            st.markdown("**Mission response**")
            st.line_chart(
                trade_df.set_index("parameter_value")[
                    ["remaining_energy_wh", "mission_feasible_flag"]
                ],
                width="stretch",
            )