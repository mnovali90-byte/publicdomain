#!/usr/bin/env python3
"""
Conta le edizioni in italiano di ogni autore nel catalogo SBN (Servizio Bibliotecario
Nazionale: il catalogo collettivo delle biblioteche italiane, gestito dall'ICCU).

Fonte: l'archivio SPARQL pubblico di SBN (https://triplestore.iccu.sbn.it/sparql), che
contiene le registrazioni dell'OPAC SBN in formato BIBFRAME. È lo stesso archivio che
Wikidata ha autorizzato per le sue interrogazioni federate.

Come si riconosce l'autore:
  1) dal codice VIAF che Wikidata indica per lui (proprietà P214): sicuro;
  2) se SBN non ha quell'autore collegato al VIAF, dal nome «Cognome, Nome» (cognome uguale,
     nome per intero o per iniziale; se i candidati sono troppi si lascia perdere). Può
     confondere gli omonimi: in quel caso si scrive "metodo": "nome".

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
import unicodedata
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
LIMITE_AGENTI = 1000
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


def _parole(testo):
    t = unicodedata.normalize("NFKD", testo or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z ]+", " ", t.lower()).split()


def nome_compatibile(nome, etichetta):
    """'Laura Ingalls Wilder' è compatibile con 'Wilder, Laura Ingalls' e con 'Wilder, L. I.';
    'A. A. Milne' con 'Milne, Alan Alexander'. Il cognome deve coincidere; i nomi, per intero o per iniziale."""
    if "," not in etichetta:
        return False
    cogn, resto = etichetta.split(",", 1)
    mie = _parole(nome)
    if not mie or _parole(cogn) != mie[-1:]:
        return False
    loro, nostri = _parole(resto), mie[:-1]
    if not nostri or not loro:
        return False
    a, b = nostri[0], loro[0]
    return a == b or (len(a) == 1 and b.startswith(a)) or (len(b) == 1 and a.startswith(b))


def agenti_per_nome(nome, interroga_fn):
    cognome = re.sub(r"[^\w]", "", nome.split()[-1])
    if len(cognome) < 3:
        return []
    righe = interroga_fn(f'SELECT DISTINCT ?a ?l WHERE {{ ?a <{LAB}> ?l . ?l bif:contains "\'{cognome}\'" . '
                         f'FILTER(CONTAINS(STR(?a), "/resource/Agent/")) }} LIMIT {LIMITE_AGENTI}')
    time.sleep(PAUSA)
    if len(righe) >= LIMITE_AGENTI:      # elenco tagliato: meglio non indovinare
        return []
    uri = [r["a"]["value"] for r in righe if nome_compatibile(nome, r["l"]["value"])]
    return uri if 0 < len(uri) <= 6 else []


def corpo(filtro):
    return (f"{filtro} ?c <{BF}agent> ?a . ?w <{BF}contribution> ?c . ?w <{BF}language> ?ln . "
            f"?ln <{VAL}> <{ITA}> .")


def conta(filtro, interroga_fn):
    c = corpo(filtro)
    n = int(interroga_fn(f"SELECT (COUNT(DISTINCT ?w) AS ?n) WHERE {{ {c} }}")[0]["n"]["value"])
    time.sleep(PAUSA)
    if not n:
        return 0, None, 0
    data = (f"?w <{BF}hasInstance> ?i . ?i <{BF}provisionActivity> ?pa . ?pa a <{BF}Publication> . "
            f"?pa <{BF}date> ?d . FILTER(REGEX(?d, \"^[0-9]{{4}}$\"))")
    r = interroga_fn(f"SELECT (MAX(?d) AS ?u) WHERE {{ {c} {data} }}")
    ultimo = int(r[0]["u"]["value"]) if r and "u" in r[0] else None
    time.sleep(PAUSA)
    r = interroga_fn(f"SELECT (COUNT(DISTINCT ?w) AS ?n) WHERE {{ {c} {data} FILTER(?d >= \"2000\") }}")
    time.sleep(PAUSA)
    return n, ultimo, int(r[0]["n"]["value"])


def edizioni_italiane(nome, viaf, interroga_fn=interroga):
    """Prima il codice VIAF; se SBN non ha quell'autore collegato al VIAF, il nome."""
    metodo, n, ultimo, dal_2000 = None, 0, None, 0
    if viaf:
        f = f'?a <{SAME}> <http://viaf.org/viaf/{viaf}> . FILTER(CONTAINS(STR(?a), "/resource/Agent/"))'
        n, ultimo, dal_2000 = conta(f, interroga_fn)
        metodo = "viaf"
    if not n:
        uri = agenti_per_nome(nome, interroga_fn)
        if uri:
            n, ultimo, dal_2000 = conta("VALUES ?a { " + " ".join(f"<{u}>" for u in uri) + " }", interroga_fn)
            metodo = "nome"
    return {"trovato": n > 0, "edizioni": n, "ultimo": ultimo, "dal_2000": dal_2000,
            "metodo": metodo if n else None, "fonte": "SBN"}


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
        if voce.get("v") != 3:      # 2 = VIAF poi nome; le voci della prima versione si rifanno
            return False
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
            voce["v"] = 3
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
                a.setdefault("traduzioni", {})["sbn_it"] = {k: v for k, v in voce.items() if k not in ("ts", "v")}
                ci_sono += 1
        f.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"sbn: {ci_sono} autori con dati ({fatti} nuovi, {errori} errori)", file=sys.stderr)


if __name__ == "__main__":
    elabora(dt.date.today())
