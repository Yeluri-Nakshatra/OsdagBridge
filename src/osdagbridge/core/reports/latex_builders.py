# =============================================================================
# OsdagBridge — LaTeX table & figure builders
# =============================================================================
# Every table in the design report is produced through `LongTable` (or the
# `KeyValueTable` convenience wrapper).  The builder guarantees:
#
#   • header rows repeat on every page (`\endfirsthead` / `\endhead`),
#   • a "Continued on next page" cue (`\endfoot`) and a clean last foot,
#   • grouped rows (per girder / per bracing panel) are kept on one page
#     (`\\*` forbids a page break after the row),
#   • header shading, fonts, paddings and column widths come from
#     `styles.THEME` — never from the calling chapter.
#
# The builder emits plain LaTeX strings (the report generator assembles a
# single `.tex` document), so chapters stay free of layout literals.
# =============================================================================
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Union

from .styles import THEME, ReportTheme
from .report_utils import _tex

__all__ = [
    "Column", "Cell", "LongTable", "KeyValueTable",
    "status_cell", "ur_cell", "figure_block", "figure_row",
    "placeholder_box", "table_note", "col_spec",
]


# ─────────────────────────────────────────────────────────────────────────────
# Column / cell primitives
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Column:
    """A paragraph column.  `align` is 'l', 'c' or 'r'; width in cm."""
    width_cm: float
    align: str = "l"
    header: str = ""

    @property
    def spec(self) -> str:
        kind = {"l": "L", "c": "C", "r": "R"}.get(self.align, "L")
        return f"{kind}{{{self.width_cm:g}cm}}"


def col_spec(columns: Sequence[Union[Column, str]], outer_rules: bool = True) -> str:
    """Build the longtable column specification, e.g. `|L{4cm}|C{2cm}|`."""
    specs = [c.spec if isinstance(c, Column) else str(c) for c in columns]
    body = "|".join(specs)
    return f"|{body}|" if outer_rules else body


@dataclass
class Cell:
    """A header/body cell that may span columns and/or rows.

    `text` is inserted verbatim (already LaTeX).  Row spans are rendered with
    the colortbl-safe `\\multirow{-n}{*}` idiom (placed in the LAST row of the
    span) so shaded header rows do not paint over the spanning text.
    """
    text: str = ""
    colspan: int = 1
    rowspan: int = 1
    align: str = "c"
    bold: bool = False

    def latex(self, last_row_of_span: bool = True) -> str:
        t = rf"\textbf{{{self.text}}}" if (self.bold and self.text) else self.text
        if self.rowspan > 1:
            # `=` = wrap inside the paragraph column's width
            t = rf"\multirow{{-{self.rowspan}}}{{=}}{{{t}}}" if last_row_of_span else ""
        if self.colspan > 1:
            return rf"\multicolumn{{{self.colspan}}}{{{self.align}|}}{{{t}}}"
        return t


# ─────────────────────────────────────────────────────────────────────────────
# Status helpers
# ─────────────────────────────────────────────────────────────────────────────
def status_cell(ok: Optional[bool], warn: bool = False) -> str:
    """Return the themed PASS / FAIL / WARN / --- macro."""
    if ok is None:
        return r"\statusNA"
    if warn:
        return r"\statusWarn"
    return r"\statusPass" if ok else r"\statusFail"


def status_from_text(text) -> str:
    """Map an engine status string ('PASS', 'FAIL', 'WARN', ...) to a macro."""
    s = str(text or "").strip().upper()
    if not s or s in ("---", "N/A", "NA", "NONE"):
        return r"\statusNA" if s != "N/A" else "N/A"
    if "FAIL" in s:
        return r"\statusFail"
    if "WARN" in s:
        return r"\statusWarn"
    if "PASS" in s or s == "OK":
        return r"\statusPass"
    return _tex(text)


