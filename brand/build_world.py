#!/usr/bin/env python3
"""Génère landing/assets/img/world.html — le décor du site vitrine.

Un seul voyage, du nord au sud, qui évolue au défilement (piloté par assets/js/qafila.js) :
  scène 0  Golfe de Tunis   : Boukornine, Sidi Bou Saïd, port de Radès, porte-conteneurs
  scène 1  Sahel            : oliveraies, ribat, route en pointillés, camion Qafila
  scène 2  Djérid (Tozeur)  : façades en briques sculptées, palmeraie, dunes
  scène 3  Sahara, crépuscule : dunes, caravane de dromadaires
  scène 4  Sahara, nuit     : campement, feu, étoiles

Palette : uniquement les teintes des jetons de docs/02-BRAND.md (et leurs mélanges).
Aucune dépendance. Sortie déterministe (graine fixe) :  python3 brand/build_world.py
"""
import math
import random
from pathlib import Path

W, H = 1600, 900
OUT = Path(__file__).resolve().parent.parent / "landing" / "assets" / "img" / "world.html"
ACTORS = {}  # éléments mobiles (camion, caravane) sortis du décor pour être animés en GPU

# --- Jetons de marque -------------------------------------------------------
INK, BLUE, BRICK, HENNA, PALM, SAND, LIME = "#16213A", "#1F5FAD", "#C27C2C", "#B4472A", "#2F5D46", "#EAD9BE", "#F7F3EA"


