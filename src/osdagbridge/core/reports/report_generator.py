# =============================================================================
# OsdagBridge — Report Generator (orchestration entry point)
# =============================================================================
#   • Full title page with logo
#   • Numbered TOC (Executive Summary + Chapters 1-9)
#   • Executive Summary, Chapters 1–8 and References
#
# All layout rules (page geometry, colours, fonts, table style, header/footer,
# figure and chart themes) live in `styles.py` — the single source of truth.
# Tables are produced through `latex_builders.LongTable` so every table
# repeats its header on page breaks.  Charts for Section 5.5 and Chapter 7
# are rendered by `charts.py` from the data extracted in `summary_data.py`.
# =============================================================================
#
#   FLOW OF REPORT GENERATION
#   ──────────────────────────────────────────────────────────────────────────
#   USER CLICKS "Generate Report"
#     [output_dock.py] OutputDock._on_report_clicked()
#       └─► [template_page.py] CustomWindow.open_report_dialog(cad_generator)
#             ├── ReportOptionsDialog → ReportRequest
#             └─► _ReportWorker.run()
#                   └─► [plategirderbridge.py] PlateGirderBridge.generate_design_report()
#                         ├── build_report_payload(request, inputs, outputs) → ReportPayload
#                         ├── payload.figure_data = {attr: png bytes}
#                         └─► generate_report(payload, request)
#                               ├── discovers pdflatex (OsdagLatexEnv or PATH)
#                               ├── writes figures / logos / charts into a temp dir
#                               ├── assembles the LaTeX document (styles + chapters)
#                               ├── runs pdflatex twice (TOC, page refs)
#                               └── copies <stem>.pdf / <stem>.tex to output_dir
# =============================================================================

import os, shutil, logging, datetime, tempfile, subprocess
from dataclasses import dataclass, field
from typing import Optional, List

from osdagbridge.core.utils.common import (
    KEY_DESIGN_MODE,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE
)

from osdagbridge.core.reports.report_utils import _tex
from .styles import THEME, latex_preamble
from .latex_builders import LongTable, Column
from .executive_summary import executive_summary
from .chap1 import ch1_project_info
from .chap2 import ch2_input_parameters
from .chap3 import ch3_loads
from .chap4 import ch4_analysis
from .chap5 import ch5_design_checks
from .chap6 import ch6_drawings
from .chap7 import ch7_quantities
from .chap8 import ch8_design_log
from .chap9 import references

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# PREAMBLE (generated from styles.THEME)
# ═══════════════════════════════════════════════════════════════════════════════

def preamble(project_name, job_number, report_date, report_version='Rev 0'):
    pn, jn, rd, rv = _tex(project_name), _tex(job_number), _tex(report_date), _tex(report_version)
    header_left = pn + r" $|$ " + jn
    header_right = rd + r" $|$ " + rv
    return "\n".join([
        latex_preamble(header_left, header_right, THEME),
        r"\title{\Large\textbf{OsdagBridge} \\ \normalsize Open Source Software for Steel Girder Bridge Design \\ \vspace{2cm} \large Design Report}",
        r"\author{}",
        r"\date{}",
        "",
        r"\begin{document}",
        "",
    ])


# ═══════════════════════════════════════════════════════════════════════════════
# TITLE PAGE
# ═══════════════════════════════════════════════════════════════════════════════

