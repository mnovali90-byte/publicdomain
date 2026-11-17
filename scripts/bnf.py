#!/usr/bin/env python3
"""
Conta le edizioni in francese di ogni autore nel catalogo della Biblioteca nazionale di Francia (BnF).

Fonte: il servizio SRU pubblico del Catalogue général della BnF (https://catalogue.bnf.fr/api/SRU),
gratuito e senza registrazione; i dati della BnF sono sotto Licence Ouverte (Etalab).

Come si riconosce l'autore: dal suo codice BnF che Wikidata indica (proprietà P268). Si cercano le
notizie bibliografiche collegate a quella scheda d'autore (criterio bib.author2bib), quindi niente
omonimi. Se Wikidata non ha il codice BnF, l'autore resta senza dato (non si cerca per nome).

Cosa si conta: le notizie in lingua francese collegate all'autore (anche ristampe, antologie e libri
in cui compare come collaboratore) e quante hanno una data dal 2000 in poi.

Scrive, per ogni autore, "traduzioni": {"bnf_fr": {...}} nei file data/<anno>.json:
  {"trovato": bool, "edizioni": N, "dal_2000": N, "metodo": "codice_bnf", "fonte": "BnF"}
Cache in data/cache_bnf.json (45 giorni). Gentile con il server: una richiesta alla volta.
"""
import datetime as dt
import json
import os
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from arricchisci import sparql  # noqa: E402  (Wikidata, con gestione degli errori)

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
CACHE = DATA_DIR / "cache_bnf.json"
VALIDITA_GIORNI = 45
PER_ANNO = int(os.environ.get("BNF_PER_ANNO", "300"))
BUDGET_MINUTI = float(os.environ.get("BUDGET_MINUTI_BNF", "25"))
FINE_LAVORO = time.time() + BUDGET_MINUTI * 60
PAUSA = 0.6
VERSIONE = 1
ENDPOINT = "https://catalogue.bnf.fr/api/SRU"
UA = "publicdomain-radar/1.0 (https://github.com/mnovali90-byte/publicdomain)"
# Autori di cui sappiamo che la BnF ha molte edizioni francesi: se un giro ne trova meno, c'è un problema.
CONTROLLI = {"Q38757": ("Bertolt Brecht", 300)}


def quanti(query, tentativi=3):
    """Numero di notizie che rispondono alla ricerca (senza scaricarle)."""
    url = ENDPOINT + "?" + urllib.parse.urlencode({"version": "1.2", "operation": "searchRetrieve",
                                                   "query": query, "maximumRecords": "0"})
    for t in range(tentativi):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            testo = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
            m = re.search(r"<srw:numberOfRecords>(\d+)</srw:numberOfRecords>", testo)
            if not m:
                raise ValueError("risposta senza numero di risultati")
            return int(m.group(1))
        except Exception:
            if t == tentativi - 1:
                raise
            time.sleep(3 * (t + 1))
        finally:
            time.sleep(PAUSA)


def edizioni_francesi(codice_bnf, anno_oggi, quanti_fn=quanti):
    rid = re.sub(r"\D", "", codice_bnf or "")[:8]
    if len(rid) != 8:
        return {"trovato": False, "edizioni": 0, "dal_2000": 0, "metodo": None, "fonte": "BnF"}
    base = f'bib.author2bib all "{rid}" and bib.language any "fre"'
    n = quanti_fn(base)
    anni = " ".join(str(y) for y in range(2000, anno_oggi + 1))
    d2000 = quanti_fn(f'{base} and bib.date any "{anni}"') if n else 0
    # niente min(): se i recenti superano il totale è un errore da vedere (scripts/controlli.py)
    return {"trovato": n > 0, "edizioni": n, "dal_2000": d2000, "metodo": "codice_bnf", "fonte": "BnF"}


def codici_bnf(qids):
    """Il codice BnF che Wikidata indica per ogni autore (proprietà P268)."""
    out = {}
    for i in range(0, len(qids), 80):
        valori = " ".join(f"wd:{q}" for q in qids[i:i + 80])
        for b in sparql(f"SELECT ?a ?v WHERE {{ VALUES ?a {{ {valori} }} ?a wdt:P268 ?v }}"):
            out.setdefault(b["a"]["value"].rsplit("/", 1)[-1], b["v"]["value"])
        time.sleep(2)
    return out


def e_recente(voce, oggi):
    try:
        return voce.get("v") == VERSIONE and (oggi - dt.date.fromisoformat(voce["ts"])).days < VALIDITA_GIORNI
    except Exception:
        return False


def candidati(pacchetto):
    lista = [a for a in pacchetto["autori"] if a.get("letterario") and a.get("n_opere", 1) > 0 and not re.fullmatch(r"Q\d+", a["nome"])]
    lista.sort(key=lambda a: (-(a.get("indice") if a.get("indice") is not None else -1), -a.get("pagine_wikipedia", 0)))
    return lista[:PER_ANNO]


def elabora(oggi, conta_fn=edizioni_francesi, codici_fn=codici_bnf):
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    file = [f for f in sorted(DATA_DIR.glob("*[0-9][0-9][0-9][0-9].json")) if not f.name.startswith(("us-", "anniversari-", "es-"))]
    pacchetti = [(f, json.loads(f.read_text(encoding="utf-8"))) for f in file]
    da_fare, visti = [], set()
    for _, p in pacchetti:
        for a in candidati(p):
            if a["wikidata"] not in visti and not e_recente(cache.get(a["wikidata"]), oggi):
                da_fare.append(a); visti.add(a["wikidata"])
    print(f"bnf: {len(da_fare)} autori da controllare", file=sys.stderr)
    codici = codici_fn([a["wikidata"] for a in da_fare]) if da_fare else {}
    fatti = errori = 0
    for a in da_fare:
        if time.time() > FINE_LAVORO:
            print("  tempo finito: il resto al prossimo giro", file=sys.stderr)
            break
        try:
            voce = conta_fn(codici.get(a["wikidata"]), oggi.year)
            voce["ts"], voce["v"] = oggi.isoformat(), VERSIONE
            cache[a["wikidata"]] = voce
            fatti += 1
        except Exception as e:
            errori += 1
            print(f"  {a['nome']}: {e}", file=sys.stderr)
            if errori >= 8 and fatti < errori:
                print("  la BnF non risponde come previsto: mi fermo, i dati già presi restano.", file=sys.stderr)
                break
        if fatti % 20 == 19:
            CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    if fatti + errori >= 10 and errori > fatti:
        raise RuntimeError("la BnF non risponde come previsto: non scrivo nulla.")
    ci_sono = 0
    for f, p in pacchetti:
        cambiato = False
        for a in p["autori"]:
            voce = cache.get(a["wikidata"])
            if voce and voce.get("metodo"):          # solo autori con codice BnF
                a.setdefault("traduzioni", {})["bnf_fr"] = {k: v for k, v in voce.items() if k not in ("ts", "v")}
                ci_sono += 1; cambiato = True
        if cambiato:
            f.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
    for q, (nome, minimo) in CONTROLLI.items():
        v = cache.get(q)
        if v and v["edizioni"] < minimo:
            print(f"::warning::BnF: controllo fallito, {nome} ha {v['edizioni']} edizioni (attese almeno {minimo})", file=sys.stderr)
    print(f"bnf: {ci_sono} autori con dati ({fatti} nuovi, {errori} errori)", file=sys.stderr)


if __name__ == "__main__":
    elabora(dt.date.today())
