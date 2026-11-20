#!/usr/bin/env python3
"""Illustrations plates des produits/services Qafila (SVG → PNG 512 px).

Usage : python3 build_products.py   (nécessite rsvg-convert)
Sortie : brand/products/<REF>.svg|png — utilisées par scripts/seed.py et la landing.
"""
import subprocess
from pathlib import Path

INK, BLUE, BRICK, HENNA, PALM, SAND, LIME = "#16213A", "#1F5FAD", "#C27C2C", "#B4472A", "#2F5D46", "#EAD9BE", "#F7F3EA"
OUT = Path(__file__).resolve().parent / "products"


def tile(body, bg=SAND):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
<rect width="200" height="200" rx="28" fill="{bg}"/>
<path d="M0 160 H200" stroke="{INK}" stroke-opacity=".12" stroke-width="2"/>
{body}
</svg>"""


def truck(x=30, y=88, body=BLUE, scale=1.0, label=None):
    s = scale
    lab = f'<text x="{x + 52 * s}" y="{y + 30 * s}" font-family="Familjen Grotesk" font-weight="700" font-size="{15 * s}" fill="{LIME}" text-anchor="middle">{label}</text>' if label else ""
    return f"""<g>
<rect x="{x}" y="{y}" width="{104 * s}" height="{58 * s}" rx="{6 * s}" fill="{body}"/>
<path d="M{x + 104 * s} {y + 16 * s} h{24 * s} l{16 * s} {18 * s} v{24 * s} h-{40 * s} z" fill="{INK}"/>
<rect x="{x + 110 * s}" y="{y + 21 * s}" width="{14 * s}" height="{12 * s}" rx="2" fill="{LIME}" opacity=".85"/>
<circle cx="{x + 24 * s}" cy="{y + 62 * s}" r="{11 * s}" fill="{INK}"/><circle cx="{x + 24 * s}" cy="{y + 62 * s}" r="{4 * s}" fill="{SAND}"/>
<circle cx="{x + 120 * s}" cy="{y + 62 * s}" r="{11 * s}" fill="{INK}"/><circle cx="{x + 120 * s}" cy="{y + 62 * s}" r="{4 * s}" fill="{SAND}"/>
{lab}</g>"""


def route(label_a, label_b):
    return f"""<path d="M34 50 C 80 20 120 70 166 40" fill="none" stroke="{BRICK}" stroke-width="3" stroke-dasharray="5 7" stroke-linecap="round"/>
<circle cx="34" cy="50" r="7" fill="{BRICK}"/><circle cx="166" cy="40" r="8" fill="{HENNA}"/>
<text x="34" y="74" font-family="Familjen Grotesk" font-size="12" font-weight="700" fill="{INK}" text-anchor="middle">{label_a}</text>
<text x="166" y="64" font-family="Familjen Grotesk" font-size="12" font-weight="700" fill="{INK}" text-anchor="middle">{label_b}</text>"""


def pallet(x, y, w=120):
    return f"""<g fill="{BRICK}">
<rect x="{x}" y="{y}" width="{w}" height="8" rx="2"/>
<rect x="{x}" y="{y + 18}" width="{w}" height="8" rx="2"/>
<rect x="{x + 4}" y="{y + 8}" width="14" height="10"/><rect x="{x + w / 2 - 7}" y="{y + 8}" width="14" height="10"/><rect x="{x + w - 18}" y="{y + 8}" width="14" height="10"/>
</g>"""


def box(x, y, w, h, fill=BRICK):
    return f"""<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{fill}"/>
<path d="M{x + w / 2 - 8} {y} v{h * .4} h16 v-{h * .4}" fill="{LIME}" opacity=".55"/>"""


ITEMS = {
    "QF-TR-SOU": tile(route("Tunis", "Sousse") + truck(label="QAFILA")),
    "QF-TR-SFX": tile(route("Tunis", "Sfax") + truck(label="QAFILA")),
    "QF-TR-TOZ": tile(route("Tunis", "Tozeur") + truck(label="QAFILA")
                      + f'<g fill="{PALM}"><path d="M186 160 v-36" stroke="{PALM}" stroke-width="4"/><path d="M186 124 q-18 -4 -24 8 q12 -10 24 -8 q-6 -16 -22 -14 q14 -2 22 14 q8 -16 24 -12 q-16 0 -24 12 q16 -6 26 6 q-14 -8 -26 -6z"/></g>'),
    "QF-FTL-19": tile(truck(x=14, y=74, body=INK, scale=1.15, label="19 t")
                      + f'<text x="100" y="48" font-family="Familjen Grotesk" font-size="20" font-weight="800" fill="{BLUE}" text-anchor="middle">CAMION COMPLET</text>'),
    "QF-EXP": tile(f"""<g transform="translate(40 70)">