def hx(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    """Mélange deux couleurs de la palette (t = part de b)."""
    a, b = hx(a), hx(b)
    return "#" + "".join(f"{round(a[i] + (b[i] - a[i]) * t):02X}" for i in range(3))


def n(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


# --- Géométrie --------------------------------------------------------------
def smooth(pts):
    """Catmull-Rom → Bézier cubiques."""
    d = f"M{n(pts[0][0])},{n(pts[0][1])}"
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{n(c1[0])},{n(c1[1])} {n(c2[0])},{n(c2[1])} {n(p2[0])},{n(p2[1])}"
    return d


def profile(rng, y, amp, count, x0=-260, x1=W + 260, waves=None):
    pts = []
    for i in range(count + 1):
        x = x0 + (x1 - x0) * i / count
        dy = rng.uniform(-amp, amp)
        if waves:
            dy = sum(a * math.sin(x / p + ph) for a, p, ph in waves) + rng.uniform(-amp, amp) * .25
        pts.append((x, y + dy))
    return pts


def land(pts, bottom=H + 20):
    return smooth(pts) + f" L{n(pts[-1][0])},{bottom} L{n(pts[0][0])},{bottom} Z"


def y_at(pts, x):
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        if xa <= x <= xb:
            return ya + (yb - ya) * (x - xa) / (xb - xa)
    return pts[-1][1]


def anim_translate(values, dur, begin="0s"):
    return (f'<animateTransform attributeName="transform" type="translate" values="{values}" '
            f'dur="{dur}" begin="{begin}" repeatCount="indefinite" calcMode="spline" '
            f'keySplines="{";".join([".45 0 .55 1"] * (values.count(";")))}"/>')


def anim_rotate(a, cx, cy, dur, begin="0s"):
    return (f'<animateTransform attributeName="transform" type="rotate" '
            f'values="{-a} {cx} {cy};{a} {cx} {cy};{-a} {cx} {cy}" dur="{dur}" begin="{begin}" '
            f'repeatCount="indefinite" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/>')


# --- Bibliothèque de motifs (defs) -----------------------------------------
def defs():
    olive_leaf = [mix(PALM, SAND, .35), mix(PALM, SAND, .5), mix(PALM, LIME, .62), mix(PALM, INK, .1)]
    rng = random.Random(7)
    # Olivier : tronc noueux, houppier en grappes de feuilles
    canopy = []
    for _ in range(26):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0, 1) ** .6
        cx, cy = math.cos(a) * 30 * r, -58 + math.sin(a) * 17 * r
        canopy.append(f'<ellipse cx="{n(cx)}" cy="{n(cy)}" rx="{n(rng.uniform(7, 12))}" ry="{n(rng.uniform(5, 8))}" '
                      f'fill="{rng.choice(olive_leaf[:2])}"/>')
    for _ in range(14):
        a = rng.uniform(math.pi * 1.05, math.pi * 1.95)
        cx, cy = math.cos(a) * rng.uniform(8, 26), -60 + math.sin(a) * rng.uniform(4, 14)
        canopy.append(f'<ellipse cx="{n(cx)}" cy="{n(cy)}" rx="{n(rng.uniform(3, 6))}" ry="{n(rng.uniform(2, 4))}" fill="{olive_leaf[2]}"/>')
    for _ in range(10):
        a = rng.uniform(.1, math.pi - .1)
        cx, cy = math.cos(a) * rng.uniform(10, 28), -56 + math.sin(a) * rng.uniform(4, 14)
        canopy.append(f'<ellipse cx="{n(cx)}" cy="{n(cy)}" rx="{n(rng.uniform(4, 8))}" ry="{n(rng.uniform(2, 4))}" fill="{olive_leaf[3]}" opacity=".55"/>')
    trunk = mix(INK, BRICK, .35)
    olive = (f'<g id="olive"><ellipse cx="2" cy="1" rx="30" ry="5" fill="{INK}" opacity=".12"/>'
             f'<path d="M-6,0 C-2,-8 -9,-16 -3,-26 C1,-33 -6,-40 -2,-48 L3,-48 C2,-40 8,-33 5,-26 C2,-16 9,-8 7,0 Z" fill="{trunk}"/>'
             f'<path d="M-2,-36 C-8,-42 -16,-44 -20,-50 M3,-38 C9,-44 15,-45 20,-52" stroke="{trunk}" stroke-width="3" fill="none" stroke-linecap="round"/>'
             f'{"".join(canopy)}</g>')

    # Palmier dattier : stipe annelé, palmes à folioles, régimes de dattes
    rng = random.Random(11)
    stipe = mix(INK, BRICK, .45)
    rings = "".join(
        f'<path d="M{n(-5 + i * .12)},{-i * 9 - 4} q5,-3 10,0" stroke="{mix(stipe, INK, .3)}" stroke-width="1.6" fill="none"/>'
        for i in range(15))
    fronds = []
    for k in range(11):
        ang = -math.pi / 2 + (k - 5) * .3 + rng.uniform(-.08, .08)
        L = rng.uniform(62, 80)
        tx, ty = math.cos(ang) * L, math.sin(ang) * L * .75 + abs(k - 5) * 7
        mx, my = tx * .5, ty * .5 - 16
        col = rng.choice([mix(PALM, SAND, .15), mix(PALM, SAND, .3), PALM, mix(PALM, INK, .2)])
        leaflets = []
        for j in range(1, 9):
            t = j / 9
            px = (1 - t) ** 2 * 0 + 2 * (1 - t) * t * mx + t * t * tx
            py = (1 - t) ** 2 * 0 + 2 * (1 - t) * t * my + t * t * ty
            ll = 16 * (1 - t * .55)
            for s in (-1, 1):
                leaflets.append(f'M{n(px)},{n(py)} l{n(s * ll * .5)},{n(ll * .85)}')
        fronds.append(f'<path d="M0,0 Q{n(mx)},{n(my)} {n(tx)},{n(ty)}" stroke="{col}" stroke-width="3" fill="none"/>'
                      f'<path d="{" ".join(leaflets)}" stroke="{col}" stroke-width="2.4" stroke-linecap="round" fill="none"/>')
    dates = "".join(f'<circle cx="{n(rng.uniform(-9, 9))}" cy="{n(rng.uniform(4, 16))}" r="2.6" fill="{rng.choice([BRICK, HENNA, mix(BRICK, HENNA, .5)])}"/>'
                    for _ in range(18))
    palm = (f'<g id="palm"><ellipse cx="0" cy="1" rx="26" ry="4" fill="{INK}" opacity=".12"/>'
            f'<path d="M-6,0 C-5,-50 -2,-100 1,-138 L9,-138 C7,-100 6,-50 6,0 Z" fill="{stipe}"/>{rings}'
            f'<g transform="translate(5 -138)">{dates}{"".join(fronds)}</g></g>')

    # Figuier de Barbarie (hindi) : raquettes et fruits
    rng = random.Random(5)
    pads = []
    spec = [(0, -14, 13, 17, 0), (-14, -34, 10, 14, -25), (13, -36, 10, 14, 20), (-2, -50, 9, 13, 5), (24, -18, 9, 12, 35), (-24, -14, 9, 12, -40)]
    for x, y, rx, ry, rot in spec:
        c = rng.choice([mix(PALM, SAND, .3), mix(PALM, SAND, .45)])
        pads.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" transform="rotate({rot} {x} {y})" fill="{c}"/>'
                    f'<ellipse cx="{x - 3}" cy="{y - 3}" rx="{rx * .45}" ry="{ry * .5}" transform="rotate({rot} {x} {y})" fill="{mix(PALM, LIME, .55)}" opacity=".5"/>')
        for _ in range(3):
            a = rng.uniform(-math.pi, 0)
            pads.append(f'<ellipse cx="{n(x + math.cos(a) * rx * .95)}" cy="{n(y + math.sin(a) * ry * .95)}" rx="2.6" ry="3.4" fill="{rng.choice([HENNA, BRICK])}"/>')
    cactus = f'<g id="cactus"><ellipse cx="0" cy="1" rx="30" ry="4" fill="{INK}" opacity=".12"/>{"".join(pads)}</g>'

    # Dromadaire chargé (orienté vers la droite, pieds à y=0)
    camel_body = ("M8,-64 C12,-82 30,-98 52,-100 C70,-101 82,-88 88,-74 C93,-72 99,-76 103,-86 C106,-98 113,-106 121,-106 "
                  "C129,-106 134,-100 132,-93 L125,-91 C120,-89 118,-82 116,-74 C112,-60 104,-53 97,-50 L95,-24 L97,0 L91,0 L88,-24 "
                  "L86,-47 L76,-47 L74,-24 L72,0 L66,0 L66,-24 L64,-49 C52,-49 40,-49 31,-51 L29,-24 L31,0 L25,0 L22,-24 L20,-53 "
                  "L14,-53 L12,-24 L13,0 L7,0 L6,-24 L5,-51 C1,-55 2,-61 8,-64 Z")

    def camel(fill, blanket, load):
        return (f'<path d="{camel_body}" fill="{fill}"/>'
                f'<path d="M6,-60 C0,-56 -2,-46 0,-36" stroke="{fill}" stroke-width="3" fill="none" stroke-linecap="round"/>'
                f'<path d="M30,-94 C40,-104 64,-104 74,-94 L78,-74 L26,-74 Z" fill="{blanket}"/>'
                f'<path d="M26,-74 L78,-74" stroke="{LIME}" stroke-width="2" stroke-dasharray="3 3" opacity=".8"/>'
                + "".join(f'<path d="M{28 + i * 5},-74 v7" stroke="{blanket}" stroke-width="1.6"/>' for i in range(11))
                + f'<rect x="38" y="-112" width="24" height="16" rx="2" fill="{load}"/>'
                f'<path d="M38,-104 h24 M50,-112 v16" stroke="{mix(load, INK, .35)}" stroke-width="1.4"/>')
    camel_dusk = camel(mix(INK, HENNA, .45), HENNA, SAND)
    camel_night = camel(mix(INK, BLUE, .12), mix(HENNA, INK, .45), mix(SAND, INK, .55))
    # Chamelier en djellaba et chèche
    def man(fill, cloth):
        return (f'<path d="M0,0 L4,-30 C2,-44 6,-56 12,-58 C18,-56 22,-44 20,-30 L24,0 L16,0 L13,-20 L11,-20 L8,0 Z" fill="{fill}"/>'
                f'<circle cx="12" cy="-64" r="6" fill="{fill}"/><path d="M5,-66 C8,-74 18,-74 20,-66 C16,-68 9,-68 5,-66 Z" fill="{cloth}"/>'
                f'<path d="M20,-44 L34,-30" stroke="{fill}" stroke-width="3" stroke-linecap="round"/>'
                f'<path d="M34,-30 L40,4" stroke="{mix(fill, INK, .3)}" stroke-width="2"/>')

    # Camion Qafila (porteur 19 t, vue de profil, roule vers la droite)
    truck = (f'<g id="truck-art">'
             f'<ellipse cx="110" cy="2" rx="118" ry="7" fill="{INK}" opacity=".18"/>'
             f'<rect x="0" y="-104" width="160" height="82" rx="4" fill="{BLUE}"/>'
             + "".join(f'<path d="M{8 + i * 12},-98 v70" stroke="{mix(BLUE, INK, .22)}" stroke-width="1.4"/>' for i in range(13))
             + f'<rect x="0" y="-104" width="160" height="10" fill="{mix(BLUE, INK, .3)}"/>'
             f'<text x="80" y="-52" text-anchor="middle" class="w-truck-text" fill="{LIME}">qafila</text>'
             f'<path d="M22,-40 h116" stroke="{BRICK}" stroke-width="3" stroke-dasharray="7 6" stroke-linecap="round"/>'
             f'<circle cx="22" cy="-40" r="4.5" fill="{BRICK}"/><circle cx="138" cy="-40" r="5" fill="{HENNA}"/>'
             f'<path d="M164,-88 L196,-88 C204,-88 210,-80 214,-70 L222,-50 L222,-18 L164,-18 Z" fill="{INK}"/>'
             f'<path d="M172,-82 L194,-82 C199,-82 203,-77 206,-70 L211,-58 L172,-58 Z" fill="{mix(BLUE, LIME, .55)}"/>'
             f'<path d="M176,-80 L184,-60" stroke="{LIME}" stroke-width="2" opacity=".6"/>'
             f'<rect x="216" y="-34" width="8" height="6" rx="1" fill="{BRICK}"/>'
             f'<rect x="-4" y="-22" width="230" height="8" rx="2" fill="{mix(INK, LIME, .2)}"/>'
             + "".join(f'<g transform="translate({x} -8)"><circle r="15" fill="{INK}"/><circle r="7" fill="{mix(INK, LIME, .6)}"/>'
                       f'<g class="w-wheel"><path d="M-6,0 h12 M0,-6 v12" stroke="{INK}" stroke-width="2"/></g></g>' for x in (32, 66, 192))
             + '</g>')

    # Textures : briques du Djérid, ondulations
    patterns = (
        f'<pattern id="bricks" width="24" height="12" patternUnits="userSpaceOnUse">'
        f'<rect width="24" height="12" fill="{mix(BRICK, SAND, .32)}"/>'
        f'<rect x="1" y="1" width="10" height="4" fill="{mix(BRICK, SAND, .18)}"/><rect x="13" y="1" width="10" height="4" fill="{mix(BRICK, SAND, .24)}"/>'
        f'<rect x="-5" y="7" width="10" height="4" fill="{mix(BRICK, SAND, .2)}"/><rect x="7" y="7" width="10" height="4" fill="{mix(BRICK, SAND, .14)}"/>'
        f'<rect x="19" y="7" width="10" height="4" fill="{mix(BRICK, SAND, .2)}"/></pattern>'
        f'<pattern id="bricks-dusk" width="24" height="12" patternUnits="userSpaceOnUse">'
        f'<rect width="24" height="12" fill="{mix(BRICK, HENNA, .3)}"/>'
        f'<rect x="1" y="1" width="10" height="4" fill="{mix(BRICK, HENNA, .45)}"/><rect x="13" y="1" width="10" height="4" fill="{BRICK}"/></pattern>'
        f'<pattern id="corrug" width="6" height="10" patternUnits="userSpaceOnUse"><rect width="6" height="10" fill="#fff" opacity="0"/>'
        f'<path d="M3,0 v10" stroke="{INK}" stroke-width="1" opacity=".22"/></pattern>'
        f'<pattern id="grille" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="{mix(BLUE, LIME, .15)}"/>'
        f'<path d="M0,4 h8 M4,0 v8" stroke="{mix(BLUE, INK, .35)}" stroke-width="1.4"/><circle cx="4" cy="4" r="1.4" fill="{LIME}"/></pattern>'
        f'<linearGradient id="sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{mix(BLUE, LIME, .55)}"/>'
        f'<stop offset=".5" stop-color="{mix(BLUE, LIME, .32)}"/><stop offset="1" stop-color="{mix(BLUE, INK, .05)}"/></linearGradient>'
        f'<radialGradient id="sun-g"><stop offset="0" stop-color="{mix(BRICK, LIME, .55)}"/><stop offset=".55" stop-color="{mix(BRICK, LIME, .3)}"/>'
        f'<stop offset="1" stop-color="{BRICK}"/></radialGradient>'
        f'<radialGradient id="halo"><stop offset="0" stop-color="{mix(BRICK, LIME, .5)}" stop-opacity=".55"/>'
        f'<stop offset="1" stop-color="{mix(BRICK, LIME, .5)}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="fire-g"><stop offset="0" stop-color="{mix(BRICK, LIME, .4)}" stop-opacity=".9"/>'
        f'<stop offset="1" stop-color="{HENNA}" stop-opacity="0"/></radialGradient>'
        f'<mask id="crescent"><circle cx="0" cy="0" r="34" fill="#fff"/><circle cx="14" cy="-8" r="30" fill="#000"/></mask>'
    )
    return (f'<defs>{patterns}{olive}{palm}{cactus}{truck}'
            f'<g id="camel-dusk">{camel_dusk}</g><g id="camel-night">{camel_night}</g>'
            f'<g id="man-dusk">{man(mix(INK, HENNA, .45), BLUE)}</g><g id="man-night">{man(mix(INK, BLUE, .12), mix(BLUE, INK, .4))}</g>'
            f'</defs>')


