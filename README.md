# UAV Mission Performance Estimator

A Python-based engineering tool for estimating fixed-wing UAV mission performance from preliminary design inputs.

The tool uses inputs such as mass, payload, battery characteristics, aerodynamic assumptions, propulsion efficiency, cruise speed, and wind to estimate:

- power required
- endurance
- range
- speed-performance trade-offs
- configuration comparisons
- mission feasibility

## Current Features

- fixed-wing steady level-flight performance model
- stall speed and minimum recommended cruise speed
- drag, power, endurance, and range calculations
- airspeed sweep analysis
- best-endurance and best-range speed identification
- comparison of multiple UAV configurations
- mission feasibility assessment at chosen cruise speed
- CSV export of results
- automatic plot generation

## Example Outputs

### Power vs Airspeed
![Power vs Airspeed](assets/screenshots/power-vs-speed.png)

### Endurance vs Airspeed
![Endurance vs Airspeed](assets/screenshots/endurance-vs-speed.png)

### Range vs Airspeed
![Range vs Airspeed](assets/screenshots/range-vs-speed.png)

### Configuration Comparison
![Configuration Comparison](assets/screenshots/configuration-comparison.png)

## Project Structure

```text
uav-mission-performance-estimator/
├─ configs/
├─ outputs/
├─ src/uav_mpe/
├─ tests/
├─ README.md
├─ pyproject.toml
└─ .gitignore