def title_page(m, osdag_logo, org_logo):
    fig = THEME.figure
    if osdag_logo:
        lhs = r'\includegraphics[width=\linewidth,keepaspectratio]{' + osdag_logo.replace('\\', '/') + r'}'
    else:
        lhs = r'\textit{(Osdag Logo)}'
    if org_logo:
        rhs = (r'\includegraphics[width=\linewidth,height=' + fig.logo_height + r',keepaspectratio]{'
               + org_logo.replace('\\', '/') + r'}')
    else:
        rhs = r''

    logos_tex = (r"\noindent" + "\n"
                 r"\begin{minipage}[c]{0.6\textwidth}\raggedright" + "\n" + lhs + "\n" + r"\end{minipage}%" + "\n"
                 r"\hfill" + "\n"
                 r"\begin{minipage}[c]{0.35\textwidth}\raggedleft" + "\n" + rhs + "\n" + r"\end{minipage}" + "\n"
                 r"\\[1cm]" + "\n")

    t = LongTable([Column(4.2, "l"), Column(10.4, "l")], header=[], continued=False)
    for label, value in (
        ("Project Name", m.project_name), ("Project Location", m.project_location),
        ("Author / Designer", m.designer), ("Reviewer", m.reviewer), ("Organization", m.company),
        ("Client Name and Organization", m.client), ("Job Number", m.job_number),
        ("Date", m.report_date), ("Report Version", m.subtitle or ""),
    ):
        t.add_row([r"\textbf{" + label + "}", _tex(value)])

    return "\n".join([
        r"\begin{titlepage}",
        r"\thispagestyle{firstpage}",
        r"\centering",
        r"\vspace*{1.2cm}",
        logos_tex,
        r"{\Huge \textbf{OsdagBridge}}\\[0.3cm]",
        r"{\large Open Source Software for Steel Girder Bridge Design}\\[1.4cm]",
        r"{\Large Design Report}\\[1.2cm]",
        t.render(),
        r"\end{titlepage}",
        "",
    ])


# ═══════════════════════════════════════════════════════════════════════════════
# TOC
# ═══════════════════════════════════════════════════════════════════════════════

def toc_section():
    return "\n".join([r"\newpage", r"\tableofcontents", r"\clearpage", ""])


# ---------------------------------------------------------------------------
# Public data-classes
# ---------------------------------------------------------------------------

@dataclass
class ReportMetadata:
    project_name: str
    project_location: str
    designer: str
    client: str
    company: str
    group_name: str = ''
    subtitle: str = ''
    job_number: str = ''
    additional_comments: str = ''
    logo_path: Optional[str] = None
    report_date: str = ''
    reviewer: str = ''

@dataclass
class ReportOptions:
    sections: List[str]
    include_figures: bool
    include_toc: bool
    include_pdf: bool

@dataclass
class ReportRequest:
    metadata: ReportMetadata
    options: ReportOptions
    output_dir: str
    file_stem: str

@dataclass
class ReportFigures:
    plan:            Optional[str] = None
    cross_section:   Optional[str] = None
    final_geometry:  Optional[str] = None
    longitudinal_elevation: Optional[str] = None
    girder_3d:       Optional[str] = None
    girder_front:    Optional[str] = None
    girder_top:      Optional[str] = None
    girder_end:      Optional[str] = None
    bm_envelope:     Optional[str] = None
    sf_envelope:     Optional[str] = None
    defl_ll:         Optional[str] = None
    shear_connector: Optional[str] = None
    cross_bracing:   Optional[str] = None

@dataclass
class ReportPayload:
    metadata:         ReportMetadata
    options:          ReportOptions
    inputs:           dict
    analysis_summary: dict
    design_checks:    list
    figures:          ReportFigures
    log_entries:      List[str] = field(default_factory=list)
    output_dict:      dict = field(default_factory=dict)
    figure_data:      dict = field(default_factory=dict)  # {attr: bytes} — cleared after writing to tmpdir


@dataclass
class ReportResult:
    pdf_path: Optional[str]
    tex_path: Optional[str]


