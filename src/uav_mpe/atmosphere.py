from __future__ import annotations

from uav_mpe.models import Config


def isa_density_kg_per_m3(altitude_m: float) -> float:
    if altitude_m < 0.0:
        raise ValueError("altitude_m must be non-negative.")
    if altitude_m > 11000.0:
        raise ValueError("This Version 2 ISA model currently supports altitudes up to 11,000 m.")

    t0_k = 288.15
    p0_pa = 101325.0
    lapse_rate_k_per_m = 0.0065
    gas_constant_j_per_kg_k = 287.05
    g0_m_per_s2 = 9.80665

    temperature_k = t0_k - lapse_rate_k_per_m * altitude_m
    pressure_pa = p0_pa * (temperature_k / t0_k) ** (
        g0_m_per_s2 / (gas_constant_j_per_kg_k * lapse_rate_k_per_m)
    )
    density_kg_per_m3 = pressure_pa / (gas_constant_j_per_kg_k * temperature_k)

    return density_kg_per_m3


def get_air_density_kg_per_m3(config: Config) -> float:
    env = config.environment

    if env.air_density_kg_per_m3 is not None:
        return env.air_density_kg_per_m3

    if env.altitude_m is None:
        raise ValueError(
            "Environment must define either air_density_kg_per_m3 or altitude_m."
        )

    return isa_density_kg_per_m3(env.altitude_m)