# =============================================================================
# Unit tests — report generator refactor (styles, builders, data, charts)
# =============================================================================
# Run:  pytest tests/unit/test_report_generator.py -q
# No LaTeX compiler is required: the tests assert on the generated LaTeX
# source and on the chart PNGs.  The optional end-to-end PDF test runs only
# when `pdflatex` is on PATH.
# =============================================================================
from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))

from osdagbridge.core.reports import styles                                  # noqa: E402
from osdagbridge.core.reports.latex_builders import (                        # noqa: E402
    Cell, Column, KeyValueTable, LongTable, figure_block, status_cell, ur_cell,
)
from osdagbridge.core.reports import summary_data, loads_data, charts       # noqa: E402
from osdagbridge.core.reports.report_generator import (                     # noqa: E402
    ReportMetadata, ReportOptions, ReportRequest, ReportDataBridge,
    build_report_payload, assemble_document, preamble,
)
import report_fixture                                                        # noqa: E402

CHAPTER_FILES = [REPO / "src" / "osdagbridge" / "core" / "reports" / f
                 for f in ("executive_summary.py", "chap1.py", "chap2.py", "chap3.py", "chap4.py",
                           "chap5.py", "chap6.py", "chap7.py", "chap8.py", "chap9.py")]


@pytest.fixture(scope="module")
def inputs():
    return report_fixture.build_input_dict()


@pytest.fixture(scope="module")
def outputs():
    return report_fixture.build_output_dict()


# ─────────────────────────────────────────────────────────────────────────────
# styles.py — single source of truth
# ─────────────────────────────────────────────────────────────────────────────
def test_preamble_contains_geometry_and_colours():
    pre = styles.latex_preamble("L", "R")
    assert "headheight=" in pre and "footskip=" in pre and "headsep=" in pre
    for name, _ in (styles.THEME.palette.primary, styles.THEME.palette.pass_, styles.THEME.palette.fail):
        assert rf"\definecolor{{{name}}}" in pre
    assert r"\statusPass" in pre and r"\urFail" in pre
    assert r"\endfirsthead" not in pre            # preamble holds no tables
    assert "vspace{-" not in pre                  # no negative-space footer hacks


def test_footer_legend_lives_inside_footer_band():
    pre = styles.latex_preamble("L", "R")
    assert r"\fancyfoot[L]" in pre and "hasSDonPage" in pre
    assert styles.THEME.header_footer.software_default_note in pre


def test_chapters_have_no_hardcoded_formatting():
    """Chapter files must consume formatting from styles / builders only."""
    banned = [r"\setlength", r"\definecolor", r"\begin{tabular}", r"\begin{table}",
              r"\\[6pt]", r"\\[8pt]", r"\fancyhead", r"\titleformat"]
    for f in CHAPTER_FILES:
        text = f.read_text(encoding="utf-8")
        for b in banned:
            assert b not in text, f"{f.name} contains formatting literal {b!r}"
        assert not re.search(r"[LCR]\{\d+(\.\d+)?cm\}", text), f"{f.name} contains a raw column spec"


# ─────────────────────────────────────────────────────────────────────────────
# latex_builders.py
# ─────────────────────────────────────────────────────────────────────────────
def test_longtable_repeats_header_and_has_continuation_cues():
    t = LongTable([Column(3, "l", "A"), Column(4, "c", "B")], caption="Cap", label="tab:x")
    t.add_row(["1", "2"])
    tex = t.render()
    assert tex.count(r"\textbf{A}") == 2            # first head + running head
    assert r"\endfirsthead" in tex and r"\endhead" in tex
    assert r"\endfoot" in tex and r"\endlastfoot" in tex
    assert "Continued on next page" in tex
    assert "(continued)" in tex
    assert r"\label{tab:x}" in tex
    assert r"\rowcolor{osdagHeaderFill}" in tex


def test_longtable_groups_are_kept_together():
    t = LongTable([Column(2, "c", "G"), Column(4, "l", "P"), Column(3, "c", "V")])
    t.add_group("G1", [["a", "1"], ["b", "2"], ["c", "3"]])
    tex = t.render()
    assert r"\multirow{3}{=}{G1}" in tex
    assert tex.count(r"\\*") == 2 and r"\cline{2-3}" in tex
    assert tex.rstrip().endswith(r"\end{longtable}")


def test_stacked_header_with_spans():
    t = LongTable([Column(2, "c"), Column(2, "c"), Column(2, "c"), Column(2, "c")],
                  header=[[Cell("Id", rowspan=2, bold=True), Cell("Group", colspan=3, bold=True)],
                          [None, "a", "b", "c"]])
    tex = t.render()
    assert r"\multicolumn{3}{c|}{\textbf{Group}}" in tex
    assert r"\multirow{-2}{=}{\textbf{Id}}" in tex       # span placed in LAST row (colortbl-safe)
    assert r"\cline{2-4}" in tex


