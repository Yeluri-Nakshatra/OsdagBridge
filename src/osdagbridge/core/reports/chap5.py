# =============================================================================
# Chapter 5: Design Checks
# Presentation only — values come from `bridge` (ReportDataBridge) and the
# engine's output_dict.  Every table is a `LongTable` (repeating headers,
# grouped rows kept together); styling from `styles` via `latex_builders`.
# =============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from osdagbridge.core.utils.common import (
    KEY_DD_AS_BOT, KEY_DD_AS_LONG, KEY_DD_AS_MIN, KEY_DD_AS_REQ_BOT, KEY_DD_AS_REQ_TOP, KEY_DD_AS_TOP,
    KEY_DD_COVER_OK, KEY_DD_DIA_BOT, KEY_DD_D_BOT, KEY_DD_FY, KEY_DD_GAMMA_DL, KEY_DD_GAMMA_LL,
    KEY_DD_HAS_OVERHANG, KEY_DD_IMPACT_FACTOR, KEY_DD_MIN_COVER, KEY_DD_MU_BOT, KEY_DD_MU_OH, KEY_DD_MU_TOP,
    KEY_DD_M_BARRIER, KEY_DD_M_DL, KEY_DD_M_DL_OH, KEY_DD_M_LL, KEY_DD_M_LL_OH, KEY_DD_M_ULS_HOG,
    KEY_DD_M_ULS_OH, KEY_DD_M_ULS_SAG, KEY_DD_PUNCH_C1, KEY_DD_PUNCH_C2, KEY_DD_PUNCH_OK, KEY_DD_PUNCH_U1,
    KEY_DD_PUNCH_VED, KEY_DD_PUNCH_VED_KN, KEY_DD_SHEAR_OK, KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC,
    KEY_DD_SPACING_MAX, KEY_DD_SPAN, KEY_DD_SPC_BOT, KEY_DD_TYRE_LENGTH, KEY_DD_TYRE_WIDTH, KEY_DD_VEHICLE,
    KEY_DD_VRD_C_MPA, KEY_DD_WDL, KEY_DD_WHEEL_LOAD, KEY_DD_WK_BOT, KEY_DD_WK_LIMIT, KEY_DD_WK_OH, KEY_DD_WK_TOP,
    KEY_DECK_CONCRETE_GRADE_BASIC, KEY_DESIGN_MODE, KEY_DS_BOTTOM_CLEAR_COVER, KEY_DS_REINF_MATERIAL,
    KEY_DS_STUD_DIAMETER, KEY_DS_TOP_CLEAR_COVER, KEY_MATERIAL_DECK_FCK, KEY_MATERIAL_DECK_FCTM, KEY_MP_ED_TYPE,
    KEY_SD_BOTTOM_FLANGE_THICKNESS, KEY_SD_BOTTOM_FLANGE_WIDTH, KEY_SD_BS_FCD, KEY_SD_BS_FCDW_LC,
    KEY_SD_BS_FCDW_WB, KEY_SD_BS_FPSD, KEY_SD_BS_R, KEY_SD_CLASS_FLANGE, KEY_SD_CLASS_WEB, KEY_SD_COMPOSITE_IZ,
    KEY_SD_DEFL_LIVE, KEY_SD_DEFL_TOTAL, KEY_SD_EFFECTIVE_SLAB_WIDTH, KEY_SD_FLANGE_CLASS_LIMIT,
    KEY_SD_FLANGE_SLENDERNESS, KEY_SD_HIGH_SHEAR, KEY_SD_IS_FQ, KEY_SD_IS_FQD, KEY_SD_IS_IYS_MIN,
    KEY_SD_IS_IYS_PROV, KEY_SD_LTB_CHI, KEY_SD_LTB_LAMBDA, KEY_SD_LTB_MB, KEY_SD_LTB_MCR, KEY_SD_MDV,
    KEY_SD_MD_CAPACITY, KEY_SD_MN_AXIAL, KEY_SD_MN_MOMENT, KEY_SD_MN_RATIO, KEY_SD_MU_APPLIED, KEY_SD_PANEL_CD,
    KEY_SD_PNA_DEPTH, KEY_SD_SC_D_LIMIT, KEY_SD_SC_EDGE_DIST, KEY_SD_SC_Qr_kN, KEY_SD_SC_Qu_kN,
    KEY_SD_SC_REQ_EDGE_DIST, KEY_SD_SC_SL1, KEY_SD_SC_SL2, KEY_SD_SC_SR, KEY_SD_SECTION_CLASS,
    KEY_SD_SECTION_PROP_AREA, KEY_SD_SECTION_PROP_IZ, KEY_SD_SECTION_PROP_ZUZ, KEY_SD_SECTION_PROP_ZZ,
    KEY_SD_SHEAR_AV, KEY_SD_SHEAR_KV, KEY_SD_SHEAR_LAMBDA_W, KEY_SD_SHEAR_TAU_B, KEY_SD_SHEAR_VCR,
    KEY_SD_SHEAR_VU, KEY_SD_STIFF_END_COUNT, KEY_SD_STIFF_END_THICK, KEY_SD_STIFF_INT_SPACING,
    KEY_SD_STIFF_INT_THICK, KEY_SD_STIFF_LONG, KEY_SD_STIFF_METHOD, KEY_SD_STRESS_STEEL,
    KEY_SD_STRESS_STEEL_ALLOWABLE, KEY_SD_TOP_FLANGE_THICKNESS, KEY_SD_TOP_FLANGE_WIDTH, KEY_SD_TOTAL_DEPTH,
    KEY_SD_TS_VL, KEY_SD_TS_VRD, KEY_SD_ULS_PER_GIRDER, KEY_SD_WEB_CLASS_LIMIT, KEY_SD_WEB_SLENDERNESS,
    KEY_SD_WEB_THICKNESS, KEY_SPAN, KEY_TS_DECK_OVERHANG, KEY_TS_DECK_THICKNESS, KEY_TS_NO_OF_GIRDERS,
    KEY_UTIL_FLEXURE, KEY_UTIL_INTERACTION, KEY_UTIL_LTB, KEY_UTIL_SHEAR,
)

from osdagbridge.core.reports.report_utils import _tex, _render_value, get_girder_entries
from .latex_builders import (Column, KeyValueTable, LongTable, figure_block, status_cell,
                             status_from_text, table_note, ur_cell)
from .styles import THEME

if TYPE_CHECKING:
    from .report_generator import ReportDataBridge

_NA = "---"


def _dfmt(v, nd=2):
    try:
        return f"{float(v):.{nd}f}"
    except (TypeError, ValueError):
        return ""


def _unit(v, nd, unit):
    s = _dfmt(v, nd)
    return (s + unit) if s else ""


def _ge_status(provided, required):
    try:
        return status_cell(float(provided) >= float(required))
    except (TypeError, ValueError):
        return _NA


def _le_status(actual, allowable):
    try:
        return status_cell(float(actual) <= float(allowable))
    except (TypeError, ValueError):
        return _NA


def _band_status(ratio):
    """Engine bands: PASS < 0.90, WARN < 1.00, FAIL >= 1.00."""
    try:
        r = float(ratio)
    except (TypeError, ValueError):
        return _NA
    if r < 0.90:
        return status_cell(True)
    if r < 1.00:
        return status_cell(True, warn=True)
    return status_cell(False)


# Shared column layouts (cm) — all derived from THEME.page.text_width_cm = 16.0
_COLS_5 = lambda h: [Column(1.8, "c", h[0]), Column(4.4, "l", h[1]), Column(3.2, "c", h[2]),   # noqa: E731
                     Column(3.0, "c", h[3]), Column(1.6, "c", h[4])]
_COLS_CHECK = lambda h: [Column(2.0, "c", h[0]), Column(3.6, "l", h[1]), Column(3.0, "c", h[2]),   # noqa: E731
                         Column(3.6, "c", h[3]), Column(1.6, "c", h[4])]


