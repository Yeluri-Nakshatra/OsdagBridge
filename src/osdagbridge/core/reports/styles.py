# =============================================================================
# OsdagBridge — Report Style System (SINGLE SOURCE OF TRUTH)
# =============================================================================
# Every layout rule and visual attribute used by the LaTeX design report lives
# here: page geometry, typography, colour palette, table style, header/footer
# theme, figure sizes and the matplotlib chart theme.
#
# Chapter modules must NOT contain formatting literals (no `\setlength`,
# `\definecolor`, column widths, colours, font sizes).  They obtain everything
# from `THEME` (directly or through `latex_builders`).  Changing a value here
# re-styles the whole report.
#
# Only LaTeX packages that were already used by the baseline preamble are
# required, so the report keeps compiling with the TeX distribution bundled
# with Osdag (`osdag_latex_env`).
# =============================================================================
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Page geometry
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class PageGeometry:
    """Paper size, margins and the header/footer bands.

    `head_height`, `head_sep` and `foot_skip` are what keep body text (and the
    last rows of a table) from colliding with the header/footer boxes: fancyhdr
    needs `headheight` >= the real header height, and `footskip` is the distance
    from the last text baseline to the footer baseline.
    """
    paper: str = "a4paper"
    document_class: str = "report"
    base_font_pt: int = 12
    margin_left: str = "25mm"
    margin_right: str = "25mm"
    margin_top: str = "25mm"
    margin_bottom: str = "28mm"
    head_height: str = "16pt"
    head_sep: str = "12pt"
    foot_skip: str = "34pt"
    line_stretch: float = 1.12
    # Usable text width in cm (A4 width 21.0 cm minus the two side margins).
    # Column widths in tables are derived from this value.
    text_width_cm: float = 16.0


# ─────────────────────────────────────────────────────────────────────────────
# Colour palette
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Palette:
    """Named colours.  Each entry is (LaTeX colour name, HTML hex)."""
    primary:      Tuple[str, str] = ("osdagGreen",      "91B014")   # brand
    primary_dark: Tuple[str, str] = ("osdagGreenDark",  "5E7A00")
    header_fill:  Tuple[str, str] = ("osdagHeaderFill", "EEF3DA")   # table header rows
    group_fill:   Tuple[str, str] = ("osdagGroupFill",  "F3F3F3")   # sub-heading rows
    muted:        Tuple[str, str] = ("osdagMuted",      "555555")
    pass_:        Tuple[str, str] = ("osdagPass",       "1B7F3B")
    warn:         Tuple[str, str] = ("osdagWarn",       "C77700")
    fail:         Tuple[str, str] = ("osdagFail",       "C62828")
    link:         Tuple[str, str] = ("osdagLink",       "1F4E79")

    # Chart colours (hex with '#', used by matplotlib)
    chart_girder:    str = "#2F5D8A"   # steel blue
    chart_deck:      str = "#7F8C8D"   # concrete grey
    chart_bracing:   str = "#91B014"   # osdag green
    chart_diaphragm: str = "#C9A227"   # amber
    chart_concrete:  str = "#7F8C8D"
    chart_rebar:     str = "#B5651D"
    chart_fail:      str = "#C62828"
    chart_threshold: str = "#D32F2F"
    chart_grid:      str = "#D5D5D5"
    chart_text:      str = "#222222"

    def all_latex(self) -> Dict[str, str]:
        """{latex_name: hex} for every LaTeX colour defined above."""
        out = {}
        for attr in ("primary", "primary_dark", "header_fill", "group_fill",
                     "muted", "pass_", "warn", "fail", "link"):
            name, hexval = getattr(self, attr)
            out[name] = hexval
        return out


