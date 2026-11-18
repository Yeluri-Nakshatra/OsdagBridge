# =============================================================================
# OsdagBridge — Report fixture (headless sample design)
# =============================================================================
# A realistic, self-contained `input_dict` / `output_dict` pair that mirrors
# the key scheme produced by the plate-girder pipeline (defaults.py, designer.py,
# deckdesign.py, crossbracingforces.py, Osdag member-design dumps).  It lets
# the report generator be exercised without the GUI, OpenSees or CAD:
#
#     python tools/report_preview.py --out build/report
#
# Numbers are representative of a 30 m, 3-girder, two-lane composite plate
# girder bridge; they are *sample data*, not a verified design.
# =============================================================================
from __future__ import annotations

import io
import math
from typing import Dict

from osdagbridge.core.utils.common import (  # noqa: E402
    KEY_BL_IRC_CLASS_SV, KEY_CARRIAGEWAY_WIDTH, KEY_CB_AREA, KEY_CB_LOAD, KEY_CB_TYPE,
    KEY_CROSS_BRACING, KEY_DECK_CONCRETE_GRADE_BASIC, KEY_DESIGN_MODE,
    KEY_DD_AS_BOT, KEY_DD_AS_LONG, KEY_DD_AS_MIN, KEY_DD_AS_REQ_BOT, KEY_DD_AS_REQ_TOP, KEY_DD_AS_TOP,
    KEY_DD_COVER_OK, KEY_DD_DIA_BOT, KEY_DD_D_BOT, KEY_DD_FY, KEY_DD_GAMMA_DL, KEY_DD_GAMMA_LL,
    KEY_DD_HAS_OVERHANG, KEY_DD_IMPACT_FACTOR, KEY_DD_MIN_COVER, KEY_DD_MU_BOT, KEY_DD_MU_OH,
    KEY_DD_MU_TOP, KEY_DD_M_BARRIER, KEY_DD_M_DL, KEY_DD_M_DL_OH, KEY_DD_M_LL, KEY_DD_M_LL_OH,
    KEY_DD_M_ULS_HOG, KEY_DD_M_ULS_OH, KEY_DD_M_ULS_SAG, KEY_DD_PUNCH_C1, KEY_DD_PUNCH_C2,
    KEY_DD_PUNCH_OK, KEY_DD_PUNCH_U1, KEY_DD_PUNCH_VED, KEY_DD_PUNCH_VED_KN, KEY_DD_SHEAR_OK,
    KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC, KEY_DD_SPACING_MAX, KEY_DD_SPAN, KEY_DD_SPC_BOT,
    KEY_DD_TYRE_LENGTH, KEY_DD_TYRE_WIDTH, KEY_DD_VEHICLE, KEY_DD_VRD_C_MPA, KEY_DD_WDL,
    KEY_DD_WHEEL_LOAD, KEY_DD_WK_BOT, KEY_DD_WK_LIMIT, KEY_DD_WK_OH, KEY_DD_WK_TOP,
    KEY_DO_GAMMA_C_BASIC, KEY_DO_GAMMA_FLT, KEY_DO_GAMMA_M0, KEY_DO_GAMMA_M1, KEY_DO_GAMMA_MF,
    KEY_DO_GAMMA_S, KEY_DO_GAMMA_V, KEY_DS_BOTTOM_CLEAR_COVER, KEY_DS_REINF_MATERIAL,
    KEY_DS_STUD_DIAMETER, KEY_DS_STUD_HEIGHT, KEY_DS_TOP_CLEAR_COVER, KEY_END_DIAPHRAGM,
    KEY_FOOTPATH, KEY_GIRDER, KEY_INCLUDE_MEDIAN, KEY_LL_CUSTOM_VEHICLES, KEY_LL_ECCENTRICITY,
    KEY_LL_FOOTPATH_PRESSURE_MODE, KEY_LL_FOOTPATH_PRESSURE_VALUE, KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED, KEY_LL_IRC_70R_WHEELED, KEY_LL_IRC_AA_TRACKED, KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A, KEY_LL_IRC_CLASS_FATIGUE, KEY_LL_IRC_CLASS_SV, KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_DECK_FCK, KEY_MATERIAL_DECK_FCTM, KEY_MATERIAL_GIRDER_DENSITY,
    KEY_MP_CB_BRACING_SECTION_DESIGNATION, KEY_MP_CB_MEMBER_ID, KEY_MP_CB_SELECT_GIRDERS,
    KEY_MP_CB_SPACING, KEY_MP_CB_TYPE, KEY_MP_ED_BRACING_SECTION_DESIGNATION, KEY_MP_ED_MEMBER_ID,
    KEY_MP_ED_SELECT_GIRDERS, KEY_MP_ED_TYPE, KEY_MP_GD_MEMBER_ID, KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS, KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_MASS, KEY_MP_GIRDER_SYMMETRY,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS, KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
    KEY_MP_GIRDER_TORSIONAL_RESTRAINT, KEY_MP_GIRDER_TYPE, KEY_MP_GIRDER_WARPING_RESTRAINT,
    KEY_MP_GIRDER_WEB_DEPTH, KEY_MP_GIRDER_WEB_THICKNESS, KEY_MP_GIRDER_WEB_TYPE,
    KEY_MP_STIFFENER_BEARING_THICKNESS, KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING, KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_MP_STIFFENER_LONGITUDINAL, KEY_MP_STIFFENER_NO_BEARING_STIFFENERS, KEY_MP_STIFFENER_SPACING,
    KEY_PL_SELF_WEIGHT_FACTOR, KEY_RL_LOAD_VALUE, KEY_RL_TYPE, KEY_SD_BOTTOM_FLANGE_THICKNESS,
    KEY_SD_BOTTOM_FLANGE_WIDTH, KEY_SD_BS_FCD, KEY_SD_BS_FCDW_LC, KEY_SD_BS_FCDW_WB, KEY_SD_BS_FPSD,
    KEY_SD_BS_R, KEY_SD_CLASS_FLANGE, KEY_SD_CLASS_WEB, KEY_SD_COMPOSITE_IZ, KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL, KEY_SD_EFFECTIVE_SLAB_WIDTH, KEY_SD_FLANGE_CLASS_LIMIT,
    KEY_SD_FLANGE_SLENDERNESS, KEY_SD_HIGH_SHEAR, KEY_SD_IS_FQ, KEY_SD_IS_FQD, KEY_SD_IS_IYS_MIN,
    KEY_SD_IS_IYS_PROV, KEY_SD_LTB_CHI, KEY_SD_LTB_LAMBDA, KEY_SD_LTB_MB, KEY_SD_LTB_MCR, KEY_SD_MDV,
    KEY_SD_MD_CAPACITY, KEY_SD_MN_AXIAL, KEY_SD_MN_MOMENT, KEY_SD_MN_RATIO, KEY_SD_MU_APPLIED,
    KEY_SD_PANEL_CD, KEY_SD_PNA_DEPTH, KEY_SD_SC_D_LIMIT, KEY_SD_SC_EDGE_DIST, KEY_SD_SC_Qr_kN,
    KEY_SD_SC_Qu_kN, KEY_SD_SC_REQ_EDGE_DIST, KEY_SD_SC_SL1, KEY_SD_SC_SL2, KEY_SD_SC_SR,
    KEY_SD_SECTION_CLASS, KEY_SD_SECTION_DESIGNATION, KEY_SD_SECTION_PROP_AREA,
    KEY_SD_SECTION_PROP_IZ, KEY_SD_SECTION_PROP_ZUZ, KEY_SD_SECTION_PROP_ZZ, KEY_SD_SHEAR_AV,
    KEY_SD_SHEAR_DIAMETER, KEY_SD_SHEAR_HEIGHT, KEY_SD_SHEAR_KV, KEY_SD_SHEAR_LAMBDA_W,
    KEY_SD_SHEAR_LONGITUDINAL_SPACING, KEY_SD_SHEAR_STUDS_PER_SECTION, KEY_SD_SHEAR_TAU_B,
    KEY_SD_SHEAR_ULTIMATE_STRENGTH, KEY_SD_SHEAR_VCR, KEY_SD_SHEAR_VU, KEY_SD_SHEAR_YIELD_STRENGTH,
    KEY_SD_STIFF_END_COUNT, KEY_SD_STIFF_END_THICK, KEY_SD_STIFF_INT_SPACING, KEY_SD_STIFF_INT_THICK,
    KEY_SD_STIFF_LONG, KEY_SD_STIFF_METHOD, KEY_SD_STRESS_STEEL, KEY_SD_STRESS_STEEL_ALLOWABLE,
    KEY_SD_TOP_FLANGE_THICKNESS, KEY_SD_TOP_FLANGE_WIDTH, KEY_SD_TOTAL_DEPTH, KEY_SD_TS_VL,
    KEY_SD_TS_VRD, KEY_SD_ULS_PER_GIRDER, KEY_SD_WEB_CLASS_LIMIT, KEY_SD_WEB_SLENDERNESS,
    KEY_SD_WEB_THICKNESS, KEY_SKEW_ANGLE, KEY_SL_DAMPING, KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR, KEY_SL_SEISMIC_ZONE, KEY_SL_SOIL_TYPE, KEY_SL_SPECTRAL_COEFF,
    KEY_SL_TIME_PERIOD, KEY_SL_VERTICAL_COEFF, KEY_SL_ZONE_FACTOR, KEY_SPAN, KEY_STRUCTURE_TYPE,
    KEY_TL_HIGHEST_MAX_TEMP, KEY_TL_LOWEST_MIN_TEMP, KEY_TS_DECK_OVERHANG, KEY_TS_DECK_THICKNESS,
    KEY_TS_FOOTPATH_WIDTH, KEY_TS_GIRDER_SPACING, KEY_TS_NO_OF_FOOTPATHS, KEY_TS_NO_OF_GIRDERS,
    KEY_TS_OVERALL_WIDTH, KEY_UTIL_FLEXURE, KEY_UTIL_INTERACTION, KEY_UTIL_LTB, KEY_UTIL_SHEAR,
    KEY_WC_LD_LANE_TABLE_COUNT, KEY_WC_MATERIAL, KEY_WC_THICKNESS, KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED, KEY_WL_HOURLY_MEAN_WIND, KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE, KEY_WL_TERRAIN_TYPE, KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE,
)

