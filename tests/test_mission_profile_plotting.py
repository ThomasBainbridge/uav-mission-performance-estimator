from pathlib import Path

from uav_mpe.mission_profile import evaluate_simple_mission_profile
from uav_mpe.mission_profile_plotting import (
    plot_mission_energy_by_segment,
    plot_remaining_energy_by_segment,
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


def test_plot_mission_energy_by_segment_creates_file(tmp_path: Path):
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

    output = tmp_path / "mission_energy_by_segment.png"
    returned_path = plot_mission_energy_by_segment(mission_profile, output)

    assert returned_path.exists()
    assert returned_path == output


def test_plot_remaining_energy_by_segment_creates_file(tmp_path: Path):
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

    output = tmp_path / "remaining_energy_by_segment.png"
    returned_path = plot_remaining_energy_by_segment(mission_profile, output)

    assert returned_path.exists()
    assert returned_path == output