# ═══════════════════════════════════════════════════════════════════════════════
# 5.1 Plate girder design
# ═══════════════════════════════════════════════════════════════════════════════
def _girder_section(bridge, girder_entries) -> str:
    od = bridge.output_dict
    rv = lambda key, unit="": _render_value(od, key, unit)   # noqa: E731
    out = []

    # Table: section properties (per girder group of 13 rows)
    t = LongTable([Column(2.2, "c", "Girder"), Column(7.6, "l", "Property"), Column(4.6, "c", "Value")],
                  caption="Girder Section Properties (Final Optimized / User-selected)", label="tab:girder-section-props")
    props = [
        ("Depth, $D$ (mm)", KEY_SD_TOTAL_DEPTH), ("Top Flange Width, $b_{tf}$ (mm)", KEY_SD_TOP_FLANGE_WIDTH),
        ("Bottom Flange Width, $b_{bf}$ (mm)", KEY_SD_BOTTOM_FLANGE_WIDTH),
        ("Top Flange Thickness, $t_{tf}$ (mm)", KEY_SD_TOP_FLANGE_THICKNESS),
        ("Bottom Flange Thickness, $t_{bf}$ (mm)", KEY_SD_BOTTOM_FLANGE_THICKNESS),
        ("Web Thickness, $t_w$ (mm)", KEY_SD_WEB_THICKNESS), ("Gross Area, $A$ (cm$^2$)", KEY_SD_SECTION_PROP_AREA),
        ("Moment of Inertia, $I_z$ (cm$^4$)", KEY_SD_SECTION_PROP_IZ),
        ("Elastic Section Modulus, $Z_{ez}$ (cm$^3$)", KEY_SD_SECTION_PROP_ZZ),
        ("Plastic Section Modulus, $Z_{pz}$ (cm$^3$)", KEY_SD_SECTION_PROP_ZUZ),
        ("Effective Slab Width, $b_{eff}$ (mm)", KEY_SD_EFFECTIVE_SLAB_WIDTH),
        ("Transformed Composite $I_z$ (cm$^4$)", KEY_SD_COMPOSITE_IZ),
        ("Depth to Plastic Neutral Axis (mm)", KEY_SD_PNA_DEPTH),
    ]
    for lbl, _ in girder_entries:
        t.add_group(_tex(lbl), [[name, rv(key)] for name, key in props])
    out.append(t.render())

    # Table: classification
    t = LongTable([Column(2.0, "c", "Girder"), Column(2.8, "l", "Element"), Column(3.2, "c", "Slenderness Ratio"),
                   Column(2.4, "c", "Class Limit"), Column(3.6, "c", "Classification")],
                  caption="Girder Section Classification", label="tab:girder-classification", note="IS 800:2007 Table 2.")
    for lbl, _ in girder_entries:
        t.add_group(_tex(lbl), [
            ["Top Flange", rv(KEY_SD_FLANGE_SLENDERNESS), rv(KEY_SD_FLANGE_CLASS_LIMIT), rv(KEY_SD_CLASS_FLANGE)],
            ["Web", rv(KEY_SD_WEB_SLENDERNESS), rv(KEY_SD_WEB_CLASS_LIMIT), rv(KEY_SD_CLASS_WEB)],
            ["Overall Section", _NA, _NA, rv(KEY_SD_SECTION_CLASS)],
        ])
    out.append(t.render())

    # Table: moment capacity
    def _pct_ur(key):
        try:
            u = float(od.get(key)) / 100.0
            return f"{u:.2f}", u
        except (TypeError, ValueError):
            return "", None
    flex_s, flex_u = _pct_ur(KEY_UTIL_FLEXURE)
    t = LongTable(_COLS_5(["Girder", "Parameter", "Formula / Reference", "Value", "Status"]),
                  caption="Moment Capacity Check", label="tab:moment-capacity",
                  note="IRC 22 Cl. 603.3.1, IS 800 Cl. 8.2.1.")
    for lbl, _ in girder_entries:
        t.add_group(_tex(lbl), [
            ["Applied Moment, $M_u$", "Governing LC (ULS)", rv(KEY_SD_MU_APPLIED, " kN-m"), _NA],
            ["Design Moment Capacity, $M_d$", "IRC 22 Cl. 603.3.1", rv(KEY_SD_MD_CAPACITY, " kN-m"), _NA],
            ["Utilization Ratio, $M_u / M_d$", "$M_u / M_d$", ur_cell(flex_u) if flex_u is not None else "",
             status_cell(flex_u <= 1.0) if flex_u is not None else _NA],
        ])
    out.append(t.render())

    # Table: shear capacity
    shear_s, shear_u = _pct_ur(KEY_UTIL_SHEAR)
    t = LongTable(_COLS_5(["Girder", "Parameter", "Formula / Reference", "Value", "Status"]),
                  caption="Shear Capacity Check", label="tab:shear-capacity",
                  note="IS 800 Cl. 8.4, IRC 22 Cl. 603.3.3.2.")
    for lbl, _ in girder_entries:
        t.add_group(_tex(lbl), [
            ["Applied Shear, $V_u$", "Governing LC (ULS)", rv(KEY_SD_SHEAR_VU, " kN"), _NA],
            ["Shear Area, $A_v$", r"$d_w \times t_w$", rv(KEY_SD_SHEAR_AV, " mm$^2$"), _NA],
            ["Panel Aspect Ratio, $c/d$", _NA, rv(KEY_SD_PANEL_CD), _NA],
            ["Shear Buckling Coefficient, $k_v$", "IS 800 Cl. 8.4.2.2", rv(KEY_SD_SHEAR_KV), _NA],
            [r"Web Slenderness, $\lambda_w$", r"$\sqrt{f_{yw}/(\sqrt{3}\,\tau_{cr})}$", rv(KEY_SD_SHEAR_LAMBDA_W), _NA],
            [r"Design Shear Stress, $\tau_b$", "IRC 22 Cl. 603.3.3.2", rv(KEY_SD_SHEAR_TAU_B, " MPa"), _NA],
            ["Shear Buckling Resistance, $V_{cr}$", r"$A_v \times \tau_b$", rv(KEY_SD_SHEAR_VCR, " kN"), _NA],
            ["Utilization Ratio, $V_u / V_d$", "$V_u / V_d$", ur_cell(shear_u) if shear_u is not None else "",
             status_cell(shear_u <= 1.0) if shear_u is not None else _NA],
        ])
    out.append(t.render())

    # Table: interaction
    mv_s, mv_u = _pct_ur(KEY_UTIL_INTERACTION)
    _mn_r, _mn_ax, _mn_mo = od.get(KEY_SD_MN_RATIO), od.get(KEY_SD_MN_AXIAL), od.get(KEY_SD_MN_MOMENT)
    if _mn_r is None or _mn_ax is None or _mn_mo is None:
        mn_cond = mn_val = "N/A"
        mn_status = "N/A"
    else:
        mn_cond = f"{float(_mn_ax):.2f} + {float(_mn_mo):.2f} = {float(_mn_r):.3f}"
        mn_val = f"{float(_mn_r):.3f}"
        mn_status = _band_status(_mn_r)
    t = LongTable(_COLS_5(["Girder", "Check", "Condition", "Value", "Status"]),
                  caption="Interaction Checks (M-V and M-N)", label="tab:interaction", note="IRC 22 Cl. 603.3.3.3.")
    for lbl, _ in girder_entries:
        t.add_group(_tex(lbl), [
            ["High Shear Condition?", r"$V_u > 0.6\,V_d$", rv(KEY_SD_HIGH_SHEAR), _NA],
            ["Reduced Moment Capacity, $M_{dv}$", "IRC 22 Cl. 603.3.3.3", rv(KEY_SD_MDV, " kN-m"), _NA],
            [r"Interaction: $M_u \leq M_{dv}$", _NA, ur_cell(mv_u) if mv_u is not None else "",
             _band_status(mv_u) if mv_u is not None else _NA],
            [r"Interaction: $N_u/N_{Rd} + M_u/M_{dv} \leq 1.0$", mn_cond, mn_val, mn_status],
        ])
    out.append(t.render())

    # Table: LTB
    ltb_s, ltb_u = _pct_ur(KEY_UTIL_LTB)
    t = LongTable(_COLS_5(["Girder", "Parameter", "Formula / Reference", "Value", "Status"]),
                  caption="Lateral Torsional Buckling Check --- Construction Stage", label="tab:ltb",
                  note="IRC 22 Cl. 603.3.3.1, IS 800 Cl. 8.2.2.")
    for lbl, _ in girder_entries:
        t.add_group(_tex(lbl), [
            ["Elastic Critical Moment, $M_{cr}$", "IRC 22 Cl. 603.3.3.1", rv(KEY_SD_LTB_MCR, " kN-m"), _NA],
            [r"Non-dim. Slenderness, $\bar{\lambda}_{LT}$", r"$\sqrt{M_p / M_{cr}}$", rv(KEY_SD_LTB_LAMBDA), _NA],
            [r"LTB Reduction Factor, $\chi_{LT}$", "IS 800 Cl. 8.2.2", rv(KEY_SD_LTB_CHI), _NA],
            ["LTB Resistance, $M_b$", r"$\chi_{LT}\,M_p / \gamma_{m0}$", rv(KEY_SD_LTB_MB, " kN-m"), _NA],
            [r"$M_u \leq M_b$", "$M_u / M_b$", ur_cell(ltb_u) if ltb_u is not None else "",
             _band_status(ltb_u) if ltb_u is not None else _NA],
        ])
    out.append(t.render())

    # Table: stiffener summary
    t = LongTable([Column(2.2, "c", "Girder"), Column(6.4, "l", "Item"), Column(5.8, "l", "Value")],
                  caption="Stiffener Design Summary", label="tab:stiffener-summary")
    for lbl, _ in girder_entries:
        t.add_group(_tex(lbl), [
            ["Shear Buckling Design Method", rv(KEY_SD_STIFF_METHOD)],
            ["Intermediate Stiffener Thickness", rv(KEY_SD_STIFF_INT_THICK, " mm")],
            ["Intermediate Stiffener Spacing", rv(KEY_SD_STIFF_INT_SPACING, " mm")],
            ["End Panel Stiffener Thickness", rv(KEY_SD_STIFF_END_THICK, " mm")],
            ["No. of End Panel Stiffeners", rv(KEY_SD_STIFF_END_COUNT)],
            ["Longitudinal Stiffeners", rv(KEY_SD_STIFF_LONG)],
        ])
    out.append(t.render())

    # Table: intermediate stiffener checks (Custom mode only — verification table)
    is_custom = str(bridge.input_dict.get(KEY_DESIGN_MODE, "Optimized")).strip().lower() in {"custom", "customized"}
    if is_custom:
        t = LongTable(_COLS_CHECK(["Girder", "Check", "Required", "Provided", "Status"]),
                      caption="Intermediate Stiffener Checks", label="tab:int-stiffener", note="IS 800 Cl. 8.7.1.2.")
        for lbl, _ in girder_entries:
            t.add_group(_tex(lbl), [
                ["Min. Moment of Inertia, $I_s$", rv(KEY_SD_IS_IYS_MIN, " mm$^4$"), rv(KEY_SD_IS_IYS_PROV, " mm$^4$"),
                 _ge_status(od.get(KEY_SD_IS_IYS_PROV), od.get(KEY_SD_IS_IYS_MIN))],
                [r"Buckling Resistance, $F_{qd} \geq F_q$", rv(KEY_SD_IS_FQ, " kN"), rv(KEY_SD_IS_FQD, " kN"),
                 _ge_status(od.get(KEY_SD_IS_FQD), od.get(KEY_SD_IS_FQ))],
            ])
        out.append(t.render())

    # Table: bearing (end panel) stiffener checks
    _bs_r = od.get(KEY_SD_BS_R)

    def _bs_check(resist_key):
        prov = od.get(resist_key)
        try:
            if prov is None or float(prov) <= 0.0 or _bs_r is None:
                return ("N/A", "N/A", "N/A")
            return (f"{_bs_r} kN", f"{prov} kN", status_cell(float(prov) >= float(_bs_r)))
        except (TypeError, ValueError):
            return ("N/A", "N/A", "N/A")

    t = LongTable(_COLS_CHECK(["Girder", "Check", "Required", "Provided", "Status"]),
                  caption="End Panel (Bearing) Stiffener Checks", label="tab:bearing-stiffener", note="IS 800 Cl. 8.7.3.")
    for lbl, _ in girder_entries:
        t.add_group(_tex(lbl), [
            ["Web Buckling Resistance", *_bs_check(KEY_SD_BS_FCDW_WB)],
            ["Local Crushing Resistance", *_bs_check(KEY_SD_BS_FCDW_LC)],
            ["Bearing Capacity", *_bs_check(KEY_SD_BS_FPSD)],
            ["Column Buckling Resistance", *_bs_check(KEY_SD_BS_FCD)],
        ])
    out.append(t.render())

    # Table: deflection (per girder)
    try:
        _span_m = float(bridge.input_dict.get(KEY_SPAN))
        _allow_live, _allow_total = _span_m * 1000.0 / 800.0, _span_m * 1000.0 / 600.0
    except (TypeError, ValueError):
        _allow_live = _allow_total = None
    t = LongTable(_COLS_CHECK(["Girder", "Check", "Allowable", "Actual", "Status"]),
                  caption="Serviceability --- Deflection Checks", label="tab:deflection", note="IRC 22 Cl. 604.3.2.")
    for gi, (lbl, _) in enumerate(girder_entries, start=1):
        live = od.get(f"{KEY_SD_DEFL_LIVE}.G{gi}")
        total = od.get(f"{KEY_SD_DEFL_TOTAL}.G{gi}")
        t.add_group(_tex(lbl), [
            [r"Live Load Deflection, $\delta_{LL}$", f"$L/800$ = {_allow_live:.1f} mm" if _allow_live else "",
             _unit(live, 3, " mm"), _le_status(live, _allow_live)],
            [r"Total Load Deflection, $\delta_{total}$", f"$L/600$ = {_allow_total:.1f} mm" if _allow_total else "",
             _unit(total, 3, " mm"), _le_status(total, _allow_total)],
        ])
    out.append(t.render())

    # Table: SLS stress limitation
    dr = od.get("design_results", {}) or {}
    sig, alw = dr.get(KEY_SD_STRESS_STEEL), dr.get(KEY_SD_STRESS_STEEL_ALLOWABLE)
    t = LongTable(_COLS_CHECK(["Girder", "Element", "Allowable Stress", "Actual Stress", "Status"]),
                  caption="Serviceability --- Maximum Stress Limitation", label="tab:sls-stress", note="IRC 22 Cl. 604.3.1.")
    for lbl, _ in girder_entries:
        t.add_row([_tex(lbl), r"Structural Steel ($0.9\,f_y$)", _unit(alw, 2, " MPa"), _unit(sig, 2, " MPa"),
                   _le_status(sig, alw)])
    out.append(t.render())

    # Table: fatigue (governing of normal / shear)
    fat = ((dr.get(KEY_SD_ULS_PER_GIRDER, {}) or {}).get("fatigue", {}) or {})
    t = LongTable(_COLS_CHECK(["Girder", r"Stress Range, $\Delta\sigma$", "Fatigue Limit, $f_{fd}$", "Utilization Ratio", "Status"]),
                  caption="Serviceability --- Fatigue Assessment", label="tab:fatigue",
                  note=r"IRC 22 Cl. 605 --- governing of normal and shear fatigue (worst by DCR). "
                       r"Capacity reduction factor $\mu_r$ applied where plate thickness $>$ 25 mm.")
    for gi, (lbl, _) in enumerate(girder_entries, start=1):
        g = fat.get(f"G{gi}", {}) or {}
        t.add_row([_tex(lbl), _unit(g.get("demand"), 2, " MPa"), _unit(g.get("capacity"), 2, " MPa"),
                   ur_cell(g.get("ur")) if g.get("ur") is not None else "", status_from_text(g.get("status"))])
    out.append(t.render())

    # Table: girder design summary (controlling check per girder)
    pg = dr.get("per_girder", {}) or {}
    t = LongTable([Column(1.5, "c", "Girder"), Column(3.6, "l", "Controlling LC / Combination"),
                   Column(2.8, "l", "Controlling Check"), Column(1.8, "c", "Demand"), Column(1.8, "c", "Capacity"),
                   Column(1.1, "c", "UR"), Column(1.4, "c", "Status")],
                  caption="Girder Design Summary (DCR / Utilization Ratio)", label="tab:girder-summary", size="compact",
                  note="UR = Demand / Capacity. The controlling check is the criterion with the highest UR for each girder, "
                       "with the real load case/combination that drives it.")
    for gi, (lbl, _) in enumerate(girder_entries, start=1):
        g_data = pg.get(f"G{gi}", {}) or {}
        checks = g_data.get("checks") or []
        if not checks:
            t.add_row([_tex(lbl), "", "", "", "", "", ""])
            continue
        ctrl = max(checks, key=lambda c: c.get("dcr") or 0.0)
        ctrl_lc, best = None, None
        for lc_name, lc_data in (g_data.get("per_lc") or {}).items():
            if str(lc_name).lower().startswith("envelope"):
                continue
            for chk in lc_data.get("checks") or []:
                if chk.get("id") == ctrl.get("check_id"):
                    d = chk.get("dcr") or 0.0
                    if best is None or d > best:
                        best, ctrl_lc = d, lc_name
        if ctrl_lc is None:
            ctrl_lc = (g_data.get("demand") or {}).get("governing_combination") or ""

        def _wu(value, unit):
            s = _dfmt(value, 2)
            return (s + " " + unit) if (s and unit and str(unit) not in ("-", "–")) else s
        t.add_row([_tex(lbl), _tex(ctrl_lc), _tex(ctrl.get("name", "")), _wu(ctrl.get("demand"), ctrl.get("demand_unit")),
                   _wu(ctrl.get("capacity"), ctrl.get("capacity_unit")), ur_cell(ctrl.get("dcr"), 3),
                   status_from_text(ctrl.get("status"))])
    out.append(t.render())

    # Shear connectors
    t = LongTable([Column(3.4, "l", "Parameter"), Column(5.4, "c", "Formula"), Column(2.4, "c", "Value"),
                   Column(3.2, "l", "Reference")], caption="Shear Connector Capacity", label="tab:sc-capacity")
    t.add_row(["Design Resistance, $Q_u$",
               r"\footnotesize $Q_u=\min(Q_{u,s},\,Q_{u,c})$; $Q_{u,s}=\dfrac{0.8\,f_u\,(\pi d^2/4)}{\gamma_v}$; "
               r"$Q_{u,c}=\dfrac{0.29\,\alpha\,d^2\sqrt{f_{ck}\,E_{cm}}}{\gamma_v}$",
               _unit(dr.get(KEY_SD_SC_Qu_kN), 2, " kN"), "IRC 22 Cl. 606.3.1 (Eq. 6.1)"])
    t.add_row(["Fatigue Shear Resistance, $Q_r$", r"IRC 22 Table 8 ($\phi d$, $N_{sc}$)",
               _unit(dr.get(KEY_SD_SC_Qr_kN), 2, " kN"), "IRC 22 Cl. 606.3.2 (Table 8)"])
    out.append(t.render())

    sc_prov = dr.get("stud_spacing_provided_mm")
    t = LongTable([Column(3.4, "l", "Criterion"), Column(4.0, "c", "Governing Spacing"),
                   Column(4.0, "c", "Actual Spacing Provided"), Column(2.0, "c", "Status")],
                  caption="Shear Connector Spacing", label="tab:sc-spacing",
                  note=r"IRC 22 Cl. 606.4, 606.9. Governing spacing $= \min(S_{L1}, S_{L2}, S_R)$.")
    for crit, req in (("ULS Shear ($S_{L1}$)", dr.get(KEY_SD_SC_SL1)), ("Full Composite ($S_{L2}$)", dr.get(KEY_SD_SC_SL2)),
                      ("SLS Fatigue ($S_R$)", dr.get(KEY_SD_SC_SR)), ("Max Spacing Limit (IRC 22)", dr.get("stud_spacing_max_mm"))):
        t.add_row([crit, _unit(req, 1, " mm"), _unit(sc_prov, 1, " mm"), _le_status(sc_prov, req)])
    out.append(t.render())

    ts_vl, ts_vrd = dr.get(KEY_SD_TS_VL), dr.get(KEY_SD_TS_VRD)
    try:
        ts_ur = f"{float(ts_vl) / float(ts_vrd):.2f}" if float(ts_vrd) > 0 else _NA
    except (TypeError, ValueError, ZeroDivisionError):
        ts_ur = _NA
    ts_ok = dr.get("transverse_shear_ok")
    dd = od.get("deck_design_results", {}) or {}
    try:
        ast_prov = (float(dd.get("rebar_bottom_area") or 0) + float(dd.get("rebar_top_area") or 0)) / 100.0
    except (TypeError, ValueError):
        ast_prov = None
    ast_req = dr.get("Ast_required_cm2_per_m")
    stud_d, d_lim = bridge.input_dict.get(KEY_DS_STUD_DIAMETER), dr.get(KEY_SD_SC_D_LIMIT)
    edge, edge_req = dr.get(KEY_SD_SC_EDGE_DIST), dr.get(KEY_SD_SC_REQ_EDGE_DIST)
    t = LongTable([Column(5.0, "l", "Check"), Column(7.2, "l", "Value"), Column(2.0, "c", "Status")],
                  caption="Transverse Shear and Detailing Checks", label="tab:transverse-shear", note="IRC 22 Cl. 606.6, 606.10.")
    t.add_row(["Longitudinal Shear per unit length, $V_L$", _unit(ts_vl, 2, " kN/m"), _NA])
    t.add_row(["Transverse Shear Capacity of Slab, $V_{Rd}$", _unit(ts_vrd, 2, " kN/m"), _NA])
    t.add_row(["Transverse Shear Check", "$V_L/V_{Rd}$ = " + ts_ur,
               status_cell(bool(ts_ok)) if ts_ok is not None else _NA])
    t.add_row(["Min. Transverse Reinforcement, $A_{st,min}$",
               "Required " + _unit(ast_req, 2, r" cm$^2$/m") + ", Provided " + _unit(ast_prov, 2, r" cm$^2$/m"),
               _le_status(ast_req, ast_prov)])
    t.add_row([r"Stud Diameter $\leq 2\,t_f$", "$d$ = " + _unit(stud_d, 1, " mm") + r" $\leq 2t_f$ = " + _unit(d_lim, 1, " mm"),
               _le_status(stud_d, d_lim)])
    t.add_row(["Stud Edge Distance", "Provided " + _unit(edge, 1, " mm") + r" (req. $\geq$ " + _unit(edge_req, 1, " mm") + ")",
               _le_status(edge_req, edge)])
    out.append(t.render())
    return "\n".join(out)


