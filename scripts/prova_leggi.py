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

def cerca_pdf(nome, url, lingua, chiavi, largo=2500, massimo=3, timeout=400):
    print("=" * 60, "\n", nome, url, flush=True)
    d, fin = scarica(url, True, timeout=timeout, tentativi=2)
    print(" byte:", len(d), flush=True)
    if d[:4] != b"%PDF": print(" non è un PDF:", d[:80]); return ""
    t, modo = pdf_testo(d, lingua); print(" modo:", modo, "| caratteri:", len(t), flush=True)
    estratti(t, chiavi, largo=largo, massimo=massimo)
    return t

# ITALIA: Allegato XV dal testo francese CVCE
d, fin = scarica("https://www.cvce.eu/content/publication/1999/1/1/0eaf4219-d6d9-4c35-935a-6f55327448e7/publishable_fr.pdf", True, timeout=300, tentativi=2)
t, modo = pdf_testo(d, "fra"); print("FR byte", len(d), "caratteri", len(t), flush=True)
pos = [m.start() for m in re.finditer(r"Annexe XV", t)]
ultima_toc = pos[3] if len(pos) > 3 else 0
print("posizioni Annexe XV:", pos)
for k in re.finditer(r"propri[eé]t[eé] industrielle, litt[eé]raire et artistique|Propri[eé]t[eé] industrielle, litt[eé]raire et artistique", t):
    print(" titolo a", k.start())
inizio = max(x for x in pos if x > 200000) if [x for x in pos if x > 200000] else 0
for x in [y for y in pos if y > 200000]:
    print("=" * 40, "da", x, flush=True); print(t[x:x+4500], flush=True)
# SPAGNA: legge 1879 nel BOE (BOE-A-1879-40001)
for nome, url in [("scheda", "https://www.boe.es/buscar/doc.php?id=BOE-A-1879-40001"), ("xml", "https://www.boe.es/diario_boe/xml.php?id=BOE-A-1879-40001")]:
    print("=" * 60, "\nSPAGNA 1879", nome, url, flush=True)
    h, fin = scarica(url, tentativi=2); tt = testo(h); print(" caratteri:", len(tt))
    print(" inizio:", tt[:400])
    estratti(tt, [r"ochenta", r"Art\S*\.? ?6"], largo=1400, massimo=4)
    print(" link pdf:", [l for l in sorted(set(re.findall(r'href="([^"]+)"', h))) if "pdf" in l.lower()][:5])