N_GIRDERS = 3
SPAN_M = 30.0
SPACING_M = 2.75


# ─────────────────────────────────────────────────────────────────────────────
# input_dict
# ─────────────────────────────────────────────────────────────────────────────
def build_input_dict() -> Dict:
    d: Dict = {
        KEY_STRUCTURE_TYPE: "Composite Steel Plate Girder Bridge",
        KEY_SPAN: str(SPAN_M),
        KEY_CARRIAGEWAY_WIDTH: "7.5",
        KEY_DESIGN_MODE: "Optimized",
        KEY_INCLUDE_MEDIAN: "No",
        KEY_FOOTPATH: "Both Sides",
        KEY_SKEW_ANGLE: "0",
        KEY_GIRDER: "E 250 (Fe 410 W) A",
        KEY_CROSS_BRACING: "E 250 (Fe 410 W) A",
        KEY_END_DIAPHRAGM: "E 250 (Fe 410 W) A",
        KEY_DECK_CONCRETE_GRADE_BASIC: "M40",
        KEY_MATERIAL_DECK_FCK: "40",
        KEY_MATERIAL_DECK_FCTM: "3.0",
        KEY_MATERIAL_GIRDER_DENSITY: "78.5",
        KEY_MATERIAL_DECK_DENSITY: "25.0",
        "latitude": "19.133", "longitude": "72.915",
        "seismic_zone": "III", "wind_speed": "44",
        "shade_temp_max": "40.0", "shade_temp_min": "12.5",
        KEY_TL_HIGHEST_MAX_TEMP: "40.0", KEY_TL_LOWEST_MIN_TEMP: "12.5",
        # typical section
        KEY_TS_OVERALL_WIDTH: "11.0",
        KEY_TS_NO_OF_GIRDERS: str(N_GIRDERS),
        KEY_TS_GIRDER_SPACING: str(SPACING_M),
        KEY_TS_DECK_OVERHANG: "1.25",
        KEY_TS_DECK_THICKNESS: "250.0",
        KEY_TS_FOOTPATH_WIDTH: "1.5",
        KEY_TS_NO_OF_FOOTPATHS: "2",
        KEY_WC_LD_LANE_TABLE_COUNT: "2",
        KEY_CB_TYPE: "IRC 5 - RCC Crash Barrier",
        KEY_CB_LOAD: "9.46",
        KEY_CB_AREA: "378400",
        KEY_RL_TYPE: "IRC 5 - RCC Railing",
        KEY_RL_LOAD_VALUE: "1.50",
        KEY_WC_MATERIAL: "Bituminous",
        KEY_WC_THICKNESS: "65.0",
        KEY_PL_SELF_WEIGHT_FACTOR: "1.00",
        # live loads (Loading tab of Additional Inputs)
        KEY_LL_IRC_CLASS_A: True,
        KEY_LL_IRC_AA_WHEELED: False,
        KEY_LL_IRC_AA_TRACKED: False,
        KEY_LL_IRC_70R_WHEELED: True,
        KEY_LL_IRC_70R_TRACKED: True,
        KEY_LL_IRC_70R_BOGIE: False,
        KEY_LL_IRC_CLASS_SV: True,
        KEY_LL_IRC_CLASS_FATIGUE: True,
        KEY_BL_IRC_CLASS_SV: False,
        KEY_LL_CUSTOM_VEHICLES: [],
        KEY_LL_ECCENTRICITY: "1.2",
        KEY_LL_FOOTPATH_PRESSURE_MODE: "As per IRC 6",
        KEY_LL_FOOTPATH_PRESSURE_VALUE: "",
        # wind
        KEY_WL_BASIC_WIND_SPEED: "44", KEY_WL_AVG_EXPOSED_HEIGHT: "10",
        KEY_WL_TERRAIN_TYPE: "Plain Terrain",
        KEY_WL_HOURLY_MEAN_WIND: "27.80", KEY_WL_HOURLY_WIND_PRESSURE: "463.70",
        KEY_WL_TRANSVERSE_WIND_FORCE: "61.84", KEY_WL_LONGITUDINAL_WIND_FORCE: "15.46",
        KEY_WL_VERTICAL_WIND_FORCE: "117.14",
        # seismic
        KEY_SL_SEISMIC_ZONE: "III", KEY_SL_IMPORTANCE_FACTOR: "1.2",
        KEY_SL_SOIL_TYPE: "Type II – Medium Soil", KEY_SL_TIME_PERIOD: "0.5", KEY_SL_DAMPING: "5",
        KEY_SL_ZONE_FACTOR: "0.16", KEY_SL_SPECTRAL_COEFF: "2.5",
        KEY_SL_HORIZONTAL_COEFF: "0.08", KEY_SL_VERTICAL_COEFF: "0.0533",
        # partial safety factors
        KEY_DO_GAMMA_M0: "1.10", KEY_DO_GAMMA_M1: "1.25", KEY_DO_GAMMA_C_BASIC: "1.50",
        KEY_DO_GAMMA_S: "1.15", KEY_DO_GAMMA_V: "1.25", KEY_DO_GAMMA_FLT: "1.00", KEY_DO_GAMMA_MF: "1.35",
        # deck design options
        KEY_DS_REINF_MATERIAL: "Fe 500", KEY_DS_TOP_CLEAR_COVER: "50", KEY_DS_BOTTOM_CLEAR_COVER: "50",
        KEY_DS_STUD_DIAMETER: "20", KEY_DS_STUD_HEIGHT: "100",
    }
    # girder member properties (per girder keys: BASE.G{i}.M1)
    for i in range(1, N_GIRDERS + 1):
        d[f"{KEY_MP_GD_SELECT_GIRDER}.G{i}"] = f"G{i}"
        d[f"{KEY_MP_GD_MEMBER_ID}.G{i}.M1"] = f"G{i}M1"
        d[f"{KEY_MP_GIRDER_TYPE}.G{i}.M1"] = "Welded Plate Girder"
        d[f"{KEY_MP_GIRDER_SYMMETRY}.G{i}.M1"] = "Mono-symmetric"
        d[f"{KEY_MP_GIRDER_DEPTH}.G{i}.M1"] = "1600"
        d[f"{KEY_MP_GIRDER_WEB_DEPTH}.G{i}.M1"] = "1544"
        d[f"{KEY_MP_GIRDER_WEB_THICKNESS}.G{i}.M1"] = "14"
        d[f"{KEY_MP_GIRDER_TOP_FLANGE_WIDTH}.G{i}.M1"] = "450"
        d[f"{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G{i}.M1"] = "25"
        d[f"{KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH}.G{i}.M1"] = "550"
        d[f"{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G{i}.M1"] = "31"
        d[f"{KEY_MP_GIRDER_MASS}.G{i}.M1"] = "391.5"                 # kg/m
        d[f"{KEY_MP_GIRDER_TORSIONAL_RESTRAINT}.G{i}.M1"] = "Fully Restrained"
        d[f"{KEY_MP_GIRDER_WARPING_RESTRAINT}.G{i}.M1"] = "Both flanges partially restrained"
        d[f"{KEY_MP_GIRDER_WEB_TYPE}.G{i}.M1"] = "Tension field action"
        d[f"{KEY_MP_STIFFENER_INTERMEDIATE}.G{i}.M1"] = "Yes"
        d[f"{KEY_MP_STIFFENER_INTERMEDIATE_SPACING}.G{i}.M1"] = "1500"
        d[f"{KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS}.G{i}.M1"] = "12"
        d[f"{KEY_MP_STIFFENER_LONGITUDINAL}.G{i}.M1"] = "No"
        d[f"{KEY_MP_STIFFENER_NO_BEARING_STIFFENERS}.G{i}.M1"] = "2"
        d[f"{KEY_MP_STIFFENER_SPACING}.G{i}.M1"] = "300"
        d[f"{KEY_MP_STIFFENER_BEARING_THICKNESS}.G{i}.M1"] = "20"
    for i in range(1, N_GIRDERS):
        p = f"G{i}G{i+1}"
        d[f"{KEY_MP_CB_SELECT_GIRDERS}.{p}.B{i}M1"] = f"G{i}-G{i+1}"
        d[f"{KEY_MP_CB_MEMBER_ID}.{p}.B{i}M1"] = f"B{i}M1"
        d[f"{KEY_MP_CB_TYPE}.{p}.B{i}M1"] = "X - Bracing"
        d[f"{KEY_MP_CB_BRACING_SECTION_DESIGNATION}.{p}.B{i}M1"] = "L 100 x 100 x 10"
        d[f"{KEY_MP_CB_SPACING}.{p}.B{i}M1"] = "5.0"
        d[f"{KEY_MP_ED_SELECT_GIRDERS}.{p}.E{i}M1"] = f"G{i}-G{i+1}"
        d[f"{KEY_MP_ED_MEMBER_ID}.{p}.E{i}M1"] = f"E{i}M1"
        d[f"{KEY_MP_ED_TYPE}.{p}.E{i}M1"] = "Cross Bracing"
        d[f"{KEY_MP_ED_BRACING_SECTION_DESIGNATION}.{p}.E{i}M1"] = "L 110 x 110 x 10"
    return d