def ur_cell(value, nd: int = 2, limit: float = 1.0) -> str:
    """Format a utilisation ratio; values above `limit` are emphasised in red."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return "---"
    s = f"{f:.{nd}f}"
    return rf"\urFail{{{s}}}" if f > limit else s


def table_note(text: str) -> str:
    """Themed italic note printed under a table (text is LaTeX)."""
    return rf"\tableNote{{{text}}}"


# ─────────────────────────────────────────────────────────────────────────────
# LongTable builder
# ─────────────────────────────────────────────────────────────────────────────
class LongTable:
    """Builder for a `longtable` with repeating headers.

    Parameters
    ----------
    columns : list[Column | str]
        Column definitions (Column objects or raw specs such as ``C{2cm}``).
    caption : str | None
        Caption text (LaTeX).  Numbered by LaTeX (``Table n.m``).
    header : list[list[Cell | str]] | None
        One or more header rows.  Strings are wrapped in ``\\textbf``.
        When omitted, the `header` attribute of each Column is used.
    label : str | None
        ``\\label`` for cross references.
    size : 'normal' | 'compact' | 'dense'
        Font/padding preset from the theme.
    note : str | None
        Italic note placed under the table.
    """

    def __init__(self, columns: Sequence[Union[Column, str]], caption: Optional[str] = None,
                 header: Optional[Sequence[Sequence[Union[Cell, str]]]] = None,
                 label: Optional[str] = None, size: str = "normal",
                 note: Optional[str] = None, theme: ReportTheme = THEME,
                 continued: bool = True, header_fill: Optional[bool] = None,
                 outer_rules: bool = True, numbered: bool = True):
        self.columns = list(columns)
        self.caption = caption
        self.numbered = numbered          # False → \caption* (no "Table n.m")
        self.label = label
        self.size = size
        self.note = note
        self.theme = theme
        self.continued = continued
        self.header_fill = theme.table.header_fill if header_fill is None else header_fill
        self.outer_rules = outer_rules
        self._rows: List[str] = []
        if header is None:
            auto = [c.header for c in self.columns if isinstance(c, Column)]
            header = [auto] if any(auto) else []
        self.header_rows = [list(r) for r in header]

    # ── public API ───────────────────────────────────────────────────────
    @property
    def ncols(self) -> int:
        return len(self.columns)

    def add_row(self, cells: Iterable, keep_with_next: bool = False,
                hline: bool = True, cline: Optional[str] = None) -> "LongTable":
        """Append a body row.  `cells` are LaTeX strings (escape with `_tex`)."""
        cells = ["" if c is None else str(c) for c in cells]
        eol = r"\\*" if (keep_with_next and self.theme.table.keep_groups_together) else r"\\"
        line = " & ".join(cells) + " " + eol
        if cline:
            line += rf" \cline{{{cline}}}"
        elif hline:
            line += r" \hline"
        self._rows.append(line)
        return self

    def add_group(self, label: str, rows: Sequence[Sequence], first_col_rowspan: bool = True) -> "LongTable":
        """Append rows that share a first-column label (rendered with multirow).

        All rows of the group are glued together with ``\\*`` so the group is
        never split across pages; the last row ends with ``\\hline``.
        """
        rows = [list(r) for r in rows]
        n = len(rows)
        if n == 0:
            return self
        for i, r in enumerate(rows):
            if first_col_rowspan:
                first = rf"\multirow{{{n}}}{{=}}{{{label}}}" if i == 0 else ""
            else:
                first = label if i == 0 else ""
            cells = [first] + ["" if c is None else str(c) for c in r]
            last = (i == n - 1)
            if last:
                self.add_row(cells, keep_with_next=False, hline=True)
            else:
                self.add_row(cells, keep_with_next=True, hline=False,
                             cline=f"2-{self.ncols}")
        return self

    def add_section_row(self, text: str, align: str = "l") -> "LongTable":
        """A shaded full-width sub-heading row."""
        fill = self.theme.palette.group_fill[0]
        self._rows.append(
            rf"\multicolumn{{{self.ncols}}}{{|{align}|}}{{\cellcolor{{{fill}}}\textbf{{{text}}}}} \\* \hline"
        )
        return self

    def add_message_row(self, label: str, message: str) -> "LongTable":
        """First column = label, remaining columns merged into one message."""
        span = self.ncols - 1
        self._rows.append(rf"{label} & \multicolumn{{{span}}}{{c|}}{{{message}}} \\ \hline")
        return self

    def add_raw(self, tex: str) -> "LongTable":
        self._rows.append(tex)
        return self

    def is_empty(self) -> bool:
        return not self._rows

    # ── rendering ───────────────────────────────────────────────────────
    def _size_cmd(self) -> str:
        return {"compact": r"\tableCompact", "dense": r"\tableDense"}.get(self.size, "")

    def _render_header_rows(self) -> str:
        if not self.header_rows:
            return ""
        fill = self.theme.palette.header_fill[0]
        out = []
        nrows = len(self.header_rows)
        # Track row spans so `\multirow{-n}` lands in the last row of the span.
        pending: dict = {}   # column index -> (Cell, rows remaining)
        for ri, row in enumerate(self.header_rows):
            cells_tex = []
            ci = 0
            for item in row:
                if isinstance(item, Cell):
                    if item.rowspan > 1:
                        pending[ci] = (item, item.rowspan - 1)
                        cells_tex.append(item.latex(last_row_of_span=False))
                    else:
                        cells_tex.append(item.latex())
                    ci += item.colspan
                elif item is None:
                    # placeholder for a column under an active row span
                    cell, remaining = pending.get(ci, (None, 0))
                    if cell is not None and remaining == 1:
                        cells_tex.append(cell.latex(last_row_of_span=True))
                        pending.pop(ci, None)
                    elif cell is not None:
                        pending[ci] = (cell, remaining - 1)
                        cells_tex.append("")
                    else:
                        cells_tex.append("")
                    ci += 1
                else:
                    text = str(item)
                    if self.theme.table.header_bold and text:
                        text = rf"\textbf{{{text}}}"
                    cells_tex.append(text)
                    ci += 1
            prefix = rf"\rowcolor{{{fill}}} " if self.header_fill else ""
            line = prefix + " & ".join(cells_tex) + r" \\"
            if ri < nrows - 1:
                # Partial rules between stacked header rows: skip every column
                # that is still covered by an active row span.
                covered = set(pending.keys())
                segments, start = [], None
                for col in range(1, self.ncols + 1):
                    if (col - 1) in covered:
                        if start is not None:
                            segments.append((start, col - 1))
                            start = None
                    elif start is None:
                        start = col
                if start is not None:
                    segments.append((start, self.ncols))
                if covered:
                    line += "".join(rf" \cline{{{a}-{b}}}" for a, b in segments)
                else:
                    line += r" \hline"
            else:
                line += r" \hline"
            out.append(line)
        return "\n".join(out)

    def render(self) -> str:
        t = self.theme.table
        parts = []
        size_cmd = self._size_cmd()
        if size_cmd:
            parts.append(r"\begingroup" + size_cmd)
        parts.append(rf"\begin{{longtable}}{{{col_spec(self.columns, self.outer_rules)}}}")

        header = self._render_header_rows()
        label_tex = rf"\label{{{self.label}}}" if self.label else ""

        # ── first head ──
        if self.caption:
            if self.numbered:
                parts.append(rf"\caption{{{self.caption}}}{label_tex}\\")
            else:
                parts.append(rf"\caption*{{{self.caption}}}{label_tex}\\")
        parts.append(r"\hline")
        if header:
            parts.append(header)
        parts.append(r"\endfirsthead")

        # ── running head ──
        if self.caption:
            if self.numbered:
                parts.append(rf"\caption[]{{{self.caption} {t.continued_caption_suffix}}}\\")
            else:
                parts.append(rf"\caption*{{{self.caption} {t.continued_caption_suffix}}}\\")
        parts.append(r"\hline")
        if header:
            parts.append(header)
        parts.append(r"\endhead")

        # ── running foot / last foot ──
        if self.continued:
            parts.append(
                rf"\multicolumn{{{self.ncols}}}{{r}}{{{self.theme.typography.note_size_cmd}"
                rf"\textit{{{t.continued_text}}}}} \\"
            )
        parts.append(r"\endfoot")
        parts.append(r"\endlastfoot")

        # ── body ──
        if self._rows:
            parts.extend(self._rows)
        else:
            parts.append(rf"\multicolumn{{{self.ncols}}}{{|c|}}{{\textit{{No data available}}}} \\ \hline")

        parts.append(r"\end{longtable}")
        if size_cmd:
            parts.append(r"\endgroup")
        if self.note:
            parts.append(table_note(self.note))
        return "\n".join(parts) + "\n"

    __str__ = render


# ─────────────────────────────────────────────────────────────────────────────
# Key-value (parameter / value) table
# ─────────────────────────────────────────────────────────────────────────────
class KeyValueTable(LongTable):
    """Two-column *Parameter | Value* table with themed widths."""

    def __init__(self, caption: Optional[str] = None, rows: Optional[Sequence[Sequence[str]]] = None,
                 label: Optional[str] = None, note: Optional[str] = None,
                 param_header: str = "Parameter", value_header: str = "Value",
                 wide_param: bool = False, theme: ReportTheme = THEME, **kw):
        t = theme.table
        pw = t.kv_wide_param_width_cm if wide_param else t.kv_param_width_cm
        vw = theme.page.text_width_cm - pw - 0.8     # 0.8 cm ≈ rules + padding
        cols = [Column(pw, "l", param_header), Column(round(vw, 2), "l", value_header)]
        super().__init__(cols, caption=caption, label=label, note=note, theme=theme, **kw)
        for r in (rows or []):
            self.add_row(list(r))

    def add(self, param: str, value: str) -> "KeyValueTable":
        self.add_row([param, value])
        return self


# ─────────────────────────────────────────────────────────────────────────────
# Figures
# ─────────────────────────────────────────────────────────────────────────────
def placeholder_box(text: str, theme: ReportTheme = THEME) -> str:
    return (r"\noindent\fbox{\parbox{" + theme.figure.placeholder_width + r"}{\centering\textit{[ PLACEHOLDER: "
            + text + r" ]}}}")


def figure_block(path: Optional[str], caption: str, width: Optional[str] = None,
                 label: Optional[str] = None, numbered: bool = True,
                 theme: ReportTheme = THEME) -> str:
    """`figure[H]` with an image (or a placeholder box when `path` is None)."""
    f = theme.figure
    width = width or f.default_width
    cap_cmd = r"\caption" if numbered else r"\caption*"
    label_tex = (rf"\label{{{label}}}" + "\n") if label else ""
    if path:
        body = rf"\includegraphics[width={width},keepaspectratio]{{{path.replace(chr(92), '/')}}}"
    else:
        body = placeholder_box(caption, theme)
    return "\n".join([
        r"\begin{figure}[H]",
        r"\centering",
        rf"\vspace{{{f.vspace_before}}}",
        body,
        rf"{cap_cmd}{{{caption}}}",
        label_tex + r"\end{figure}",
    ]) + "\n"


def figure_row(items: Sequence[tuple], theme: ReportTheme = THEME) -> str:
    """Side-by-side minipage figures.  `items` = [(path, caption, label), ...]."""
    n = max(1, len(items))
    width = theme.figure.triple_width if n == 3 else rf"{0.96 / n:.2f}\textwidth"
    cells = []
    for path, caption, label in items:
        label_tex = rf"\label{{{label}}}" if label else ""
        if path:
            body = rf"\includegraphics[width=\linewidth,keepaspectratio]{{{path.replace(chr(92), '/')}}}"
        else:
            body = rf"\fbox{{\parbox{{0.95\linewidth}}{{\centering\textit{{[ {caption} ]}}}}}}"
        cells.append("\n".join([
            rf"\begin{{minipage}}[t]{{{width}}}",
            r"\centering",
            body,
            rf"\captionof{{figure}}{{{caption}}}{label_tex}",
            r"\end{minipage}",
        ]))
    return r"\noindent" + "\n" + ("\n" + r"\hfill" + "\n").join(cells) + "\n"
