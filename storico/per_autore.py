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
      ?w wdt:P31/wdt:P279* wd:Q7725634. ?w wdt:P50 ?a. ?a wdt:P31 wd:Q5 }}"""
    r = sparql_o_errore(q, timeout=180)
    return None if r is None else {qid(val(x, "a")) for x in r}


def semi(da_date, budget_fine):
    """Insieme dei QID degli autori da interrogare. Tiene quanto già scaricato e completa le fasce mancanti."""
    f = f"{CARTELLA}/semi.json"
    try:
        s = json.load(open(f, encoding="utf8"))
    except Exception:
        s = {"fasce": {}, "famose": None}
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
    return sorted(tutti), mancanti


def opere_di(autori):
    v = " ".join("wd:" + a for a in autori)
    q = f"""SELECT ?w ?wLabel ?wit ?sl ?en ?itw (MIN(?p) AS ?pub) (MIN(?c) AS ?cre) ?a ?aLabel ?morte ?nascita ?fl WHERE {{
      VALUES ?a0 {{ {v} }} ?w wdt:P50 ?a0. ?w wikibase:sitelinks ?sl. FILTER(?sl >= 1)
      ?w wdt:P31/wdt:P279* ?r. VALUES ?r {{ {RADICI} }}
      ?w wdt:P50 ?a.
      OPTIONAL {{ ?a wdt:P570 ?morte }} OPTIONAL {{ ?a wdt:P569 ?nascita }} OPTIONAL {{ ?a wdt:P1317 ?fl }}
      OPTIONAL {{ ?w wdt:P577 ?p }} OPTIONAL {{ ?w wdt:P571 ?c }}
      OPTIONAL {{ ?w rdfs:label ?wit FILTER(LANG(?wit) = "it") }}
      OPTIONAL {{ ?en schema:about ?w; schema:isPartOf <https://en.wikipedia.org/> }}
      OPTIONAL {{ ?itw schema:about ?w; schema:isPartOf <https://it.wikipedia.org/> }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,it,mul". }}
    }} GROUP BY ?w ?wLabel ?wit ?sl ?en ?itw ?a ?aLabel ?morte ?nascita ?fl"""
    r = sparql_o_errore(q)
    if r is None:
        return None
    out = {}
    for x in r:
        k = qid(val(x, "w"))
        o = out.setdefault(k, {"qid": k, "titolo": val(x, "wLabel"), "titolo_it": val(x, "wit"), "anno": None,
                               "autori": {}, "pagine": int(val(x, "sl")), "wiki_en": val(x, "en"), "wiki_it": val(x, "itw")})
        for y in (_anno(val(x, "pub")), _anno(val(x, "cre"))):
            if y is not None and (o["anno"] is None or y < o["anno"]):
                o["anno"] = y
        ak = qid(val(x, "a"))
        au = o["autori"].setdefault(ak, {"qid": ak, "nome": val(x, "aLabel"), "morte": None, "antico": False})
        m = _anno(val(x, "morte"))
        if m is not None and (au["morte"] is None or m > au["morte"]):
            au["morte"] = m
        for y in (_anno(val(x, "nascita")), _anno(val(x, "fl"))):
            if y is not None and y < ANTICHI and m is None:
                au["antico"] = True
    res = []
    for o in out.values():
        if re.fullmatch(r"Q\d+", o["titolo"] or ""):
            continue
        o["autori"] = [a for a in o["autori"].values() if not re.fullmatch(r"Q\d+", a["nome"] or "")]
        res.append(o)
    return res


def libera(o):
    """Libera in almeno un paese: USA (anno fino al 1930), Europa (tutti gli autori morti entro il 1955), antichi."""
    if o.get("anno") is not None and o["anno"] <= ANNO_USA:
        return True
    au = o.get("autori") or []
    if au and all((a.get("morte") is not None and a["morte"] <= ANNO_UE) or a.get("antico") for a in au):
        return True
    return False


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
        fresco = (vecchio and vecchio.get("autori") == gruppo
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
                vecchio = {"scaricato": oggi.isoformat(), "autori": gruppo, "opere": [o for o in r if libera(o)]}
                json.dump(vecchio, open(f, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
            time.sleep(0.5)
        if vecchio:                             # anche se vecchio o con autori diversi: meglio che niente
            for o in vecchio["opere"]:
                tutte[o["qid"]] = o
        if not fresco and not (vecchio and vecchio.get("scaricato") == oggi.isoformat()):
            mancanti += 1
    return list(tutte.values()), mancanti