# ─────────────────────────────────────────────────────────────────────────────
# output_dict
# ─────────────────────────────────────────────────────────────────────────────
def _osdag_member_result(section: str, capacity_kN: float, demand_kN: float,
                         slenderness: float, welded: bool = True) -> dict:
    """Shape of an Osdag member-design dump as read by `_extract_osdag_summary`."""
    r = {
        "section_size.designation": section,
        "Member.tension_capacity": round(capacity_kN, 2),
        "Member.efficiency": round(demand_kN / capacity_kN, 3),
        "Member.Slenderness": round(slenderness, 1),
    }
    if welded:
        r["Weld.Type"] = "Fillet"
    return r


def _pair_designs(diag_c, diag_t, chord_c, chord_t, section_d, section_c, cap_d, cap_c, sl_d, sl_c) -> dict:
    out = {}
    for i in range(1, N_GIRDERS):
        pair = f"G{i}-G{i+1}"
        f = 1.0 if i == 1 else 0.92
        out[pair] = {
            "diagonal": {
                "tension":     _osdag_member_result(section_d, cap_d, diag_t * f, sl_d),
                "compression": _osdag_member_result(section_d, cap_d * 0.78, diag_c * f, sl_d),
            },
            "chord": {
                "tension":     _osdag_member_result(section_c, cap_c, chord_t * f, sl_c),
                "compression": _osdag_member_result(section_c, cap_c * 0.82, chord_c * f, sl_c),
            },
        }
    return out


