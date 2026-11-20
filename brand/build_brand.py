#!/usr/bin/env python3
"""Génère les fichiers du logo Qafila (SVG vectorisés + PNG).

Usage : python build_brand.py <dossier_polices_ttf> [<fichier_thmanyah_ttf_otf>]
Nécessite fontTools (et rsvg-convert pour les PNG).
Le texte est converti en tracés : les SVG ne dépendent d'aucune police installée.
"""
import subprocess
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

INK, BLUE, BRICK, HENNA, LIME, SAND = "#16213A", "#1F5FAD", "#C27C2C", "#B4472A", "#F7F3EA", "#EAD9BE"
OUT = Path(__file__).resolve().parent / "logo"


def text_path(font_path, text, size, wght=None, rtl=False):
    """Retourne (d, largeur) du texte vectorisé, ligne de base à y=0."""
    font = TTFont(font_path)
    if wght and "fvar" in font:
        axes = {a.axisTag: a for a in font["fvar"].axes}
        font = instancer.instantiateVariableFont(font, {"wght": max(axes["wght"].minValue, min(wght, axes["wght"].maxValue))})
    upm = font["head"].unitsPerEm
    scale = size / upm
    gs = font.getGlyphSet()
    if rtl:
        glyphs = shape_arabic(font, text)
    else:
        cmap = font.getBestCmap()
        glyphs = [cmap[ord(c)] for c in text]
    hmtx = font["hmtx"]
    pen = SVGPathPen(gs)
    x = 0
    kern = latin_kerning(font)
    for i, g in enumerate(glyphs):
        tpen = TransformPen(pen, (scale, 0, 0, -scale, x * scale, 0))
        gs[g].draw(tpen)
        x += hmtx[g][0]
        if i + 1 < len(glyphs):
            x += kern.get((g, glyphs[i + 1]), 0)
    return pen.getCommands(), x * scale


def latin_kerning(font):
    pairs = {}
    if "GPOS" not in font:
        return pairs
    try:
        for lookup in font["GPOS"].table.LookupList.Lookup:
            for st in lookup.SubTable:
                st = getattr(st, "ExtSubTable", st)
                if getattr(st, "Format", None) == 1 and hasattr(st, "PairSet"):
                    for g1, ps in zip(st.Coverage.glyphs, st.PairSet):
                        for pvr in ps.PairValueRecord:
                            v = getattr(pvr.Value1, "XAdvance", 0) or 0
                            pairs.setdefault((g1, pvr.SecondGlyph), v)
    except Exception:
        pass
    return pairs


def shape_arabic(font, text):
    """Mise en forme arabe via HarfBuzz si disponible (uharfbuzz)."""
    import uharfbuzz as hb
    blob = hb.Blob.from_file_path(font.reader.file.name)
    face = hb.Face(blob)
    hfont = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hfont, buf, {})
    order = font.getGlyphOrder()
    return [order[i.codepoint] for i in buf.glyph_infos]


def symbol_shapes(fg=LIME, stop=BRICK, end=HENNA):
    """Le symbole : un « q » tracé comme une route, trois étapes, une arrivée."""
    return f"""
  <circle cx="30.5" cy="28" r="12.5" fill="none" stroke="{fg}" stroke-width="5.5"/>
  <path d="M43 15.5 V46" stroke="{fg}" stroke-width="5.5" stroke-linecap="round" fill="none"/>
  <circle cx="18" cy="28" r="2.9" fill="{stop}"/>
  <circle cx="30.5" cy="15.5" r="2.9" fill="{stop}"/>
  <circle cx="30.5" cy="40.5" r="2.9" fill="{stop}"/>
  <circle cx="43" cy="51" r="5.2" fill="{end}"/>"""


def write(name, svg):
    (OUT / name).write_text(svg.strip() + "\n", encoding="utf-8")


def png(name, width, out=None):
    out = out or name.replace(".svg", f"-{width}.png")
    subprocess.run(["rsvg-convert", "-w", str(width), str(OUT / name), "-o", str(OUT / out)], check=True)


def main():
    fonts = Path(sys.argv[1])
    thmanyah = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    OUT.mkdir(exist_ok=True)

    # Symbole sur tuile (favicon, icône d'application, avatar)
    write("qafila-symbol.svg", f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <title>Qafila</title>
  <rect width="64" height="64" rx="16" fill="{INK}"/>{symbol_shapes()}
</svg>""")
    # Symbole sans tuile, pour fonds clairs / sombres
    write("qafila-symbol-ink.svg", f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="12 9 40 49">{symbol_shapes(fg=INK)}
</svg>""")
    write("qafila-symbol-white.svg", f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="12 9 40 49">{symbol_shapes(fg=LIME)}
</svg>""")

    # Logo horizontal : le « q » est la route elle-même, suivi de « afila »
    size = 46
    k = size / 1200  # unités Funnel Display (upm 1200, hauteur d'x 600)
    base = 46
    d_lat, w_lat = text_path(fonts / "FunnelDisplay.ttf", "afila", size, wght=700)
    ar = None
    if thmanyah:
        try:
            ar = text_path(thmanyah, "قافلة", 26, rtl=True)
        except Exception as exc:  # uharfbuzz absent ou police invalide
            print("Arabe ignoré :", exc)

    def route_q(fg, x0):
        cx, cy, r, sw = 345, 300, 237, 150
        sx = cx + r
        X = lambda v: x0 + v * k
        Y = lambda v: base - v * k
        return (f'<circle cx="{X(cx):.2f}" cy="{Y(cy):.2f}" r="{r*k:.2f}" fill="none" stroke="{fg}" stroke-width="{sw*k:.2f}"/>'
                f'<path d="M{X(sx):.2f} {Y(612):.2f} V{Y(-150):.2f}" stroke="{fg}" stroke-width="{sw*k:.2f}" fill="none"/>'
                + "".join(f'<circle cx="{X(a):.2f}" cy="{Y(b):.2f}" r="{44*k:.2f}" fill="{BRICK}"/>'
                          for a, b in ((cx - r, cy), (cx, cy + r), (cx, cy - r)))
                + f'<circle cx="{X(sx):.2f}" cy="{Y(-215):.2f}" r="{92*k:.2f}" fill="{HENNA}"/>'), x0 + (sx + 75 + 40) * k

    for variant, fg, ar_fill in (("", INK, BRICK), ("-white", LIME, SAND)):
        q_svg, x_text = route_q(fg, 4)
        width = x_text + w_lat + 4
        ar_svg = ""
        if ar:
            d_ar, w_ar = ar
            ar_x = width + 16
            ar_svg = (f'<rect x="{width + 6:.1f}" y="18" width="1.5" height="30" fill="{ar_fill}" opacity=".6"/>'
                      f'<path transform="translate({ar_x:.1f} {base})" fill="{ar_fill}" d="{d_ar}"/>')
            width = ar_x + w_ar + 4
        write(f"qafila-logo{variant}.svg", f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} 60">
  <title>Qafila</title>
  {q_svg}
  <path transform="translate({x_text:.2f} {base})" fill="{fg}" d="{d_lat}"/>
  {ar_svg}
</svg>""")

    for name, w in (("qafila-symbol.svg", 512), ("qafila-symbol.svg", 180), ("qafila-symbol.svg", 32),
                    ("qafila-logo.svg", 600), ("qafila-logo-white.svg", 600)):
        png(name, w)
    print("Logos générés dans", OUT, "(arabe inclus)" if ar else "(sans arabe : police Thmanyah absente)")


if __name__ == "__main__":
    main()
