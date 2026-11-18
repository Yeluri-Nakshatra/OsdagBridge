# =============================================================================
# Chapter 3: Loads and Load Combinations
# Presentation only — values come from input_dict, IRC 6 helpers and
# `loads_data` (vehicle / footpath rows).  Layout from `styles` via builders.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CB_LOAD,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_RL_LOAD_VALUE,
    KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_TIME_PERIOD,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_ZONE_FACTOR,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE,
)

from osdagbridge.core.reports.report_utils import _tex, _render_value
from .latex_builders import Cell, Column, KeyValueTable, LongTable
from .loads_data import braking_force_total_kN, footpath_rows, vehicle_rows

_M2 = r" kN/m\textsuperscript{2}"
_M3 = r" kN/m\textsuperscript{3}"
_DEG = r" $^\circ$C"


def _fmt(v, nd=2, unit=""):
    try:
        return f"{float(v):.{nd}f}{unit}"
    except (TypeError, ValueError):
        return "---"


# ─────────────────────────────────────────────────────────────────────────────
# Live loads
# ─────────────────────────────────────────────────────────────────────────────
def _vehicle_live_load_table(input_dict) -> str:
    rows = vehicle_rows(input_dict)
    t = LongTable(
        columns=[Column(2.5, "l"), Column(1.6, "c"), Column(1.6, "c"), Column(2.2, "c"),
                 Column(1.5, "c"), Column(2.2, "c"), Column(2.2, "c")],
        caption="Vehicle Live Loads (IRC 6:2017 Cl. 204)",
        label="tab:vehicle-live-loads",
        header=[
            [Cell("Vehicle", rowspan=2, bold=True), "Total Load", "Impact Factor",
             Cell("Braking Load (Cl. 211)", colspan=3, bold=True), "Centrifugal Force"],
            [None, "(kN)", "(1 + IM)", "Considered?", "Value (kN)", "Eccentricity (m)", "(Cl. 212)"],
        ],
        size="compact",
        note=(r"Total load = sum of axle loads of one train (IRC 6 Cl. 204 / Annex A). "
              r"Impact factor per Cl. 208.2 (Class A, Fatigue) and Cl. 208.3 (Class AA / 70R); "
              r"not applied to the SV loading (Cl. 204.5.3). Braking value = 20\,\% of the train load "
              r"(first lane, Cl. 211.2) acting at the eccentricity above the deck (Cl. 211.3). "
              r"Centrifugal force (Cl. 212) applies to curved alignments only; the deck is straight, so it is not applicable."),
    )
    if not rows:
        t.add_message_row("---", r"No vehicle selected in the Loading tab")
    for r in rows:
        if r.impact_factor is not None:
            imp = f"{r.impact_factor:.3f}"
        else:
            imp = r"\footnotesize " + _tex(r.impact_note)
        t.add_row([
            _tex(r.name),
            _fmt(r.total_load_kN, 1) if r.total_load_kN is not None else "---",
            imp,
            "Yes" if r.braking_considered else "No",
            _fmt(r.braking_kN, 1) if r.braking_kN is not None else "---",
            _fmt(r.braking_eccentricity_m, 2) if r.braking_eccentricity_m is not None else "---",
            r"\footnotesize " + _tex(r.centrifugal),
        ])
    total, basis = braking_force_total_kN(input_dict, rows)
    if total is not None:
        t.add_message_row(r"\textbf{Design braking force}",
                          rf"\textbf{{{total:.1f} kN}} --- {_tex(basis)}")
    return t.render()


def _footpath_live_load_table(input_dict) -> str:
    t = KeyValueTable(caption="Footpath Live Load (IRC 6:2017 Cl. 206)", label="tab:footpath-live-load")
    for param, value in footpath_rows(input_dict):
        t.add(param, value)
    return t.render()