# ─────────────────────────────────────────────────────────────────────────────
# Typography
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Typography:
    body_size_cmd: str = ""                 # "" = document default
    table_size_cmd: str = ""                # normal tables
    table_compact_size_cmd: str = r"\footnotesize"
    table_dense_size_cmd: str = r"\scriptsize"
    caption_size_cmd: str = r"\small"
    note_size_cmd: str = r"\small"
    footer_size_cmd: str = r"\footnotesize"
    header_size_cmd: str = r"\footnotesize"
    chapter_title_cmd: str = r"\normalfont\Large\bfseries\centering"
    section_title_cmd: str = r"\normalfont\large\bfseries"
    subsection_title_cmd: str = r"\normalfont\normalsize\bfseries"


# ─────────────────────────────────────────────────────────────────────────────
# Table style
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class TableStyle:
    col_sep_pt: float = 5.0            # \tabcolsep
    col_sep_compact_pt: float = 3.5
    array_stretch: float = 1.28        # row height factor (replaces `\\[6pt]` hacks)
    extra_row_height_pt: float = 1.0   # \extrarowheight
    rule_width_pt: float = 0.5         # \arrayrulewidth
    lt_pre_pt: float = 6.0             # space before a longtable
    lt_post_pt: float = 10.0           # space after a longtable
    caption_skip_pt: float = 4.0       # caption <-> table gap
    header_fill: bool = True           # shade header rows
    header_bold: bool = True
    continued_text: str = "Continued on next page"
    continued_caption_suffix: str = "(continued)"
    keep_groups_together: bool = True  # `\\*` inside grouped rows
    # default widths (cm) of the parameter / value columns of key-value tables
    kv_param_width_cm: float = 5.6
    kv_value_width_cm: float = 9.6
    kv_wide_param_width_cm: float = 7.0


# ─────────────────────────────────────────────────────────────────────────────
# Header / footer theme
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class HeaderFooterTheme:
    footer_left: str = r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"
    page_format: str = r"Page \thepage\ of \pageref{LastPage}"
    rule_thickness: str = "1pt"
    head_rule_gap: str = "2pt"
    foot_rule_gap: str = "5pt"
    software_default_note: str = "* Software default value"


# ─────────────────────────────────────────────────────────────────────────────
# Figures
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class FigureStyle:
    default_width: str = r"0.85\textwidth"
    wide_width: str = r"0.95\textwidth"
    chart_width: str = r"0.92\textwidth"
    envelope_width: str = r"0.78\textwidth"
    triple_width: str = r"0.31\textwidth"
    placeholder_width: str = r"0.97\textwidth"
    logo_height: str = "2.2cm"
    vspace_before: str = "4pt"
    vspace_after: str = "2pt"


# ─────────────────────────────────────────────────────────────────────────────
# Charts (matplotlib)
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class ChartTheme:
    dpi: int = 200
    figsize_wide: Tuple[float, float] = (8.0, 3.9)
    figsize_square: Tuple[float, float] = (6.4, 3.9)
    font_family: str = "DejaVu Sans"
    title_size: float = 10.5
    label_size: float = 9.0
    tick_size: float = 8.0
    value_label_size: float = 7.5
    bar_width: float = 0.62
    bar_edge_color: str = "#FFFFFF"
    bar_edge_width: float = 0.6
    grid_alpha: float = 0.6
    threshold_value: float = 1.0
    threshold_linestyle: str = "--"
    threshold_linewidth: float = 1.4
    threshold_label: str = "UR = 1.0 (limit)"
    ur_axis_headroom: float = 0.18     # extra space above tallest bar
    ur_axis_min_top: float = 1.25      # y-axis always reaches at least this
    image_format: str = "png"