def use(ref, x, y, s=1, extra=""):
    return f'<use href="#{ref}" transform="translate({n(x)} {n(y)}) scale({n(s) if s != int(s) else int(s)})"{extra}/>'


def layer(depth, body, cls=""):
    """Une couche de profondeur ; regroupées ensuite en 3 calques composités (fond, milieu, avant)."""
    return [(depth, body)]


# --- Ciel : étoiles, soleil, lune, nuages, oiseaux --------------------------
def sky():
    rng = random.Random(3)
    stars = []
    for i in range(230):
        x, y = rng.uniform(0, W), rng.uniform(0, 560) ** 1.05
        r = rng.choice([.7, .9, 1.1, 1.4, 1.9]) if rng.random() > .08 else 2.4
        tw = ""
        if i % 9 == 0:
            tw = (f'<animate attributeName="opacity" values="1;.25;1" dur="{n(rng.uniform(2.5, 5))}s" '
                  f'begin="{n(rng.uniform(0, 4))}s" repeatCount="indefinite"/>')
        stars.append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{r}" fill="{LIME}" opacity="{n(rng.uniform(.45, 1))}">{tw}</circle>')
    # quelques étoiles à quatre branches
    for _ in range(9):
        x, y, s = rng.uniform(80, W - 80), rng.uniform(40, 380), rng.uniform(4, 7)
        stars.append(f'<path d="M{n(x)},{n(y - s)} Q{n(x)},{n(y)} {n(x + s)},{n(y)} Q{n(x)},{n(y)} {n(x)},{n(y + s)} '
                     f'Q{n(x)},{n(y)} {n(x - s)},{n(y)} Q{n(x)},{n(y)} {n(x)},{n(y - s)} Z" fill="{LIME}"/>')
    clouds = []
    for k in range(7):
        cx, cy, sc = rng.uniform(-100, W), rng.uniform(90, 330), rng.uniform(.6, 1.3)
        puffs = "".join(f'<ellipse cx="{n(dx * sc)}" cy="{n(dy * sc)}" rx="{n(rx * sc)}" ry="{n(ry * sc)}"/>'
                        for dx, dy, rx, ry in [(-50, 6, 46, 16), (-12, -8, 38, 24), (30, -2, 44, 20), (66, 8, 34, 12), (0, 10, 90, 12)])
        clouds.append(f'<g fill="{LIME}" opacity="{n(rng.uniform(.55, .85))}" transform="translate({n(cx)} {n(cy)})">'
                      f'<g>{anim_translate(f"0 0;{n(rng.uniform(40, 90))} 0;0 0", f"{n(rng.uniform(50, 80))}s")}{puffs}</g></g>')
    birds = []
    for k in range(6):
        x, y, s = rng.uniform(300, 1300), rng.uniform(220, 400), rng.uniform(.7, 1.2)
        birds.append(f'<g transform="translate({n(x)} {n(y)}) scale({n(s)})"><path d="M-10,0 Q-5,-6 0,0 Q5,-6 10,0" stroke="{INK}" '
                     f'stroke-width="1.8" fill="none" opacity=".55">'
                     f'<animate attributeName="d" values="M-10,0 Q-5,-6 0,0 Q5,-6 10,0;M-10,-3 Q-5,2 0,0 Q5,2 10,-3;M-10,0 Q-5,-6 0,0 Q5,-6 10,0" '
                     f'dur="{n(rng.uniform(.9, 1.4))}s" repeatCount="indefinite"/></path>'
                     f'{anim_translate(f"0 0;{n(rng.uniform(30, 70))} {n(rng.uniform(-14, 14))};0 0", f"{n(rng.uniform(14, 22))}s")}</g>')
    sun = (f'<g id="w-sun"><circle r="150" fill="url(#halo)"/><circle r="52" fill="url(#sun-g)"/>'
           f'<circle r="64" fill="none" stroke="{mix(BRICK, LIME, .45)}" stroke-width="1.5" stroke-dasharray="4 8" opacity=".7"/></g>')
    moon = (f'<g id="w-moon"><circle r="90" fill="{LIME}" opacity=".06"/>'
            f'<g mask="url(#crescent)"><circle r="34" fill="{LIME}"/>'
            f'<circle cx="-12" cy="10" r="5" fill="{SAND}" opacity=".5"/><circle cx="-20" cy="-8" r="3" fill="{SAND}" opacity=".5"/></g></g>')
    shooting = (f'<path d="M0,0 l-120,48" stroke="{LIME}" stroke-width="1.6" stroke-linecap="round" opacity="0">'
                f'<animate attributeName="opacity" values="0;0;.9;0" keyTimes="0;.9;.93;1" dur="11s" repeatCount="indefinite"/>'
                f'<animateTransform attributeName="transform" type="translate" values="1300 90;1300 90;1180 138;1100 170" keyTimes="0;.9;.95;1" dur="11s" repeatCount="indefinite"/></path>')
    return {"stars": "".join(stars), "sun": sun, "moon": moon, "clouds": "".join(clouds)}


