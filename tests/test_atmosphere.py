import pytest

from uav_mpe.atmosphere import get_air_density_kg_per_m3, isa_density_kg_per_m3
from uav_mpe.models import Aircraft, Config, Environment, Mission


def make_test_config_with_density() -> Config:
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
            required_distance_km=100.0,
        ),
    )


def make_test_config_with_altitude(altitude_m: float) -> Config:
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
            altitude_m=altitude_m,
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


def test_isa_density_at_sea_level_is_reasonable():
    rho = isa_density_kg_per_m3(0.0)
    assert rho == pytest.approx(1.225, abs=0.01)


def test_isa_density_decreases_with_altitude():
    rho_0 = isa_density_kg_per_m3(0.0)
    rho_2000 = isa_density_kg_per_m3(2000.0)

    assert rho_2000 < rho_0


def test_get_air_density_returns_direct_density_when_provided():
    config = make_test_config_with_density()
    rho = get_air_density_kg_per_m3(config)

    assert rho == pytest.approx(1.225)


def test_get_air_density_computes_from_altitude_when_density_not_provided():
    config = make_test_config_with_altitude(0.0)
    rho = get_air_density_kg_per_m3(config)

    assert rho == pytest.approx(1.225, abs=0.01)


def test_negative_altitude_raises_error():
    with pytest.raises(ValueError):
        isa_density_kg_per_m3(-10.0)