from pathlib import Path

import pandas as pd

from uav_mpe.mission_profile import evaluate_simple_mission_profile
from uav_mpe.mission_profile_export import (
    save_mission_profile_segments_to_csv,
    save_mission_profile_summary_to_csv,
)
from uav_mpe.models import Aircraft, Config, Environment, Mission


def make_test_config(wind_speed_m_per_s: float = 0.0) -> Config:
    return Config(
        aircraft=Aircraft(
            empty_mass_kg=4.0,
            payload_mass_kg=1.0,
            battery_mass_kg=1.5,
            battery_specific_energy_wh_per_kg=220.0,
            wing_area_m2=0.8,
            aspect_ratio=8.0,
            oswald_efficiency=0.8,
            cd0=0.03,
            cl_max=1.4,
            eta_total=0.7,
            hotel_load_w=15.0,
            payload_load_w=10.0,
        ),
        environment=Environment(
            air_density_kg_per_m3=1.225,
            wind_speed_m_per_s=wind_speed_m_per_s,
            g_m_per_s2=9.81,
        ),
        mission=Mission(
            usable_battery_fraction=0.85,
            reserve_fraction=0.10,
            cruise_speed_m_per_s=20.0,
            required_distance_km=100.0,
        ),
    )


def test_save_mission_profile_segments_to_csv_creates_file(tmp_path: Path):
    config = make_test_config()

    mission_profile = evaluate_simple_mission_profile(
        config,
        outbound_distance_km=20.0,
        loiter_duration_min=10.0,
        return_distance_km=20.0,
        outbound_wind_speed_m_per_s=0.0,
        return_wind_speed_m_per_s=0.0,
        cruise_mode="best_range",
        max_speed_m_per_s=40.0,
        num_points=80,
    )

    output = tmp_path / "mission_profile_segments.csv"
    returned_path = save_mission_profile_segments_to_csv(mission_profile, output)

    assert returned_path.exists()
    assert returned_path == output

    df = pd.read_csv(output)
    expected_columns = {
        "segment_name",
        "segment_type",
        "electrical_power_w",
        "energy_used_wh",
        "propulsion_electrical_power_w",
        "hotel_load_w",
        "payload_load_w",
        "non_propulsive_electrical_load_w",
        "propulsion_energy_wh",
        "hotel_energy_wh",
        "payload_energy_wh",
        "non_propulsive_energy_wh",
        "remaining_energy_wh_after_segment",
    }
    assert expected_columns.issubset(df.columns)


def test_save_mission_profile_summary_to_csv_creates_file(tmp_path: Path):
    config = make_test_config()

    mission_profile = evaluate_simple_mission_profile(
        config,
        outbound_distance_km=20.0,
        loiter_duration_min=10.0,
        return_distance_km=20.0,
        outbound_wind_speed_m_per_s=0.0,
        return_wind_speed_m_per_s=0.0,
        cruise_mode="best_range",
        max_speed_m_per_s=40.0,
        num_points=80,
    )

    output = tmp_path / "mission_profile_summary.csv"
    returned_path = save_mission_profile_summary_to_csv(mission_profile, output)

    assert returned_path.exists()
    assert returned_path == output

    df = pd.read_csv(output)
    expected_columns = {
        "available_energy_wh",
        "total_time_h",
        "total_energy_used_wh",
        "total_propulsion_energy_wh",
        "total_hotel_energy_wh",
        "total_payload_energy_wh",
        "total_non_propulsive_energy_wh",
        "remaining_energy_wh",
        "mission_feasible",
        "number_of_segments",
    }
    assert set(df.columns) == expected_columns