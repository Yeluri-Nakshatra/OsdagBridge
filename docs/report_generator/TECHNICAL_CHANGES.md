# OsdagBridge LaTeX Report Generator — Technical Changes

Screening task: *LaTeX Report Generator Refactoring & Enhancements* (FOSSEE, IIT Bombay).
All work is confined to `src/osdagbridge/core/reports/` plus a headless preview tool,
a fixture and unit tests. The public API (`build_report_payload`, `generate_report`,
`ReportRequest`, `ReportPayload`, …) is unchanged, so the desktop GUI needs no edits.

Deliverables in this folder:

| File | Purpose |
|------|---------|
| `Report_Before.pdf` | Baseline generator (`dev` @ `d74f56d`) rendered from the sample fixture |
| `Report_After.pdf` | Refactored generator rendered from the **same** fixture |
| `ROADMAP.md` | Plan, architecture and acceptance criteria |
| `TECHNICAL_CHANGES.md` | This document |

---

## 1. Summary of what changed

| # | Task item | What was done |
|---|-----------|---------------|
| 1 | Repeated table headers across page breaks | Every table (56 in the sample report) is now a `longtable` emitted by one builder that always writes `\endfirsthead` / `\endhead` / `\endfoot` / `\endlastfoot`. Header rows repeat on every page, the running caption reads "Table n.m: … (continued)" and a "Continued on next page" cue is printed. `tabular` inside `table[H]` (which cannot break at all) no longer exists in the report. |
| 2 | Footer overlap / vertical spacing | Page geometry now declares `headheight`, `headsep` and `footskip`; the footer is a two-line `\parbox` **inside** the footer band (organisation + page number, and the "* Software default value" legend only on pages that need it). The baseline implemented the legend with `\vspace{-20pt}` inside `\footrule`, which pushed rows into the footer. Row padding is now `\arraystretch` + `\extrarowheight` (no more `\\[6pt]` hacks), `\raggedbottom` is set, grouped rows are glued with `\\*`, and figures are protected with `\needspace`. |
| 3 | Load & geometry table refactoring (Chapter 3) | Live loads are split into **Table 3.3 Vehicle Live Loads** (one row per vehicle ticked in the *Loading* tab: total load kN, impact factor, braking considered? / value / eccentricity, centrifugal force) and **Table 3.4 Footpath Live Load**. Chapter 3 is also organised into Permanent / Live / Environmental loads / Load combinations sections. |
| 4 | Utilisation-ratio charts (Section 5.5) | Two matplotlib charts are generated during report generation and embedded as Figures 5.1 and 5.2: governing UR per primary element, and UR of every design check in a 2 × 2 panel (girders, deck slab, cross bracing, end diaphragms). Both carry the red dashed `UR = 1.0` line; failing bars are drawn in red. A "Governing UR per element" table accompanies them. |
| 5 | Material quantity charts (Chapter 7) | Figure 7.1 structural steel tonnage (girders, cross bracing, end diaphragms) and Figure 7.2 concrete volume (m³) vs reinforcement steel (MT) on twin axes. PNGs are written to a temporary `charts/` asset folder and embedded with the figure builder. |
| 6 | Centralised style system | `styles.py` is the single source of truth (page geometry, palette, typography, table style, header/footer theme, figure sizes, chart theme). The whole LaTeX preamble is *generated* from it. Chapter files contain no `\setlength`, `\definecolor`, column-width or colour literals — this is enforced by a unit test. |

### Extra polish
* End-diaphragm tables (Section 5.4) now read the end-diaphragm results; the baseline printed the cross-bracing data under the end-diaphragm headings.
* The Executive Summary's *Key Design Outcomes* is a real table (component, governing check, max UR, status) computed from results instead of four hard-coded "pass" lines; the overall status/UR in the Project Overview is derived from all four components.
* Chapter 7 gains an *End Diaphragms* BOQ row and a total-steel line.
* Section 5.5 "Transverse shear (slab)" row is filled from the design results (was always "—").
* Status cells use themed macros (`\statusPass` / `\statusFail` / `\statusWarn`), failing URs are red, header rows are tinted, section rows inside tables are shaded.
* `pdflatex` is run a third time automatically when the log asks for a rerun; the `.log` is copied next to the PDF for diagnostics.
* The empty placeholder table "Reactions at Supports" in Chapter 4 was removed (its content is already in Table 4.1).
* Headless preview tool and 22 unit tests (see §5).

