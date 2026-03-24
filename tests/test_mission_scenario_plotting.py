from pathlib import Path

from uav_mpe.mission_scenario_comparison import compare_mission_scenarios
from uav_mpe.mission_scenario_plotting import plot_mission_scenario_energy_balance


def test_plot_mission_scenario_energy_balance_creates_file(tmp_path: Path):
    comparison_df = compare_mission_scenarios(
        config_paths=[
            "configs/mission_baseline.yaml",
            "configs/mission_windy.yaml",
            "configs/mission_loiter.yaml",
        ],
        max_speed_m_per_s=40.0,
        num_points=80,
    )

    output = tmp_path / "mission_scenario_energy_balance.png"
    returned_path = plot_mission_scenario_energy_balance(comparison_df, output)

    assert returned_path.exists()
    assert returned_path == output