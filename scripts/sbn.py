#!/usr/bin/env python3
"""
Conta le edizioni in italiano di ogni autore nel catalogo SBN (Servizio Bibliotecario
Nazionale: il catalogo collettivo delle biblioteche italiane, gestito dall'ICCU).

Fonte: l'archivio SPARQL pubblico di SBN (https://triplestore.iccu.sbn.it/sparql), che
contiene le registrazioni dell'OPAC SBN in formato BIBFRAME. È lo stesso archivio che
Wikidata ha autorizzato per le sue interrogazioni federate.

Come si riconosce l'autore:
  1) dal codice VIAF che Wikidata indica per lui (proprietà P214): sicuro;
  2) se manca, dal nome nella forma «Cognome, Nome» esatta (può confondere gli omonimi):
     in quel caso si scrive "metodo": "nome".

Cosa si conta: le registrazioni (opere) il cui autore o collaboratore è quella persona e
la cui lingua è l'italiano, con l'anno di pubblicazione più recente e quante sono dal 2000.
Non dice se l'edizione è ancora in commercio, né quanto è buona la traduzione.

Scrive, per ogni autore, "traduzioni": {"sbn_it": {...}} nei file data/<anno>.json:
  {"trovato": bool, "edizioni": N, "ultimo": anno|None, "dal_2000": N,
   "metodo": "viaf"|"nome", "fonte": "SBN"}
Cache in data/cache_sbn.json (45 giorni). Gentile con il server: una richiesta alla volta.
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
CACHE = DATA_DIR / "cache_sbn.json"
VALIDITA_GIORNI = 45
PER_ANNO = int(os.environ.get("SBN_PER_ANNO", "300"))
BUDGET_MINUTI = float(os.environ.get("BUDGET_MINUTI_SBN", "40"))
FINE_LAVORO = time.time() + BUDGET_MINUTI * 60
PAUSA = 0.6
ENDPOINT = "https://triplestore.iccu.sbn.it/sparql"
BF = "http://id.loc.gov/ontologies/bibframe/"
SAME = "http://www.w3.org/2002/07/owl#sameAs"
LAB = "http://www.w3.org/2000/01/rdf-schema#label"
VAL = "http://www.w3.org/1999/02/22-rdf-syntax-ns#value"
ITA = "http://id.loc.gov/vocabulary/languages/ita"
UA = "publicdomain-radar/1.0 (https://github.com/mnovali90-byte/publicdomain)"


def interroga(query, tentativi=3):
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": query, "format": "application/sparql-results+json"})
    ultimo = None
    for t in range(tentativi):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/sparql-results+json", "User-Agent": UA})
            with urllib.request.urlopen(req, timeout=100) as r:
                return json.load(r)["results"]["bindings"]
        except Exception as e:
            ultimo = e
            time.sleep(5 * (t + 1))
    raise RuntimeError(f"SBN: {str(ultimo)[:120]}")


def etichetta_sbn(nome):
    """'Laura Ingalls Wilder' -> 'Wilder, Laura Ingalls' (la forma usata da SBN)."""
    parole = nome.split()
    return f"{parole[-1]}, {' '.join(parole[:-1])}" if len(parole) > 1 else nome


def filtro_agente(viaf, nome):
    if viaf:
        return f'?a <{SAME}> <http://viaf.org/viaf/{viaf}> . FILTER(CONTAINS(STR(?a), "/resource/Agent/"))', "viaf"
    esatto = etichetta_sbn(nome).replace("\\", "").replace('"', "")
    cognome = re.sub(r"[^\w]", "", nome.split()[-1])
    if len(cognome) < 3:
        return None, None
    return (f'?a <{LAB}> ?l . ?l bif:contains "\'{cognome}\'" . '
            f'FILTER(STR(?l) = "{esatto}" && CONTAINS(STR(?a), "/resource/Agent/"))'), "nome"


def corpo(filtro):
    return (f"{filtro} ?c <{BF}agent> ?a . ?w <{BF}contribution> ?c . ?w <{BF}language> ?ln . "
            f"?ln <{VAL}> <{ITA}> .")


def edizioni_italiane(nome, viaf, interroga_fn=interroga):
    filtro, metodo = filtro_agente(viaf, nome)
    if not filtro:
        return {"trovato": False, "edizioni": 0, "ultimo": None, "dal_2000": 0, "metodo": None, "fonte": "SBN"}
    c = corpo(filtro)
    n = int(interroga_fn(f"SELECT (COUNT(DISTINCT ?w) AS ?n) WHERE {{ {c} }}")[0]["n"]["value"])
    time.sleep(PAUSA)
    ultimo, dal_2000 = None, 0
    if n:
        data = (f"?w <{BF}hasInstance> ?i . ?i <{BF}provisionActivity> ?pa . ?pa a <{BF}Publication> . "
                f"?pa <{BF}date> ?d . FILTER(REGEX(?d, \"^[0-9]{{4}}$\"))")
        r = interroga_fn(f"SELECT (MAX(?d) AS ?u) WHERE {{ {c} {data} }}")
        ultimo = int(r[0]["u"]["value"]) if r and "u" in r[0] else None
        time.sleep(PAUSA)
        r = interroga_fn(f"SELECT (COUNT(DISTINCT ?w) AS ?n) WHERE {{ {c} {data} FILTER(?d >= \"2000\") }}")
        dal_2000 = int(r[0]["n"]["value"])
        time.sleep(PAUSA)
    return {"trovato": n > 0, "edizioni": n, "ultimo": ultimo, "dal_2000": dal_2000, "metodo": metodo, "fonte": "SBN"}


def codici_viaf(qids):
    """Il codice VIAF che Wikidata indica per ogni autore (proprietà P214)."""
    out = {}
    for i in range(0, len(qids), 80):
        valori = " ".join(f"wd:{q}" for q in qids[i:i + 80])
        for b in sparql(f"SELECT ?a ?v WHERE {{ VALUES ?a {{ {valori} }} ?a wdt:P214 ?v }}"):
            out.setdefault(b["a"]["value"].rsplit("/", 1)[-1], b["v"]["value"])
        time.sleep(2)
    return out


def e_recente(voce, oggi):
    try:
        return (oggi - dt.date.fromisoformat(voce["ts"])).days < VALIDITA_GIORNI
    except Exception:
        return False


def candidati(pacchetto):
    lista = [a for a in pacchetto["autori"] if a.get("letterario") and a.get("n_opere", 1) > 0 and not re.fullmatch(r"Q\d+", a["nome"])]
    lista.sort(key=lambda a: (-(a.get("indice") if a.get("indice") is not None else -1), -a.get("pagine_wikipedia", 0)))
    return lista[:PER_ANNO]


def elabora(oggi, conta_fn=edizioni_italiane, viaf_fn=codici_viaf):
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    file = sorted(DATA_DIR.glob("[0-9][0-9][0-9][0-9].json"))
    pacchetti = [(f, json.loads(f.read_text(encoding="utf-8"))) for f in file]
    da_fare = []
    for _, p in pacchetti:
        da_fare += [a for a in candidati(p) if not e_recente(cache.get(a["wikidata"]), oggi)]
    print(f"sbn: {len(da_fare)} autori da controllare", file=sys.stderr)
    viaf = viaf_fn([a["wikidata"] for a in da_fare]) if da_fare else {}
    fatti = errori = 0
    for i, a in enumerate(da_fare):
        if time.time() > FINE_LAVORO:
            print("  tempo finito: il resto al prossimo giro", file=sys.stderr)
            break
        try:
            voce = conta_fn(a["nome"], viaf.get(a["wikidata"]))
            voce["ts"] = oggi.isoformat()
            cache[a["wikidata"]] = voce
            fatti += 1
        except Exception as e:
            errori += 1
            print(f"  {a['nome']}: {e}", file=sys.stderr)
            if errori >= 8 and fatti < errori:
                print("  SBN non risponde come previsto: mi fermo, i dati già presi restano.", file=sys.stderr)
                break
        if fatti % 20 == 19:
            CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    if fatti + errori >= 10 and errori > fatti:
        raise RuntimeError("SBN non risponde come previsto: non scrivo nulla.")
    ci_sono = 0
    for f, p in pacchetti:
        for a in p["autori"]:
            voce = cache.get(a["wikidata"])
            if voce:
                a.setdefault("traduzioni", {})["sbn_it"] = {k: v for k, v in voce.items() if k != "ts"}
                ci_sono += 1
        f.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"sbn: {ci_sono} autori con dati ({fatti} nuovi, {errori} errori)", file=sys.stderr)


if __name__ == "__main__":
    elabora(dt.date.today())