def _forces_dict(diag_t, diag_c, chord_t, chord_c, spacing_m, diag_len, horiz, alpha) -> dict:
    pairs = {}
    for i in range(1, N_GIRDERS):
        f = 1.0 if i == 1 else 0.92
        pairs[f"G{i}-G{i+1}"] = {
            "diag_tension_kN": round(diag_t * f, 3), "diag_compression_kN": round(diag_c * f, 3),
            "chord_tension_kN": round(chord_t * f, 3), "chord_compression_kN": round(chord_c * f, 3),
            "diag_tension_gov_lc": "ULS-03: 1.35DL + 1.75DW + 1.5LL + 0.9WL",
            "diag_compression_gov_lc": "ULS-03: 1.35DL + 1.75DW + 1.5LL + 0.9WL",
            "chord_tension_gov_lc": "ULS-05: 1.35DL + 1.75DW + 1.5WL",
            "chord_compression_gov_lc": "ULS-05: 1.35DL + 1.75DW + 1.5WL",
        }
    return {
        "brace_type": "X",
        "pairs": pairs,
        "geometry": {"diagonal_length_m": diag_len, "horiz_proj_m": horiz,
                     "alpha_deg": alpha, "cb_spacing_m": spacing_m},
    }


_COMBOS = [
    "ULS-01: 1.35DL + 1.75DW + 1.5LL",
    "ULS-03: 1.35DL + 1.75DW + 1.5LL + 0.9WL",
    "SLS-RARE-01: 1.0DL + 1.2DW + 1.0LL",
    "SLS-FREQUENT-01: 1.0DL + 1.2DW + 0.75LL",
    "ACCIDENTAL 1: 1.0DL + 1.0DW + 0.75LL",
]

