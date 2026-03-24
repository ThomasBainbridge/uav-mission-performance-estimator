import argparse
from pathlib import Path

import yaml

from uav_mpe.atmosphere import get_air_density_kg_per_m3
from uav_mpe.comparison import compare_configurations
from uav_mpe.exporting import save_comparison_to_csv, save_sweep_to_csv
from uav_mpe.mission import (
    energy_margin_wh,
    is_mission_feasible,
    range_margin_km,
    required_mission_energy_wh,
    required_mission_time_hours,
)
from uav_mpe.mission_profile import evaluate_simple_mission_profile
from uav_mpe.mission_profile_export import (
    save_mission_profile_segments_to_csv,
    save_mission_profile_summary_to_csv,
)
from uav_mpe.mission_profile_plotting import (
    plot_mission_energy_by_segment,
    plot_remaining_energy_by_segment,
)
from uav_mpe.models import Config
from uav_mpe.operating_points import (
    get_best_endurance_operating_point,
    get_best_range_operating_point,
    get_best_wind_adjusted_range_operating_point,
)
from uav_mpe.performance import (
    air_power_required_watts,
    battery_available_for_mission_j,
    battery_available_for_mission_wh,
    battery_nominal_energy_wh,
    battery_usable_energy_wh,
    drag_coefficient,
    drag_force_newtons,
    electrical_power_required_watts,
    endurance_hours,
    endurance_seconds,
    induced_drag_factor,
    lift_coefficient,
    minimum_recommended_cruise_speed_m_per_s,
    still_air_range_km,
    still_air_range_m,
    stall_speed_m_per_s,
    total_mass_kg,
    weight_newtons,
    wind_adjusted_ground_speed_m_per_s,
    wind_adjusted_range_km,
    wind_adjusted_range_m,
)
from uav_mpe.plotting import (
    plot_comparison_ranges,
    plot_endurance_vs_speed,
    plot_power_vs_speed,
    plot_range_vs_speed,
)
from uav_mpe.sweeps import (
    best_endurance_row,
    best_still_air_range_row,
    best_wind_adjusted_range_row,
    build_speed_sweep,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fixed-wing UAV mission performance estimator"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/example_fixed_wing.yaml",
        help="Path to YAML configuration file",
    )
    return parser.parse_args()


def load_config(path: str | Path) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Config.model_validate(data)


