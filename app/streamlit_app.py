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
    minimum_recommended_cruise_speed_m_per_s,
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

MISSION_SCENARIO_FILES = [
    str(CONFIG_DIR / "mission_baseline.yaml"),
    str(CONFIG_DIR / "mission_windy.yaml"),
    str(CONFIG_DIR / "mission_loiter.yaml"),
]


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
        "battery_available_for_mission_wh": battery_available_for_mission_wh(config),
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
        loiter_duration_min=profile.loiter_duration_min,
        return_distance_km=profile.return_distance_km,
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

    return pd.DataFrame(
        {
            "segment_name": [str(segment["segment_name"]) for segment in segments],
            "energy_used_wh": [float(segment["energy_used_wh"]) for segment in segments],
        }
    ).set_index("segment_name")


def make_remaining_energy_df(mission_profile: dict[str, object]) -> pd.DataFrame:
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

        remaining_energy_wh = float("nan")
        mission_feasible_flag = float("nan")

        if mission_profile is not None:
            remaining_energy_wh = float(mission_profile["remaining_energy_wh"])
            mission_feasible_flag = 1.0 if bool(mission_profile["mission_feasible"]) else 0.0

        rows.append(
            {
                "parameter_value": float(value),
                "still_air_range_km": summary["still_air_range_km"],
                "wind_adjusted_range_km": summary["wind_adjusted_range_km"],
                "endurance_h": summary["endurance_h"],
                "stall_speed_m_per_s": summary["stall_speed_m_per_s"],
                "electrical_power_required_w": summary["electrical_power_required_w"],
                "remaining_energy_wh": remaining_energy_wh,
                "mission_feasible_flag": mission_feasible_flag,
            }
        )

    return pd.DataFrame(rows)


st.set_page_config(
    page_title="UAV Mission Performance Estimator",
    layout="wide",
)

st.title("UAV Mission Performance Estimator")
st.caption("Version 3.7 live Streamlit interface with scenario saving, editable inputs, downloads, and trade studies.")

config_options = list_yaml_configs(str(CONFIG_DIR))

with st.sidebar:
    st.header("Configuration")
    selected_config = st.selectbox("Select YAML config", options=config_options)

base_config = load_config(selected_config)
working_config = base_config.model_copy(deep=True)