class ReportDataBridge:
    """Centralized data extraction for the OsdagBridge report.

    The member-design helpers accept ``kind='cb'`` (cross bracing, default)
    or ``kind='ed'`` (end diaphragm) so Chapter 5 can render both member
    sets from their own results.
    """

    _FORCES_KEY = {"cb": "crossbracing_forces_dict", "ed": "end_diaphragm_forces_dict"}
    _DESIGN_KEY = {"cb": "crossbracing_design_results", "ed": "end_diaphragm_design_results"}

    def __init__(self, output_dict: dict, input_dict: dict, payload: "ReportPayload"):
        self.output_dict = output_dict
        self.input_dict = input_dict
        self.payload = payload

    # =====================================================================
    # CHAPTER 5: CROSS BRACING / END DIAPHRAGM
    # =====================================================================

    def _cb_forces_dict(self, kind: str = "cb") -> dict:
        return self.output_dict.get(self._FORCES_KEY.get(kind, "crossbracing_forces_dict"), {}) or {}

    def _cb_pair_designs(self, kind: str = "cb") -> dict:
        return self.output_dict.get(self._DESIGN_KEY.get(kind, "crossbracing_design_results"), {}) or {}

    def _cb_osdag(self, pair: str, member: str, force_type: str, kind: str = "cb") -> dict:
        """Normalised Osdag member-design summary for one member."""
        from .summary_data import extract_member_summary
        try:
            raw = self._cb_pair_designs(kind)[pair][member][force_type]
            return extract_member_summary(raw or {})
        except (KeyError, TypeError):
            return {}

    def get_cb_pairs(self, kind: str = "cb") -> list:
        """Sorted list of girder pair keys e.g. ['G1-G2', 'G2-G3']."""
        try:
            pairs = set(self._cb_forces_dict(kind).get("pairs", {}).keys())
            pairs |= set(self._cb_pair_designs(kind).keys())
            return sorted(pairs)
        except Exception:
            return []

    def get_cb_geometry(self, kind: str = "cb") -> dict:
        return self._cb_forces_dict(kind).get("geometry", {}) or {}

    def get_cb_brace_type(self, kind: str = "cb") -> str:
        try:
            return self._cb_forces_dict(kind).get("brace_type", "X")
        except Exception:
            return "X"

    def get_cb_force(self, pair: str, member: str, force_type: str, kind: str = "cb") -> str:
        try:
            pairs = self._cb_forces_dict(kind)["pairs"][pair]
            key = f"diag_{force_type}_kN" if member == "diagonal" else f"chord_{force_type}_kN"
            val = pairs.get(key)
            if val is not None:
                return f"{val:.3f}"
        except (KeyError, TypeError):
            pass
        return ""

    def get_cb_nature(self, pair: str, member: str, kind: str = "cb") -> str:
        try:
            pairs = self._cb_forces_dict(kind)["pairs"][pair]
            t_key = "diag_tension_kN"     if member == "diagonal" else "chord_tension_kN"
            c_key = "diag_compression_kN" if member == "diagonal" else "chord_compression_kN"
            has_t = pairs.get(t_key) is not None
            has_c = pairs.get(c_key) is not None
            if has_t and has_c:
                return "T / C"
            if has_t:
                return "T"
            if has_c:
                return "C"
        except (KeyError, TypeError):
            pass
        return ""

    def get_cb_governing_force(self, pair: str, member: str, kind: str = "cb") -> tuple:
        """(force_kN_str, force_type) for the governing (max absolute) force."""
        try:
            pairs = self._cb_forces_dict(kind)["pairs"][pair]
            t_key = "diag_tension_kN"     if member == "diagonal" else "chord_tension_kN"
            c_key = "diag_compression_kN" if member == "diagonal" else "chord_compression_kN"
            t_val = pairs.get(t_key)
            c_val = pairs.get(c_key)
            if t_val is not None and c_val is not None:
                if abs(c_val) >= abs(t_val):
                    return (f"{c_val:.3f}", "compression")
                return (f"{t_val:.3f}", "tension")
            if c_val is not None:
                return (f"{c_val:.3f}", "compression")
            if t_val is not None:
                return (f"{t_val:.3f}", "tension")
        except (KeyError, TypeError):
            pass
        return ("", "compression")

    def get_cb_section(self, pair: str, member: str, force_type: str, kind: str = "cb") -> str:
        val = self._cb_osdag(pair, member, force_type, kind).get("section")
        return _tex(val) if val else ""

    def get_cb_capacity(self, pair: str, member: str, force_type: str, kind: str = "cb") -> str:
        val = self._cb_osdag(pair, member, force_type, kind).get("capacity_kN")
        return f"{float(val):.3f}" if val is not None else ""

    def get_cb_efficiency(self, pair: str, member: str, force_type: str, kind: str = "cb") -> str:
        val = self._cb_osdag(pair, member, force_type, kind).get("efficiency")
        return f"{float(val):.3f}" if val is not None else ""

    def get_cb_slenderness(self, pair: str, member: str, kind: str = "cb") -> str:
        for ft in ("compression", "tension"):
            val = self._cb_osdag(pair, member, ft, kind).get("slenderness")
            if val is not None:
                return f"{float(val):.1f}"
        return ""

    def get_cb_status(self, pair: str, member: str, force_type: str, kind: str = "cb") -> str:
        """Themed PASS / FAIL macro based on UR <= 1.0."""
        try:
            val = self._cb_osdag(pair, member, force_type, kind).get("efficiency")
            if val is not None:
                return r"\statusPass" if float(val) <= 1.0 else r"\statusFail"
        except (TypeError, ValueError):
            pass
        return ""

    def get_cb_gov_lc(self, pair: str, member: str, force_type: str, kind: str = "cb") -> str:
        try:
            pfx = "diag" if member == "diagonal" else "chord"
            key = f"{pfx}_{force_type}_gov_lc"
            val = self._cb_forces_dict(kind)["pairs"][pair].get(key)
            return _tex(val) if val else ""
        except (KeyError, TypeError):
            return ""

    def get_cb_connection(self, pair: str, member: str, force_type: str, kind: str = "cb") -> str:
        val = self._cb_osdag(pair, member, force_type, kind).get("connection")
        return str(val) if val else ""

    def get_cb_effective_length(self, member: str, kind: str = "cb") -> str:
        try:
            geom = self.get_cb_geometry(kind)
            L_m = geom.get("diagonal_length_m", 0) if member == "diagonal" else geom.get("horiz_proj_m", 0)
            return f"{L_m * 1000:.0f}"
        except (TypeError, ValueError):
            return ""

    def get_cb_alpha_deg(self, kind: str = "cb") -> str:
        try:
            return f"{self.get_cb_geometry(kind).get('alpha_deg', 0):.2f}"
        except Exception:
            return ""

    def get_cb_section_property(self, pair: str, member: str, prop: str, kind: str = "cb"):
        """Raw section property (A in cm², rv in cm, …) stored by the member design."""
        pair_id = pair.replace("-", "")
        base = "transverse_member_design." + kind + ".section_properties."
        if member == "diagonal":
            names = ["bracing", "end_diaphragm"] if kind == "cb" else ["end_diaphragm", "bracing"]
        else:
            names = ["bottom_chord", "top_chord"]
        for n in names:
            val = self.output_dict.get(f"{base}{n}.{pair_id}.{prop}")
            if val is not None:
                return val
        return None


