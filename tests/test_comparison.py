from uav_mpe.comparison import compare_configurations


def test_compare_configurations_returns_dataframe_with_expected_columns():
    df = compare_configurations(
        config_paths=[
            "configs/example_fixed_wing.yaml",
            "configs/example_fixed_wing_long_range.yaml",
            "configs/example_fixed_wing_fast.yaml",
        ],
        max_speed_m_per_s=40.0,
        num_points=50,
    )

    expected_columns = {
        "configuration",
        "total_mass_kg",
        "stall_speed_m_per_s",
        "minimum_recommended_cruise_speed_m_per_s",
        "propulsion_electrical_power_at_nominal_cruise_w",
        "hotel_load_w",
        "payload_load_w",
        "non_propulsive_electrical_load_w",
        "electrical_power_at_nominal_cruise_w",
        "best_endurance_speed_m_per_s",
        "maximum_endurance_h",
        "best_still_air_range_speed_m_per_s",
        "maximum_still_air_range_km",
        "best_wind_adjusted_range_speed_m_per_s",
        "maximum_wind_adjusted_range_km",
    }

    assert set(df.columns) == expected_columns
    assert len(df) == 3


def test_compare_configurations_outputs_are_positive():
    df = compare_configurations(
        config_paths=[
            "configs/example_fixed_wing.yaml",
            "configs/example_fixed_wing_long_range.yaml",
            "configs/example_fixed_wing_fast.yaml",
        ],
        max_speed_m_per_s=40.0,
        num_points=50,
    )

    assert (df["total_mass_kg"] > 0.0).all()
    assert (df["stall_speed_m_per_s"] > 0.0).all()
    assert (df["maximum_endurance_h"] > 0.0).all()
    assert (df["maximum_still_air_range_km"] > 0.0).all()
    assert (df["maximum_wind_adjusted_range_km"] > 0.0).all()
    assert (df["electrical_power_at_nominal_cruise_w"] > 0.0).all()