---

## 2. Files altered / added under `src/osdagbridge/core/reports/`

| File | Status | Notes |
|------|--------|-------|
| `styles.py` | **new** | `ReportTheme` dataclasses + `latex_preamble()` emitters (geometry, packages, colours, table lengths, macros, page styles, headings) |
| `latex_builders.py` | **new** | `Column`, `Cell`, `LongTable`, `KeyValueTable`, `status_cell`, `ur_cell`, `figure_block`, `figure_row`, `table_note` |
| `charts.py` | **new** | `render_ur_overview`, `render_ur_detail`, `render_steel_tonnage`, `render_concrete_vs_rebar`, `generate_report_charts` |
| `summary_data.py` | **new** | `collect_utilization()` → 4 × `ComponentUR`; `collect_material_quantities()` → `MaterialSummary`; `end_diaphragm_quantities()`; `extract_member_summary()` |
| `loads_data.py` | **new** | `vehicle_rows()`, `footpath_rows()`, `braking_force_total_kN()`, `selected_vehicles()` |
| `report_generator.py` | rewritten orchestration | preamble/title/TOC from `styles`; `_render_charts()`; `assemble_document()` (pure, testable); `ReportDataBridge` helpers take `kind="cb"|"ed"`; rerun-aware compile loop |
| `report_utils.py` | modified | figure helpers delegate to the builders; `_tex` also maps `–`, `—`, `°` |
| `executive_summary.py` | rewritten | builder tables, unnumbered captions (no "Table 0.x"), data-driven outcomes |
| `chap1.py` … `chap9.py` | rewritten (chap9 unchanged) | all tables through `LongTable` / `KeyValueTable`; `chap3` new live-load tables; `chap5` Section 5.5 charts; `chap7` charts + ED row |
| `templates/default_template.tex` | unchanged | |

Outside the package:

| File | Purpose |
|------|---------|
| `tools/report_preview.py` | Headless generator: fixture → `.tex` + `.pdf` (+ PNG pages). `--src` lets the baseline code run on the same fixture. |
| `tools/report_fixture.py` | Sample `input_dict` / `output_dict` mirroring the engine's key scheme, plus synthetic figures |
| `tests/unit/test_report_generator.py` | 22 unit tests + optional end-to-end PDF test |
| `docs/report_generator/*` | roadmap, this document, Before/After PDFs |

---

## 3. Structure of the centralised style module (`styles.py`)

```
ReportTheme (frozen dataclass)  ──  THEME = ReportTheme()
├── page: PageGeometry        paper, margins, head_height, head_sep, foot_skip,
│                             line_stretch, text_width_cm (drives column widths)
├── palette: Palette          osdagGreen, header_fill, group_fill, pass/warn/fail,
│                             muted, link  + chart colours (girder/deck/bracing/
│                             diaphragm/concrete/rebar/fail/threshold)
├── typography: Typography    size commands for tables (normal/compact/dense),
│                             captions, notes, header/footer, chapter/section titles
├── table: TableStyle         tabcolsep, arraystretch, extrarowheight, rule width,
│                             LTpre/LTpost, caption skip, header fill/bold,
│                             continued texts, keep_groups_together, key-value widths
├── header_footer: HeaderFooterTheme   footer text, page format, rule thickness,
│                             software-default legend
├── figure: FigureStyle       default / wide / chart / envelope / triple widths,
│                             logo height, spacing
└── chart: ChartTheme         dpi, figsize, fonts, bar width, grid alpha,
                              threshold value/style/label, axis headroom

Emitters (pure functions of THEME):
  latex_document_class · latex_geometry · latex_packages · latex_colors ·
  latex_table_lengths · latex_macros · latex_page_styles(header_left, header_right) ·
  latex_headings · latex_preamble(...)   ← used by report_generator.preamble()
```

Changing e.g. `TableStyle.array_stretch` or `Palette.primary` restyles every
table / rule / chart in the report. Chapter modules only call builders
(`LongTable(...)`, `KeyValueTable(...)`, `figure_block(...)`) and semantic macros
(`\statusPass`, `\urFail{}`, `\tableNote{}`), which the preamble defines.

---

## 4. Key LaTeX / code decisions and rationale