def _format_project_location(pl_data):
    if not pl_data:
        return ''
    if isinstance(pl_data, str):
        try:
            import ast
            pl_dict = ast.literal_eval(pl_data)
        except Exception:
            return pl_data
    elif isinstance(pl_data, dict):
        pl_dict = pl_data
    else:
        return str(pl_data)

    method = pl_dict.get('method')
    data = pl_dict.get('data', {})

    if method == 'location_name':
        dist = data.get('district', '')
        state = data.get('state', '')
        if dist and state:
            return f"{dist}, {state}"
        return dist or state or r''
    elif method == 'map':
        lat = data.get('latitude', '')
        lon = data.get('longitude', '')
        if lat and lon:
            try:
                from osdagbridge.core.bridge_types.plate_girder.ui_fields_project_location import DB_PATH
                from osdagbridge.core.data.project_location.database import Database
                db = Database(DB_PATH)
                db.connect()
                nearest = db.get_nearest_station_temperature(float(lat), float(lon))
                db.close()
                if nearest:
                    return f"{nearest['station']}, {nearest['state']}"
            except Exception as e:
                logger.warning(f"Reverse geocode error: {e}")
            return f"Lat: {lat}°, Lon: {lon}°"
        return 'Map Location'
    elif method == 'custom_data':
        return 'Custom Location Data'

    return str(pl_data)

