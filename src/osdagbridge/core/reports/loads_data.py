# =============================================================================
# OsdagBridge — Live-load data for Chapter 3 (vehicle & footpath tables)
# =============================================================================
# Builds the rows of the *Vehicle Live Loads* and *Footpath Live Load* tables
# from the Loading tab of Additional Inputs (`loading.live_load.*` keys) and
# the IRC 6:2017 helpers already used by the engine.  Only vehicles selected
# in the UI appear in the table.  Pure data — no LaTeX.
# =============================================================================
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from osdagbridge.core.utils.common import (
    KEY_BL_IRC_CLASS_SV,
    KEY_FOOTPATH,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_ECCENTRICITY,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_SPAN,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_NO_OF_FOOTPATHS,
    KEY_WC_LD_LANE_TABLE_COUNT,
)

logger = logging.getLogger(__name__)

G_KN_PER_TONNE = 9.81


@dataclass
class VehicleRow:
    name: str
    clause: str
    total_load_kN: Optional[float]
    impact_factor: Optional[float]          # (1 + IM); None when not applicable
    impact_note: str                         # e.g. "Cl. 208.2" or "Not applied (Cl. 204.5.3)"
    braking_considered: bool
    braking_kN: Optional[float]              # 20 % of the train load (Cl. 211.2, first lane)
    braking_eccentricity_m: Optional[float]  # height above deck (Cl. 211.3)
    centrifugal: str                         # text — IRC 6 Cl. 212 applies to curved decks only
    description: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────
def _truthy(v) -> bool:
    if v is True:
        return True
    return str(v).strip().lower() in ("true", "yes", "1", "checked", "on")


def _f(v) -> Optional[float]:
    try:
        if v in (None, ""):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _irc6():
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
    return IRC6_2017


def _kN_factor() -> float:
    """Engine vehicle loads are expressed in the `keyfile` unit system
    (`t = kN * g`, `kN = kilo * N`).  Dividing by `kN` yields kilonewtons."""
    try:
        from osdagbridge.core.utils.codes.keyfile import kN
        return float(kN) or 1.0
    except Exception:
        return 1.0


def _sum_kN(vehicle: dict) -> Optional[float]:
    try:
        return round(float(sum(vehicle.get("wheel_loads") or [])) / _kN_factor(), 2)
    except Exception:
        return None


def _total_load_kN(key: str) -> Optional[float]:
    """Total train load in kN from the engine's IRC 6 vehicle definitions."""
    irc6 = _irc6()
    try:
        if key == KEY_LL_IRC_CLASS_A:
            return _sum_kN(irc6.cl_204_1_ClassA_vehicle())
        if key == KEY_LL_IRC_70R_WHEELED:
            return _sum_kN(irc6.cl_204_1_Class70R_vehicle_wheel())
        if key == KEY_LL_IRC_70R_TRACKED:
            v = irc6.cl_204_1_Class70R_vehicle_track()
            udl = float(v.get("wheel_loads_udl", 0.0)) / _kN_factor()   # kN/m per track
            length = float(v["x"][-1] - v["x"][0]) if v.get("x") else 0.0
            n_tracks = len(v.get("z") or [1, 1])
            return round(udl * length * n_tracks, 2)
        if key == KEY_LL_IRC_CLASS_SV:
            return _f(irc6.cl_204_5_1_special_vehicle().get("total_load_kN"))
        if key == KEY_LL_IRC_CLASS_FATIGUE:
            return _sum_kN(irc6.cl_204_6_fatigue_load())
        if key == KEY_LL_IRC_70R_BOGIE:
            return round(2 * 20.0 * G_KN_PER_TONNE, 2)             # 2 axles × 20 t (Cl. 204.1 Fig. 1)
        if key == KEY_LL_IRC_AA_WHEELED:
            return round(40.0 * G_KN_PER_TONNE, 2)                 # 40 t (Annex A)
        if key == KEY_LL_IRC_AA_TRACKED:
            return round(70.0 * G_KN_PER_TONNE, 2)                 # 70 t (Annex A)
    except Exception as exc:
        logger.warning("Could not evaluate total load for %s: %s", key, exc)
    return None


#: (input key, display name, IRC 6 clause, impact rule, short description)
VEHICLE_SPECS: Sequence[Tuple[str, str, str, str, str]] = (
    (KEY_LL_IRC_CLASS_A,        "Class A",            "Cl. 204.1", "class_a", "Two-lane carriageway train"),
    (KEY_LL_IRC_AA_WHEELED,     "Class AA (Wheeled)", "Annex A",   "heavy",   "Wheeled, 40 t"),
    (KEY_LL_IRC_AA_TRACKED,     "Class AA (Tracked)", "Annex A",   "tracked", "Tracked, 70 t"),
    (KEY_LL_IRC_70R_WHEELED,    "Class 70R (Wheeled)", "Cl. 204.1", "heavy",  "Wheeled, 100 t"),
    (KEY_LL_IRC_70R_TRACKED,    "Class 70R (Tracked)", "Cl. 204.1", "tracked", "Tracked, 70 t"),
    (KEY_LL_IRC_70R_BOGIE,      "Class 70R (Bogie)",  "Cl. 204.1", "heavy",   "Bogie, 2 × 20 t"),
    (KEY_LL_IRC_CLASS_SV,       "Class SV",           "Cl. 204.5", "sv",      "Special vehicle, 385 t"),
    (KEY_LL_IRC_CLASS_FATIGUE,  "Class Fatigue",      "Cl. 204.6", "class_a", "Fatigue truck, 40 t"),
)


