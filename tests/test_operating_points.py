from uav_mpe.models import Aircraft, Config, Environment, Mission
from uav_mpe.operating_points import (
    get_best_endurance_operating_point,
    get_best_range_operating_point,
    get_best_wind_adjusted_range_operating_point,
)


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


def test_best_endurance_operating_point_has_expected_keys():
    config = make_test_config()
    op = get_best_endurance_operating_point(config, max_speed_m_per_s=40.0, num_points=80)

    expected_keys = {
        "airspeed_m_per_s",
        "electrical_power_w",
        "endurance_h",
        "still_air_range_km",
        "wind_adjusted_range_km",
    }

    assert set(op.keys()) == expected_keys


def test_best_range_operating_point_has_expected_keys():
    config = make_test_config()
    op = get_best_range_operating_point(config, max_speed_m_per_s=40.0, num_points=80)

    expected_keys = {
        "airspeed_m_per_s",
        "electrical_power_w",
        "endurance_h",
        "still_air_range_km",
        "wind_adjusted_range_km",
    }

    assert set(op.keys()) == expected_keys


def test_best_endurance_speed_is_not_greater_than_best_range_speed():
    config = make_test_config()
    endurance_op = get_best_endurance_operating_point(
        config,
        max_speed_m_per_s=40.0,
        num_points=80,
    )
    range_op = get_best_range_operating_point(
        config,
        max_speed_m_per_s=40.0,
        num_points=80,
    )

    assert endurance_op["airspeed_m_per_s"] <= range_op["airspeed_m_per_s"]


def test_best_range_has_positive_outputs():
    config = make_test_config()
    op = get_best_range_operating_point(config, max_speed_m_per_s=40.0, num_points=80)

    assert op["airspeed_m_per_s"] > 0.0
    assert op["electrical_power_w"] > 0.0
    assert op["endurance_h"] > 0.0
    assert op["still_air_range_km"] > 0.0


def test_headwind_best_wind_adjusted_range_differs_from_still_air_range():
    config = make_test_config(wind_speed_m_per_s=5.0)

    still_air_op = get_best_range_operating_point(
        config,
        max_speed_m_per_s=40.0,
        num_points=80,
    )
    wind_op = get_best_wind_adjusted_range_operating_point(
        config,
        max_speed_m_per_s=40.0,
        num_points=80,
    )

    assert wind_op["wind_adjusted_range_km"] <= still_air_op["still_air_range_km"]