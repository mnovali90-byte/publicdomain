"""Controllo delle pagine VERE, aperte come in un telefono (21/11/2026): le parti che il browser costruisce da solo (radar,
Già pubblici) devono dire quello che calcola scripts/regole.py. Serve un server locale sulla cartella del sito:
    python3 -m http.server 8765      (poi)      python3 scripts/controllo_pagine.py [http://localhost:8765]
Prende un campione per ogni caso: autore di paese alleato (con la nota sul Trattato), autore di cittadinanza non nota, autore normale, autore con gli
80 anni spagnoli. Esce con errore se una data o un «da verificare» non torna."""
import asyncio, glob, json, re, sys
from datetime import date
from pathlib import Path

from playwright.async_api import async_playwright

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE / "scripts"))
import regole as R  # noqa: E402

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8765"
OGGI = date.today().year
PAESI = {"it": "Italia", "fr": "Francia", "de": "Germania", "uk": "Regno Unito", "es": "Spagna"}

autori = {}
for f in sorted(glob.glob(str(RADICE / "data" / "[0-9]*.json"))):
    for a in json.load(open(f, encoding="utf-8")).get("autori", []):
        if a.get("letterario") and re.match(r"\d{4}", str(a.get("morte") or "")):
            autori.setdefault(a["wikidata"], a)
morte = lambda a: int(str(a["morte"])[:4])
casi = {
    "paese alleato": [a for a in autori.values() if R.nota_trattato(a.get("paesi"), morte(a), OGGI)][:4],
    "cittadinanza non nota": [a for a in autori.values() if not a.get("paesi")][:4],
    "normale": [a for a in autori.values() if a.get("paesi") and not R.nota_trattato(a.get("paesi"), morte(a), OGGI)][:4],
}
casi["Milne e Brecht"] = [autori[q] for q in ("Q207036", "Q38757") if q in autori]


async def main():
    errori, n = [], 0
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome")
        pg = await b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        errjs = []
        pg.on("pageerror", lambda e: errjs.append(str(e)))
        # radar: scheda dell'autore, Italia scelta
        for tipo, lista in casi.items():
            for a in lista:
                await pg.goto(f"{BASE}/radar/?c=1#/autore/{a['wikidata']}")
                await pg.wait_for_timeout(2500)
                righe = await pg.evaluate("""() => [...document.querySelectorAll('dialog[open] ul.ps li')].map(li =>
                    [li.querySelector('.c') ? li.querySelector('.c').firstChild.textContent.trim() : '', (li.querySelector('.v') || {}).textContent || ''])""")
                if not righe:
                    errori.append(f"radar {a['nome']}: scheda non aperta"); continue
                for k, nome in PAESI.items():
                    v = next((x[1] for x in righe if x[0] == nome), None)
                    if v is None:
                        errori.append(f"radar {a['nome']}: manca la riga {nome}"); continue
                    n += 1
                    ok = str(R.anno_libero(morte(a), k)) in v and "verificare" not in v
                    if not ok:
                        errori.append(f"radar [{tipo}] {a['nome']}: {nome} «{v}»")
        # Già pubblici: la frase sull'autore (statoAutore) per gli stessi autori, con il flag «alleato o non noto» del Python
        await pg.goto(f"{BASE}/gia-pubblici/")
        await pg.wait_for_timeout(3000)
        for tipo, lista in casi.items():
            for a in lista:
                al = 1 if R.paesi_alleati(a.get("paesi")) else 0
                testo = await pg.evaluate("(x) => statoAutore(x).map(r => typeof r === 'string' ? r : r.textContent).join(' | ')",
                                          {"q": a["wikidata"], "n": a["nome"], "m": morte(a), "an": False, "al": bool(al)})
                n += 1
                nota = R.nota_trattato(a.get("paesi"), morte(a), OGGI)
                prima = testo.split(":")[0]
                if "Italia" not in prima or nota != ("Trattato di pace" in testo):
                    errori.append(f"Già pubblici [{tipo}] {a['nome']}: «{testo[:120]}»")
                if str(R.anno_libero(morte(a), "it")) not in testo or str(R.anno_libero(morte(a), "es")) not in testo:
                    errori.append(f"Già pubblici [{tipo}] {a['nome']}: date diverse dalle regole: «{testo[:120]}»")
        await b.close()
    errori += [f"errore JavaScript: {e}" for e in errjs]
    for e in errori:
        print("ERRORE:", e)
    print(f"Pagine vere controllate: {n} valori, errori: {len(errori)}")
    sys.exit(1 if errori else 0)


asyncio.run(main())
