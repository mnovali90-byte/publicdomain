"""Il logo RDR (sigla con il taglio-lancetta sull'ultima R, «Public Domain Radar» sotto per tutta la larghezza), come codice da inserire nelle pagine.
Fino al 21/11/2026 era PDR: cambiato perché PDR è anche la sigla di The Public Domain Review."""
import pathlib, re

_RADICE = pathlib.Path(__file__).resolve().parent.parent
_svg = (_RADICE / "assets" / "logo-rdr.svg").read_text(encoding="utf-8")
_VB = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', _svg)
_W, _H = float(_VB.group(1)), float(_VB.group(2))
SOTTO = "PUBLIC DOMAIN RADAR"


def marchio_html(larghezza=110):
    svg = re.sub(r'<svg [^>]*>', f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_W:g} {_H:g}" aria-hidden="true" focusable="false">', _svg, count=1).strip()
    svg = svg.replace('id="t"', 'id="pdrt"').replace('url(#t)', 'url(#pdrt)')
    sub = '<b style="left:0;width:100%">' + "".join(f"<i>{'&nbsp;' if c == ' ' else c}</i>" for c in SOTTO) + "</b>"
    return f'<span class="pdr" style="--w:{larghezza}px">{svg}<span class="sub">{sub}</span></span>'


CSS_MARCHIO = """
.pdr{display:inline-flex;flex-direction:column;align-items:stretch;width:var(--w,110px);color:currentColor;text-transform:none;letter-spacing:0;line-height:1;vertical-align:middle}
.pdr svg{display:block;width:100%;height:auto;color:#F7F7F4}
.pdr .sub{position:relative;display:block;height:calc(var(--w)*.06);margin-top:calc(var(--w)*.05);font:500 calc(var(--w)*.052)/1 'DM Mono',ui-monospace,Menlo,monospace;text-transform:uppercase;color:#A9A9B6}
.pdr .sub b{position:absolute;top:0;display:flex;justify-content:space-between;font-weight:500}
.pdr .sub i{font-style:normal}.pdr .sub b i:first-child{margin-left:-.06em}.pdr .sub b i:last-child{margin-right:-.06em}
"""