# ═══════════════════════════════════════════════════════════════════════════════
# 5.2 Deck slab design
# ═══════════════════════════════════════════════════════════════════════════════
def _deck_section(bridge) -> str:
    deck_rpt = bridge.output_dict.get("deck_report_values", {}) or {}
    inp = bridge.input_dict
    has = bool(deck_rpt)
    oh = bool(deck_rpt.get(KEY_DD_HAS_OVERHANG))
    PH = r"\placeholder{---}"

    def v(key, default=0.0):
        try:
            x = deck_rpt.get(key)
            return default if x in (None, "") else float(x)
        except (TypeError, ValueError):
            return default

    def f(key, nd=2, scale=1.0, unit=""):
        if not has:
            return PH
        x = deck_rpt.get(key)
        if x in (None, ""):
            return PH
        try:
            return f"{float(x) * scale:.{nd}f}{unit}"
        except (TypeError, ValueError):
            return _tex(x)

    def s(ok):
        return status_cell(bool(ok)) if has else _NA

    def foh(key, nd=2, scale=1.0, unit=""):
        if not has:
            return PH
        return f(key, nd, scale, unit) if oh else "N/A"

    rv = lambda key, unit="": _render_value(inp, key, unit)   # noqa: E731
    out = []

    t = KeyValueTable(caption="Deck Slab --- Loading and Geometry", label="tab:deck-loading")
    t.add("Effective Span of Deck Slab, $l_{eff}$", f(KEY_DD_SPAN, 0, 1000.0, " mm") + " (girder spacing, c/c)")
    t.add("Deck Thickness, $t_s$", rv(KEY_TS_DECK_THICKNESS, " mm"))
    t.add("Clear Cover (IRC 112 Cl. 15.2)", "Top " + rv(KEY_DS_TOP_CLEAR_COVER) + " / Bottom " + rv(KEY_DS_BOTTOM_CLEAR_COVER) + " mm")
    t.add("Concrete Grade (IRC 112 Cl. 6.4)", rv(KEY_DECK_CONCRETE_GRADE_BASIC) + " ($f_{ck}$ = " + rv(KEY_MATERIAL_DECK_FCK)
          + " MPa, $f_{ctm}$ = " + rv(KEY_MATERIAL_DECK_FCTM) + " MPa)")
    t.add("Reinforcement Grade (IRC 112 Cl. 6.2)", rv(KEY_DS_REINF_MATERIAL) + " ($f_y$ = " + f(KEY_DD_FY, 0) + " MPa)")
    t.add("Dead Load per Unit Area, $w_{DL}$", f(KEY_DD_WDL, 2, 1.0, r" kN/m\textsuperscript{2}") + " (slab self-weight)")
    t.add("IRC 6 Wheel Load (Class A / 70R)", f(KEY_DD_WHEEL_LOAD, 1, 1.0, " kN"))
    t.add("Tyre Contact Width (IRC 6 Annex A)", f(KEY_DD_TYRE_WIDTH, 0, 1000.0, " mm") + " (transverse)")
    t.add("Impact Factor (IRC 6 Cl. 208.2)", f(KEY_DD_IMPACT_FACTOR, 3))
    t.add("Governing Live Load Case", f(KEY_DD_VEHICLE))
    out.append(t.render())

    t = LongTable([Column(2.6, "c", "Location"), Column(3.6, "l", "Parameter"), Column(3.2, "l", "Formula / Reference"),
                   Column(3.0, "c", "Value"), Column(1.6, "c", "Status")],
                  caption="Deck Slab --- Flexure Check: Interior Panel (Pigeaud's Method)", label="tab:deck-flexure",
                  note=r"IRC 112 Cl. 12.2. Distribution (longitudinal) reinforcement designed for 20\% of main steel moment (IRC 21 Cl. 305.18).")
    gdl, gll = f(KEY_DD_GAMMA_DL, 2), f(KEY_DD_GAMMA_LL, 2)
    t.add_group(r"At Midspan (Sagging)", [
        ["Transverse BM (DL), $M_{T,DL}$", r"$w_{DL}\,l_{eff}^2/10$", f(KEY_DD_M_DL, 2, 1.0, " kN-m/m"), _NA],
        ["Transverse BM (LL), $M_{T,LL}$", "Effective width (IRC 112 B3.1)", f(KEY_DD_M_LL, 2, 1.0, " kN-m/m"), _NA],
        ["Total Design BM, $M_{u,sag}$", gdl + " DL + " + gll + " LL", f(KEY_DD_M_ULS_SAG, 2, 1.0, " kN-m/m"), _NA],
        ["Effective depth, $d$", r"$t_s - c_{nom} - \phi/2$", f(KEY_DD_D_BOT, 1, 1.0, " mm"), _NA],
        ["Moment Capacity, $M_{Rd}$", "IRC 112 Cl. 12.2", f(KEY_DD_MU_BOT, 2, 1.0, " kN-m/m"), s(v(KEY_DD_MU_BOT) >= v(KEY_DD_M_ULS_SAG))],
    ])
    t.add_group(r"At Support (Hogging)", [
        ["Total Design BM, $M_{u,hog}$", gdl + " DL + " + gll + " LL (at support)", f(KEY_DD_M_ULS_HOG, 2, 1.0, " kN-m/m"), _NA],
        ["Required Top Steel, $A_{st,top}$", r"$M_u / (0.87\,f_y\,d)$", f(KEY_DD_AS_REQ_TOP, 0, 1.0, r" mm\textsuperscript{2}/m"), _NA],
        ["Moment Capacity, $M_{Rd}$", "IRC 112 Cl. 12.2", f(KEY_DD_MU_TOP, 2, 1.0, " kN-m/m"), s(v(KEY_DD_MU_TOP) >= v(KEY_DD_M_ULS_HOG))],
    ])
    out.append(t.render())

    cols4 = lambda h: [Column(5.0, "l", h[0]), Column(3.4, "c", h[1]), Column(4.2, "c", h[2]), Column(1.8, "c", h[3])]   # noqa: E731
    t = LongTable(cols4(["Parameter", "Formula", "Value", "Status"]),
                  caption="Deck Slab --- Cantilever Overhang Flexure Check", label="tab:deck-overhang",
                  note="IRC 6 Cl. 206.4 crash barrier loads applied at kerb face; IRC 112 Cl. 12.2 flexure.")
    t.add_row(["Overhang Length, $l_{oh}$", _NA, rv(KEY_TS_DECK_OVERHANG, " m"), _NA])
    t.add_row(["Crash Barrier Load Moment", "IRC 6 Cl. 206.4", foh(KEY_DD_M_BARRIER, 2, 1.0, " kN-m/m"), _NA])
    t.add_row(["Dead Load Moment", r"$w_{DL}\,l_{oh}^2/2$ + railing", foh(KEY_DD_M_DL_OH, 2, 1.0, " kN-m/m"), _NA])
    t.add_row(["Live Load Moment (eccentric wheel)", r"Wheel load $\times$ arm", foh(KEY_DD_M_LL_OH, 2, 1.0, " kN-m/m"), _NA])
    t.add_row(["Total Hogging Moment, $M_{u,oh}$", gdl + " DL + " + gll + " (LL + CB)", foh(KEY_DD_M_ULS_OH, 2, 1.0, " kN-m/m"), _NA])
    t.add_row(["Moment Capacity (top steel), $M_{Rd,oh}$", "IRC 112 Cl. 12.2", foh(KEY_DD_MU_OH, 2, 1.0, " kN-m/m"),
               (s(v(KEY_DD_MU_OH) >= v(KEY_DD_M_ULS_OH)) if oh else ("N/A" if has else _NA))])
    out.append(t.render())

    t = LongTable(cols4(["Parameter", "Formula / Reference", "Value", "Status"]),
                  caption="Deck Slab --- Punching Shear Check (IRC 112 Cl. 10.4.6)", label="tab:deck-punching",
                  note="Punching shear reinforcement not typically required for deck slabs with $d \\geq 200$ mm and adequate longitudinal reinforcement.")
    t.add_row(["Design Wheel Load (ULS), $V_{Ed}$", r"$\gamma_Q\,(1+IF)\,P_w$", f(KEY_DD_PUNCH_VED_KN, 1, 1.0, " kN"), _NA])
    t.add_row(["Tyre Contact Area", r"$a \times b$ (IRC 6 Annex A)", f(KEY_DD_TYRE_WIDTH, 0, 1000.0) + r" $\times$ " + f(KEY_DD_TYRE_LENGTH, 0) + " mm", _NA])
    t.add_row(["Loaded Area at mid-depth, $b_0$", r"$c_1 \times c_2$ (incl.\ WC dispersion)", f(KEY_DD_PUNCH_C1, 0) + r" $\times$ " + f(KEY_DD_PUNCH_C2, 0) + " mm", _NA])
    t.add_row(["Control Perimeter, $u_1$", r"$2(c_1+c_2) + 4\pi d$", f(KEY_DD_PUNCH_U1, 0, 1.0, " mm"), _NA])
    t.add_row(["Punching Shear Stress, $v_{Ed}$", r"$V_{Ed} / (u_1\,d)$", f(KEY_DD_PUNCH_VED, 3, 1.0, " MPa"), _NA])
    t.add_row(["Punching Resistance, $v_{Rd,c}$", r"IRC 112 Eq.\ 10.1", f(KEY_DD_VRD_C_MPA, 3, 1.0, " MPa"), _NA])
    t.add_row(["Punching Shear Check", r"$v_{Ed} \leq v_{Rd,c}$",
               (ur_cell(v(KEY_DD_PUNCH_VED) / v(KEY_DD_VRD_C_MPA)) if (has and v(KEY_DD_VRD_C_MPA) > 0) else PH),
               s(deck_rpt.get(KEY_DD_PUNCH_OK))])
    out.append(t.render())

    wks = [v(KEY_DD_WK_BOT), v(KEY_DD_WK_TOP)] + ([v(KEY_DD_WK_OH)] if oh else [])
    gov_wk = max(wks)
    t = KeyValueTable(caption="Crack Width Check (Deck Slab)", label="tab:deck-crack", wide_param=True,
                      param_header="Parameter", value_header="Value / Reference")
    t.add("Min. Reinforcement for Crack Control, $A_{s,min}$", f(KEY_DD_AS_MIN, 0, 1.0, r" mm\textsuperscript{2}/m") + " [IRC 112 Cl. 16.5.1]")
    t.add("Provided Reinforcement (bottom)", r"$\phi$" + f(KEY_DD_DIA_BOT, 0) + " @ " + f(KEY_DD_SPC_BOT, 0) + " mm c/c ("
          + f(KEY_DD_AS_BOT, 0, 1.0, r" mm\textsuperscript{2}/m") + ")")
    t.add("Max. Permissible Crack Width", f(KEY_DD_WK_LIMIT, 2, 1.0, " mm"))
    t.add("Calculated Crack Width, $w_k$ (governing)", (f"{gov_wk:.4f} mm" if has else PH))
    t.add("Crack Width Check", s(has and gov_wk <= v(KEY_DD_WK_LIMIT)))
    out.append(t.render())

    d_bot = v(KEY_DD_D_BOT)
    t = LongTable(cols4(["Parameter", "Formula / Reference", "Value", "Status"]),
                  caption="One-Way (Beam) Shear Check (Deck Slab)", label="tab:deck-shear",
                  note="IRC 112 Cl. 10.3.2. Shear reinforcement not provided in deck slabs; capacity relies on concrete and main reinforcement.")
    t.add_row(["Design Shear per unit width, $V_{Ed}$", r"$\gamma_{DL} V_{DL} + \gamma_{LL}(1{+}IF)V_{LL}$", f(KEY_DD_SHEAR_VED, 2, 1.0, " kN/m"), _NA])
    t.add_row(["Effective depth, $d$", r"$t_s - c_{nom} - \phi/2$", f(KEY_DD_D_BOT, 1, 1.0, " mm"), _NA])
    t.add_row(["Size factor, $k$", r"$1 + \sqrt{200/d} \leq 2.0$", (f"{min(1.0 + (200.0 / d_bot) ** 0.5, 2.0):.3f}" if (has and d_bot > 0) else PH), _NA])
    t.add_row([r"Long.\ reinforcement ratio, $\rho_l$", r"$A_{sl}/(b_w\,d) \leq 0.02$",
               (f"{min(v(KEY_DD_AS_BOT) / (1000.0 * d_bot), 0.02):.4f}" if (has and d_bot > 0) else PH), _NA])
    t.add_row(["Shear resistance (no stirrups), $V_{Rd,c}$", r"$v_{Rd,c}\,b_w\,d$ (Cl.\ 10.3.2)", f(KEY_DD_SHEAR_VRDC, 2, 1.0, " kN/m"), _NA])
    t.add_row(["One-Way Shear Check", r"$V_{Ed} \leq V_{Rd,c}$",
               (ur_cell(v(KEY_DD_SHEAR_VED) / v(KEY_DD_SHEAR_VRDC)) if (has and v(KEY_DD_SHEAR_VRDC) > 0) else PH),
               s(deck_rpt.get(KEY_DD_SHEAR_OK))])
    out.append(t.render())

    mm2 = r" mm\textsuperscript{2}/m"
    t = LongTable([Column(5.0, "l", "Parameter"), Column(3.8, "c", "Required / Limit"), Column(3.8, "c", "Provided"), Column(1.8, "c", "Status")],
                  caption="Reinforcement Detailing Summary (Deck Slab)", label="tab:deck-detailing",
                  note="IRC 112 Cl. 16.3, IS 456 Cl. 26.5.")
    t.add_section_row("Main Reinforcement --- Bottom (Transverse)")
    t.add_row(["Required Area, $A_{st,req}$", f(KEY_DD_AS_REQ_BOT, 0, 1.0, mm2), f(KEY_DD_AS_BOT, 0, 1.0, mm2), s(v(KEY_DD_AS_BOT) >= v(KEY_DD_AS_REQ_BOT))])
    t.add_row([r"Bar Diameter $\times$ Spacing", r"$\phi \geq 10$ mm (IRC 112)", r"$\phi$" + f(KEY_DD_DIA_BOT, 0) + " @ " + f(KEY_DD_SPC_BOT, 0) + " mm c/c", _NA])
    t.add_row([r"Min.\ Reinforcement $A_{s,min}$ (IRC 112 Cl. 16.3.1)", f(KEY_DD_AS_MIN, 0, 1.0, mm2), f(KEY_DD_AS_BOT, 0, 1.0, mm2), s(v(KEY_DD_AS_BOT) >= v(KEY_DD_AS_MIN))])
    t.add_row([r"Max.\ Bar Spacing (IRC 112 Cl. 16.3.2)", f(KEY_DD_SPACING_MAX, 0, 1.0, " mm"), f(KEY_DD_SPC_BOT, 0, 1.0, " mm"), s(0.0 < v(KEY_DD_SPC_BOT) <= v(KEY_DD_SPACING_MAX))])
    t.add_section_row("Distribution Reinforcement --- Longitudinal")
    t.add_row(["Required Area, $A_{st,dist}$", r"$\geq 20\%$ of main steel", f(KEY_DD_AS_LONG, 0, 1.0, mm2),
               s(v(KEY_DD_AS_LONG) >= max(0.20 * v(KEY_DD_AS_BOT), v(KEY_DD_AS_MIN)))])
    t.add_section_row("Top Reinforcement (Support / Cantilever Overhang)")
    t.add_row(["Required Area, $A_{st,top}$", f(KEY_DD_AS_REQ_TOP, 0, 1.0, mm2), f(KEY_DD_AS_TOP, 0, 1.0, mm2), s(v(KEY_DD_AS_TOP) >= v(KEY_DD_AS_REQ_TOP))])
    t.add_section_row("Cover and Detailing")
    t.add_row(["Clear Cover (IRC 112 Cl. 15.2)", r"$\geq$ " + f(KEY_DD_MIN_COVER, 0) + " mm (Table 14.2)",
               "Top " + rv(KEY_DS_TOP_CLEAR_COVER) + " / Bottom " + rv(KEY_DS_BOTTOM_CLEAR_COVER) + " mm", s(deck_rpt.get(KEY_DD_COVER_OK))])
    out.append(t.render())
    return "\n".join(out)


