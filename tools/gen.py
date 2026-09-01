"""Generate the SVG asset set for Bjorn Verschoor's GitHub profile README.

Text is converted to outlines so the rendering is identical everywhere GitHub
shows the README, independent of the fonts installed on the viewer's machine.
"""
import io
import os
import re
from dataclasses import dataclass

import uharfbuzz as hb
from fontTools.misc.transform import Transform
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "assets")
os.makedirs(OUT, exist_ok=True)

BRAND = "#28A496"

@dataclass(frozen=True)
class Theme:
    """Colour tokens for one GitHub colour scheme."""
    name: str
    ink: str
    muted: str
    accent: str
    rule: str

LIGHT = Theme("light", "#0B1215", "#5A666B", "#17786D", "#D9DEDC")
DARK = Theme("dark", "#E9EFEC", "#8B989A", "#3FCFBE", "#2B3439")


class Face:
    """A variable font pinned to one instance, able to render text as SVG paths."""

    def __init__(self, path: str, axes: dict):
        base = TTFont(path)
        instantiateVariableFont(base, axes, inplace=True, updateFontNames=False)
        buf = io.BytesIO()
        base.save(buf)
        data = buf.getvalue()
        self.tt = TTFont(io.BytesIO(data))
        self.glyphs = self.tt.getGlyphSet()
        self.names = self.tt.getGlyphOrder()
        self.upem = self.tt["head"].unitsPerEm
        self.hb = hb.Font(hb.Face(data))

    def _shape(self, text: str, size: float, tracking: float):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf)
        scale = size / self.upem
        x = 0.0
        runs = []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            runs.append((self.names[info.codepoint], x + pos.x_offset * scale, pos.y_offset * scale))
            x += pos.x_advance * scale + tracking
        return runs, (x - tracking if text else 0.0)

    def text(self, text: str, size: float, tracking: float = 0.0):
        """Return (svg path data with baseline at y=0, advance width)."""
        runs, width = self._shape(text, size, tracking)
        scale = size / self.upem
        parts = []
        for gname, gx, gy in runs:
            pen = SVGPathPen(self.glyphs)
            self.glyphs[gname].draw(TransformPen(pen, Transform(scale, 0, 0, -scale, gx, -gy)))
            cmds = pen.getCommands()
            if cmds:
                parts.append(cmds)
        return " ".join(parts), width

    def width(self, text: str, size: float, tracking: float = 0.0) -> float:
        return self._shape(text, size, tracking)[1]


DISPLAY = Face(os.path.join(ROOT, "fonts", "Archivo.ttf"), {"wght": 700, "wdth": 100})
DISPLAY_MED = Face(os.path.join(ROOT, "fonts", "Archivo.ttf"), {"wght": 600, "wdth": 100})
MONO = Face(os.path.join(ROOT, "fonts", "JetBrainsMono.ttf"), {"wght": 600})


def write(name: str, body: str, width: float, height: float) -> None:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" fill="none" role="img">\n{body}\n</svg>\n'
    )
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(svg)


def path(d: str, fill: str, x: float, y: float) -> str:
    return f'<path transform="translate({x:.2f} {y:.2f})" fill="{fill}" d="{d}"/>'


# --------------------------------------------------------------------------- header

def header(theme: Theme) -> None:
    W, H = 760, 176
    name_d, name_w = DISPLAY.text("BJORN VERSCHOOR", 58, tracking=-1.2)
    role = "FULL-STACK DEVELOPER   /   CO-FOUNDER OF FIKSUP   /   DORDRECHT, NL"
    role_d, role_w = MONO.text(role, 12.5, tracking=1.6)
    body = [
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="none"/>',
        path(name_d, theme.ink, (W - name_w) / 2, 92),
        f'<rect x="{(W - 132) / 2:.1f}" y="112" width="132" height="4" rx="2" fill="{BRAND}"/>',
        path(role_d, theme.muted, (W - role_w) / 2, 148),
    ]
    write(f"header-{theme.name}.svg", "\n".join(body), W, H)


# ------------------------------------------------------------------------- headings

def heading(slug: str, index: str, title: str, theme: Theme) -> None:
    W, H = 830, 46
    title_d, title_w = DISPLAY_MED.text(title.upper(), 23, tracking=0.6)
    idx_d, idx_w = MONO.text(index, 12, tracking=1.4)
    bar_x, text_x = 0, 20
    rule_x = text_x + title_w + 18
    rule_end = W - idx_w - 14
    body = [
        f'<rect x="{bar_x}" y="10" width="6" height="26" rx="1" fill="{BRAND}"/>',
        path(title_d, theme.ink, text_x, 31),
        f'<rect x="{rule_x:.1f}" y="22" width="{max(rule_end - rule_x, 0):.1f}" height="1" fill="{theme.rule}"/>',
        path(idx_d, theme.muted, W - idx_w, 27),
    ]
    write(f"heading-{slug}-{theme.name}.svg", "\n".join(body), W, H)


def subheading(slug: str, title: str, theme: Theme) -> None:
    W, H = 830, 30
    d, w = MONO.text(title.upper(), 12.5, tracking=1.8)
    body = [
        f'<rect x="0" y="9" width="10" height="1" fill="{BRAND}"/>',
        path(d, theme.muted, 20, 14),
    ]
    write(f"subheading-{slug}-{theme.name}.svg", "\n".join(body), W, H)


