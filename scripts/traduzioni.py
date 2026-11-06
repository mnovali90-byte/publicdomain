#!/usr/bin/env python3
"""
Controlla, con Open Library, in quali lingue esistono le opere di ciascun autore.

Per ogni autore (i più noti di ogni anno) fa UNA richiesta a Open Library, cerca le
sue opere (le più pubblicate per prime) e conta in quante esistono edizioni in
italiano, inglese, spagnolo, francese, tedesco.

Il risultato è un'indicazione, non un verdetto:
  - "esiste almeno un'edizione" non dice se la traduzione è buona o recente;
  - Open Library non conosce tutte le edizioni: zero può voler dire "non registrata";
  - il nome è l'unico aggancio, quindi si accettano solo opere il cui autore
    ha esattamente quel nome (gli omonimi vengono scartati).

Scrive, per ogni autore, il campo "traduzioni" nei file data/<anno>.json:
  {"opere": N, "con_lingua": N, "per_lingua": {"it": n, "en": n, ...},
   "parziale": bool, "fonte": "Open Library", "ts": "AAAA-MM-GG"}

Cache in data/cache_traduzioni.json (una voce vale 45 giorni).
"""
import concurrent.futures
import datetime as dt
import json
import os
import pathlib
import re
import sys
import time
import unicodedata
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from arricchisci import http_json  # noqa: E402  (stessa gestione di errori e tentativi)

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
CACHE = DATA_DIR / "cache_traduzioni.json"
VALIDITA_GIORNI = 45
PER_ANNO = int(os.environ.get("TRADUZIONI_PER_ANNO", "300"))   # quanti autori per anno
LAVORATORI = 2
PAUSA = 1.0               # secondi tra due richieste dello stesso lavoratore (cortesia verso Open Library)
BUDGET_MINUTI = float(os.environ.get("BUDGET_MINUTI_TRAD", "40"))
FINE_LAVORO = time.time() + BUDGET_MINUTI * 60
LIMITE = 100              # opere lette per autore
LINGUE = {"ita": "it", "eng": "en", "spa": "es", "fre": "fr", "ger": "de"}   # codici MARC usati da Open Library
URL = "https://openlibrary.org/search.json?"


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", s.lower()).split()


def stesso_autore(nome, nomi_trovati):
    """Il nome cercato e uno dei nomi dell'opera devono avere le stesse parole (ordine libero)."""
    voluto = sorted(norm(nome))
    return any(sorted(norm(n)) == voluto for n in nomi_trovati or [])


def conta_lingue(nome, risposta):
    """Dalla risposta di Open Library: quante opere dell'autore, e in quante lingue."""
    docs = [d for d in (risposta or {}).get("docs", []) if stesso_autore(nome, d.get("author_name"))]
    per_lingua = {v: 0 for v in LINGUE.values()}
    con_lingua = 0
    for d in docs:
        lingue = set(d.get("language") or [])
        if lingue:
            con_lingua += 1
        for marc, breve in LINGUE.items():
            if marc in lingue:
                per_lingua[breve] += 1
    return {
        "opere": len(docs),
        "con_lingua": con_lingua,
        "per_lingua": per_lingua,
        "parziale": int((risposta or {}).get("numFound", 0)) > LIMITE,
        "fonte": "Open Library",
    }


def interroga(nome):
    q = URL + urllib.parse.urlencode({
        "author": nome, "limit": LIMITE, "sort": "editions",
        "fields": "key,title,language,author_name,first_publish_year,edition_count",
    })
    r = http_json(q)
    time.sleep(PAUSA)
    return conta_lingue(nome, r)


def e_recente(voce, oggi):
    try:
        return (oggi - dt.date.fromisoformat(voce["ts"])).days < VALIDITA_GIORNI
    except Exception:
        return False


def carica_cache():
    return json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}


def salva_cache(cache):
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def candidati(pacchetto):
    """I più noti dell'anno: prima per indice di popolarità (se c'è), poi per pagine Wikimedia."""
    lista = [a for a in pacchetto["autori"] if a.get("letterario") and a.get("n_opere", 1) > 0 and not re.fullmatch(r"Q\d+", a["nome"])]
    lista.sort(key=lambda a: (-(a.get("indice") if a.get("indice") is not None else -1), -a.get("pagine_wikipedia", 0)))
    return lista[:PER_ANNO]


def elabora(oggi, interroga_fn=interroga):
    cache = carica_cache()
    file = [f for f in sorted(DATA_DIR.glob("*[0-9][0-9][0-9][0-9].json")) if not f.name.startswith(("us-", "anniversari-"))]
    pacchetti = [(f, json.loads(f.read_text(encoding="utf-8"))) for f in file]
    da_fare = []
    for _, p in pacchetti:
        da_fare += [a for a in candidati(p) if not e_recente(cache.get(a["wikidata"]), oggi)]
    print(f"traduzioni: {len(da_fare)} autori da controllare", file=sys.stderr)
    errori = fatti = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=LAVORATORI) as ex:
        for i in range(0, len(da_fare), 20):
            if time.time() > FINE_LAVORO:
                print("  tempo finito: il resto al prossimo giro", file=sys.stderr)
                break
            gruppo = da_fare[i:i + 20]
            futuri = {a["wikidata"]: (a, ex.submit(interroga_fn, a["nome"])) for a in gruppo}
            for c, (a, f) in futuri.items():
                try:
                    voce = f.result()
                    voce["ts"] = oggi.isoformat()
                    cache[c] = voce
                    fatti += 1
                except Exception as e:
                    errori += 1
                    print(f"  {a['nome']}: {e}", file=sys.stderr)
            salva_cache(cache)
    if fatti + errori >= 10 and errori > fatti:
        raise RuntimeError("Open Library non risponde come previsto: non scrivo nulla.")
    ci_sono = 0
    for f, p in pacchetti:
        for a in p["autori"]:
            voce = cache.get(a["wikidata"])
            if voce:
                a["traduzioni"] = {k: v for k, v in voce.items()}
                ci_sono += 1
        p["traduzioni_aggiornato"] = oggi.isoformat()
        f.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
    salva_cache(cache)
    print(f"traduzioni: {ci_sono} autori con dati ({fatti} nuovi, {errori} errori)", file=sys.stderr)


if __name__ == "__main__":
    elabora(dt.date.today())
