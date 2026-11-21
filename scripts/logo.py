"""Genera il logo RDR (21/11/2026, al posto di PDR, che è anche la sigla di The Public Domain Review).

Lettere R D R di Big Shoulders Display 900 come disegno fisso, prese dal file del carattere che il sito usa già
(assets/fonts/big-shoulders-display-900-latin.woff2), con il taglio sull'ultima R:
il buco della R è lo schermo del radar e il taglio è la lancetta che parte esattamente dal centro del buco
(centro misurato sul disegno della lettera, non a occhio), inclinata di 40 gradi, sottile.

Scrive assets/logo-rdr.svg (testata delle pagine) e assets/favicon.svg (icona del sito).
Mockup approvato da Marco il 21/11/2026 («solo taglio bianco», senza punto e senza lancetta piena nel buco).
"""
import math, pathlib
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen

RADICE = pathlib.Path(__file__).resolve().parent.parent
SIGLA = "RDR"
ALTEZZA = 150          # corpo del carattere in unità del disegno (come il logo di prima)
SP = 4                 # spazio in più tra le lettere
ANGOLO = -40           # inclinazione della lancetta (gradi, verso l'alto a destra)
SPESSORE = 3.7         # spessore del taglio (come nel mockup approvato)

f = TTFont(RADICE / "assets" / "fonts" / "big-shoulders-display-900-latin.woff2")
if "fvar" in f:                         # il file è un carattere variabile: si fissa il peso 900
    f = instantiateVariableFont(f, {"wght": 900})
gs = f.getGlyphSet(); cmap = f.getBestCmap(); upem = f["head"].unitsPerEm
k = ALTEZZA / upem

ox = 0; info = []
for ch in SIGLA:
    g = gs[cmap[ord(ch)]]
    bp = BoundsPen(gs); g.draw(bp); xmin, ymin, xmax, ymax = bp.bounds
    info.append((ch, g, ox, xmin * k, xmax * k, ymax * k))
    ox += g.width * k + SP
shift = -info[0][3]                     # bordo sinistro della prima lettera -> x=0
cap = max(i[5] for i in info)
paths = []
for ch, g, o, a, b, top in info:
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    g.draw(TransformPen(pen, (k, 0, 0, -k, o + shift, cap)))
    paths.append(pen.getCommands())
W = info[-1][2] + shift + info[-1][4]


def contorni(g):
    """Contorni della lettera come liste di punti (coordinate del carattere)."""
    rp = DecomposingRecordingPen(gs); g.draw(rp)
    out, cur = [], []
    for op, args in rp.value:
        if op == "moveTo":
            cur = [args[0]]
        elif op in ("lineTo", "qCurveTo", "curveTo"):
            cur.extend(args)
        elif op in ("closePath", "endPath"):
            out.append(cur); cur = []
    return out


# centro del buco dell'ultima R = centro del contorno interno più piccolo
ultima = info[-1]
interni = sorted(contorni(ultima[1]), key=lambda c: (max(p[0] for p in c) - min(p[0] for p in c)) * (max(p[1] for p in c) - min(p[1] for p in c)))
buco = interni[0]
bx = (min(p[0] for p in buco) + max(p[0] for p in buco)) / 2
by = (min(p[1] for p in buco) + max(p[1] for p in buco)) / 2
cx = bx * k + ultima[2] + shift
cy = cap - by * k
a = math.radians(ANGOLO)
x2, y2 = cx + 300 * math.cos(a), cy + 300 * math.sin(a)

taglio = (f'<line x1="{cx:.2f}" y1="{cy:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#000" stroke-width="{SPESSORE}"/>')
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.2f} {cap:.2f}" role="img" aria-label="RDR">
<defs><mask id="t" maskUnits="userSpaceOnUse" x="-5" y="-5" width="{W+10:.2f}" height="{cap+10:.2f}"><rect x="-5" y="-5" width="{W+10:.2f}" height="{cap+10:.2f}" fill="#fff"/>{taglio}</mask></defs>
<path fill="currentColor" mask="url(#t)" d="{' '.join(paths)}"/></svg>
'''
(RADICE / "assets" / "logo-rdr.svg").write_text(svg, encoding="utf-8")

# icona del sito: quadrato scuro con gli angoli arrotondati, sigla chiara al centro
s = 52 / W
tx, ty = (64 - W * s) / 2, (64 - cap * s) / 2
fav = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#0C0C10"/>'
       f'<defs><mask id="f" maskUnits="userSpaceOnUse" x="-5" y="-5" width="{W+10:.2f}" height="{cap+10:.2f}"><rect x="-5" y="-5" width="{W+10:.2f}" height="{cap+10:.2f}" fill="#fff"/>{taglio}</mask></defs>'
       f'<g transform="translate({tx:.2f} {ty:.2f}) scale({s:.4f})"><path fill="#F7F7F4" mask="url(#f)" d="{" ".join(paths)}"/></g></svg>\n')
(RADICE / "assets" / "favicon.svg").write_text(fav, encoding="utf-8")
print("OK", f"larghezza {W:.2f}", f"altezza {cap:.2f}", f"centro del buco {cx:.2f},{cy:.2f}")