# ---------------------------------------------------------------------------
# Public builder helper (unchanged signature)
# ---------------------------------------------------------------------------

def build_report_payload(request, input_dict, output_dict):
    try:
        rd  = request.metadata.report_date or datetime.date.today().isoformat()
        lp  = request.metadata.logo_path
        raw_pl = request.metadata.project_location or input_dict.get('project.location') or ''
        pl = _format_project_location(raw_pl)

        md = ReportMetadata(
            project_name  = request.metadata.project_name,
            project_location = pl,
            designer      = request.metadata.designer,
            client        = request.metadata.client,
            company       = request.metadata.company,
            group_name    = request.metadata.group_name,
            subtitle      = request.metadata.subtitle,
            job_number    = request.metadata.job_number,
            additional_comments = request.metadata.additional_comments,
            logo_path     = lp,
            report_date   = rd,
            reviewer      = getattr(request.metadata, 'reviewer', ''))

        # Inject detailed project location and weather data into input_dict dict
        try:
            import ast
            if isinstance(raw_pl, str) and '{' in raw_pl:
                pl_dict = ast.literal_eval(raw_pl)
            elif isinstance(raw_pl, dict):
                pl_dict = raw_pl
            else:
                pl_dict = {}

            if pl_dict and isinstance(pl_dict, dict):
                data = pl_dict.get('data', {})
                weather = pl_dict.get('weather_data', {})

                lat_val = data.get('latitude') or weather.get('latitude')
                lon_val = data.get('longitude') or weather.get('longitude')

                if 'latitude' not in input_dict and lat_val:
                    input_dict['latitude'] = lat_val
                if 'longitude' not in input_dict and lon_val:
                    input_dict['longitude'] = lon_val

                if 'seismic_zone' not in input_dict and weather.get('zone'):
                    input_dict['seismic_zone'] = weather.get('zone')
                if 'wind_speed' not in input_dict and weather.get('wind_speed'):
                    input_dict['wind_speed'] = weather.get('wind_speed')
                if 'shade_temp_max' not in input_dict and weather.get('max_temp'):
                    input_dict['shade_temp_max'] = weather.get('max_temp')
                if 'shade_temp_min' not in input_dict and weather.get('min_temp'):
                    input_dict['shade_temp_min'] = weather.get('min_temp')
        except Exception as e:
            logger.warning(f"Failed to parse project location data: {e}")

        # ── Table 3.6 rows 3 & 4: effective bridge temp range and rise/fall ────
        for _tkey in (KEY_TL_BRIDGE_TEMP_MIN, KEY_TL_BRIDGE_TEMP_MAX,
                      KEY_TL_TEMP_RISE, KEY_TL_TEMP_FALL):
            if not input_dict.get(_tkey) and output_dict.get(_tkey):
                input_dict[_tkey] = output_dict[_tkey]

        if not input_dict.get(KEY_TL_BRIDGE_TEMP_MIN):
            try:
                max_str = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get('shade_temp_max')
                min_str = input_dict.get(KEY_TL_LOWEST_MIN_TEMP)  or input_dict.get('shade_temp_min')
                if max_str and min_str:
                    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
                    res   = IRC6_2017.cl_215_2_effective_bridge_temperature(
                                float(max_str), float(min_str), 'metallic', False)
                    t_min = res.get('T_min', 0)
                    t_max = res.get('T_max', 0)
                    mean  = (t_max + t_min) / 2.0
                    input_dict[KEY_TL_BRIDGE_TEMP_MIN] = f"{t_min:.2f}"
                    input_dict[KEY_TL_BRIDGE_TEMP_MAX] = f"{t_max:.2f}"
                    input_dict[KEY_TL_TEMP_RISE]       = f"{t_max - mean:.2f}"
                    input_dict[KEY_TL_TEMP_FALL]       = f"{mean - t_min:.2f}"
            except Exception as _te:
                logger.warning(f"Could not compute temperature values for report: {_te}")

        asum = {}
        if output_dict:
            asum = output_dict.get('analysis_summary', {})

        dc = []
        le = []
        if output_dict:
            if 'design_checks' in output_dict:
                dc = output_dict['design_checks']
            if 'design_log' in output_dict:
                le = output_dict['design_log']

        if not le:
            try:
                from osdagbridge.core.utils.logger import bridge_logger
                le = bridge_logger.get_success_log()
            except Exception as _le:
                logger.warning("Could not read design log from logger: %s", _le)

        return ReportPayload(metadata=md, options=request.options, inputs=input_dict,
                             analysis_summary=asum, design_checks=dc,
                             figures=ReportFigures(), log_entries=le,
                             output_dict=output_dict or {})

    except Exception as exc:
        logger.warning("build_report_payload error: %s", exc)
        return ReportPayload(
            metadata=request.metadata, options=request.options,
            inputs={}, analysis_summary={}, design_checks=[],
            figures=ReportFigures(), log_entries=[],
            output_dict={})