# ═══════════════════════════════════════════════════════════════════════════════
# 5.3 / 5.4 Cross bracing & end diaphragm (shared renderer)
# ═══════════════════════════════════════════════════════════════════════════════
def _member_tables(bridge, kind: str, title: str, label_pfx: str) -> str:
    pairs = bridge.get_cb_pairs(kind)
    out = []

    t = LongTable([Column(1.7, "c", "Panel"), Column(2.2, "l", "Member"), Column(2.3, "l", "Connection"),
                   Column(2.9, "c", "Section"), Column(2.2, "c", r"$A_g$ (mm\textsuperscript{2})"), Column(2.2, "c", "$r_{min}$ (mm)")],
                  caption=f"{title} --- Connection and Section Properties", label=f"tab:{label_pfx}-props",
                  note="$A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration.")
    for pair in pairs:
        rows = []
        for member, mlabel in (("diagonal", "Diagonal"), ("chord", "Top / Bottom chord")):
            _, ftype = bridge.get_cb_governing_force(pair, member, kind)
            a = bridge.get_cb_section_property(pair, member, "A", kind)
            rv_ = bridge.get_cb_section_property(pair, member, "rv", kind)
            rows.append([mlabel, bridge.get_cb_connection(pair, member, ftype, kind), bridge.get_cb_section(pair, member, ftype, kind),
                         f"{float(a) * 100:.1f}" if a is not None else "", f"{float(rv_) * 10:.1f}" if rv_ is not None else ""])
        t.add_group(_tex(pair), rows)
    out.append(t.render())

    def _sl_status(slnd, limit):
        try:
            return status_cell(float(slnd) <= limit)
        except (TypeError, ValueError):
            return _NA

    t = LongTable([Column(1.8, "c", "Panel"), Column(2.2, "l", "Member"), Column(1.6, "c", "Nature"),
                   Column(2.6, "c", r"Eff.\ Length $KL$ (mm)"), Column(2.0, "c", "$KL/r$"), Column(3.4, "c", "Limit / Status")],
                  caption=f"{title} --- Slenderness Ratio Check (IS 800 Cl. 3.8)", label=f"tab:{label_pfx}-slenderness",
                  note="Limit = 250 for compression members, 400 for tension members. $K = 1.0$ for members with both ends pinned.")
    top_on = bridge.output_dict.get("member_properties.cross_bracing_details.top_chord", True)
    bot_on = bridge.output_dict.get("member_properties.cross_bracing_details.bottom_chord", True)
    for pair in pairs:
        kl_d, sl_d = bridge.get_cb_effective_length("diagonal", kind), bridge.get_cb_slenderness(pair, "diagonal", kind)
        kl_c, sl_c = bridge.get_cb_effective_length("chord", kind), bridge.get_cb_slenderness(pair, "chord", kind)
        rows = [["Diagonal", "C", kl_d, sl_d, "250 --- " + _sl_status(sl_d, 250)]]
        if top_on:
            rows.append(["Top chord", "C", kl_c, sl_c, "250 --- " + _sl_status(sl_c, 250)])
        if bot_on:
            rows.append(["Bottom chord", "T", kl_c, sl_c, "400 --- " + _sl_status(sl_c, 400)])
        t.add_group(_tex(pair), rows)
    out.append(t.render())

    t = LongTable([Column(1.5, "c", "Panel"), Column(1.7, "l", "Member"), Column(2.3, "c", "Section"), Column(2.7, "l", "Governing LC"),
                   Column(1.6, "c", "Demand (kN)"), Column(1.6, "c", "Capacity (kN)"), Column(1.0, "c", "UR"), Column(1.4, "c", "Status")],
                  caption=f"{title} Design --- Capacity Summary", label=f"tab:{label_pfx}-capacity", size="compact",
                  note="Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension) using the Osdag member-design module.")
    for pair in pairs:
        rows = []
        for member, mlabel in (("diagonal", "Diagonal"), ("chord", "Chord")):
            force, ftype = bridge.get_cb_governing_force(pair, member, kind)
            rows.append([mlabel, bridge.get_cb_section(pair, member, ftype, kind), bridge.get_cb_gov_lc(pair, member, ftype, kind),
                         force, bridge.get_cb_capacity(pair, member, ftype, kind),
                         ur_cell(bridge.get_cb_efficiency(pair, member, ftype, kind), 3) if bridge.get_cb_efficiency(pair, member, ftype, kind) else "",
                         bridge.get_cb_status(pair, member, ftype, kind) or _NA])
        t.add_group(_tex(pair), rows)
    out.append(t.render())
    return "\n".join(out)


