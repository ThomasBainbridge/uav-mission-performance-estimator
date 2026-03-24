import pytest

from uav_mpe.models import Aircraft, Config, Environment, Mission
from uav_mpe.performance import (
    battery_available_for_mission_wh,
    battery_nominal_energy_wh,
    battery_usable_energy_wh,
    minimum_recommended_cruise_speed_m_per_s,
    stall_speed_m_per_s,
    total_mass_kg,
    weight_newtons,
)


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
            air_density_kg_per_m3=1.225,
            wind_speed_m_per_s=0.0,
            g_m_per_s2=9.81,
        ),
        mission=Mission(
            usable_battery_fraction=0.85,
            reserve_fraction=0.10,
            cruise_speed_m_per_s=20.0,
        ),
    )


def test_total_mass():
    config = make_test_config()
    assert total_mass_kg(config) == 6.5


def test_weight_is_positive():
    config = make_test_config()
    assert weight_newtons(config) > 0.0


def test_battery_energy_chain():
    config = make_test_config()
    nominal = battery_nominal_energy_wh(config)
    usable = battery_usable_energy_wh(config)
    available = battery_available_for_mission_wh(config)

    assert nominal == 330.0
    assert usable == 280.5
    assert available == pytest.approx(252.45)


def test_stall_and_minimum_cruise_speed():
    config = make_test_config()
    v_stall = stall_speed_m_per_s(config)
    v_min = minimum_recommended_cruise_speed_m_per_s(config)

    assert v_stall > 0.0
    assert v_min > v_stall