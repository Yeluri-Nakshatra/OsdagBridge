# =============================================================================
# Chapter 2: Input Parameters
# Presentation only — layout from `styles` via `latex_builders`.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_CB_LOAD,
    KEY_CB_TYPE,
    KEY_CROSS_BRACING,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DESIGN_MODE,
    KEY_DO_GAMMA_C_BASIC,
    KEY_DO_GAMMA_FLT,
    KEY_DO_GAMMA_M0,
    KEY_DO_GAMMA_M1,
    KEY_DO_GAMMA_MF,
    KEY_DO_GAMMA_S,
    KEY_DO_GAMMA_V,
    KEY_END_DIAPHRAGM,
    KEY_FOOTPATH,
    KEY_GIRDER,
    KEY_INCLUDE_MEDIAN,
    KEY_MD_TYPE,
    KEY_MP_CB_BRACING_SECTION_DESIGNATION,
    KEY_MP_CB_MEMBER_ID,
    KEY_MP_CB_SELECT_GIRDERS,
    KEY_MP_CB_SPACING,
    KEY_MP_CB_TYPE,
    KEY_MP_ED_BRACING_SECTION_DESIGNATION,
    KEY_MP_ED_MEMBER_ID,
    KEY_MP_ED_SELECT_GIRDERS,
    KEY_MP_ED_TYPE,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_SYMMETRY,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
    KEY_MP_GIRDER_TORSIONAL_RESTRAINT,
    KEY_MP_GIRDER_TYPE,
    KEY_MP_GIRDER_WARPING_RESTRAINT,
    KEY_MP_GIRDER_WEB_THICKNESS,
    KEY_MP_GIRDER_WEB_TYPE,
    KEY_MP_STIFFENER_BEARING_THICKNESS,
    KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_MP_STIFFENER_LONGITUDINAL,
    KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
    KEY_MP_STIFFENER_SPACING,
    KEY_RL_LOAD_VALUE,
    KEY_RL_TYPE,
    KEY_SD_SHEAR_DIAMETER,
    KEY_SD_SHEAR_HEIGHT,
    KEY_SD_SHEAR_STUDS_PER_SECTION,
    KEY_SD_SHEAR_ULTIMATE_STRENGTH,
    KEY_SD_SHEAR_YIELD_STRENGTH,
    KEY_SKEW_ANGLE,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_OVERALL_WIDTH,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS
)

from osdagbridge.core.reports.report_utils import _render_value, get_girder_entries, _tex
from .latex_builders import Column, KeyValueTable, LongTable

_DEG = r"$^\circ$"


def ch2_input_parameters(m, input_dict, output_dict=None):
    girder_entries = get_girder_entries(input_dict)
    n_girders = len(girder_entries)
    rv = lambda key, unit="": _render_value(input_dict, key, unit)   # noqa: E731

    loc = KeyValueTable(caption="Project Location", label="tab:project-location")
    loc.add("Project Location", _tex(m.project_location))
    loc.add("Latitude / Longitude", rv('latitude') + ', ' + rv('longitude'))
    loc.add("Seismic Zone (IRC 6)", rv('seismic_zone'))
    loc.add("Basic Wind Speed (IRC 6)", rv('wind_speed', ' m/s'))
    loc.add("Shade Temp. Max / Min (IRC 6)", rv('shade_temp_max') + _DEG + "C / " + rv('shade_temp_min') + _DEG + "C")

    geo = KeyValueTable(caption="Bridge Geometry", label="tab:bridge-geometry")
    geo.add("Type of Structure", rv(KEY_STRUCTURE_TYPE))
    geo.add("Span", rv(KEY_SPAN, ' m'))
    geo.add("Carriageway Width", rv(KEY_CARRIAGEWAY_WIDTH, ' m'))
    geo.add("Include Median", rv(KEY_INCLUDE_MEDIAN))
    geo.add("Footpath", rv(KEY_FOOTPATH))
    geo.add("Skew Angle", rv(KEY_SKEW_ANGLE, _DEG) + r" (IRC 24 Cl. 504.8 limit: $\pm$15" + _DEG + ")")

    mat = KeyValueTable(caption="Material Selection", label="tab:material")
    mat.add("Girder Steel Grade (IS 2062)", rv(KEY_GIRDER))
    mat.add("Cross Bracing Steel Grade", rv(KEY_CROSS_BRACING))
    mat.add("End Diaphragm Steel Grade", rv(KEY_END_DIAPHRAGM))
    mat.add("Concrete Deck Grade (IRC 22)", rv(KEY_DECK_CONCRETE_GRADE_BASIC))

    ts = KeyValueTable(caption="Typical Section Details", label="tab:typical-section")
    ts.add("Overall Bridge Width", rv(KEY_TS_OVERALL_WIDTH, ' m'))
    ts.add("No. of Girders", rv(KEY_TS_NO_OF_GIRDERS))
    ts.add("Girder Spacing", rv(KEY_TS_GIRDER_SPACING, ' m'))
    ts.add("Deck Overhang Width", rv(KEY_TS_DECK_OVERHANG, ' m'))
    ts.add("Deck Thickness", rv(KEY_TS_DECK_THICKNESS, ' mm'))
    ts.add("Footpath Width", rv(KEY_TS_FOOTPATH_WIDTH, ' m') + " (IRC 5 Cl. 104.3.6 min: 1.5 m)")
    ts.add("No. of Traffic Lanes", rv(KEY_WC_LD_LANE_TABLE_COUNT) + " (per IRC 5 Cl. 104.3.1)")

    comp = KeyValueTable(caption="Components Details", label="tab:components")
    comp.add("Crash Barrier Type", rv(KEY_CB_TYPE))
    comp.add("Crash Barrier Load", rv(KEY_CB_LOAD, ' kN/m'))
    if str(input_dict.get(KEY_INCLUDE_MEDIAN, "")).strip().lower() in ("yes", "true", "1"):
        comp.add("Median Type", rv(KEY_MD_TYPE))
    comp.add("Railing Type", rv(KEY_RL_TYPE))
    comp.add("Railing Load", rv(KEY_RL_LOAD_VALUE, ' kN/m'))
    comp.add("Wearing Course Material", rv(KEY_WC_MATERIAL))
    comp.add("Wearing Course Thickness", rv(KEY_WC_THICKNESS, ' mm'))

    return r"""
\chapter{Input Parameters}

This section documents all inputs provided to OsdagBridge. User-provided inputs are clearly distinguished from software-assumed defaults. Where the user did not supply a value, the software has applied the IRC/IS code default or an empirical guideline; these are annotated with an asterisk (\sdstar{}).

\section{Basic Inputs (User-Defined)}
\label{sec:basic-inputs}

\noindent\textit{Note: These inputs are mandatory and were provided by the user.}

""" + loc.render() + "\n" + geo.render() + "\n" + mat.render() + r"""

\section{Additional Inputs}
\label{sec:additional-inputs}

Where the user has modified additional inputs, those values are reported here. Where no modification was made, the software default is shown.

""" + ts.render() + "\n" + comp.render() + "\n" \
        + _girder_tables(input_dict, n_girders) + "\n" \
        + _bracing_tables(input_dict, n_girders) + "\n" \
        + _shear_connector_table(input_dict, output_dict) + "\n" \
        + _safety_factors_table(input_dict)


