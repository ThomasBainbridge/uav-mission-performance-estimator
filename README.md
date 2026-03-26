# UAV Mission Performance Estimator

A Python-based engineering tool for estimating fixed-wing UAV performance and mission-profile behaviour from preliminary design inputs.

The project has been developed in stages, progressing from a core fixed-wing performance estimator to segmented mission-profile analysis, a polished Streamlit front end for interactive trade studies, and more realistic mission-phase modelling.

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

### Version 4 – Extended Mission Modelling

Version 4 improved the physical realism of the mission model by introducing additional mission phases and more flexible mission-definition options.

It introduced:

- climb segment modelling using climb altitude and climb rate
- descent segment modelling using descent altitude, descent rate, and descent power factor
- segment-specific altitude support for outbound, loiter, and return phases
- reserve strategy options using either reserve fraction or fixed reserve energy
- richer config-driven mission definitions for more realistic mission studies
- backend mission-model extensions while keeping compatibility with the existing CLI and Streamlit workflows


## How to Run 

Run the CLI version with a selected config file:


py -m uav_mpe.main --config configs/example_fixed_wing.yaml


Run the Streamlit app:

streamlit run app/streamlit_app.py