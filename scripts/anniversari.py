#!/usr/bin/env python3
"""
Calendario degli anniversari letterari (nascite, morti, prime edizioni).

Fonti aperte: Wikidata (persone e opere con date), catalogo SBN (edizioni italiane dell'autore).
Per l'anno ANNO prende gli anniversari tondi: 50, 75, 100, 125, 150, 175, 200, 250, 300, 400 anni.

Regole di qualità:
  - solo persone con occupazioni letterarie o di pensiero (romanziere, poeta, drammaturgo, scrittore per
    ragazzi, novellista, saggista, filosofo, psicologo, psicoanalista, storico);
  - chi ha anche occupazioni non letterarie (attore, politico, sportivo, scienziato…) resta solo se ha scritto
    almeno un'opera con una sua pagina Wikipedia;
  - se Wikidata ha per la stessa data valori in contrasto (due anni diversi) la voce si scarta;
  - se per lo stesso evento ci sono giorni diversi, il giorno si considera non noto;
  - le date nel calendario giuliano (Russia ecc.) si convertono nel calendario gregoriano;
  - data/anniversari_esclusioni.json: elenco (a mano) di voci da non mostrare.

Scrive data/anniversari-<anno>.json. Se una ricerca non va a buon fine, per quel gruppo restano i dati
del giro precedente (il file è la cache).
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

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
ANNO = int(os.environ.get("ANNO_CALENDARIO", "2027"))
ETA = [50, 75, 100, 125, 150, 175, 200, 225, 250, 300, 400, 500]
SOGLIA_PERSONE, SOGLIA_OPERE = 30, 15
BUDGET_MIN = float(os.environ.get("BUDGET_MINUTI_ANNIV", "70"))
FINE = time.time() + BUDGET_MIN * 60
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
URL = "https://query.wikidata.org/sparql"

# romanziere, poeta, drammaturgo, scrittore per ragazzi, novellista, saggista, filosofo, psicologo, psicoanalista, storico
OCC = "wd:Q6625963 wd:Q49757 wd:Q214917 wd:Q4853732 wd:Q15949613 wd:Q11774202 wd:Q4964182 wd:Q212980 wd:Q211423 wd:Q201788"
# attore, regista, politico, musicista, compositore, scienziato, fisico, matematico, pittore, calciatore…
NON_LETT = ("wd:Q33999 wd:Q2526255 wd:Q82955 wd:Q639669 wd:Q36834 wd:Q901 wd:Q169470 wd:Q170790 wd:Q1028181 "
            "wd:Q10833314 wd:Q1234713 wd:Q16533 wd:Q11513337 wd:Q483501 wd:Q2259451 wd:Q937857 wd:Q11513337")
# romanzo, racconto, teatro, poesia, opera letteraria, raccolta di racconti, libro, saggio, opuscolo
CLASSI = ["Q8261", "Q49084", "Q25379", "Q5185279", "Q7725634", "Q1279564", "Q571", "Q35760", "Q149537"]
RIFERIMENTO = "wd:Q1580166 wd:Q23622 wd:Q1347367 wd:Q4006"  # enciclopedie, dizionari…
GIULIANO = "http://www.wikidata.org/entity/Q1985786"


def sparql(q):
    for t in range(3):
        try:
            r = urllib.request.Request(URL + "?" + urllib.parse.urlencode({"query": q, "format": "json"}), headers=UA)
            with urllib.request.urlopen(r, timeout=75) as f:
                return json.load(f)["results"]["bindings"]
        except Exception as e:
            print("  errore:", str(e)[:90], file=sys.stderr)
            time.sleep(8 * (t + 1))
    return None


def g(x, k):
    return x.get(k, {}).get("value")


def qid(u):
    return u.rsplit("/", 1)[-1]


def giuliano_a_gregoriano(y, m, d):
    """Converte una data del calendario giuliano in gregoriano (via numero giuliano del giorno)."""
    a = (14 - m) // 12
    yy, mm = y + 4800 - a, m + 12 * a - 3
    jdn = d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - 32083
    return dt.date.fromordinal(jdn - 1721425)  # JDN -> ordinale gregoriano


def estremi(y):
    return f'"{y:04d}-01-01T00:00:00Z"^^xsd:dateTime', f'"{y + 1:04d}-01-01T00:00:00Z"^^xsd:dateTime'


def q_persone(prop, y):
    a, b = estremi(y)
    return sparql(f'''SELECT ?p ?pLabel ?pit ?desc ?d ?pr ?cal ?sl ?bad WHERE {{ VALUES ?o {{ {OCC} }}
 ?p wdt:P106 ?o; wdt:P31 wd:Q5; p:{prop}/psv:{prop} [wikibase:timeValue ?d; wikibase:timePrecision ?pr; wikibase:timeCalendarModel ?cal].
 FILTER(?d>={a} && ?d<{b}) ?p wikibase:sitelinks ?sl. FILTER(?sl>={SOGLIA_PERSONE})
 FILTER NOT EXISTS {{ ?p wdt:{prop} ?altra. FILTER(?altra<{a} || ?altra>={b}) }}
 OPTIONAL {{ ?p wdt:P106 ?bad. VALUES ?bad {{ {NON_LETT} }} FILTER NOT EXISTS {{ ?lib wdt:P50 ?p; wikibase:sitelinks ?s2. FILTER(?s2>=10) }} }}
 OPTIONAL {{ ?p rdfs:label ?pit FILTER(LANG(?pit)="it") }} OPTIONAL {{ ?p schema:description ?desc FILTER(LANG(?desc)="en") }}
 SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}''')


def q_opere(y):
    a, b = estremi(y)
    tutte = []
    for c in CLASSI:
        r = sparql(f'''SELECT ?p ?pLabel ?pit ?desc ?au ?auth ?d ?pr ?cal ?sl WHERE {{ ?p wdt:P31 wd:{c}; wikibase:sitelinks ?sl. FILTER(?sl>={SOGLIA_OPERE})
 ?p p:P577/psv:P577 [wikibase:timeValue ?d; wikibase:timePrecision ?pr; wikibase:timeCalendarModel ?cal]. FILTER(?d>={a} && ?d<{b})
 FILTER NOT EXISTS {{ VALUES ?rif {{ {RIFERIMENTO} }} ?p wdt:P31 ?rif }}
 OPTIONAL {{ ?p wdt:P50 ?au. ?au rdfs:label ?auth FILTER(LANG(?auth)="en") }}
 OPTIONAL {{ ?p rdfs:label ?pit FILTER(LANG(?pit)="it") }} OPTIONAL {{ ?p schema:description ?desc FILTER(LANG(?desc)="en") }}
 SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}''')
        if r is None:
            return None
        tutte += r
        time.sleep(1)
    return tutte


def giorno(x):
    """(mese, giorno) in calendario gregoriano, oppure None se la data è solo l'anno."""
    if int(g(x, "pr")) < 11:
        return None
    d = g(x, "d")[:10]
    y, m, dd = int(d[:4]), int(d[5:7]), int(d[8:10])
    if g(x, "cal") == GIULIANO:
        try:
            gg = giuliano_a_gregoriano(y, m, dd)
            return gg.month, gg.day
        except Exception:
            return None
    return m, dd


