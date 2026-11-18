# =============================================================================
# Chapter 4: Analysis Results
# =============================================================================
from typing import TYPE_CHECKING
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
)
from osdagbridge.core.reports.report_utils import _tex, _fig_embed
from .latex_builders import Cell, Column, KeyValueTable, LongTable, status_cell

if TYPE_CHECKING:
    from .report_generator import ReportDataBridge


def ch4_analysis(asum, fig_paths, bridge: "ReportDataBridge", span_m: float):
    lc_summary  = (asum or {}).get('load_cases', {}) or {}
    rxn_summary = (asum or {}).get('reactions',  {}) or {}

    def _is_moving(lc_name: str) -> bool:
        n = lc_name.lower()
        return "moving" in n or " pos_" in n

    lc_summary  = {k: v for k, v in lc_summary.items()  if not _is_moving(k)}
    rxn_summary = {k: v for k, v in rxn_summary.items() if not _is_moving(k)}

    def _fmt(val, nd=3):
        try:
            return f"{float(val):.{nd}f}"
        except (TypeError, ValueError):
            return "---"

    demands = LongTable(
        columns=[Column(2.9, "c"), Column(1.5, "c"), Column(1.1, "c"), Column(1.2, "c"),
                 Column(1.5, "c"), Column(1.1, "c"), Column(1.2, "c"), Column(1.5, "c"), Column(1.5, "c")],
        caption="Summary of Maximum Demands", label="tab:max-demands", size="dense",
        header=[
            [Cell("Load Case / Combination", rowspan=2, bold=True), Cell("Bending Moment", colspan=3, bold=True),
             Cell("Shear Force", colspan=3, bold=True), Cell("Reaction at Supports", colspan=2, bold=True)],
            [None, "Max (kN-m)", "Girder", "Loc. (m)", "Max (kN)", "Girder", "Loc. (m)", "Left (kN)", "Right (kN)"],
        ],
        note="Values are the maxima over all girders of the grillage model for each load case / combination.",
    )
    all_lcs = list(lc_summary.keys()) + [k for k in rxn_summary if k not in lc_summary]
    for lc in all_lcs:
        bm_d  = lc_summary.get(lc) or {}
        rxn_d = rxn_summary.get(lc) or {}
        demands.add_row([
            _tex(lc), _fmt(bm_d.get('max_bm')), _tex(bm_d.get('bm_girder', '---')), _fmt(bm_d.get('bm_location')),
            _fmt(bm_d.get('max_sf')), _tex(bm_d.get('sf_girder', '---')), _fmt(bm_d.get('sf_location')),
            _fmt(rxn_d.get('left_kN')), _fmt(rxn_d.get('right_kN')),
        ])

    # ── Deflection summary (worst girder) ─────────────────────────────────
    _span_m         = float(bridge.input_dict.get(KEY_SPAN, 0) or 0)
    _allow_live_mm  = _span_m * 1000.0 / 800.0
    _allow_total_mm = _span_m * 1000.0 / 600.0
    try:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1) or 1)
    except (TypeError, ValueError):
        n = 1
    _live_mm = _total_mm = None
    for _gi in range(1, n + 1):
        _l = bridge.output_dict.get(f"{KEY_SD_DEFL_LIVE}.G{_gi}")
        _t = bridge.output_dict.get(f"{KEY_SD_DEFL_TOTAL}.G{_gi}")
        if _l is not None:
            _live_mm  = max(_live_mm, float(_l))  if _live_mm  is not None else float(_l)
        if _t is not None:
            _total_mm = max(_total_mm, float(_t)) if _total_mm is not None else float(_t)

    defl = KeyValueTable(caption=r"Deflection Summary (Live Load \& Total Load)", label="tab:deflection-summary",
                         wide_param=True, note="IRC 22 Cl. 604.3.2: live load + impact $\\leq L/800$; total $\\leq L/600$.")
    defl.add(r"Deflection due to Live Load, $\delta_{LL}$", f"{_live_mm:.3f} mm" if _live_mm is not None else "---")
    defl.add(r"Allowable Live Load Deflection, $\Delta_{allow}$", f"$L/800$ = {_allow_live_mm:.1f} mm")
    defl.add("Live Load Deflection Check Status",
             status_cell(_live_mm <= _allow_live_mm) if _live_mm is not None else "---")
    defl.add(r"Deflection due to Total Load, $\delta_{total}$", f"{_total_mm:.3f} mm" if _total_mm is not None else "---")
    defl.add(r"Allowable Total Deflection, $\Delta_{allow}$", f"$L/600$ = {_allow_total_mm:.1f} mm")
    defl.add("Total Load Deflection Check Status",
             status_cell(_total_mm <= _allow_total_mm) if _total_mm is not None else "---")

    return r"""
\chapter{Analysis Results}

A grillage model was used for structural analysis. The deck is idealized as a grid of elastic beam elements --- longitudinal members represent the composite steel girders with effective slab, and transverse members represent the slab or cross frames. This section summarizes the critical output from that analysis.

\section{Maximum Demands and Reactions}
\label{sec:max-demands}

""" + demands.render() + r"""

\section{Deflections}
\label{sec:deflections}

""" + defl.render() + r"""

\section{Force and Deflection Envelopes}
\label{sec:envelopes}

""" + _fig_embed(fig_paths.get('bm_envelope'), 'Bending Moment Envelope (ULS): max/min BM along the span. X-axis: distance from left support (m); Y-axis: bending moment (kN-m).') + r"""
""" + _fig_embed(fig_paths.get('sf_envelope'), 'Shear Force Envelope (ULS): max/min SF along the span. X-axis: distance from left support (m); Y-axis: shear force (kN).') + r"""
""" + _fig_embed(fig_paths.get('defl_ll'), r'Vertical Deflection $D_y$ (1.0 LL): maximum deflection along the span.') + r"""
"""