def _girder_tables(input_dict, n_girders):
    n = n_girders if n_girders >= 1 else 1
    girder_entries = get_girder_entries(input_dict)
    if not girder_entries:
        girder_entries = [(f"Girder {i}", "M1") for i in range(1, n + 1)]
    rv = lambda key, unit="": _render_value(input_dict, key, unit)   # noqa: E731

    gen = LongTable([Column(2.0, "l", "Girder"), Column(1.8, "l", "Member ID"), Column(3.2, "l", "Design Mode"),
                     Column(3.4, "l", "Girder Type"), Column(3.6, "l", "Girder Symmetry")],
                    caption="Girder General Information", label="tab:girder-general")
    dim = LongTable([Column(1.6, "l", "Girder"), Column(2.4, "c", "Total Depth, $D$ (mm)"),
                     Column(1.8, "c", "Web, $t_w$ (mm)"),
                     Column(4.0, "c", r"Top Flange ($b_{tf}$, $t_{tf}$) mm"),
                     Column(4.0, "c", r"Bottom Flange ($b_{bf}$, $t_{bf}$) mm")],
                    caption="Girder Section Dimensions", label="tab:girder-dimensions")
    rst = LongTable([Column(1.3, "l", "Girder"), Column(2.3, "l", "Torsional / Warping Restraint"),
                     Column(2.2, "l", "Web Philosophy"), Column(3.0, "l", "Intermediate Stiffeners"),
                     Column(2.3, "l", "Longitudinal Stiffeners"), Column(2.6, "l", "Bearing Stiffener")],
                    caption="Girder Restraint and Stiffener Details", label="tab:girder-restraint", size="compact")

    for i, (g_lbl, m_id) in enumerate(girder_entries, start=1):
        s = f".G{i}.M1"
        gen.add_row([_tex(g_lbl), _tex(m_id), rv(KEY_DESIGN_MODE), rv(KEY_MP_GIRDER_TYPE + s), rv(KEY_MP_GIRDER_SYMMETRY + s)])
        dim.add_row([_tex(g_lbl), rv(KEY_MP_GIRDER_DEPTH + s, ' mm'), rv(KEY_MP_GIRDER_WEB_THICKNESS + s, ' mm'),
                     rv(KEY_MP_GIRDER_TOP_FLANGE_WIDTH + s, ' mm') + ', ' + rv(KEY_MP_GIRDER_TOP_FLANGE_THICKNESS + s, ' mm'),
                     rv(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH + s, ' mm') + ', ' + rv(KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS + s, ' mm')])
        rst.add_row([_tex(g_lbl),
                     rv(KEY_MP_GIRDER_TORSIONAL_RESTRAINT + s) + ', ' + rv(KEY_MP_GIRDER_WARPING_RESTRAINT + s),
                     rv(KEY_MP_GIRDER_WEB_TYPE + s),
                     rv(KEY_MP_STIFFENER_INTERMEDIATE + s) + '; Spacing: ' + rv(KEY_MP_STIFFENER_INTERMEDIATE_SPACING + s, ' mm')
                     + '; Thickness: ' + rv(KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS + s, ' mm'),
                     rv(KEY_MP_STIFFENER_LONGITUDINAL + s),
                     'No.: ' + rv(KEY_MP_STIFFENER_NO_BEARING_STIFFENERS + s) + '; Spacing: '
                     + rv(KEY_MP_STIFFENER_SPACING + s, ' mm') + '; Thickness: '
                     + rv(KEY_MP_STIFFENER_BEARING_THICKNESS + s, ' mm')])

    return r"""
\subsection{Girder Details}
\label{subsec:girder-details}

""" + gen.render() + "\n" + dim.render() + "\n" + rst.render()