# --- Scène 0 : Golfe de Tunis -----------------------------------------------
def scene_north():
    rng = random.Random(10)
    far_blue = mix(BLUE, LIME, .7)
    # Boukornine (deux sommets) et le Cap Bon au loin
    bouk = [(860, 560), (960, 520), (1040, 470), (1100, 430), (1150, 402), (1186, 396), (1222, 420), (1252, 414), (1290, 386),
            (1330, 404), (1400, 450), (1480, 498), (1580, 530), (1700, 552), (1800, 560)]
    capbon = profile(random.Random(2), 548, 6, 10, x0=1300, x1=1900)
    far = (f'<path d="{land(capbon)}" fill="{mix(BLUE, LIME, .8)}"/>'
           f'<path d="{smooth(bouk)} L1800,600 L860,600 Z" fill="{far_blue}"/>'
           f'<path d="M1186,396 C1200,430 1180,470 1210,520 L1250,560 L1230,470 C1222,440 1240,430 1252,414 Z" fill="{mix(BLUE, LIME, .78)}"/>'
           f'<path d="M1290,386 C1300,420 1330,450 1350,500 L1420,560 L1380,470 Z" fill="{mix(BLUE, LIME, .6)}" opacity=".6"/>')
    # Mer, vagues, porte-conteneurs
    waves = []
    for row in range(16):
        y = 572 + row ** 1.45 * 6.5
        for _ in range(9 + row):
            x = rng.uniform(-200, W + 200)
            w = 6 + row * 1.6
            waves.append(f'<path d="M{n(x)},{n(y)} q{n(w / 2)},-{n(w / 4)} {n(w)},0 t{n(w)},0" />')
    sea = (f'<rect x="-260" y="556" width="{W + 520}" height="360" fill="url(#sea)"/>'
           f'<path d="M-260,557 H{W + 260}" stroke="{LIME}" stroke-width="2" opacity=".6"/>'
           f'<g stroke="{LIME}" stroke-width="1.6" fill="none" stroke-linecap="round" opacity=".55">'
           f'{anim_translate("0 0;18 2;0 0", "9s")}{"".join(waves)}</g>')
    cont_cols = [BLUE, HENNA, BRICK, PALM, SAND, mix(BLUE, LIME, .3), INK]
    boxes = []
    for r in range(3):
        for c in range(9 - r):
            boxes.append(f'<rect x="{30 + c * 30 + r * 10}" y="{-40 - r * 14}" width="28" height="13" fill="{rng.choice(cont_cols)}"/>'
                         f'<rect x="{30 + c * 30 + r * 10}" y="{-40 - r * 14}" width="28" height="13" fill="url(#corrug)"/>')
    ship = (f'<g transform="translate(560 612) scale(.78)"><g>{anim_translate("0 0;0 3;0 0", "4.5s")}'
            f'<path d="M0,-26 L330,-26 L314,4 L18,4 Z" fill="{INK}"/><path d="M4,-18 L326,-18" stroke="{HENNA}" stroke-width="4"/>'
            f'{"".join(boxes)}<rect x="296" y="-74" width="26" height="48" fill="{LIME}"/>'
            f'<rect x="300" y="-68" width="18" height="4" fill="{INK}" opacity=".7"/><rect x="300" y="-58" width="18" height="4" fill="{INK}" opacity=".7"/>'
            f'<path d="M309,-74 v-16" stroke="{INK}" stroke-width="2"/><path d="M309,-90 l14,4 l-14,4" fill="{HENNA}"/>'
            f'<path d="M-40,8 q30,-5 60,0 t60,0" stroke="{LIME}" stroke-width="2" fill="none" opacity=".7"/></g></g>')
    # Port de Radès : quai, portiques, conteneurs empilés
    quay_y = 640
    stacks = []
    for c in range(16):
        h = rng.randint(1, 4)
        for r in range(h):
            col = rng.choice(cont_cols[:6])
            x = 1180 + c * 34
            stacks.append(f'<rect x="{x}" y="{quay_y - 14 - r * 14}" width="32" height="13" fill="{col}"/>'
                          f'<rect x="{x}" y="{quay_y - 14 - r * 14}" width="32" height="13" fill="url(#corrug)"/>')
    cranes = []
    for k, x in enumerate((1210, 1380, 1550)):
        c = HENNA if k != 1 else mix(HENNA, LIME, .25)
        lattice = "".join(f'<path d="M{x + 8},{quay_y - 20 - i * 22} l40,-22 M{x + 48},{quay_y - 20 - i * 22} l-40,-22"/>' for i in range(6))
        cranes.append(f'<g stroke="{c}" fill="none" stroke-width="5" stroke-linejoin="round">'
                      f'<path d="M{x + 8},{quay_y} V{quay_y - 152} M{x + 48},{quay_y} V{quay_y - 152}"/>'
                      f'<g stroke-width="2.2">{lattice}</g>'
                      f'<path d="M{x - 120},{quay_y - 150} H{x + 110} M{x - 120},{quay_y - 150} L{x + 28},{quay_y - 196} L{x + 110},{quay_y - 150}" stroke-width="4"/>'
                      f'<path d="M{x + 28},{quay_y - 196} V{quay_y - 150}" stroke-width="3"/></g>'
                      f'<rect x="{x - 4}" y="{quay_y - 166}" width="20" height="14" fill="{LIME}" stroke="{c}" stroke-width="2"/>'
                      f'<g><path d="M{x - 70},{quay_y - 150} v58" stroke="{INK}" stroke-width="1.5"/>'
                      f'<rect x="{x - 86}" y="{quay_y - 92}" width="32" height="13" fill="{rng.choice(cont_cols[:4])}"/>'
                      f'{anim_translate("0 0;0 26;0 26;0 0", f"{7 + k}s")}</g>')
    port = (f'<rect x="1120" y="{quay_y}" width="800" height="22" fill="{mix(SAND, INK, .15)}"/>'
            f'<path d="M1120,{quay_y} H1920" stroke="{LIME}" stroke-width="2"/>'
            + "".join(f'<rect x="{1130 + i * 46}" y="{quay_y + 6}" width="6" height="10" fill="{INK}" opacity=".35"/>' for i in range(17))
            + "".join(stacks) + "".join(cranes))
    # Sidi Bou Saïd : colline, maisons blanches, portes et grilles bleues, coupole, minaret, bougainvilliers
    hill = [(-260, 600), (-100, 560), (60, 546), (200, 556), (340, 590), (480, 640), (620, 700), (760, 770), (900, 860), (980, 920)]
    houses = []
    rows = [(565, .62, (-120, 300)), (600, .74, (-180, 420)), (640, .86, (-200, 520)), (690, 1.0, (-220, 640)), (750, 1.12, (-240, 760))]
    white, shade = mix(LIME, "#FFFFFF", .6), mix(SAND, LIME, .35)
    for base, s, (xa, xb) in rows:
        x = xa
        while x < xb:
            w = rng.uniform(58, 104) * s
            h = rng.uniform(48, 86) * s
            top = base - h
            if base - 10 > y_at(hill, x + w / 2) + 70 * s or True:
                g = [f'<rect x="{n(x)}" y="{n(top)}" width="{n(w)}" height="{n(h + 40)}" fill="{white}"/>',
                     f'<rect x="{n(x + w * .84)}" y="{n(top)}" width="{n(w * .16)}" height="{n(h + 40)}" fill="{shade}"/>',
                     f'<rect x="{n(x - 2)}" y="{n(top - 4 * s)}" width="{n(w + 4)}" height="{n(5 * s)}" fill="{shade}"/>']
                r = rng.random()
                if r < .45:   # porte bleue cintrée et cloutée
                    dw, dh = 16 * s, 30 * s
                    dx = x + rng.uniform(.15, .55) * w
                    g.append(f'<path d="M{n(dx)},{n(base)} V{n(base - dh + dw / 2)} A{n(dw / 2)},{n(dw / 2)} 0 0 1 {n(dx + dw)},{n(base - dh + dw / 2)} V{n(base)} Z" fill="{BLUE}"/>'
                             f'<path d="M{n(dx - 3 * s)},{n(base)} V{n(base - dh + dw / 2)} A{n(dw / 2 + 3 * s)},{n(dw / 2 + 3 * s)} 0 0 1 {n(dx + dw + 3 * s)},{n(base - dh + dw / 2)} V{n(base)}" fill="none" stroke="{mix(SAND, BRICK, .25)}" stroke-width="{n(2 * s)}"/>'
                             + "".join(f'<circle cx="{n(dx + dw * (.25 + .5 * (i % 2)))}" cy="{n(base - dh * (.25 + .18 * (i // 2)))}" r="{n(1.1 * s)}" fill="{INK}"/>' for i in range(6)))
                if r > .3:    # fenêtre à grille (moucharabieh)
                    ww, wh = 14 * s, 18 * s
                    wx = x + rng.uniform(.1, .6) * w
                    g.append(f'<rect x="{n(wx)}" y="{n(top + h * .25)}" width="{n(ww)}" height="{n(wh)}" fill="url(#grille)"/>'
                             f'<path d="M{n(wx - 2 * s)},{n(top + h * .25)} q{n(ww / 2 + 2 * s)},-{n(8 * s)} {n(ww + 4 * s)},0" fill="{BLUE}"/>')
                if rng.random() < .22:  # coupole
                    cr = w * .26
                    cx = x + w * rng.uniform(.3, .6)
                    g.append(f'<path d="M{n(cx - cr)},{n(top - 3 * s)} A{n(cr)},{n(cr)} 0 0 1 {n(cx + cr)},{n(top - 3 * s)} Z" fill="{white}"/>'
                             f'<path d="M{n(cx + cr * .3)},{n(top - cr * .9)} A{n(cr)},{n(cr)} 0 0 1 {n(cx + cr)},{n(top - 3 * s)} L{n(cx + cr * .4)},{n(top - 3 * s)} Z" fill="{shade}"/>')
                if rng.random() < .35:  # bougainvillier
                    bx, by = x + rng.uniform(0, w), top + rng.uniform(0, h * .5)
                    g.append("".join(f'<circle cx="{n(bx + rng.uniform(-14, 14) * s)}" cy="{n(by + rng.uniform(-8, 10) * s)}" r="{n(rng.uniform(2.5, 5) * s)}" '
                                     f'fill="{rng.choice([HENNA, mix(HENNA, LIME, .25), mix(HENNA, BRICK, .3), mix(PALM, SAND, .3)])}"/>' for _ in range(16)))
                houses.append("".join(g))
            x += w + rng.uniform(-6, 12) * s
    minaret = (f'<g transform="translate(150 470)"><rect x="0" y="0" width="34" height="96" fill="{white}"/>'
               f'<rect x="26" y="0" width="8" height="96" fill="{shade}"/><rect x="-5" y="-8" width="44" height="10" fill="{shade}"/>'
               f'<rect x="6" y="-34" width="22" height="26" fill="{white}"/><path d="M6,-34 L17,-48 L28,-34 Z" fill="{PALM}"/>'
               f'<rect x="12" y="20" width="10" height="16" rx="5" fill="{BLUE}"/><rect x="12" y="50" width="10" height="16" rx="5" fill="{BLUE}"/>'
               f'<path d="M17,-48 v-10" stroke="{BRICK}" stroke-width="2"/><circle cx="17" cy="-60" r="3" fill="{BRICK}"/></g>')
    palms_n = "".join(use("palm", x, y, s) for x, y, s in [(330, 600, .55), (-40, 575, .5), (470, 650, .7)])
    # Balustrade bleue au premier plan
    rail = (f'<g transform="translate(-260 812)"><rect width="1140" height="10" fill="{BLUE}"/>'
            + "".join(f'<path d="M{20 + i * 22},10 v58 M{9 + i * 22},10 q11,26 22,0 M{9 + i * 22},68 q11,-26 22,0" stroke="{BLUE}" stroke-width="3" fill="none"/>' for i in range(51))
            + f'<rect y="68" width="1140" height="8" fill="{BLUE}"/></g>'
            f'<g transform="translate(700 812)"><path d="M0,0 C10,-30 40,-30 50,0 Z" fill="{HENNA}"/><rect x="5" y="0" width="40" height="40" fill="{mix(BRICK, SAND, .2)}"/>'
            f'<g fill="{mix(PALM, SAND, .2)}">' + "".join(f'<ellipse cx="{25 + rng.uniform(-22, 22)}" cy="{-8 + rng.uniform(-30, 4)}" rx="9" ry="4" transform="rotate({rng.randint(-50, 50)} 25 -10)"/>' for _ in range(12))
            + "</g></g>")
    near = f'<path d="{land(hill)}" fill="{mix(SAND, LIME, .45)}"/>{minaret}{palms_n}{"".join(houses)}{rail}'
    return (layer(.15, far) + layer(.3, sea) + layer(.45, ship + port) + layer(1, near))


