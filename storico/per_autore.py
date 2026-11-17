"""Seconda strada per lo Storico: partire dagli AUTORI invece che dai tipi di opera e dalle date.

Perché: cercando solo opere di certi tipi con un anno di pubblicazione restavano fuori i titoli più importanti.
Prove del 17/11/2026:
  - Amleto su Wikidata è una "tragedia di Shakespeare", tipo che non era nella lista;
  - Iliade ha solo la data di composizione (800 a.C.), non quella di pubblicazione;
  - Orwell (morto nel 1950, 1984 libero in Europa dal 2021) mancava del tutto, perché ha esordito nel 1933.
  Con i 7.341 autori di allora la ricerca per autore portava le opere libere da 19.827 a 94.077.

Come funziona:
1. SEMI (data/storico/semi.json, rifatti ogni 90 giorni): tutti gli scrittori (scrittore, poeta, drammaturgo,
   romanziere, saggista...) morti entro l'anno in cui scade la regola europea (oggi: morti entro il 1955),
   un anno di morte per volta; più gli autori delle opere letterarie più note (almeno 20 Wikipedia),
   che porta dentro chi non ha data di morte (Omero) e verrà filtrato dopo; più gli autori già trovati per data.
2. OPERE: per blocchi di autori, tutte le loro opere scritte (tipo che discende da "opera letteraria" o
   "opera scritta") con almeno una pagina Wikipedia. Anno = il più antico tra pubblicazione e composizione.
   Ogni blocco si salva subito in data/storico/blocchi/ (rifatto dopo 90 giorni): se il tempo finisce, si riparte.
3. LIBERA IN ALMENO UN PAESE, altrimenti fuori:
   - USA: anno dell'opera fino al 1930 (95 anni compiuti);
   - Europa: tutti gli autori morti entro il 1955 (70 anni dopo la morte);
   - autori senza data di morte ma nati, o attivi, prima del 1800 (antichi).
   Il verdetto per ogni paese lo calcola la pagina da anno e morti, così resta giusto anche l'anno dopo.
"""
import json, os, re, sys, time, urllib.parse
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from opere import get, val, qid  # noqa: E402

CARTELLA = "data/storico"
OCCUPAZIONI = "wd:Q36180 wd:Q49757 wd:Q214917 wd:Q6625963 wd:Q4853732 wd:Q482980 wd:Q1930187 wd:Q11774202 wd:Q18844224"
RADICI = "wd:Q7725634 wd:Q47461344"          # opera letteraria, opera scritta
ANNO_USA = date.today().year - 96             # 2026 -> 1930
ANNO_UE = date.today().year - 71              # 2026 -> 1955 (morti entro quest'anno: liberi)
ANTICHI = 1800
RINFRESCA_SEMI, RINFRESCA_BLOCCHI = 90, 90


def sparql_o_errore(q, timeout=120):
    """Come sparql(), ma None se Wikidata non ha risposto (per non scambiare un errore per «nessun risultato»)."""
    d = get("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"}), timeout=timeout)
    return None if d is None else d["results"]["bindings"]


def _anno(v):
    m = re.match(r"(-?\d+)", v or "")
    return int(m.group(1)) if m else None


def fasce_morte():
    f = [(1000, 1299), (1300, 1399), (1400, 1449), (1450, 1499)]
    f += [(y, y + 24) for y in range(1500, 1800, 25)]
    f += [(y, y) for y in range(1800, ANNO_UE + 1)]
    return f


def scrittori_morti(da, a):
    q = f"""SELECT ?a WHERE {{
      ?a wdt:P570 ?m. hint:Prior hint:rangeSafe true .
      FILTER(?m >= "{da:04d}-01-01T00:00:00Z"^^xsd:dateTime && ?m < "{a + 1:04d}-01-01T00:00:00Z"^^xsd:dateTime)
      ?a wdt:P31 wd:Q5; wdt:P106 ?o; wikibase:sitelinks ?sl. VALUES ?o {{ {OCCUPAZIONI} }} FILTER(?sl >= 3) }}"""
    r = sparql_o_errore(q)
    return None if r is None else {qid(val(x, "a")) for x in r}


def autori_opere_famose():
    q = f"""SELECT DISTINCT ?a WHERE {{ ?w wikibase:sitelinks ?sl. FILTER(?sl >= 20)
      ?w wdt:P31/wdt:P279* wd:Q7725634. ?w wdt:P50 ?a. }}"""   # niente «?a è un essere umano»: Omero su Wikidata non lo è
    r = sparql_o_errore(q, timeout=180)
    return None if r is None else {qid(val(x, "a")) for x in r}


