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
# 1) trattato di pace, PDF ufficiale del Regno Unito
print("=" * 60, "\nTRATTATO (UK Treaty Series 1948 n.50)")
d, fin = scarica("https://treaties.fcdo.gov.uk/data/Library2/pdf/1948-TS0050.pdf", True)
print(" scaricati", len(d), "byte", fin)
open("/tmp/trattato.pdf", "wb").write(d)
try:
    t = subprocess.run(["pdftotext", "-layout", "/tmp/trattato.pdf", "-"], capture_output=True, text=True, timeout=120).stdout
except Exception as e:
    t = ""; print(" pdftotext non disponibile", e)
t = re.sub(r"\s+", " ", t); print(" caratteri di testo:", len(t))
i = t.find("ANNEX XV")
print(" posizioni 'ANNEX XV':", [m.start() for m in re.finditer("ANNEX XV", t)][:6])
estratti(t, [r"Literary and artistic property|literary and artistic property", r"copyright"], largo=1800, massimo=4)
# 2) legge spagnola 1879
for nome, url, chiavi in [
  ("SPAGNA 1879 BOE ELI", "https://www.boe.es/eli/es/l/1879/01/10/(1)", [r"ochenta", r"Art[ií]culo 6"]),
  ("SPAGNA 1879 Wikisource (trascrizione, non ufficiale)", "https://es.wikisource.org/wiki/Ley_de_10_de_enero_de_1879,_de_la_propiedad_intelectual_(Espa%C3%B1a)", [r"ochenta", r"Art[ií]culo 6\.?[ºo]?"]),
]:
    print("=" * 60, "\n", nome, url)
    h, fin = scarica(url); tt = testo(h); print(" finale:", fin, "| caratteri:", len(tt))
    estratti(tt, chiavi, largo=700)
