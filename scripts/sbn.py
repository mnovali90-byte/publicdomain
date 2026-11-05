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
     nome per intero o per iniziale; se SBN indica gli anni e non coincidono con Wikidata la
     scheda è un omonimo e si scarta; se i candidati sono troppi si lascia perdere). Può
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
SOGLIA_NOTO = 40          # pagine Wikipedia: da qui in su l'autore è «molto noto»
SOGLIA_POCHE = 3          # e con così poche edizioni in SBN è sospetto
# Autori di cui sappiamo che in SBN hanno molte edizioni italiane: se un giro ne trova meno, c'è un bug.
CONTROLLI = {"Q38757": ("Bertolt Brecht", 300), "Q207036": ("A. A. Milne", 50),
             "Q237514": ("Laura Ingalls Wilder", 200), "Q529858": ("Giovanni Papini", 250)}
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
    def uguali(a, b):
        return a == b or (len(a) == 1 and b.startswith(a)) or (len(b) == 1 and a.startswith(b))
    # ogni nome si confronta con il suo corrispondente, non solo il primo:
    # «A. A.» è compatibile con «Alan Alexander» ma non con «Annabel» né con «A. J. M.»
    if not all(uguali(a, b) for a, b in zip(nostri, loro)):
        return False
    # se uno ha più nomi dell'altro, i nomi dell'altro devono essere scritti per intero e uguali
    corto = nostri if len(nostri) < len(loro) else loro
    lungo = loro if corto is nostri else nostri
    return len(nostri) == len(loro) or all(c == l for c, l in zip(corto, lungo))


def anni_etichetta(etichetta):
    """'Milne, A. A. <1882-1956>' -> (1882, 1956). Mancano o sono incompleti: None."""
    m = re.search(r"<\s*(?:ca\.?\s*)?(\d{3,4})?\s*-\s*(\d{3,4})?\s*>", etichetta or "")
    if not m:
        return None, None
    return (int(m.group(1)) if m.group(1) else None), (int(m.group(2)) if m.group(2) else None)


def anni_compatibili(etichetta, nascita, morte):
    """True = gli anni coincidono (±1); False = contraddicono; None = non confrontabili."""
    n_et, m_et = anni_etichetta(etichetta)
    try:
        n_wd = int(str(nascita)[:4]) if nascita else None
        m_wd = int(str(morte)[:4]) if morte else None
    except ValueError:
        return None
    esito = None
    for et, wd in ((n_et, n_wd), (m_et, m_wd)):
        if et and wd:
            if abs(et - wd) > 1:
                return False
            esito = True
    return esito


def agenti_per_nome(nome, interroga_fn, nascita=None, morte=None):
    """Schede SBN con cognome uguale e nome compatibile. Restituisce (uri, verificato):
    se l'etichetta ha gli anni e contraddicono Wikidata, la scheda si scarta (è un omonimo);
    verificato = tutte le schede tenute hanno gli anni che coincidono."""
    cognome = re.sub(r"[^\w]", "", nome.split()[-1])
    if len(cognome) < 3:
        return [], False
    righe = interroga_fn(f'SELECT DISTINCT ?a ?l WHERE {{ ?a <{LAB}> ?l . ?l bif:contains "\'{cognome}\'" . '
                         f'FILTER(CONTAINS(STR(?a), "/resource/Agent/")) }} LIMIT {LIMITE_AGENTI}')
    time.sleep(PAUSA)
    if len(righe) >= LIMITE_AGENTI:      # elenco tagliato: meglio non indovinare
        return [], False
    tenute = []
    for r in righe:
        et = r["l"]["value"]
        if nome_compatibile(nome, et) and anni_compatibili(et, nascita, morte) is not False:
            tenute.append((r["a"]["value"], anni_compatibili(et, nascita, morte)))
    if not 0 < len(tenute) <= 6:
        return [], False
    return [u for u, _ in tenute], all(v is True for _, v in tenute)


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


def edizioni_italiane(nome, viaf, nascita=None, morte=None, interroga_fn=interroga):
    """Prima il codice VIAF; se SBN non ha quell'autore collegato al VIAF, il nome."""
    metodo, n, ultimo, dal_2000 = None, 0, None, 0
    if viaf:
        f = f'?a <{SAME}> <http://viaf.org/viaf/{viaf}> . FILTER(CONTAINS(STR(?a), "/resource/Agent/"))'
        n, ultimo, dal_2000 = conta(f, interroga_fn)
        metodo = "viaf"
    if not n:
        uri, verificato = agenti_per_nome(nome, interroga_fn, nascita, morte)
        if uri:
            n, ultimo, dal_2000 = conta("VALUES ?a { " + " ".join(f"<{u}>" for u in uri) + " }", interroga_fn)
            metodo = "nome_anni" if verificato else "nome"
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
        if voce.get("v") != 5:      # 2 = VIAF poi nome; le voci della prima versione si rifanno
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
    file = sorted(DATA_DIR.glob("*[0-9][0-9][0-9][0-9].json"))
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
            voce = conta_fn(a["nome"], viaf.get(a["wikidata"]), a.get("nascita"), a.get("morte"))
            voce["ts"] = oggi.isoformat()
            voce["v"] = 5
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
    ci_sono, sospetti = 0, []
    for f, p in pacchetti:
        for a in p["autori"]:
            voce = cache.get(a["wikidata"])
            if voce:
                dati = {k: v for k, v in voce.items() if k not in ("ts", "v")}
                if a.get("pagine_wikipedia", 0) >= SOGLIA_NOTO and dati["edizioni"] <= SOGLIA_POCHE:
                    dati["sospetto"] = True
                    sospetti.append({"wikidata": a["wikidata"], "nome": a["nome"], "pagine": a["pagine_wikipedia"],
                                     "edizioni": dati["edizioni"], "metodo": dati.get("metodo")})
                a.setdefault("traduzioni", {})["sbn_it"] = dati
                ci_sono += 1
        f.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA_DIR / "sospetti_sbn.json").write_text(json.dumps(sospetti, ensure_ascii=False, indent=1), encoding="utf-8")
    for q, (nome, minimo) in CONTROLLI.items():
        v = cache.get(q)
        if v and v["edizioni"] < minimo:
            print(f"::warning::SBN: controllo fallito, {nome} ha {v['edizioni']} edizioni (attese almeno {minimo})", file=sys.stderr)
    print(f"sbn: {len(sospetti)} autori sospetti (molto noti, quasi nessuna edizione) in data/sospetti_sbn.json", file=sys.stderr)
    print(f"sbn: {ci_sono} autori con dati ({fatti} nuovi, {errori} errori)", file=sys.stderr)


if __name__ == "__main__":
    elabora(dt.date.today())