# (id, name, clause, demand, capacity, unit) — per-girder checks (designer.CATEGORY_MAP ids)
_GIRDER_CHECKS = [
    (1,  "Bending Resistance",            "IRC 22 Cl. 603.3.1", 10436.0, 12820.0, "kN-m"),
    (2,  "Vertical Shear",                "IS 800 Cl. 8.4",      1545.0,  2470.0, "kN"),
    (3,  "M-V Interaction",               "IRC 22 Cl. 603.3.3.3", 0.74,    1.0,   "-"),
    (5,  "Lateral Torsional Buckling",    "IS 800 Cl. 8.2.2",    2184.0,  3150.0, "kN-m"),
    (6,  "Longitudinal Shear (studs)",    "IRC 22 Cl. 606",       612.0,   790.0, "kN/m"),
    (8,  "Fatigue (normal stress)",       "IRC 22 Cl. 605",        72.4,   101.3, "MPa"),
    (9,  "Fatigue (shear stress)",        "IRC 22 Cl. 605",        31.2,    64.0, "MPa"),
    (11, "SLS Stress Limitation",         "IRC 22 Cl. 604.3.1",   198.5,   225.0, "MPa"),
    (13, "Live Load Deflection",          "IRC 22 Cl. 604.3.2",    28.9,    37.5, "mm"),
    (14, "Total Deflection",              "IRC 22 Cl. 604.3.2",    44.1,    50.0, "mm"),
]


def _girder_checks(scale: float) -> list:
    rows = []
    for cid, name, clause, dem, cap, unit in _GIRDER_CHECKS:
        d = round(dem * scale, 3)
        dcr = round(d / cap, 4)
        rows.append({
            "check_id": cid, "name": name, "clause": clause,
            "demand": d, "capacity": cap, "demand_unit": unit, "capacity_unit": unit,
            "dcr": dcr, "status": "PASS" if dcr < 0.9 else ("WARN" if dcr < 1.0 else "FAIL"),
        })
    return rows


def _per_lc(scale: float) -> dict:
    out = {}
    for j, lc in enumerate(_COMBOS):
        f = scale * (1.0 - 0.07 * j)
        checks = [{"id": c["check_id"], "label": c["name"], "clause": c["clause"],
                   "demand": round(c["demand"] * (1 - 0.07 * j), 3), "capacity": c["capacity"],
                   "dcr": round(c["dcr"] * (1 - 0.07 * j), 4), "status": c["status"], "note": ""}
                  for c in _girder_checks(scale)]
        out[lc] = {"checks": checks, "max_dcr": max(c["dcr"] for c in checks), "overall_status": "PASS"}
    out["Envelope ULS"] = {"checks": [], "max_dcr": 0.0, "overall_status": "PASS"}
    return out


