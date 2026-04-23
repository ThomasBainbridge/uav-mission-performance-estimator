# UAV Mission Performance Estimator

A browser-based engineering tool for fixed-wing UAV preliminary performance analysis and segmented mission evaluation. All calculations run client-side — no server, no installation, no runtime dependencies.

---

**Live demo:** https://thomasbainbridge.github.io/uav-performance-and-mission-analysis/

---

## What it does

Enter your UAV's design parameters and get immediate feedback on flight performance, mission feasibility, and energy consumption. The tool is built around a parametric aerodynamic and energy model suited to early-stage design studies and rapid trade analysis.

---

## Features

### Performance analysis

- ISA troposphere atmosphere model (h ≤ 11 000 m), with optional air density override
- Parabolic drag polar: `CD = CD₀ + CL²/(π·e·AR)`
- Full speed sweep from stall to 40 m/s — power, endurance, and range polars
- Three operating points identified numerically: best endurance, best still-air range, best wind-adjusted range
- Stall speed and minimum safe cruise speed (1.3 × V_stall)

### Energy and battery modelling

- Peukert correction: `f = (E_nom / P_total)^(n−1)` — reduces effective capacity at high discharge rates (n = 1 → ideal)
- Separate hotel load and payload electrical load, with a distinct loiter payload load
- Fixed reserve energy (Wh) or fractional reserve — mutually exclusive, fixed Wh takes priority
- Usable and mission-available energy computed per scenario

### Mission profile

- Segmented profile: climb → outbound cruise → loiter → return cruise → descent
- Per-leg wind speeds for accurate asymmetric round-trip analysis
- Payload drop mid-mission — set a return payload mass and all post-loiter segments (weight, drag, stall speed) update accordingly
- Stall margin check on every cruise and loiter segment — amber warning rows in the table where SM < 1.3
- Three cruise modes: fixed speed, best range, best wind-adjusted range

### Trade studies

- **1D trade study** — sweep any design parameter (battery mass, wing area, aspect ratio, CD₀, efficiency, altitude, cruise speed) across a user-defined range; plots range, endurance, and mission remaining energy
- **2D trade study** — sweep two parameters simultaneously and render a colour-mapped heatmap of any output metric; binary feasibility renders as red/green

### Scenario management

- Six built-in presets covering baseline, high-speed, long-range, windy, loiter-heavy, and delivery missions
- Save and load named scenarios in browser local storage
- Compare any two or more saved scenarios side-by-side with charts and a summary table

### Sharing and export

- URL state sharing — the active scenario is base64-encoded into the URL so a link reopens the exact configuration
- CSV download for every result table: speed sweep, operating points, mission segments, trade study, 2D trade, and scenario comparison
- JSON download of the active scenario configuration

---

## Physics summary

| Quantity | Model |
|---|---|
| Air density | ISA troposphere, or manual override |
| Lift coefficient | `CL = 2W / (ρV²S)` — level flight (L = W) |
| Drag | `CD = CD₀ + CL²/(π·e·AR)`,  `D = ½ρV²S·CD` |
| Power chain | `P_air = D·V`,  `P_total = P_air/η + P_hotel + P_payload` |
| Energy budget | `E_usable = E_nom × f_usable × f_Peukert` |
| Climb | `P_climb = P_level + m·g·Vc/η` (small-angle approx, evaluated at cruise speed) |
| Descent | `P_descent = f_d × (P_air/η) + P_np` |
| Wind | `V_ground = max(0, V_air − V_wind)` applied per leg |

The model is suited to early-stage design decisions and rapid sensitivity studies — it is not a substitute for high-fidelity CFD or flight dynamics simulation.

---

## File structure

```
├── index.html       — UI shell, tab layout, methodology collapsible
├── styles.css       — Design system (Syne · Space Grotesk · DM Mono)
└── js/
    ├── configs.js   — Preset configurations and validation reference data
    └── app.js       — All physics, rendering, and event logic
```

---

## Running locally

Any static file server works:

```bash
python3 -m http.server 8080
# open http://localhost:8080
```

---

## Deploying to GitHub Pages

1. Push the repository to GitHub
2. Go to **Settings → Pages → Source: Deploy from branch → main / (root)**
3. The tool is live at `https://<username>.github.io/<repo>/`

No build step required.

---

## Extending the tool

**Adding a preset** — add an entry to `PRESET_CONFIGS` in `js/configs.js`. All fields should be populated; set unused optional fields (e.g. `reserve_fraction` when `reserve_energy_wh` is set) to `null`.

**Adding a trade parameter** — add an entry to `TRADE_PARAMETERS` in `js/app.js`. Each entry needs a `label`, `get`, `set`, and default range hints (`minFactor`/`maxFactor` or `minFixed`/`maxPad`).

**Adding a 2D output metric** — add an entry to `TRADE2D_OUTPUT_METRICS` in `js/app.js` and ensure the key matches a field returned by `makeSummary()` or the mission profile result object.

---

## Author

Thomas Bainbridge
