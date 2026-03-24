import pytest

from uav_mpe.mission import (
    energy_margin_wh,
    is_mission_feasible,
    range_margin_km,
    required_mission_energy_wh,
    required_mission_time_hours,
)
from uav_mpe.models import Aircraft, Config, Environment, Mission


def make_test_config(
    required_distance_km: float | None = None,
    wind_speed_m_per_s: float = 0.0,
) -> Config:
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
            required_distance_km=required_distance_km,
        ),
    )


def test_required_mission_time_is_positive_for_feasible_case():
    config = make_test_config(required_distance_km=100.0)

    assert required_mission_time_hours(config) > 0.0
    assert required_mission_energy_wh(config) > 0.0


def test_shorter_mission_is_feasible():
    config = make_test_config(required_distance_km=80.0)

    assert is_mission_feasible(config) is True
    assert range_margin_km(config) > 0.0
    assert energy_margin_wh(config) > 0.0


def test_longer_mission_is_not_feasible():
    config = make_test_config(required_distance_km=150.0)

    assert is_mission_feasible(config) is False
    assert range_margin_km(config) < 0.0
    assert energy_margin_wh(config) < 0.0


def test_headwind_can_make_mission_impossible():
    config = make_test_config(required_distance_km=10.0, wind_speed_m_per_s=50.0)

    assert required_mission_time_hours(config) == float("inf")
    assert required_mission_energy_wh(config) == float("inf")
    assert is_mission_feasible(config) is False


def test_missing_required_distance_raises_error():
    config = make_test_config(required_distance_km=None)

    with pytest.raises(ValueError):
        required_mission_time_hours(config)