
const STORAGE_KEY = "uav_mpe_saved_scenarios_v1";
const DEFAULT_PRESET_KEY = Object.keys(PRESET_CONFIGS)[0];
const charts = {};
let activePresetKey = DEFAULT_PRESET_KEY;
let baseConfig = deepClone(PRESET_CONFIGS[DEFAULT_PRESET_KEY]);
let activeConfig = deepClone(baseConfig);
let latestResults = null;
let latestTradeStudy = [];
let latestComparison = [];

// FIX 4 — chart colour palette aligned with the CSS design tokens
const CHART_PALETTE = ["#00c8ff", "#00e8a0", "#ffcc33", "#1a8cff", "#ff3d5a", "#c084fc"];

const FIELD_GROUPS = {
  aircraft: [
    ["empty_mass_kg", "Empty mass [kg]", 0.1],
    ["payload_mass_kg", "Payload mass [kg]", 0.1],
    ["battery_mass_kg", "Battery mass [kg]", 0.1],
    ["battery_specific_energy_wh_per_kg", "Battery specific energy [Wh/kg]", 1],
    ["wing_area_m2", "Wing area [m²]", 0.01],
    ["aspect_ratio", "Aspect ratio [-]", 0.1],
    ["oswald_efficiency", "Oswald efficiency [-]", 0.01],
    ["cd0", "Cd0 [-]", 0.001],
    ["cl_max", "Cl_max [-]", 0.01],
    ["eta_total", "Total propulsion efficiency [-]", 0.01],
    ["hotel_load_w", "Hotel load [W]", 1],
    ["payload_load_w", "Payload load [W]", 1],
    ["loiter_payload_load_w", "Loiter payload load [W]", 1],
  ],
  environment: [
    ["altitude_m", "Altitude [m]", 10],
    ["air_density_kg_per_m3", "Override air density [kg/m³]", 0.001],
    ["wind_speed_m_per_s", "General wind speed [m/s]", 0.1],
    ["g_m_per_s2", "g [m/s²]", 0.01],
  ],
  mission: [
    ["usable_battery_fraction", "Usable battery fraction [-]", 0.01],
    // FIX 2 — labels clarify the mutual-exclusion priority
    ["reserve_energy_wh", "Fixed reserve [Wh] (takes priority)", 1],
    ["reserve_fraction", "Reserve fraction [-] (ignored if Wh set)", 0.01],
    ["cruise_speed_m_per_s", "Cruise speed [m/s]", 0.1],
    ["required_distance_km", "Required distance [km]", 0.1],
  ],
  profile: [
    ["climb_altitude_m", "Climb altitude [m]", 10],
    ["climb_rate_m_per_s", "Climb rate [m/s]", 0.1],
    ["outbound_distance_km", "Outbound distance [km]", 0.1],
    ["outbound_altitude_m", "Outbound altitude [m]", 10],
    ["loiter_duration_min", "Loiter duration [min]", 1],
    ["loiter_altitude_m", "Loiter altitude [m]", 10],
    ["return_distance_km", "Return distance [km]", 0.1],
    ["return_altitude_m", "Return altitude [m]", 10],
    ["descent_altitude_m", "Descent altitude [m]", 10],
    ["descent_rate_m_per_s", "Descent rate [m/s]", 0.1],
    ["descent_power_factor", "Descent power factor [-]", 0.01],
    ["outbound_wind_speed_m_per_s", "Outbound wind speed [m/s]", 0.1],
    ["return_wind_speed_m_per_s", "Return wind speed [m/s]", 0.1],
  ],
};

const TRADE_PARAMETERS = {
  battery_mass_kg: { label: "Battery mass [kg]", get: c => c.aircraft.battery_mass_kg, set: (c,v)=> c.aircraft.battery_mass_kg=v, minFactor:0.7, maxFactor:1.3, step:0.1 },
  payload_mass_kg: { label: "Payload mass [kg]", get: c => c.aircraft.payload_mass_kg, set: (c,v)=> c.aircraft.payload_mass_kg=v, minFactor:0.7, maxFactor:1.3, step:0.1 },
  wing_area_m2: { label: "Wing area [m²]", get: c => c.aircraft.wing_area_m2, set: (c,v)=> c.aircraft.wing_area_m2=v, minFactor:0.7, maxFactor:1.3, step:0.01 },
  cd0: { label: "Cd0 [-]", get: c => c.aircraft.cd0, set: (c,v)=> c.aircraft.cd0=v, minFactor:0.8, maxFactor:1.2, step:0.001 },
  altitude_m: { label: "Altitude [m]", get: c => c.environment.altitude_m ?? 0, set: (c,v)=> { c.environment.altitude_m=v; c.environment.air_density_kg_per_m3=null; }, minFixed:0, maxPad:3000, step:10 },
  cruise_speed_m_per_s: { label: "Cruise speed [m/s]", get: c => c.mission.cruise_speed_m_per_s, set: (c,v)=> c.mission.cruise_speed_m_per_s=v, minFactor:0.7, maxFactor:1.3, step:0.1 },
};

