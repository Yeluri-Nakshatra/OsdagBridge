# =============================================================================
# OsdagBridge — Report summary data (utilisation ratios & material quantities)
# =============================================================================
# Pure data extraction for the Section 5.5 utilisation-ratio charts and the
# Chapter 7 material-quantity charts.  No LaTeX, no matplotlib: every function
# reads already-computed engine results from `output_dict` / `input_dict` and
# returns plain dataclasses, so the module is unit-testable in isolation and
# the charts/tables stay thin.
#
# Nothing is recalculated here — the values are the same ones printed in the
# individual check tables of Chapter 5 and Table 7.1.
# =============================================================================
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from osdagbridge.core.utils.common import (
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_GIRDER_SPACING,
    KEY_MP_ED_TYPE,
    KEY_UTIL_FLEXURE,
    KEY_UTIL_SHEAR,
    KEY_UTIL_INTERACTION,
    KEY_UTIL_LTB,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class URItem:
    """One design check: label + utilisation ratio (demand / capacity)."""
    label: str
    ur: Optional[float]
    status: str = ""                 # PASS / WARN / FAIL / N/A
    demand: Optional[float] = None
    capacity: Optional[float] = None
    unit: str = ""
    governing: str = ""              # governing load case / member

    @property
    def passes(self) -> Optional[bool]:
        if self.ur is None:
            return None
        return self.ur <= 1.0


@dataclass
class ComponentUR:
    """Utilisation ratios of one primary element."""
    name: str                        # "Steel Plate Girders"
    key: str                         # girder | deck | bracing | diaphragm
    items: List[URItem] = field(default_factory=list)
    note: str = ""                   # shown when there are no items

    @property
    def max_ur(self) -> Optional[float]:
        vals = [i.ur for i in self.items if i.ur is not None]
        return max(vals) if vals else None

    @property
    def governing_item(self) -> Optional[URItem]:
        cands = [i for i in self.items if i.ur is not None]
        return max(cands, key=lambda i: i.ur) if cands else None

    @property
    def status(self) -> str:
        m = self.max_ur
        if m is None:
            return "N/A"
        return "PASS" if m <= 1.0 else "FAIL"


@dataclass
class MaterialSummary:
    """Material quantities for Chapter 7 charts (all derived from Table 7.1)."""
    steel_items: List[Tuple[str, Optional[float]]] = field(default_factory=list)  # (label, MT)
    concrete_m3: Optional[float] = None
    rebar_mt: Optional[float] = None
    shear_studs_mt: Optional[float] = None
    crash_barrier_m3: Optional[float] = None
    end_diaphragm: Optional[dict] = None     # row data for Table 7.1 (2(d))

    @property
    def total_steel_mt(self) -> Optional[float]:
        vals = [v for _, v in self.steel_items if v is not None]
        return sum(vals) if vals else None


# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────
def _f(v) -> Optional[float]:
    try:
        if v is None or v == "" or str(v).strip().upper() in ("N.A.", "NA", "N/A", "---"):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _status_for(ur: Optional[float], engine_status=None) -> str:
    if engine_status:
        s = str(engine_status).upper()
        if "FAIL" in s:
            return "FAIL"
        if "WARN" in s:
            return "WARN"
        if "PASS" in s:
            return "PASS"
    if ur is None:
        return "N/A"
    return "PASS" if ur <= 1.0 else "FAIL"


# ─────────────────────────────────────────────────────────────────────────────
# Steel plate girders
# ─────────────────────────────────────────────────────────────────────────────
#: Check-id groups mirror `designer.PlateGirderDesigner.CATEGORY_MAP`.
GIRDER_CHECK_CATEGORIES: Sequence[Tuple[str, Tuple[int, ...]]] = (
    ("Flexure",               (1,)),
    ("Shear",                 (2,)),
    ("Interaction",           (3, 4)),
    ("LTB (construction)",    (5,)),
    ("Longitudinal shear",    (6, 7)),
    ("Fatigue",               (8, 9)),
    ("SLS stress",            (11,)),
    ("Deflection",            (13, 14)),
)


def girder_urs(output_dict: dict) -> ComponentUR:
    """Worst UR per check category across all (non edge-beam) girders."""
    comp = ComponentUR("Steel Plate Girders", "girder")
    dr = output_dict.get("design_results", {}) or {}
    per_girder = dr.get("per_girder", {}) or {}

    best: Dict[str, URItem] = {}
    for g, gd in per_girder.items():
        if str(g).startswith("EB") or not isinstance(gd, dict):
            continue
        checks = list(gd.get("checks") or [])
        # SLS-conditional checks (deflection, stress) may only exist per load case
        for lc, ld in (gd.get("per_lc") or {}).items():
            if str(lc).lower().startswith("envelope"):
                continue
            for chk in (ld.get("checks") or []):
                checks.append({
                    "check_id": chk.get("id"), "name": chk.get("label"),
                    "dcr": chk.get("dcr"), "demand": chk.get("demand"),
                    "capacity": chk.get("capacity"), "status": chk.get("status"),
                    "governing": lc,
                })
        for label, ids in GIRDER_CHECK_CATEGORIES:
            for chk in checks:
                if chk.get("check_id") not in ids:
                    continue
                ur = _f(chk.get("dcr"))
                if ur is None:
                    continue
                cur = best.get(label)
                if cur is None or ur > cur.ur:
                    best[label] = URItem(
                        label=label, ur=round(ur, 4),
                        status=_status_for(ur, chk.get("status")),
                        demand=_f(chk.get("demand")), capacity=_f(chk.get("capacity")),
                        unit=str(chk.get("demand_unit") or ""),
                        governing=str(chk.get("governing") or g),
                    )
    if best:
        comp.items = [best[label] for label, _ in GIRDER_CHECK_CATEGORIES if label in best]
        return comp

    # Fallback: flat category URs stored as percentages (util.* keys)
    for label, key in (("Flexure", KEY_UTIL_FLEXURE), ("Shear", KEY_UTIL_SHEAR),
                       ("Interaction", KEY_UTIL_INTERACTION), ("LTB (construction)", KEY_UTIL_LTB)):
        v = _f(output_dict.get(key))
        if v is not None:
            comp.items.append(URItem(label, round(v / 100.0, 4), _status_for(v / 100.0)))
    if not comp.items:
        comp.note = "Girder design results not available."
    return comp


# ─────────────────────────────────────────────────────────────────────────────
# Concrete deck slab
# ─────────────────────────────────────────────────────────────────────────────
#: (label, keys) — the worst of the listed `deck_design_results` keys is used.
DECK_UR_GROUPS: Sequence[Tuple[str, Tuple[str, ...]]] = (
    ("Flexure (sagging)",   ("ur_bot_uls",)),
    ("Flexure (hogging)",   ("ur_top_uls",)),
    ("Overhang flexure",    ("ur_oh_uls",)),
    ("One-way shear",       ("ur_bot_shear", "ur_oh_shear")),
    ("Punching shear",      ("ur_bot_punch", "ur_oh_punch")),
    ("Transverse shear",    ("ur_composite_trans_shear",)),
    ("Crack width",         ("ur_bot_crack", "ur_top_crack", "ur_oh_crack", "ur_composite_crack")),
    ("SLS concrete stress", ("ur_bot_sls_c", "ur_top_sls_c", "ur_oh_sls_c", "ur_composite_conc_stress")),
    ("SLS rebar stress",    ("ur_bot_sls_s", "ur_top_sls_s", "ur_oh_sls_s", "ur_composite_rebar_stress")),
)


def deck_urs(output_dict: dict) -> ComponentUR:
    comp = ComponentUR("Concrete Deck Slab", "deck")
    dd = output_dict.get("deck_design_results", {}) or {}
    for label, keys in DECK_UR_GROUPS:
        vals = [(_f(dd.get(k)), k) for k in keys if dd.get(k) is not None]
        vals = [(v, k) for v, k in vals if v is not None and v < 9.0]   # 9.999 = "not computed"
        if not vals:
            continue
        v, k = max(vals, key=lambda t: t[0])
        comp.items.append(URItem(label, round(v, 4), _status_for(v), governing=k))
    if not comp.items:
        comp.note = "Deck slab design results not available."
    return comp


# ─────────────────────────────────────────────────────────────────────────────
# Cross bracing / end diaphragm (Osdag member design dumps)
# ─────────────────────────────────────────────────────────────────────────────
def extract_member_summary(result: Optional[dict]) -> dict:
    """Normalise an Osdag member-design dump to {section, capacity_kN, efficiency,
    slenderness, connection}.

    Mirrors `results_data._extract_osdag_summary` so the report package does
    not import the solver-bound `results_data` module (which pulls in
    OpenSees at import time).
    """
    if not result:
        return {}

    def _first(*keys):
        for k in keys:
            v = result.get(k)
            if v is not None:
                return v
        return None

    return {
        "section":     _first("section_size.designation", "Optimum.Designation"),
        "capacity_kN": _first("Member.tension_capacity",  "Design.Strength"),
        "efficiency":  _first("Member.efficiency",        "Optimum.UR"),
        "slenderness": result.get("Member.Slenderness"),
        "connection":  "Welded" if "Weld.Type" in result else "Bolted",
    }


def _osdag_summary(raw: dict) -> dict:
    try:
        return extract_member_summary(raw or {})
    except Exception:
        return {}


def member_design_urs(pair_designs: dict, forces_dict: Optional[dict], name: str, key: str,
                      slenderness_limits: Tuple[float, float] = (250.0, 400.0)) -> ComponentUR:
    """URs of a bracing-type member set: {pair: {member: {force_type: raw}}}.

    Items (worst over all panels): diagonal/chord × compression/tension, plus
    the slenderness ratio expressed as KL/r divided by its IS 800 limit.
    """
    comp = ComponentUR(name, key)
    if not isinstance(pair_designs, dict) or not pair_designs:
        comp.note = f"{name} design results not available."
        return comp

    best: Dict[str, URItem] = {}
    slender_best: Optional[URItem] = None
    for pair, members in pair_designs.items():
        if not isinstance(members, dict):
            continue
        for member, force_types in members.items():
            if not isinstance(force_types, dict):
                continue
            m_label = "Diagonal" if str(member).lower().startswith("diag") else "Chord"
            for ftype, raw in force_types.items():
                summ = _osdag_summary(raw)
                ur = _f(summ.get("efficiency"))
                cap = _f(summ.get("capacity_kN"))
                f_label = "compression" if str(ftype).lower().startswith("comp") else "tension"
                label = f"{m_label} ({f_label})"
                if ur is not None:
                    cur = best.get(label)
                    if cur is None or ur > cur.ur:
                        best[label] = URItem(label, round(ur, 4), _status_for(ur),
                                             demand=(cap * ur if cap else None), capacity=cap,
                                             unit="kN", governing=str(pair))
                sl = _f(summ.get("slenderness"))
                if sl is not None:
                    limit = slenderness_limits[0] if (m_label == "Diagonal" or f_label == "compression") else slenderness_limits[1]
                    ratio = sl / limit if limit else None
                    if ratio is not None and (slender_best is None or ratio > slender_best.ur):
                        slender_best = URItem("Slenderness", round(ratio, 4), _status_for(ratio),
                                              demand=sl, capacity=limit, unit="KL/r",
                                              governing=f"{pair} {m_label.lower()}")
    order = ["Diagonal (compression)", "Diagonal (tension)", "Chord (compression)", "Chord (tension)"]
    comp.items = [best[k] for k in order if k in best] + [best[k] for k in best if k not in order]
    if slender_best is not None:
        comp.items.append(slender_best)
    if not comp.items:
        comp.note = f"{name} design results not available."
    return comp


def bracing_urs(output_dict: dict) -> ComponentUR:
    return member_design_urs(output_dict.get("crossbracing_design_results"),
                             output_dict.get("crossbracing_forces_dict"),
                             "Cross Bracing", "bracing")


def diaphragm_urs(output_dict: dict, input_dict: Optional[dict] = None) -> ComponentUR:
    comp = member_design_urs(output_dict.get("end_diaphragm_design_results"),
                             output_dict.get("end_diaphragm_forces_dict"),
                             "End Diaphragms", "diaphragm")
    if not comp.items:
        ed_type = _end_diaphragm_type(input_dict or {})
        if ed_type and "brac" not in ed_type.lower():
            comp.note = (f"End diaphragm configured as {ed_type}; moment/shear design of "
                         "rolled/welded diaphragms is not implemented in this version.")
    return comp


def _end_diaphragm_type(input_dict: dict) -> str:
    for k, v in (input_dict or {}).items():
        if str(k).startswith(KEY_MP_ED_TYPE) and v:
            return str(v)
    return ""


def collect_utilization(output_dict: dict, input_dict: Optional[dict] = None) -> List[ComponentUR]:
    """All four primary elements, in report order (always 4 entries)."""
    output_dict = output_dict or {}
    return [
        girder_urs(output_dict),
        deck_urs(output_dict),
        bracing_urs(output_dict),
        diaphragm_urs(output_dict, input_dict),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Material quantities (Chapter 7)
# ─────────────────────────────────────────────────────────────────────────────
STEEL_DENSITY_T_PER_M3 = 7.85


def end_diaphragm_quantities(input_dict: dict, output_dict: dict) -> Optional[dict]:
    """Tonnage of the end diaphragms from the ED design results.

    The BOQ generator covers girders and cross bracing only; end diaphragms are
    derived here from the same section properties the ED design stored in
    `output_dict` (`transverse_member_design.ed.section_properties.*`).
    Returns None when the ED has not been designed.
    """
    try:
        n_g = int(float(input_dict.get(KEY_TS_NO_OF_GIRDERS) or 0))
    except (TypeError, ValueError):
        return None
    if n_g < 2:
        return None
    pairs = [f"G{i}G{i+1}" for i in range(1, n_g)]
    ed_type = _end_diaphragm_type(input_dict)
    is_bracing = "brac" in ed_type.lower() if ed_type else bool(output_dict.get("end_diaphragm_forces_dict"))
    geom = (output_dict.get("end_diaphragm_forces_dict") or {}).get("geometry", {}) or {}
    spacing = _f(input_dict.get(KEY_TS_GIRDER_SPACING)) or 0.0

    total_len_m = 0.0
    total_mass_kg = 0.0
    n_members = 0
    for pid in pairs:
        if is_bracing:
            members = (
                ("end_diaphragm", 2, _f(geom.get("diagonal_length_m")) or 0.0),   # 2 diagonals
                ("top_chord",     1, _f(geom.get("horiz_proj_m")) or spacing),
                ("bottom_chord",  1, _f(geom.get("horiz_proj_m")) or spacing),
            )
        else:
            members = (("end_diaphragm", 1, spacing),)
        for name, count, length in members:
            pfx = f"transverse_member_design.ed.section_properties.{name}.{pid}"
            area_cm2 = _f(output_dict.get(f"{pfx}.A"))
            mass_kg_m = _f(output_dict.get(f"{pfx}.M"))
            if area_cm2 is None and mass_kg_m is None:
                continue
            if mass_kg_m is None:
                mass_kg_m = area_cm2 / 1e4 * STEEL_DENSITY_T_PER_M3 * 1000.0
            if length <= 0:
                continue
            n = count * 2            # diaphragms at both supports
            n_members += n
            total_len_m += n * length
            total_mass_kg += n * length * mass_kg_m
    if n_members == 0:
        return None
    vol_m3 = total_mass_kg / (STEEL_DENSITY_T_PER_M3 * 1000.0)
    return {
        "qty": n_members,
        "vol_total_m3": round(vol_m3, 3),
        "wt_single_mt": round(total_mass_kg / n_members / 1000.0, 4),
        "wt_total_mt": round(total_mass_kg / 1000.0, 3),
        "length_total_m": round(total_len_m, 2),
        "type": ed_type or ("Cross Bracing" if is_bracing else "Beam"),
    }


def collect_material_quantities(input_dict: dict, output_dict: dict) -> MaterialSummary:
    """Material summary from the Table 7.1 quantities (already injected into
    `input_dict` by `calculate_material_quantities`) plus the end diaphragms."""
    inp = input_dict or {}
    girders = _f(inp.get("steel_girders_wt_total"))
    bracing_parts = [_f(inp.get(k)) for k in ("bracing_top_wt_total", "bracing_bot_wt_total", "bracing_diag_wt_total")]
    bracing = sum(v for v in bracing_parts if v is not None) if any(v is not None for v in bracing_parts) else None
    ed = end_diaphragm_quantities(inp, output_dict or {})
    ed_mt = ed["wt_total_mt"] if ed else None
    return MaterialSummary(
        steel_items=[("Plate Girders", girders), ("Cross Bracing", bracing), ("End Diaphragms", ed_mt)],
        concrete_m3=_f(inp.get("concrete_deck_vol_total")),
        rebar_mt=_f(inp.get("rebar_deck_wt_total")),
        shear_studs_mt=_f(inp.get("shear_studs_wt_total")),
        crash_barrier_m3=_f(inp.get("crash_barrier_vol_total")),
        end_diaphragm=ed,
    )