# ─────────────────────────────────────────────────────────────────────────────
# Chapter
# ─────────────────────────────────────────────────────────────────────────────
def ch3_loads(input_dict):
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    # ── Wind: prefer stored values; fall back to IRC 6 Table 12 ───────────
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not vz_val or not pz_val:
        try:
            _vb  = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or input_dict.get('wind_speed')
            _h   = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)
            _ter = {"Plain Terrain": "plain", "Terrain with Obstructions": "obstructed"}.get(
                str(input_dict.get(KEY_WL_TERRAIN_TYPE, "")).strip(), "plain")
            _res = IRC6_2017.table_12(float(_h), _ter, float(_vb))
            vz_val = vz_val or _res.get("Vz")
            pz_val = pz_val or _res.get("Pz")
        except Exception:
            pass

    # ── Seismic: prefer stored values; fall back to IRC 6 Cl. 218.5.1 ──────
    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral    = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah          = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av          = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z    = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st   = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp   = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res  = IRC6_2017.cl_218_5_1(zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                        live_load_kN=_live, period_T=float(_tp) if _tp else None,
                        damping_percent=float(_damp))
            sl_zone_factor = sl_zone_factor or _res.get("Z")
            sl_spectral    = sl_spectral or _res.get("Sa_g_adjusted")
            sl_ah          = sl_ah or _res.get("Ah")
            sl_av          = sl_av or round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    def _sl(v):
        return f"{float(v):.4f}" if v not in (None, "") else "N/A"

    # ── Load combinations (dynamically generated from IRC 6) ───────────────
    _LOAD_LABEL_MAP = {
        'dead_load': 'DL', 'surfacing': 'SIDL', 'live_load': 'LL', 'wind_load': 'WL',
        'thermal_load': 'TL', 'vehicle_collision': 'VC', 'barge_impact': 'BI',
        'floating_bodies': 'FB', 'seismic': 'EQ',
    }

    def _fmt_factors(factors):
        parts = []
        for load, val in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):
                add = val.get('adding')
                rel = val.get('relieving')
                add_s = f"{add:.2f}" if add is not None else '--'
                rel_s = f"{rel:.2f}" if rel is not None else '--'
                parts.append(f"{label}({add_s}/{rel_s})")
            else:
                if val is None:
                    continue
                parts.append(f"{label}({val:.2f})")
        return ' + '.join(parts)

    lc = LongTable([Column(3.4, "c", "Combination ID"), Column(11.6, "l", "Load Cases (partial factors)")],
                   caption="Load Combinations (IRC 6:2017 Annex B)", label="tab:load-combinations",
                   note=r"All IRC 6 load combinations are auto-generated by OsdagBridge. "
                        r"Permanent loads are shown as (adding / relieving) factors. "
                        r"User-defined custom combinations, if any, are appended.")
    try:
        for i, combo in enumerate(IRC6_2017.uls_load_combinations(), start=1):
            lc.add_row([f"ULS-{i:02d}", _tex(_fmt_factors(combo['factors']))])
        for i, combo in enumerate(IRC6_2017.sls_load_combinations(), start=1):
            lc.add_row([f"SLS-{i:02d}", _tex(_fmt_factors(combo['factors']))])
    except Exception:
        pass

    # ── Tables ────────────────────────────────────────────────────────────
    dead = KeyValueTable(caption="Dead Load --- Self Weight (DL)", label="tab:dead-load")
    dead.add("Steel Self-Weight (unit weight)", _render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, _M3))
    dead.add("Concrete Deck (unit weight)", _render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, _M3))
    dead.add("Self-Weight Factor", _render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR))

    sidl = KeyValueTable(caption="Superimposed Dead Load --- Surfacing and Furniture (SIDL)", label="tab:sidl")
    sidl.add("Wearing Course", _render_value(input_dict, KEY_WC_MATERIAL) + ", "
             + _render_value(input_dict, KEY_WC_THICKNESS, " mm"))
    sidl.add("Crash Barrier Load", _render_value(input_dict, KEY_CB_LOAD, " kN/m per barrier"))
    sidl.add("Railing Load", _render_value(input_dict, KEY_RL_LOAD_VALUE, r" kN/m\sdstar{}"))

    wind = KeyValueTable(caption="Wind Load (WL) --- IRC 6:2017 Cl. 209", label="tab:wind-load")
    wind.add(r"Basic Wind Speed, $V_b$", _render_value(input_dict, 'wind_speed', ' m/s') + " [from Project Location]")
    wind.add("Terrain Type", _render_value(input_dict, KEY_WL_TERRAIN_TYPE))
    wind.add("Average Exposed Height, $H$", _render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m'))
    wind.add(r"Hourly Mean Wind Speed, $V_z$", _fmt(vz_val, 2, " m/s") if vz_val not in (None, "") else "N/A")
    wind.add(r"Hourly Wind Pressure, $P_z$", _fmt(pz_val, 2, r" N/m\textsuperscript{2}") if pz_val not in (None, "") else "N/A")
    wind.add("Transverse Wind Force", _render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, ' kN'))
    wind.add("Longitudinal Wind Force", _render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN'))
    wind.add("Vertical Wind Force", _render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, ' kN'))

    eq = KeyValueTable(caption="Earthquake Load (EQ) --- IRC 6:2017 Cl. 218", label="tab:seismic-load")
    eq.add("Seismic Zone", _render_value(input_dict, 'seismic_zone') + " [from Project Location]")
    eq.add("Zone Factor, $Z$", _sl(sl_zone_factor))
    eq.add("Importance Factor, $I$", _render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR))
    eq.add("Type of Soil", _render_value(input_dict, KEY_SL_SOIL_TYPE))
    eq.add(r"Spectral Acceleration Coefficient, $S_a/g$", _sl(sl_spectral))
    eq.add("Horizontal Seismic Coefficient, $A_h$", _sl(sl_ah))
    eq.add("Vertical Seismic Coefficient, $A_v$", _sl(sl_av))

    temp = KeyValueTable(caption="Temperature Load (TL) --- IRC 6:2017 Cl. 215", label="tab:temperature-load")
    temp.add("Maximum Shade Temperature", _render_value(input_dict, 'shade_temp_max') + _DEG)
    temp.add("Minimum Shade Temperature", _render_value(input_dict, 'shade_temp_min') + _DEG)
    temp.add("Effective Bridge Temperature Range",
             _render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN) + " to "
             + _render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX) + _DEG)
    temp.add("Temperature Rise / Fall for Design",
             "+" + _render_value(input_dict, KEY_TL_TEMP_RISE) + _DEG + r" / \textminus{}"
             + _render_value(input_dict, KEY_TL_TEMP_FALL) + _DEG)

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\section{Permanent Loads}
\label{sec:permanent-loads}

""" + dead.render() + "\n" + sidl.render() + r"""

\section{Live Loads}
\label{sec:live-loads}

Vehicular live loads are applied as per the vehicle classes selected in the \emph{Loading} tab of the Additional Inputs. Each selected vehicle is listed below with its total load, dynamic impact allowance and the associated longitudinal (braking) and centrifugal effects. Footpath (footway) live load is reported separately.

""" + _vehicle_live_load_table(input_dict) + "\n" + _footpath_live_load_table(input_dict) + r"""

\section{Environmental Loads}
\label{sec:environmental-loads}

""" + wind.render() + "\n" + eq.render() + "\n" + temp.render() + r"""

\section{Load Combinations}
\label{sec:load-combinations}

""" + lc.render()