# --- Scène 1 : Sahel --------------------------------------------------------
def scene_sahel():
    rng = random.Random(21)
    far_pts = profile(rng, 528, 0, 14, waves=[(16, 140, 0), (8, 60, 1.2)])
    far2 = profile(rng, 556, 0, 16, waves=[(12, 110, 2), (6, 45, .3)])
    far_dots = "".join(f'<ellipse cx="{n(x)}" cy="{n(y_at(far2, x) + rng.uniform(4, 30))}" rx="3.2" ry="2.2" fill="{mix(PALM, SAND, .55)}"/>'
                       for x in [rng.uniform(-240, W + 240) for _ in range(220)])
    far = (f'<path d="{land(far_pts)}" fill="{mix(PALM, LIME, .78)}"/>'
           f'<path d="{land(far2)}" fill="{mix(PALM, SAND, .7)}"/>{far_dots}')
    # Ribat (tour ronde crénelée) sur une butte
    rib = (f'<path d="M1020,600 C1080,560 1140,548 1240,546 C1340,548 1400,560 1470,600 Z" fill="{mix(PALM, SAND, .62)}"/>'
           f'<g transform="translate(1240 556)">'
           f'<rect x="-120" y="-50" width="240" height="60" fill="{mix(SAND, BRICK, .18)}"/>'
           + "".join(f'<rect x="{-120 + i * 16}" y="-60" width="10" height="12" fill="{mix(SAND, BRICK, .18)}"/>' for i in range(15))
           + f'<rect x="-30" y="-150" width="60" height="140" fill="{mix(SAND, BRICK, .1)}"/><rect x="12" y="-150" width="18" height="140" fill="{mix(SAND, BRICK, .28)}"/>'
           + "".join(f'<rect x="{-30 + i * 13}" y="-162" width="8" height="14" fill="{mix(SAND, BRICK, .1)}"/>' for i in range(5))
           + f'<rect x="-4" y="-120" width="5" height="16" fill="{INK}" opacity=".6"/><rect x="-4" y="-80" width="5" height="16" fill="{INK}" opacity=".6"/>'
           f'<path d="M-14,10 V-18 A14,14 0 0 1 14,-18 V10 Z" fill="{mix(INK, BRICK, .3)}"/>'
           f'<path d="M0,-162 v-26" stroke="{INK}" stroke-width="2"/><path d="M0,-188 h22 l-5,7 l5,7 h-22 Z" fill="{HENNA}">'
           f'{anim_rotate(4, 0, -181, "3s")}</path></g>')
    field = profile(rng, 600, 0, 12, waves=[(14, 200, .4), (6, 70, 2)])
    furrows = "".join(f'<path d="{smooth([(x, y_at(field, x) + 18 + k * 22 + 8 * math.sin(x / 90 + k)) for x in range(-240, W + 260, 80)])}" '
                      f'stroke="{mix(BRICK, SAND, .55)}" stroke-width="2" fill="none" opacity=".55"/>' for k in range(11))
    olives = []
    for row, (yo, s, gap) in enumerate([(18, .42, 52), (52, .55, 66), (96, .7, 84), (152, .88, 108)]):
        x = -240 + rng.uniform(0, gap)
        while x < W + 240:
            olives.append(use("olive", x, y_at(field, x) + yo, s * rng.uniform(.9, 1.1)))
            x += gap * rng.uniform(.85, 1.15)
    mid = f'<path d="{land(field)}" fill="{mix(BRICK, SAND, .72)}"/>{furrows}{"".join(olives)}'
    # Route, poteaux, cactus, panneau
    road_y = 812
    poles = "".join(f'<g transform="translate({x} {road_y - 22})"><path d="M0,0 V-150" stroke="{mix(INK, BRICK, .4)}" stroke-width="5"/>'
                    f'<path d="M-18,-140 H18" stroke="{mix(INK, BRICK, .4)}" stroke-width="4"/></g>' for x in range(-200, W + 260, 300))
    wires = "".join(f'<path d="M{x - 18},{road_y - 162} Q{x + 132},{road_y - 132} {x + 282},{road_y - 162} M{x + 18},{road_y - 162} Q{x + 168},{road_y - 128} {x + 318},{road_y - 162}" '
                    f'stroke="{INK}" stroke-width="1.2" fill="none" opacity=".45"/>' for x in range(-200, W + 260, 300))
    sign = (f'<g transform="translate(1390 {road_y - 22})"><path d="M0,0 V-96" stroke="{mix(INK, LIME, .4)}" stroke-width="5"/>'
            f'<rect x="-60" y="-150" width="120" height="62" rx="6" fill="{BLUE}"/><rect x="-55" y="-145" width="110" height="52" rx="4" fill="none" stroke="{LIME}" stroke-width="2"/>'
            f'<text x="0" y="-122" text-anchor="middle" class="w-sign-ar" fill="{LIME}">صفاقس</text>'
            f'<text x="0" y="-100" text-anchor="middle" class="w-sign" fill="{LIME}">Sfax 127</text></g>')
    cacti = "".join(use("cactus", x, road_y + y, s) for x, y, s in [(80, 74, 1.3), (520, 88, 1.1), (980, 70, 1.4), (1500, 84, 1.2), (-150, 80, 1)])
    near = (f'<path d="M-260,{road_y - 34} H{W + 260} V{H + 20} H-260 Z" fill="{mix(BRICK, SAND, .6)}"/>{poles}{wires}{sign}'
            f'<rect x="-260" y="{road_y - 20}" width="{W + 520}" height="52" fill="{mix(INK, LIME, .25)}"/>'
            f'<path d="M-260,{road_y - 20} H{W + 260} M-260,{road_y + 32} H{W + 260}" stroke="{LIME}" stroke-width="3" opacity=".8"/>'
            f'<path d="M-260,{road_y + 6} H{W + 260}" stroke="{BRICK}" stroke-width="4" stroke-dasharray="34 26"/>'
            f'{cacti}')
    ACTORS["truck"] = dict(scene=1, x=0, y=road_y + 14, box=(-10, -122, 252, 140), scale=1.05, body='<use href="#truck-art"/>')
    return layer(.15, far) + layer(.3, rib) + layer(.55, mid) + layer(1, near)