def _bracing_tables(input_dict, n_girders):
    n = n_girders if n_girders >= 2 else 2
    rv = lambda key, unit="": _render_value(input_dict, key, unit)   # noqa: E731

    cb = LongTable([Column(2.2, "l", "Location"), Column(2.2, "l", "Member IDs"), Column(3.2, "l", "Type of Bracing"),
                    Column(3.6, "l", "Bracing Section"), Column(2.4, "c", "Spacing (m)")],
                   caption="Member Properties: Cross Bracing Details", label="tab:cross-bracing-details")
    ed = LongTable([Column(2.6, "l", "Location"), Column(2.6, "l", "Member IDs"), Column(4.2, "l", "Type of Diaphragm"),
                    Column(5.0, "l", "Section")],
                   caption="Member Properties: End Diaphragm Details", label="tab:end-diaphragm-details")
    for i in range(1, n):
        p = f".G{i}G{i+1}"
        cb.add_row([rv(f"{KEY_MP_CB_SELECT_GIRDERS}{p}.B{i}M1"), rv(f"{KEY_MP_CB_MEMBER_ID}{p}.B{i}M1"),
                    rv(f"{KEY_MP_CB_TYPE}{p}.B{i}M1"), rv(f"{KEY_MP_CB_BRACING_SECTION_DESIGNATION}{p}.B{i}M1"),
                    rv(f"{KEY_MP_CB_SPACING}{p}.B{i}M1")])
        ed.add_row([rv(f"{KEY_MP_ED_SELECT_GIRDERS}{p}.E{i}M1"), rv(f"{KEY_MP_ED_MEMBER_ID}{p}.E{i}M1"),
                    rv(f"{KEY_MP_ED_TYPE}{p}.E{i}M1"), rv(f"{KEY_MP_ED_BRACING_SECTION_DESIGNATION}{p}.E{i}M1")])

    return r"""
\subsection{Transverse Members}
\label{subsec:transverse-members}

""" + cb.render() + "\n" + ed.render()


def _shear_connector_table(input_dict, output_dict=None):
    od = output_dict or {}
    t = KeyValueTable(caption="Shear Connector Details", label="tab:shear-connectors")
    t.add("Stud Diameter", _render_value(od, KEY_SD_SHEAR_DIAMETER, ' mm'))
    t.add("Stud Height", _render_value(od, KEY_SD_SHEAR_HEIGHT, ' mm'))
    t.add("Stud $f_y$", _render_value(od, KEY_SD_SHEAR_YIELD_STRENGTH, ' MPa'))
    t.add("Stud $f_u$", _render_value(od, KEY_SD_SHEAR_ULTIMATE_STRENGTH, ' MPa'))
    t.add("No. of Studs per Section", _render_value(od, KEY_SD_SHEAR_STUDS_PER_SECTION))
    return r"""
\subsection{Shear Connectors and Partial Safety Factors}
\label{subsec:shear-and-safety}

""" + t.render()


def _safety_factors_table(input_dict):
    t = KeyValueTable(caption="Partial Safety Factors", label="tab:safety-factors",
                      note="All values are per IRC 22 Table 1 unless user-modified.")
    t.add(r"$\gamma_{M0}$ (Yielding / Buckling)", _render_value(input_dict, KEY_DO_GAMMA_M0))
    t.add(r"$\gamma_{M1}$ (Ultimate Stress)", _render_value(input_dict, KEY_DO_GAMMA_M1))
    t.add(r"$\gamma_C$ (Concrete, Basic)", _render_value(input_dict, KEY_DO_GAMMA_C_BASIC))
    t.add(r"$\gamma_s$ (Reinforcement)", _render_value(input_dict, KEY_DO_GAMMA_S))
    t.add(r"$\gamma_v$ (Shear Connectors)", _render_value(input_dict, KEY_DO_GAMMA_V))
    t.add(r"$\gamma_{fft}$ (Fatigue Load)", _render_value(input_dict, KEY_DO_GAMMA_FLT))
    t.add(r"$\gamma_{Mft}$ (Fatigue Strength)", _render_value(input_dict, KEY_DO_GAMMA_MF))
    return t.render()
