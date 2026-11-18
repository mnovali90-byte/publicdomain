#!/usr/bin/env python3
"""
USA: conta le edizioni in inglese di ogni autore nel catalogo della Library of Congress (LC).

Fonte: il servizio SRU pubblico del catalogo LC (http://lx2.loc.gov:210/LCDB) e le schede d'autore di id.loc.gov.
Come si riconosce l'autore (dal codice, come per la BnF; prove in docs/registro-prove.md, 18/11/2026):
  1. codice LC che Wikidata indica per l'autore (P244) -> intestazione ufficiale della scheda d'autore su id.loc.gov
     («Wells, H. G. (Herbert George), 1866-1946»); se il codice non c'è, l'autore resta senza dato (niente nome);
  2. nel catalogo si cercano le notizie con quell'intestazione (senza accenti: con gli accenti il catalogo non trova);
  3. il catalogo non filtra per lingua né per anno, quindi si scaricano le notizie e si conta una notizia solo se
     l'intestazione compare come autore o collaboratore (campi 100, 700, 800, non solo come soggetto 600) e la
     lingua è l'inglese (campo 008); «dal 2000» dall'anno nel campo 008.
Come per gli altri cataloghi si contano tutte le pubblicazioni collegate alla persona, anche le collaborazioni.

Scrive per ogni autore "traduzioni": {"loc_en": {"trovato", "edizioni", "dal_2000", "metodo": "codice_lc", "fonte"}}.
Cache in data/cache_loc.json (45 giorni). Una richiesta alla volta, con pause: il servizio chiude le connessioni
se si va troppo veloci.
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
import alma  # noqa: E402  (stessi autori candidati degli altri cataloghi)

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
CACHE = DATA_DIR / "cache_loc.json"
VALIDITA_GIORNI = 45
BUDGET_MINUTI = float(os.environ.get("BUDGET_MINUTI_LOC", "30"))
FINE_LAVORO = time.time() + BUDGET_MINUTI * 60
VERSIONE = 1
SRU = "http://lx2.loc.gov:210/LCDB"
UA = "publicdomain-radar/1.0 (https://github.com/mnovali90-byte/publicdomain)"
PAUSA = 2.5
MASSIMO = 2000
CONTROLLI = {"Q42511": ("H. G. Wells", 400)}


class ErroreTecnico(Exception):
    pass


def sa(t):
    return "".join(c for c in unicodedata.normalize("NFKD", t or "") if not unicodedata.combining(c))


def chiave(t):
    return re.sub(r"[^a-z0-9]+", " ", sa(t).lower()).strip()


def get(url, tentativi=5):
    ultimo = None
    for t in range(tentativi):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            x = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "replace")
            time.sleep(PAUSA)
            return x
        except Exception as e:
            ultimo = e
            time.sleep(8 * (t + 1))
    raise ErroreTecnico(str(ultimo)[:150])


def intestazione(codice):
    """Intestazione ufficiale della scheda d'autore LC (None se il codice non esiste più)."""
    t = get(f"https://id.loc.gov/authorities/names/{codice}.json")
    for x in json.loads(t):
        if x.get("@id", "").endswith("/" + codice) and "http://www.loc.gov/mads/rdf/v1#authoritativeLabel" in x:
            return x["http://www.loc.gov/mads/rdf/v1#authoritativeLabel"][0]["@value"]
    return None


def pagina(lab, start):
    """Una pagina di risultati; si riprova se arrivano meno notizie del previsto (il servizio a volte le tronca)."""
    for t in range(4):
        x = get(SRU + "?" + urllib.parse.urlencode({"version": "1.1", "operation": "searchRetrieve", "query": f'bath.personalName="{sa(lab)}"',
                                                    "maximumRecords": "50", "startRecord": str(start), "recordSchema": "marcxml"}))
        m = re.search(r"numberOfRecords>(\d+)<", x)
        if not m:
            time.sleep(10)
            continue
        tot = int(m.group(1))
        recs = re.findall(r"<record xmlns[^>]*>(.*?)</record>", x, re.S)
        attese = max(0, min(50, tot - start + 1))
        if len(recs) == attese:
            return tot, recs
        time.sleep(10)
    raise ErroreTecnico(f"pagina {start} incompleta")


def notizie(lab):
    out, start = [], 1
    while True:
        tot, recs = pagina(lab, start)
        for rec in recs:
            ruoli = set()
            for tag, corpo in re.findall(r'tag="(100|700|800|600)"[^>]*>(.*?)</datafield>', rec, re.S):
                testo = " ".join(v for c, v in re.findall(r'code="(\w)">([^<]*)<', corpo) if c in "abcdq")
                if chiave(testo).startswith(chiave(lab)):
                    ruoli.add("soggetto" if tag == "600" else "autore o collaboratore")
            f008 = (re.findall(r'tag="008">([^<]*)<', rec) or [""])[0]
            out.append({"ruoli": sorted(ruoli), "lingua": f008[35:38], "anno": f008[7:11]})
        start += 50
        if start > tot or start > MASSIMO:
            return tot, out