with st.sidebar:
    st.header("Editable inputs")

    st.subheader("Aircraft")
    payload_mass_kg = st.number_input(
        "Payload mass [kg]",
        min_value=0.0,
        value=float(base_config.aircraft.payload_mass_kg),
        step=0.1,
    )
    battery_mass_kg = st.number_input(
        "Battery mass [kg]",
        min_value=0.1,
        value=float(base_config.aircraft.battery_mass_kg),
        step=0.1,
    )
    battery_specific_energy_wh_per_kg = st.number_input(
        "Battery specific energy [Wh/kg]",
        min_value=50.0,
        value=float(base_config.aircraft.battery_specific_energy_wh_per_kg),
        step=10.0,
    )
    wing_area_m2 = st.number_input(
        "Wing area [m²]",
        min_value=0.1,
        value=float(base_config.aircraft.wing_area_m2),
        step=0.05,
    )
    aspect_ratio = st.number_input(
        "Aspect ratio [-]",
        min_value=1.0,
        value=float(base_config.aircraft.aspect_ratio),
        step=0.5,
    )
    cd0 = st.number_input(
        "Cd0 [-]",
        min_value=0.001,
        value=float(base_config.aircraft.cd0),
        step=0.001,
        format="%.3f",
    )
    cl_max = st.number_input(
        "Cl_max [-]",
        min_value=0.1,
        value=float(base_config.aircraft.cl_max),
        step=0.05,
    )
    eta_total = st.number_input(
        "Total propulsion efficiency [-]",
        min_value=0.05,
        max_value=1.0,
        value=float(base_config.aircraft.eta_total),
        step=0.01,
        format="%.2f",
    )

    st.subheader("Environment")
    altitude_m = st.number_input(
        "Altitude [m]",
        min_value=0.0,
        value=float(base_config.environment.altitude_m or 0.0),
        step=100.0,
    )
    general_wind_speed_m_per_s = st.number_input(
        "General wind speed [m/s]",
        value=float(base_config.environment.wind_speed_m_per_s),
        step=1.0,
    )

    st.subheader("Mission")
    cruise_speed_m_per_s = st.number_input(
        "Cruise speed [m/s]",
        min_value=1.0,
        value=float(base_config.mission.cruise_speed_m_per_s),
        step=0.5,
    )

    use_required_distance = st.checkbox(
        "Use required mission distance",
        value=base_config.mission.required_distance_km is not None,
    )
    required_distance_default = (
        float(base_config.mission.required_distance_km)
        if base_config.mission.required_distance_km is not None
        else 100.0
    )
    required_distance_km = st.number_input(
        "Required mission distance [km]",
        min_value=1.0,
        value=required_distance_default,
        step=5.0,
        disabled=not use_required_distance,
    )

    if working_config.mission.profile is not None:
        st.subheader("Mission profile")

        outbound_distance_km = st.number_input(
            "Outbound distance [km]",
            min_value=1.0,
            value=float(working_config.mission.profile.outbound_distance_km),
            step=1.0,
        )

        use_loiter = st.checkbox(
            "Use loiter segment",
            value=working_config.mission.profile.loiter_duration_min is not None,
        )
        loiter_default = (
            float(working_config.mission.profile.loiter_duration_min)
            if working_config.mission.profile.loiter_duration_min is not None
            else 15.0
        )
        loiter_duration_min = st.number_input(
            "Loiter duration [min]",
            min_value=1.0,
            value=loiter_default,
            step=5.0,
            disabled=not use_loiter,
        )

        use_return = st.checkbox(
            "Use return segment",
            value=working_config.mission.profile.return_distance_km is not None,
        )
        return_default = (
            float(working_config.mission.profile.return_distance_km)
            if working_config.mission.profile.return_distance_km is not None
            else 25.0
        )
        return_distance_km = st.number_input(
            "Return distance [km]",
            min_value=1.0,
            value=return_default,
            step=1.0,
            disabled=not use_return,
        )

        outbound_wind_speed_m_per_s = st.number_input(
            "Outbound segment wind [m/s]",
            value=float(working_config.mission.profile.outbound_wind_speed_m_per_s),
            step=1.0,
        )
        return_wind_speed_m_per_s = st.number_input(
            "Return segment wind [m/s]",
            value=float(working_config.mission.profile.return_wind_speed_m_per_s),
            step=1.0,
        )

        cruise_mode = st.selectbox(
            "Cruise mode",
            options=["fixed_speed", "best_range", "best_wind_adjusted_range"],
            index=["fixed_speed", "best_range", "best_wind_adjusted_range"].index(
                working_config.mission.profile.cruise_mode
            ),
        )

working_config.aircraft.payload_mass_kg = float(payload_mass_kg)
working_config.aircraft.battery_mass_kg = float(battery_mass_kg)
working_config.aircraft.battery_specific_energy_wh_per_kg = float(battery_specific_energy_wh_per_kg)
working_config.aircraft.wing_area_m2 = float(wing_area_m2)
working_config.aircraft.aspect_ratio = float(aspect_ratio)
working_config.aircraft.cd0 = float(cd0)
working_config.aircraft.cl_max = float(cl_max)
working_config.aircraft.eta_total = float(eta_total)

working_config.environment.altitude_m = float(altitude_m)
working_config.environment.air_density_kg_per_m3 = None
working_config.environment.wind_speed_m_per_s = float(general_wind_speed_m_per_s)

working_config.mission.cruise_speed_m_per_s = float(cruise_speed_m_per_s)
working_config.mission.required_distance_km = (
    float(required_distance_km) if use_required_distance else None
)

if working_config.mission.profile is not None:
    working_config.mission.profile.outbound_distance_km = float(outbound_distance_km)
    working_config.mission.profile.loiter_duration_min = (
        float(loiter_duration_min) if use_loiter else None
    )
    working_config.mission.profile.return_distance_km = (
        float(return_distance_km) if use_return else None
    )
    working_config.mission.profile.outbound_wind_speed_m_per_s = float(outbound_wind_speed_m_per_s)
    working_config.mission.profile.return_wind_speed_m_per_s = float(return_wind_speed_m_per_s)
    working_config.mission.profile.cruise_mode = cruise_mode

