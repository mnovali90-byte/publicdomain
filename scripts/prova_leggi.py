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

# ITALIA: trattato, testo francese CVCE (86 pagine): le annexes ci sono?
t = cerca_pdf("TRATTATO FR (CVCE)", "https://www.cvce.eu/content/publication/1999/1/1/0eaf4219-d6d9-4c35-935a-6f55327448e7/publishable_fr.pdf", "fra",
              [r"Annexe XV", r"litt[eé]raire et artistique", r"droits d.auteur", r"[Pp]ropri[eé]t[eé] industrielle, litt"], largo=3500, massimo=4, timeout=300)
print(" 'Annexe XV' a:", [m.start() for m in re.finditer(r"Annexe XV", t)][:10] if t else None, "| tot", len(t))
# ITALIA: Nazioni Unite, UNTS vol. 49
cerca_pdf("TRATTATO UNTS", "https://treaties.un.org/doc/Publication/UNTS/Volume%2049/volume-49-I-747-English.pdf", "eng",
          [r"ANNEX XV", r"literary and artistic property", r"[Cc]opyright"], largo=3500, massimo=3)
# SPAGNA: regolamento 1880 (BOE, testo consolidato) e Gazeta digitalizzata
print("=" * 60, "\nSPAGNA regolamento 1880 BOE", flush=True)
h, fin = scarica("https://www.boe.es/eli/es/rd/1880/09/03/(1)", tentativi=1); tt = testo(h); print(" caratteri:", len(tt))
estratti(tt, [r"ochenta", r"Ley de 10 de enero de 1879"], largo=700, massimo=4)
print("=" * 60, "\nSPAGNA Prensa Histórica (Ministerio de Cultura)", flush=True)
h, fin = scarica("https://prensahistorica.mcu.es/va/catalogo_imagenes/grupo.do?path=43581", tentativi=1)
print(" finale:", fin, "| caratteri:", len(testo(h)), "|", testo(h)[:500])
print(" link pdf:", [l for l in sorted(set(re.findall(r'href="([^"]+)"', h))) if "pdf" in l.lower() or "descarga" in l.lower()][:10])