def build_output_dict() -> Dict:
    o: Dict = {}
    # steel design details (flat keys)
    o.update({
        KEY_SD_SECTION_DESIGNATION: "WPG 1600 x 450/25 x 550/31 x 14",
        KEY_SD_TOTAL_DEPTH: "1600", KEY_SD_TOP_FLANGE_WIDTH: "450", KEY_SD_BOTTOM_FLANGE_WIDTH: "550",
        KEY_SD_TOP_FLANGE_THICKNESS: "25", KEY_SD_BOTTOM_FLANGE_THICKNESS: "31", KEY_SD_WEB_THICKNESS: "14",
        KEY_SD_SECTION_PROP_AREA: "498.7", KEY_SD_SECTION_PROP_IZ: "2186450", KEY_SD_SECTION_PROP_ZZ: "25612",
        KEY_SD_SECTION_PROP_ZUZ: "29870", KEY_SD_EFFECTIVE_SLAB_WIDTH: "2750", KEY_SD_COMPOSITE_IZ: "4927300",
        KEY_SD_PNA_DEPTH: "212.4",
        KEY_SD_FLANGE_SLENDERNESS: "8.68", KEY_SD_FLANGE_CLASS_LIMIT: "9.4", KEY_SD_CLASS_FLANGE: "Plastic",
        KEY_SD_WEB_SLENDERNESS: "110.3", KEY_SD_WEB_CLASS_LIMIT: "126", KEY_SD_CLASS_WEB: "Semi-compact",
        KEY_SD_SECTION_CLASS: "Semi-compact",
        KEY_SD_MU_APPLIED: "10436.0", KEY_SD_MD_CAPACITY: "12820.0",
        KEY_UTIL_FLEXURE: "81.4", KEY_UTIL_SHEAR: "62.6", KEY_UTIL_INTERACTION: "74.0", KEY_UTIL_LTB: "69.3",
        KEY_SD_SHEAR_VU: "1545.0", KEY_SD_SHEAR_AV: "21616", KEY_SD_PANEL_CD: "0.97", KEY_SD_SHEAR_KV: "9.59",
        KEY_SD_SHEAR_LAMBDA_W: "1.12", KEY_SD_SHEAR_TAU_B: "114.3", KEY_SD_SHEAR_VCR: "2470.0",
        KEY_SD_HIGH_SHEAR: "No", KEY_SD_MDV: "12820.0",
        KEY_SD_MN_RATIO: None, KEY_SD_MN_AXIAL: None, KEY_SD_MN_MOMENT: None,
        KEY_SD_LTB_MCR: "9840.0", KEY_SD_LTB_LAMBDA: "0.87", KEY_SD_LTB_CHI: "0.71", KEY_SD_LTB_MB: "3150.0",
        KEY_SD_STIFF_METHOD: "Tension field action", KEY_SD_STIFF_INT_THICK: "12", KEY_SD_STIFF_INT_SPACING: "1500",
        KEY_SD_STIFF_END_THICK: "20", KEY_SD_STIFF_END_COUNT: "2", KEY_SD_STIFF_LONG: "Not provided",
        KEY_SD_IS_IYS_MIN: "2.41e6", KEY_SD_IS_IYS_PROV: "5.76e6", KEY_SD_IS_FQ: "318.0", KEY_SD_IS_FQD: "612.0",
        KEY_SD_BS_R: "1610.0", KEY_SD_BS_FCDW_WB: "2180.0", KEY_SD_BS_FCDW_LC: "2605.0",
        KEY_SD_BS_FPSD: "2850.0", KEY_SD_BS_FCD: "2335.0",
        KEY_SD_SHEAR_DIAMETER: "20", KEY_SD_SHEAR_HEIGHT: "100", KEY_SD_SHEAR_YIELD_STRENGTH: "385",
        KEY_SD_SHEAR_ULTIMATE_STRENGTH: "495", KEY_SD_SHEAR_STUDS_PER_SECTION: "2",
        KEY_SD_SHEAR_LONGITUDINAL_SPACING: "250",
        "steeldesign.details.shear.longitudinal_spacing": "250",
        "steeldesign.details.shear.studs_per_section": "2",
        "steeldesign.details.shear.diameter": "20",
        "steeldesign.details.shear.height": "100",
        "member_properties.cross_bracing_details.top_chord": True,
        "member_properties.cross_bracing_details.bottom_chord": True,
    })
    for i in range(1, N_GIRDERS + 1):
        o[f"{KEY_SD_DEFL_LIVE}.G{i}"] = round(28.9 * (1.0 if i == 2 else 0.93), 3)
        o[f"{KEY_SD_DEFL_TOTAL}.G{i}"] = round(44.1 * (1.0 if i == 2 else 0.93), 3)

    # design_results (nested)
    per_girder = {}
    for i in range(1, N_GIRDERS + 1):
        scale = 1.0 if i == 2 else 0.93
        per_girder[f"G{i}"] = {
            "checks": _girder_checks(scale),
            "per_lc": _per_lc(scale),
            "demand": {"governing_combination": _COMBOS[0]},
        }
    fatigue = {f"G{i}": {"demand": round(72.4 * (1.0 if i == 2 else 0.93), 2), "capacity": 101.3,
                         "ur": round(72.4 * (1.0 if i == 2 else 0.93) / 101.3, 3), "status": "PASS"}
               for i in range(1, N_GIRDERS + 1)}
    o["design_results"] = {
        "per_girder": per_girder,
        KEY_SD_ULS_PER_GIRDER: {"fatigue": fatigue},
        KEY_SD_STRESS_STEEL: 198.5, KEY_SD_STRESS_STEEL_ALLOWABLE: 225.0,
        KEY_SD_SC_Qu_kN: 92.6, KEY_SD_SC_Qr_kN: 38.2,
        KEY_SD_SC_SL1: 302.0, KEY_SD_SC_SL2: 410.0, KEY_SD_SC_SR: 275.0,
        "stud_spacing_provided_mm": 250.0, "stud_spacing_max_mm": 600.0,
        KEY_SD_TS_VL: 612.0, KEY_SD_TS_VRD: 790.0, "transverse_shear_ok": True,
        "Ast_required_cm2_per_m": 6.42,
        KEY_SD_SC_D_LIMIT: 50.0, KEY_SD_SC_EDGE_DIST: 60.0, KEY_SD_SC_REQ_EDGE_DIST: 25.0,
    }

    # deck slab
    o["deck_design_results"] = {
        "ur_bot_uls": 0.812, "ur_top_uls": 0.744, "ur_bot_sls_c": 0.61, "ur_bot_sls_s": 0.58,
        "ur_top_sls_c": 0.55, "ur_top_sls_s": 0.52, "ur_bot_crack": 0.77, "ur_top_crack": 0.69,
        "ur_bot_shear": 0.46, "ur_bot_punch": 0.39, "ur_oh_uls": 0.91, "ur_oh_sls_c": 0.63,
        "ur_oh_sls_s": 0.6, "ur_oh_crack": 0.83, "ur_oh_shear": 0.41, "ur_oh_punch": 0.35,
        "ur_composite_trans_shear": 0.775, "ur_composite_crack": 0.77,
        "ur_composite_conc_stress": 0.61, "ur_composite_rebar_stress": 0.58,
        "rebar_bottom_area": 1340.0, "rebar_top_area": 1005.0,
    }
    o["deck_report_values"] = {
        KEY_DD_SPAN: 2.75, KEY_DD_FY: 500, KEY_DD_WDL: 6.25, KEY_DD_WHEEL_LOAD: 114.0,
        KEY_DD_TYRE_WIDTH: 0.5, KEY_DD_TYRE_LENGTH: 250, KEY_DD_IMPACT_FACTOR: 1.207,
        KEY_DD_VEHICLE: "Class 70R (Wheeled)", KEY_DD_GAMMA_DL: 1.35, KEY_DD_GAMMA_LL: 1.5,
        KEY_DD_M_DL: 4.73, KEY_DD_M_LL: 38.6, KEY_DD_M_ULS_SAG: 64.28, KEY_DD_D_BOT: 192.0,
        KEY_DD_MU_BOT: 79.2, KEY_DD_M_ULS_HOG: 55.4, KEY_DD_AS_REQ_TOP: 720, KEY_DD_MU_TOP: 74.5,
        KEY_DD_HAS_OVERHANG: True, KEY_DD_M_BARRIER: 12.4, KEY_DD_M_DL_OH: 6.1, KEY_DD_M_LL_OH: 21.8,
        KEY_DD_M_ULS_OH: 59.5, KEY_DD_MU_OH: 65.4, KEY_DD_PUNCH_VED_KN: 206.4, KEY_DD_PUNCH_C1: 750,
        KEY_DD_PUNCH_C2: 500, KEY_DD_PUNCH_U1: 4913, KEY_DD_PUNCH_VED: 0.219, KEY_DD_VRD_C_MPA: 0.561,
        KEY_DD_PUNCH_OK: True, KEY_DD_AS_MIN: 312, KEY_DD_DIA_BOT: 16, KEY_DD_SPC_BOT: 150,
        KEY_DD_AS_BOT: 1340, KEY_DD_WK_LIMIT: 0.3, KEY_DD_WK_BOT: 0.231, KEY_DD_WK_TOP: 0.207,
        KEY_DD_WK_OH: 0.249, KEY_DD_SHEAR_VED: 98.6, KEY_DD_SHEAR_VRDC: 214.3, KEY_DD_SHEAR_OK: True,
        KEY_DD_AS_REQ_BOT: 1012, KEY_DD_SPACING_MAX: 300, KEY_DD_AS_LONG: 402, KEY_DD_AS_TOP: 1005,
        KEY_DD_MIN_COVER: 40, KEY_DD_COVER_OK: True,
    }

    # cross bracing & end diaphragm
    diag_len = round(math.hypot(SPACING_M / 2.0, 1.45), 4)
    alpha = round(math.degrees(math.atan2(1.45, SPACING_M / 2.0)), 2)
    o["crossbracing_forces_dict"] = _forces_dict(96.4, 101.2, 61.5, 58.3, 5.0, diag_len, SPACING_M / 2.0, alpha)
    o["crossbracing_design_results"] = _pair_designs(101.2, 96.4, 58.3, 61.5, "L 100 x 100 x 10",
                                                     "L 90 x 90 x 8", 374.0, 301.0, 118.4, 96.2)
    o["end_diaphragm_forces_dict"] = _forces_dict(132.8, 139.6, 84.1, 79.2, SPAN_M, diag_len, SPACING_M / 2.0, alpha)
    o["end_diaphragm_design_results"] = _pair_designs(139.6, 132.8, 79.2, 84.1, "L 110 x 110 x 10",
                                                      "L 100 x 100 x 8", 412.0, 333.0, 109.7, 92.5)
    for i in range(1, N_GIRDERS):
        pid = f"G{i}G{i+1}"
        for sec, a_cm2, rv_cm, m_kg_m in (("bracing", 19.03, 1.94, 14.9), ("top_chord", 13.79, 1.76, 10.8),
                                          ("bottom_chord", 13.79, 1.76, 10.8)):
            o[f"transverse_member_design.cb.section_properties.{sec}.{pid}.A"] = a_cm2
            o[f"transverse_member_design.cb.section_properties.{sec}.{pid}.rv"] = rv_cm
            o[f"transverse_member_design.cb.section_properties.{sec}.{pid}.M"] = m_kg_m
        for sec, a_cm2, rv_cm, m_kg_m in (("end_diaphragm", 21.06, 2.14, 16.5), ("top_chord", 15.39, 1.96, 12.1),
                                          ("bottom_chord", 15.39, 1.96, 12.1)):
            o[f"transverse_member_design.ed.section_properties.{sec}.{pid}.A"] = a_cm2
            o[f"transverse_member_design.ed.section_properties.{sec}.{pid}.rv"] = rv_cm
            o[f"transverse_member_design.ed.section_properties.{sec}.{pid}.M"] = m_kg_m

    # analysis summary (Chapter 4)
    lcs = ["DL (self weight)", "SIDL (surfacing)", "Class A - 2 lanes", "Class 70R (Wheeled)",
           "Class 70R (Tracked)", "Class SV", "Wind (WL)", "Temperature (TL)", "Seismic (EQ)",
           "ULS-01", "ULS-03", "SLS-RARE-01", "SLS-FREQUENT-01"]
    bm = [1812.0, 486.0, 2345.0, 3021.0, 2688.0, 3410.0, 212.0, 95.0, 388.0, 10436.0, 9876.0, 7212.0, 6540.0]
    sf = [241.6, 64.8, 338.4, 433.9, 371.2, 489.5, 28.3, 12.7, 51.7, 1545.0, 1462.0, 1083.0, 960.0]
    lc_summary, reactions = {}, {}
    for lc, m, v in zip(lcs, bm, sf):
        lc_summary[lc] = {"max_bm": m, "bm_girder": "G2", "bm_location": 15.0,
                          "max_sf": v, "sf_girder": "G1", "sf_location": 0.0}
        reactions[lc] = {"left_kN": round(v * 0.98, 2), "right_kN": round(v * 0.97, 2)}
    o["analysis_summary"] = {"load_cases": lc_summary, "reactions": reactions}
    o["design_log"] = [
        "[00:00:01] INFO Stage 1 - Inputs validated",
        "[00:00:02] INFO Stage 2 - Initial sizing complete (D = 1600 mm)",
        "[00:00:14] INFO Stage 3 - Grillage analysis complete: 13 load cases",
        "[00:00:16] WARNING Stage 4 - Web is semi-compact; LTB check uses elastic modulus",
        "[00:00:19] INFO Stage 5 - Girder design checks complete: all PASS",
        "[00:00:21] INFO Stage 6 - Deck slab design complete",
        "[00:00:23] INFO Stage 7 - Cross bracing and end diaphragm design complete",
    ]
    return o


