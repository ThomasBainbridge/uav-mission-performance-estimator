# UAV Performance and Mission Analysis

A web-based engineering tool for estimating fixed-wing UAV performance and mission-profile behaviour from preliminary design inputs.

This project provides a parametric framework for evaluating UAV flight performance, mission feasibility, and energy consumption using simplified aerodynamic and propulsion models. It is designed for early-stage design studies, trade analysis, and rapid mission assessment.

The tool is deployed as a static web application using HTML, CSS, and JavaScript, enabling immediate access without requiring a Python runtime or backend server.

---

## Overview

The model evaluates UAV performance and mission execution by combining:

* steady-level flight performance analysis
* aerodynamic drag and power estimation
* endurance and range optimisation
* segmented mission modelling
* electrical power and energy accounting

The tool allows users to explore how design parameters and mission definitions influence feasibility, efficiency, and overall system performance.

---

## Key Features

### Performance Modelling

* Stall speed estimation
* Cruise speed constraints and recommendations
* Drag and power requirement calculations
* Airspeed sweep analysis
* Identification of:

  * best endurance speed
  * best range speed

### Mission Analysis

* Segmented mission modelling:

  * outbound
  * loiter
  * return
* Mission feasibility evaluation
* Total mission time and distance estimation
* Energy consumption tracking across all mission phases

### Energy and Electrical Modelling

* Propulsion power estimation
* Hotel (onboard systems) electrical load modelling
* Payload electrical load modelling
* Total electrical power and energy breakdown
* Per-segment and mission-level energy accounting

### Interactive Web Interface

* Browser-based parameter input
* Instant calculation and updates
* Clean visual presentation of results
* No installation or backend required

---

## Engineering Scope and Assumptions

The model is intended for **preliminary design and trade studies**. Key assumptions include:

* steady, quasi-level flight conditions
* simplified aerodynamic drag representation
* reduced-order propulsion modelling
* ISA-based atmospheric approximation
* no high-fidelity CFD or transient flight dynamics

The tool is not intended for detailed design validation but provides rapid insight into system-level behaviour.

---

## Project Evolution

The project has been developed in stages, progressing from a Python-based performance estimator to a fully deployable web-based engineering tool.

### Version 1 – Core Performance Estimator

* steady level-flight modelling
* drag, power, endurance, and range calculations
* airspeed sweeps and optimal speed identification

### Version 2 – Mission-Profile Analysis

* segmented mission modelling
* mission energy tracking
* scenario-based evaluation

### Version 3 – Interactive Application Layer

* user interface for parameter input and results visualisation
* real-time analysis capability

### Version 4 – Extended Mission Modelling

* climb and descent segment modelling
* altitude-dependent mission phases
* improved mission definition flexibility

### Version 5 – Electrical Energy Modelling

* inclusion of hotel and payload electrical loads
* full mission energy breakdown by source
* improved interpretation of energy usage

### Current Version – Web Deployment

* migration from Python/Streamlit to a static web application
* browser-based execution of the performance model
* permanent hosting via GitHub Pages

---

## Project Structure

```text
uav-mission-performance-estimator/
├── index.html          # Main application interface
├── styles.css          # Styling and layout
├── js/
│   └── app.js          # Core performance and mission model
├── assets/             # Images and static resources (optional)
└── README.md
```

---

## Usage

1. Open the deployed website
2. Enter UAV parameters:

   * mass
   * aerodynamic properties
   * propulsion characteristics
3. Define mission parameters:

   * speeds
   * distances
   * loiter duration
4. View:

   * performance outputs
   * mission feasibility
   * energy breakdown

All calculations are executed directly in the browser.

---

## Deployment

The application is hosted using GitHub Pages and runs entirely client-side.

No installation, Python environment, or server infrastructure is required.

---

## Future Work

Potential extensions include:

* integration of propeller performance data
* wind and atmospheric variability modelling
* optimisation routines for mission planning
* coupling with higher-fidelity aerodynamic models
* exportable reports and design summaries

---

## Author

Thomas Bainbridge


---