def semi(da_date, budget_fine):
    """Insieme dei QID degli autori da interrogare. Tiene quanto già scaricato e completa le fasce mancanti."""
    f = f"{CARTELLA}/semi.json"
    try:
        s = json.load(open(f, encoding="utf8"))
    except Exception:
        s = {"fasce": {}, "famose": None}
    if s.get("v") != 2:          # 2: gli autori delle opere famose non devono più essere «esseri umani» (Omero)
        s["famose"], s["v"] = None, 2
    oggi = date.today()
    for da, a in fasce_morte():
        k = f"{da}-{a}"
        v = s["fasce"].get(k)
        if v and (oggi - date.fromisoformat(v["scaricato"])).days < RINFRESCA_SEMI:
            continue
        if time.time() > budget_fine:
            break
        r = scrittori_morti(da, a)
        if r is not None:
            s["fasce"][k] = {"scaricato": oggi.isoformat(), "autori": sorted(r)}
        time.sleep(1)
    if not s.get("famose") or (oggi - date.fromisoformat(s["famose"]["scaricato"])).days >= RINFRESCA_SEMI:
        r = autori_opere_famose()
        if r is not None:
            s["famose"] = {"scaricato": oggi.isoformat(), "autori": sorted(r)}
    json.dump(s, open(f, "w", encoding="utf8"), separators=(",", ":"))
    tutti = set(da_date)
    for v in s["fasce"].values():
        tutti |= set(v["autori"])
    if s.get("famose"):
        tutti |= set(s["famose"]["autori"])
    mancanti = [k for k in (f"{da}-{a}" for da, a in fasce_morte()) if k not in s["fasce"]]
    tutti = {a for a in tutti if a and re.fullmatch(r"Q\d+", a)}   # niente autori «anonimi» senza codice
    return sorted(tutti), mancanti


def opere_di(autori):
    v = " ".join("wd:" + a for a in autori)
    q = f"""SELECT ?w ?wLabel ?wit ?sl ?en ?itw (MIN(?p) AS ?pub) (MIN(?c) AS ?cre) ?a ?aLabel ?morte ?nascita ?fl ?attivo WHERE {{
      VALUES ?a0 {{ {v} }} ?w wdt:P50 ?a0. ?w wikibase:sitelinks ?sl. FILTER(?sl >= 1)
      ?w wdt:P31/wdt:P279* ?r. VALUES ?r {{ {RADICI} }}
      ?w wdt:P50 ?a.
      OPTIONAL {{ ?a wdt:P570 ?morte }} OPTIONAL {{ ?a wdt:P569 ?nascita }} OPTIONAL {{ ?a wdt:P1317 ?fl }} OPTIONAL {{ ?a wdt:P2031 ?attivo }}
      OPTIONAL {{ ?w wdt:P577 ?p }} OPTIONAL {{ ?w wdt:P571 ?c }}
      OPTIONAL {{ ?w rdfs:label ?wit FILTER(LANG(?wit) = "it") }}
      OPTIONAL {{ ?en schema:about ?w; schema:isPartOf <https://en.wikipedia.org/> }}
      OPTIONAL {{ ?itw schema:about ?w; schema:isPartOf <https://it.wikipedia.org/> }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,it,mul". }}
    }} GROUP BY ?w ?wLabel ?wit ?sl ?en ?itw ?a ?aLabel ?morte ?nascita ?fl ?attivo"""
    r = sparql_o_errore(q)
    if r is None:
        return None
    out = {}
    for x in r:
        k = qid(val(x, "w"))
        o = out.setdefault(k, {"qid": k, "titolo": val(x, "wLabel"), "titolo_it": val(x, "wit"), "anno": None, "pub": None,
                               "cre": None, "autori": {}, "pagine": int(val(x, "sl")), "wiki_en": val(x, "en"), "wiki_it": val(x, "itw")})
        for campo in ("pub", "cre"):
            y = _anno(val(x, campo))
            if y is not None and (o[campo] is None or y < o[campo]):
                o[campo] = y
        # l'anno che si mostra e che conta per gli USA è quello di pubblicazione; senza, quello di composizione
        # (Orgoglio e pregiudizio: scritto nel 1796-97, pubblicato nel 1813)
        o["anno"] = o["pub"] if o["pub"] is not None else o["cre"]
        ak = qid(val(x, "a"))
        au = o["autori"].setdefault(ak, {"qid": ak, "nome": val(x, "aLabel"), "morte": None, "antico": False})
        m = _anno(val(x, "morte"))
        if m is not None and (au["morte"] is None or m > au["morte"]):
            au["morte"] = m
        for y in (_anno(val(x, "nascita")), _anno(val(x, "fl")), _anno(val(x, "attivo"))):
            if y is not None and y < ANTICHI and m is None:
                au["antico"] = True
    res = []
    for o in out.values():
        if re.fullmatch(r"Q\d+", o["titolo"] or ""):
            continue
        o["autori"] = [a for a in o["autori"].values() if not re.fullmatch(r"Q\d+", a["nome"] or "")]
        res.append(o)
    return res


def libera_ue(o):
    """Europa (70 anni dalla morte): tutti gli autori morti entro il 1955, o antichi; oppure opera uscita
    più di 100 anni prima di quella data (chi pubblicava nel 1855 è per forza morto entro il 1955)."""
    if o.get("anno") is not None and o["anno"] <= ANNO_UE - 100:
        return True
    au = o.get("autori") or []
    return bool(au) and all((a.get("morte") is not None and a["morte"] <= ANNO_UE) or a.get("antico") for a in au)


