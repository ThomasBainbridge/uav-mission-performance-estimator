from uav_mpe.models import Aircraft


def test_aircraft_model_creation():
    aircraft = Aircraft(
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
    )
    assert aircraft.empty_mass_kg == 4.0