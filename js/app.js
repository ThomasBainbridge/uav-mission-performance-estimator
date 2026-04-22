
// ─────────────────────────────────────────────────────────────────────────────
// State
// ─────────────────────────────────────────────────────────────────────────────
const STORAGE_KEY     = "uav_mpe_saved_scenarios_v1";
const DEFAULT_PRESET_KEY = Object.keys(PRESET_CONFIGS)[0];
const charts = {};
let activePresetKey = DEFAULT_PRESET_KEY;
let baseConfig      = deepClone(PRESET_CONFIGS[DEFAULT_PRESET_KEY]);
let activeConfig    = deepClone(baseConfig);
let latestResults   = null;
let latestTradeStudy  = [];
let latestComparison  = [];
let latestTrade2dData = [];

// ─────────────────────────────────────────────────────────────────────────────
// Design tokens (must match styles.css)
// ─────────────────────────────────────────────────────────────────────────────
const CHART_PALETTE = ["#00c8ff", "#00e8a0", "#ffcc33", "#1a8cff", "#ff3d5a", "#c084fc"];

// ─────────────────────────────────────────────────────────────────────────────
// Field definitions
// ─────────────────────────────────────────────────────────────────────────────
const FIELD_GROUPS = {
  aircraft: [
    ["empty_mass_kg",                    "Empty mass [kg]",                       0.1],
    ["payload_mass_kg",                  "Payload mass [kg]",                     0.1],
    ["battery_mass_kg",                  "Battery mass [kg]",                     0.1],
    ["battery_specific_energy_wh_per_kg","Battery specific energy [Wh/kg]",       1  ],
    ["wing_area_m2",                     "Wing area [m²]",                        0.01],
    ["aspect_ratio",                     "Aspect ratio [-]",                      0.1],
    ["oswald_efficiency",                "Oswald efficiency [-]",                 0.01],
    ["cd0",                              "Cd0 [-]",                               0.001],
    ["cl_max",                           "Cl_max [-]",                            0.01],
    ["eta_total",                        "Total propulsion efficiency [-]",       0.01],
    ["hotel_load_w",                     "Hotel load [W]",                        1  ],
    ["payload_load_w",                   "Payload load [W]",                      1  ],
    ["loiter_payload_load_w",            "Loiter payload load [W]",               1  ],
    ["peukert_exponent",                 "Peukert exponent [-] (1 = ideal)",      0.01],
  ],
  environment: [
    ["altitude_m",              "Altitude [m]",                   10  ],
    ["air_density_kg_per_m3",   "Override air density [kg/m³]",   0.001],
    ["wind_speed_m_per_s",      "General wind speed [m/s]",       0.1 ],
    ["g_m_per_s2",              "g [m/s²]",                       0.01],
  ],
  mission: [
    ["usable_battery_fraction", "Usable battery fraction [-]",              0.01],
    ["reserve_energy_wh",       "Fixed reserve [Wh] (takes priority)",      1  ],
    ["reserve_fraction",        "Reserve fraction [-] (ignored if Wh set)", 0.01],
    ["cruise_speed_m_per_s",    "Cruise speed [m/s]",                       0.1],
    ["required_distance_km",    "Required distance [km]",                   0.1],
  ],
  profile: [
    ["climb_altitude_m",              "Climb altitude [m]",                        10  ],
    ["climb_rate_m_per_s",            "Climb rate [m/s]",                          0.1 ],
    ["outbound_distance_km",          "Outbound distance [km]",                    0.1 ],
    ["outbound_altitude_m",           "Outbound altitude [m]",                     10  ],
    ["loiter_duration_min",           "Loiter duration [min]",                     1   ],
    ["loiter_altitude_m",             "Loiter altitude [m]",                       10  ],
    ["return_distance_km",            "Return distance [km]",                      0.1 ],
    ["return_altitude_m",             "Return altitude [m]",                       10  ],
    ["return_payload_mass_kg",        "Return payload mass [kg] (blank = no drop)", 0.1],
    ["descent_altitude_m",            "Descent altitude [m]",                      10  ],
    ["descent_rate_m_per_s",          "Descent rate [m/s]",                        0.1 ],
    ["descent_power_factor",          "Descent power factor [-]",                  0.01],
    ["outbound_wind_speed_m_per_s",   "Outbound wind speed [m/s]",                 0.1 ],
    ["return_wind_speed_m_per_s",     "Return wind speed [m/s]",                   0.1 ],
  ],
};

const TRADE_PARAMETERS = {
  battery_mass_kg:    { label: "Battery mass [kg]",       get: c=>c.aircraft.battery_mass_kg,              set:(c,v)=>c.aircraft.battery_mass_kg=v,             minFactor:0.5, maxFactor:2.0,  step:0.1   },
  wing_area_m2:       { label: "Wing area [m²]",          get: c=>c.aircraft.wing_area_m2,                 set:(c,v)=>c.aircraft.wing_area_m2=v,                minFactor:0.6, maxFactor:1.8,  step:0.01  },
  aspect_ratio:       { label: "Aspect ratio [-]",        get: c=>c.aircraft.aspect_ratio,                 set:(c,v)=>c.aircraft.aspect_ratio=v,                minFactor:0.6, maxFactor:1.8,  step:0.1   },
  payload_mass_kg:    { label: "Payload mass [kg]",       get: c=>c.aircraft.payload_mass_kg,              set:(c,v)=>c.aircraft.payload_mass_kg=v,             minFactor:0.5, maxFactor:2.0,  step:0.1   },
  cd0:                { label: "Cd0 [-]",                 get: c=>c.aircraft.cd0,                          set:(c,v)=>c.aircraft.cd0=v,                         minFactor:0.5, maxFactor:2.0,  step:0.001 },
  eta_total:          { label: "Total efficiency [-]",    get: c=>c.aircraft.eta_total,                    set:(c,v)=>c.aircraft.eta_total=v,                   minFactor:0.7, maxFactor:1.0,  step:0.01  },
  altitude_m:         { label: "Altitude [m]",            get: c=>c.environment.altitude_m??0,             set:(c,v)=>{c.environment.altitude_m=v;c.environment.air_density_kg_per_m3=null;}, minFixed:0, maxPad:3000, step:10 },
  cruise_speed_m_per_s:{ label:"Cruise speed [m/s]",      get: c=>c.mission.cruise_speed_m_per_s,          set:(c,v)=>c.mission.cruise_speed_m_per_s=v,         minFactor:0.6, maxFactor:1.8,  step:0.1   },
};

const TRADE2D_OUTPUT_METRICS = {
  still_air_range_km:        "Still-air range [km]",
  wind_adjusted_range_km:    "Wind-adj. range [km]",
  endurance_h:               "Endurance [h]",
  electrical_power_required_w: "Electrical power [W]",
  stall_speed_m_per_s:       "Stall speed [m/s]",
  profile_remaining_energy_wh: "Profile remaining energy [Wh]",
  profile_feasible_flag:     "Profile feasible (0/1)",
};

// ─────────────────────────────────────────────────────────────────────────────
// Speed-sweep cache  (cleared at top of every renderAll call)
// ─────────────────────────────────────────────────────────────────────────────
const sweepCache = new Map();

function sweepCacheKey(config, maxSpeed, numPoints, effectiveMinSpeed) {
  const a = config.aircraft;
  const e = config.environment;
  const m = config.mission;
  return JSON.stringify([
    a.empty_mass_kg, a.payload_mass_kg, a.battery_mass_kg,
    a.battery_specific_energy_wh_per_kg, a.wing_area_m2,
    a.aspect_ratio, a.oswald_efficiency, a.cd0, a.cl_max, a.eta_total,
    a.hotel_load_w, a.payload_load_w, a.peukert_exponent ?? 1.0,
    e.altitude_m, e.air_density_kg_per_m3, e.wind_speed_m_per_s, e.g_m_per_s2,
    m.usable_battery_fraction, m.reserve_energy_wh, m.reserve_fraction,
    maxSpeed, numPoints, effectiveMinSpeed,
  ]);
}

// ─────────────────────────────────────────────────────────────────────────────
// Utilities
// ─────────────────────────────────────────────────────────────────────────────
function deepClone(obj) { return JSON.parse(JSON.stringify(obj)); }
function isNil(v)       { return v === null || v === undefined || v === ""; }

