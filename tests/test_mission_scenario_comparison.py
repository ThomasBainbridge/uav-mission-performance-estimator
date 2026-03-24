from pathlib import Path

from uav_mpe.mission_scenario_comparison import compare_mission_scenarios


def test_compare_mission_scenarios_returns_expected_columns():
    df = compare_mission_scenarios(
        config_paths=[
            "configs/mission_baseline.yaml",
            "configs/mission_windy.yaml",
            "configs/mission_loiter.yaml",
        ],
        max_speed_m_per_s=40.0,
        num_points=80,
    )

    expected_columns = {
        "scenario",
        "mission_feasible",
        "available_energy_wh",
        "total_time_h",
        "total_energy_used_wh",
        "remaining_energy_wh",
        "number_of_segments",
        "outbound_distance_km",
        "loiter_duration_min",
        "return_distance_km",
        "cruise_mode",
    }

    assert set(df.columns) == expected_columns
    assert len(df) == 3


def test_compare_mission_scenarios_names_match_file_stems():
    config_paths = [
        "configs/mission_baseline.yaml",
        "configs/mission_windy.yaml",
        "configs/mission_loiter.yaml",
    ]

    df = compare_mission_scenarios(
        config_paths=config_paths,
        max_speed_m_per_s=40.0,
        num_points=80,
    )

    expected_names = {Path(path).stem for path in config_paths}
    actual_names = set(df["scenario"])

    assert actual_names == expected_names


def test_compare_mission_scenarios_outputs_are_sensible():
    df = compare_mission_scenarios(
        config_paths=[
            "configs/mission_baseline.yaml",
            "configs/mission_windy.yaml",
            "configs/mission_loiter.yaml",
        ],
        max_speed_m_per_s=40.0,
        num_points=80,
    )

    assert (df["available_energy_wh"] > 0.0).all()
    assert (df["total_time_h"] > 0.0).all()
    assert (df["total_energy_used_wh"] > 0.0).all()
    assert (df["number_of_segments"] >= 2).all()