# ═══════════════════════════════════════════════════════════════════════════════
# 5.5 Overall design check summary
# ═══════════════════════════════════════════════════════════════════════════════
def _overall_summary(bridge, charts: Optional[dict], components) -> str:
    charts = charts or {}
    od = bridge.output_dict
    pg = (od.get("design_results", {}) or {}).get("per_girder", {}) or {}
    deck_rpt = od.get("deck_report_values", {}) or {}
    has_deck = bool(deck_rpt)
    oh = bool(deck_rpt.get(KEY_DD_HAS_OVERHANG))

    def dkv(key):
        try:
            x = deck_rpt.get(key)
            return 0.0 if x in (None, "") else float(x)
        except (TypeError, ValueError):
            return 0.0

    def _vu(v, unit):
        s = _dfmt(v, 2)
        u = (unit or "").strip()
        return (s + " " + u) if (s and u) else s

    def _gov_lc(g, ids):
        best = None
        for lc, ld in ((pg.get(g) or {}).get("per_lc") or {}).items():
            if str(lc).lower().startswith("envelope"):
                continue
            for chk in ld.get("checks") or []:
                if chk.get("id") in ids:
                    d = chk.get("dcr") or 0.0
                    if best is None or d > best[0]:
                        best = (d, lc)
        return _tex(str(best[1]).strip()) if best else _NA

    def dcr_row(ids, fallback_unit=""):
        best = None
        for g, gd in pg.items():
            if str(g).startswith("EB"):
                continue
            for chk in gd.get("checks") or []:
                if chk.get("check_id") in ids:
                    d = chk.get("dcr") or 0.0
                    if best is None or d > best[0]:
                        best = (d, chk.get("demand"), chk.get("capacity"), chk.get("demand_unit") or "", chk.get("capacity_unit") or "", g)
        if best is not None:
            d, dem, cap, du, cu, g = best
            return (_gov_lc(g, ids), _vu(dem, du) or _NA, _vu(cap, cu) or _NA, ur_cell(d))
        best = None
        for g, gd in pg.items():
            if str(g).startswith("EB"):
                continue
            for lc, ld in (gd.get("per_lc") or {}).items():
                if str(lc).lower().startswith("envelope"):
                    continue
                for chk in ld.get("checks") or []:
                    if chk.get("id") in ids:
                        d = chk.get("dcr") or 0.0
                        if best is None or d > best[0]:
                            best = (d, chk.get("demand"), chk.get("capacity"), lc)
        if best is None:
            return (_NA, _NA, _NA, _NA)
        d, dem, cap, lc = best
        return (_tex(str(lc).strip()), _vu(dem, fallback_unit) or _NA, _vu(cap, fallback_unit) or _NA, ur_cell(d))

    def member_row(kind, force_type):
        best = None
        for pair in bridge.get_cb_pairs(kind):
            for member in ("diagonal", "chord"):
                cap = bridge.get_cb_capacity(pair, member, force_type, kind)
                eff = bridge.get_cb_efficiency(pair, member, force_type, kind)
                try:
                    ur = float(eff)
                except (TypeError, ValueError):
                    continue
                if best is None or ur > best[0]:
                    best = (ur, pair, member, cap)
        if best is None:
            return (_NA, _NA, _NA, _NA)
        ur, pair, member, cap = best
        gov = bridge.get_cb_gov_lc(pair, member, force_type, kind) or _NA
        dem = f"{float(cap) * ur:.2f} kN" if cap else _NA
        return (gov, dem, (cap + " kN") if cap else _NA, ur_cell(ur))

    def slender_row(kind):
        best = None
        for pair in bridge.get_cb_pairs(kind):
            for member in ("diagonal", "chord"):
                try:
                    sf = float(bridge.get_cb_slenderness(pair, member, kind))
                except (TypeError, ValueError):
                    continue
                lim = 400.0 if member == "chord" else 250.0
                ratio = sf / lim
                if best is None or ratio > best[0]:
                    best = (ratio, sf, lim)
        if best is None:
            return (_NA, _NA, _NA, _NA)
        ratio, sf, lim = best
        return (_NA, f"{sf:.1f}", f"{lim:.0f}", ur_cell(ratio))

    deck_combo = (r"Basic ULS: " + _tex(f"{dkv(KEY_DD_GAMMA_DL):g}DL + {dkv(KEY_DD_GAMMA_LL):g}LL")) if has_deck else _NA

    def deck_row(dem_key, cap_key, unit, is_oh=False):
        if not has_deck:
            return (_NA, _NA, _NA, _NA)
        if is_oh and not oh:
            return (deck_combo, "N/A", "N/A", "N/A")
        dem, cap = dkv(dem_key), dkv(cap_key)
        return (deck_combo, f"{dem:.2f} {unit}", f"{cap:.2f} {unit}", ur_cell(dem / cap) if cap > 0 else _NA)

    def gov_sls_frequent():
        best = None
        for g, gd in pg.items():
            if str(g).startswith("EB"):
                continue
            for lc, ld in (gd.get("per_lc") or {}).items():
                if "frequent" not in str(lc).lower():
                    continue
                d = ld.get("max_dcr") or 0.0
                if best is None or d > best[0]:
                    best = (d, lc)
        return _tex(str(best[1]).strip()) if best else "Frequent SLS"

    wks = [dkv(KEY_DD_WK_BOT), dkv(KEY_DD_WK_TOP)] + ([dkv(KEY_DD_WK_OH)] if oh else [])
    gov_wk, wk_lim = max(wks), dkv(KEY_DD_WK_LIMIT)
    crack = ((gov_sls_frequent() if has_deck else _NA), (f"{gov_wk:.3f} mm" if has_deck else _NA),
             (f"{wk_lim:.3f} mm" if has_deck else _NA), (ur_cell(gov_wk / wk_lim) if (has_deck and wk_lim > 0) else _NA))

    ed_type = ""
    for k, v in bridge.input_dict.items():
        if str(k).startswith(KEY_MP_ED_TYPE) and v:
            ed_type = str(v)
            break
    ed_is_cb = "brac" in ed_type.strip().lower() or bool(bridge.get_cb_pairs("ed"))

    t = LongTable([Column(3.4, "l", "Member / Check"), Column(4.6, "l", "Governing Load Combo"),
                   Column(2.4, "c", "Demand"), Column(2.4, "c", "Capacity"), Column(1.2, "c", "UR")],
                  caption="Overall Design Check Summary --- All Members", label="tab:overall-summary",
                  note=r"UR = Demand / Capacity. All values $\leq 1.0$ indicate passing checks; failing ratios are shown in red. "
                       r"The governing check for each component is detailed in the individual design check sections above.")
    t.add_section_row("Steel Plate Girders")
    t.add_row(["Girder --- Moment", *dcr_row({1})])
    t.add_row(["Girder --- Shear", *dcr_row({2})])
    t.add_row(["Girder --- LTB (construction)", *dcr_row({5})])
    t.add_row(["Girder --- Deflection", *dcr_row({13, 14}, "mm")])
    t.add_row(["Girder --- Stress", *dcr_row({11}, "MPa")])
    t.add_row(["Girder --- Fatigue", *dcr_row({8, 9}, "MPa")])
    t.add_section_row("Concrete Deck Slab")
    ts_row = dcr_row({16})
    if ts_row[3] == _NA:
        # Transverse shear is a bridge-level check stored in design_results
        _dr = od.get("design_results", {}) or {}
        try:
            _vl, _vrd = float(_dr.get(KEY_SD_TS_VL)), float(_dr.get(KEY_SD_TS_VRD))
            ts_row = ("Envelope ULS", f"{_vl:.2f} kN/m", f"{_vrd:.2f} kN/m", ur_cell(_vl / _vrd) if _vrd > 0 else _NA)
        except (TypeError, ValueError):
            pass
    t.add_row(["Transverse Shear (slab)", *ts_row])
    t.add_row(["Crack Width (slab)", *crack])
    t.add_row(["Deck --- Flexure (sagging)", *deck_row(KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT, "kN-m/m")])
    t.add_row(["Deck --- Flexure (hogging)", *deck_row(KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP, "kN-m/m")])
    t.add_row(["Deck --- Cantilever Overhang", *deck_row(KEY_DD_M_ULS_OH, KEY_DD_MU_OH, "kN-m/m", is_oh=True)])
    t.add_row(["Deck --- Punching Shear", *deck_row(KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA, "MPa")])
    t.add_row(["Deck --- One-Way Shear", *deck_row(KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC, "kN/m")])
    t.add_section_row("Cross Bracing")
    t.add_row(["Cross Bracing --- Compression", *member_row("cb", "compression")])
    t.add_row(["Cross Bracing --- Tension", *member_row("cb", "tension")])
    t.add_row(["Cross Bracing --- Slenderness", *slender_row("cb")])
    t.add_section_row("End Diaphragms")
    if ed_is_cb:
        t.add_row(["End Diaphragm --- Compression", *member_row("ed", "compression")])
        t.add_row(["End Diaphragm --- Tension", *member_row("ed", "tension")])
        t.add_row(["End Diaphragm --- Slenderness", *slender_row("ed")])
    else:
        t.add_message_row("End Diaphragm --- Moment", "Rolled / Welded section --- design to be added")
        t.add_message_row("End Diaphragm --- Shear", "Rolled / Welded section --- design to be added")

    # Governing UR per component (same data as the charts)
    comp_tbl = ""
    if components:
        c = LongTable([Column(3.6, "l", "Component"), Column(4.0, "l", "Governing Check"), Column(2.0, "c", "Max UR"),
                       Column(1.6, "c", "Status"), Column(2.4, "c", "Checks Plotted")],
                      caption="Governing Utilization Ratio per Primary Element", label="tab:governing-ur")
        for comp in components:
            g = comp.governing_item
            c.add_row([comp.name, _tex(g.label) if g else _tex(comp.note or _NA),
                       ur_cell(comp.max_ur) if comp.max_ur is not None else _NA,
                       status_from_text(comp.status), str(len([i for i in comp.items if i.ur is not None]))])
        comp_tbl = c.render()

    figs = []
    if charts.get("ur_overview"):
        figs.append(figure_block(charts["ur_overview"],
                                 "Governing utilization ratio (demand / capacity) of each primary element; the red dashed line marks $UR = 1.0$",
                                 width=r"0.72\textwidth", label="fig:ur-overview"))
    if charts.get("ur_detail"):
        figs.append(figure_block(charts["ur_detail"],
                                 "Utilization ratio of every design check, grouped by component (plate girders, deck slab, cross bracing, end diaphragms); bars above the red dashed $UR = 1.0$ line indicate failing checks",
                                 width=THEME.figure.chart_width, label="fig:ur-detail"))
    if not figs:
        figs.append(table_note("Utilization-ratio charts are not available because no design-check results were found."))

    return r"""
\section{Overall Design Check Summary}
\label{sec:overall-summary}

The utilization ratio $UR = \text{Demand} / \text{Capacity}$ of every design check is summarised below. Checks with $UR \leq 1.0$ pass; $UR > 1.0$ fails. The charts are generated automatically from the same results as the tables.

""" + "\n".join(figs) + "\n" + comp_tbl + "\n" + t.render()