function sanitizeNumber(value) {
  if (value === "" || value === null || value === undefined) return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function fmt(value, digits = 2) {
  if (!Number.isFinite(value)) return "∞";
  return Number(value).toFixed(digits);
}

function fmtMetric(value, unit = "", digits = 2) {
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return `${fmt(value, digits)}${unit}`;
}

function downloadText(filename, text, mime = "text/plain") {
  const blob = new Blob([text], { type: mime });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

function rowsToCSV(rows) {
  if (!rows.length) return "";
  const headers = [...new Set(rows.flatMap(r => Object.keys(r)))];
  const escape = v => {
    if (v === null || v === undefined) return "";
    const s = String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return [headers.join(","), ...rows.map(r => headers.map(h => escape(r[h])).join(","))].join("\n");
}

function toTitle(v) { return v.replace(/_/g, " "); }

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1,3), 16);
  const g = parseInt(hex.slice(3,5), 16);
  const b = parseInt(hex.slice(5,7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

function debounce(fn, ms) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

// ─────────────────────────────────────────────────────────────────────────────
// URL state sharing
// ─────────────────────────────────────────────────────────────────────────────
function configToParam(config) {
  try { return btoa(JSON.stringify(config)); } catch { return null; }
}
function configFromParam(str) {
  try { return JSON.parse(atob(str)); } catch { return null; }
}
function buildShareUrl(config) {
  const param = configToParam(config);
  if (!param) return null;
  const url = new URL(window.location.href.split("?")[0]);
  url.searchParams.set("s", param);
  return url.toString();
}
function loadFromUrl() {
  const p = new URLSearchParams(window.location.search).get("s");
  if (!p) return false;
  const cfg = configFromParam(p);
  if (!cfg) return false;
  baseConfig = deepClone(cfg);
  activeConfig = deepClone(cfg);
  return true;
}

function showToast(msg) {
  const el = document.getElementById("shareToast");
  el.textContent = msg;
  el.classList.add("is-visible");
  setTimeout(() => el.classList.remove("is-visible"), 2400);
}

// ─────────────────────────────────────────────────────────────────────────────
// Physics — atmosphere & basic quantities
// ─────────────────────────────────────────────────────────────────────────────
function isaDensityKgPerM3(altitudeM) {
  if (altitudeM < 0)     throw new Error("altitude_m must be non-negative.");
  if (altitudeM > 11000) throw new Error("ISA model supports altitudes up to 11 000 m.");
  const t0 = 288.15, p0 = 101325.0, lapse = 0.0065, R = 287.05, g0 = 9.80665;
  const T = t0 - lapse * altitudeM;
  const P = p0 * Math.pow(T / t0, g0 / (R * lapse));
  return P / (R * T);
}
function getAirDensityKgPerM3(config) {
  const env = config.environment;
  if (!isNil(env.air_density_kg_per_m3)) return env.air_density_kg_per_m3;
  if (isNil(env.altitude_m))             throw new Error("Environment must define either air density or altitude.");
  return isaDensityKgPerM3(env.altitude_m);
}
function totalMassKg(config)    { return config.aircraft.empty_mass_kg + config.aircraft.payload_mass_kg + config.aircraft.battery_mass_kg; }
function weightNewtons(config)  { return totalMassKg(config) * config.environment.g_m_per_s2; }

// ─────────────────────────────────────────────────────────────────────────────
// Battery energy (including Peukert correction)
// ─────────────────────────────────────────────────────────────────────────────
function batteryNominalEnergyWh(config) {
  return config.aircraft.battery_mass_kg * config.aircraft.battery_specific_energy_wh_per_kg;
}

// Peukert correction factor: f = (E_nom / P_total)^(n-1)
// Reference: 1-hour discharge rate. n=1 → no correction (ideal).
function peukertFactor(config) {
  const n = config.aircraft.peukert_exponent ?? 1.0;
  if (Math.abs(n - 1.0) < 1e-9) return 1.0;
  const e_nom   = batteryNominalEnergyWh(config);       // Wh
  const p_total = electricalPowerRequiredWatts(config); // W (no circular dep)
  if (p_total <= 0) return 1.0;
  return Math.pow(e_nom / p_total, n - 1.0);
}

function batteryUsableEnergyWh(config) {
  return batteryNominalEnergyWh(config) * config.mission.usable_battery_fraction * peukertFactor(config);
}

function reserveEnergyWh(config) {
  const usable = batteryUsableEnergyWh(config);
  if (!isNil(config.mission.reserve_energy_wh)) {
    if (config.mission.reserve_energy_wh > usable)
      throw new Error("reserve_energy_wh cannot exceed usable battery energy.");
    return config.mission.reserve_energy_wh;
  }
  if (!isNil(config.mission.reserve_fraction)) return usable * config.mission.reserve_fraction;
  return 0;
}

function batteryAvailableForMissionWh(config) { return batteryUsableEnergyWh(config) - reserveEnergyWh(config); }
function batteryAvailableForMissionJ(config)  { return batteryAvailableForMissionWh(config) * 3600; }

// ─────────────────────────────────────────────────────────────────────────────
// Aerodynamics & power
// ─────────────────────────────────────────────────────────────────────────────
function stallSpeedMps(config) {
  return Math.sqrt((2 * weightNewtons(config)) / (getAirDensityKgPerM3(config) * config.aircraft.wing_area_m2 * config.aircraft.cl_max));
}
function minimumRecommendedCruiseSpeedMps(config, margin = 1.3) { return margin * stallSpeedMps(config); }
function liftCoefficient(config) {
  const w = weightNewtons(config), rho = getAirDensityKgPerM3(config);
  const v = config.mission.cruise_speed_m_per_s, s = config.aircraft.wing_area_m2;
  return w / (0.5 * rho * v * v * s);
}
function inducedDragFactor(config)  { return 1 / (Math.PI * config.aircraft.oswald_efficiency * config.aircraft.aspect_ratio); }
function dragCoefficient(config)    { const cl = liftCoefficient(config); return config.aircraft.cd0 + inducedDragFactor(config) * cl * cl; }
function dragForceNewtons(config) {
  const rho = getAirDensityKgPerM3(config), v = config.mission.cruise_speed_m_per_s, s = config.aircraft.wing_area_m2;
  return 0.5 * rho * v * v * s * dragCoefficient(config);
}
function airPowerRequiredWatts(config)                 { return dragForceNewtons(config) * config.mission.cruise_speed_m_per_s; }
function propulsionElectricalPowerRequiredWatts(config){ return airPowerRequiredWatts(config) / config.aircraft.eta_total; }
function hotelLoadWatts(config)                        { return config.aircraft.hotel_load_w; }
function payloadLoadWatts(config)                      { return config.aircraft.payload_load_w; }
function nonPropulsiveElectricalLoadWatts(config)      { return hotelLoadWatts(config) + payloadLoadWatts(config); }
function electricalPowerRequiredWatts(config)          { return propulsionElectricalPowerRequiredWatts(config) + nonPropulsiveElectricalLoadWatts(config); }

// ─────────────────────────────────────────────────────────────────────────────
// Endurance, range, mission feasibility
// ─────────────────────────────────────────────────────────────────────────────
function enduranceSeconds(config) { return batteryAvailableForMissionJ(config) / electricalPowerRequiredWatts(config); }
function enduranceHours(config)   { return enduranceSeconds(config) / 3600; }
function stillAirRangeKm(config)  { return config.mission.cruise_speed_m_per_s * enduranceSeconds(config) / 1000; }

// NOTE: single-leg wind model — conservative one-way headwind estimate.
// For accurate round-trip analysis use the segmented Mission profile (per-leg winds).
function windAdjustedGroundSpeedMps(config) { return Math.max(0, config.mission.cruise_speed_m_per_s - config.environment.wind_speed_m_per_s); }
function windAdjustedRangeKm(config)        { return windAdjustedGroundSpeedMps(config) * enduranceSeconds(config) / 1000; }

function requiredDistanceKm(config) {
  if (isNil(config.mission.required_distance_km)) throw new Error("Mission required distance is not set.");
  return config.mission.required_distance_km;
}
// Same single-leg wind caveat as windAdjustedRangeKm
function requiredMissionTimeHours(config) {
  const gs = windAdjustedGroundSpeedMps(config);
  if (gs <= 0) return Infinity;
  return requiredDistanceKm(config) / (gs * 3.6);
}
function requiredMissionEnergyWh(config) { return electricalPowerRequiredWatts(config) * requiredMissionTimeHours(config); }
function rangeMarginKm(config)   { return windAdjustedRangeKm(config) - requiredDistanceKm(config); }
function energyMarginWh(config)  { return batteryAvailableForMissionWh(config) - requiredMissionEnergyWh(config); }
function isMissionFeasible(config) {
  return windAdjustedGroundSpeedMps(config) > 0 && rangeMarginKm(config) >= 0 && energyMarginWh(config) >= 0;
}

// ─────────────────────────────────────────────────────────────────────────────
// Segment helpers
// ─────────────────────────────────────────────────────────────────────────────
function configWithFlightConditions(config, airspeed, windSpeed, altitude = null) {
  const c = deepClone(config);
  c.mission.cruise_speed_m_per_s  = airspeed;
  c.environment.wind_speed_m_per_s = windSpeed;
  if (!isNil(altitude)) { c.environment.altitude_m = altitude; c.environment.air_density_kg_per_m3 = null; }
  return c;
}

function climbTimeHours(altitude, rate) {
  if (altitude < 0 || rate <= 0) throw new Error("Invalid climb inputs.");
  return (altitude / rate) / 3600;
}
// Climb drag evaluated at cruise speed — small-angle approx (γ < ~10°)
function climbExtraPowerWatts(config, rate)        { return (totalMassKg(config) * config.environment.g_m_per_s2 * rate) / config.aircraft.eta_total; }
function climbTotalElectricalPowerWatts(config, rate){ return electricalPowerRequiredWatts(config) + climbExtraPowerWatts(config, rate); }
function climbEnergyWh(config, altitude, rate)       { return climbTotalElectricalPowerWatts(config, rate) * climbTimeHours(altitude, rate); }

function descentTimeHours(altitude, rate) {
  if (altitude < 0 || rate <= 0) throw new Error("Invalid descent inputs.");
  return (altitude / rate) / 3600;
}
// Descent power = fraction of cruise propulsion power. Descent rate only affects duration.
function descentTotalElectricalPowerWatts(config, factor) {
  return factor * (airPowerRequiredWatts(config) / config.aircraft.eta_total) + nonPropulsiveElectricalLoadWatts(config);
}
function descentEnergyWh(config, altitude, rate, factor) {
  return descentTotalElectricalPowerWatts(config, factor) * descentTimeHours(altitude, rate);
}

function segmentBreakdownFields(config, totalElectricalPowerW, timeH) {
  const hotel = hotelLoadWatts(config), payload = payloadLoadWatts(config);
  const nonProp = nonPropulsiveElectricalLoadWatts(config);
  const propulsion = totalElectricalPowerW - nonProp;
  return {
    propulsion_electrical_power_w: propulsion,
    hotel_load_w:    hotel,
    payload_load_w:  payload,
    non_propulsive_electrical_load_w: nonProp,
    propulsion_energy_wh:  propulsion * timeH,
    hotel_energy_wh:       hotel    * timeH,
    payload_energy_wh:     payload  * timeH,
    non_propulsive_energy_wh: nonProp * timeH,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Speed sweep (cached)
// ─────────────────────────────────────────────────────────────────────────────
function buildSpeedSweep(config, maxSpeed = 40, numPoints = 120, minSpeed = null) {
  const vMin = isNil(minSpeed) ? minimumRecommendedCruiseSpeedMps(config) : Number(minSpeed);
  if (maxSpeed <= vMin) throw new Error(`max_speed_m_per_s must be greater than ${vMin.toFixed(2)}.`);
  if (numPoints < 2)    throw new Error("num_points must be at least 2.");

  const cacheKey = sweepCacheKey(config, maxSpeed, numPoints, vMin);
  if (sweepCache.has(cacheKey)) return sweepCache.get(cacheKey);

  const rows = [];
  for (let i = 0; i < numPoints; i++) {
    const v = vMin + (i * (maxSpeed - vMin)) / (numPoints - 1);
    const sc = deepClone(config);
    sc.mission.cruise_speed_m_per_s = v;
    rows.push({
      airspeed_m_per_s:              v,
      lift_coefficient:              liftCoefficient(sc),
      induced_drag_factor:           inducedDragFactor(sc),
      drag_coefficient:              dragCoefficient(sc),
      drag_force_n:                  dragForceNewtons(sc),
      air_power_w:                   airPowerRequiredWatts(sc),
      propulsion_electrical_power_w: propulsionElectricalPowerRequiredWatts(sc),
      hotel_load_w:                  hotelLoadWatts(sc),
      payload_load_w:                payloadLoadWatts(sc),
      non_propulsive_electrical_load_w: nonPropulsiveElectricalLoadWatts(sc),
      electrical_power_w:            electricalPowerRequiredWatts(sc),
      endurance_h:                   enduranceHours(sc),
      still_air_range_km:            stillAirRangeKm(sc),
      wind_adjusted_ground_speed_m_per_s: windAdjustedGroundSpeedMps(sc),
      wind_adjusted_range_km:        windAdjustedRangeKm(sc),
    });
  }

  sweepCache.set(cacheKey, rows);
  return rows;
}

function maxBy(rows, key) { return rows.reduce((best, row) => row[key] > best[key] ? row : best, rows[0]); }
function getBestEnduranceOperatingPoint(config, maxSpeed=40, numPoints=120)          { return maxBy(buildSpeedSweep(config, maxSpeed, numPoints), "endurance_h"); }
function getBestRangeOperatingPoint(config, maxSpeed=40, numPoints=120)             { return maxBy(buildSpeedSweep(config, maxSpeed, numPoints), "still_air_range_km"); }
function getBestWindAdjustedRangeOperatingPoint(config, maxSpeed=40, numPoints=120) { return maxBy(buildSpeedSweep(config, maxSpeed, numPoints), "wind_adjusted_range_km"); }

// ─────────────────────────────────────────────────────────────────────────────
// Cruise segment
// ─────────────────────────────────────────────────────────────────────────────
function evaluateCruiseSegment(config, mode, segmentName, distanceKm, windSpeed=0, altitude=null, maxSpeed=40, numPoints=120) {
  let airspeed;
  if (mode === "fixed_speed") {
    airspeed = config.mission.cruise_speed_m_per_s;
  } else if (mode === "best_range") {
    const cfg = configWithFlightConditions(config, config.mission.cruise_speed_m_per_s, windSpeed, altitude);
    airspeed = getBestRangeOperatingPoint(cfg, maxSpeed, numPoints).airspeed_m_per_s;
  } else if (mode === "best_wind_adjusted_range") {
    const cfg = configWithFlightConditions(config, config.mission.cruise_speed_m_per_s, windSpeed, altitude);
    airspeed = getBestWindAdjustedRangeOperatingPoint(cfg, maxSpeed, numPoints).airspeed_m_per_s;
  } else {
    throw new Error(`Unsupported cruise mode: ${mode}`);
  }

  const segCfg       = configWithFlightConditions(config, airspeed, windSpeed, altitude);
  const electricalPowerW = electricalPowerRequiredWatts(segCfg);
  const groundSpeed  = windAdjustedGroundSpeedMps(segCfg);
  const timeH        = groundSpeed <= 0 ? Infinity : distanceKm / (groundSpeed * 3.6);
  const energyUsedWh = electricalPowerW * timeH;

  // Stall margin check
  const vStall       = stallSpeedMps(segCfg);
  const stallMargin  = airspeed / vStall;
  const stallMarginOk = stallMargin >= 1.3;

  return {
    segment_name: segmentName,
    segment_type: "cruise",
    speed_mode:   mode,
    distance_km:  distanceKm,
    altitude_m:   altitude,
    airspeed_m_per_s:    airspeed,
    ground_speed_m_per_s: groundSpeed,
    stall_speed_m_per_s: vStall,
    stall_margin:        stallMargin,
    stall_margin_ok:     stallMarginOk,
    electrical_power_w:  electricalPowerW,
    time_h:              timeH,
    duration_min:        timeH * 60,
    energy_used_wh:      energyUsedWh,
    ...segmentBreakdownFields(segCfg, electricalPowerW, timeH),
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Loiter segment
// ─────────────────────────────────────────────────────────────────────────────
function evaluateLoiterSegmentBestEndurance(config, segmentName, durationMin, altitude=null, maxSpeed=40, numPoints=120) {
  const selCfg = deepClone(config);
  if (!isNil(altitude)) { selCfg.environment.altitude_m = altitude; selCfg.environment.air_density_kg_per_m3 = null; }
  if (!isNil(selCfg.aircraft.loiter_payload_load_w)) selCfg.aircraft.payload_load_w = selCfg.aircraft.loiter_payload_load_w;

  const op           = getBestEnduranceOperatingPoint(selCfg, maxSpeed, numPoints);
  const timeH        = durationMin / 60;
  const airspeed     = op.airspeed_m_per_s;
  const electricalPowerW = op.electrical_power_w;

  // Stall margin at loiter speed & altitude
  const brkCfg = deepClone(selCfg);
  brkCfg.mission.cruise_speed_m_per_s = airspeed;
  const vStall     = stallSpeedMps(brkCfg);
  const stallMargin = airspeed / vStall;

  return {
    segment_name: segmentName,
    segment_type: "loiter",
    speed_mode:   "best_endurance",
    duration_min: durationMin,
    altitude_m:   altitude,
    airspeed_m_per_s:    airspeed,
    stall_speed_m_per_s: vStall,
    stall_margin:        stallMargin,
    stall_margin_ok:     stallMargin >= 1.3,
    electrical_power_w:  electricalPowerW,
    time_h:              timeH,
    energy_used_wh:      electricalPowerW * timeH,
    ...segmentBreakdownFields(brkCfg, electricalPowerW, timeH),
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Mission profile
// ─────────────────────────────────────────────────────────────────────────────
function evaluateSimpleMissionProfile(config, profile, maxSpeed=40, numPoints=120) {
  const segments = [];
  const addSegment = seg => {
    const prev = segments.length ? segments[segments.length - 1].remaining_energy_wh_after_segment : batteryAvailableForMissionWh(config);
    seg.remaining_energy_wh_after_segment = prev - seg.energy_used_wh;
    segments.push(seg);
  };

  // ── Climb ──
  if (!isNil(profile.climb_altitude_m) && !isNil(profile.climb_rate_m_per_s)) {
    const pW   = climbTotalElectricalPowerWatts(config, profile.climb_rate_m_per_s);
    const timeH = climbTimeHours(profile.climb_altitude_m, profile.climb_rate_m_per_s);
    addSegment({
      segment_name: "climb",
      segment_type: "climb",
      speed_mode:   "fixed_climb",
      climb_altitude_m:  profile.climb_altitude_m,
      climb_rate_m_per_s: profile.climb_rate_m_per_s,
      electrical_power_w: pW,
      time_h:      timeH,
      duration_min: timeH * 60,
      energy_used_wh: climbEnergyWh(config, profile.climb_altitude_m, profile.climb_rate_m_per_s),
      stall_speed_m_per_s: stallSpeedMps(config),
      stall_margin: null,
      stall_margin_ok: null,
      ...segmentBreakdownFields(config, pW, timeH),
    });
  }

  // ── Outbound cruise ──
  addSegment(evaluateCruiseSegment(config, profile.cruise_mode, "outbound",
    profile.outbound_distance_km, profile.outbound_wind_speed_m_per_s ?? 0,
    profile.outbound_altitude_m, maxSpeed, numPoints));

  // ── Loiter ──
  if (!isNil(profile.loiter_duration_min)) {
    addSegment(evaluateLoiterSegmentBestEndurance(config, "loiter",
      profile.loiter_duration_min, profile.loiter_altitude_m, maxSpeed, numPoints));
  }

  // ── Payload drop: swap mass for return + descent if return_payload_mass_kg set ──
  let returnConfig = config;
  if (!isNil(profile.return_payload_mass_kg)) {
    returnConfig = deepClone(config);
    returnConfig.aircraft.payload_mass_kg = profile.return_payload_mass_kg;
  }

  // ── Return cruise ──
  if (!isNil(profile.return_distance_km)) {
    addSegment(evaluateCruiseSegment(returnConfig, profile.cruise_mode, "return",
      profile.return_distance_km, profile.return_wind_speed_m_per_s ?? 0,
      profile.return_altitude_m, maxSpeed, numPoints));
  }

  // ── Descent ──
  if (!isNil(profile.descent_altitude_m) && !isNil(profile.descent_rate_m_per_s)) {
    const pW    = descentTotalElectricalPowerWatts(returnConfig, profile.descent_power_factor);
    const timeH = descentTimeHours(profile.descent_altitude_m, profile.descent_rate_m_per_s);
    addSegment({
      segment_name: "descent",
      segment_type: "descent",
      speed_mode:   "fixed_descent",
      descent_altitude_m:  profile.descent_altitude_m,
      descent_rate_m_per_s: profile.descent_rate_m_per_s,
      descent_power_factor: profile.descent_power_factor,
      electrical_power_w:   pW,
      time_h:      timeH,
      duration_min: timeH * 60,
      energy_used_wh: descentEnergyWh(returnConfig, profile.descent_altitude_m, profile.descent_rate_m_per_s, profile.descent_power_factor),
      stall_speed_m_per_s: stallSpeedMps(returnConfig),
      stall_margin: null,
      stall_margin_ok: null,
      ...segmentBreakdownFields(returnConfig, pW, timeH),
    });
  }

  const finite = segments.filter(s => Number.isFinite(s.energy_used_wh));
  const totalTimeH            = segments.reduce((sum, s) => sum + s.time_h, 0);
  const totalEnergyUsedWh     = segments.reduce((sum, s) => sum + s.energy_used_wh, 0);
  const totalPropulsionWh     = finite.reduce((sum, s) => sum + s.propulsion_energy_wh, 0);
  const totalHotelWh          = finite.reduce((sum, s) => sum + s.hotel_energy_wh, 0);
  const totalPayloadWh        = finite.reduce((sum, s) => sum + s.payload_energy_wh, 0);
  const totalNonPropWh        = finite.reduce((sum, s) => sum + s.non_propulsive_energy_wh, 0);
  const availableEnergyWh     = batteryAvailableForMissionWh(config);
  const remainingEnergyWh     = availableEnergyWh - totalEnergyUsedWh;
  const anyStallWarning       = segments.some(s => s.stall_margin_ok === false);

  return {
    available_energy_wh:         availableEnergyWh,
    total_time_h:                totalTimeH,
    total_energy_used_wh:        totalEnergyUsedWh,
    total_propulsion_energy_wh:  totalPropulsionWh,
    total_hotel_energy_wh:       totalHotelWh,
    total_payload_energy_wh:     totalPayloadWh,
    total_non_propulsive_energy_wh: totalNonPropWh,
    remaining_energy_wh:         remainingEnergyWh,
    mission_feasible: Number.isFinite(totalEnergyUsedWh) && remainingEnergyWh >= 0,
    any_stall_warning: anyStallWarning,
    segments,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Summary
// ─────────────────────────────────────────────────────────────────────────────
function makeSummary(config) {
  return {
    total_mass_kg:                       totalMassKg(config),
    weight_n:                            weightNewtons(config),
    resolved_air_density_kg_per_m3:      getAirDensityKgPerM3(config),
    stall_speed_m_per_s:                 stallSpeedMps(config),
    minimum_recommended_cruise_speed_m_per_s: minimumRecommendedCruiseSpeedMps(config),
    battery_nominal_energy_wh:           batteryNominalEnergyWh(config),
    battery_usable_energy_wh:            batteryUsableEnergyWh(config),
    reserve_energy_wh:                   reserveEnergyWh(config),
    battery_available_for_mission_wh:    batteryAvailableForMissionWh(config),
    air_power_required_w:                airPowerRequiredWatts(config),
    propulsion_electrical_power_required_w: propulsionElectricalPowerRequiredWatts(config),
    hotel_load_w:                        hotelLoadWatts(config),
    payload_load_w:                      payloadLoadWatts(config),
    non_propulsive_electrical_load_w:    nonPropulsiveElectricalLoadWatts(config),
    electrical_power_required_w:         electricalPowerRequiredWatts(config),
    endurance_h:                         enduranceHours(config),
    still_air_range_km:                  stillAirRangeKm(config),
    wind_adjusted_range_km:              windAdjustedRangeKm(config),
  };
}

function compareSavedScenarios(names) {
  const saved = getSavedScenarios();
  return names.map(name => {
    const cfg     = saved[name];
    const profile = evaluateSimpleMissionProfile(cfg, cfg.mission.profile);
    return {
      scenario:                  name,
      mission_feasible:          profile.mission_feasible,
      available_energy_wh:       profile.available_energy_wh,
      total_time_h:              profile.total_time_h,
      total_energy_used_wh:      profile.total_energy_used_wh,
      total_propulsion_energy_wh: profile.total_propulsion_energy_wh,
      total_hotel_energy_wh:     profile.total_hotel_energy_wh,
      total_payload_energy_wh:   profile.total_payload_energy_wh,
      total_non_propulsive_energy_wh: profile.total_non_propulsive_energy_wh,
      remaining_energy_wh:       profile.remaining_energy_wh,
      number_of_segments:        profile.segments.length,
      outbound_distance_km:      cfg.mission.profile.outbound_distance_km,
      loiter_duration_min:       cfg.mission.profile.loiter_duration_min,
      return_distance_km:        cfg.mission.profile.return_distance_km,
      cruise_mode:               cfg.mission.profile.cruise_mode,
    };
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// localStorage helpers
// ─────────────────────────────────────────────────────────────────────────────
function getSavedScenarios()          { try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}"); } catch { return {}; } }
function saveSavedScenarios(saved)    { localStorage.setItem(STORAGE_KEY, JSON.stringify(saved)); }

// ─────────────────────────────────────────────────────────────────────────────
// Form building & sync
// ─────────────────────────────────────────────────────────────────────────────
function syncPresetControls() {
  const sel = document.getElementById("presetSelect");
  sel.innerHTML = Object.keys(PRESET_CONFIGS).map(n => `<option value="${n}">${n}</option>`).join("");
  sel.value = activePresetKey;
  refreshSavedScenarioLists();
}

function refreshSavedScenarioLists() {
  const saved   = getSavedScenarios();
  const options = Object.keys(saved).sort();
  const html    = options.map(n => `<option value="${n}">${n}</option>`).join("");
  document.getElementById("savedScenarioSelect").innerHTML = html;
  document.getElementById("compareScenarios").innerHTML    = html;
}

function buildInputFields() {
  Object.entries(FIELD_GROUPS).forEach(([groupKey, fields]) => {
    const container = document.getElementById(`${groupKey}Fields`);
    container.innerHTML = "";
    fields.forEach(([fieldKey, label, step]) => {
      const wrapper = document.createElement("label");
      wrapper.className = "field";
      wrapper.innerHTML = `<span>${label}</span><input type="number" step="${step}" data-group="${groupKey}" data-field="${fieldKey}">`;
      container.appendChild(wrapper);
    });
    if (groupKey === "profile") {
      const modeField = document.createElement("label");
      modeField.className = "field";
      modeField.innerHTML = `<span>Cruise mode</span>
        <select data-group="profile" data-field="cruise_mode">
          <option value="fixed_speed">Fixed speed</option>
          <option value="best_range">Best range</option>
          <option value="best_wind_adjusted_range">Best wind-adjusted range</option>
        </select>`;
      container.appendChild(modeField);
    }
  });
  document.querySelectorAll("[data-group][data-field]").forEach(el => {
    el.addEventListener("input",  onFieldChange);
    el.addEventListener("change", onFieldChange);
  });
}

function onFieldChange(event) {
  const { group, field } = event.target.dataset;
  const target = group === "profile" ? activeConfig.mission.profile : activeConfig[group];
  if (!target) return;
  if (event.target.tagName === "SELECT") {
    target[field] = event.target.value;
  } else {
    target[field] = sanitizeNumber(event.target.value);
  }
  // Mutual exclusion for reserve fields
  if (group === "mission" && field === "reserve_energy_wh" && !isNil(activeConfig.mission.reserve_energy_wh)) {
    activeConfig.mission.reserve_fraction = null;
    const el = document.querySelector('[data-group="mission"][data-field="reserve_fraction"]');
    if (el) el.value = "";
  } else if (group === "mission" && field === "reserve_fraction" && !isNil(activeConfig.mission.reserve_fraction)) {
    activeConfig.mission.reserve_energy_wh = null;
    const el = document.querySelector('[data-group="mission"][data-field="reserve_energy_wh"]');
    if (el) el.value = "";
  }
  debouncedRenderAll();
}

function populateForm(config) {
  Object.entries(FIELD_GROUPS).forEach(([groupKey, fields]) => {
    fields.forEach(([fieldKey]) => {
      const el     = document.querySelector(`[data-group="${groupKey}"][data-field="${fieldKey}"]`);
      const source = groupKey === "profile" ? config.mission.profile : config[groupKey];
      const value  = source?.[fieldKey];
      el.value = isNil(value) ? "" : value;
    });
  });
  const modeEl = document.querySelector('[data-group="profile"][data-field="cruise_mode"]');
  if (modeEl) modeEl.value = config.mission.profile?.cruise_mode ?? "best_range";
}

// ─────────────────────────────────────────────────────────────────────────────
// Metric cards & tables
// ─────────────────────────────────────────────────────────────────────────────
function renderMetricCards(containerId, metrics, classifications = {}) {
  const container = document.getElementById(containerId);
  const template  = document.getElementById("metricCardTemplate");
  container.innerHTML = "";
  metrics.forEach(metric => {
    const node = template.content.firstElementChild.cloneNode(true);
    node.querySelector(".metric-card__label").textContent = metric.label;
    node.querySelector(".metric-card__value").textContent = metric.value;
    const cls = classifications[metric.label];
    if (cls === "good") node.classList.add("metric-card--good");
    if (cls === "bad")  node.classList.add("metric-card--bad");
    if (cls === "warn") node.classList.add("metric-card--warn");
    container.appendChild(node);
  });
}

function renderTable(tableId, rows, columns = null) {
  const table = document.getElementById(tableId);
  if (!rows || !rows.length) {
    table.innerHTML = "<tbody><tr><td>No data available.</td></tr></tbody>";
    return;
  }
  const cols  = columns ?? [...new Set(rows.flatMap(r => Object.keys(r)))];
  const thead = `<thead><tr>${cols.map(c => `<th>${toTitle(c)}</th>`).join("")}</tr></thead>`;
  const tbody = `<tbody>${rows.map(row => {
    const stallWarn = row.stall_margin_ok === false;
    const rowCls    = stallWarn ? ' class="row--warn"' : "";
    return `<tr${rowCls}>${cols.map(col => {
      const value = row[col];
      let cls = "", text;
      if (typeof value === "boolean") {
        cls  = value ? "status-good" : "status-bad";
        text = value ? "Yes" : "No";
      } else if (col === "stall_margin" && typeof value === "number") {
        cls  = value < 1.3 ? "status-warn" : "status-good";
        text = fmt(value, 3);
      } else if (typeof value === "number") {
        text = fmt(value, 3);
      } else {
        text = String(value ?? "");
      }
      return `<td class="${cls}">${text}</td>`;
    }).join("")}</tr>`;
  }).join("")}</tbody>`;
  table.innerHTML = thead + tbody;
}

// ─────────────────────────────────────────────────────────────────────────────
// Chart helpers
// ─────────────────────────────────────────────────────────────────────────────
function upsertChart(key, canvasId, type, data, options = {}) {
  const ctx = document.getElementById(canvasId);
  if (charts[key]) charts[key].destroy();

  data.datasets = data.datasets.map((ds, i) => {
    const colour = CHART_PALETTE[i % CHART_PALETTE.length];
    return {
      borderColor:     colour,
      backgroundColor: type === "bar" ? hexToRgba(colour, 0.28) : hexToRgba(colour, 0.1),
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.3,
      fill: type !== "bar",
      ...ds,
    };
  });

  charts[key] = new Chart(ctx, {
    type,
    data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "#c8ddf2", font: { size: 12 } } } },
      scales: {
        x: { ticks: { color: "#4e7092" }, grid: { color: "rgba(0,200,255,0.07)" } },
        y: { ticks: { color: "#4e7092" }, grid: { color: "rgba(0,200,255,0.07)" } },
      },
      ...options,
    },
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// 2D Heatmap rendering
// ─────────────────────────────────────────────────────────────────────────────
function heatmapColor(t, isBinary) {
  t = Math.max(0, Math.min(1, t));
  if (isBinary) {
    // red → green
    const r = Math.round(255 * (1 - t));
    const g = Math.round(232 * t);
    const b = Math.round(90 * (1 - t) + 160 * t);
    return `rgb(${r},${g},${b})`;
  }
  // dark blue → cyan → amber (4 stops)
  const stops = [[10,26,64],[0,120,200],[0,200,255],[255,204,51]];
  const n = stops.length - 1;
  const i = Math.min(Math.floor(t * n), n - 1);
  const f = t * n - i;
  const [r1,g1,b1] = stops[i], [r2,g2,b2] = stops[i+1];
  return `rgb(${Math.round(r1+f*(r2-r1))},${Math.round(g1+f*(g2-g1))},${Math.round(b1+f*(b2-b1))})`;
}

function renderHeatmap(canvasId, data, xVals, yVals, metricKey, xLabel, yLabel, metricLabel) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !data.length) return;

  const dpr  = window.devicePixelRatio || 1;
  const wrap = canvas.parentElement;
  const W    = wrap.clientWidth  || 640;
  const H    = wrap.clientHeight || 460;
  canvas.width  = W * dpr;
  canvas.height = H * dpr;
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  const PAD = { left: 72, bottom: 54, top: 28, right: 90 };
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.bottom - PAD.top;
  const nx = xVals.length, ny = yVals.length;
  const cellW = plotW / nx, cellH = plotH / ny;

  const isBinary = metricKey.endsWith("_flag") || metricKey.endsWith("_feasible");
  const allVals  = data.map(d => d[metricKey]).filter(Number.isFinite);
  const minVal   = isBinary ? 0 : Math.min(...allVals);
  const maxVal   = isBinary ? 1 : Math.max(...allVals);

  ctx.clearRect(0, 0, W, H);

  // Cells
  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const idx = j * nx + i;
      const val = data[idx] ? data[idx][metricKey] : NaN;
      const t   = (maxVal > minVal) ? (val - minVal) / (maxVal - minVal) : 0.5;
      ctx.fillStyle = Number.isFinite(val) ? heatmapColor(t, isBinary) : "#0a1a2e";
      ctx.fillRect(PAD.left + i * cellW, PAD.top + (ny - 1 - j) * cellH, cellW + 0.5, cellH + 0.5);
    }
  }

  // Grid lines (subtle)
  ctx.strokeStyle = "rgba(0,200,255,0.05)";
  ctx.lineWidth = 0.5;
  for (let i = 0; i <= nx; i++) { ctx.beginPath(); ctx.moveTo(PAD.left + i*cellW, PAD.top); ctx.lineTo(PAD.left + i*cellW, PAD.top+plotH); ctx.stroke(); }
  for (let j = 0; j <= ny; j++) { ctx.beginPath(); ctx.moveTo(PAD.left, PAD.top + j*cellH); ctx.lineTo(PAD.left+plotW, PAD.top + j*cellH); ctx.stroke(); }

  // Axes
  ctx.strokeStyle = "rgba(0,200,255,0.2)";
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(PAD.left, PAD.top); ctx.lineTo(PAD.left, PAD.top+plotH); ctx.lineTo(PAD.left+plotW, PAD.top+plotH); ctx.stroke();

  // X ticks
  ctx.fillStyle = "#4e7092";
  ctx.font = `${11*dpr > 0 ? 11 : 11}px JetBrains Mono, monospace`;
  ctx.textAlign = "center";
  const xStep = Math.max(1, Math.floor(nx / 7));
  for (let i = 0; i < nx; i += xStep) {
    const x = PAD.left + (i + 0.5) * cellW;
    ctx.fillText(xVals[i].toFixed(3), x, H - PAD.bottom + 16);
  }

  // Y ticks
  ctx.textAlign = "right";
  const yStep = Math.max(1, Math.floor(ny / 7));
  for (let j = 0; j < ny; j += yStep) {
    const y = PAD.top + (ny - 1 - j + 0.5) * cellH;
    ctx.fillText(yVals[j].toFixed(3), PAD.left - 6, y + 4);
  }

  // Axis labels
  ctx.fillStyle = "#c8ddf2";
  ctx.font = "13px Barlow, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(xLabel, PAD.left + plotW / 2, H - 10);

  ctx.save();
  ctx.translate(15, PAD.top + plotH / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText(yLabel, 0, 0);
  ctx.restore();

  // Colour legend bar
  const legX = W - PAD.right + 14;
  const legH = plotH;
  const legW = 14;
  for (let i = 0; i < legH; i++) {
    const t = 1 - i / legH;
    ctx.fillStyle = heatmapColor(t, isBinary);
    ctx.fillRect(legX, PAD.top + i, legW, 1.5);
  }
  ctx.strokeStyle = "rgba(0,200,255,0.2)";
  ctx.strokeRect(legX, PAD.top, legW, legH);

  ctx.fillStyle = "#4e7092";
  ctx.font = "10px JetBrains Mono, monospace";
  ctx.textAlign = "left";
  ctx.fillText(maxVal.toFixed(2), legX + legW + 4, PAD.top + 10);
  ctx.fillText(minVal.toFixed(2), legX + legW + 4, PAD.top + legH - 4);

  ctx.fillStyle = "#c8ddf2";
  ctx.font = "10px Barlow, sans-serif";
  ctx.fillText(metricLabel.split("[")[0].trim(), legX, PAD.top - 8);
}

// ─────────────────────────────────────────────────────────────────────────────
// Collect results (optimised: 2 sweeps in collectResults, rest cached)
// ─────────────────────────────────────────────────────────────────────────────
function collectResults(config) {
  const summary = makeSummary(config);

  // Display sweep (from stall speed — full polar view)
  const sweep = buildSpeedSweep(config, 40, 120, stallSpeedMps(config));

  // Operating-point sweep built once; all three points derived from it
  const opSweep = buildSpeedSweep(config, 40, 120); // default minSpeed = 1.3×Vstall
  const operating = [
    { operating_point: "best_endurance",          ...maxBy(opSweep, "endurance_h") },
    { operating_point: "best_still_air_range",    ...maxBy(opSweep, "still_air_range_km") },
    { operating_point: "best_wind_adjusted_range",...maxBy(opSweep, "wind_adjusted_range_km") },
  ];

  const missionSummary = {
    mission_feasible:       isMissionFeasible(config),
    required_mission_time_h:   isNil(config.mission.required_distance_km) ? null : requiredMissionTimeHours(config),
    required_mission_energy_wh: isNil(config.mission.required_distance_km) ? null : requiredMissionEnergyWh(config),
    range_margin_km:        isNil(config.mission.required_distance_km) ? null : rangeMarginKm(config),
    energy_margin_wh:       isNil(config.mission.required_distance_km) ? null : energyMarginWh(config),
  };
  const missionProfile = evaluateSimpleMissionProfile(config, config.mission.profile);
  return { summary, sweep, operating, missionSummary, missionProfile };
}

// ─────────────────────────────────────────────────────────────────────────────
// Render functions
// ─────────────────────────────────────────────────────────────────────────────
function renderTop(results) {
  const s = results.summary;
  renderMetricCards("topMetrics", [
    { label: "Total mass",                    value: fmtMetric(s.total_mass_kg, " kg") },
    { label: "Stall speed",                   value: fmtMetric(s.stall_speed_m_per_s, " m/s") },
    { label: "Min recommended cruise",        value: fmtMetric(s.minimum_recommended_cruise_speed_m_per_s, " m/s") },
    { label: "Resolved air density",          value: fmtMetric(s.resolved_air_density_kg_per_m3, " kg/m³", 3) },
    { label: "Electrical power",              value: fmtMetric(s.electrical_power_required_w, " W", 1) },
    { label: "Endurance",                     value: fmtMetric(s.endurance_h, " h") },
    { label: "Still-air range",               value: fmtMetric(s.still_air_range_km, " km") },
    { label: "Wind-adj. range (1-leg est.)",  value: fmtMetric(s.wind_adjusted_range_km, " km") },
  ]);
}

function renderPerformance(results) {
  const s = results.summary;
  renderMetricCards("performanceCards", [
    { label: "Air power",               value: fmtMetric(s.air_power_required_w, " W", 1) },
    { label: "Propulsion electrical",   value: fmtMetric(s.propulsion_electrical_power_required_w, " W", 1) },
    { label: "Non-propulsive load",     value: fmtMetric(s.non_propulsive_electrical_load_w, " W", 1) },
    { label: "Mission energy available",value: fmtMetric(s.battery_available_for_mission_wh, " Wh", 1) },
  ]);
  renderTable("performanceSummaryTable", [s], Object.keys(s));
  renderTable("sweepTable", results.sweep.slice(0, 20),
    ["airspeed_m_per_s","air_power_w","propulsion_electrical_power_w","electrical_power_w","endurance_h","still_air_range_km","wind_adjusted_range_km"]);

  const labels = results.sweep.map(r => r.airspeed_m_per_s.toFixed(2));
  upsertChart("powerChart", "powerChart", "line", { labels, datasets: [
    { label: "Air power [W]",              data: results.sweep.map(r => r.air_power_w) },
    { label: "Propulsion electrical [W]",  data: results.sweep.map(r => r.propulsion_electrical_power_w) },
    { label: "Total electrical [W]",       data: results.sweep.map(r => r.electrical_power_w) },
  ]});
  upsertChart("enduranceChart","enduranceChart","line",{ labels, datasets:[{ label:"Endurance [h]", data: results.sweep.map(r=>r.endurance_h) }]});
  upsertChart("rangeChart","rangeChart","line",{ labels, datasets:[
    { label:"Still-air range [km]",   data: results.sweep.map(r=>r.still_air_range_km) },
    { label:"Wind-adjusted range [km]",data: results.sweep.map(r=>r.wind_adjusted_range_km) },
  ]});
}

function renderOperating(results) {
  renderTable("operatingTable", results.operating,
    ["operating_point","airspeed_m_per_s","electrical_power_w","endurance_h","still_air_range_km","wind_adjusted_range_km"]);
}

function renderMission(results) {
  const m = results.missionSummary, p = results.missionProfile;
  const profileFeasClassification = p.mission_feasible ? "good" : "bad";
  const stallClass = p.any_stall_warning ? "warn" : "good";

  renderMetricCards("missionMetrics", [
    { label: "Required mission feasible",  value: fmtMetric(m.mission_feasible) },
    { label: "Required mission time",      value: m.required_mission_time_h   === null ? "—" : fmtMetric(m.required_mission_time_h, " h") },
    { label: "Required mission energy",    value: m.required_mission_energy_wh=== null ? "—" : fmtMetric(m.required_mission_energy_wh, " Wh", 1) },
    { label: "Range margin",               value: m.range_margin_km           === null ? "—" : fmtMetric(m.range_margin_km, " km") },
    { label: "Energy margin",              value: m.energy_margin_wh          === null ? "—" : fmtMetric(m.energy_margin_wh, " Wh", 1) },
    { label: "Profile feasible",           value: fmtMetric(p.mission_feasible) },
    { label: "Profile total time",         value: fmtMetric(p.total_time_h, " h") },
    { label: "Profile remaining energy",   value: fmtMetric(p.remaining_energy_wh, " Wh", 1) },
    { label: "Stall margin ok all segs",   value: p.any_stall_warning ? "Warning" : "OK" },
  ], {
    "Required mission feasible": m.mission_feasible ? "good" : "bad",
    "Profile feasible":          profileFeasClassification,
    "Stall margin ok all segs":  stallClass,
  });

  renderTable("missionTotalsTable", [{
    available_energy_wh:            p.available_energy_wh,
    total_time_h:                   p.total_time_h,
    total_energy_used_wh:           p.total_energy_used_wh,
    total_propulsion_energy_wh:     p.total_propulsion_energy_wh,
    total_hotel_energy_wh:          p.total_hotel_energy_wh,
    total_payload_energy_wh:        p.total_payload_energy_wh,
    total_non_propulsive_energy_wh: p.total_non_propulsive_energy_wh,
    remaining_energy_wh:            p.remaining_energy_wh,
    mission_feasible:               p.mission_feasible,
    any_stall_warning:              p.any_stall_warning,
    number_of_segments:             p.segments.length,
  }]);
  renderTable("missionSegmentsTable", p.segments,
    ["segment_name","segment_type","speed_mode","distance_km","duration_min",
     "airspeed_m_per_s","ground_speed_m_per_s","stall_speed_m_per_s","stall_margin","stall_margin_ok",
     "electrical_power_w","energy_used_wh","remaining_energy_wh_after_segment"]);

  upsertChart("segmentEnergyChart","segmentEnergyChart","bar",{
    labels: p.segments.map(s=>s.segment_name),
    datasets:[
      { label:"Total energy used [Wh]",  data: p.segments.map(s=>s.energy_used_wh) },
      { label:"Propulsion energy [Wh]",  data: p.segments.map(s=>s.propulsion_energy_wh) },
    ],
  });
  upsertChart("remainingEnergyChart","remainingEnergyChart","line",{
    labels: ["start",...p.segments.map(s=>s.segment_name)],
    datasets:[{ label:"Remaining energy [Wh]", data: [p.available_energy_wh,...p.segments.map(s=>s.remaining_energy_wh_after_segment)] }],
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// 1D Trade study
// ─────────────────────────────────────────────────────────────────────────────
function setTradeDefaults() {
  const key  = document.getElementById("tradeParameter").value;
  const meta = TRADE_PARAMETERS[key];
  const cur  = meta.get(activeConfig);
  const min  = meta.minFixed !== undefined ? meta.minFixed : Math.max(meta.step, cur * meta.minFactor);
  const max  = meta.maxPad   !== undefined ? Math.max(1000, cur + meta.maxPad) : cur * meta.maxFactor;
  document.getElementById("tradeMin").value  = min;
  document.getElementById("tradeMax").value  = max;
  document.getElementById("tradeMin").step   = meta.step;
  document.getElementById("tradeMax").step   = meta.step;
}

function runTradeStudy() {
  const key    = document.getElementById("tradeParameter").value;
  const meta   = TRADE_PARAMETERS[key];
  const min    = Number(document.getElementById("tradeMin").value);
  const max    = Number(document.getElementById("tradeMax").value);
  const points = Number(document.getElementById("tradePoints").value);
  if (!(max > min)) throw new Error("Trade-study maximum must be greater than minimum.");
  const rows = [];
  for (let i = 0; i < points; i++) {
    const value = min + (i * (max - min)) / (points - 1);
    const cfg   = deepClone(activeConfig);
    meta.set(cfg, value);
    sweepCache.clear();
    const sum  = makeSummary(cfg);
    const prof = evaluateSimpleMissionProfile(cfg, cfg.mission.profile);
    rows.push({
      parameter_value:             value,
      still_air_range_km:          sum.still_air_range_km,
      wind_adjusted_range_km:      sum.wind_adjusted_range_km,
      endurance_h:                 sum.endurance_h,
      stall_speed_m_per_s:         sum.stall_speed_m_per_s,
      electrical_power_required_w: sum.electrical_power_required_w,
      remaining_energy_wh:         prof.remaining_energy_wh,
      mission_feasible_flag:       prof.mission_feasible ? 1 : 0,
    });
  }
  latestTradeStudy = rows;
  renderTable("tradeTable", rows);
  const labels = rows.map(r => r.parameter_value.toFixed(3));
  upsertChart("tradeRangeChart","tradeRangeChart","line",{ labels, datasets:[
    { label:"Still-air range [km]",    data: rows.map(r=>r.still_air_range_km) },
    { label:"Wind-adjusted range [km]",data: rows.map(r=>r.wind_adjusted_range_km) },
    { label:"Endurance [h]",           data: rows.map(r=>r.endurance_h) },
  ]});
  upsertChart("tradeMissionChart","tradeMissionChart","line",{ labels, datasets:[
    { label:"Remaining energy [Wh]",   data: rows.map(r=>r.remaining_energy_wh) },
    { label:"Mission feasible flag",   data: rows.map(r=>r.mission_feasible_flag) },
  ]});
}

// ─────────────────────────────────────────────────────────────────────────────
// 2D Trade study
// ─────────────────────────────────────────────────────────────────────────────
function initTrade2dControls() {
  const xSel = document.getElementById("trade2dXParam");
  const ySel = document.getElementById("trade2dYParam");
  const mSel = document.getElementById("trade2dMetric");

  const paramHtml = Object.entries(TRADE_PARAMETERS)
    .map(([k, v]) => `<option value="${k}">${v.label}</option>`).join("");
  xSel.innerHTML = paramHtml;
  ySel.innerHTML = paramHtml;

  mSel.innerHTML = Object.entries(TRADE2D_OUTPUT_METRICS)
    .map(([k, v]) => `<option value="${k}">${v}</option>`).join("");

  // Default X = battery_mass, Y = wing_area
  xSel.value = "battery_mass_kg";
  ySel.value = "wing_area_m2";
  mSel.value = "still_air_range_km";
  setTrade2dDefaults();

  xSel.addEventListener("change", setTrade2dDefaults);
  ySel.addEventListener("change", setTrade2dDefaults);
}

function setTrade2dDefaults() {
  ["X","Y"].forEach(axis => {
    const key  = document.getElementById(`trade2d${axis}Param`).value;
    const meta = TRADE_PARAMETERS[key];
    const cur  = meta.get(activeConfig);
    const min  = meta.minFixed !== undefined ? meta.minFixed : Math.max(meta.step, cur * meta.minFactor);
    const max  = meta.maxPad   !== undefined ? Math.max(1000, cur + meta.maxPad) : cur * meta.maxFactor;
    document.getElementById(`trade2d${axis}Min`).value = min;
    document.getElementById(`trade2d${axis}Max`).value = max;
  });
}

function runTrade2d() {
  const xKey  = document.getElementById("trade2dXParam").value;
  const yKey  = document.getElementById("trade2dYParam").value;
  const mKey  = document.getElementById("trade2dMetric").value;
  const xMin  = Number(document.getElementById("trade2dXMin").value);
  const xMax  = Number(document.getElementById("trade2dXMax").value);
  const yMin  = Number(document.getElementById("trade2dYMin").value);
  const yMax  = Number(document.getElementById("trade2dYMax").value);
  const n     = Math.max(5, Math.min(35, Number(document.getElementById("trade2dGrid").value)));
  if (!(xMax > xMin)) throw new Error("2D trade: X max must be greater than X min.");
  if (!(yMax > yMin)) throw new Error("2D trade: Y max must be greater than Y min.");
  if (xKey === yKey)  throw new Error("2D trade: X and Y parameters must be different.");

  const xMeta = TRADE_PARAMETERS[xKey];
  const yMeta = TRADE_PARAMETERS[yKey];
  const xVals = Array.from({length: n}, (_, i) => xMin + i*(xMax-xMin)/(n-1));
  const yVals = Array.from({length: n}, (_, i) => yMin + i*(yMax-yMin)/(n-1));

  const needsProfile = mKey.startsWith("profile_");
  const rows = [];

  for (let j = 0; j < n; j++) {
    for (let i = 0; i < n; i++) {
      sweepCache.clear();
      const cfg = deepClone(activeConfig);
      xMeta.set(cfg, xVals[i]);
      yMeta.set(cfg, yVals[j]);
      try {
        const sum = makeSummary(cfg);
        let profileRemainingWh = NaN, profileFeasibleFlag = NaN;
        if (needsProfile) {
          const prof = evaluateSimpleMissionProfile(cfg, cfg.mission.profile);
          profileRemainingWh  = prof.remaining_energy_wh;
          profileFeasibleFlag = prof.mission_feasible ? 1 : 0;
        }
        rows.push({
          [xKey]:                      xVals[i],
          [yKey]:                      yVals[j],
          still_air_range_km:          sum.still_air_range_km,
          wind_adjusted_range_km:      sum.wind_adjusted_range_km,
          endurance_h:                 sum.endurance_h,
          electrical_power_required_w: sum.electrical_power_required_w,
          stall_speed_m_per_s:         sum.stall_speed_m_per_s,
          profile_remaining_energy_wh: profileRemainingWh,
          profile_feasible_flag:       profileFeasibleFlag,
        });
      } catch {
        rows.push({
          [xKey]: xVals[i], [yKey]: yVals[j],
          still_air_range_km: NaN, wind_adjusted_range_km: NaN,
          endurance_h: NaN, electrical_power_required_w: NaN,
          stall_speed_m_per_s: NaN,
          profile_remaining_energy_wh: NaN, profile_feasible_flag: NaN,
        });
      }
    }
  }

  latestTrade2dData = rows;
  renderHeatmap(
    "trade2dCanvas", rows, xVals, yVals, mKey,
    xMeta.label, yMeta.label, TRADE2D_OUTPUT_METRICS[mKey] ?? mKey
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Scenario comparison
// ─────────────────────────────────────────────────────────────────────────────
function renderComparison() {
  const sel   = document.getElementById("compareScenarios");
  const names = [...sel.selectedOptions].map(o => o.value);
  latestComparison = names.length >= 2 ? compareSavedScenarios(names) : [];
  renderTable("compareTable", latestComparison);
  const labels = latestComparison.map(r => r.scenario);
  upsertChart("scenarioEnergyChart","scenarioEnergyChart","bar",{ labels, datasets:[
    { label:"Total energy used [Wh]", data: latestComparison.map(r=>r.total_energy_used_wh) },
    { label:"Remaining energy [Wh]",  data: latestComparison.map(r=>r.remaining_energy_wh) },
  ]});
  upsertChart("scenarioTimeChart","scenarioTimeChart","bar",{ labels, datasets:[
    { label:"Mission time [h]", data: latestComparison.map(r=>r.total_time_h) },
  ]});
}

// ─────────────────────────────────────────────────────────────────────────────
// Main render
// ─────────────────────────────────────────────────────────────────────────────
const debouncedRenderAll = debounce(renderAll, 160);

function renderAll() {
  sweepCache.clear(); // fresh cache for each render call
  try {
    populateForm(activeConfig);
    latestResults = collectResults(activeConfig);
    renderTop(latestResults);
    renderPerformance(latestResults);
    renderOperating(latestResults);
    renderMission(latestResults);
    renderComparison();
  } catch (err) {
    alert(err.message);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Validation against reference outputs
// ─────────────────────────────────────────────────────────────────────────────
function validateAgainstPythonReference() {
  sweepCache.clear();
  const js = collectResults(deepClone(PRESET_CONFIGS.example_fixed_wing));
  const py = EXPECTED_OUTPUTS.example_fixed_wing;
  const checks = [
    [js.summary.total_mass_kg,            py.total_mass_kg],
    [js.summary.stall_speed_m_per_s,      py.stall_speed_m_per_s],
    [js.summary.electrical_power_required_w, py.electrical_power_required_w],
    [js.summary.still_air_range_km,       py.still_air_range_km],
    [js.operating[0].airspeed_m_per_s,    py.best_endurance.airspeed_m_per_s],
    [js.missionProfile.total_energy_used_wh, py.mission_profile.total_energy_used_wh],
    [js.missionProfile.remaining_energy_wh,  py.mission_profile.remaining_energy_wh],
  ];
  checks.forEach(([a, b]) => {
    if (Math.abs(a - b) > 1e-6 * Math.max(1, Math.abs(b)))
      throw new Error(`Validation mismatch: ${a} vs ${b}`);
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Event binding
// ─────────────────────────────────────────────────────────────────────────────
function bindEvents() {
  // Tabs
  document.querySelectorAll(".tab").forEach(btn => btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(el => el.classList.remove("is-active"));
    document.querySelectorAll(".tab-panel").forEach(el => el.classList.remove("is-active"));
    btn.classList.add("is-active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("is-active");
  }));

  // Preset controls
  document.getElementById("loadPresetBtn").addEventListener("click", () => {
    activePresetKey = document.getElementById("presetSelect").value;
    baseConfig = deepClone(PRESET_CONFIGS[activePresetKey]);
    activeConfig = deepClone(baseConfig);
    document.getElementById("scenarioName").value = `${activePresetKey}_custom`;
    renderAll();
  });
  document.getElementById("resetBtn").addEventListener("click", () => { activeConfig = deepClone(baseConfig); renderAll(); });

  // Saved scenarios
  document.getElementById("saveScenarioBtn").addEventListener("click", () => {
    const name = document.getElementById("scenarioName").value.trim();
    if (!name) return alert("Enter a scenario name.");
    const saved = getSavedScenarios();
    saved[name] = deepClone(activeConfig);
    saveSavedScenarios(saved);
    refreshSavedScenarioLists();
  });
  document.getElementById("deleteScenarioBtn").addEventListener("click", () => {
    const name = document.getElementById("savedScenarioSelect").value;
    if (!name) return;
    const saved = getSavedScenarios();
    delete saved[name];
    saveSavedScenarios(saved);
    refreshSavedScenarioLists();
    renderComparison();
  });
  document.getElementById("loadSavedBtn").addEventListener("click", () => {
    const name = document.getElementById("savedScenarioSelect").value;
    if (!name) return;
    const saved = getSavedScenarios();
    baseConfig = deepClone(saved[name]);
    activeConfig = deepClone(saved[name]);
    document.getElementById("scenarioName").value = name;
    renderAll();
  });
  document.getElementById("compareScenarios").addEventListener("change", renderComparison);

  // Share link
  document.getElementById("copyLinkBtn").addEventListener("click", () => {
    const url = buildShareUrl(activeConfig);
    if (!url) return;
    navigator.clipboard.writeText(url).then(
      () => showToast("Share link copied to clipboard"),
      () => { prompt("Copy this link:", url); }
    );
  });

  // Downloads
  document.getElementById("downloadConfigBtn").addEventListener("click", () =>
    downloadText(`${document.getElementById("scenarioName").value || "scenario"}.json`,
      JSON.stringify(activeConfig, null, 2), "application/json"));
  document.getElementById("exportSummaryBtn").addEventListener("click", () =>
    downloadText("uav_summary.csv", rowsToCSV([{
      ...latestResults.summary, ...latestResults.missionSummary,
      mission_profile_feasible: latestResults.missionProfile.mission_feasible,
      mission_profile_remaining_energy_wh: latestResults.missionProfile.remaining_energy_wh,
    }]), "text/csv"));
  document.getElementById("downloadSweepBtn").addEventListener("click",    () => downloadText("speed_sweep.csv",        rowsToCSV(latestResults.sweep), "text/csv"));
  document.getElementById("downloadOperatingBtn").addEventListener("click", () => downloadText("operating_points.csv",  rowsToCSV(latestResults.operating), "text/csv"));
  document.getElementById("downloadMissionBtn").addEventListener("click",   () => downloadText("mission_segments.csv",  rowsToCSV(latestResults.missionProfile.segments), "text/csv"));
  document.getElementById("downloadTradeBtn").addEventListener("click",     () => downloadText("trade_study.csv",       rowsToCSV(latestTradeStudy), "text/csv"));
  document.getElementById("downloadCompareBtn").addEventListener("click",   () => downloadText("scenario_comparison.csv", rowsToCSV(latestComparison), "text/csv"));
  document.getElementById("downloadTrade2dBtn").addEventListener("click",   () => downloadText("trade_2d.csv",          rowsToCSV(latestTrade2dData), "text/csv"));

  // 1D trade
  document.getElementById("tradeParameter").addEventListener("change", setTradeDefaults);
  document.getElementById("runTradeBtn").addEventListener("click", () => { try { runTradeStudy(); } catch(e) { alert(e.message); } });

  // 2D trade
  document.getElementById("runTrade2dBtn").addEventListener("click", () => {
    const btn = document.getElementById("runTrade2dBtn");
    btn.textContent = "Computing…";
    btn.disabled = true;
    setTimeout(() => {
      try { runTrade2d(); } catch(e) { alert(e.message); }
      btn.textContent = "Run 2D trade";
      btn.disabled = false;
    }, 20);
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Initialisation
// ─────────────────────────────────────────────────────────────────────────────
function seedSavedScenarios() {
  const saved = getSavedScenarios();
  if (Object.keys(saved).length) return;
  saveSavedScenarios({ baseline: deepClone(PRESET_CONFIGS.example_fixed_wing) });
}

function initTradeControls() {
  const sel = document.getElementById("tradeParameter");
  sel.innerHTML = Object.entries(TRADE_PARAMETERS).map(([k, v]) => `<option value="${k}">${v.label}</option>`).join("");
  sel.value = "battery_mass_kg";
  setTradeDefaults();
}

function init() {
  // Load config from URL if present
  const loadedFromUrl = loadFromUrl();

  buildInputFields();
  syncPresetControls();
  seedSavedScenarios();
  refreshSavedScenarioLists();
  populateForm(activeConfig);
  initTradeControls();
  initTrade2dControls();
  bindEvents();

  if (!loadedFromUrl) validateAgainstPythonReference();

  renderAll();
  runTradeStudy();
}

document.addEventListener("DOMContentLoaded", init);
