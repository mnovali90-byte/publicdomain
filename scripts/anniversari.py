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


def mese_solo(x):
    """Mese della data se Wikidata la dà solo con mese e anno (precisione 10)."""
    if int(g(x, "pr")) == 10:
        return int(g(x, "d")[5:7])
    return None


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
                               "anno": anno_ev, "anni": eta, "pagine": int(g(x, "sl")), "giorni": set(), "mesi": set(), "bad": False})
        v["giorni"].add(giorno(x))
        if mese_solo(x):
            v["mesi"].add(mese_solo(x))
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
        if not mg and not gs and len(v["mesi"]) == 1:   # solo mese e anno
            v["mese"] = next(iter(v["mesi"]))
        del v["giorni"], v["mesi"], v["bad"]
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


def data_da_infobox(testo, anno, campi="released|release_date|published|pub_date|publication_date|first_published|date"):
    """Cerca nell'infobox la data di pubblicazione con giorno. Restituisce (mese, giorno) o None.
    Se l'infobox indica più date diverse nell'anno atteso, non si decide (None)."""
    trovate = set()
    for riga in re.findall(r"\|\s*(?:" + campi + r")\s*=([^\n]*(?:\n(?!\s*\|)[^\n]*)*)", testo, re.I):
        for m in re.finditer(r"\{\{\s*(?:start|release|publication)[ _]date[^|}]*\|(?:df=\w+\|)?(\d{4})\|(\d{1,2})\|(\d{1,2})", riga, re.I):
            if int(m[1]) == anno:
                trovate.add((int(m[2]), int(m[3])))
        for m in re.finditer(r"\{\{\s*(?:birth|death)[ _-]date(?:[ _]and[ _]age)?\s*\|(?:[a-z]+=\w+\|)*(\d{4})\|(\d{1,2})\|(\d{1,2})", riga, re.I):
            if int(m[1]) == anno:
                trovate.add((int(m[2]), int(m[3])))
        for m in re.finditer(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", riga):
            if int(m[3]) == anno and m[2].lower() in MESI_EN:
                trovate.add((MESI_EN[m[2].lower()], int(m[1])))
        for m in re.finditer(r"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", riga):
            if int(m[3]) == anno and m[1].lower() in MESI_EN:
                trovate.add((MESI_EN[m[1].lower()], int(m[2])))
    return next(iter(trovate)) if len(trovate) == 1 else None


def mese_da_infobox(testo, anno, campi="released|release_date|published|pub_date|publication_date|first_published|date"):
    """Mese di pubblicazione dall'infobox («Month YYYY»), se uno solo."""
    trovati = set()
    for riga in re.findall(r"\|\s*(?:" + campi + r")\s*=([^\n]*(?:\n(?!\s*\|)[^\n]*)*)", testo, re.I):
        for m in re.finditer(r"\b([A-Za-z]+)\s+(\d{4})\b", riga):
            if int(m[2]) == anno and m[1].lower() in MESI_EN:
                trovati.add(MESI_EN[m[1].lower()])
        for m in re.finditer(r"\{\{\s*(?:start|release|publication)[ _]date[^|}]*\|(?:df=\w+\|)?(\d{4})\|(\d{1,2})(?:\||\}\})", riga, re.I):
            if int(m[1]) == anno:
                trovati.add(int(m[2]))
    return next(iter(trovati)) if len(trovati) == 1 else None


def controlla_date_opere(voci):
    """Controllo incrociato Wikidata - Wikipedia (infobox inglese) per le date delle prime edizioni."""
    opere = list(voci)   # opere e persone
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
        campi = {"nascita": "birth_date", "morte": "death_date"}.get(v["tipo"])
        d = (data_da_infobox(testo[:15000], v["anno"], campi) if campi else data_da_infobox(testo[:12000], v["anno"])) if testo else None
        wd = (v["mese"], v["giorno"]) if v.get("mese") and v.get("giorno") else None
        v["fonte_data"] = "wikidata" if wd else None
        if d and wd and d == wd:
            v["fonte_data"] = "wikidata+wikipedia"; conta["conferma"] += 1
        elif d and not wd and d != (1, 1) and (not v.get("mese") or v["mese"] == d[0]):
            v["mese"], v["giorno"] = d; v["fonte_data"] = "wikipedia"; conta["aggiunta"] += 1
        elif not wd and not d and not v.get("mese") and testo and v["tipo"] == "prima edizione":
            mm = mese_da_infobox(testo[:12000], v["anno"])
            if mm and mm != 1:
                v["mese"] = mm; v["fonte_data"] = "wikipedia (mese)"; conta["mese"] = conta.get("mese", 0) + 1
        elif d and wd and d != wd:
            v["mese"] = v["giorno"] = None; v["fonte_data"] = "discordante"; conta["discordante"] += 1
            print("  data discordante:", v["nome"], wd, d, file=sys.stderr)
    print("controllo date (opere e persone):", conta, file=sys.stderr)


MESI_L = {
    "en": MESI_EN,
    "it": {m: i + 1 for i, m in enumerate(["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"])},
    "fr": {m: i + 1 for i, m in enumerate(["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"])},
    "de": {m: i + 1 for i, m in enumerate(["januar", "februar", "märz", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "dezember"])},
    "es": {m: i + 1 for i, m in enumerate(["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"])},
}
VERBI = re.compile(r"published|publication|released|appeared|issued|pubblicat|uscì|uscito|edito|prima edizione|publié|paru|parution|parut|para[îi]t|sort[ie]|erschien|erschienen|veröffentlicht|publicad|apareci", re.I)


def date_da_testo(testo, anno, lg):
    """Date (mese, giorno) o solo mese trovate in frasi che parlano di pubblicazione, nell'anno atteso."""
    mesi = MESI_L[lg]
    nome = "|".join(sorted(mesi, key=len, reverse=True))
    t = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", testo)
    t = re.sub(r"<ref[^>]*>.*?</ref>|<ref[^>/]*/>|\{\{[^{}]*\}\}|<!--.*?-->", " ", t, flags=re.S)
    giorni, soli = set(), set()
    for frase in re.split(r"(?<=[^\d][.!?])\s+|\n", t):
        if not VERBI.search(frase) or str(anno) not in frase:
            continue
        for m in re.finditer(rf"\b(\d{{1,2}})(?:º|°|er|\.)?\s+(?:de\s+)?({nome})\s+(?:de\s+)?{anno}\b", frase, re.I):
            giorni.add((mesi[m[2].lower()], int(m[1])))
        for m in re.finditer(rf"\b({nome})\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+{anno}\b", frase, re.I):
            giorni.add((mesi[m[1].lower()], int(m[2])))
        for m in re.finditer(rf"\b({nome})\s+(?:de\s+)?{anno}\b", frase, re.I):
            soli.add(mesi[m[1].lower()])
    return giorni, soli


def cerca_date_testo(voci):
    """Per le opere senza giorno: cerca nelle frasi di Wikipedia (en, it, fr, de, es) la data di pubblicazione."""
    da = [v for v in voci if v["tipo"] == "prima edizione" and not v.get("giorno")]
    titoli = {}
    for i in range(0, len(da), 50):
        gruppo = da[i:i + 50]
        r = json_url("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
            "action": "wbgetentities", "ids": "|".join(v["qid"] for v in gruppo), "props": "sitelinks",
            "sitefilter": "|".join(l + "wiki" for l in MESI_L), "format": "json"}))
        for k, e in ((r or {}).get("entities") or {}).items():
            titoli[k] = {l: s["title"] for l in MESI_L for s in [(e.get("sitelinks") or {}).get(l + "wiki")] if s}
    esiti = {}
    for lg in MESI_L:
        lista = [(k, t[lg]) for k, t in titoli.items() if lg in t]
        for i in range(0, len(lista), 20):
            gruppo = lista[i:i + 20]
            r = json_url(f"https://{lg}.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
                "action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main", "redirects": 1,
                "titles": "|".join(t for _, t in gruppo), "format": "json", "formatversion": 2}))
            if not r:
                continue
            pt = {p["title"]: (p.get("revisions") or [{}])[0].get("slots", {}).get("main", {}).get("content", "") for p in r.get("query", {}).get("pages", [])}
            for red in r.get("query", {}).get("redirects", []) or []:
                pt[red["from"]] = pt.get(red["to"], "")
            for k, t in gruppo:
                esiti.setdefault(k, {})[lg] = date_da_testo(pt.get(t, "")[:20000], next(v["anno"] for v in da if v["qid"] == k), lg)
            time.sleep(1)
    n = 0
    for v in da:
        e = esiti.get(v["qid"], {})
        giorni = set().union(*[x[0] for x in e.values()]) if e else set()
        soli = set().union(*[x[1] for x in e.values()]) if e else set()
        giorni.discard((1, 1))
        if len(giorni) == 1 and (not v.get("mese") or v["mese"] == next(iter(giorni))[0]):
            v["mese"], v["giorno"] = next(iter(giorni)); v["fonte_data"] = "wikipedia (testo: " + ",".join(l for l, x in e.items() if x[0]) + ")"; n += 1
        elif not v.get("mese") and not giorni and len(soli) == 1 and next(iter(soli)) != 1:
            v["mese"] = next(iter(soli)); v["fonte_data"] = "wikipedia (mese, testo)"; n += 1
        elif len(giorni) > 1:
            print("  date multiple nel testo:", v["nome"], sorted(giorni), file=sys.stderr)
    print("date dal testo di Wikipedia:", n, "su", len(da), file=sys.stderr)


