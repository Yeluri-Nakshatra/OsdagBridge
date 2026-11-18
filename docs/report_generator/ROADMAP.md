# OsdagBridge Report Generator — Refactoring Roadmap

Scope: `src/osdagbridge/core/reports/` (FOSSEE / IIT Bombay screening task:
*LaTeX Report Generator Refactoring & Enhancements*).

The report is assembled as a LaTeX string from ten chapter modules and compiled
with `pdflatex`. The baseline has six classes of problems:

| # | Problem in baseline | Where it shows |
|---|---------------------|----------------|
| 1 | Tables split across pages without repeating their header row | Chapters 2, 3, 5, 7 (`longtable` used without `\endfirsthead`/`\endhead`) and `tabular` inside `table[H]` (cannot break at all) |
| 2 | Rows bleed into the footer; "* Software default value" note collides with footer | `\fancyfoot` built with negative `\vspace` hacks, no `footskip`/`headheight` in geometry, `\[6pt]` padding hacks |
| 3 | Live loads and footpath load merged into one two-column list | Chapter 3 "Live Loads (LL)" |
| 4 | No visual summary of utilisation ratios | Section 5.5 |
| 5 | No visual summary of material quantities | Chapter 7 |
| 6 | Fonts, colours, paddings, column widths, `\setlength` calls scattered in every chapter | every chapter file |

## Target architecture

```
core/reports/
├── styles.py          SINGLE SOURCE OF TRUTH — page geometry, typography, colour palette,
│                      table style, header/footer theme, figure sizes, chart theme.
│                      Emits the LaTeX preamble fragments from these values.
├── latex_builders.py  Table / figure toolkit (LongTable, KeyValueTable, figure blocks,
│                      status + UR cells) — every chapter builds tables through it, so
│                      header repetition, padding and colours are applied in one place.
├── charts.py          matplotlib (Agg) chart generators → PNG assets (UR charts, material charts).
├── summary_data.py    Pure data extraction: utilisation ratios of girders / deck / cross
│                      bracing / end diaphragms, material quantities (no LaTeX, unit-testable).
├── loads_data.py      Pure data extraction: live-load vehicle rows and footpath rows from
│                      the UI "Loading" tab keys + IRC 6 helpers.
├── report_generator.py Orchestrator: preamble/title/TOC from styles, chart asset step,
│                      chapter calls, two pdflatex passes (unchanged public API).
└── chapN.py, executive_summary.py  Thin presentation modules: data → builders.
```

Design rules
1. **No formatting literals in chapter files.** Column widths, colours, fonts,
   paddings and spacing all come from `styles.py` (`ReportTheme`).
2. **Every table is a `longtable`** emitted by `LongTable`, which always writes
   `\endfirsthead` / `\endhead` / `\endfoot` / `\endlastfoot`, so header rows
   repeat on every page and a "continued on next page" cue is printed.
3. **Grouped rows never break.** Multirow groups (per girder, per bracing panel)
   use `\*` so a girder's block is kept together.
4. **Charts are data-driven.** `summary_data.py` returns plain lists of
   `(label, ur)`; `charts.py` draws them; the chapter only embeds the PNG.
5. **Headless, reproducible verification.** `tools/report_preview.py` renders
   the report from a fixture without the GUI or the solver.

## Milestones

| Milestone | Deliverable | Acceptance check |
|-----------|-------------|------------------|
| M1 Style system | `styles.py`, preamble emitted from it | grep: no `\setlength`, `\definecolor`, `L{..cm}` literals left in `chap*.py` |
| M2 Table toolkit | `latex_builders.py` + unit tests | every generated longtable contains `\endfirsthead` and `\endhead` |
| M3 Layout fixes | geometry (`headheight`, `headsep`, `footskip`), footer theme, `\raggedbottom`, row padding | footer never overlapped; no `fancyhdr` headheight warnings in the log |
| M4 Chapter 3 | separate *Vehicle Live Loads* and *Footpath Live Load* tables with unit columns, vehicles from the UI selection | rows == selected vehicles; braking/impact/centrifugal columns filled |
| M5 UR charts | `summary_data.py`, `charts.py`, Section 5.5 figures | red dashed `UR = 1.0` line, pass/fail colouring, all four components |
| M6 Material charts | Chapter 7 steel tonnage + concrete vs rebar charts | PNGs auto-saved into the temp asset dir and embedded |
| M7 Harness & tests | `tools/report_preview.py`, fixture, `tests/unit/test_report_*.py` | `pytest tests/unit -k report` green; PDF compiles with 0 errors |
| M8 Deliverables | `Report_Before.pdf`, `Report_After.pdf`, `TECHNICAL_CHANGES.md` | both PDFs produced from the same fixture |

## Out of scope
* Changing design/analysis logic or `output_dict` keys produced by the engine.
* GUI changes (report options dialog) — the public `generate_report()` /
  `build_report_payload()` API is kept byte-for-byte compatible.
