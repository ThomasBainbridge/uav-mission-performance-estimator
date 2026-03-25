import pytest

from uav_mpe.climb import (
    climb_energy_wh,
    climb_extra_power_watts,
    climb_time_hours,
    climb_time_seconds,
    climb_total_electrical_power_watts,
)
from uav_mpe.models import Aircraft, Config, Environment, Mission, MissionSegmentProfile


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
            profile=MissionSegmentProfile(
                climb_altitude_m=500.0,
                climb_rate_m_per_s=2.0,
                outbound_distance_km=25.0,
                loiter_duration_min=15.0,
                return_distance_km=25.0,
                outbound_wind_speed_m_per_s=0.0,
                return_wind_speed_m_per_s=0.0,
                cruise_mode="best_range",
            ),
        ),
    )


def test_climb_time_seconds():
    assert climb_time_seconds(500.0, 2.0) == 250.0


def test_climb_time_hours():
    assert climb_time_hours(500.0, 2.0) == pytest.approx(250.0 / 3600.0)


def test_climb_extra_power_is_positive():
    config = make_test_config()
    assert climb_extra_power_watts(config, 2.0) > 0.0


def test_climb_total_power_is_greater_than_level_power():
    config = make_test_config()
    assert climb_total_electrical_power_watts(config, 2.0) > climb_extra_power_watts(config, 2.0)


def test_climb_energy_is_positive():
    config = make_test_config()
    assert climb_energy_wh(config, 500.0, 2.0) > 0.0