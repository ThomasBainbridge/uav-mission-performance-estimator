import numpy as np
import pytest

from uav_mpe.models import Aircraft, Config, Environment, Mission
from uav_mpe.performance import minimum_recommended_cruise_speed_m_per_s
from uav_mpe.sweeps import (
    best_endurance_row,
    best_still_air_range_row,
    best_wind_adjusted_range_row,
    build_speed_sweep,
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
        ),
    )


def test_build_speed_sweep_returns_dataframe_with_expected_columns():
    config = make_test_config()
    df = build_speed_sweep(config, max_speed_m_per_s=40.0, num_points=50)

    expected_columns = {
        "airspeed_m_per_s",
        "lift_coefficient",
        "induced_drag_factor",
        "drag_coefficient",
        "drag_force_n",
        "air_power_w",
        "propulsion_electrical_power_w",
        "hotel_load_w",
        "payload_load_w",
        "non_propulsive_electrical_load_w",
        "electrical_power_w",
        "endurance_h",
        "still_air_range_km",
        "wind_adjusted_ground_speed_m_per_s",
        "wind_adjusted_range_km",
    }

    assert set(df.columns) == expected_columns
    assert len(df) == 50


def test_speed_sweep_starts_at_minimum_recommended_speed_and_ends_at_max_speed():
    config = make_test_config()
    df = build_speed_sweep(config, max_speed_m_per_s=40.0, num_points=50)

    v_min = minimum_recommended_cruise_speed_m_per_s(config)

    assert df.iloc[0]["airspeed_m_per_s"] == pytest.approx(v_min)
    assert df.iloc[-1]["airspeed_m_per_s"] == pytest.approx(40.0)


def test_speed_sweep_speed_is_monotonic_increasing():
    config = make_test_config()
    df = build_speed_sweep(config, max_speed_m_per_s=40.0, num_points=50)

    assert df["airspeed_m_per_s"].is_monotonic_increasing


def test_speed_sweep_power_breakdown_is_internally_consistent():
    config = make_test_config()
    df = build_speed_sweep(config, max_speed_m_per_s=40.0, num_points=50)

    assert np.allclose(
        df["non_propulsive_electrical_load_w"],
        df["hotel_load_w"] + df["payload_load_w"],
    )
    assert np.allclose(
        df["electrical_power_w"],
        df["propulsion_electrical_power_w"] + df["non_propulsive_electrical_load_w"],
    )


def test_best_rows_match_dataframe_maxima():
    config = make_test_config()
    df = build_speed_sweep(config, max_speed_m_per_s=40.0, num_points=80)

    best_endurance = best_endurance_row(config, max_speed_m_per_s=40.0, num_points=80)
    best_still_air_range = best_still_air_range_row(config, max_speed_m_per_s=40.0, num_points=80)
    best_wind_range = best_wind_adjusted_range_row(config, max_speed_m_per_s=40.0, num_points=80)

    assert best_endurance["endurance_h"] == pytest.approx(df["endurance_h"].max())
    assert best_still_air_range["still_air_range_km"] == pytest.approx(df["still_air_range_km"].max())
    assert best_wind_range["wind_adjusted_range_km"] == pytest.approx(df["wind_adjusted_range_km"].max())


def test_headwind_reduces_best_wind_adjusted_range():
    still_air = make_test_config(wind_speed_m_per_s=0.0)
    headwind = make_test_config(wind_speed_m_per_s=5.0)

    best_still_air = best_wind_adjusted_range_row(still_air, max_speed_m_per_s=40.0, num_points=80)
    best_headwind = best_wind_adjusted_range_row(headwind, max_speed_m_per_s=40.0, num_points=80)

    assert best_headwind["wind_adjusted_range_km"] < best_still_air["wind_adjusted_range_km"]


def test_invalid_sweep_bounds_raise_error():
    config = make_test_config()
    v_min = minimum_recommended_cruise_speed_m_per_s(config)

    with pytest.raises(ValueError):
        build_speed_sweep(config, max_speed_m_per_s=v_min, num_points=50)