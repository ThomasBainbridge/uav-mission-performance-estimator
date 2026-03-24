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

## Version 2 Enhancements

Version 2 extends the tool beyond single-point performance estimation into simple mission-profile analysis.

New capabilities include:

- reusable best-endurance and best-range operating point selection
- segmented mission profile evaluation for outbound, loiter, and return phases
- mission energy usage and remaining-energy tracking by segment
- mission profile CSV export
- mission profile plot generation
- ISA atmosphere support using altitude-based density estimation

### Mission Profile Outputs

#### Mission Energy by Segment
![Mission Energy by Segment](assets/screenshots/mission-energy-by-segment.png)

#### Remaining Energy by Segment
![Remaining Energy by Segment](assets/screenshots/remaining-energy-by-segment.png)

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