def raccogli(righe, tipo, eta, anno_ev, voci, esclusi):
    """Raggruppa le righe per (tipo, qid); più giorni diversi -> giorno non noto."""
    per = {}
    for x in righe:
        nome = g(x, "pLabel")
        if not nome or re.fullmatch(r"Q\d+", nome):
            continue
        k = qid(g(x, "p"))
        v = per.setdefault(k, {"tipo": tipo, "qid": k, "nome": nome, "it": g(x, "pit"), "desc": g(x, "desc"),
                               "autore": g(x, "auth"), "autore_qid": qid(g(x, "au")) if g(x, "au") else None,
                               "anno": anno_ev, "anni": eta, "pagine": int(g(x, "sl")), "giorni": set(), "bad": False})
        v["giorni"].add(giorno(x))
        if x.get("bad"):
            v["bad"] = True
    for k, v in per.items():
        if v["bad"]:
            esclusi.append(v["nome"])
            continue
        gs = {x for x in v["giorni"] if x}          # i valori «solo anno» non contano: contano i giorni
        mg = next(iter(gs)) if len(gs) == 1 else None   # più giorni diversi = giorno non noto
        if tipo == "prima edizione" and mg == (1, 1):    # 1 gennaio nei dati delle opere è quasi sempre un segnaposto
            mg = None
        v["mese"], v["giorno"] = mg if mg else (None, None)
        del v["giorni"], v["bad"]
        voci.append(v)