def selected_vehicles(input_dict: dict) -> List[Tuple[str, str]]:
    """[(key, name)] of the vehicles ticked in the Loading tab (UI order)."""
    out = [(k, name) for k, name, *_ in VEHICLE_SPECS if _truthy(input_dict.get(k))]
    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if isinstance(custom, list):
        for c in custom:
            if isinstance(c, dict) and c.get("name"):
                out.append(("custom", str(c["name"])))
            elif isinstance(c, str) and c.strip():
                out.append(("custom", c.strip()))
    return out


def _impact(rule: str, span_m: Optional[float]) -> Tuple[Optional[float], str]:
    if span_m is None:
        return None, "span not available"
    irc6 = _irc6()
    try:
        if rule == "class_a":
            return round(1.0 + irc6.cl_208_2_impact_factor(span_m), 3), "Cl. 208.2"
        if rule in ("heavy", "tracked"):
            return round(1.0 + irc6.cl_208_3_impact_factor(span_m), 3), "Cl. 208.3"
        if rule == "sv":
            return None, "Not applied"
    except Exception as exc:
        logger.warning("Impact factor lookup failed (%s): %s", rule, exc)
    return None, "---"


def braking_force_total_kN(input_dict: dict, rows: Sequence[VehicleRow]) -> Tuple[Optional[float], str]:
    """Total longitudinal braking force per IRC 6 Cl. 211.2 for the design lanes.

    20 % of the first lane train + 10 % of the second lane train (same class),
    plus 5 % of the loads on each lane in excess of two.  The governing
    (heaviest braking-considered, non-SV) train is used for every lane.
    """
    lanes = int(_f(input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)) or 0)
    trains = [r for r in rows if r.braking_considered and r.total_load_kN and r.name != "Class SV"]
    if lanes <= 0 or not trains:
        return None, "---"
    w = max(r.total_load_kN for r in trains)
    name = max(trains, key=lambda r: r.total_load_kN).name
    total = 0.20 * w
    if lanes >= 2:
        total += 0.10 * w
    if lanes > 2:
        total += 0.05 * w * (lanes - 2)
    return round(total, 2), f"{lanes} lane(s), {name} train (Cl. 211.2)"


def vehicle_rows(input_dict: dict) -> List[VehicleRow]:
    """One row per vehicle selected in the UI."""
    span = _f(input_dict.get(KEY_SPAN))
    ecc = _f(input_dict.get(KEY_LL_ECCENTRICITY))
    sv_braking = _truthy(input_dict.get(KEY_BL_IRC_CLASS_SV))
    rows: List[VehicleRow] = []
    spec_by_key = {k: (name, clause, rule, desc) for k, name, clause, rule, desc in VEHICLE_SPECS}
    for key, name in selected_vehicles(input_dict):
        if key == "custom":
            rows.append(VehicleRow(name, "User-defined", None, None, "---", False, None, ecc,
                                   "Not applicable", "Custom vehicle"))
            continue
        _, clause, rule, desc = spec_by_key[key]
        total = _total_load_kN(key)
        imp, imp_note = _impact(rule, span)
        if key == KEY_LL_IRC_CLASS_SV:
            braking_on = sv_braking
        else:
            braking_on = True        # braking follows the vehicle selection (Cl. 211.2)
        braking = round(0.20 * total, 2) if (braking_on and total) else None
        rows.append(VehicleRow(
            name=name, clause=clause, total_load_kN=total,
            impact_factor=imp, impact_note=imp_note,
            braking_considered=braking_on, braking_kN=braking,
            braking_eccentricity_m=ecc,
            centrifugal="Not applicable",
            description=desc,
        ))
    return rows


def footpath_rows(input_dict: dict) -> List[Tuple[str, str]]:
    """(parameter, value) rows of the Footpath Live Load table."""
    irc6 = _irc6()
    fp_present = str(input_dict.get(KEY_FOOTPATH, "")).strip()
    has_fp = fp_present.lower() not in ("", "no", "none", "false", "0")
    mode = str(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")).strip()
    custom_val = _f(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE))
    n_fp = input_dict.get(KEY_TS_NO_OF_FOOTPATHS)
    width = _f(input_dict.get(KEY_TS_FOOTPATH_WIDTH))

    rows: List[Tuple[str, str]] = []
    rows.append(("Footpath Provided", fp_present or "No"))
    if has_fp:
        if n_fp not in (None, ""):
            rows.append(("Number of Footpaths", str(n_fp)))
        if width is not None:
            rows.append(("Footpath Width", f"{width:g} m"))

    if mode.lower() in ("as per irc 6", "as per irc6", "automatic", ""):
        try:
            p = float(irc6.cl_206_1_footway_load())
            rows.append(("Footway Live Load Intensity, $P$", f"{p:.3f} kN/m\\textsuperscript{{2}}"))
        except Exception:
            rows.append(("Footway Live Load Intensity, $P$", "---"))
        rows.append(("Basis", "As per IRC 6:2017 Cl. 206.1 (500 kg/m\\textsuperscript{2} for spans up to 7.5 m, reduced for longer spans)"))
    else:
        rows.append(("Footway Live Load Intensity, $P$",
                     f"{custom_val:.3f} kN/m\\textsuperscript{{2}}" if custom_val is not None else "---"))
        rows.append(("Basis", "User-defined (Custom)"))

    try:
        kerb = irc6.cl_206_2_kerb_load()
        rows.append(("Kerb Load (Cl. 206.2)",
                     f"{float(kerb.get('kerb_load_kN_per_m2', 0)):.3f} kN/m\\textsuperscript{{2}} "
                     f"(kerb width {kerb.get('kerb_width_mm', '---')} mm)"))
    except Exception:
        pass
    if not has_fp:
        rows.append(("Note", "No footpath in the typical section; footway live load is not applied to the deck."))
    return rows