def test_longtable_unnumbered_caption():
    t = LongTable([Column(2, "l", "A")], caption="Table 1 -- X", numbered=False)
    t.add_row(["v"])
    tex = t.render()
    assert r"\caption*{Table 1 -- X}" in tex and r"\caption{" not in tex


def test_key_value_table_widths_fit_text_width():
    t = KeyValueTable(caption="C", rows=[("p", "v")])
    total = sum(c.width_cm for c in t.columns)
    assert total <= styles.THEME.page.text_width_cm - 0.7


def test_status_and_ur_cells():
    assert status_cell(True) == r"\statusPass"
    assert status_cell(False) == r"\statusFail"
    assert status_cell(None) == r"\statusNA"
    assert ur_cell(0.874) == "0.87"
    assert ur_cell(1.03) == r"\urFail{1.03}"
    assert ur_cell("n/a") == "---"


def test_figure_block_placeholder_and_image():
    assert "PLACEHOLDER" in figure_block(None, "Cap")
    tex = figure_block("charts/a.png", "Cap", label="fig:a")
    assert r"\includegraphics" in tex and "charts/a.png" in tex and r"\label{fig:a}" in tex


# ─────────────────────────────────────────────────────────────────────────────
# summary_data.py
# ─────────────────────────────────────────────────────────────────────────────
def test_collect_utilization_four_components(outputs, inputs):
    comps = summary_data.collect_utilization(outputs, inputs)
    assert [c.key for c in comps] == ["girder", "deck", "bracing", "diaphragm"]
    girder, deck, cb, ed = comps
    assert girder.max_ur == pytest.approx(0.882, abs=1e-3)      # total deflection 44.1 / 50
    assert girder.governing_item.label in ("Deflection", "SLS stress")
    assert deck.max_ur == pytest.approx(0.91, abs=1e-3)         # overhang flexure
    assert cb.max_ur is not None and ed.max_ur is not None
    assert all(c.status == "PASS" for c in comps)
    assert any(i.label == "Slenderness" for i in cb.items)


def test_collect_utilization_handles_missing_results():
    comps = summary_data.collect_utilization({}, {})
    assert len(comps) == 4
    assert all(c.max_ur is None for c in comps)
    assert all(c.note for c in comps)


def test_girder_fallback_to_percent_keys():
    from osdagbridge.core.utils.common import KEY_UTIL_FLEXURE, KEY_UTIL_SHEAR
    comp = summary_data.girder_urs({KEY_UTIL_FLEXURE: "81.4", KEY_UTIL_SHEAR: "120"})
    assert comp.max_ur == pytest.approx(1.2)
    assert comp.status == "FAIL"


def test_material_quantities(inputs, outputs):
    from osdagbridge.core.boq.boq_generator import calculate_material_quantities
    inp = dict(inputs)
    inp.update(calculate_material_quantities(inp, outputs))
    mat = summary_data.collect_material_quantities(inp, outputs)
    labels = [l for l, _ in mat.steel_items]
    assert labels == ["Plate Girders", "Cross Bracing", "End Diaphragms"]
    assert mat.concrete_m3 == pytest.approx(82.5, abs=0.01)
    assert mat.rebar_mt == pytest.approx(9.9, abs=0.01)
    assert mat.end_diaphragm and mat.end_diaphragm["qty"] == 16
    assert mat.total_steel_mt > 35


# ─────────────────────────────────────────────────────────────────────────────
# loads_data.py
# ─────────────────────────────────────────────────────────────────────────────
def test_vehicle_rows_follow_ui_selection(inputs):
    rows = loads_data.vehicle_rows(inputs)
    names = [r.name for r in rows]
    assert names == ["Class A", "Class 70R (Wheeled)", "Class 70R (Tracked)", "Class SV", "Class Fatigue"]
    class_a = rows[0]
    assert class_a.total_load_kN == pytest.approx(543.47, abs=0.1)     # 55.4 t × 9.81
    assert class_a.impact_factor == pytest.approx(1.207, abs=1e-3)      # 1 + 9/(13.5+30)
    assert class_a.braking_considered and class_a.braking_kN == pytest.approx(0.2 * 543.47, abs=0.1)
    assert class_a.braking_eccentricity_m == 1.2
    sv = [r for r in rows if r.name == "Class SV"][0]
    assert sv.impact_factor is None and not sv.braking_considered   # KEY_BL_IRC_CLASS_SV = False
    assert sv.total_load_kN == pytest.approx(3776.9, abs=0.5)


def test_vehicle_rows_empty_when_nothing_selected():
    assert loads_data.vehicle_rows({}) == []


def test_braking_force_total_two_lanes(inputs):
    rows = loads_data.vehicle_rows(inputs)
    total, basis = loads_data.braking_force_total_kN(inputs, rows)
    assert total == pytest.approx(0.30 * 981.0, abs=0.1)              # 20 % + 10 % of 70R(W)
    assert "2 lane" in basis


