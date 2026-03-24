from uav_mpe.mission_profile import (
    evaluate_cruise_segment_best_range,
    evaluate_cruise_segment_fixed_speed,
    evaluate_loiter_segment_best_endurance,
    evaluate_simple_mission_profile,
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


def test_fixed_speed_cruise_segment_is_positive():
    config = make_test_config()

    segment = evaluate_cruise_segment_fixed_speed(
        config,
        segment_name="outbound",
        distance_km=20.0,
        wind_speed_m_per_s=0.0,
    )

    assert segment["segment_type"] == "cruise"
    assert segment["speed_mode"] == "fixed_speed"
    assert segment["airspeed_m_per_s"] > 0.0
    assert segment["ground_speed_m_per_s"] > 0.0
    assert segment["time_h"] > 0.0
    assert segment["energy_used_wh"] > 0.0


def test_best_range_cruise_segment_is_positive():
    config = make_test_config()

    segment = evaluate_cruise_segment_best_range(
        config,
        segment_name="outbound",
        distance_km=20.0,
        wind_speed_m_per_s=0.0,
        max_speed_m_per_s=40.0,
        num_points=80,
    )

    assert segment["segment_type"] == "cruise"
    assert segment["speed_mode"] == "best_range"
    assert segment["airspeed_m_per_s"] > 0.0
    assert segment["ground_speed_m_per_s"] > 0.0
    assert segment["time_h"] > 0.0
    assert segment["energy_used_wh"] > 0.0


def test_best_endurance_loiter_segment_is_positive():
    config = make_test_config()

    segment = evaluate_loiter_segment_best_endurance(
        config,
        segment_name="loiter",
        loiter_duration_min=15.0,
        max_speed_m_per_s=40.0,
        num_points=80,
    )

    assert segment["segment_type"] == "loiter"
    assert segment["speed_mode"] == "best_endurance"
    assert segment["airspeed_m_per_s"] > 0.0
    assert segment["time_h"] > 0.0
    assert segment["energy_used_wh"] > 0.0


def test_simple_mission_profile_can_be_feasible():
    config = make_test_config()

    result = evaluate_simple_mission_profile(
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

    assert result["mission_feasible"] is True
    assert result["total_time_h"] > 0.0
    assert result["total_energy_used_wh"] > 0.0
    assert result["remaining_energy_wh"] > 0.0
    assert len(result["segments"]) == 3


def test_simple_mission_profile_can_be_infeasible():
    config = make_test_config()

    result = evaluate_simple_mission_profile(
        config,
        outbound_distance_km=80.0,
        loiter_duration_min=60.0,
        return_distance_km=80.0,
        outbound_wind_speed_m_per_s=0.0,
        return_wind_speed_m_per_s=0.0,
        cruise_mode="best_range",
        max_speed_m_per_s=40.0,
        num_points=80,
    )

    assert result["mission_feasible"] is False
    assert result["remaining_energy_wh"] < 0.0


def test_extreme_headwind_can_make_segment_impossible():
    config = make_test_config()

    segment = evaluate_cruise_segment_fixed_speed(
        config,
        segment_name="outbound",
        distance_km=5.0,
        wind_speed_m_per_s=50.0,
    )

    assert segment["ground_speed_m_per_s"] == 0.0
    assert segment["time_h"] == float("inf")
    assert segment["energy_used_wh"] == float("inf")