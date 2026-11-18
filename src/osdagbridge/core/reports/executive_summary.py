# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

from osdagbridge.core.reports.report_utils import _fig_or_placeholder, _render_value, _tex, get_girder_entries
from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_SD_SECTION_DESIGNATION,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS
)
from .latex_builders import Column, KeyValueTable, LongTable, status_from_text, ur_cell
from .styles import THEME
from .summary_data import collect_utilization


def executive_summary(input_dict, output_dict, fig_paths) -> str:
    plan_fig = _fig_or_placeholder(fig_paths.get('girder_top'), 'Figure 1 -- Overall Bridge Plan')
    cs_fig = _fig_or_placeholder(fig_paths.get('cross_section'),
                                  'Figure 2 -- Typical Cross-Section (with girder, deck, barriers, footpath)')
    geom_fig = _fig_or_placeholder(fig_paths.get('final_geometry'),
                                    'Figure 3 -- 3D View of Bridge Superstructure')

    sec = _render_value(output_dict, KEY_SD_SECTION_DESIGNATION)

    # ── Component utilisation (same source as Section 5.5) ────────────────
    components = collect_utilization(output_dict, input_dict)
    girders = components[0]
    gov = girders.governing_item
    gov_name = gov.label if gov else ""
    overall = [c for c in components if c.max_ur is not None]
    if overall:
        worst = max(overall, key=lambda c: c.max_ur)
        overall_ur_str = f"{worst.max_ur:.2f} ({worst.name})"
        overall_status = "Pass" if all(c.max_ur <= 1.0 for c in overall) else (
            "Fail (" + ", ".join(c.name for c in overall if c.max_ur > 1.0) + ")")
    else:
        overall_ur_str = ""
        overall_status = ""

    # Executive-summary tables precede Chapter 1, so they are captioned
    # without LaTeX numbering (like Figures 1--3) to avoid "Table 0.x".
    ov = KeyValueTable(caption="Project Overview", label="tab:project-overview", numbered=False)
    ov.add("Bridge Type", _render_value(input_dict, KEY_STRUCTURE_TYPE))
    ov.add("Design Standard", "IRC 5, IRC 6, IRC 22, IRC 24, IS 800")
    ov.add("Span", _render_value(input_dict, KEY_SPAN, ' m'))
    ov.add("Carriageway Width", _render_value(input_dict, KEY_CARRIAGEWAY_WIDTH, ' m'))
    ov.add("No. of Girders", _render_value(input_dict, KEY_TS_NO_OF_GIRDERS))
    ov.add("Girder Spacing", _render_value(input_dict, KEY_TS_GIRDER_SPACING, ' m'))
    ov.add("Deck Thickness", _render_value(input_dict, KEY_TS_DECK_THICKNESS, ' mm'))
    ov.add("Overall Design Status", status_from_text(overall_status) if overall_status else "---")
    ov.add("Governing Girder Check", _tex(gov_name) if gov_name else "---")
    ov.add("Overall Utilization Ratio (max)", _tex(overall_ur_str) if overall_ur_str else "---")

    # ── Table 1: final geometry per girder (dynamic column count) ─────────
    labels = get_girder_entries(input_dict) or [("", "")]
    n_cols = len(labels)
    label_w = 3.0
    per_col_overhead = 2 * THEME.table.col_sep_pt / 28.45 + 0.05     # pt → cm, + rule
    avail = THEME.page.text_width_cm - label_w - per_col_overhead * (n_cols + 1)
    gw = round(max(1.4, avail / n_cols), 2)
    cols = [Column(label_w, "l", "")] + [Column(gw, "c", _tex(lbl)) for lbl, _ in labels]
    t1 = LongTable(cols, caption="Table 1 -- Final Bridge Geometry (after optimization)",
                   label="tab:final-geometry", numbered=False)
    t1.add_row(["Member ID"] + [_tex(mid) for _, mid in labels])
    t1.add_row(["Section Designation"] + [sec] * n_cols)
    t1.add_row(["Governing Check"] + [_tex(gov_name)] * n_cols)
    t1.add_row(["Utilization Ratio"] + [ur_cell(girders.max_ur)] * n_cols)

    # ── Key design outcomes: one row per primary element ──────────────────
    ko = LongTable([Column(3.8, "l", "Component"), Column(4.4, "l", "Governing Check"),
                    Column(2.2, "c", "Max UR"), Column(2.0, "c", "Status")],
                   caption="Table 2 -- Key Design Outcomes", label="tab:key-outcomes", numbered=False,
                   note="UR = Demand / Capacity. A value $\\leq 1.0$ indicates a passing check. "
                        "Details in Chapter 5; chart in Section~\\ref{sec:overall-summary}.")
    for c in components:
        g = c.governing_item
        ko.add_row([c.name, _tex(g.label) if g else _tex(c.note or "---"),
                    ur_cell(c.max_ur) if c.max_ur is not None else "---",
                    status_from_text(c.status)])

    return r"""
\newpage
{\centering\Large\bfseries Executive Summary\par}
\addcontentsline{toc}{chapter}{Executive Summary}
\vspace{0.8em}

This section provides a concise summary of the bridge design, key inputs, governing loads, and final design outcomes.

\section*{Project Overview}
\addcontentsline{toc}{section}{Project Overview}
\label{sec:project-overview}

""" + ov.render() + "\n" + plan_fig + r"""

\newpage

""" + cs_fig + '\n' + geom_fig + '\n' + t1.render() + r"""

\section*{Key Design Outcomes Summary}
\addcontentsline{toc}{section}{Key Design Outcomes Summary}
\label{sec:key-outcomes}

""" + ko.render() + r"""

\section*{Design Assumptions and Limitations}
\addcontentsline{toc}{section}{Design Assumptions and Limitations}
\label{sec:assumptions}

\begin{itemize}
\item Additional inputs not provided by the user were assumed by software per IRC/IS code defaults or practical consideration.
\item Grillage analysis was performed using OSPGrillage assuming simply supported I-girders.
\item Substructure and foundation design are not included in this report.
\item Splice connections and bearings are not designed in this version.
\end{itemize}
"""