def carica_esclusioni():
    f = DATA / "anniversari_esclusioni.json"
    if not f.exists():
        return set(), set()
    d = json.loads(f.read_text(encoding="utf-8"))
    return set(d.get("qid", {}).keys()), set(d.get("nomi", {}).keys())

MESI_EN = {m: i + 1 for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"])}


def json_url(u):
    for t in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as f:
                return json.load(f)
        except Exception as e:
            print("  errore:", str(e)[:80], file=sys.stderr)
            time.sleep(5 * (t + 1))
    return None


def data_da_infobox(testo, anno):
    """Cerca nell'infobox la data di pubblicazione con giorno. Restituisce (mese, giorno) o None.
    Se l'infobox indica più date diverse nell'anno atteso, non si decide (None)."""
    trovate = set()
    for riga in re.findall(r"\|\s*(?:released|release_date|published|pub_date|publication_date|first_published|date)\s*=([^\n]*(?:\n(?!\s*\|)[^\n]*)*)", testo, re.I):
        for m in re.finditer(r"\{\{\s*(?:start|release|publication)[ _]date[^|}]*\|(?:df=\w+\|)?(\d{4})\|(\d{1,2})\|(\d{1,2})", riga, re.I):
            if int(m[1]) == anno:
                trovate.add((int(m[2]), int(m[3])))
        for m in re.finditer(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", riga):
            if int(m[3]) == anno and m[2].lower() in MESI_EN:
                trovate.add((MESI_EN[m[2].lower()], int(m[1])))
        for m in re.finditer(r"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", riga):
            if int(m[3]) == anno and m[1].lower() in MESI_EN:
                trovate.add((MESI_EN[m[1].lower()], int(m[2])))
    return next(iter(trovate)) if len(trovate) == 1 else None


def controlla_date_opere(voci):
    """Controllo incrociato Wikidata - Wikipedia (infobox inglese) per le date delle prime edizioni."""
    opere = [v for v in voci if v["tipo"] == "prima edizione"]
    titoli = {}
    for i in range(0, len(opere), 50):
        gruppo = opere[i:i + 50]
        r = json_url("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
            "action": "wbgetentities", "ids": "|".join(v["qid"] for v in gruppo), "props": "sitelinks", "sitefilter": "enwiki", "format": "json"}))
        for k, e in ((r or {}).get("entities") or {}).items():
            t = (e.get("sitelinks") or {}).get("enwiki", {}).get("title")
            if t:
                titoli[k] = t
    wp = {}
    lista = list(titoli.items())
    for i in range(0, len(lista), 20):
        gruppo = lista[i:i + 20]
        r = json_url("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main", "redirects": 1,
            "titles": "|".join(t for _, t in gruppo), "format": "json", "formatversion": 2}))
        if not r:
            continue
        per_titolo = {p["title"]: (p.get("revisions") or [{}])[0].get("slots", {}).get("main", {}).get("content", "") for p in r.get("query", {}).get("pages", [])}
        for red in r.get("query", {}).get("redirects", []) or []:
            per_titolo[red["from"]] = per_titolo.get(red["to"], "")
        for k, t in gruppo:
            wp[k] = per_titolo.get(t, "")
        time.sleep(1)
    conta = {"conferma": 0, "aggiunta": 0, "discordante": 0}
    for v in opere:
        testo = wp.get(v["qid"], "")
        d = data_da_infobox(testo[:12000], v["anno"]) if testo else None
        wd = (v["mese"], v["giorno"]) if v.get("mese") else None
        v["fonte_data"] = "wikidata" if wd else None
        if d and wd and d == wd:
            v["fonte_data"] = "wikidata+wikipedia"; conta["conferma"] += 1
        elif d and not wd and d != (1, 1):
            v["mese"], v["giorno"] = d; v["fonte_data"] = "wikipedia"; conta["aggiunta"] += 1
        elif d and wd and d != wd:
            v["mese"] = v["giorno"] = None; v["fonte_data"] = "discordante"; conta["discordante"] += 1
            print("  data discordante:", v["nome"], wd, d, file=sys.stderr)
    print("controllo date opere:", conta, file=sys.stderr)


