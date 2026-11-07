"""Genera assets/logo-pdr.svg: lettere P D R di Big Shoulders Display (900) come disegno fisso, con il taglio sulla R.
Il bordo sinistro della P è a x=0, così si allinea alla scritta sotto."""
import math, sys, urllib.request, pathlib
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

URLS = ["https://raw.githubusercontent.com/google/fonts/main/ofl/bigshouldersdisplay/BigShouldersDisplay%5Bwght%5D.ttf"]
dati = None
for u in URLS:
    try:
        dati = urllib.request.urlopen(u, timeout=60).read(); break
    except Exception as e:
        print("errore", u, e, file=sys.stderr)
pathlib.Path("/tmp/f.ttf").write_bytes(dati)
f = instantiateVariableFont(TTFont("/tmp/f.ttf"), {"wght": 900})
gs = f.getGlyphSet(); cmap = f.getBestCmap(); upem = f["head"].unitsPerEm
k = 150 / upem
SP = 4
ox = 0; info = []
for ch in "PDR":
    g = gs[cmap[ord(ch)]]
    bp = BoundsPen(gs); g.draw(bp); xmin, ymin, xmax, ymax = bp.bounds
    info.append((ch, g, ox, xmin * k, xmax * k, ymax * k))
    ox += g.width * k + SP
shift = -info[0][3]            # bordo sinistro della P -> x=0
cap = max(i[5] for i in info)
paths = []
for ch, g, o, a, b, top in info:
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    g.draw(TransformPen(pen, (k, 0, 0, -k, o + shift, cap)))
    paths.append(pen.getCommands())
W = info[-1][2] + shift + info[-1][4]
R = info[-1]; rx0, rx1 = R[2] + shift + R[3], R[2] + shift + R[4]
cx = rx0 + 0.64 * (rx1 - rx0); cy = cap * 0.505
a = math.radians(-38); x2 = cx + 300 * math.cos(a); y2 = cy + 300 * math.sin(a)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.2f} {cap:.2f}" role="img" aria-label="PDR">
<defs><mask id="t" maskUnits="userSpaceOnUse" x="-5" y="-5" width="{W+10:.2f}" height="{cap+10:.2f}"><rect x="-5" y="-5" width="{W+10:.2f}" height="{cap+10:.2f}" fill="#fff"/><line x1="{cx:.2f}" y1="{cy:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#000" stroke-width="6"/></mask></defs>
<path fill="currentColor" mask="url(#t)" d="{' '.join(paths)}"/></svg>
'''
pathlib.Path("assets").mkdir(exist_ok=True)
pathlib.Path("assets/logo-pdr.svg").write_text(svg)
print("OK", W, cap, cx, cy)
