# UAV Mission Performance Estimator

A Python-based engineering tool for estimating fixed-wing UAV performance and mission-profile behaviour from preliminary design inputs.

The project has been developed in stages, progressing from a core fixed-wing performance estimator to segmented mission-profile analysis and, most recently, a lightweight Streamlit front end.

## Version Overview

### Version 1 – Core Performance Estimator

Version 1 established the core fixed-wing UAV performance engine.

It introduced:

- fixed-wing steady level-flight performance modelling
- stall speed and minimum recommended cruise speed
- drag, power, endurance, and range calculations
- airspeed sweep analysis
- best-endurance and best-range speed identification
- comparison of multiple UAV configurations
- mission feasibility assessment at chosen cruise speed
- CSV export of results
- automatic plot generation

### Version 2 – Mission-Profile and Scenario Analysis

Version 2 extended the tool from single-point performance estimation into segmented mission analysis.

It introduced:

- reusable best-endurance, best-range, and best wind-adjusted range operating point selection
- config-driven segmented mission profiles
- outbound / loiter / return mission evaluation
- mission profile energy tracking by segment
- mission profile CSV export
- mission profile plot generation
- ISA atmosphere support using altitude-based density estimation
- CLI config selection
- mission scenario comparison across multiple YAML cases

### Version 3 – Streamlit Front End

Version 3 added a lightweight user-facing application layer on top of the existing analysis engine.

It introduced:

- a Streamlit interface for selecting YAML config files
- browser-based display of performance summary metrics
- operating point inspection
- mission feasibility and segmented mission-profile display
- mission scenario and configuration comparison in a simple UI
- a more accessible workflow without editing source code directly

## Example Outputs

### Power vs Airspeed
![Power vs Airspeed](assets/screenshots/power-vs-speed.png)

### Endurance vs Airspeed
![Endurance vs Airspeed](assets/screenshots/endurance-vs-speed.png)

### Range vs Airspeed
![Range vs Airspeed](assets/screenshots/range-vs-speed.png)

### Configuration Comparison
![Configuration Comparison](assets/screenshots/configuration-comparison.png)

### Mission Energy by Segment
![Mission Energy by Segment](assets/screenshots/mission-energy-by-segment.png)

### Remaining Energy by Segment
![Remaining Energy by Segment](assets/screenshots/remaining-energy-by-segment.png)

## How to Run

Run the CLI version with a selected config file:

```powershell
py -m uav_mpe.main --config configs/example_fixed_wing.yaml