def sbn_autori(voci):
    """Edizioni italiane dell'autore (SBN): per le persone, e per l'autore delle opere."""
    import sbn
    cache = {}
    if (DATA / "cache_sbn.json").exists():
        cache = json.loads((DATA / "cache_sbn.json").read_text(encoding="utf-8"))
    risultati = {}
    da_fare = {}
    for v in voci:
        q = v["qid"] if v["tipo"] != "prima edizione" else v.get("autore_qid")
        nome = v["nome"] if v["tipo"] != "prima edizione" else v.get("autore")
        if q and nome:
            da_fare[q] = nome
    viaf = sbn.codici_viaf(list(da_fare)) if da_fare else {}
    errori = 0
    for q, nome in da_fare.items():
        c = cache.get(q)
        if c and c.get("v") == 5 and "edizioni" in c:
            risultati[q] = {k: c[k] for k in ("edizioni", "ultimo", "dal_2000", "trovato")}
            continue
        if time.time() > FINE:
            break
        try:
            r = sbn.edizioni_italiane(nome, viaf.get(q))
            risultati[q] = {k: r[k] for k in ("edizioni", "ultimo", "dal_2000", "trovato")}
        except Exception as e:
            errori += 1
            print("  sbn:", nome, str(e)[:80], file=sys.stderr)
            if errori >= 8:
                break
    return risultati


def main():
    file = DATA / f"anniversari-{ANNO}.json"
    vecchio = json.loads(file.read_text(encoding="utf-8")) if file.exists() else {"voci": []}
    nuovi, esclusi, falliti = [], [], []
    from concurrent.futures import ThreadPoolExecutor
    lavori = [(tipo, eta) for eta in ETA for tipo in ("nascita", "morte", "prima edizione")]

    def esegui(lav):
        tipo, eta = lav
        if time.time() > FINE:
            return lav, None
        y = ANNO - eta
        r = q_persone("P569", y) if tipo == "nascita" else q_persone("P570", y) if tipo == "morte" else q_opere(y)
        time.sleep(1)
        return lav, r

    with ThreadPoolExecutor(max_workers=4) as pool:
        for (tipo, eta), r in pool.map(esegui, lavori):
            if r is None:
                falliti.append((tipo, eta))
            else:
                raccogli(r, tipo, eta, ANNO - eta, nuovi, esclusi)
    for tipo, eta in falliti:  # gruppo non riuscito: restano i dati del giro precedente
        nuovi += [v for v in vecchio["voci"] if v["tipo"] == tipo and v["anni"] == eta]
    print(f"gruppi non riusciti: {falliti}", file=sys.stderr)
    ex_q, ex_nomi = carica_esclusioni()
    voci = [v for v in nuovi if v["qid"] not in ex_q and v["nome"] not in ex_nomi]
    # una persona/opera per tipo e anni
    visti, uniche = set(), []
    for v in sorted(voci, key=lambda v: -v["pagine"]):
        k = (v["tipo"], v["qid"])
        if k not in visti:
            visti.add(k); uniche.append(v)
    try:
        controlla_date_opere(uniche)
    except Exception as e:
        print('Controllo date non riuscito:', e, file=sys.stderr)
    try:
        sbn_dati = sbn_autori(uniche)
    except Exception as e:
        print("SBN non disponibile:", e, file=sys.stderr)
        sbn_dati = {}
    vecchio_sbn = {(v["tipo"], v["qid"]): v.get("sbn") for v in vecchio["voci"]}
    for v in uniche:
        q = v["qid"] if v["tipo"] != "prima edizione" else v.get("autore_qid")
        v["sbn"] = sbn_dati.get(q) or vecchio_sbn.get((v["tipo"], v["qid"]))
    uniche.sort(key=lambda v: ((v["mese"] or 13), (v["giorno"] or 0), -v["pagine"]))
    out = {"anno": ANNO, "generato": dt.date.today().isoformat(), "fonti": ["Wikidata", "SBN"], "voci": uniche}
    file.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(uniche)} voci; escluse per altre occupazioni: {len(esclusi)}")


if __name__ == "__main__":
    main()