def edizioni_inglesi(codici, anno_oggi):
    """codici: i codici LC (P244) dell'autore. Distingue: senza codice / codice senza scheda / riconosciuto."""
    if not codici:
        return {"trovato": False, "edizioni": 0, "dal_2000": 0, "metodo": None, "fonte": "Library of Congress"}
    contate, intestazioni = {}, []
    for c in codici:
        lab = intestazione(c)
        if not lab:
            continue
        intestazioni.append(lab)
        tot, recs = notizie(lab)
        for i, r in enumerate(recs):
            if "autore o collaboratore" in r["ruoli"] and r["lingua"] == "eng":
                contate[(lab, i)] = r
    if not intestazioni:
        return {"trovato": False, "edizioni": 0, "dal_2000": 0, "metodo": None, "fonte": "Library of Congress", "nota": "codice LC senza scheda"}
    d = sum(1 for r in contate.values() if r["anno"].isdigit() and 2000 <= int(r["anno"]) <= anno_oggi)
    return {"trovato": len(contate) > 0, "edizioni": len(contate), "dal_2000": d, "metodo": "codice_lc",
            "fonte": "Library of Congress", "intestazione": intestazioni[0]}


def codici_lc(qids):
    out = {}
    for i in range(0, len(qids), 60):
        for b in sparql("SELECT ?a ?v WHERE { VALUES ?a { " + " ".join("wd:" + q for q in qids[i:i + 60]) + " } ?a wdt:P244 ?v }"):
            out.setdefault(b["a"]["value"].rsplit("/", 1)[-1], [])
            if b["v"]["value"] not in out[b["a"]["value"].rsplit("/", 1)[-1]]:
                out[b["a"]["value"].rsplit("/", 1)[-1]].append(b["v"]["value"])
        time.sleep(2)
    return out


def e_recente(voce, oggi):
    try:
        return voce.get("v") == VERSIONE and (oggi - dt.date.fromisoformat(voce["ts"])).days < VALIDITA_GIORNI
    except Exception:
        return False


def elabora(oggi):
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    file = [f for f in sorted(DATA_DIR.glob("*[0-9][0-9][0-9][0-9].json")) if not f.name.startswith(("us-", "anniversari-"))]
    pacchetti = [(f, json.loads(f.read_text(encoding="utf-8"))) for f in file]
    da_fare, visti = [], set()
    for _, p in pacchetti:
        for a in alma.candidati(p):
            if a["wikidata"] not in visti and not e_recente(cache.get(a["wikidata"]), oggi):
                da_fare.append(a); visti.add(a["wikidata"])
    print(f"loc: {len(da_fare)} autori da controllare", file=sys.stderr)
    codici = codici_lc([a["wikidata"] for a in da_fare]) if da_fare else {}
    fatti = errori = 0
    for a in da_fare:
        if time.time() > FINE_LAVORO:
            print("  tempo finito: il resto al prossimo giro", file=sys.stderr)
            pathlib.Path(".incompleto").touch()
            break
        try:
            voce = edizioni_inglesi(codici.get(a["wikidata"], []), oggi.year)
            voce["ts"], voce["v"] = oggi.isoformat(), VERSIONE
            cache[a["wikidata"]] = voce
            fatti += 1
        except Exception as e:
            errori += 1
            print(f"  {a['nome']}: {e}", file=sys.stderr)
            if errori >= 8 and fatti < errori:
                print("  la Library of Congress non risponde come previsto: mi fermo, i dati già presi restano.", file=sys.stderr)
                break
        if fatti % 10 == 9:
            CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    n = 0
    for f, p in pacchetti:
        cambiato = False
        for a in p["autori"]:
            voce = cache.get(a["wikidata"])
            if voce and voce.get("metodo"):
                a.setdefault("traduzioni", {})["loc_en"] = {k: v for k, v in voce.items() if k not in ("ts", "v")}
                n += 1; cambiato = True
        if cambiato:
            f.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
    for q, (nome, minimo) in CONTROLLI.items():
        v = cache.get(q)
        if v and v["edizioni"] < minimo:
            print(f"::warning::LC: controllo fallito, {nome} ha {v['edizioni']} edizioni (attese almeno {minimo})", file=sys.stderr)
    print(f"loc: {n} autori con dati ({fatti} nuovi, {errori} errori)", file=sys.stderr)


if __name__ == "__main__":
    elabora(dt.date.today())
