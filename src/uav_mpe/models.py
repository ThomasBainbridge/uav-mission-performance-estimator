from pydantic import BaseModel, Field


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
    air_density_kg_per_m3: float = Field(gt=0)
    wind_speed_m_per_s: float = 0.0
    g_m_per_s2: float = 9.81


class Mission(BaseModel):
    usable_battery_fraction: float = Field(gt=0, le=1)
    reserve_fraction: float = Field(ge=0, lt=1)
    cruise_speed_m_per_s: float = Field(gt=0)


class Config(BaseModel):
    aircraft: Aircraft
    environment: Environment
    mission: Mission