import re, sys, html, urllib.request
UA = {"User-Agent": "Mozilla/5.0 (PublicDomainTool research; https://github.com/mnovali90-byte/publicdomain)"}
def scarica(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            return r.read().decode("utf-8", "replace"), r.geturl()
    except Exception as e:
        return "", f"ERRORE {e}"
def testo(h):
    h = re.sub(r"(?is)<(script|style).*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))
def estratti(t, chiavi, largo=500, massimo=6):
    n = 0
    for k in chiavi:
        for m in re.finditer(k, t):
            print(f"  [{k}] ...{t[max(0, m.start()-120):m.start()+largo]}...\n")
            n += 1
            if n >= massimo: return
FONTI = [
 ("ITALIA legge 633/1941 art. 25", "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:legge:1941-04-22;633~art25", [r"Art\. ?25", r"settantesimo anno|cinquantesimo anno"]),
 ("ITALIA legge 633/1941 art. 32-ter", "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:legge:1941-04-22;633~art32ter", [r"1 gennaio|primo gennaio"]),
 ("ITALIA trattato di pace 1947 (DLCPS 1430/1947)", "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo.capo.provvisorio.stato:1947-11-28;1430", [r"Allegato XV|propriet. letteraria|diritto d.autore", r"Trattato"]),
 ("ITALIA DLgsLgt 440/1945 testo completo", "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo.luogotenenziale:1945-07-20;440", [r"Art\. ?[2-5]\.?", r"entrata in vigore"]),
 ("SPAGNA legge 10 gennaio 1879 (BOE/Gazeta)", "https://www.boe.es/datos/pdfs/BOE//1879/012/A00097-00099.pdf", [r"ochenta", r"Art\. ?6"]),
]
for nome, url, chiavi in FONTI:
    print("=" * 70, "\n", nome, url)
    h, fin = scarica(url)
    t = testo(h)
    print(" finale:", fin, "| caratteri:", len(t))
    estratti(t, chiavi)
