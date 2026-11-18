# =============================================================================
# OsdagBridge — Report chart generation (matplotlib, headless)
# =============================================================================
# Charts are rendered to temporary PNG assets during report generation and
# embedded with `latex_builders.figure_block`.  All visual attributes come
# from `styles.THEME.chart` / `styles.THEME.palette`.
#
#   • utilisation-ratio charts (Section 5.5): bars for every design check of the
#     four primary components with a red dashed `UR = 1.0` threshold line,
#   • material-quantity charts (Chapter 7): structural steel tonnage per
#     component and concrete volume (m³) vs reinforcement weight (MT).
# =============================================================================
from __future__ import annotations

import logging
import os
from typing import List, Optional, Sequence, Tuple

from .styles import THEME, ReportTheme

logger = logging.getLogger(__name__)


def _mpl():
    """Import matplotlib lazily with the non-interactive Agg backend."""
    import matplotlib
    matplotlib.use("Agg", force=False)
    import matplotlib.pyplot as plt
    return plt


def _apply_rc(plt, theme: ReportTheme) -> None:
    c = theme.chart
    plt.rcParams.update({
        "font.family": c.font_family,
        "font.size": c.label_size,
        "axes.titlesize": c.title_size,
        "axes.labelsize": c.label_size,
        "xtick.labelsize": c.tick_size,
        "ytick.labelsize": c.tick_size,
        "axes.edgecolor": "#444444",
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "text.color": theme.palette.chart_text,
        "axes.labelcolor": theme.palette.chart_text,
        "xtick.color": theme.palette.chart_text,
        "ytick.color": theme.palette.chart_text,
        "figure.dpi": 100,
        "savefig.dpi": c.dpi,
    })


def _wrap(label: str, width: int = 16) -> str:
    import textwrap
    return "\n".join(textwrap.wrap(str(label), width=width)) or str(label)


def _save(fig, path: str, theme: ReportTheme) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fig.savefig(path, dpi=theme.chart.dpi, bbox_inches="tight", facecolor="white")
    plt = _mpl()
    plt.close(fig)
    return path.replace("\\", "/")


# ─────────────────────────────────────────────────────────────────────────────
# Utilisation ratio charts
# ─────────────────────────────────────────────────────────────────────────────
COMPONENT_COLORS = {
    "girder":    "chart_girder",
    "deck":      "chart_deck",
    "bracing":   "chart_bracing",
    "diaphragm": "chart_diaphragm",
}


def _component_color(key: str, theme: ReportTheme) -> str:
    attr = COMPONENT_COLORS.get(key, "chart_girder")
    return getattr(theme.palette, attr)


def _draw_threshold(ax, theme: ReportTheme):
    c = theme.chart
    ax.axhline(c.threshold_value, color=theme.palette.chart_threshold,
               linestyle=c.threshold_linestyle, linewidth=c.threshold_linewidth,
               label=c.threshold_label, zorder=3)


def _ur_ylim(ax, values: Sequence[float], theme: ReportTheme):
    c = theme.chart
    top = max([v for v in values if v is not None] + [0.0])
    ax.set_ylim(0, max(c.ur_axis_min_top, top * (1.0 + c.ur_axis_headroom)))


