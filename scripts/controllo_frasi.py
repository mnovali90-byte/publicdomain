"""Controllo delle frasi sui paesi (21/11/2026, dopo il caso Milne): cerca nelle pagine pubblicate le affermazioni imprecise.
1. «libero/libera in Europa» o «free in Europe» seguito da una data: in Spagna valgono 80 anni per chi è morto prima del 1987,
   in Italia gli autori di paesi alleati vanno verificati, quindi «Europa» non è mai preciso.
2. Schede autore di paesi alleati che mostrano una data per l'Italia invece di «da verificare».
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
    if "/autore/" in f or "/author/" in f:
        if "paese alleato nella Seconda guerra" in t or "Allied country in the Second World War" in t:
            m = re.search(r'<span class="c">(Italia|Italy)<small>[^<]*</small></span><span class="v">([^<]*)</span>', t)
            if m and m.group(2) not in ("da verificare", "to be checked") and not m.group(2).startswith(("libero dal", "free since")):
                errori.append(f"{Path(f).relative_to(RADICE)}: Italia «{m.group(2)}» per un autore di paese alleato")
for e in errori[:50]:
    print(e)
print(f"Frasi imprecise trovate: {len(errori)}")
sys.exit(1 if errori else 0)
