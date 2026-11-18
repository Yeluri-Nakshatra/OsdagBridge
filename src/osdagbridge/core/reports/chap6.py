# =============================================================================
# Chapter 6: Drawings and Visualizations
# =============================================================================
from .latex_builders import figure_block, figure_row


def ch6_drawings(fig_paths):
    """Chapter 6 – CAD-generated views (figure numbering is automatic)."""
    g = fig_paths.get
    return r"""
\chapter{Drawings and Visualizations}
\label{ch:drawings}

This section presents CAD-generated views of the designed bridge and its components. All views are generated automatically by OsdagBridge using pythonOCC.

\section{Bridge Configuration and Layout}
\label{sec:bridge-layout}

""" + figure_block(g('final_geometry'), 'Overall 3D Bridge Superstructure', label='fig:bridge-3d') \
    + figure_block(g('cross_section'), 'Typical Cross Section', label='fig:cross-section') \
    + figure_block(g('girder_top'), 'Top View', label='fig:top-view') + r"""

\section{Plate Girder --- Detailed Views}
\label{sec:girder-views}

""" + figure_block(g('girder_3d'), '3D View of Plate Girders', label='fig:girder-3d') \
    + figure_block(g('section_preview'), 'Cross Section of Plate Girder', label='fig:girder-xsec', width=r'0.45\textwidth') \
    + figure_block(g('stiffener_preview'), 'Side View of Girder', label='fig:girder-side') + r"""

\section{Cross Bracing Detail}
\label{sec:bracing-detail}

""" + figure_block(g('cb_diagram'), 'Cross Bracing Layout', label='fig:cb-layout') \
    + figure_row([
        (g('cb_bracing'), 'Cross Bracing -- Bracing Section', 'fig:cb-bracing-sec'),
        (g('cb_top_chord'), 'Cross Bracing -- Top Chord Section', 'fig:cb-top-chord'),
        (g('cb_bottom_chord'), 'Cross Bracing -- Bottom Chord Section', 'fig:cb-bottom-chord'),
    ]) + r"""

\section{End Diaphragm Detail}
\label{sec:diaphragm-detail}

""" + figure_block(g('ed_diagram'), 'End Diaphragm Layout', label='fig:ed-layout') \
    + figure_row([
        (g('ed_bracing'), 'End Diaphragm -- Bracing Section', 'fig:ed-bracing-sec'),
        (g('ed_top_chord'), 'End Diaphragm -- Top Chord Section', 'fig:ed-top-chord'),
        (g('ed_bottom_chord'), 'End Diaphragm -- Bottom Chord Section', 'fig:ed-bottom-chord'),
    ]) + "\n"
