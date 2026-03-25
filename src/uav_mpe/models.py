from pydantic import BaseModel, Field, model_validator


class Aircraft(BaseModel):
    empty_mass_kg: float = Field(gt=0)
    payload_mass_kg: float = Field(ge=0)
    battery_mass_kg: float = Field(gt=0)
    battery_specific_energy_wh_per_kg: float = Field(gt=0)
    wing_area_m2: float = Field(gt=0)
    aspect_ratio: float = Field(gt=0)
    oswald_efficiency: float = Field(gt=0, le=1)
    cd0: float = Field(gt=0)
    cl_max: float = Field(gt=0)
    eta_total: float = Field(gt=0, le=1)


class Environment(BaseModel):
    air_density_kg_per_m3: float | None = Field(default=None, gt=0)
    altitude_m: float | None = Field(default=None, ge=0)
    wind_speed_m_per_s: float = 0.0
    g_m_per_s2: float = 9.81

    @model_validator(mode="after")
    def validate_density_or_altitude(self):
        if self.air_density_kg_per_m3 is None and self.altitude_m is None:
            raise ValueError(
                "Environment must define either air_density_kg_per_m3 or altitude_m."
            )
        return self


class MissionSegmentProfile(BaseModel):
    climb_altitude_m: float | None = Field(default=None, ge=0)
    climb_rate_m_per_s: float | None = Field(default=None, gt=0)
    outbound_distance_km: float = Field(gt=0)
    loiter_duration_min: float | None = Field(default=None, gt=0)
    return_distance_km: float | None = Field(default=None, gt=0)
    descent_altitude_m: float | None = Field(default=None, ge=0)
    descent_rate_m_per_s: float | None = Field(default=None, gt=0)
    descent_power_factor: float = Field(default=0.7, gt=0, le=1)
    outbound_wind_speed_m_per_s: float = 0.0
    return_wind_speed_m_per_s: float = 0.0
    cruise_mode: str = "best_range"

    @model_validator(mode="after")
    def validate_cruise_mode(self):
        allowed = {
            "fixed_speed",
            "best_range",
            "best_wind_adjusted_range",
        }
        if self.cruise_mode not in allowed:
            raise ValueError(
                "cruise_mode must be one of: "
                "'fixed_speed', 'best_range', 'best_wind_adjusted_range'."
            )
        return self


class Mission(BaseModel):
    usable_battery_fraction: float = Field(gt=0, le=1)
    reserve_fraction: float = Field(ge=0, lt=1)
    cruise_speed_m_per_s: float = Field(gt=0)
    required_distance_km: float | None = Field(default=None, gt=0)
    profile: MissionSegmentProfile | None = None


class Config(BaseModel):
    aircraft: Aircraft
    environment: Environment
    mission: Mission