# ---------------------------------------------------------------------------

from osdagbridge.core.boq.boq_generator import calculate_material_quantities

# ===========================================================================
# Public entry point
# ===========================================================================

_FIGURE_MAP = [
    ('plan',                  'plan.png'),
    ('cross_section',         'cross_section.png'),
    ('final_geometry',        'final_geometry.png'),
    ('longitudinal_elevation','longitudinal_elevation.png'),
    ('girder_3d',             'girder_3d.png'),
    ('girder_top',            'girder_top.png'),
    ('section_preview',       'section_preview.png'),
    ('stiffener_preview',     'stiffener_preview.png'),
    ('cb_diagram',            'cb_diagram.png'),
    ('cb_bracing',            'cb_bracing.png'),
    ('cb_top_chord',          'cb_top_chord.png'),
    ('cb_bottom_chord',       'cb_bottom_chord.png'),
    ('ed_diagram',            'ed_diagram.png'),
    ('ed_bracing',            'ed_bracing.png'),
    ('ed_top_chord',          'ed_top_chord.png'),
    ('ed_bottom_chord',       'ed_bottom_chord.png'),
    ('bm_envelope',           'bm_envelope.png'),
    ('sf_envelope',           'sf_envelope.png'),
    ('defl_ll',               'defl_ll.png'),
]


def _discover_compiler() -> str:
    """Bundled pdflatex (osdag_latex_env) when available, else PATH lookup."""
    compiler = 'pdflatex'
    try:
        import importlib
        module = importlib.import_module('osdag_latex_env.__main__')
        latex_env = getattr(module, 'OsdagLatexEnv')()
        if latex_env.pdflatex:
            compiler = str(latex_env.pdflatex)
            if latex_env.bin_dir:
                os.environ['PATH'] = str(latex_env.bin_dir) + os.pathsep + os.environ.get('PATH', '')
    except Exception as e:
        logger.info("osdag_latex_env not found or failed to load. (%s)", e)
    return compiler


def _needs_rerun(log_path: str) -> bool:
    """True when the pdflatex log asks for another pass (labels / longtable)."""
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as fh:
            log = fh.read()
    except OSError:
        return False
    return ('Rerun to get' in log) or ('Table widths have changed' in log)