def render_ur_overview(components: Sequence, path: str,
                       theme: ReportTheme = THEME) -> Optional[str]:
    """One bar per primary component = its governing (maximum) UR.

    `components` is a sequence of objects with `.name`, `.key` and `.max_ur`
    (see `summary_data.ComponentUR`).  Returns the saved path or None if
    nothing could be plotted.
    """
    data = [(c.name, c.key, c.max_ur) for c in components if c.max_ur is not None]
    if not data:
        return None
    plt = _mpl()
    _apply_rc(plt, theme)
    c = theme.chart
    fig, ax = plt.subplots(figsize=theme.chart.figsize_square)
    labels = [_wrap(d[0], 14) for d in data]
    values = [d[2] for d in data]
    colors = [theme.palette.chart_fail if v > c.threshold_value else _component_color(k, theme)
              for (_, k, v) in data]
    bars = ax.bar(labels, values, width=c.bar_width, color=colors,
                  edgecolor=c.bar_edge_color, linewidth=c.bar_edge_width, zorder=2)
    for b, v in zip(bars, values):
        ax.annotate(f"{v:.2f}", (b.get_x() + b.get_width() / 2, b.get_height()),
                    ha="center", va="bottom", fontsize=c.value_label_size,
                    xytext=(0, 2), textcoords="offset points")
    _draw_threshold(ax, theme)
    _ur_ylim(ax, values, theme)
    ax.set_ylabel("Utilisation Ratio (Demand / Capacity)")
    ax.set_title("Governing Utilisation Ratio per Component")
    ax.yaxis.grid(True, color=theme.palette.chart_grid, alpha=c.grid_alpha, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", frameon=False, fontsize=c.tick_size)
    return _save(fig, path, theme)


def render_ur_detail(components: Sequence, path: str,
                     theme: ReportTheme = THEME) -> Optional[str]:
    """One panel per primary element (2 × 2 grid): a bar for every design
    check, colour-coded by component, failing checks in red, and the red
    dashed UR = 1.0 threshold in every panel (shared y-axis)."""
    groups = [(comp, [it for it in comp.items if it.ur is not None]) for comp in components]
    if not any(items for _, items in groups):
        return None
    plt = _mpl()
    _apply_rc(plt, theme)
    c = theme.chart
    n = len(groups)
    ncols = 2 if n > 1 else 1
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(10.0, 3.6 * nrows), sharey=True)
    axes = list(axes.flat) if hasattr(axes, "flat") else [axes]
    all_vals = [it.ur for _, items in groups for it in items]
    y_top = max(c.ur_axis_min_top, max(all_vals) * (1.0 + c.ur_axis_headroom))

    for ax, (comp, items) in zip(axes, groups):
        base = _component_color(comp.key, theme)
        ax.set_title(comp.name, fontsize=c.title_size, color=base, fontweight="bold")
        if not items:
            ax.text(0.5, 0.5, comp.note or "No results", transform=ax.transAxes,
                    ha="center", va="center", fontsize=c.label_size, color=theme.palette.chart_text)
            ax.set_xticks([])
        else:
            xs = list(range(len(items)))
            colors = [theme.palette.chart_fail if it.ur > c.threshold_value else base for it in items]
            bars = ax.bar(xs, [it.ur for it in items], width=c.bar_width, color=colors,
                          edgecolor=c.bar_edge_color, linewidth=c.bar_edge_width, zorder=2)
            for b, it in zip(bars, items):
                ax.annotate(f"{it.ur:.2f}", (b.get_x() + b.get_width() / 2, it.ur), ha="center",
                            va="bottom", fontsize=c.value_label_size, xytext=(0, 2),
                            textcoords="offset points")
            ax.set_xticks(xs)
            ax.set_xticklabels([_wrap(it.label, 10) for it in items], fontsize=c.tick_size - 1,
                               rotation=35, ha="right", rotation_mode="anchor")
        _draw_threshold(ax, theme)
        ax.set_ylim(0, y_top)
        ax.yaxis.grid(True, color=theme.palette.chart_grid, alpha=c.grid_alpha, zorder=0)
        ax.set_axisbelow(True)
    for ax in axes[n:]:
        ax.axis("off")
    for i, ax in enumerate(axes[:n]):
        if i % ncols == 0:
            ax.set_ylabel("Utilisation Ratio")
    fig.suptitle("Utilisation Ratio (Demand / Capacity) of all Design Checks", fontsize=c.title_size + 1)
    axes[0].legend(loc="upper right", frameon=False, fontsize=c.tick_size)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return _save(fig, path, theme)


# ─────────────────────────────────────────────────────────────────────────────
# Material quantity charts
# ─────────────────────────────────────────────────────────────────────────────
def render_steel_tonnage(items: Sequence[Tuple[str, float]], path: str,
                         theme: ReportTheme = THEME) -> Optional[str]:
    """Bar chart of structural steel tonnage per component (MT)."""
    data = [(lbl, float(v)) for lbl, v in items if v is not None]
    if not data or all(v <= 0 for _, v in data):
        return None
    plt = _mpl()
    _apply_rc(plt, theme)
    c = theme.chart
    fig, ax = plt.subplots(figsize=theme.chart.figsize_square)
    labels = [_wrap(l, 14) for l, _ in data]
    values = [v for _, v in data]
    palette_cycle = [theme.palette.chart_girder, theme.palette.chart_bracing,
                     theme.palette.chart_diaphragm, theme.palette.chart_rebar,
                     theme.palette.chart_deck]
    colors = [palette_cycle[i % len(palette_cycle)] for i in range(len(values))]
    bars = ax.bar(labels, values, width=c.bar_width, color=colors,
                  edgecolor=c.bar_edge_color, linewidth=c.bar_edge_width, zorder=2)
    for b, v in zip(bars, values):
        ax.annotate(f"{v:,.2f} MT", (b.get_x() + b.get_width() / 2, b.get_height()),
                    ha="center", va="bottom", fontsize=c.value_label_size,
                    xytext=(0, 2), textcoords="offset points")
    ax.set_ylabel("Structural steel (MT)")
    ax.set_title("Structural Steel Tonnage by Component")
    ax.set_ylim(0, max(values) * 1.18 if max(values) > 0 else 1)
    ax.yaxis.grid(True, color=theme.palette.chart_grid, alpha=c.grid_alpha, zorder=0)
    ax.set_axisbelow(True)
    return _save(fig, path, theme)