# ─────────────────────────────────────────────────────────────────────────────
# Aggregate theme
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class ReportTheme:
    page: PageGeometry = field(default_factory=PageGeometry)
    palette: Palette = field(default_factory=Palette)
    typography: Typography = field(default_factory=Typography)
    table: TableStyle = field(default_factory=TableStyle)
    header_footer: HeaderFooterTheme = field(default_factory=HeaderFooterTheme)
    figure: FigureStyle = field(default_factory=FigureStyle)
    chart: ChartTheme = field(default_factory=ChartTheme)

    # ── convenience ──────────────────────────────────────────────────────
    @property
    def primary_color(self) -> str:
        return self.palette.primary[0]

    def col_width_cm(self, fraction: float) -> float:
        """Width in cm of a column occupying `fraction` of the text width."""
        return round(self.page.text_width_cm * fraction, 2)


THEME = ReportTheme()


# =============================================================================
# LaTeX emitters — the preamble is generated from THEME so that every
# `\setlength`, colour and macro is defined exactly once.
# =============================================================================

#: LaTeX packages — identical set to the baseline report so the bundled TeX
#: distribution needs nothing new.
PACKAGES = (
    "graphicx", "amsmath", "amssymb", "booktabs", "array", "tabularx", "float",
    "fancyhdr", "xcolor", "setspace", "enumitem", "caption", "subcaption",
    "multirow", "colortbl", "longtable", "titlesec", "titletoc", "lastpage",
    "makecell", "etoolbox", "needspace",
)


def latex_document_class(theme: ReportTheme = THEME) -> str:
    p = theme.page
    return rf"\documentclass[{p.base_font_pt}pt,{p.paper}]{{{p.document_class}}}"


def latex_geometry(theme: ReportTheme = THEME) -> str:
    p = theme.page
    return (
        rf"\usepackage[{p.paper}, left={p.margin_left}, right={p.margin_right}, "
        rf"top={p.margin_top}, bottom={p.margin_bottom}, "
        rf"headheight={p.head_height}, headsep={p.head_sep}, footskip={p.foot_skip}]{{geometry}}"
    )


def latex_packages(theme: ReportTheme = THEME) -> str:
    lines = [latex_geometry(theme)]
    lines += [rf"\usepackage{{{pkg}}}" for pkg in PACKAGES]
    lines.append(r"\usepackage[hidelinks]{hyperref}")
    return "\n".join(lines)


def latex_colors(theme: ReportTheme = THEME) -> str:
    return "\n".join(
        rf"\definecolor{{{name}}}{{HTML}}{{{hexval}}}"
        for name, hexval in theme.palette.all_latex().items()
    )


def latex_table_lengths(theme: ReportTheme = THEME) -> str:
    t = theme.table
    ty = theme.typography
    return "\n".join([
        r"% ── Table layout (from styles.TableStyle) ──────────────────────────",
        rf"\setlength{{\tabcolsep}}{{{t.col_sep_pt:g}pt}}",
        rf"\renewcommand{{\arraystretch}}{{{t.array_stretch:g}}}",
        rf"\setlength{{\extrarowheight}}{{{t.extra_row_height_pt:g}pt}}",
        rf"\setlength{{\arrayrulewidth}}{{{t.rule_width_pt:g}pt}}",
        rf"\setlength{{\LTpre}}{{{t.lt_pre_pt:g}pt}}",
        rf"\setlength{{\LTpost}}{{{t.lt_post_pt:g}pt}}",
        r"\setlength{\LTleft}{\fill}",
        r"\setlength{\LTright}{\fill}",
        rf"\setlength{{\abovecaptionskip}}{{{t.caption_skip_pt:g}pt}}",
        rf"\setlength{{\belowcaptionskip}}{{{t.caption_skip_pt:g}pt}}",
        r"\captionsetup{labelfont=bf, textfont=bf, justification=raggedright, "
        rf"singlelinecheck=false, format=plain, font={ty.caption_size_cmd.lstrip(chr(92)) or 'normalsize'}}}",
        r"\captionsetup[longtable]{labelfont=bf, textfont=bf, justification=raggedright, singlelinecheck=false}",
        r"% Column types: L/C/R = ragged-left / centred / ragged-right paragraph columns",
        r"\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}",
        r"\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}",
        r"\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}",
        r"% multirow cells (group labels, stacked headers) wrap and centre in their column",
        r"\renewcommand{\multirowsetup}{\centering}",
        r"% Compact / dense table environments share one definition",
        rf"\newcommand{{\tableCompact}}{{{ty.table_compact_size_cmd}\setlength{{\tabcolsep}}{{{t.col_sep_compact_pt:g}pt}}}}",
        rf"\newcommand{{\tableDense}}{{{ty.table_dense_size_cmd}\setlength{{\tabcolsep}}{{{t.col_sep_compact_pt:g}pt}}}}",
        r"% Page-bottom protection for figures (a figure never leaves a dangling",
        r"% caption).  NOTE: no \needspace before longtable -- longtable's own",
        r"% \LT@start already moves a table whose head + first row do not fit, and",
        r"% a \needspace glue in front of it makes longtable emit a foot-only page",
        r"% followed by a duplicated head (verified with pdflatex).",
        r"\BeforeBeginEnvironment{figure}{\needspace{8\baselineskip}}",
        r"\raggedbottom",
        r"% Let TeX stretch inter-word space a little before producing overfull lines",
        r"\setlength{\emergencystretch}{1.5em}",
    ])


