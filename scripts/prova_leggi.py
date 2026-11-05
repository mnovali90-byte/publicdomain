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
 ("ITALIA legge 633/1941", "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:legge:1941-04-22;633!vig=", [r"Art\. ?25\b", r"cinquantesimo|settantesimo anno"]),
 ("ITALIA DLgsLgt 440/1945", "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo.luogotenenziale:1945-07-20;440", [r"prorogat", r"sei anni"]),
 ("ITALIA DLgsLgt 1948 n.1 (proroga bellica)", "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo.presidente.repubblica:1947-12-20;1", [r"prorog|proroga"]),
 ("SPAGNA TRLPI (BOE-A-1996-8930)", "https://www.boe.es/buscar/act.php?id=BOE-A-1996-8930", [r"Disposici[oó]n transitoria cuarta", r"ochenta a[ñn]os", r"7 de diciembre de 1987"]),
 ("SPAGNA TRLPI XML", "https://www.boe.es/diario_boe/xml.php?id=BOE-A-1996-8930", [r"transitoria cuarta", r"ochenta a[ñn]os"]),
]
for nome, url, chiavi in FONTI:
    print("=" * 70, "\n", nome, url)
    h, fin = scarica(url)
    t = testo(h)
    print(" finale:", fin, "| caratteri:", len(t))
    estratti(t, chiavi)