def test_footpath_rows(inputs):
    rows = dict(loads_data.footpath_rows(inputs))
    assert rows["Footpath Provided"] == "Both Sides"
    assert "kN/m" in rows["Footway Live Load Intensity, $P$"]
    assert "IRC 6" in rows["Basis"]


# ─────────────────────────────────────────────────────────────────────────────
# charts.py
# ─────────────────────────────────────────────────────────────────────────────
def test_charts_are_rendered(tmp_path, inputs, outputs):
    from osdagbridge.core.boq.boq_generator import calculate_material_quantities
    inp = dict(inputs)
    inp.update(calculate_material_quantities(inp, outputs))
    comps = summary_data.collect_utilization(outputs, inp)
    mat = summary_data.collect_material_quantities(inp, outputs)
    paths = charts.generate_report_charts(comps, mat, str(tmp_path))
    assert set(paths) == {"ur_overview", "ur_detail", "steel_tonnage", "concrete_vs_rebar"}
    for key, p in paths.items():
        assert p and os.path.exists(p), key
        assert os.path.getsize(p) > 5_000


def test_charts_degrade_gracefully(tmp_path):
    comps = summary_data.collect_utilization({}, {})
    mat = summary_data.MaterialSummary()
    paths = charts.generate_report_charts(comps, mat, str(tmp_path))
    assert all(v is None for v in paths.values())


# ─────────────────────────────────────────────────────────────────────────────
# Full document assembly (no compiler)
# ─────────────────────────────────────────────────────────────────────────────
def _request(tmp_path):
    meta = ReportMetadata(project_name="P & Q", project_location="Loc", designer="D", client="C",
                          company="Org", subtitle="Rev 2", job_number="J_1", report_date="2026-11-18")
    opts = ReportOptions(sections=["loads", "analysis", "design_checks", "drawings"],
                         include_figures=True, include_toc=True, include_pdf=True)
    return ReportRequest(metadata=meta, options=opts, output_dir=str(tmp_path), file_stem="Report")


def test_assemble_document(tmp_path, inputs, outputs):
    from osdagbridge.core.boq.boq_generator import calculate_material_quantities
    req = _request(tmp_path)
    payload = build_report_payload(req, dict(inputs), dict(outputs))
    payload.inputs.update(calculate_material_quantities(payload.inputs, payload.output_dict))
    comps = summary_data.collect_utilization(payload.output_dict, payload.inputs)
    mat = summary_data.collect_material_quantities(payload.inputs, payload.output_dict)
    charts_ = {"paths": {"ur_overview": "charts/ur_overview.png", "ur_detail": "charts/ur_detail.png",
                         "steel_tonnage": "charts/steel.png", "concrete_vs_rebar": "charts/conc.png"},
               "components": comps, "material": mat}
    tex = assemble_document(payload, {}, None, None, charts_)

    assert tex.startswith(r"\documentclass") and tex.rstrip().endswith(r"\end{document}")
    assert r"\begin{tabular}" not in tex                     # every table is a longtable
    n_tables = tex.count(r"\begin{longtable}")
    assert n_tables >= 50
    assert tex.count(r"\endfirsthead") == n_tables and tex.count(r"\endhead") == n_tables
    # Chapter 3: separate vehicle and footpath tables, vehicles as selected in the UI
    assert "Vehicle Live Loads" in tex and "Footpath Live Load" in tex
    assert "Class 70R (Wheeled)" in tex and "Class AA (Wheeled)" not in tex
    # Section 5.5 charts and Chapter 7 charts embedded
    assert "charts/ur_overview.png" in tex and "charts/ur_detail.png" in tex
    assert "charts/steel.png" in tex and "charts/conc.png" in tex
    # End diaphragm section uses its own section (L 110 ...) not the cross-bracing one
    assert "L 110 x 110 x 10" in tex
    # metadata escaped
    assert r"P \& Q" in tex and r"J\_" in tex


def test_report_data_bridge_kinds(outputs, inputs):
    b = ReportDataBridge(outputs, inputs, None)
    assert b.get_cb_pairs("cb") == ["G1-G2", "G2-G3"]
    assert b.get_cb_section("G1-G2", "diagonal", "compression", "cb") == "L 100 x 100 x 10"
    assert b.get_cb_section("G1-G2", "diagonal", "compression", "ed") == "L 110 x 110 x 10"
    assert b.get_cb_status("G1-G2", "diagonal", "compression", "ed") == r"\statusPass"


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex not on PATH")
def test_end_to_end_pdf(tmp_path, inputs, outputs):
    from osdagbridge.core.reports.report_generator import generate_report
    req = _request(tmp_path)
    payload = build_report_payload(req, dict(inputs), dict(outputs))
    result = generate_report(payload, req)
    assert result.pdf_path and os.path.exists(result.pdf_path)
    log = (tmp_path / "Report.log").read_text(encoding="utf-8", errors="ignore")
    assert "! " not in log.replace("!  ", "")          # no LaTeX errors