def latex_macros(theme: ReportTheme = THEME) -> str:
    pal = theme.palette
    return "\n".join([
        r"% ── Semantic macros (from styles) ───────────────────────────────────",
        r"\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}",
        r"\newcommand{\todo}[1]{\colorbox{yellow}{TODO: #1}}",
        rf"\newcommand{{\statusPass}}{{\textcolor{{{pal.pass_[0]}}}{{\textbf{{PASS}}}}}}",
        rf"\newcommand{{\statusFail}}{{\textcolor{{{pal.fail[0]}}}{{\textbf{{FAIL}}}}}}",
        rf"\newcommand{{\statusWarn}}{{\textcolor{{{pal.warn[0]}}}{{\textbf{{WARN}}}}}}",
        rf"\newcommand{{\statusNA}}{{\textcolor{{{pal.muted[0]}}}{{---}}}}",
        rf"\newcommand{{\urFail}}[1]{{\textcolor{{{pal.fail[0]}}}{{\textbf{{#1}}}}}}",
        rf"\newcommand{{\tableNote}}[1]{{\noindent{theme.typography.note_size_cmd}\textit{{#1}}\par}}",
        r"% Software-default asterisk: marks the page so the footer prints the legend",
        r"\newbool{hasSDonPage}",
        r"\boolfalse{hasSDonPage}",
        r"\newcommand{\markSD}{\global\booltrue{hasSDonPage}}",
        r"\newcommand{\sdstar}{\textsuperscript{*}\markSD{}}",
        r"\AddToHook{shipout/before}{\global\boolfalse{hasSDonPage}}",
    ])