def libera_usa(o):
    """USA (95 anni dalla pubblicazione): uscita entro il 1930. Senza anno: solo se tutti gli autori sono
    antichi o morti più di 100 anni prima del 1955 (l'opera è per forza molto vecchia)."""
    if o.get("anno") is not None:
        return o["anno"] <= ANNO_USA
    au = o.get("autori") or []
    return bool(au) and all(a.get("antico") or (a.get("morte") is not None and a["morte"] <= ANNO_UE - 100) for a in au)


def libera(o):
    """Libera in almeno un paese: altrimenti fuori dallo Storico."""
    return libera_ue(o) or libera_usa(o)


def opere_anonime():
    """Opere famose senza autore su Wikidata (Beowulf, Le mille e una notte...): entrano se hanno una data entro il 1930."""
    q = f"""SELECT ?w ?wLabel ?wit ?sl ?en ?itw (MIN(?p) AS ?pub) (MIN(?c) AS ?cre) WHERE {{
      ?w wikibase:sitelinks ?sl. FILTER(?sl >= 10)
      ?w wdt:P31/wdt:P279* wd:Q7725634. FILTER NOT EXISTS {{ ?w wdt:P50 ?x }}
      OPTIONAL {{ ?w wdt:P577 ?p }} OPTIONAL {{ ?w wdt:P571 ?c }}
      OPTIONAL {{ ?w rdfs:label ?wit FILTER(LANG(?wit) = "it") }}
      OPTIONAL {{ ?en schema:about ?w; schema:isPartOf <https://en.wikipedia.org/> }}
      OPTIONAL {{ ?itw schema:about ?w; schema:isPartOf <https://it.wikipedia.org/> }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,it,mul". }}
    }} GROUP BY ?w ?wLabel ?wit ?sl ?en ?itw"""
    r = sparql_o_errore(q, timeout=180)
    if r is None:
        return None
    out = []
    for x in r:
        pub, cre = _anno(val(x, "pub")), _anno(val(x, "cre"))
        anno = pub if pub is not None else cre
        if anno is None or anno > ANNO_USA or re.fullmatch(r"Q\d+", val(x, "wLabel") or ""):
            continue
        out.append({"qid": qid(val(x, "w")), "titolo": val(x, "wLabel"), "titolo_it": val(x, "wit"), "anno": anno, "pub": pub,
                    "cre": cre, "autori": [], "pagine": int(val(x, "sl")), "wiki_en": val(x, "en"), "wiki_it": val(x, "itw")})
    return out


VERSIONE = 2     # 2: anno di pubblicazione e di composizione separati, tutte le opere salvate (17/11/2026)
CASSETTI = 700   # gli autori vanno sempre nello stesso cassetto (numero del QID modulo 700): se se ne aggiunge uno,
                 # si riscarica solo il suo cassetto, non tutto


def opere_per_autore(semi_qid, budget_fine):
    """Opere di tutti gli autori-seme, a cassetti salvati su disco. Restituisce (opere, cassetti mancanti)."""
    cartella = f"{CARTELLA}/blocchi"
    os.makedirs(cartella, exist_ok=True)
    oggi = date.today()
    cassetti = {}
    for a in semi_qid:
        cassetti.setdefault(int(a[1:]) % CASSETTI, []).append(a)
    tutte, mancanti = {}, 0
    for n in sorted(cassetti):
        gruppo = sorted(cassetti[n])
        f = f"{cartella}/c{n:03d}.json"
        vecchio = None
        try:
            vecchio = json.load(open(f, encoding="utf8"))
        except Exception:
            pass
        fresco = (vecchio and vecchio.get("v") == VERSIONE and vecchio.get("autori") == gruppo
                  and (oggi - date.fromisoformat(vecchio["scaricato"])).days < RINFRESCA_BLOCCHI)
        if not fresco and time.time() < budget_fine:
            r = opere_di(gruppo)
            if r is None:                       # cassetto troppo pesante (autori con migliaia di opere): a pezzi
                r = []
                for j in range(0, len(gruppo), 8):
                    p = opere_di(gruppo[j:j + 8])
                    if p is None:
                        r = None; break
                    r += p
            if r is not None:
                vecchio = {"v": VERSIONE, "scaricato": oggi.isoformat(), "autori": gruppo, "opere": r}   # tutte: le regole si applicano dopo
                json.dump(vecchio, open(f, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
            time.sleep(0.5)
        if vecchio:                             # anche se vecchio o con autori diversi: meglio che niente
            for o in vecchio["opere"]:
                if libera(o):
                    tutte[o["qid"]] = o
        if not fresco and not (vecchio and vecchio.get("scaricato") == oggi.isoformat()):
            mancanti += 1
    return list(tutte.values()), mancanti