**Builder instead of PyLaTeX.** The repository's generator assembles raw LaTeX
strings; PyLaTeX is not a dependency (no import, not in `environment.yml` or the
conda recipe). The task allows "LaTeX longtable headers with `\endhead` and
`\endfirsthead`" as the alternative, so a small dependency-free `LongTable`
builder was written. It gives the same abstraction level as PyLaTeX's
`LongTable` while supporting what the report actually needs — stacked headers
with row/column spans, shaded header rows, continued captions, `\\*` row
gluing — without adding a runtime package to the Osdag conda environment.

**No new LaTeX packages.** The preamble uses exactly the packages the baseline
already loaded, so the report keeps compiling with the TeX distribution bundled
by `osdag_latex_env`.

**Stacked headers that survive `\rowcolor`.** Row-spanning header cells are
rendered as `\multirow{-n}{=}{…}` in the *last* spanned row (colortbl otherwise
paints over the text), and `\multirowsetup` is set to `\centering` so the text
wraps inside the paragraph column.

**Why no `\needspace` before tables.** The baseline (and a first iteration of
this refactor) used `\needspace` before every table. A reproducible experiment
(`pdflatex`, same fixture) showed that stretchable glue in front of a
`longtable` makes `\LT@start` emit a foot-only page followed by the running head
*and* the first head on the next page. longtable's own start-up logic already
moves a table whose head + first row do not fit, so the hook was removed;
figures keep theirs.

**Footer inside the footer band.** `footskip=34pt` with a 28 mm bottom margin
leaves room for the two-line footer; the "* Software default value" legend is
rendered by `\fancyfoot[L]` conditional on the per-page `hasSDonPage` flag (set
by `\sdstar`, reset at shipout), so neither the text block nor the rule moves.

**Data layer separated from presentation.** `summary_data.py` and
`loads_data.py` read the engine's `output_dict` / `input_dict` and return plain
dataclasses; they do not recalculate design values (the UR charts show exactly
the numbers printed in the Chapter 5 tables). They are unit-tested without
LaTeX or matplotlib.

**Solver decoupling.** `_extract_osdag_summary` lives in `results_data.py`,
which imports OpenSees at module level. The report package now has its own
equivalent (`summary_data.extract_member_summary`) so report generation never
imports the solver.

**Vehicle loads in kN.** The IRC 6 vehicle definitions in `irc6_2017.py` are
expressed in the `keyfile` unit system (`t = kN·g`, `kN = 1000·N`), i.e. in
newtons. `loads_data` divides by the `kN` constant so the table prints
kilonewtons (Class A train = 543.5 kN). Braking per vehicle is 20 % of the
train load (IRC 6 Cl. 211.2, first lane); the design braking force for the
lane count follows the 20 % + 10 % + 5 %·(n−2) rule.

---

## 5. Verification

* `python tools/report_preview.py --out build/after --render` — compiles the
  full report from the fixture in ≈ 13 s (MiKTeX, pdflatex) with **0 LaTeX
  errors**, no "rerun" warnings and a single remaining overfull line (a long
  bulleted sentence in Chapter 8, inherited text).
* `python tools/report_preview.py --src ../OsdagBridge-baseline/src --out build/before --stem Report_Before`
  produced `Report_Before.pdf` from the untouched `dev` branch with the same
  fixture, so the two PDFs are directly comparable.
* `pytest tests/unit/test_report_generator.py` — 22 tests: style emitters,
  builder output (header repetition, continuation cues, grouped rows, spans,
  unnumbered captions), UR / material extraction, live-load rows, chart
  rendering and graceful degradation, full-document assembly invariants
  (every table is a longtable with `\endfirsthead`/`\endhead`, no `tabular`),
  `ReportDataBridge` kinds, and an end-to-end PDF test when `pdflatex` is
  available.

### Environment note
The solver wheel (`openseespy`) does not load on the Python used for this work,
so the GUI pipeline could not be run end-to-end here; the Before/After PDFs
were generated headlessly from `tools/report_fixture.py`, which reproduces the
engine's `input_dict` / `output_dict` key scheme for a 30 m, three-girder,
two-lane composite plate-girder bridge. The preview tool installs a no-op
OpenSees shim only when the real module cannot be imported; the application
code path is unaffected.

### Observation outside the task scope (not changed)
`boq_generator.calculate_material_quantities` treats
`member_properties.girder_details.section_properties.area` as m² although the
engine stores it in cm²; when that key is present the "Volume" column of Table
7.1 is overstated by 10⁴ (weights are computed from mass per metre and are
correct). The fixture omits the key so the BOQ derives the area from the plate
dimensions.