config = working_config

summary = make_performance_summary(config)
sweep_df = make_sweep_df(config)
operating_points_df = make_operating_points_summary(config)
mission_profile = make_mission_profile_result(config)
selected_stem = Path(selected_config).stem

st.subheader("Selected configuration")
st.code(selected_config)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total mass [kg]", f"{summary['total_mass_kg']:.2f}")
c2.metric("Stall speed [m/s]", f"{summary['stall_speed_m_per_s']:.2f}")
c3.metric("Min recommended cruise [m/s]", f"{summary['minimum_recommended_cruise_speed_m_per_s']:.2f}")
c4.metric("Resolved air density [kg/m³]", f"{summary['resolved_air_density_kg_per_m3']:.3f}")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Electrical power [W]", f"{summary['electrical_power_required_w']:.1f}")
c6.metric("Endurance [h]", f"{summary['endurance_h']:.2f}")
c7.metric("Still-air range [km]", f"{summary['still_air_range_km']:.1f}")
c8.metric("Wind-adjusted range [km]", f"{summary['wind_adjusted_range_km']:.1f}")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "Performance",
        "Operating points",
        "Mission",
        "Scenario comparison",
        "Config",
        "Trade study",
    ]
)

with tab1:
    st.subheader("Speed sweep table")
    st.dataframe(sweep_df.round(3), use_container_width=True)
    st.download_button(
        "Download speed sweep CSV",
        data=dataframe_to_csv_bytes(sweep_df),
        file_name=f"{selected_stem}_speed_sweep.csv",
        mime="text/csv",
    )

    st.subheader("Live charts")

    st.markdown("**Power vs airspeed**")
    st.line_chart(
        make_sweep_chart_df(sweep_df, ["air_power_w", "electrical_power_w"]),
        use_container_width=True,
    )

    st.markdown("**Endurance vs airspeed**")
    st.line_chart(
        make_sweep_chart_df(sweep_df, ["endurance_h"]),
        use_container_width=True,
    )

    st.markdown("**Range vs airspeed**")
    st.line_chart(
        make_sweep_chart_df(sweep_df, ["still_air_range_km", "wind_adjusted_range_km"]),
        use_container_width=True,
    )

with tab2:
    st.subheader("Operating points")
    st.dataframe(operating_points_df.round(3), use_container_width=True)
    st.download_button(
        "Download operating points CSV",
        data=dataframe_to_csv_bytes(operating_points_df),
        file_name=f"{selected_stem}_operating_points.csv",
        mime="text/csv",
    )

with tab3:
    st.subheader("Mission feasibility")

    if config.mission.required_distance_km is not None:
        m1, m2, m3 = st.columns(3)
        m1.metric("Mission feasible", str(is_mission_feasible(config)))
        m2.metric("Range margin [km]", f"{range_margin_km(config):.2f}")
        m3.metric("Energy margin [Wh]", f"{energy_margin_wh(config):.2f}")

        m4, m5 = st.columns(2)
        m4.metric("Required mission time [h]", f"{required_mission_time_hours(config):.2f}")
        m5.metric("Required mission energy [Wh]", f"{required_mission_energy_wh(config):.2f}")

    if mission_profile is not None:
        st.subheader("Segmented mission profile")
        st.metric("Profile feasible", str(mission_profile["mission_feasible"]))

        s1, s2, s3 = st.columns(3)
        s1.metric("Total mission time [h]", f"{float(mission_profile['total_time_h']):.2f}")
        s2.metric("Energy used [Wh]", f"{float(mission_profile['total_energy_used_wh']):.2f}")
        s3.metric("Remaining energy [Wh]", f"{float(mission_profile['remaining_energy_wh']):.2f}")

        mission_summary_df = mission_profile_summary_df(mission_profile)
        segments_df = mission_profile_segments_df(mission_profile)

        st.markdown("**Mission summary**")
        st.dataframe(mission_summary_df.round(3), use_container_width=True)
        st.download_button(
            "Download mission summary CSV",
            data=dataframe_to_csv_bytes(mission_summary_df),
            file_name=f"{selected_stem}_mission_summary.csv",
            mime="text/csv",
        )

        st.markdown("**Mission segments**")
        st.dataframe(segments_df.round(3), use_container_width=True)
        st.download_button(
            "Download mission segments CSV",
            data=dataframe_to_csv_bytes(segments_df),
            file_name=f"{selected_stem}_mission_segments.csv",
            mime="text/csv",
        )

        st.markdown("**Mission energy by segment**")
        st.bar_chart(make_mission_energy_df(mission_profile), use_container_width=True)

        st.markdown("**Remaining energy by segment**")
        st.line_chart(make_remaining_energy_df(mission_profile), use_container_width=True)
    else:
        st.info("No segmented mission profile is defined in this config.")