def _render_charts(payload, tmp_dir: str) -> dict:
    """Section 5.5 / Chapter 7 charts → {key: relative path | None}."""
    from .summary_data import collect_utilization, collect_material_quantities
    from .charts import generate_report_charts
    charts_dir = os.path.join(tmp_dir, 'charts')
    os.makedirs(charts_dir, exist_ok=True)
    try:
        components = collect_utilization(payload.output_dict, payload.inputs)
        material = collect_material_quantities(payload.inputs, payload.output_dict)
        paths = generate_report_charts(components, material, charts_dir, THEME)
    except Exception as exc:
        logger.warning("Report charts could not be generated: %s", exc, exc_info=True)
        components, material, paths = [], None, {}
    # pdflatex runs with cwd=tmp_dir → use relative paths
    rel = {k: (os.path.relpath(p, tmp_dir).replace('\\', '/') if p else None) for k, p in paths.items()}
    return {"paths": rel, "components": components, "material": material}


def assemble_document(payload, fig_paths: dict, osdag_logo_latex, org_logo_latex, charts: dict) -> str:
    """Build the complete LaTeX source (no I/O)."""
    bridge = ReportDataBridge(payload.output_dict, payload.inputs, payload)
    span_m = float(payload.inputs.get(KEY_SPAN, 0) or 0)
    secs = payload.options.sections

    doc_parts = [
        preamble(payload.metadata.project_name, payload.metadata.job_number,
                 payload.metadata.report_date, payload.metadata.subtitle or 'Rev 0'),
        title_page(payload.metadata, osdag_logo_latex, org_logo_latex),
    ]
    if payload.options.include_toc:
        doc_parts.append(toc_section())

    doc_parts.append(executive_summary(payload.inputs, payload.output_dict, fig_paths))
    doc_parts.append(ch1_project_info(payload.metadata))
    doc_parts.append(ch2_input_parameters(payload.metadata, payload.inputs, payload.output_dict))

    if 'loads' in secs:
        doc_parts.append(ch3_loads(payload.inputs))
    if 'analysis' in secs:
        doc_parts.append(ch4_analysis(payload.analysis_summary, fig_paths, bridge, span_m))
    if 'design_checks' in secs:
        doc_parts.append(ch5_design_checks(payload.design_checks, bridge,
                                           charts=charts.get("paths"), components=charts.get("components")))
    if 'drawings' in secs and payload.options.include_figures:
        doc_parts.append(ch6_drawings(fig_paths))

    doc_parts.append(ch7_quantities(payload.inputs, charts=charts.get("paths"), material=charts.get("material")))
    doc_parts.append(ch8_design_log(payload.log_entries, payload.inputs))
    doc_parts.append(references())
    doc_parts.append(r"\end{document}")
    return "\n".join(doc_parts)


