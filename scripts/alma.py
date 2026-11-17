#!/usr/bin/env python3
"""
Conta le edizioni di ogni autore nei cataloghi di due biblioteche nazionali che usano il sistema Alma:

  - Spagna: Biblioteca Nacional de España (BNE), edizioni in spagnolo.
    https://catalogo.bne.es/view/sru/34BNE_INST · dati CC0.
    L'autore si riconosce dal suo codice BNE che Wikidata indica (proprietà P950): niente omonimi.
  - Regno Unito: British Library (BL), edizioni in inglese.
    https://eu06.alma.exlibrisgroup.com/view/sru/44BL_MAIN
    La British Library non permette di cercare per codice d'autore (provato con ISNI e Library of
    Congress: zero risultati), quindi si cerca per cognome più anni di nascita e morte, che sono
    scritti nella scheda d'autore ("Brecht, Bertolt, 1898-1956"): gli omonimi sono quasi esclusi.

Si contano le notizie collegate all'autore in quella lingua e quante hanno anno di pubblicazione
dal 2000 in poi, chiedendo solo il numero di risultati (maximumRecords=0).

Scrive, per ogni autore, in "traduzioni": "bne_es" e "bl_en" nei file data/<anno>.json:
  {"trovato": bool, "edizioni": N, "dal_2000": N, "metodo": "codice_bne"|"nome_anni", "fonte": "BNE"|"British Library"}
Cache in data/cache_alma.json (45 giorni). Una richiesta alla volta.
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
from arricchisci import sparql  # noqa: E402

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
CACHE = DATA_DIR / "cache_alma.json"
VALIDITA_GIORNI = 45
PER_ANNO = int(os.environ.get("ALMA_PER_ANNO", "300"))
BUDGET_MINUTI = float(os.environ.get("BUDGET_MINUTI_ALMA", "30"))
FINE_LAVORO = time.time() + BUDGET_MINUTI * 60
PAUSA = 0.6
VERSIONE = 1
UA = "publicdomain-radar/1.0 (https://github.com/mnovali90-byte/publicdomain)"
CATALOGHI = {
    "bne_es": {"url": "https://catalogo.bne.es/view/sru/34BNE_INST", "lingua": "spa", "fonte": "BNE"},
    "bl_en": {"url": "https://eu06.alma.exlibrisgroup.com/view/sru/44BL_MAIN", "lingua": "eng", "fonte": "British Library"},
}
# controlli: se un giro trova meno di così, c'è un problema
CONTROLLI = {("bne_es", "Q38757"): ("Bertolt Brecht", 100), ("bl_en", "Q38757"): ("Bertolt Brecht", 300)}


def quanti(base, query, tentativi=3):
    url = base + "?" + urllib.parse.urlencode({"version": "1.2", "operation": "searchRetrieve", "query": query, "maximumRecords": "0"})
    for t in range(tentativi):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            testo = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
            m = re.search(r"numberOfRecords>(\d+)<", testo)
            if not m:
                raise ValueError("risposta senza numero di risultati")
            return int(m.group(1))
        except Exception:
            if t == tentativi - 1:
                raise
            time.sleep(3 * (t + 1))
        finally:
            time.sleep(PAUSA)


def _ascii(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def chiave_nome(a):
    """'Cognome nascita-morte' per la British Library, o None se mancano gli anni."""
    n, m = str(a.get("nascita") or "")[:4], str(a.get("morte") or "")[:4]
    if not (n.isdigit() and m.isdigit()):
        return None
    parole = [p for p in re.split(r"[\s,]+", a["nome"]) if p and not p.endswith(".")]
    if not parole:
        return None
    cognome = re.sub(r"[\"()]", "", parole[-1])
    return f"{cognome} {n}-{m}"


def conta(cat, filtro_autore, quanti_fn=quanti):
    c = CATALOGHI[cat]
    base = f'{filtro_autore} and alma.language={c["lingua"]}'
    n = quanti_fn(c["url"], base)
    d = quanti_fn(c["url"], f"{base} and alma.main_pub_date>=2000") if n else 0
    return {"trovato": n > 0, "edizioni": n, "dal_2000": min(d, n), "fonte": c["fonte"]}


def codici_bne(qids):
    out = {}
    for i in range(0, len(qids), 80):
        valori = " ".join(f"wd:{q}" for q in qids[i:i + 80])
        for b in sparql(f"SELECT ?a ?v WHERE {{ VALUES ?a {{ {valori} }} ?a wdt:P950 ?v }}"):
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


def voce_autore(a, codice_bne, quanti_fn=quanti):
    out = {}
    if codice_bne and re.fullmatch(r"[A-Za-z0-9]+", codice_bne):
        out["bne_es"] = dict(conta("bne_es", f"alma.authority_id={codice_bne}", quanti_fn), metodo="codice_bne")
    k = chiave_nome(a)
    if k:
        out["bl_en"] = dict(conta("bl_en", f'alma.creator all "{_ascii(k)}"', quanti_fn), metodo="nome_anni")
    return out


def elabora(oggi, quanti_fn=quanti, codici_fn=codici_bne):
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    file = [f for f in sorted(DATA_DIR.glob("*[0-9][0-9][0-9][0-9].json")) if not f.name.startswith(("us-", "anniversari-"))]
    pacchetti = [(f, json.loads(f.read_text(encoding="utf-8"))) for f in file]
    da_fare, visti = [], set()
    for _, p in pacchetti:
        for a in candidati(p):
            if a["wikidata"] not in visti and not e_recente(cache.get(a["wikidata"]), oggi):
                da_fare.append(a); visti.add(a["wikidata"])
    print(f"alma: {len(da_fare)} autori da controllare", file=sys.stderr)
    codici = codici_fn([a["wikidata"] for a in da_fare]) if da_fare else {}
    fatti = errori = 0
    for a in da_fare:
        if time.time() > FINE_LAVORO:
            print("  tempo finito: il resto al prossimo giro", file=sys.stderr)
            break
        try:
            voce = voce_autore(a, codici.get(a["wikidata"]), quanti_fn)
            voce["ts"], voce["v"] = oggi.isoformat(), VERSIONE
            cache[a["wikidata"]] = voce
            fatti += 1
        except Exception as e:
            errori += 1
            print(f"  {a['nome']}: {e}", file=sys.stderr)
            if errori >= 8 and fatti < errori:
                print("  i cataloghi non rispondono come previsto: mi fermo, i dati già presi restano.", file=sys.stderr)
                break
        if fatti % 20 == 19:
            CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    if fatti + errori >= 10 and errori > fatti:
        raise RuntimeError("i cataloghi non rispondono come previsto: non scrivo nulla.")
    conteggi = {k: 0 for k in CATALOGHI}
    for f, p in pacchetti:
        cambiato = False
        for a in p["autori"]:
            voce = cache.get(a["wikidata"]) or {}
            for k in CATALOGHI:
                if voce.get(k):
                    a.setdefault("traduzioni", {})[k] = voce[k]
                    conteggi[k] += 1; cambiato = True
        if cambiato:
            f.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
    for (k, q), (nome, minimo) in CONTROLLI.items():
        v = (cache.get(q) or {}).get(k)
        if v and v["edizioni"] < minimo:
            print(f"::warning::{k}: controllo fallito, {nome} ha {v['edizioni']} edizioni (attese almeno {minimo})", file=sys.stderr)
    print(f"alma: {conteggi} autori con dati ({fatti} nuovi, {errori} errori)", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "prova":     # prova veloce su pochi autori, senza scrivere nulla
        for nome, nasc, mor, bne in [("Bertolt Brecht", "1898", "1956", "XX1150786"), ("A. A. Milne", "1882", "1956", None),
                                     ("Robert Walser", "1878", "1956", None), ("Federico García Lorca", "1898", "1936", None)]:
            print(nome, voce_autore({"nome": nome, "nascita": nasc, "morte": mor}, bne))
    else:
        elabora(dt.date.today())