# ─────────────────────────────────────────────────────────────────────────────
# Synthetic figures (bytes) so figure embedding is exercised
# ─────────────────────────────────────────────────────────────────────────────
def _png(draw, size=(7, 3.2)) -> bytes:
    import matplotlib
    matplotlib.use("Agg", force=False)
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=size)
    draw(ax)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buf.getvalue()


def _schematic(title):
    def draw(ax):
        ax.set_title(title, fontsize=10)
        ax.plot([0, SPAN_M], [0, 0], color="#2F5D8A", lw=3)
        for g in range(N_GIRDERS):
            ax.plot([0, SPAN_M], [g * SPACING_M, g * SPACING_M], color="#2F5D8A", lw=2)
        for x in range(0, int(SPAN_M) + 1, 5):
            ax.plot([x, x], [0, (N_GIRDERS - 1) * SPACING_M], color="#91B014", lw=1)
        ax.set_aspect("equal")
        ax.axis("off")
    return draw


def _section(title, w=0.9, h=1.6):
    def draw(ax):
        ax.set_title(title, fontsize=10)
        ax.add_patch(__import__("matplotlib.patches", fromlist=["Rectangle"]).Rectangle((-w / 2, h - 0.03), w, 0.03, color="#2F5D8A"))
        ax.add_patch(__import__("matplotlib.patches", fromlist=["Rectangle"]).Rectangle((-0.01, 0.03), 0.02, h - 0.06, color="#2F5D8A"))
        ax.add_patch(__import__("matplotlib.patches", fromlist=["Rectangle"]).Rectangle((-w * 0.6, 0), w * 1.2, 0.03, color="#2F5D8A"))
        ax.set_xlim(-1, 1); ax.set_ylim(-0.1, h + 0.1); ax.set_aspect("equal"); ax.axis("off")
    return draw


