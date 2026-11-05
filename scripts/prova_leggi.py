import re, sys, html, subprocess, urllib.request
UA = {"User-Agent": "Mozilla/5.0 (PublicDomainTool research; https://github.com/mnovali90-byte/publicdomain)"}
def scarica(url, binario=False):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
            d = r.read(); return (d if binario else d.decode("utf-8", "replace")), r.geturl()
    except Exception as e:
        return (b"" if binario else ""), f"ERRORE {e}"
def testo(h):
    h = re.sub(r"(?is)<(script|style).*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))
def estratti(t, chiavi, largo=900, massimo=5):
    n = 0
    for k in chiavi:
        for m in re.finditer(k, t):
            print(f"  [{k}] ...{t[max(0, m.start()-200):m.start()+largo]}...\n"); n += 1
            if n >= massimo: return
# 1) trattato di pace: più fonti, con nuovi tentativi
import time
PDFS = ["https://treaties.fcdo.gov.uk/data/Library2/pdf/1948-TS0050.pdf",
        "https://www.cvce.eu/content/publication/1999/1/1/0eaf4219-d6d9-4c35-935a-6f55327448e7/publishable_en.pdf",
        "https://www.cvce.eu/content/publication/1999/1/1/0eaf4219-d6d9-4c35-935a-6f55327448e7/publishable_fr.pdf"]
from pypdf import PdfReader
import io
for url in PDFS:
    print("=" * 60, "\nTRATTATO", url)
    d = b""
    for tentativo in range(3):
        d, fin = scarica(url, True)
        if d: break
        print(" ", fin); time.sleep(10)
    print(" scaricati", len(d), "byte")
    if not d: continue
    try:
        r = PdfReader(io.BytesIO(d)); pagine = [(re.sub(r"\s+", " ", (pg.extract_text() or ""))) for pg in r.pages]
    except Exception as e:
        print(" PDF illeggibile", e); continue
    print(" pagine:", len(pagine), "| con testo:", sum(1 for x in pagine if len(x) > 200))
    t = " ".join(pagine)
    trovati = [m.start() for m in re.finditer(r"literary and artistic property|Literary and artistic|propri[eé]t[eé] litt[eé]raire", t)]
    print(" occorrenze:", len(trovati))
    for pos in trovati[:3]:
        print("  ...", t[max(0, pos-300):pos+2200], "...\n")
    if trovati: break
# 2) legge spagnola 1879
for nome, url, chiavi in [
  ("SPAGNA 1879 BOE ELI", "https://www.boe.es/eli/es/l/1879/01/10/(1)", [r"ochenta", r"Art[ií]culo 6"]),
  ("SPAGNA 1879 Wikisource (trascrizione, non ufficiale)", "https://es.wikisource.org/wiki/Ley_de_10_de_enero_de_1879,_de_la_propiedad_intelectual_(Espa%C3%B1a)", [r"ochenta", r"Art[ií]culo 6\.?[ºo]?"]),
]:
    print("=" * 60, "\n", nome, url)
    h, fin = scarica(url); tt = testo(h); print(" finale:", fin, "| caratteri:", len(tt))
    estratti(tt, chiavi, largo=700)
