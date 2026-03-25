import pytest

from uav_mpe.descent import (
    descent_energy_wh,
    descent_time_hours,
    descent_time_seconds,
    descent_total_electrical_power_watts,
)
from uav_mpe.models import Aircraft, Config, Environment, Mission


def make_test_config() -> Config:
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
            altitude_m=0.0,
            wind_speed_m_per_s=0.0,
            g_m_per_s2=9.81,
        ),
        mission=Mission(
            usable_battery_fraction=0.85,
            reserve_fraction=0.10,
            cruise_speed_m_per_s=20.0,
            required_distance_km=100.0,
        ),
    )


def test_descent_time_seconds():
    assert descent_time_seconds(500.0, 2.5) == 200.0


def test_descent_time_hours():
    assert descent_time_hours(500.0, 2.5) == pytest.approx(200.0 / 3600.0)


def test_descent_power_is_positive():
    config = make_test_config()
    assert descent_total_electrical_power_watts(config, 0.7) > 0.0


def test_descent_energy_is_positive():
    config = make_test_config()
    assert descent_energy_wh(config, 500.0, 2.5, 0.7) > 0.0