<rect x="0" y="10" width="70" height="56" rx="8" fill="{HENNA}"/><path d="M70 26 h22 l18 20 v20 h-40z" fill="{INK}"/>
<circle cx="20" cy="70" r="11" fill="{INK}"/><circle cx="90" cy="70" r="11" fill="{INK}"/>
<path d="M-30 24 h22 M-36 40 h28 M-26 56 h18" stroke="{BRICK}" stroke-width="5" stroke-linecap="round"/></g>
<text x="100" y="48" font-family="Familjen Grotesk" font-size="22" font-weight="800" fill="{INK}" text-anchor="middle">24 h</text>"""),
    "QF-STK": tile(f"""<path d="M30 160 V70 L100 38 L170 70 V160" fill="{INK}"/>
<rect x="48" y="86" width="104" height="74" fill="{LIME}"/>
{box(56, 132, 26, 22)}{box(87, 132, 26, 22)}{box(118, 132, 26, 22, BLUE)}{box(70, 106, 26, 22, BLUE)}{box(103, 106, 26, 22)}"""),
    "QF-FRD": tile(f"""<path d="M30 160 V70 L100 38 L170 70 V160" fill="{BLUE}"/>
<rect x="48" y="86" width="104" height="74" fill="{LIME}"/>
<g stroke="{BLUE}" stroke-width="6" stroke-linecap="round"><path d="M100 96 v52 M78 109 l44 26 M78 135 l44 -26"/></g>
<text x="100" y="64" font-family="Familjen Grotesk" font-size="14" font-weight="800" fill="{LIME}" text-anchor="middle">2–8 °C</text>"""),
    "QF-DOU": tile(f"""<rect x="52" y="34" width="96" height="124" rx="8" fill="{LIME}" stroke="{INK}" stroke-width="3"/>
<path d="M68 60 h64 M68 76 h64 M68 92 h40" stroke="{INK}" stroke-opacity=".35" stroke-width="5" stroke-linecap="round"/>
<g transform="rotate(-14 112 126)"><rect x="76" y="108" width="74" height="36" rx="6" fill="none" stroke="{HENNA}" stroke-width="4"/>
<text x="113" y="132" font-family="Familjen Grotesk" font-size="14" font-weight="800" fill="{HENNA}" text-anchor="middle">DOUANE</text></g>"""),
    "QF-MAN": tile(f"""<g transform="translate(36 52)">
<rect x="0" y="40" width="70" height="56" rx="6" fill="{PALM}"/><rect x="10" y="10" width="44" height="34" rx="4" fill="none" stroke="{INK}" stroke-width="6"/>
<path d="M70 20 v76 M70 96 h56" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>
<circle cx="18" cy="104" r="10" fill="{INK}"/><circle cx="58" cy="104" r="10" fill="{INK}"/>
{box(84, 56, 36, 34)}</g>"""),
    "QF-PAL": tile(pallet(40, 112) + pallet(40, 84) + pallet(40, 56)),
    "QF-CRT": tile(box(36, 96, 58, 58) + box(104, 96, 58, 58) + box(70, 40, 58, 58)),
    "QF-FLM": tile(f"""<rect x="58" y="44" width="56" height="112" rx="10" fill="{BLUE}" opacity=".35"/>
<rect x="58" y="44" width="56" height="112" rx="10" fill="none" stroke="{BLUE}" stroke-width="4"/>
<ellipse cx="86" cy="44" rx="28" ry="9" fill="{LIME}" stroke="{BLUE}" stroke-width="4"/><ellipse cx="86" cy="44" rx="7" ry="3" fill="{INK}"/>
<path d="M114 70 C 140 74 150 90 160 140" fill="none" stroke="{BLUE}" stroke-opacity=".55" stroke-width="14"/>"""),
}


def main():
    OUT.mkdir(exist_ok=True)
    for ref, svg in ITEMS.items():
        path = OUT / f"{ref}.svg"
        path.write_text(svg, encoding="utf-8")
        subprocess.run(["rsvg-convert", "-w", "512", str(path), "-o", str(OUT / f"{ref}.png")], check=True)
    print(len(ITEMS), "illustrations générées dans", OUT)


if __name__ == "__main__":
    main()
