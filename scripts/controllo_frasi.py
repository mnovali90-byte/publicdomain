"""Controllo delle frasi sui paesi (21/11/2026, dopo il caso Milne): cerca nelle pagine pubblicate le affermazioni imprecise.
1. «libero/libera in Europa» o «free in Europe» seguito da una data: in Spagna valgono 80 anni per chi è morto prima del 1987,
   in Italia gli autori di paesi alleati vanno verificati, quindi «Europa» non è mai preciso.
2. (tolto il 22/11/2026: per i paesi alleati l'Italia ha di nuovo la data, con una nota)
3. (21/11/2026, regole in un posto solo) Ogni scheda autore, italiana e inglese: la tabella «paese per paese» deve dire
   esattamente quello che calcola scripts/regole.py (data o «da verificare»), paese per paese.
Esce con errore se trova qualcosa."""
import glob, re, sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
errori = []
EUROPA = re.compile(r"(liber[oaie]|free)(?:\s|<[^>]+>)+in(?:\s|<[^>]+>)+europ[ae](?:\s|<[^>]+>)+(dal|from|il|on)\b", re.I)
for f in glob.glob(str(RADICE / "**" / "*.html"), recursive=True):
    if "/node_modules/" in f or "/docs/" in f:
        continue
    t = Path(f).read_text(encoding="utf-8", errors="ignore")
    for m in EUROPA.finditer(t):
        errori.append(f"{Path(f).relative_to(RADICE)}: «{t[max(0, m.start() - 30):m.end() + 30].strip()}»")
# 3. tabella paese per paese di ogni scheda contro scripts/regole.py
import json  # noqa: E402
from datetime import date  # noqa: E402
sys.path.insert(0, str(RADICE / "scripts"))
import regole as R  # noqa: E402
OGGI = date.today().year
try:
    MPF = set(json.loads((RADICE / "data" / "registro" / "mpf.json").read_text(encoding="utf-8")).get("autori", {}))
except Exception:
    MPF = set()
NOMI = {"Italia": "it", "Francia": "fr", "Germania": "de", "Regno Unito": "uk", "Spagna": "es",
        "Italy": "it", "France": "fr", "Germany": "de", "United Kingdom": "uk", "Spain": "es"}
schede = {}
for f in glob.glob(str(RADICE / "data" / "[0-9]*.json")) + glob.glob(str(RADICE / "data" / "es-[0-9]*.json")):
    for a in json.load(open(f, encoding="utf-8")).get("autori", []):
        for k, d in (("pagina", "autore"), ("pagina_en", "en/author")):
            if a.get(k):
                schede[f"{d}/{a[k]}"] = a
n_schede = n_righe = 0
for chiave, a in schede.items():
    f = RADICE / chiave / "index.html"
    if not f.exists():
        continue
    t = f.read_text(encoding="utf-8")
    m_ul = re.search(r'<ul class="ps">(.*?)</ul>', t, re.S)
    if not m_ul:
        continue
    n_schede += 1
    D = int(re.match(r"-?\d+", str(a["morte"])).group(0))
    en = chiave.startswith("en/")
    for nome, val in re.findall(r'<span class="c">([^<]+)<small>.*?</small></span><span class="v">([^<]*)</span>', m_ul.group(1)):
        p = NOMI.get(nome.strip())
        if not p:
            continue
        n_righe += 1
        y = R.anno_libero(D, p, a["wikidata"] in MPF)
        atteso = ((f"free since {y}" if en else f"libero dal {y}") if y <= OGGI else (f"1 Jan {y}" if en else f"1° gen {y}"))
        if val.strip() != atteso:
            errori.append(f"{chiave}: {nome} «{val}», le regole dicono «{atteso}»")
print(f"Schede controllate contro scripts/regole.py: {n_schede}, righe paese: {n_righe}")

for e in errori[:50]:
    print(e)
print(f"Frasi imprecise trovate: {len(errori)}")
sys.exit(1 if errori else 0)
