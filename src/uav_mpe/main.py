from pathlib import Path
import yaml

from uav_mpe.models import Config
from uav_mpe.performance import (
    battery_available_for_mission_j,
    battery_available_for_mission_wh,
    battery_nominal_energy_wh,
    battery_usable_energy_wh,
    minimum_recommended_cruise_speed_m_per_s,
    stall_speed_m_per_s,
    total_mass_kg,
    weight_newtons,
)


def load_config(path: str | Path) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Config.model_validate(data)


def main() -> None:
    config = load_config("configs/example_fixed_wing.yaml")

    print("UAV Mission Performance Estimator")
    print("-" * 40)
    print(f"Total mass [kg]: {total_mass_kg(config):.3f}")
    print(f"Weight [N]: {weight_newtons(config):.3f}")
    print(f"Battery nominal energy [Wh]: {battery_nominal_energy_wh(config):.3f}")
    print(f"Battery usable energy [Wh]: {battery_usable_energy_wh(config):.3f}")
    print(f"Battery available for mission [Wh]: {battery_available_for_mission_wh(config):.3f}")
    print(f"Battery available for mission [J]: {battery_available_for_mission_j(config):.3f}")
    print(f"Stall speed [m/s]: {stall_speed_m_per_s(config):.3f}")
    print(
        f"Minimum recommended cruise speed [m/s]: "
        f"{minimum_recommended_cruise_speed_m_per_s(config):.3f}"
    )


if __name__ == "__main__":
    main()