def render_concrete_vs_rebar(concrete_m3: Optional[float], rebar_mt: Optional[float],
                             path: str, theme: ReportTheme = THEME) -> Optional[str]:
    """Twin-axis bar chart: deck concrete volume (m³) vs reinforcement weight (MT)."""
    if concrete_m3 is None and rebar_mt is None:
        return None
    plt = _mpl()
    _apply_rc(plt, theme)
    c = theme.chart
    fig, ax1 = plt.subplots(figsize=theme.chart.figsize_square)
    ax2 = ax1.twinx()
    ax2.spines["right"].set_visible(True)

    cv = float(concrete_m3 or 0.0)
    rv = float(rebar_mt or 0.0)
    b1 = ax1.bar([0], [cv], width=c.bar_width, color=theme.palette.chart_concrete,
                 edgecolor=c.bar_edge_color, linewidth=c.bar_edge_width, zorder=2,
                 label="Concrete volume (m³)")
    b2 = ax2.bar([1], [rv], width=c.bar_width, color=theme.palette.chart_rebar,
                 edgecolor=c.bar_edge_color, linewidth=c.bar_edge_width, zorder=2,
                 label="Reinforcement steel (MT)")
    ax1.annotate(f"{cv:,.2f} m³", (0, cv), ha="center", va="bottom",
                 fontsize=c.value_label_size, xytext=(0, 2), textcoords="offset points")
    ax2.annotate(f"{rv:,.2f} MT", (1, rv), ha="center", va="bottom",
                 fontsize=c.value_label_size, xytext=(0, 2), textcoords="offset points")
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(["Concrete deck slab", "Reinforcement steel"])
    ax1.set_ylabel("Concrete volume (m³)", color=theme.palette.chart_concrete)
    ax2.set_ylabel("Reinforcement steel (MT)", color=theme.palette.chart_rebar)
    ax1.set_ylim(0, cv * 1.25 if cv > 0 else 1)
    ax2.set_ylim(0, rv * 1.25 if rv > 0 else 1)
    ax1.set_title("Deck Concrete Volume vs Reinforcement Steel Weight")
    ax1.yaxis.grid(True, color=theme.palette.chart_grid, alpha=c.grid_alpha, zorder=0)
    ax1.set_axisbelow(True)
    ax1.legend([b1, b2], ["Concrete volume (m³)", "Reinforcement steel (MT)"],
               loc="upper center", frameon=False, fontsize=c.tick_size, ncol=2,
               bbox_to_anchor=(0.5, -0.12))
    return _save(fig, path, theme)


# ─────────────────────────────────────────────────────────────────────────────
# Orchestration helper used by report_generator
# ─────────────────────────────────────────────────────────────────────────────
def generate_report_charts(components, material, charts_dir: str,
                           theme: ReportTheme = THEME) -> dict:
    """Render every chart the report embeds.  Returns {key: path or None}.

    Never raises: a failing chart is logged and reported as None so the
    report degrades to a textual note instead of aborting.
    """
    ext = theme.chart.image_format
    jobs = {
        "ur_overview":        lambda p: render_ur_overview(components, p, theme),
        "ur_detail":          lambda p: render_ur_detail(components, p, theme),
        "steel_tonnage":      lambda p: render_steel_tonnage(material.steel_items, p, theme),
        "concrete_vs_rebar":  lambda p: render_concrete_vs_rebar(material.concrete_m3, material.rebar_mt, p, theme),
    }
    out = {}
    for key, fn in jobs.items():
        path = os.path.join(charts_dir, f"{key}.{ext}")
        try:
            out[key] = fn(path)
        except Exception as exc:   # pragma: no cover - defensive
            logger.warning("Chart '%s' could not be generated: %s", key, exc)
            out[key] = None
    return out
