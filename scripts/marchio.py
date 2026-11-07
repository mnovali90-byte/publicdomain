"""Il logo PDR (sigla con il taglio sulla R, tre parole sotto le tre lettere), come codice da inserire nelle pagine."""
import pathlib, re

_RADICE = pathlib.Path(__file__).resolve().parent.parent
_svg = (_RADICE / "assets" / "logo-pdr.svg").read_text(encoding="utf-8")
_W = 215.67
_LETTERE = [("PUBLIC", 0, 61.42), ("DOMAIN", 74.58, 137.65), ("RADAR", 152.82, 215.67)]


def marchio_html(larghezza=110):
    svg = re.sub(r'<svg [^>]*>', '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 215.67 120" aria-hidden="true" focusable="false">', _svg, count=1).strip()
    svg = svg.replace('id="t"', 'id="pdrt"').replace('url(#t)', 'url(#pdrt)')
    sub = "".join(f'<b style="left:{a / _W * 100:.3f}%;width:{(b - a) / _W * 100:.3f}%">' + "".join(f"<i>{c}</i>" for c in w) + "</b>" for w, a, b in _LETTERE)
    return f'<span class="pdr" style="--w:{larghezza}px">{svg}<span class="sub">{sub}</span></span>'


CSS_MARCHIO = """
.pdr{display:inline-flex;flex-direction:column;align-items:stretch;width:var(--w,110px);color:currentColor;text-transform:none;letter-spacing:0;line-height:1;vertical-align:middle}
.pdr svg{display:block;width:100%;height:auto;color:#F7F7F4}
.pdr .sub{position:relative;display:block;height:calc(var(--w)*.06);margin-top:calc(var(--w)*.05);font:500 calc(var(--w)*.052)/1 'DM Mono',ui-monospace,Menlo,monospace;text-transform:uppercase;color:#A9A9B6}
.pdr .sub b{position:absolute;top:0;display:flex;justify-content:space-between;font-weight:500}
.pdr .sub i{font-style:normal}.pdr .sub b i:first-child{margin-left:-.06em}.pdr .sub b i:last-child{margin-right:-.06em}
"""
