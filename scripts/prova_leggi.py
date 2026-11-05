import re, sys, html, io, subprocess, time, urllib.request, os
UA = {"User-Agent": "Mozilla/5.0 (PublicDomainTool research; https://github.com/mnovali90-byte/publicdomain)"}
def scarica(url, binario=False, timeout=300, tentativi=3):
    ult = ""
    for i in range(tentativi):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                d = r.read(); return (d if binario else d.decode("utf-8", "replace")), r.geturl()
        except Exception as e:
            ult = f"ERRORE {e}"; print("  ", url[:90], ult, flush=True); time.sleep(8)
    return (b"" if binario else ""), ult
def testo(h):
    h = re.sub(r"(?is)<(script|style).*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))
def estratti(t, chiavi, largo=1500, massimo=4, prima=300):
    n = 0
    for k in chiavi:
        for m in re.finditer(k, t):
            print(f"  [{k}] ...{t[max(0, m.start()-prima):m.start()+largo]}...\n", flush=True); n += 1
            if n >= massimo: return
def pdf_testo(d, lingua):
    from pypdf import PdfReader
    r = PdfReader(io.BytesIO(d)); pag = [re.sub(r"\s+", " ", pg.extract_text() or "") for pg in r.pages]
    if sum(len(x) for x in pag) > 300 * max(1, len(pag)) / 3: return " ".join(pag), "testo"
    open("/tmp/x.pdf", "wb").write(d)
    subprocess.run(["pdftoppm", "-r", "200", "-png", "/tmp/x.pdf", "/tmp/pg"], check=False)
    out = []
    for f in sorted(x for x in os.listdir("/tmp") if x.startswith("pg") and x.endswith(".png")):
        out.append(subprocess.run(["tesseract", "/tmp/" + f, "-", "-l", lingua], capture_output=True, text=True).stdout)
    return re.sub(r"\s+", " ", " ".join(out)), "OCR"

print("=" * 60, "\nITALIA: Allegato XV su Normattiva (DLCPS 1430/1947)")
base = "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo.capo.provvisorio.stato:1947-11-28;1430"
for suf in ["~allXV", "~all15", "~allegatoXV", "!vig=~allXV"]:
    h, fin = scarica(base + suf, tentativi=1); t = testo(h)
    print(" ", suf, "->", len(t), "caratteri;", "letter" in t.lower(), "propriet" in t.lower())
    if re.search(r"propriet. letteraria|diritto d.autore|Annex XV|ALLEGATO XV", t, re.I) and len(t) > 3000:
        estratti(t, [r"[Pp]ropriet. letteraria", r"diritti? d.autore"], largo=2500); break

print("=" * 60, "\nITALIA: trattato PDF UK (timeout lungo)")
d, fin = scarica("https://treaties.fcdo.gov.uk/data/Library2/pdf/1948-TS0050.pdf", True, timeout=400)
print(" byte:", len(d))
if d:
    t, modo = pdf_testo(d, "eng"); print(" modo:", modo, "| caratteri:", len(t))
    pos = [m.start() for m in re.finditer(r"ANNEX XV", t)]; print(" ANNEX XV a:", pos[:8])
    estratti(t, [r"[Ll]iterary and artistic (property|works)", r"[Cc]opyright"], largo=2500, massimo=3)

print("=" * 60, "\nSPAGNA: legge 1879, scheda BOE e PDF")
h, fin = scarica("https://www.boe.es/eli/es/l/1879/01/10/(1)", tentativi=1)
print(" pagina:", len(testo(h)), "caratteri;", testo(h)[:600])
links = sorted(set(re.findall(r'href="([^"]+)"', h)))
print(" link:", [l for l in links if "pdf" in l.lower() or "gazeta" in l.lower() or "BOE-A-1879" in l][:10])
for l in [l for l in links if "pdf" in l.lower() or "BOE-A-1879" in l][:2]:
    u = l if l.startswith("http") else "https://www.boe.es" + l
    d, fin = scarica(u, True)
    print(" scarico", u, len(d))
    if d[:4] == b"%PDF":
        t, modo = pdf_testo(d, "spa"); print(" modo:", modo, "| caratteri:", len(t))
        estratti(t, [r"ochenta", r"Art\S* ?6"], largo=1200, massimo=4)