def generate_report(payload, request):
    # type: (ReportPayload, ReportRequest) -> ReportResult
    """Compile the full OsdagBridge Design Report to PDF (+ .tex source)."""
    tex_path = None
    try:
        compiler = _discover_compiler()
        logger.info("Compiler: %s", compiler)

        os.makedirs(request.output_dir, exist_ok=True)
        pdf_path = os.path.join(request.output_dir, request.file_stem + '.pdf')
        tex_path = os.path.join(request.output_dir, request.file_stem + '.tex')

        with tempfile.TemporaryDirectory() as tmp_dir:
            # ── Figures: bytes → tmp_dir/images/*.png (then free RAM) ──
            tmp_images = os.path.join(tmp_dir, 'images')
            os.makedirs(tmp_images, exist_ok=True)
            fig_paths = {}
            for attr, img_bytes in list(payload.figure_data.items()):
                if img_bytes:
                    p = os.path.join(tmp_images, attr + '.png')
                    with open(p, 'wb') as fh:
                        fh.write(img_bytes)
                    fig_paths[attr] = 'images/' + attr + '.png'
            payload.figure_data.clear()

            # ── Logos → tmp_dir/assets ──
            tmp_assets = os.path.join(tmp_dir, 'assets')
            os.makedirs(tmp_assets, exist_ok=True)
            here = os.path.dirname(os.path.abspath(__file__))
            osdag_logo_src = os.path.join(here, '..', 'data', 'ResourceFiles', 'vectors', 'Osdag Logo.png')
            iit_logo_src   = os.path.join(here, 'assets', 'IIT Bombay Logo.png')

            osdag_logo_latex = None
            if os.path.exists(osdag_logo_src):
                shutil.copy2(osdag_logo_src, os.path.join(tmp_assets, 'osdag_logo.png'))
                osdag_logo_latex = 'assets/osdag_logo.png'

            org_logo_latex = None
            org_logo_src = (payload.metadata.logo_path
                            if (payload.metadata.logo_path and os.path.exists(payload.metadata.logo_path))
                            else (iit_logo_src if os.path.exists(iit_logo_src) else None))
            if org_logo_src:
                shutil.copy2(org_logo_src, os.path.join(tmp_assets, 'org_logo.png'))
                org_logo_latex = 'assets/org_logo.png'

            # ── Chapter 7 quantities (BOQ) ──
            quantities = calculate_material_quantities(payload.inputs, payload.output_dict)
            payload.inputs.update(quantities)

            # ── Charts (Section 5.5 and Chapter 7) → tmp_dir/charts ──
            charts = _render_charts(payload, tmp_dir)

            # ── Assemble & write LaTeX ──
            full_tex = assemble_document(payload, fig_paths, osdag_logo_latex, org_logo_latex, charts)
            tmp_tex = os.path.join(tmp_dir, request.file_stem + '.tex')
            tmp_pdf = os.path.join(tmp_dir, request.file_stem + '.pdf')
            with open(tmp_tex, 'w', encoding='utf-8') as f:
                f.write(full_tex)

            # ── Compile: at least twice (TOC, LastPage); a third pass when
            #    LaTeX reports that labels / longtable widths changed ──
            res = None
            tmp_log = os.path.join(tmp_dir, request.file_stem + '.log')
            for pass_no in range(1, 4):
                try:
                    kwargs = {
                        'cwd': tmp_dir,
                        'stdout': subprocess.PIPE,
                        'stderr': subprocess.PIPE,
                        'check': False,
                        'env': os.environ.copy(),
                    }
                    if os.name == 'nt':
                        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                    res = subprocess.run(
                        [compiler, '-interaction=nonstopmode', request.file_stem + '.tex'],
                        **kwargs
                    )
                except Exception as exc:
                    logger.warning(f"pdflatex run failed: {exc}")
                    break
                if pass_no >= 2 and not _needs_rerun(tmp_log):
                    break

            if os.path.exists(tmp_tex):
                shutil.copy2(tmp_tex, tex_path)
            if os.path.exists(tmp_pdf):
                shutil.copy2(tmp_pdf, pdf_path)
            if os.path.exists(tmp_log):
                shutil.copy2(tmp_log, os.path.join(request.output_dir, request.file_stem + '.log'))

        if os.path.exists(pdf_path):
            logger.info("Report generated: %s", pdf_path)
            return ReportResult(pdf_path=pdf_path, tex_path=tex_path)

        logger.error("pdflatex ran but no PDF was produced.")
        if res is not None:
            logger.error("pdflatex STDOUT:\n%s", res.stdout.decode('utf-8', 'ignore'))
            logger.error("pdflatex STDERR:\n%s", res.stderr.decode('utf-8', 'ignore'))
        return ReportResult(pdf_path=None, tex_path=tex_path)

    except Exception as exc:
        logger.error("generate_report failed: %s", exc, exc_info=True)
        if tex_path and os.path.exists(tex_path):
            return ReportResult(pdf_path=None, tex_path=tex_path)
        return ReportResult(pdf_path=None, tex_path=None)