def schede_voci(voci):
    """Informazioni per le schede (italiano e inglese): descrizione breve, paese, anni di vita, opere
    principali, Nobel per la letteratura, genere e lingua originale delle opere, link a Wikipedia."""
    persone = [v["qid"] for v in voci if v["tipo"] != "prima edizione"]
    opere = [v["qid"] for v in voci if v["tipo"] == "prima edizione"]
    out = {}

    def lista(x, k):
        return [t for t in (g(x, k) or "").split("|") if t]

    for lang in ("it", "en"):
        sito = "https://%s.wikipedia.org/" % lang
        for i in range(0, len(persone), 40):
            gruppo = " ".join("wd:" + q for q in persone[i:i + 40])
            r = sparql(f'''SELECT ?p (SAMPLE(?di) AS ?desc) (GROUP_CONCAT(DISTINCT ?paese; separator="|") AS ?paesi)
 (GROUP_CONCAT(DISTINCT ?opera; separator="|") AS ?opere) (MIN(YEAR(?bd)) AS ?nato) (MIN(YEAR(?dd)) AS ?morto)
 (MIN(?ny) AS ?nobel) (SAMPLE(?w) AS ?wiki) WHERE {{ VALUES ?p {{ {gruppo} }}
 OPTIONAL {{ ?p schema:description ?di FILTER(LANG(?di)="{lang}") }}
 OPTIONAL {{ ?p wdt:P27 ?c. ?c rdfs:label ?paese FILTER(LANG(?paese)="{lang}") }}
 OPTIONAL {{ ?p wdt:P800 ?o. OPTIONAL {{ ?o rdfs:label ?ol FILTER(LANG(?ol)="{lang}") }} OPTIONAL {{ ?o rdfs:label ?oe FILTER(LANG(?oe)="en") }} BIND(COALESCE(?ol, ?oe) AS ?opera) }}
 OPTIONAL {{ ?p wdt:P569 ?bd }} OPTIONAL {{ ?p wdt:P570 ?dd }}
 OPTIONAL {{ ?p p:P166 ?st. ?st ps:P166 wd:Q37922. OPTIONAL {{ ?st pq:P585 ?nd. BIND(YEAR(?nd) AS ?ny) }} }}
 OPTIONAL {{ ?w schema:about ?p; schema:isPartOf <{sito}> }}
 }} GROUP BY ?p''') or []
            for x in r:
                d = out.setdefault(qid(g(x, "p")), {}).setdefault(lang, {})
                d.update({"desc": g(x, "desc"), "paesi": lista(x, "paesi")[:2], "opere": lista(x, "opere")[:3],
                          "nato": int(g(x, "nato")) if g(x, "nato") else None, "morto": int(g(x, "morto")) if g(x, "morto") else None,
                          "nobel": int(g(x, "nobel")) if g(x, "nobel") else None, "wiki": g(x, "wiki")})
            time.sleep(1)
        for i in range(0, len(opere), 40):
            gruppo = " ".join("wd:" + q for q in opere[i:i + 40])
            r = sparql(f'''SELECT ?p (SAMPLE(?di) AS ?desc) (GROUP_CONCAT(DISTINCT ?gen; separator="|") AS ?generi)
 (SAMPLE(?lin) AS ?lingua) (SAMPLE(?tit) AS ?titolo) (SAMPLE(?w) AS ?wiki) WHERE {{ VALUES ?p {{ {gruppo} }}
 OPTIONAL {{ ?p schema:description ?di FILTER(LANG(?di)="{lang}") }}
 OPTIONAL {{ ?p wdt:P136 ?g. ?g rdfs:label ?gen FILTER(LANG(?gen)="{lang}") }}
 OPTIONAL {{ ?p wdt:P407 ?l. ?l rdfs:label ?lin FILTER(LANG(?lin)="{lang}") }}
 OPTIONAL {{ ?p wdt:P1476 ?tit }}
 OPTIONAL {{ ?w schema:about ?p; schema:isPartOf <{sito}> }}
 }} GROUP BY ?p''') or []
            for x in r:
                d = out.setdefault(qid(g(x, "p")), {}).setdefault(lang, {})
                d.update({"desc": g(x, "desc"), "generi": lista(x, "generi")[:2], "lingua": g(x, "lingua"),
                          "titolo_orig": g(x, "titolo"), "wiki": g(x, "wiki")})
            time.sleep(1)
    return out


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
        cerca_date_testo(uniche)
    except Exception as e:
        print('Controllo date non riuscito:', e, file=sys.stderr)
    try:
        sch = schede_voci(uniche)
    except Exception as e:
        print("Schede non riuscite:", e, file=sys.stderr)
        sch = {}
    vecchio_sch = {(v["tipo"], v["qid"]): v.get("scheda") for v in vecchio["voci"]}
    for v in uniche:
        v["scheda"] = sch.get(v["qid"]) or vecchio_sch.get((v["tipo"], v["qid"]))
        v.pop("sbn", None)
    corr = DATA / "anniversari_correzioni.json"
    if corr.exists():
        for k, c in json.loads(corr.read_text(encoding="utf-8")).get("voci", {}).items():
            for v in uniche:
                if f'{v["tipo"]}:{v["qid"]}' == k:
                    v["mese"], v["giorno"], v["fonte_data"] = c["mese"], c["giorno"], "verifica: " + c["fonte"]
    uniche.sort(key=lambda v: ((v["mese"] or 13), (v["giorno"] or 99), -v["pagine"]))
    out = {"anno": ANNO, "generato": dt.date.today().isoformat(), "fonti": ["Wikidata", "Wikipedia"], "voci": uniche}
    file.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(uniche)} voci; escluse per altre occupazioni: {len(esclusi)}")


if __name__ == "__main__":
    main()
