from pathlib import Path

from uav_mpe.comparison import compare_configurations
from uav_mpe.models import Aircraft, Config, Environment, Mission
from uav_mpe.plotting import (
    plot_comparison_ranges,
    plot_endurance_vs_speed,
    plot_power_vs_speed,
    plot_range_vs_speed,
)
from uav_mpe.sweeps import build_speed_sweep


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
        ),
    )


def test_plot_power_vs_speed_creates_file(tmp_path: Path):
    config = make_test_config()
    df = build_speed_sweep(config, max_speed_m_per_s=40.0, num_points=50)

    output = tmp_path / "power_vs_speed.png"
    returned_path = plot_power_vs_speed(df, output)

    assert returned_path.exists()
    assert returned_path == output


def test_plot_endurance_vs_speed_creates_file(tmp_path: Path):
    config = make_test_config()
    df = build_speed_sweep(config, max_speed_m_per_s=40.0, num_points=50)

    output = tmp_path / "endurance_vs_speed.png"
    returned_path = plot_endurance_vs_speed(df, output)

    assert returned_path.exists()
    assert returned_path == output


def test_plot_range_vs_speed_creates_file(tmp_path: Path):
    config = make_test_config()
    df = build_speed_sweep(config, max_speed_m_per_s=40.0, num_points=50)

    output = tmp_path / "range_vs_speed.png"
    returned_path = plot_range_vs_speed(df, output)

    assert returned_path.exists()
    assert returned_path == output


def test_plot_comparison_ranges_creates_file(tmp_path: Path):
    comparison_df = compare_configurations(
        config_paths=[
            "configs/example_fixed_wing.yaml",
            "configs/example_fixed_wing_long_range.yaml",
            "configs/example_fixed_wing_fast.yaml",
        ],
        max_speed_m_per_s=40.0,
        num_points=50,
    )

    output = tmp_path / "configuration_comparison_ranges.png"
    returned_path = plot_comparison_ranges(comparison_df, output)

    assert returned_path.exists()
    assert returned_path == output