with tab4:
    st.subheader("Mission scenario comparison")
    scenario_df = compare_mission_scenarios(
        config_paths=MISSION_SCENARIO_FILES,
        max_speed_m_per_s=40.0,
        num_points=120,
    )
    st.dataframe(scenario_df.round(3), use_container_width=True)
    st.download_button(
        "Download mission scenario comparison CSV",
        data=dataframe_to_csv_bytes(scenario_df),
        file_name="mission_scenario_comparison.csv",
        mime="text/csv",
    )

    st.markdown("**Mission scenario energy balance**")
    scenario_chart_df = scenario_df.set_index("scenario")[["total_energy_used_wh", "remaining_energy_wh"]]
    st.bar_chart(scenario_chart_df, use_container_width=True)

    st.subheader("Configuration comparison")
    config_df = compare_configurations(
        config_paths=[
            str(CONFIG_DIR / "example_fixed_wing.yaml"),
            str(CONFIG_DIR / "example_fixed_wing_long_range.yaml"),
            str(CONFIG_DIR / "example_fixed_wing_fast.yaml"),
        ],
        max_speed_m_per_s=40.0,
        num_points=120,
    )
    st.dataframe(config_df.round(3), use_container_width=True)
    st.download_button(
        "Download configuration comparison CSV",
        data=dataframe_to_csv_bytes(config_df),
        file_name="configuration_comparison.csv",
        mime="text/csv",
    )

    st.markdown("**Maximum range by configuration**")
    config_chart_df = config_df.set_index("configuration")[["maximum_still_air_range_km", "maximum_wind_adjusted_range_km"]]
    st.bar_chart(config_chart_df, use_container_width=True)

with tab5:
    st.subheader("Base YAML")
    st.code(yaml.dump(load_config_dict(selected_config), sort_keys=False), language="yaml")

    st.subheader("Active configuration after sidebar edits")
    st.code(yaml.dump(config.model_dump(mode="python"), sort_keys=False), language="yaml")

    st.download_button(
        "Download active config YAML",
        data=config_to_yaml_bytes(config),
        file_name=f"{selected_stem}_edited.yaml",
        mime="text/yaml",
    )

    st.subheader("Save named scenario")
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

with tab6:
    st.subheader("Trade study")

    trade_parameter = st.selectbox(
        "Parameter to sweep",
        options=[
            "battery_mass_kg",
            "payload_mass_kg",
            "wing_area_m2",
            "cd0",
            "altitude_m",
            "cruise_speed_m_per_s",
        ],
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

    trade_min = st.number_input(
        "Minimum value",
        value=float(min_default),
        step=float(step_value),
        key="trade_min",
    )
    trade_max = st.number_input(
        "Maximum value",
        value=float(max_default),
        step=float(step_value),
        key="trade_max",
    )
    trade_points = st.number_input(
        "Number of points",
        min_value=3,
        max_value=100,
        value=15,
        step=1,
    )

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

        st.dataframe(trade_df.round(3), use_container_width=True)
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
            use_container_width=True,
        )

        st.markdown("**Stall speed and power response**")
        st.line_chart(
            trade_df.set_index("parameter_value")[
                ["stall_speed_m_per_s", "electrical_power_required_w"]
            ],
            use_container_width=True,
        )

        if not trade_df["remaining_energy_wh"].isna().all():
            st.markdown("**Mission response**")
            st.line_chart(
                trade_df.set_index("parameter_value")[
                    ["remaining_energy_wh", "mission_feasible_flag"]
                ],
                use_container_width=True,
            )