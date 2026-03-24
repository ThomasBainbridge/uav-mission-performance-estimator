from pathlib import Path

import yaml

from uav_mpe.models import Config
from uav_mpe.mission_profile import evaluate_simple_mission_profile


def test_config_can_load_mission_profile():
    with open("configs/example_fixed_wing.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    config = Config.model_validate(data)

    assert config.mission.profile is not None
    assert config.mission.profile.outbound_distance_km == 25.0
    assert config.mission.profile.loiter_duration_min == 15.0
    assert config.mission.profile.return_distance_km == 25.0
    assert config.mission.profile.cruise_mode == "best_range"


def test_config_driven_mission_profile_can_be_evaluated():
    with open("configs/example_fixed_wing.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    config = Config.model_validate(data)
    profile = config.mission.profile

    assert profile is not None

    result = evaluate_simple_mission_profile(
        config,
        outbound_distance_km=profile.outbound_distance_km,
        loiter_duration_min=profile.loiter_duration_min,
        return_distance_km=profile.return_distance_km,
        outbound_wind_speed_m_per_s=profile.outbound_wind_speed_m_per_s,
        return_wind_speed_m_per_s=profile.return_wind_speed_m_per_s,
        cruise_mode=profile.cruise_mode,
        max_speed_m_per_s=40.0,
        num_points=80,
    )

    assert "mission_feasible" in result
    assert "segments" in result
    assert len(result["segments"]) >= 2