def latex_page_styles(header_left: str, header_right: str,
                      theme: ReportTheme = THEME) -> str:
    r"""fancyhdr page styles `main`, `plain` and `firstpage`.

    The footer is a two-line box: line 1 = organisation | page x of y,
    line 2 (only when the page carries an `\sdstar`) = the software-default
    legend.  Both live *inside* the footer band set by `footskip`, so nothing
    is pushed into the text block (the baseline used negative `\vspace` hacks
    inside `\footrule`, which is what made rows collide with the footer).
    """
    hf = theme.header_footer
    pal = theme.palette
    ty = theme.typography
    green = pal.primary[0]

    head_rule = (rf"\renewcommand{{\headrule}}{{\color{{{green}}}\hrule width\headwidth "
                 rf"height {hf.rule_thickness} \vspace{{{hf.head_rule_gap}}}}}")
    foot_rule = (rf"\renewcommand{{\footrule}}{{\color{{{green}}}\hrule width\headwidth "
                 rf"height {hf.rule_thickness} \vspace{{{hf.foot_rule_gap}}}}}")
    foot_left = (rf"\fancyfoot[L]{{\parbox[t]{{0.72\headwidth}}{{\raggedright{ty.footer_size_cmd} "
                 rf"{hf.footer_left}"
                 rf"\ifbool{{hasSDonPage}}{{\\[1pt]\scriptsize\textit{{{hf.software_default_note}}}}}{{}}}}}}")
    foot_right = (rf"\fancyfoot[R]{{\parbox[t]{{0.26\headwidth}}{{\raggedleft{ty.footer_size_cmd} "
                  rf"{hf.page_format}}}}}")
    header = (rf"\fancyhead[L]{{{ty.header_size_cmd} {header_left}}}"
              "\n  "
              rf"\fancyhead[R]{{{ty.header_size_cmd} {header_right}}}")

    def _style(name: str, with_header: bool) -> str:
        parts = [rf"\fancypagestyle{{{name}}}{{", r"  \fancyhf{}"]
        if with_header:
            parts += ["  " + header, "  " + head_rule]
        else:
            parts += [r"  \renewcommand{\headrulewidth}{0pt}"]
        parts += ["  " + foot_left, "  " + foot_right, "  " + foot_rule, "}"]
        return "\n".join(parts)

    return "\n".join([
        _style("main", True),
        _style("plain", True),
        _style("firstpage", False),
        r"\pagestyle{main}",
        rf"\setstretch{{{theme.page.line_stretch:g}}}",
    ])


def latex_headings(theme: ReportTheme = THEME) -> str:
    """titlesec / titletoc formatting for chapters, sections and the TOC."""
    ty = theme.typography
    return "\n".join([
        r"% ── Chapter / section / TOC formatting (from styles) ───────────────",
        rf"\titleformat{{\chapter}}[block]{{{ty.chapter_title_cmd}}}{{\thechapter}}{{1em}}{{}}",
        r"\titlespacing*{\chapter}{0pt}{0pt}{12pt}",
        rf"\titleformat{{\section}}{{{ty.section_title_cmd}}}{{\thesection}}{{0.8em}}{{}}",
        r"\titlespacing*{\section}{0pt}{14pt plus 4pt minus 2pt}{6pt}",
        rf"\titleformat{{\subsection}}{{{ty.subsection_title_cmd}}}{{\thesubsection}}{{0.8em}}{{}}",
        r"\titlespacing*{\subsection}{0pt}{10pt plus 3pt minus 2pt}{4pt}",
        r"\setcounter{tocdepth}{2}",
        r"\titlecontents{chapter}[1.5em]{\normalfont\bfseries\vspace{3pt}}{\contentslabel{1.5em}}{\hspace*{-1.5em}}{\hfill\contentspage}",
        r"\titlecontents{section}[3.8em]{\normalfont}{\contentslabel{2.3em}}{\hspace*{-2.3em}}{\titlerule*[0.6pc]{.}\contentspage}",
        r"\titlecontents{subsection}[7.0em]{\normalfont}{\contentslabel{3.2em}}{\hspace*{-3.2em}}{\titlerule*[0.6pc]{.}\contentspage}",
        r"\renewcommand{\contentsname}{\centering\Large\bfseries Table of Contents}",
    ])


def latex_preamble(header_left: str, header_right: str,
                   theme: ReportTheme = THEME) -> str:
    """Complete preamble (everything before `\\begin{document}`)."""
    return "\n".join([
        latex_document_class(theme),
        "",
        latex_packages(theme),
        "",
        r"\numberwithin{table}{chapter}",
        r"\numberwithin{figure}{chapter}",
        "",
        latex_colors(theme),
        "",
        latex_table_lengths(theme),
        "",
        latex_macros(theme),
        "",
        latex_page_styles(header_left, header_right, theme),
        "",
        latex_headings(theme),
        "",
    ])
