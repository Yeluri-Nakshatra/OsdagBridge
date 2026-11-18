#!/usr/bin/env python
# =============================================================================
# OsdagBridge — Headless report preview
# =============================================================================
# Renders the full design report (TeX + PDF) from the sample fixture without
# launching the GUI, OpenSees or the CAD kernel.  Used to verify report-layout
# changes quickly and to produce the Before/After comparison PDFs.
#
#   python tools/report_preview.py --out build/report
#   python tools/report_preview.py --src ../OsdagBridge-baseline/src --out build/before --stem Report_Before
#   python tools/report_preview.py --out build/after --render        # also PNG pages
#
# Options
#   --src DIR       alternative `src` directory to import `osdagbridge` from
#                   (lets the *baseline* generator run against the same fixture)
#   --out DIR       output directory (default build/report)
#   --stem NAME     file stem for the .tex/.pdf (default Report)
#   --latex-bin DIR directory containing pdflatex (prepended to PATH)
#   --render        rasterise every PDF page to PNG (requires pypdfium2)
#   --no-figures    skip the synthetic figures (placeholders are printed)
# =============================================================================
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def _default_latex_bin() -> str | None:
    cands = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "MiKTeX", "miktex", "bin", "x64"),
        r"C:\Program Files\MiKTeX\miktex\bin\x64",
        "/usr/local/texlive/2024/bin/x86_64-linux",
        "/usr/bin",
    ]
    for c in cands:
        if c and (os.path.exists(os.path.join(c, "pdflatex.exe")) or os.path.exists(os.path.join(c, "pdflatex"))):
            return c
    return None


def _shim_solver_imports() -> None:
    """Install no-op stand-ins for OpenSees when the native solver cannot load.

    Some engine modules import `openseespy.opensees` at module level even
    though the report never calls the solver.  The shim keeps the headless
    preview usable on machines without a working OpenSees build (e.g. Python
    versions without wheels).  It is only used by this tool, never by the app.
    """
    import types
    try:
        import openseespy.opensees  # noqa: F401
        return
    except Exception:
        pass

    class _Stub(types.ModuleType):
        def __getattr__(self, name):            # any ops.* call → no-op
            if name.startswith("__"):
                raise AttributeError(name)
            return lambda *a, **k: None

    pkg = _Stub("openseespy")
    ops = _Stub("openseespy.opensees")
    pkg.opensees = ops
    sys.modules["openseespy"] = pkg
    sys.modules["openseespy.opensees"] = ops
    print("NOTE: openseespy could not be loaded; using a no-op shim for the headless preview.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default=str(REPO / "src"))
    ap.add_argument("--out", default=str(REPO / "build" / "report"))
    ap.add_argument("--stem", default="Report")
    ap.add_argument("--latex-bin", default=_default_latex_bin())
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--no-figures", action="store_true")
    args = ap.parse_args(argv)

    src = str(Path(args.src).resolve())
    sys.path.insert(0, src)
    sys.path.insert(0, str(HERE))          # tools/report_fixture.py
    if args.latex_bin:
        os.environ["PATH"] = args.latex_bin + os.pathsep + os.environ.get("PATH", "")

    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    _shim_solver_imports()

    from osdagbridge.core.reports.report_generator import (  # noqa: E402
        ReportMetadata, ReportOptions, ReportRequest, build_report_payload, generate_report,
    )
    import report_fixture  # noqa: E402

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    meta = ReportMetadata(
        project_name="Mithi River Crossing — Bridge No. 7",
        project_location="Mumbai Suburban, Maharashtra",
        designer="R. Sharma",
        client="Public Works Department, Govt. of Maharashtra",
        company="Osdag Bridge Design Cell, IIT Bombay",
        group_name="",
        subtitle="Rev 1",
        job_number="OSB-2026-007",
        additional_comments="",
        logo_path=None,
        report_date="2026-11-18",
        reviewer="A. Verma",
    )
    options = ReportOptions(
        sections=["loads", "analysis", "design_checks", "drawings"],
        include_figures=True, include_toc=True, include_pdf=True,
    )
    request = ReportRequest(metadata=meta, options=options, output_dir=str(out_dir), file_stem=args.stem)

    inputs = report_fixture.build_input_dict()
    outputs = report_fixture.build_output_dict()
    payload = build_report_payload(request, inputs, outputs)
    if not args.no_figures:
        payload.figure_data = report_fixture.build_figure_data()

    t0 = time.time()
    result = generate_report(payload, request)
    dt = time.time() - t0
    print(f"TeX: {result.tex_path}")
    print(f"PDF: {result.pdf_path}  ({dt:.1f}s)")

    if result.pdf_path and args.render:
        render_pages(result.pdf_path, out_dir / "pages")
    return 0 if result.pdf_path else 1


def render_pages(pdf_path: str, pages_dir: Path, scale: float = 1.4) -> list[str]:
    """Rasterise each PDF page to PNG (for visual regression checks)."""
    import pypdfium2 as pdfium
    pages_dir.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(pdf_path)
    out = []
    for i in range(len(pdf)):
        page = pdf[i]
        img = page.render(scale=scale).to_pil()
        p = pages_dir / f"page_{i + 1:03d}.png"
        img.save(p)
        out.append(str(p))
    print(f"Rendered {len(out)} page(s) to {pages_dir}")
    return out


if __name__ == "__main__":
    raise SystemExit(main())