def main(config_path: str) -> None:
    config = load_config(config_path)

    print("UAV Mission Performance Estimator")
    print("-" * 50)
    print(f"Loaded config: {config_path}")
    print(f"Total mass [kg]: {total_mass_kg(config):.3f}")
    print(f"Weight [N]: {weight_newtons(config):.3f}")
    print(f"Resolved air density [kg/m^3]: {get_air_density_kg_per_m3(config):.4f}")
    if config.environment.altitude_m is not None:
        print(f"Altitude [m]: {config.environment.altitude_m:.1f}")
    print(f"Battery nominal energy [Wh]: {battery_nominal_energy_wh(config):.3f}")
    print(f"Battery usable energy [Wh]: {battery_usable_energy_wh(config):.3f}")
    print(f"Battery available for mission [Wh]: {battery_available_for_mission_wh(config):.3f}")
    print(f"Battery available for mission [J]: {battery_available_for_mission_j(config):.3f}")
    print(f"Stall speed [m/s]: {stall_speed_m_per_s(config):.3f}")
    print(
        f"Minimum recommended cruise speed [m/s]: "
        f"{minimum_recommended_cruise_speed_m_per_s(config):.3f}"
    )
    print(f"Cruise speed [m/s]: {config.mission.cruise_speed_m_per_s:.3f}")
    print(f"Lift coefficient, Cl [-]: {lift_coefficient(config):.4f}")
    print(f"Induced drag factor, k [-]: {induced_drag_factor(config):.5f}")
    print(f"Drag coefficient, Cd [-]: {drag_coefficient(config):.4f}")
    print(f"Drag force [N]: {drag_force_newtons(config):.3f}")
    print(f"Air power required [W]: {air_power_required_watts(config):.3f}")
    print(f"Electrical power required [W]: {electrical_power_required_watts(config):.3f}")
    print(f"Endurance [s]: {endurance_seconds(config):.3f}")
    print(f"Endurance [h]: {endurance_hours(config):.3f}")
    print(f"Still-air range [m]: {still_air_range_m(config):.3f}")
    print(f"Still-air range [km]: {still_air_range_km(config):.3f}")
    print(f"Wind-adjusted ground speed [m/s]: {wind_adjusted_ground_speed_m_per_s(config):.3f}")
    print(f"Wind-adjusted range [m]: {wind_adjusted_range_m(config):.3f}")
    print(f"Wind-adjusted range [km]: {wind_adjusted_range_km(config):.3f}")

    if config.mission.required_distance_km is not None:
        print()
        print("Mission feasibility")
        print("-" * 50)
        print(f"Required mission distance [km]: {config.mission.required_distance_km:.3f}")
        print(f"Required mission time [h]: {required_mission_time_hours(config):.3f}")
        print(f"Required mission energy [Wh]: {required_mission_energy_wh(config):.3f}")
        print(f"Available mission energy [Wh]: {battery_available_for_mission_wh(config):.3f}")
        print(f"Range margin [km]: {range_margin_km(config):.3f}")
        print(f"Energy margin [Wh]: {energy_margin_wh(config):.3f}")
        print(f"Mission feasible [-]: {is_mission_feasible(config)}")

    print()
    print("Version 2 operating points")
    print("-" * 50)

    best_endurance_op = get_best_endurance_operating_point(
        config,
        max_speed_m_per_s=40.0,
        num_points=120,
    )
    best_range_op = get_best_range_operating_point(
        config,
        max_speed_m_per_s=40.0,
        num_points=120,
    )
    best_wind_range_op = get_best_wind_adjusted_range_operating_point(
        config,
        max_speed_m_per_s=40.0,
        num_points=120,
    )

    print("Best endurance operating point:")
    print(best_endurance_op)

    print()
    print("Best still-air range operating point:")
    print(best_range_op)

    print()
    print("Best wind-adjusted range operating point:")
    print(best_wind_range_op)

    if config.mission.profile is not None:
        print()
        print("Loaded mission profile from config")
        print("-" * 50)
        print(config.mission.profile)

        print()
        print("Version 2 mission profile")
        print("-" * 50)

        profile = config.mission.profile

        mission_profile = evaluate_simple_mission_profile(
            config,
            outbound_distance_km=profile.outbound_distance_km,
            loiter_duration_min=profile.loiter_duration_min,
            return_distance_km=profile.return_distance_km,
            outbound_wind_speed_m_per_s=profile.outbound_wind_speed_m_per_s,
            return_wind_speed_m_per_s=profile.return_wind_speed_m_per_s,
            cruise_mode=profile.cruise_mode,
            max_speed_m_per_s=40.0,
            num_points=120,
        )

        print(f"Mission feasible [-]: {mission_profile['mission_feasible']}")
        print(f"Total mission time [h]: {mission_profile['total_time_h']:.3f}")
        print(f"Total mission energy used [Wh]: {mission_profile['total_energy_used_wh']:.3f}")
        print(f"Remaining energy [Wh]: {mission_profile['remaining_energy_wh']:.3f}")

        print()
        print("Mission profile segments")
        print("-" * 50)
        for segment in mission_profile["segments"]:
            print(segment)

        mission_segments_csv = save_mission_profile_segments_to_csv(
            mission_profile,
            "outputs/mission_profile_segments.csv",
        )
        mission_summary_csv = save_mission_profile_summary_to_csv(
            mission_profile,
            "outputs/mission_profile_summary.csv",
        )

        print()
        print("Saved mission profile CSV files")
        print("-" * 50)
        print(mission_segments_csv)
        print(mission_summary_csv)

        mission_energy_plot = plot_mission_energy_by_segment(
            mission_profile,
            "outputs/mission_energy_by_segment.png",
        )
        remaining_energy_plot = plot_remaining_energy_by_segment(
            mission_profile,
            "outputs/remaining_energy_by_segment.png",
        )

        print()
        print("Saved mission profile plots")
        print("-" * 50)
        print(mission_energy_plot)
        print(remaining_energy_plot)

    print()
    print("Speed sweep summary")
    print("-" * 50)

    max_speed_m_per_s = 40.0
    num_points = 120
    diagnostic_min_speed_m_per_s = stall_speed_m_per_s(config)

    sweep_df = build_speed_sweep(
        config,
        max_speed_m_per_s=max_speed_m_per_s,
        num_points=num_points,
        min_speed_m_per_s=diagnostic_min_speed_m_per_s,
    )

    best_endurance = best_endurance_row(
        config,
        max_speed_m_per_s=max_speed_m_per_s,
        num_points=num_points,
    )
    best_still_air_range = best_still_air_range_row(
        config,
        max_speed_m_per_s=max_speed_m_per_s,
        num_points=num_points,
    )
    best_wind_range = best_wind_adjusted_range_row(
        config,
        max_speed_m_per_s=max_speed_m_per_s,
        num_points=num_points,
    )

    print(f"Sweep points [-]: {len(sweep_df)}")
    print(f"Best endurance speed [m/s]: {best_endurance['airspeed_m_per_s']:.3f}")
    print(f"Maximum endurance [h]: {best_endurance['endurance_h']:.3f}")
    print(f"Best still-air range speed [m/s]: {best_still_air_range['airspeed_m_per_s']:.3f}")
    print(f"Maximum still-air range [km]: {best_still_air_range['still_air_range_km']:.3f}")
    print(f"Best wind-adjusted range speed [m/s]: {best_wind_range['airspeed_m_per_s']:.3f}")
    print(f"Maximum wind-adjusted range [km]: {best_wind_range['wind_adjusted_range_km']:.3f}")

    print()
    print("Diagnostic sweep bounds")
    print("-" * 50)
    print(f"Minimum plotted speed [m/s]: {sweep_df['airspeed_m_per_s'].min():.3f}")
    print(f"Maximum plotted speed [m/s]: {sweep_df['airspeed_m_per_s'].max():.3f}")

    print()
    print("First five sweep rows")
    print("-" * 50)
    print(sweep_df.head().to_string(index=False))

    sweep_csv = save_sweep_to_csv(
        sweep_df,
        "outputs/speed_sweep_results.csv",
    )

    v_stall = stall_speed_m_per_s(config)
    v_min_recommended = minimum_recommended_cruise_speed_m_per_s(config)

    power_plot = plot_power_vs_speed(
        sweep_df,
        "outputs/power_vs_speed.png",
        v_stall_m_per_s=v_stall,
        v_min_recommended_m_per_s=v_min_recommended,
    )
    endurance_plot = plot_endurance_vs_speed(
        sweep_df,
        "outputs/endurance_vs_speed.png",
        v_stall_m_per_s=v_stall,
        v_min_recommended_m_per_s=v_min_recommended,
    )
    range_plot = plot_range_vs_speed(
        sweep_df,
        "outputs/range_vs_speed.png",
        v_stall_m_per_s=v_stall,
        v_min_recommended_m_per_s=v_min_recommended,
    )

    print()
    print("Saved plots")
    print("-" * 50)
    print(power_plot)
    print(endurance_plot)
    print(range_plot)

    print()
    print("Configuration comparison")
    print("-" * 50)

    comparison_df = compare_configurations(
        config_paths=[
            "configs/example_fixed_wing.yaml",
            "configs/example_fixed_wing_long_range.yaml",
            "configs/example_fixed_wing_fast.yaml",
        ],
        max_speed_m_per_s=40.0,
        num_points=120,
    )

    print(comparison_df.round(3).to_string(index=False))

    comparison_plot = plot_comparison_ranges(
        comparison_df,
        "outputs/configuration_comparison_ranges.png",
    )

    comparison_csv = save_comparison_to_csv(
        comparison_df,
        "outputs/configuration_comparison_results.csv",
    )

    print()
    print("Saved comparison plot")
    print("-" * 50)
    print(comparison_plot)

    print()
    print("Saved CSV files")
    print("-" * 50)
    print(sweep_csv)
    print(comparison_csv)


if __name__ == "__main__":
    args = parse_args()
    main(args.config)