# --- Scène 2 : Djérid, Tozeur -----------------------------------------------
MOTIFS = {
    "losange": ["...#...", "..#.#..", ".#...#.", "#..#..#", ".#...#.", "..#.#..", "...#..."],
    "chevron": ["#.....#", ".#...#.", "..#.#..", "...#..."],
    "croix": ["..#..", "..#..", "#####", "..#..", "..#.."],
    "damier": ["#.#.#.#", ".#.#.#."],
}


def motif(name, x, y, cell, color):
    out = []
    for r, line in enumerate(MOTIFS[name]):
        for c, ch in enumerate(line):
            if ch == "#":
                out.append(f'<rect x="{n(x + c * cell)}" y="{n(y + r * cell * .55)}" width="{n(cell * .8)}" height="{n(cell * .42)}" fill="{color}"/>')
    return "".join(out)


def scene_south():
    rng = random.Random(31)
    d1 = profile(rng, 520, 0, 18, waves=[(26, 170, .2), (10, 64, 1.7)])
    d2 = profile(rng, 556, 0, 18, waves=[(20, 130, 1.1), (8, 50, .4)])
    ripples = "".join(f'<path d="M{n(x)},{n(y_at(d2, x) + 16 + k * 9)} q20,-5 40,0 t40,0" stroke="{mix(BRICK, LIME, .5)}" stroke-width="1.4" fill="none" opacity=".6"/>'
                      for x in [rng.uniform(-240, W + 200) for _ in range(40)] for k in range(2))
    far = f'<path d="{land(d1)}" fill="{mix(BRICK, LIME, .72)}"/><path d="{land(d2)}" fill="{mix(BRICK, LIME, .6)}"/>{ripples}'
    grove = "".join(use("palm", x, 640 + rng.uniform(-14, 14), rng.uniform(.62, .86)) for x in range(-220, W + 240, 46))
    # Façades de brique sculptée (ksar de Tozeur)
    blocks = []
    x = -240
    base = 770
    dark, light = mix(BRICK, INK, .25), mix(BRICK, LIME, .35)
    while x < W + 240:
        w = rng.uniform(120, 220)
        h = rng.uniform(110, 190)
        top = base - h
        b = [f'<rect x="{n(x)}" y="{n(top)}" width="{n(w)}" height="{n(h + 140)}" fill="url(#bricks)"/>',
             f'<rect x="{n(x + w - 10)}" y="{n(top)}" width="10" height="{n(h + 140)}" fill="{INK}" opacity=".12"/>',
             f'<rect x="{n(x - 3)}" y="{n(top - 6)}" width="{n(w + 6)}" height="7" fill="{dark}"/>']
        for i in range(int(w // 22)):
            b.append(f'<rect x="{n(x + 6 + i * 22)}" y="{n(top - 14)}" width="10" height="9" fill="{dark}"/>')
        cell = 7
        name = rng.choice(list(MOTIFS))
        mw = len(MOTIFS[name][0]) * cell
        reps = max(1, int((w - 20) // (mw + 8)))
        for k in range(reps):
            b.append(motif(name, x + 12 + k * (mw + 8), top + 18, cell, dark))
        b.append(f'<path d="M{n(x + 10)},{n(top + 16 + len(MOTIFS[name]) * cell * .55 + 8)} H{n(x + w - 14)}" stroke="{light}" stroke-width="3"/>')
        if rng.random() < .5:
            gx, gw = x + w * .35, 40
            b.append(f'<path d="M{n(gx)},{base + 140} V{n(base - 34)} A{gw / 2},{gw / 2} 0 0 1 {n(gx + gw)},{n(base - 34)} V{base + 140} Z" fill="{mix(INK, BRICK, .35)}"/>'
                     f'<path d="M{n(gx - 6)},{base + 140} V{n(base - 34)} A{gw / 2 + 6},{gw / 2 + 6} 0 0 1 {n(gx + gw + 6)},{n(base - 34)} V{base + 140}" fill="none" stroke="{dark}" stroke-width="4" stroke-dasharray="6 3"/>')
        else:
            for k in range(2):
                wx = x + w * (.25 + .4 * k)
                b.append(f'<rect x="{n(wx)}" y="{n(top + h * .55)}" width="14" height="20" fill="{mix(INK, BRICK, .3)}"/>'
                         f'<path d="M{n(wx - 3)},{n(top + h * .55)} h20" stroke="{dark}" stroke-width="3"/>')
        if rng.random() < .3:
            b.append(f'<path d="M{n(x + w * .7)},{n(top - 14)} v-30" stroke="{INK}" stroke-width="2"/>'
                     f'<path d="M{n(x + w * .7)},{n(top - 44)} h18 l-4,6 l4,6 h-18 Z" fill="{HENNA}">{anim_rotate(5, round(x + w * .7, 1), round(top - 38, 1), "2.6s")}</path>')
        blocks.append("".join(b))
        x += w + rng.uniform(0, 6)
    town = "".join(blocks)
    near_pts = profile(rng, 820, 0, 10, waves=[(14, 260, .3)])
    near_palms = "".join(use("palm", x, y, s) for x, y, s in [(-60, 900, 1.9), (1540, 910, 2.1), (1240, 880, 1.25), (180, 870, 1.1)])
    wall = f'<rect x="-260" y="836" width="{W + 520}" height="30" fill="url(#bricks)"/><rect x="-260" y="830" width="{W + 520}" height="7" fill="{dark}"/>'
    near = f'<path d="{land(near_pts)}" fill="{mix(BRICK, SAND, .45)}"/>{wall}{near_palms}'
    return layer(.15, far) + layer(.35, grove) + layer(.6, town) + layer(1, near)


# --- Scènes 3 et 4 : Sahara au crépuscule, puis la nuit -----------------------
def dunes(rng, cols):
    out = []
    specs = [(500, [(34, 210, .2), (12, 70, 1.4)]), (560, [(30, 170, 2.2), (10, 60, .1)]), (640, [(36, 230, 1.0), (10, 80, .6)]), (760, [(30, 260, 2.6), (8, 90, 1.9)])]
    pts_all = []
    for (y, wv), (fill, rip) in zip(specs, cols):
        pts = profile(rng, y, 0, 20, waves=wv)
        pts_all.append(pts)
        # crête éclairée et ondulations
        crest = smooth(pts)
        rips = "".join(f'<path d="M{n(x)},{n(y_at(pts, x) + 14 + k * 11)} q22,-6 44,0 t44,0" stroke="{rip}" stroke-width="1.2" fill="none" opacity=".38"/>'
                       for x in [rng.uniform(-240, W + 200) for _ in range(18)] for k in range(3))
        out.append(f'<path d="{land(pts)}" fill="{fill}"/><path d="{crest}" stroke="{rip}" stroke-width="2" fill="none" opacity=".6"/>{rips}')
    return out, pts_all


def scene_desert(night=False):
    rng = random.Random(41)
    if not night:
        cols = [(mix(HENNA, LIME, .55), mix(BRICK, LIME, .6)), (mix(BRICK, HENNA, .35), mix(BRICK, LIME, .45)),
                (mix(BRICK, HENNA, .55), mix(BRICK, LIME, .3)), (mix(HENNA, INK, .15), mix(BRICK, HENNA, .3))]
    else:
        cols = [(mix(INK, BLUE, .35), mix(BLUE, LIME, .2)), (mix(INK, BLUE, .22), mix(BLUE, INK, .1)),
                (mix(INK, BLUE, .12), mix(INK, BLUE, .4)), (mix(INK, "#000000", .15), mix(INK, BLUE, .3))]
    layers, pts = dunes(rng, cols)
    tag = "night" if night else "dusk"
    crest = pts[2]
    if not night:
        cx0 = 520
        cam = [use("man-dusk", cx0 + 300, y_at(crest, cx0 + 300) + 4, .9)]
        for i in range(5):
            x = cx0 + 200 - i * 120
            cam.append(f'<g transform="translate({n(x)} {n(y_at(crest, x) + 4)}) scale(.9)"><g>{anim_translate("0 0;0 -2;0 0", "1.1s", f"{i * .2:.1f}s")}'
                       f'<use href="#camel-dusk"/></g></g>')
            if i:
                cam.append(f'<path d="M{n(x + 118)},{n(y_at(crest, x) - 86)} Q{n(x + 150)},{n(y_at(crest, x) - 60)} {n(x + 176)},{n(y_at(crest, x) - 74)}" stroke="{INK}" stroke-width="1.2" fill="none" opacity=".6"/>')
        ys = [y_at(crest, x) for x in range(cx0 - 300, cx0 + 380, 10)]
        ACTORS["caravan"] = dict(scene=3, x=0, y=0, box=(cx0 - 290, min(ys) - 115, 680, max(ys) - min(ys) + 130), scale=1, body="".join(cam))
        plants = "".join(f'<path d="M{x},{y} q-6,-18 -2,-30 M{x},{y} q4,-20 12,-26 M{x},{y} q-12,-10 -20,-14" stroke="{mix(PALM, HENNA, .3)}" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
                         for x, y in [(140, 836), (380, 860), (1120, 846), (1460, 852)])
        mid = ""
        near = layers[3] + plants
    else:
        # campement : tente bédouine, feu, dromadaires couchés
        x0 = 860
        y0 = y_at(crest, x0) + 6
        tent = (f'<g transform="translate({x0} {n(y0)})"><path d="M-110,0 L-80,-58 L0,-74 L84,-56 L120,0 Z" fill="{mix(INK, BRICK, .25)}"/>'
                f'<path d="M-80,-58 L0,-74 L84,-56" stroke="{mix(BRICK, INK, .3)}" stroke-width="3" fill="none"/>'
                + "".join(f'<path d="M{-100 + i * 22},-4 L{-74 + i * 18},-58" stroke="{mix(BRICK, INK, .45)}" stroke-width="2"/>' for i in range(9))
                + f'<path d="M-20,0 L0,-46 L20,0 Z" fill="{mix(BRICK, LIME, .2)}" opacity=".85"/></g>')
        fx, fy = x0 + 190, y_at(crest, x0 + 190) + 10
        fire = (f'<g transform="translate({n(fx)} {n(fy)})"><circle r="120" fill="url(#fire-g)" opacity=".55">'
                f'<animate attributeName="opacity" values=".45;.65;.5;.6;.45" dur="1.6s" repeatCount="indefinite"/></circle>'
                f'<path d="M-16,0 L16,-4 M-14,-4 L14,0" stroke="{mix(INK, BRICK, .5)}" stroke-width="4" stroke-linecap="round"/>'
                f'<path d="M-9,-2 C-12,-16 -2,-20 0,-34 C4,-22 12,-16 9,-2 Z" fill="{BRICK}"><animateTransform attributeName="transform" type="scale" values="1 1;1 1.15;1 .95;1 1" dur="0.9s" repeatCount="indefinite"/></path>'
                f'<path d="M-4,-2 C-6,-10 0,-14 1,-22 C3,-14 6,-10 4,-2 Z" fill="{mix(BRICK, LIME, .5)}"/></g>')
        resting = "".join(f'<g transform="translate({x} {n(y_at(crest, x) + 4)}) scale(.85)">'
                          f'<path d="M0,0 C4,-30 26,-46 52,-46 C74,-46 84,-34 90,-24 C96,-26 100,-34 106,-46 C110,-56 120,-58 126,-52 L122,-46 C116,-40 114,-26 108,-14 C104,-6 98,0 90,0 Z" fill="{mix(INK, BLUE, .12)}"/>'
                          f'<path d="M30,-44 C40,-56 60,-56 70,-44 Z" fill="{mix(HENNA, INK, .45)}"/></g>'
                          for x in (560, 680, 1240))
        mid = f'<g id="w-camp">{tent}{resting}{use("man-night", x0 + 150, y_at(crest, x0 + 150) + 4, .9)}{fire}</g>'
        near = layers[3]
    return (layer(.12, layers[0]) + layer(.25, layers[1]) + layer(.5, layers[2] + mid) + layer(1, near))


def svg(view, body, cls, extra="", par="xMidYMax slice"):
    return (f'<svg class="{cls}" xmlns="http://www.w3.org/2000/svg" viewBox="{view}" preserveAspectRatio="{par}" '
            f'focusable="false" aria-hidden="true"{extra}>{body}</svg>')


def main():
    import re
    scenes = [scene_north(), scene_sahel(), scene_south(), scene_desert(False), scene_desert(True)]
    sk = sky()
    full = f"0 0 {W} {H}"
    out = [svg("0 0 1 1", defs(), "w-defs", ' width="0" height="0"')]
    out += [f'<div class="w-sky" data-sky="{i}"></div>' for i in range(5)]
    out.append(svg(full, sk["stars"], "w-full w-stars", par="xMidYMid slice"))
    out.append(svg("-160 -160 320 320", sk["sun"], "w-orb w-sun", par="xMidYMid meet"))
    out.append(svg("-100 -100 200 200", sk["moon"], "w-orb w-moon", par="xMidYMid meet"))
    out.append(svg(full, sk["clouds"], "w-full w-clouds", par="xMidYMid slice"))
    for i, layers in enumerate(scenes):
        groups = {}
        for depth, body in layers:  # 3 calques par scène au plus
            key = .2 if depth < .4 else (.55 if depth < .9 else 1)
            groups.setdefault(key, []).append(body)
        inner = "".join(svg(full, "".join(b), "w-full w-layer", f' data-depth="{d}"') for d, b in sorted(groups.items()))
        for name, a in ACTORS.items():
            if a["scene"] == i:
                bx, by, bw, bh = a["box"]
                body = f'<g transform="translate({a["x"]} {a["y"]}) scale({a["scale"]})">{a["body"]}</g>' if name == "truck" else a["body"]
                if name == "truck":
                    bx, by, bw, bh = a["x"] + bx * a["scale"], a["y"] + by * a["scale"], bw * a["scale"], bh * a["scale"]
                inner += svg(f"{n(bx)} {n(by)} {n(bw)} {n(bh)}", body, f"w-actor w-{name}",
                             f' data-box="{n(bx)} {n(by)} {n(bw)} {n(bh)}"', par="xMidYMid meet")
        out.append(f'<div class="w-scene" data-scene="{i}">{inner}</div>')
    html = "\n".join(out) + "\n"
    html = re.sub(r"<animate(Transform)?\b[^>]*/>", "", html)  # décor statique : le mouvement vient du défilement
    OUT.write_text(html, encoding="utf-8")
    print(f"{OUT} — {len(html) / 1024:.0f} Kio, {html.count('<svg')} calques SVG")


if __name__ == "__main__":
    main()
