# UAV Mission Performance Estimator

A Python-based engineering tool for estimating fixed-wing UAV performance and mission-profile behaviour from preliminary design inputs.

The project has been developed in stages, progressing from a core fixed-wing performance estimator to segmented mission-profile analysis and, most recently, a polished Streamlit front end for interactive trade studies.

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

### Version 3 – Interactive Streamlit Application

Version 3 added a user-facing application layer on top of the existing analysis engine and was later polished into a more complete engineering trade-study tool.

It introduced:

- a live Streamlit interface for loading YAML-based cases
- editable aircraft, mission, and environment inputs directly in the UI
- live performance, mission, and comparison charts
- CSV downloads for sweeps, mission summaries, scenario comparisons, and trade studies
- YAML download for edited active configurations
- saved scenario creation directly into the `configs/` folder
- saved-scenario comparison inside the app
- trade-study / sensitivity plots for key design parameters
- reset-to-base-config workflow
- clearer usability, layout, and assumptions/scope presentation

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