def _envelope(title, ylabel, peak, sign=1):
    def draw(ax):
        import numpy as np
        x = np.linspace(0, SPAN_M, 200)
        y = sign * peak * 4 * x * (SPAN_M - x) / SPAN_M ** 2
        ax.fill_between(x, 0, y, color="#2F5D8A", alpha=0.25)
        ax.plot(x, y, color="#2F5D8A")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xlabel("Distance from left support (m)"); ax.set_ylabel(ylabel); ax.set_title(title, fontsize=10)
        ax.grid(alpha=0.3)
    return draw


def build_figure_data() -> Dict[str, bytes]:
    import matplotlib.patches  # noqa: F401 (ensures submodule import for _section)
    figs = {
        "girder_top": _png(_schematic("Plan — girder layout")),
        "cross_section": _png(_schematic("Typical cross-section (schematic)"), (7, 2.4)),
        "final_geometry": _png(_schematic("3D superstructure (schematic)")),
        "girder_3d": _png(_schematic("Plate girders — 3D view (schematic)")),
        "section_preview": _png(_section("Plate girder cross-section"), (3.5, 4)),
        "stiffener_preview": _png(_schematic("Girder side view with stiffeners")),
        "cb_diagram": _png(_schematic("Cross bracing layout"), (7, 2.5)),
        "cb_bracing": _png(_section("Bracing section L 100 x 100 x 10", 0.5, 0.5), (3, 3)),
        "cb_top_chord": _png(_section("Top chord L 90 x 90 x 8", 0.5, 0.5), (3, 3)),
        "cb_bottom_chord": _png(_section("Bottom chord L 90 x 90 x 8", 0.5, 0.5), (3, 3)),
        "ed_diagram": _png(_schematic("End diaphragm layout"), (7, 2.5)),
        "ed_bracing": _png(_section("ED bracing L 110 x 110 x 10", 0.5, 0.5), (3, 3)),
        "ed_top_chord": _png(_section("ED top chord L 100 x 100 x 8", 0.5, 0.5), (3, 3)),
        "ed_bottom_chord": _png(_section("ED bottom chord L 100 x 100 x 8", 0.5, 0.5), (3, 3)),
        "bm_envelope": _png(_envelope("Bending moment envelope (ULS)", "BM (kN-m)", 10436)),
        "sf_envelope": _png(_envelope("Shear force envelope (ULS)", "SF (kN)", 1545, -1)),
        "defl_ll": _png(_envelope("Vertical deflection (1.0 LL)", "Dy (mm)", 28.9, -1)),
    }
    return figs