# ═══════════════════════════════════════════════════════════════════════════════
# Chapter entry point
# ═══════════════════════════════════════════════════════════════════════════════
def ch5_design_checks(checks_data, bridge, charts: Optional[dict] = None, components=None) -> str:
    """Chapter 5 — Design Checks.

    Parameters
    ----------
    checks_data : dict
        Raw checks payload (unused; data is sourced from bridge).
    bridge : ReportDataBridge
    charts : dict | None
        {'ur_overview': path, 'ur_detail': path} produced by `charts.py`.
    components : list[ComponentUR] | None
        Utilisation data from `summary_data.collect_utilization`.
    """
    girder_entries = get_girder_entries(bridge.input_dict)
    if not girder_entries:
        try:
            n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        except (TypeError, ValueError):
            n = 1
        girder_entries = [(f"Girder {i}", "M1") for i in range(1, n + 1)]

    if components is None:
        from .summary_data import collect_utilization
        components = collect_utilization(bridge.output_dict, bridge.input_dict)

    return r"""
\chapter{Design Checks}

This section presents all structural design checks performed by OsdagBridge. For each member, the demand from the governing load combination, the code-based capacity, and the utilization ratio are tabulated. All checks reference IS 800:2007 and IRC 22:2014 unless stated otherwise.

\section{Plate Girder Design}
\label{sec:plate-girder}

""" + _girder_section(bridge, girder_entries) + r"""

\section{Deck Slab Design}
\label{sec:deck-design}

The reinforced concrete deck slab is designed per IRC~112:2011 (flexure, shear, crack width) and IRC~22:2014 (composite construction). Wheel loads are distributed using Pigeaud's method. The deck is checked for flexure in the transverse and longitudinal directions, punching shear, one-way (beam) shear, crack width, and reinforcement detailing.

""" + _deck_section(bridge) + r"""

\section{Cross Bracing Design}
\label{sec:cross-bracing}

Cross bracing between adjacent plate girders provides lateral stability during construction, resists transverse loads (wind, seismic, braking) in service, and prevents lateral torsional buckling of the girders. Members are designed per IS~800:2007 Cl.~7 (compression) and Cl.~6 (tension). Forces are derived from the grillage model under the governing load combination (DL + LL + WL).

""" + _member_tables(bridge, "cb", "Cross Bracing", "cb") + r"""

\section{End Diaphragm Design}
\label{sec:end-diaphragm}

End diaphragms at the supports transfer transverse loads to the bearings, restrain the bottom flanges against lateral displacement, and maintain the girder cross-section geometry during construction and in service. They are designed per IS~800:2007 and IRC~24:2010 Cl.~507.

""" + _member_tables(bridge, "ed", "End Diaphragm", "ed") + "\n" + _overall_summary(bridge, charts, components)
