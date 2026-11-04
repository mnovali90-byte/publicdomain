#!/usr/bin/env python3
"""Autori che entrano in pubblico dominio (UE: morte + 70 anni).

Scarica da Wikidata (dati aperti) gli autori morti nell'anno giusto e li salva in
data/<anno>.json. Una richiesta per mese, per evitare i timeout.

Uso:
    python scripts/aggiorna.py                # anno prossimo e quello dopo
    python scripts/aggiorna.py --anno 2027    # un anno preciso

Regola: morto nell'anno X  ->  libero dal 1 gennaio X + 71.
Se anche una sola richiesta fallisce, lo script si ferma con errore e NON
scrive nulla: i dati buoni già presenti non vengono mai sostituiti da dati parziali.
"""
import argparse
import datetime as dt
import json
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "PublicDomainTool/0.1 (https://github.com/mnovali90-byte/publicdomain)"
DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"

# scrittore, romanziere, poeta, drammaturgo, saggista, traduttore
OCCUPAZIONI = [
    "wd:Q36180", "wd:Q6625963", "wd:Q49757",
    "wd:Q214917", "wd:Q11774202", "wd:Q333634",
]

QUERY = """
SELECT ?autore ?autoreLabel ?nascita ?morte ?sl ?professioneLabel WHERE {{
  ?autore wdt:P570 ?morte .
  hint:Prior hint:rangeSafe true .
  FILTER(?morte >= "{da}T00:00:00Z"^^xsd:dateTime && ?morte < "{a}T00:00:00Z"^^xsd:dateTime)
  ?autore wdt:P31 wd:Q5 ;
          wdt:P106 ?professione ;
          wikibase:sitelinks ?sl .
  VALUES ?professione {{ {occ} }}
  OPTIONAL {{ ?autore wdt:P569 ?nascita }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "it,en". }}
}}
"""


def chiedi(da, a, tentativi=4):
    """Una richiesta a Wikidata. Se fallisce dopo i tentativi, solleva errore."""
    query = QUERY.format(da=da, a=a, occ=" ".join(OCCUPAZIONI))
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": query})
    ultimo_errore = None
    for t in range(tentativi):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/sparql-results+json",
            })
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)["results"]["bindings"]
        except urllib.error.HTTPError as e:
            ultimo_errore = e
            attesa = int(e.headers.get("Retry-After", 0) or 0) or 10 * (t + 1)
        except Exception as e:  # timeout, rete, JSON rotto
            ultimo_errore = e
            attesa = 10 * (t + 1)
        print(f"  tentativo {t + 1}/{tentativi} fallito: {ultimo_errore}", file=sys.stderr)
        time.sleep(attesa)
    raise RuntimeError(f"Wikidata non risponde per {da} -> {a}: {ultimo_errore}")


def scarica_anno(anno_morte, pausa=2):
    """Tutti gli autori morti in un anno, mese per mese. Duplicati uniti per codice Wikidata."""
    autori = {}
    for mese in range(1, 13):
        da = f"{anno_morte}-{mese:02d}-01"
        a = f"{anno_morte + 1}-01-01" if mese == 12 else f"{anno_morte}-{mese + 1:02d}-01"
        print(f"{anno_morte}-{mese:02d}...", file=sys.stderr)
        for r in chiedi(da, a):
            codice = r["autore"]["value"].rsplit("/", 1)[-1]
            morte = r["morte"]["value"][:10]
            d = autori.get(codice)
            if d is None:
                d = autori[codice] = {
                    "wikidata": codice,
                    "nome": r.get("autoreLabel", {}).get("value", codice),
                    "nascita": r.get("nascita", {}).get("value", "")[:10] or None,
                    "morte": morte,
                    "pagine_wikipedia": int(r["sl"]["value"]),
                    "professioni": [],
                }
            else:
                if morte < d["morte"]:  # più date di morte: tieni la più antica
                    d["morte"] = morte
                if not d["nascita"] and r.get("nascita"):
                    d["nascita"] = r["nascita"]["value"][:10]
            prof = r.get("professioneLabel", {}).get("value")
            if prof and prof not in d["professioni"]:
                d["professioni"].append(prof)
        time.sleep(pausa)
    return autori


def salva(anno_libero, autori):
    righe = sorted(autori.values(), key=lambda x: (-x["pagine_wikipedia"], x["nome"]))
    for d in righe:
        d["professioni"].sort()
        d["url"] = "https://www.wikidata.org/wiki/" + d["wikidata"]
    DATA_DIR.mkdir(exist_ok=True)
    pacchetto = {
        "anno_libero": anno_libero,
        "libero_dal": f"{anno_libero}-01-01",
        "regola": "UE: morte + 70 anni, dal 1 gennaio dell'anno successivo",
        "fonte": "Wikidata (CC0)",
        "aggiornato": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
        "totale": len(righe),
        "autori": righe,
    }
    percorso = DATA_DIR / f"{anno_libero}.json"
    percorso.write_text(json.dumps(pacchetto, ensure_ascii=False, indent=1), encoding="utf-8")
    return percorso


def aggiorna_indice():
    anni = sorted(int(p.stem) for p in DATA_DIR.glob("[0-9][0-9][0-9][0-9].json"))
    (DATA_DIR / "indice.json").write_text(json.dumps({"anni": anni}), encoding="utf-8")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--anno", type=int, help="anno in cui le opere diventano libere (es. 2027)")
    a = p.parse_args()
    oggi = dt.date.today().year
    anni = [a.anno] if a.anno else [oggi + 1, oggi + 2]
    # scarica tutto PRIMA di scrivere: se qualcosa fallisce, non cambia nulla
    risultati = {anno: scarica_anno(anno - 71) for anno in anni}
    for anno, autori in risultati.items():
        print(f"{anno}: {len(autori)} autori -> {salva(anno, autori)}")
    aggiorna_indice()


if __name__ == "__main__":
    main()
