# =============================================================================
# Chapter 7: Material Take-off & Quantity Summary
# Table 7.1 (BOQ) + programmatically generated material-quantity charts.
# =============================================================================
from typing import Optional

from .latex_builders import Column, LongTable, figure_block, table_note
from .styles import THEME


def _q(input_dict, key, default="N.A."):
    v = input_dict.get(key, default)
    return default if v in (None, "") else str(v)


def _ed_row(material) -> Optional[list]:
    ed = getattr(material, "end_diaphragm", None) if material is not None else None
    if not ed:
        return None
    return ["2(d)", "End Diaphragms (" + str(ed.get("type", "")) + ")",
            r"\placeholder{Area $\times$ Length}",
            str(ed.get("qty", "N.A.")), f"{ed.get('vol_total_m3', 0):.2f}",
            f"{ed.get('wt_single_mt', 0):.4f}", f"{ed.get('wt_total_mt', 0):.2f}"]


def _bom_table(input_dict, material) -> str:
    t = LongTable(
        columns=[Column(0.9, "c", "S.N."), Column(3.4, "l", "Item Description"),
                 Column(3.7, "c", "Volume (per unit)"), Column(1.2, "c", "Qty."),
                 Column(1.5, "c", r"Total Volume (m\textsuperscript{3})"),
                 Column(1.5, "c", "Unit Weight (MT)"), Column(1.6, "c", "Total Weight (MT)")],
        caption="Bill of Materials (Steel, Concrete and Reinforcement Quantities)",
        label="tab:bom", size="compact",
        note=r"Steel density 7.85 t/m\textsuperscript{3}; concrete 2.5 t/m\textsuperscript{3}; "
             r"reinforcement estimated at 120 kg per m\textsuperscript{3} of deck concrete. "
             r"N.A. = quantity not computed for this design.",
    )
    items = [
        ("1",    "Structural Steel (IS 2062) for Girders", "steel_girders"),
        ("2(a)", "Cross Bracing --- Top Chord",            "bracing_top"),
        ("2(b)", "Cross Bracing --- Bottom Chord",         "bracing_bot"),
        ("2(c)", "Cross Bracing --- Diagonals",            "bracing_diag"),
    ]
    for sn, label, pfx in items:
        t.add_row([sn, label, _q(input_dict, f"{pfx}_vol_formula"), _q(input_dict, f"{pfx}_qty"),
                   _q(input_dict, f"{pfx}_vol_total"), _q(input_dict, f"{pfx}_wt_single"),
                   _q(input_dict, f"{pfx}_wt_total")])
    ed = _ed_row(material)
    if ed:
        t.add_row(ed)
    for sn, label, pfx in [
        ("3", "Concrete (M40) for Deck Slab",  "concrete_deck"),
        ("4", "Reinforcement Steel (Fe 500)",  "rebar_deck"),
        ("5", "Shear Stud Connectors",         "shear_studs"),
        ("6", "Crash Barrier",                 "crash_barrier"),
    ]:
        t.add_row([sn, label, _q(input_dict, f"{pfx}_vol_formula"), _q(input_dict, f"{pfx}_qty"),
                   _q(input_dict, f"{pfx}_vol_total"), _q(input_dict, f"{pfx}_wt_single"),
                   _q(input_dict, f"{pfx}_wt_total")])

    total = getattr(material, "total_steel_mt", None) if material is not None else None
    if total is not None:
        t.add_section_row(rf"Total structural steel (girders + cross bracing + end diaphragms): "
                          rf"{total:.2f} MT")
    return t.render()


def _chart_section(charts, material) -> str:
    charts = charts or {}
    parts = [r"""
\section{Quantity Summary Charts}
\label{sec:quantity-charts}

The charts below are generated automatically from Table~\ref{tab:bom} and give an at-a-glance comparison of the structural steel tonnage of each component and of the deck concrete volume against the reinforcement steel weight.
"""]
    steel = charts.get("steel_tonnage")
    if steel:
        parts.append(figure_block(steel, "Structural steel tonnage by component (girders, cross bracing, end diaphragms)",
                                  width=THEME.figure.chart_width, label="fig:steel-tonnage"))
    else:
        parts.append(table_note("Steel tonnage chart not available: girder / bracing quantities were not computed."))
    conc = charts.get("concrete_vs_rebar")
    if conc:
        parts.append(figure_block(conc, r"Deck concrete volume (m\textsuperscript{3}) versus reinforcement steel weight (MT)",
                                  width=THEME.figure.chart_width, label="fig:concrete-vs-rebar"))
    else:
        parts.append(table_note("Concrete / reinforcement chart not available: deck quantities were not computed."))
    return "\n".join(parts)


def ch7_quantities(input_dict, charts=None, material=None):
    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

\section{Bill of Materials}
\label{sec:bom}

""" + _bom_table(input_dict, material) + "\n" + _chart_section(charts, material)
