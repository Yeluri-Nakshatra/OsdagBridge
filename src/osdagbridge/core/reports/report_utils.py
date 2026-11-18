from osdagbridge.core.utils.common import (
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_DEPTH,
    KEY_TS_NO_OF_GIRDERS
)


def _tex(value):
    """Escape a Python value for safe LaTeX embedding."""
    s = str(value) if value is not None else ''
    if not s:
        return r''
    # Normalise non-ASCII glyphs from section designations (e.g. "∠ 100 ⅹ 100ⅹ 10")
    # that pdflatex cannot render.
    for uni, ascii_ in [('∠', 'L'), ('ⅹ', 'x'), ('×', 'x'), ('–', '--'), ('—', '---'), ('°', r'$^\circ$')]:
        s = s.replace(uni, ascii_)
    s = s.replace('\\', r'\textbackslash{}')
    for ch, esc in [('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'),
                    ('{', r'\{'), ('}', r'\}'),
                    ('_', r'\_\allowbreak{}'),
                    ('~', r'\textasciitilde{}'), ('^', r'\^{}')]:
        s = s.replace(ch, esc)
    s = s.replace(':', r':\allowbreak{}')
    # `$^\circ$` was escaped above — restore the math degree sign
    s = s.replace(r'\$\^{}\textbackslash{}circ\$', r'$^\circ$')
    return s


def _render_value(source_dict, key, unit=""):
    val = source_dict.get(key)
    if val in ("", None):
        return ""
    return _tex(val) + unit


def get_girder_entries(input_dict):
    """
    Retrieve all girder labels and member IDs from backend keys.

    Usage Example:
    --------------------------
    girder_entries = get_girder_entries(bridge.input_dict)

    # 1. Fallback handling (if backend hasn't populated keys yet)
    if not girder_entries:
        n = int(input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]

    # 2. Loop through entries
    for lbl, mid in girder_entries:
        print(lbl, mid)
    """
    try:
        n = int(input_dict.get(KEY_TS_NO_OF_GIRDERS, 0))
    except (TypeError, ValueError):
        n = 0

    entries = []
    for i in range(1, n + 1):
        entries.append(
            (
                input_dict.get(f"{KEY_MP_GD_SELECT_GIRDER}.G{i}", ""),
                input_dict.get(f"{KEY_MP_GD_MEMBER_ID}.G{i}.M1", ""),
            )
        )
    return entries


# ── Figure helpers (thin wrappers over latex_builders, kept for API compatibility)

def _fig_or_placeholder(path, caption, width=None):
    """Unnumbered figure (or placeholder box) — used by the Executive Summary."""
    from .latex_builders import figure_block
    from .styles import THEME
    return figure_block(path, caption, width=width or THEME.figure.default_width, numbered=False)


def _fig_embed(path, caption, width=None, height=None):
    """Unnumbered figure with a small caption (analysis envelopes)."""
    from .latex_builders import figure_block
    from .styles import THEME
    return figure_block(path, r"\small " + caption, width=width or THEME.figure.envelope_width, numbered=False)