def divider(theme: Theme) -> None:
    W, H = 830, 6
    body = [
        f'<rect x="0" y="2" width="{W}" height="1" fill="{theme.rule}"/>',
        f'<rect x="0" y="0" width="86" height="4" rx="2" fill="{BRAND}"/>',
    ]
    write(f"divider-{theme.name}.svg", "\n".join(body), W, H)


# --------------------------------------------------------------------------- badges

ICON_DIR = os.path.join(ROOT, "icons")

CUSTOM_ICONS = {
    # 24x24 viewBox, single path, drawn here so the set stays consistent.
    "linkedin": "M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.42v1.56h.05c.47-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28ZM5.34 7.43a2.07 2.07 0 1 1 0-4.13 2.07 2.07 0 0 1 0 4.13ZM7.12 20.45H3.55V9h3.57v11.45ZM22.22 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.72V1.72C24 .77 23.2 0 22.22 0Z",
    "mail": "M1.5 4h21A1.5 1.5 0 0 1 24 5.5v13a1.5 1.5 0 0 1-1.5 1.5h-21A1.5 1.5 0 0 1 0 18.5v-13A1.5 1.5 0 0 1 1.5 4Zm.9 2 9.6 6.6L21.6 6H2.4ZM22 7.9l-9.44 6.49a1 1 0 0 1-1.12 0L2 7.9V18h20V7.9Z",
    "globe": "M12 0a12 12 0 1 0 0 24 12 12 0 0 0 0-24Zm7.9 7h-3.2a15.6 15.6 0 0 0-1.7-4.2A10 10 0 0 1 19.9 7ZM12 2.1c.9 1.2 1.6 2.9 2.1 4.9H9.9c.5-2 1.2-3.7 2.1-4.9ZM2.3 14a9.9 9.9 0 0 1 0-4h3.6a20.6 20.6 0 0 0 0 4H2.3Zm.8 2h3.2c.4 1.5 1 2.9 1.7 4.2A10 10 0 0 1 3.1 16Zm3.2-9H3.1a10 10 0 0 1 4.9-4.2A15.6 15.6 0 0 0 6.3 7ZM12 21.9c-.9-1.2-1.6-2.9-2.1-4.9h4.2c-.5 2-1.2 3.7-2.1 4.9ZM14.5 15h-5a18.4 18.4 0 0 1 0-6h5a18.4 18.4 0 0 1 0 6Zm.5 5.2c.7-1.3 1.3-2.7 1.7-4.2h3.2a10 10 0 0 1-4.9 4.2Zm3.1-6.2a20.6 20.6 0 0 0 0-4h3.6a9.9 9.9 0 0 1 0 4h-3.6Z",
}


def icon_path(slug: str) -> str:
    if slug in CUSTOM_ICONS:
        return CUSTOM_ICONS[slug]
    with open(os.path.join(ICON_DIR, f"{slug}.svg"), encoding="utf-8") as fh:
        raw = fh.read()
    return re.search(r'<path[^>]*\sd="([^"]+)"', raw).group(1)


def badge(slug: str, label: str, icon: str) -> None:
    """Filled brand pill: one asset that reads correctly in light and dark mode."""
    size, tracking = 11.5, 1.5
    label_d, label_w = MONO.text(label.upper(), size, tracking=tracking)
    pad_x, icon_size, gap, H = 13.0, 13.0, 8.0, 30.0
    W = pad_x * 2 + icon_size + gap + label_w
    icon_scale = icon_size / 24
    body = [
        f'<rect x="0" y="0" width="{W:.1f}" height="{H}" rx="5" fill="#17786D"/>',
        f'<path transform="translate({pad_x:.2f} {(H - icon_size) / 2:.2f}) scale({icon_scale:.4f})" '
        f'fill="#FFFFFF" d="{icon_path(icon)}"/>',
        path(label_d, "#FFFFFF", pad_x + icon_size + gap, H / 2 + size * 0.36),
    ]
    write(f"badge-{slug}.svg", "\n".join(body), W, H)


SECTIONS = [
    ("how-i-build", "01", "How I build"),
    ("stack", "02", "Tech stack"),
    ("fiksup", "03", "FiksUp"),
    ("contact", "04", "Contact"),
]

BADGES = [
    ("linkedin", "LinkedIn", "linkedin"),
    ("email", "Email", "mail"),
    ("instagram", "Instagram", "instagram"),
    ("website", "fiksup.nl", "globe"),
    ("fiksup-instagram", "Instagram", "instagram"),
    ("fiksup-linkedin", "LinkedIn", "linkedin"),
    ("fiksup-x", "X", "x"),
    ("fiksup-tiktok", "TikTok", "tiktok"),
    ("fiksup-youtube", "YouTube", "youtube"),
    ("fiksup-facebook", "Facebook", "facebook"),
]

for theme in (LIGHT, DARK):
    header(theme)
    divider(theme)
    subheading("core", "Core: what I work in every day", theme)
    for slug, index, title in SECTIONS:
        heading(slug, index, title, theme)

for slug, label, icon in BADGES:
    badge(slug, label, icon)

print("\n".join(sorted(os.listdir(OUT))))