function deepClone(obj) { return JSON.parse(JSON.stringify(obj)); }
function isNil(v) { return v === null || v === undefined || v === ""; }
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
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
function rowsToCSV(rows) {
  if (!rows.length) return "";
  const headers = [...new Set(rows.flatMap(r => Object.keys(r)))];
  const escape = value => {
    if (value === null || value === undefined) return "";
    const str = String(value);
    return /[",\n]/.test(str) ? `"${str.replace(/"/g, '""')}"` : str;
  };
  return [headers.join(","), ...rows.map(row => headers.map(h => escape(row[h])).join(","))].join("\n");
}
function toTitle(value) { return value.replace(/_/g, " "); }

// FIX 4 — helper to convert hex colour to rgba for chart fills
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
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
    el.addEventListener("input", onFieldChange);
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

  // FIX 2 — mutual exclusion: whichever reserve field the user edits last wins;
  // the other is cleared so the priority logic in reserveEnergyWh() is visible.
  if (group === "mission" && field === "reserve_energy_wh" && !isNil(activeConfig.mission.reserve_energy_wh)) {
    activeConfig.mission.reserve_fraction = null;
    const el = document.querySelector('[data-group="mission"][data-field="reserve_fraction"]');
    if (el) el.value = "";
  } else if (group === "mission" && field === "reserve_fraction" && !isNil(activeConfig.mission.reserve_fraction)) {
    activeConfig.mission.reserve_energy_wh = null;
    const el = document.querySelector('[data-group="mission"][data-field="reserve_energy_wh"]');
    if (el) el.value = "";
  }

  renderAll();
}

function populateForm(config) {
  Object.entries(FIELD_GROUPS).forEach(([groupKey, fields]) => {
    fields.forEach(([fieldKey]) => {
      const el = document.querySelector(`[data-group="${groupKey}"][data-field="${fieldKey}"]`);
      const source = groupKey === "profile" ? config.mission.profile : config[groupKey];
      const value = source?.[fieldKey];
      el.value = isNil(value) ? "" : value;
    });
  });
  const modeEl = document.querySelector('[data-group="profile"][data-field="cruise_mode"]');
  modeEl.value = config.mission.profile?.cruise_mode ?? "best_range";
}

function isaDensityKgPerM3(altitudeM) {
  if (altitudeM < 0) throw new Error("altitude_m must be non-negative.");
  if (altitudeM > 11000) throw new Error("ISA model supports altitudes up to 11000 m.");
  const t0 = 288.15, p0 = 101325.0, lapse = 0.0065, R = 287.05, g0 = 9.80665;
  const temperature = t0 - lapse * altitudeM;
  const pressure = p0 * Math.pow(temperature / t0, g0 / (R * lapse));
  return pressure / (R * temperature);
}
function getAirDensityKgPerM3(config) {
  const env = config.environment;
  if (!isNil(env.air_density_kg_per_m3)) return env.air_density_kg_per_m3;
  if (isNil(env.altitude_m)) throw new Error("Environment must define either air density or altitude.");
  return isaDensityKgPerM3(env.altitude_m);
}
function totalMassKg(config) { return config.aircraft.empty_mass_kg + config.aircraft.payload_mass_kg + config.aircraft.battery_mass_kg; }
function weightNewtons(config) { return totalMassKg(config) * config.environment.g_m_per_s2; }
function batteryNominalEnergyWh(config) { return config.aircraft.battery_mass_kg * config.aircraft.battery_specific_energy_wh_per_kg; }
function batteryUsableEnergyWh(config) { return batteryNominalEnergyWh(config) * config.mission.usable_battery_fraction; }

// FIX 2 — guard against both fields being null (returns 0 reserve as fallback)
function reserveEnergyWh(config) {
  const usable = batteryUsableEnergyWh(config);
  if (!isNil(config.mission.reserve_energy_wh)) {
    if (config.mission.reserve_energy_wh > usable) throw new Error("reserve_energy_wh cannot exceed usable battery energy.");
    return config.mission.reserve_energy_wh;
  }
  if (!isNil(config.mission.reserve_fraction)) {
    return usable * config.mission.reserve_fraction;
  }
  return 0; // neither field set — no reserve
}

function batteryAvailableForMissionWh(config) { return batteryUsableEnergyWh(config) - reserveEnergyWh(config); }
function batteryAvailableForMissionJ(config) { return batteryAvailableForMissionWh(config) * 3600; }
function stallSpeedMps(config) {
  return Math.sqrt((2 * weightNewtons(config)) / (getAirDensityKgPerM3(config) * config.aircraft.wing_area_m2 * config.aircraft.cl_max));
}
function minimumRecommendedCruiseSpeedMps(config, margin = 1.3) { return margin * stallSpeedMps(config); }
function liftCoefficient(config) {
  const w = weightNewtons(config), rho = getAirDensityKgPerM3(config), v = config.mission.cruise_speed_m_per_s, s = config.aircraft.wing_area_m2;
  return w / (0.5 * rho * v * v * s);
}
function inducedDragFactor(config) { return 1 / (Math.PI * config.aircraft.oswald_efficiency * config.aircraft.aspect_ratio); }
function dragCoefficient(config) { const cl = liftCoefficient(config); return config.aircraft.cd0 + inducedDragFactor(config) * cl * cl; }
function dragForceNewtons(config) { const rho = getAirDensityKgPerM3(config), v = config.mission.cruise_speed_m_per_s, s = config.aircraft.wing_area_m2; return 0.5 * rho * v * v * s * dragCoefficient(config); }
function airPowerRequiredWatts(config) { return dragForceNewtons(config) * config.mission.cruise_speed_m_per_s; }
function propulsionElectricalPowerRequiredWatts(config) { return airPowerRequiredWatts(config) / config.aircraft.eta_total; }
function hotelLoadWatts(config) { return config.aircraft.hotel_load_w; }
function payloadLoadWatts(config) { return config.aircraft.payload_load_w; }
function nonPropulsiveElectricalLoadWatts(config) { return hotelLoadWatts(config) + payloadLoadWatts(config); }
function electricalPowerRequiredWatts(config) { return propulsionElectricalPowerRequiredWatts(config) + nonPropulsiveElectricalLoadWatts(config); }
function enduranceSeconds(config) { return batteryAvailableForMissionJ(config) / electricalPowerRequiredWatts(config); }
function enduranceHours(config) { return enduranceSeconds(config) / 3600; }
function stillAirRangeKm(config) { return config.mission.cruise_speed_m_per_s * enduranceSeconds(config) / 1000; }
function windAdjustedGroundSpeedMps(config) { return Math.max(0, config.mission.cruise_speed_m_per_s - config.environment.wind_speed_m_per_s); }

// FIX 5 — NOTE: this is a conservative single-leg estimate. It treats the
// entire endurance as if flown against the headwind. For an out-and-back
// mission the return leg benefits from a tailwind, so the true round-trip
// range is better. Use the segmented Mission tab for an accurate energy
// balance with per-leg wind speeds.
function windAdjustedRangeKm(config) { return windAdjustedGroundSpeedMps(config) * enduranceSeconds(config) / 1000; }

function requiredDistanceKm(config) { if (isNil(config.mission.required_distance_km)) throw new Error("Mission required distance is not set."); return config.mission.required_distance_km; }

// FIX 5 — same single-leg wind caveat applies here (see windAdjustedRangeKm)
function requiredMissionTimeHours(config) {
  const gs = windAdjustedGroundSpeedMps(config); if (gs <= 0) return Infinity; return requiredDistanceKm(config) / (gs * 3.6);
}
function requiredMissionEnergyWh(config) { return electricalPowerRequiredWatts(config) * requiredMissionTimeHours(config); }
function rangeMarginKm(config) { return windAdjustedRangeKm(config) - requiredDistanceKm(config); }
function energyMarginWh(config) { return batteryAvailableForMissionWh(config) - requiredMissionEnergyWh(config); }
function isMissionFeasible(config) { return windAdjustedGroundSpeedMps(config) > 0 && rangeMarginKm(config) >= 0 && energyMarginWh(config) >= 0; }

function configWithFlightConditions(config, airspeed, windSpeed, altitude = null) {
  const updated = deepClone(config);
  updated.mission.cruise_speed_m_per_s = airspeed;
  updated.environment.wind_speed_m_per_s = windSpeed;
  if (!isNil(altitude)) {
    updated.environment.altitude_m = altitude;
    updated.environment.air_density_kg_per_m3 = null;
  }
  return updated;
}

function climbTimeHours(altitude, rate) { if (altitude < 0 || rate <= 0) throw new Error("Invalid climb inputs."); return (altitude / rate) / 3600; }
// NOTE: climb drag is evaluated at the mission cruise speed — a reasonable
// approximation for small climb angles (γ < ~10°) where L ≈ W.
function climbExtraPowerWatts(config, rate) { return (totalMassKg(config) * config.environment.g_m_per_s2 * rate) / config.aircraft.eta_total; }
function climbTotalElectricalPowerWatts(config, rate) { return electricalPowerRequiredWatts(config) + climbExtraPowerWatts(config, rate); }
function climbEnergyWh(config, altitude, rate) { return climbTotalElectricalPowerWatts(config, rate) * climbTimeHours(altitude, rate); }
function descentTimeHours(altitude, rate) { if (altitude < 0 || rate <= 0) throw new Error("Invalid descent inputs."); return (altitude / rate) / 3600; }

// FIX 7 — NOTE: descent propulsion power is modelled as a fixed fraction of
// the cruise propulsion power (evaluated at mission cruise_speed_m_per_s).
// The descent segment has no dedicated airspeed; changing descent_rate only
// affects segment duration, not power. Adjust descent_power_factor to
// represent different descent throttle strategies.
function descentTotalElectricalPowerWatts(config, factor) {
  const propulsion = airPowerRequiredWatts(config) / config.aircraft.eta_total;
  return factor * propulsion + nonPropulsiveElectricalLoadWatts(config);
}
function descentEnergyWh(config, altitude, rate, factor) { return descentTotalElectricalPowerWatts(config, factor) * descentTimeHours(altitude, rate); }

function segmentBreakdownFields(config, totalElectricalPowerW, timeH) {
  const hotel = hotelLoadWatts(config), payload = payloadLoadWatts(config), nonProp = nonPropulsiveElectricalLoadWatts(config), propulsion = totalElectricalPowerW - nonProp;
  return {
    propulsion_electrical_power_w: propulsion,
    hotel_load_w: hotel,
    payload_load_w: payload,
    non_propulsive_electrical_load_w: nonProp,
    propulsion_energy_wh: propulsion * timeH,
    hotel_energy_wh: hotel * timeH,
    payload_energy_wh: payload * timeH,
    non_propulsive_energy_wh: nonProp * timeH,
  };
}

function buildSpeedSweep(config, maxSpeed = 40, numPoints = 120, minSpeed = null) {
  const vMin = isNil(minSpeed) ? minimumRecommendedCruiseSpeedMps(config) : Number(minSpeed);
  if (maxSpeed <= vMin) throw new Error(`max_speed_m_per_s must be greater than ${vMin}.`);
  if (numPoints < 2) throw new Error("num_points must be at least 2.");
  const rows = [];
  for (let i = 0; i < numPoints; i++) {
    const v = vMin + (i * (maxSpeed - vMin)) / (numPoints - 1);
    const sweep = deepClone(config);
    sweep.mission.cruise_speed_m_per_s = v;
    rows.push({
      airspeed_m_per_s: v,
      lift_coefficient: liftCoefficient(sweep),
      induced_drag_factor: inducedDragFactor(sweep),
      drag_coefficient: dragCoefficient(sweep),
      drag_force_n: dragForceNewtons(sweep),
      air_power_w: airPowerRequiredWatts(sweep),
      propulsion_electrical_power_w: propulsionElectricalPowerRequiredWatts(sweep),
      hotel_load_w: hotelLoadWatts(sweep),
      payload_load_w: payloadLoadWatts(sweep),
      non_propulsive_electrical_load_w: nonPropulsiveElectricalLoadWatts(sweep),
      electrical_power_w: electricalPowerRequiredWatts(sweep),
      endurance_h: enduranceHours(sweep),
      still_air_range_km: stillAirRangeKm(sweep),
      wind_adjusted_ground_speed_m_per_s: windAdjustedGroundSpeedMps(sweep),
      wind_adjusted_range_km: windAdjustedRangeKm(sweep),
    });
  }
  return rows;
}

function maxBy(rows, key) { return rows.reduce((best, row) => row[key] > best[key] ? row : best, rows[0]); }
function getBestEnduranceOperatingPoint(config, maxSpeed = 40, numPoints = 120) { return maxBy(buildSpeedSweep(config, maxSpeed, numPoints), "endurance_h"); }
function getBestRangeOperatingPoint(config, maxSpeed = 40, numPoints = 120) { return maxBy(buildSpeedSweep(config, maxSpeed, numPoints), "still_air_range_km"); }
function getBestWindAdjustedRangeOperatingPoint(config, maxSpeed = 40, numPoints = 120) { return maxBy(buildSpeedSweep(config, maxSpeed, numPoints), "wind_adjusted_range_km"); }

function evaluateCruiseSegment(config, mode, segmentName, distanceKm, windSpeed = 0, altitude = null, maxSpeed = 40, numPoints = 120) {
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

  const segmentConfig = configWithFlightConditions(config, airspeed, windSpeed, altitude);
  const electricalPowerW = electricalPowerRequiredWatts(segmentConfig);
  const groundSpeed = windAdjustedGroundSpeedMps(segmentConfig);
  const timeH = groundSpeed <= 0 ? Infinity : distanceKm / (groundSpeed * 3.6);
  const energyUsedWh = electricalPowerW * timeH;
  return {
    segment_name: segmentName,
    segment_type: "cruise",
    speed_mode: mode,
    distance_km: distanceKm,
    altitude_m: altitude,
    airspeed_m_per_s: airspeed,
    ground_speed_m_per_s: groundSpeed,
    electrical_power_w: electricalPowerW,
    time_h: timeH,
    duration_min: timeH * 60,
    energy_used_wh: energyUsedWh,
    ...segmentBreakdownFields(segmentConfig, electricalPowerW, timeH),
  };
}

function evaluateLoiterSegmentBestEndurance(config, segmentName, durationMin, altitude = null, maxSpeed = 40, numPoints = 120) {
  const selectionConfig = deepClone(config);
  if (!isNil(altitude)) {
    selectionConfig.environment.altitude_m = altitude;
    selectionConfig.environment.air_density_kg_per_m3 = null;
  }
  if (!isNil(selectionConfig.aircraft.loiter_payload_load_w)) {
    selectionConfig.aircraft.payload_load_w = selectionConfig.aircraft.loiter_payload_load_w;
  }
  const op = getBestEnduranceOperatingPoint(selectionConfig, maxSpeed, numPoints);
  const timeH = durationMin / 60;
  const airspeed = op.airspeed_m_per_s;
  const electricalPowerW = op.electrical_power_w;
  const configForBreakdown = deepClone(selectionConfig);
  configForBreakdown.mission.cruise_speed_m_per_s = airspeed;
  return {
    segment_name: segmentName,
    segment_type: "loiter",
    speed_mode: "best_endurance",
    duration_min: durationMin,
    altitude_m: altitude,
    airspeed_m_per_s: airspeed,
    electrical_power_w: electricalPowerW,
    time_h: timeH,
    energy_used_wh: electricalPowerW * timeH,
    ...segmentBreakdownFields(configForBreakdown, electricalPowerW, timeH),
  };
}

function evaluateSimpleMissionProfile(config, profile, maxSpeed = 40, numPoints = 120) {
  const segments = [];
  const addSegment = segment => {
    const remaining = segments.length ? segments[segments.length - 1].remaining_energy_wh_after_segment : batteryAvailableForMissionWh(config);
    segment.remaining_energy_wh_after_segment = remaining - segment.energy_used_wh;
    segments.push(segment);
  };

  if (!isNil(profile.climb_altitude_m) && !isNil(profile.climb_rate_m_per_s)) {
    const electricalPowerW = climbTotalElectricalPowerWatts(config, profile.climb_rate_m_per_s);
    const timeH = climbTimeHours(profile.climb_altitude_m, profile.climb_rate_m_per_s);
    addSegment({
      // FIX 3 — renamed from "climb_out" to match EXPECTED_OUTPUTS reference
      segment_name: "climb",
      segment_type: "climb",
      speed_mode: "fixed_climb",
      climb_altitude_m: profile.climb_altitude_m,
      climb_rate_m_per_s: profile.climb_rate_m_per_s,
      electrical_power_w: electricalPowerW,
      time_h: timeH,
      duration_min: timeH * 60,
      energy_used_wh: climbEnergyWh(config, profile.climb_altitude_m, profile.climb_rate_m_per_s),
      ...segmentBreakdownFields(config, electricalPowerW, timeH),
    });
  }

  addSegment(evaluateCruiseSegment(config, profile.cruise_mode, "outbound", profile.outbound_distance_km, profile.outbound_wind_speed_m_per_s ?? 0, profile.outbound_altitude_m, maxSpeed, numPoints));

  if (!isNil(profile.loiter_duration_min)) {
    addSegment(evaluateLoiterSegmentBestEndurance(config, "loiter", profile.loiter_duration_min, profile.loiter_altitude_m, maxSpeed, numPoints));
  }

  if (!isNil(profile.return_distance_km)) {
    addSegment(evaluateCruiseSegment(config, profile.cruise_mode, "return", profile.return_distance_km, profile.return_wind_speed_m_per_s ?? 0, profile.return_altitude_m, maxSpeed, numPoints));
  }

  if (!isNil(profile.descent_altitude_m) && !isNil(profile.descent_rate_m_per_s)) {
    const electricalPowerW = descentTotalElectricalPowerWatts(config, profile.descent_power_factor);
    const timeH = descentTimeHours(profile.descent_altitude_m, profile.descent_rate_m_per_s);
    addSegment({
      segment_name: "descent",
      segment_type: "descent",
      speed_mode: "fixed_descent",
      descent_altitude_m: profile.descent_altitude_m,
      descent_rate_m_per_s: profile.descent_rate_m_per_s,
      descent_power_factor: profile.descent_power_factor,
      electrical_power_w: electricalPowerW,
      time_h: timeH,
      duration_min: timeH * 60,
      energy_used_wh: descentEnergyWh(config, profile.descent_altitude_m, profile.descent_rate_m_per_s, profile.descent_power_factor),
      ...segmentBreakdownFields(config, electricalPowerW, timeH),
    });
  }

  const finiteSegments = segments.filter(seg => Number.isFinite(seg.energy_used_wh));
  const totalTimeH = segments.reduce((sum, seg) => sum + seg.time_h, 0);
  const totalEnergyUsedWh = segments.reduce((sum, seg) => sum + seg.energy_used_wh, 0);
  const totalPropulsionEnergyWh = finiteSegments.reduce((sum, seg) => sum + seg.propulsion_energy_wh, 0);
  const totalHotelEnergyWh = finiteSegments.reduce((sum, seg) => sum + seg.hotel_energy_wh, 0);
  const totalPayloadEnergyWh = finiteSegments.reduce((sum, seg) => sum + seg.payload_energy_wh, 0);
  const totalNonPropulsiveEnergyWh = finiteSegments.reduce((sum, seg) => sum + seg.non_propulsive_energy_wh, 0);
  const availableEnergyWh = batteryAvailableForMissionWh(config);
  const remainingEnergyWh = availableEnergyWh - totalEnergyUsedWh;

  return {
    available_energy_wh: availableEnergyWh,
    total_time_h: totalTimeH,
    total_energy_used_wh: totalEnergyUsedWh,
    total_propulsion_energy_wh: totalPropulsionEnergyWh,
    total_hotel_energy_wh: totalHotelEnergyWh,
    total_payload_energy_wh: totalPayloadEnergyWh,
    total_non_propulsive_energy_wh: totalNonPropulsiveEnergyWh,
    remaining_energy_wh: remainingEnergyWh,
    mission_feasible: Number.isFinite(totalEnergyUsedWh) && remainingEnergyWh >= 0,
    segments,
  };
}

function makeSummary(config) {
  return {
    total_mass_kg: totalMassKg(config),
    weight_n: weightNewtons(config),
    resolved_air_density_kg_per_m3: getAirDensityKgPerM3(config),
    stall_speed_m_per_s: stallSpeedMps(config),
    minimum_recommended_cruise_speed_m_per_s: minimumRecommendedCruiseSpeedMps(config),
    battery_nominal_energy_wh: batteryNominalEnergyWh(config),
    battery_usable_energy_wh: batteryUsableEnergyWh(config),
    reserve_energy_wh: reserveEnergyWh(config),
    battery_available_for_mission_wh: batteryAvailableForMissionWh(config),
    air_power_required_w: airPowerRequiredWatts(config),
    propulsion_electrical_power_required_w: propulsionElectricalPowerRequiredWatts(config),
    hotel_load_w: hotelLoadWatts(config),
    payload_load_w: payloadLoadWatts(config),
    non_propulsive_electrical_load_w: nonPropulsiveElectricalLoadWatts(config),
    electrical_power_required_w: electricalPowerRequiredWatts(config),
    endurance_h: enduranceHours(config),
    still_air_range_km: stillAirRangeKm(config),
    wind_adjusted_range_km: windAdjustedRangeKm(config),
  };
}

function compareSavedScenarios(names) {
  const saved = getSavedScenarios();
  return names.map(name => {
    const config = saved[name];
    const profile = evaluateSimpleMissionProfile(config, config.mission.profile);
    return {
      scenario: name,
      mission_feasible: profile.mission_feasible,
      available_energy_wh: profile.available_energy_wh,
      total_time_h: profile.total_time_h,
      total_energy_used_wh: profile.total_energy_used_wh,
      total_propulsion_energy_wh: profile.total_propulsion_energy_wh,
      total_hotel_energy_wh: profile.total_hotel_energy_wh,
      total_payload_energy_wh: profile.total_payload_energy_wh,
      total_non_propulsive_energy_wh: profile.total_non_propulsive_energy_wh,
      remaining_energy_wh: profile.remaining_energy_wh,
      number_of_segments: profile.segments.length,
      outbound_distance_km: config.mission.profile.outbound_distance_km,
      loiter_duration_min: config.mission.profile.loiter_duration_min,
      return_distance_km: config.mission.profile.return_distance_km,
      cruise_mode: config.mission.profile.cruise_mode,
    };
  });
}

function getSavedScenarios() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}"); } catch { return {}; }
}
function saveSavedScenarios(saved) { localStorage.setItem(STORAGE_KEY, JSON.stringify(saved)); }

function syncPresetControls() {
  const presetSelect = document.getElementById("presetSelect");
  presetSelect.innerHTML = Object.keys(PRESET_CONFIGS).map(name => `<option value="${name}">${name}</option>`).join("");
  presetSelect.value = activePresetKey;
  refreshSavedScenarioLists();
}
function refreshSavedScenarioLists() {
  const saved = getSavedScenarios();
  const options = Object.keys(saved).sort();
  const savedSelect = document.getElementById("savedScenarioSelect");
  const compareSelect = document.getElementById("compareScenarios");
  savedSelect.innerHTML = options.map(name => `<option value="${name}">${name}</option>`).join("");
  compareSelect.innerHTML = options.map(name => `<option value="${name}">${name}</option>`).join("");
}

function renderMetricCards(containerId, metrics, classifications = {}) {
  const container = document.getElementById(containerId);
  const template = document.getElementById("metricCardTemplate");
  container.innerHTML = "";
  metrics.forEach(metric => {
    const node = template.content.firstElementChild.cloneNode(true);
    node.querySelector(".metric-card__label").textContent = metric.label;
    node.querySelector(".metric-card__value").textContent = metric.value;
    if (classifications[metric.label] === "good") node.classList.add("metric-card--good");
    if (classifications[metric.label] === "bad") node.classList.add("metric-card--bad");
    container.appendChild(node);
  });
}

function renderTable(tableId, rows, columns = null) {
  const table = document.getElementById(tableId);
  if (!rows || !rows.length) {
    table.innerHTML = "<tbody><tr><td>No data available.</td></tr></tbody>";
    return;
  }
  const cols = columns ?? [...new Set(rows.flatMap(r => Object.keys(r)))];
  const thead = `<thead><tr>${cols.map(col => `<th>${toTitle(col)}</th>`).join("")}</tr></thead>`;
  const tbody = `<tbody>${rows.map(row => `<tr>${cols.map(col => {
    const value = row[col];
    const cls = typeof value === "boolean" ? (value ? "status-good" : "status-bad") : "";
    const text = typeof value === "number" ? fmt(value, 3) : String(value ?? "");
    return `<td class="${cls}">${text}</td>`;
  }).join("")}</tr>`).join("")}</tbody>`;
  table.innerHTML = thead + tbody;
}

// FIX 4 — updated chart styling to match the new CSS palette; colours are
// applied automatically from CHART_PALETTE so all datasets stay on-brand.
function upsertChart(key, canvasId, type, data, options = {}) {
  const ctx = document.getElementById(canvasId);
  if (charts[key]) charts[key].destroy();

  data.datasets = data.datasets.map((ds, i) => {
    const colour = CHART_PALETTE[i % CHART_PALETTE.length];
    return {
      borderColor: colour,
      backgroundColor: type === "bar"
        ? hexToRgba(colour, 0.28)
        : hexToRgba(colour, 0.1),
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

function collectResults(config) {
  const summary = makeSummary(config);

  // Performance chart sweep — starts from stall speed to show full polar
  const sweep = buildSpeedSweep(config, 40, 120, stallSpeedMps(config));

  // FIX 6 — build the operating-point sweep once (min speed = 1.3×Vstall)
  // and derive all three operating points from it, eliminating three
  // previously redundant sweep builds on every render call.
  const opSweep = buildSpeedSweep(config, 40, 120); // minSpeed defaults to minimumRecommendedCruiseSpeedMps
  const operating = [
    { operating_point: "best_endurance",          ...maxBy(opSweep, "endurance_h") },
    { operating_point: "best_still_air_range",    ...maxBy(opSweep, "still_air_range_km") },
    { operating_point: "best_wind_adjusted_range",...maxBy(opSweep, "wind_adjusted_range_km") },
  ];

  const missionSummary = {
    mission_feasible: isMissionFeasible(config),
    required_mission_time_h: isNil(config.mission.required_distance_km) ? null : requiredMissionTimeHours(config),
    required_mission_energy_wh: isNil(config.mission.required_distance_km) ? null : requiredMissionEnergyWh(config),
    range_margin_km: isNil(config.mission.required_distance_km) ? null : rangeMarginKm(config),
    energy_margin_wh: isNil(config.mission.required_distance_km) ? null : energyMarginWh(config),
  };
  const missionProfile = evaluateSimpleMissionProfile(config, config.mission.profile);
  return { summary, sweep, operating, missionSummary, missionProfile };
}

function renderTop(results) {
  const s = results.summary;
  renderMetricCards("topMetrics", [
    { label: "Total mass", value: fmtMetric(s.total_mass_kg, " kg") },
    { label: "Stall speed", value: fmtMetric(s.stall_speed_m_per_s, " m/s") },
    { label: "Min recommended cruise", value: fmtMetric(s.minimum_recommended_cruise_speed_m_per_s, " m/s") },
    { label: "Resolved air density", value: fmtMetric(s.resolved_air_density_kg_per_m3, " kg/m³", 3) },
    { label: "Electrical power", value: fmtMetric(s.electrical_power_required_w, " W", 1) },
    { label: "Endurance", value: fmtMetric(s.endurance_h, " h") },
    { label: "Still-air range", value: fmtMetric(s.still_air_range_km, " km") },
    { label: "Wind-adj. range (1-leg est.)", value: fmtMetric(s.wind_adjusted_range_km, " km") },
  ]);
}

function renderPerformance(results) {
  const s = results.summary;
  renderMetricCards("performanceCards", [
    { label: "Air power", value: fmtMetric(s.air_power_required_w, " W", 1) },
    { label: "Propulsion electrical", value: fmtMetric(s.propulsion_electrical_power_required_w, " W", 1) },
    { label: "Non-propulsive load", value: fmtMetric(s.non_propulsive_electrical_load_w, " W", 1) },
    { label: "Mission energy available", value: fmtMetric(s.battery_available_for_mission_wh, " Wh", 1) },
  ]);
  renderTable("performanceSummaryTable", [s], Object.keys(s));
  renderTable("sweepTable", results.sweep.slice(0, 20), ["airspeed_m_per_s", "air_power_w", "propulsion_electrical_power_w", "electrical_power_w", "endurance_h", "still_air_range_km", "wind_adjusted_range_km"]);

  const labels = results.sweep.map(row => row.airspeed_m_per_s.toFixed(2));
  upsertChart("powerChart", "powerChart", "line", {
    labels,
    datasets: [
      { label: "Air power [W]", data: results.sweep.map(r => r.air_power_w) },
      { label: "Propulsion electrical [W]", data: results.sweep.map(r => r.propulsion_electrical_power_w) },
      { label: "Total electrical [W]", data: results.sweep.map(r => r.electrical_power_w) },
    ],
  });
  upsertChart("enduranceChart", "enduranceChart", "line", { labels, datasets: [{ label: "Endurance [h]", data: results.sweep.map(r => r.endurance_h) }] });
  upsertChart("rangeChart", "rangeChart", "line", { labels, datasets: [
    { label: "Still-air range [km]", data: results.sweep.map(r => r.still_air_range_km) },
    { label: "Wind-adjusted range [km]", data: results.sweep.map(r => r.wind_adjusted_range_km) },
  ] });
}

function renderOperating(results) {
  renderTable("operatingTable", results.operating, ["operating_point", "airspeed_m_per_s", "electrical_power_w", "endurance_h", "still_air_range_km", "wind_adjusted_range_km"]);
}

function renderMission(results) {
  const m = results.missionSummary;
  const p = results.missionProfile;
  renderMetricCards("missionMetrics", [
    { label: "Required mission feasible", value: fmtMetric(m.mission_feasible) },
    { label: "Required mission time", value: m.required_mission_time_h === null ? "—" : fmtMetric(m.required_mission_time_h, " h") },
    { label: "Required mission energy", value: m.required_mission_energy_wh === null ? "—" : fmtMetric(m.required_mission_energy_wh, " Wh", 1) },
    { label: "Range margin", value: m.range_margin_km === null ? "—" : fmtMetric(m.range_margin_km, " km") },
    { label: "Energy margin", value: m.energy_margin_wh === null ? "—" : fmtMetric(m.energy_margin_wh, " Wh", 1) },
    { label: "Profile feasible", value: fmtMetric(p.mission_feasible) },
    { label: "Profile total time", value: fmtMetric(p.total_time_h, " h") },
    { label: "Profile remaining energy", value: fmtMetric(p.remaining_energy_wh, " Wh", 1) },
  ], {
    "Required mission feasible": m.mission_feasible ? "good" : "bad",
    "Profile feasible": p.mission_feasible ? "good" : "bad",
  });

  renderTable("missionTotalsTable", [{
    available_energy_wh: p.available_energy_wh,
    total_time_h: p.total_time_h,
    total_energy_used_wh: p.total_energy_used_wh,
    total_propulsion_energy_wh: p.total_propulsion_energy_wh,
    total_hotel_energy_wh: p.total_hotel_energy_wh,
    total_payload_energy_wh: p.total_payload_energy_wh,
    total_non_propulsive_energy_wh: p.total_non_propulsive_energy_wh,
    remaining_energy_wh: p.remaining_energy_wh,
    mission_feasible: p.mission_feasible,
    number_of_segments: p.segments.length,
  }]);
  renderTable("missionSegmentsTable", p.segments, ["segment_name", "segment_type", "speed_mode", "distance_km", "duration_min", "airspeed_m_per_s", "ground_speed_m_per_s", "electrical_power_w", "energy_used_wh", "remaining_energy_wh_after_segment"]);

  upsertChart("segmentEnergyChart", "segmentEnergyChart", "bar", {
    labels: p.segments.map(seg => seg.segment_name),
    datasets: [
      { label: "Total energy used [Wh]", data: p.segments.map(seg => seg.energy_used_wh) },
      { label: "Propulsion energy [Wh]", data: p.segments.map(seg => seg.propulsion_energy_wh) },
    ],
  });
  upsertChart("remainingEnergyChart", "remainingEnergyChart", "line", {
    labels: ["start", ...p.segments.map(seg => seg.segment_name)],
    datasets: [{ label: "Remaining energy [Wh]", data: [p.available_energy_wh, ...p.segments.map(seg => seg.remaining_energy_wh_after_segment)] }],
  });
}

function setTradeDefaults() {
  const key = document.getElementById("tradeParameter").value;
  const meta = TRADE_PARAMETERS[key];
  const current = meta.get(activeConfig);
  const min = meta.minFixed !== undefined ? meta.minFixed : Math.max(meta.step, current * meta.minFactor);
  const max = meta.maxPad !== undefined ? Math.max(1000, current + meta.maxPad) : current * meta.maxFactor;
  document.getElementById("tradeMin").value = min;
  document.getElementById("tradeMax").value = max;
  document.getElementById("tradeMin").step = meta.step;
  document.getElementById("tradeMax").step = meta.step;
}

function runTradeStudy() {
  const key = document.getElementById("tradeParameter").value;
  const meta = TRADE_PARAMETERS[key];
  const min = Number(document.getElementById("tradeMin").value);
  const max = Number(document.getElementById("tradeMax").value);
  const points = Number(document.getElementById("tradePoints").value);
  if (!(max > min)) throw new Error("Trade-study maximum must be greater than minimum.");
  const rows = [];
  for (let i = 0; i < points; i++) {
    const value = min + (i * (max - min)) / (points - 1);
    const config = deepClone(activeConfig);
    meta.set(config, value);
    const summary = makeSummary(config);
    const mission = evaluateSimpleMissionProfile(config, config.mission.profile);
    rows.push({
      parameter_value: value,
      still_air_range_km: summary.still_air_range_km,
      wind_adjusted_range_km: summary.wind_adjusted_range_km,
      endurance_h: summary.endurance_h,
      stall_speed_m_per_s: summary.stall_speed_m_per_s,
      electrical_power_required_w: summary.electrical_power_required_w,
      remaining_energy_wh: mission.remaining_energy_wh,
      mission_feasible_flag: mission.mission_feasible ? 1 : 0,
    });
  }
  latestTradeStudy = rows;
  renderTable("tradeTable", rows);
  const labels = rows.map(r => r.parameter_value.toFixed(3));
  upsertChart("tradeRangeChart", "tradeRangeChart", "line", {
    labels,
    datasets: [
      { label: "Still-air range [km]", data: rows.map(r => r.still_air_range_km) },
      { label: "Wind-adjusted range [km]", data: rows.map(r => r.wind_adjusted_range_km) },
      { label: "Endurance [h]", data: rows.map(r => r.endurance_h) },
    ],
  });
  upsertChart("tradeMissionChart", "tradeMissionChart", "line", {
    labels,
    datasets: [
      { label: "Remaining energy [Wh]", data: rows.map(r => r.remaining_energy_wh) },
      { label: "Mission feasible flag", data: rows.map(r => r.mission_feasible_flag) },
    ],
  });
}

function renderComparison() {
  const compareSelect = document.getElementById("compareScenarios");
  const names = [...compareSelect.selectedOptions].map(opt => opt.value);
  latestComparison = names.length >= 2 ? compareSavedScenarios(names) : [];
  renderTable("compareTable", latestComparison);
  const labels = latestComparison.map(row => row.scenario);
  upsertChart("scenarioEnergyChart", "scenarioEnergyChart", "bar", {
    labels,
    datasets: [
      { label: "Total energy used [Wh]", data: latestComparison.map(r => r.total_energy_used_wh) },
      { label: "Remaining energy [Wh]", data: latestComparison.map(r => r.remaining_energy_wh) },
    ],
  });
  upsertChart("scenarioTimeChart", "scenarioTimeChart", "bar", {
    labels,
    datasets: [{ label: "Mission time [h]", data: latestComparison.map(r => r.total_time_h) }],
  });
}

function renderAll() {
  try {
    populateForm(activeConfig);
    latestResults = collectResults(activeConfig);
    renderTop(latestResults);
    renderPerformance(latestResults);
    renderOperating(latestResults);
    renderMission(latestResults);
    renderComparison();
  } catch (error) {
    alert(error.message);
  }
}

function validateAgainstPythonReference() {
  const js = collectResults(deepClone(PRESET_CONFIGS.example_fixed_wing));
  const py = EXPECTED_OUTPUTS.example_fixed_wing;
  const checks = [
    [js.summary.total_mass_kg, py.total_mass_kg],
    [js.summary.stall_speed_m_per_s, py.stall_speed_m_per_s],
    [js.summary.electrical_power_required_w, py.electrical_power_required_w],
    [js.summary.still_air_range_km, py.still_air_range_km],
    [js.operating[0].airspeed_m_per_s, py.best_endurance.airspeed_m_per_s],
    [js.missionProfile.total_energy_used_wh, py.mission_profile.total_energy_used_wh],
    [js.missionProfile.remaining_energy_wh, py.mission_profile.remaining_energy_wh],
  ];
  checks.forEach(([a,b]) => {
    if (Math.abs(a - b) > 1e-6 * Math.max(1, Math.abs(b))) {
      throw new Error(`Validation mismatch: ${a} vs ${b}`);
    }
  });
}

function bindEvents() {
  document.querySelectorAll(".tab").forEach(btn => btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(el => el.classList.remove("is-active"));
    document.querySelectorAll(".tab-panel").forEach(el => el.classList.remove("is-active"));
    btn.classList.add("is-active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("is-active");
  }));

  document.getElementById("loadPresetBtn").addEventListener("click", () => {
    activePresetKey = document.getElementById("presetSelect").value;
    baseConfig = deepClone(PRESET_CONFIGS[activePresetKey]);
    activeConfig = deepClone(baseConfig);
    document.getElementById("scenarioName").value = `${activePresetKey}_custom`;
    renderAll();
  });
  document.getElementById("resetBtn").addEventListener("click", () => { activeConfig = deepClone(baseConfig); renderAll(); });
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

  document.getElementById("downloadConfigBtn").addEventListener("click", () => downloadText(`${document.getElementById("scenarioName").value || "scenario"}.json`, JSON.stringify(activeConfig, null, 2), "application/json"));
  document.getElementById("exportSummaryBtn").addEventListener("click", () => downloadText("uav_summary.csv", rowsToCSV([{ ...latestResults.summary, ...latestResults.missionSummary, mission_profile_feasible: latestResults.missionProfile.mission_feasible, mission_profile_remaining_energy_wh: latestResults.missionProfile.remaining_energy_wh }]), "text/csv"));
  document.getElementById("downloadSweepBtn").addEventListener("click", () => downloadText("speed_sweep.csv", rowsToCSV(latestResults.sweep), "text/csv"));
  document.getElementById("downloadOperatingBtn").addEventListener("click", () => downloadText("operating_points.csv", rowsToCSV(latestResults.operating), "text/csv"));
  document.getElementById("downloadMissionBtn").addEventListener("click", () => downloadText("mission_segments.csv", rowsToCSV(latestResults.missionProfile.segments), "text/csv"));
  document.getElementById("downloadTradeBtn").addEventListener("click", () => downloadText("trade_study.csv", rowsToCSV(latestTradeStudy), "text/csv"));
  document.getElementById("downloadCompareBtn").addEventListener("click", () => downloadText("scenario_comparison.csv", rowsToCSV(latestComparison), "text/csv"));

  document.getElementById("tradeParameter").addEventListener("change", setTradeDefaults);
  document.getElementById("runTradeBtn").addEventListener("click", () => { try { runTradeStudy(); } catch (e) { alert(e.message); } });
}

function seedSavedScenarios() {
  const saved = getSavedScenarios();
  if (Object.keys(saved).length) return;
  saveSavedScenarios({
    baseline: deepClone(PRESET_CONFIGS.example_fixed_wing),
  });
}

function initTradeControls() {
  const select = document.getElementById("tradeParameter");
  select.innerHTML = Object.entries(TRADE_PARAMETERS).map(([key, meta]) => `<option value="${key}">${meta.label}</option>`).join("");
  select.value = "battery_mass_kg";
  setTradeDefaults();
}

function init() {
  buildInputFields();
  syncPresetControls();
  seedSavedScenarios();
  refreshSavedScenarioLists();
  populateForm(activeConfig);
  initTradeControls();
  bindEvents();
  validateAgainstPythonReference();
  renderAll();
  runTradeStudy();
}

document.addEventListener("DOMContentLoaded", init);
