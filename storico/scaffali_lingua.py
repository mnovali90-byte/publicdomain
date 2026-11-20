"""Scaffali «per lingua originale» di Già pubblici (regola decisa il 20/11/2026, campione in docs/registro-prove.md).

Prima gli scaffali per lingua prendevano solo le 3.000 opere più famose al mondo (data/storico/opere.json): l'italiano
aveva 51 titoli. Ora:
  1. chi entra: TUTTE le opere dell'archivio (data/storico/ricerca) scritte in quella lingua secondo Wikidata (P407);
     le varianti storiche sono unite alla lingua di oggi (italiano antico, toscano → italiano; francese antico →
     francese; medio alto tedesco → tedesco; inglese medio → inglese…);
  2. opere in più lingue: conta la lingua del titolo originale (P1476): «Guerra e pace» va col russo, non col
     francese; senza titolo originale va in tutte le sue lingue;
  3. solo libri e testi letterari: tipo (P31) letterario, e niente leggi, costituzioni, dizionari, manuali, inni,
     testi sacri, libretti; niente testi d'odio (data/storico_esclusioni.json);
  4. ordine: visite da persone alla Wikipedia di quella lingua negli ultimi 12 mesi chiusi, con la regola anti-picchi
     (ogni mese al massimo 3 volte il mese tipico: docs/metodo-classifica.md). Per le lingue senza una Wikipedia
     propria (es. greco antico) si usa la Wikipedia inglese.
Scrive data/storico/scaffali_lingua.json, letto da storico/pagina.py. Se Wikidata non risponde per una parte
dell'archivio, il file vecchio resta com'è (niente scaffali a metà)."""
import json, re, statistics, sys, time, urllib.error, urllib.parse, urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

R = Path(__file__).resolve().parent.parent
S = R / "data" / "storico"
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
OGGI = date.today()
FINE = OGGI.replace(day=1)
INIZIO = date(FINE.year - 1, FINE.month, 1)
PER_LINGUA = 400        # opere per lingua di cui si misurano le visite (le più diffuse per numero di Wikipedia)
TENUTE = 150            # opere per lingua salvate per la pagina (poi la pagina filtra per paese)
MIN_OPERE = 30          # una lingua diventa scaffale con almeno tante opere
MAX_LINGUE = 30

TIPI = {"Q7725634", "Q571", "Q8261", "Q25379", "Q49084", "Q5185279", "Q35760", "Q116476516", "Q47461344", "Q482",
        "Q37484", "Q1279564", "Q149537", "Q12308638", "Q1371849", "Q182357", "Q4184", "Q2831984"}
NON_LIBRI = ("constitution", "law", "legal", "statute", "treaty", "declaration", "charter", "manual", "dictionary",
             "encyclopedia", "gazetteer", "anthem", "hymn", "religious text", "scripture", "sacred", "liturgical",
             "prayer", "catechism", "creed", "encyclical", "papal bull", "edict", "decree", "atlas", "almanac", "speech",
             "sermon", "song", "libretto", "ballet", "opera", "etiquette", "reference work", "textbook", "oath", "lexicon",
             "biographical dictionary", "catalog")
TITOLI_NO = re.compile(r"\b(dizionario|diccionario|dictionnaire|dictionary|w[öo]rterbuch|manuale|manual|manuel|"
                       r"handbuch|enciclopedia|encyclop|lexicon|lexikon|promptuarium|catalogus|catalogue)", re.I)
# codici di lingua storici → lingua di oggi (ISO 639)
BASE = {"fro": "fr", "frm": "fr", "xno": "fr", "gmh": "de", "goh": "de", "enm": "en", "osp": "es", "ita": "it",
        "it-tuscany": "it", "roa-opt": "pt", "dum": "nl", "odt": "nl", "non": "is", "orv": "ru", "la-x-medieval": "la"}
VARIANTI_IT = ("tuscan", "old italian", "medieval italian", "florentine", "italian")
# lingua → Wikipedia per le visite, quando il codice non è quello della Wikipedia
WIKI = {"grc": "en", "ang": "en", "sa": "en", "pi": "en", "lzh": "zh-classical", "ota": "tr", "akk": "en",
        "egy": "en", "sux": "en", "he": "he", "arc": "en", "cu": "en", "got": "en", "peo": "en", "pal": "en"}


def get(u, prove=8):
    for t in range(prove):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"items": []}
            time.sleep(15 * (t + 1) if e.code in (429, 502, 503, 504) else 3)
        except Exception:
            time.sleep(5 * (t + 1))
    return None


def sparql(q):
    d = get("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"}))
    return None if d is None else d["results"]["bindings"]


# lingue riconosciute dall'ultima parola dell'etichetta quando la variante non ha un codice (20/11/2026: il Don
# Chisciotte su Wikidata è in «Early Modern Spanish», senza codice, e mancava dallo scaffale spagnolo)
NOMI_LINGUA = {"spanish": "es", "castilian": "es", "french": "fr", "german": "de", "english": "en", "italian": "it",
               "russian": "ru", "portuguese": "pt", "latin": "la", "greek": "el", "dutch": "nl", "polish": "pl",
               "czech": "cs", "danish": "da", "swedish": "sv", "norwegian": "no", "icelandic": "is", "hungarian": "hu",
               "catalan": "ca", "arabic": "ar", "persian": "fa", "chinese": "zh", "japanese": "ja", "hebrew": "he"}


def base(codice, etichetta_en):
    c = (codice or "").lower()
    e = (etichetta_en or "").lower()
    if any(e == v or e.startswith(v + " ") or e.endswith(" " + v) for v in VARIANTI_IT):
        return "it"
    if c in BASE:
        return BASE[c]
    if not c:
        ultima = e.split()[-1] if e.split() else ""
        if e.startswith("ancient greek"):
            return "grc"
        return NOMI_LINGUA.get(ultima)
    return c.split("-")[0]


def leggi_archivio():
    arch = {}
    for f in sorted((S / "ricerca").glob("*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")).get("opere", []):
            arch.setdefault(r[0], r)
    return arch


def info_wikidata(qids):
    info, blocchi, passata = {}, [qids[i:i + 250] for i in range(0, len(qids), 250)], 0
    nomi = {}
    while blocchi and passata < 3:
        passata += 1
        rifare = []
        for i, b in enumerate(blocchi):
            v = " ".join("wd:" + q for q in b)
            q = f"""SELECT ?w ?ling ?code ?lit ?len ?t ?tLabel ?tl WHERE {{ VALUES ?w {{ {v} }}
              OPTIONAL {{ ?w wdt:P407 ?ling OPTIONAL {{ ?ling wdt:P424 ?code }}
                         OPTIONAL {{ ?ling rdfs:label ?lit FILTER(LANG(?lit)="it") }}
                         OPTIONAL {{ ?ling rdfs:label ?len FILTER(LANG(?len)="en") }} }}
              OPTIONAL {{ ?w wdt:P31 ?t }}
              OPTIONAL {{ ?w wdt:P1476 ?tit BIND(LANG(?tit) AS ?tl) }}
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}"""
            righe = sparql(q)
            if righe is None:
                rifare += [b[:len(b) // 2], b[len(b) // 2:]]
                continue
            for r in righe:
                k = r["w"]["value"].rsplit("/", 1)[-1]
                x = info.setdefault(k, {"lingue": set(), "tipi": set(), "tipi_nomi": set(), "lingua_titolo": set()})
                if "ling" in r:
                    lb = base(r.get("code", {}).get("value"), r.get("len", {}).get("value"))
                    if lb:
                        x["lingue"].add(lb)
                        if r.get("code", {}).get("value", "").lower() == lb or lb == "it" and r.get("len", {}).get("value") == "Italian":
                            nomi.setdefault(lb, Counter())[(r.get("lit", {}).get("value"), r.get("len", {}).get("value"))] += 1
                if "t" in r:
                    x["tipi"].add(r["t"]["value"].rsplit("/", 1)[-1])
                if "tLabel" in r:
                    x["tipi_nomi"].add(r["tLabel"]["value"].lower())
                if r.get("tl", {}).get("value"):
                    x["lingua_titolo"].add(base(r["tl"]["value"], ""))
            time.sleep(1)
            if i % 60 == 0:
                print(f"  wikidata passata {passata}: blocco {i} di {len(blocchi)}", flush=True)
        blocchi = [b for b in rifare if b]
        if blocchi:
            time.sleep(120)
    mancanti = sum(len(b) for b in blocchi)
    return info, nomi, mancanti


def titoli_wiki(qids, wiki):
    out = {}
    for i in range(0, len(qids), 50):
        d = get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
            {"action": "wbgetentities", "ids": "|".join(qids[i:i + 50]), "props": "sitelinks",
             "sitefilter": wiki.replace("-", "_") + "wiki", "format": "json"}))
        for q, e in ((d or {}).get("entities") or {}).items():
            s = (e.get("sitelinks") or {}).get(wiki.replace("-", "_") + "wiki")
            if s:
                out[q] = s["title"]
        time.sleep(0.3)
    return out


def visite(wiki, titolo):
    t = urllib.parse.quote(titolo.replace(" ", "_"), safe="")
    d = get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{wiki}.wikipedia/all-access/user/{t}/monthly/"
            f"{INIZIO:%Y%m%d}00/{FINE - timedelta(days=1):%Y%m%d}00", prove=5)
    if d is None:
        return None
    s = [i["views"] for i in d.get("items", [])][:12]
    s += [0] * (12 - len(s))
    tetto = 3 * statistics.median(s)
    return int(sum(min(x, tetto) for x in s))


def main():
    inizio = time.time()
    arch = leggi_archivio()
    esc = json.loads((R / "data" / "storico_esclusioni.json").read_text(encoding="utf-8"))
    no_o, no_a = set(esc.get("qid", {})), set(esc.get("autori_qid", {}))
    print("opere nell'archivio:", len(arch), flush=True)
    info, nomi, mancanti = info_wikidata(sorted(arch))
    if mancanti:
        print(f"Wikidata non ha risposto per {mancanti} opere: il file degli scaffali resta com'è.")
        return 1
    cand, tolti = defaultdict(list), Counter()
    for k, x in info.items():
        r = arch[k]
        if r[6] or k in no_o or any(a[0] in no_a for a in r[5]):
            tolti["esclusi"] += 1
            continue
        if any(any(n in t for n in NON_LIBRI) for t in x["tipi_nomi"]) or TITOLI_NO.search(r[1] or "") or TITOLI_NO.search(r[2] or ""):
            tolti["non libri"] += 1
            continue
        if not (x["tipi"] & TIPI):
            tolti["tipo non letterario"] += 1
            continue
        ls = set(x["lingue"])
        if len(ls) > 1 and x["lingua_titolo"] - {None}:
            ls &= x["lingua_titolo"]
        for l in ls:
            cand[l].append(k)
    lingue = sorted((l for l in cand if len(cand[l]) >= MIN_OPERE), key=lambda l: -len(cand[l]))[:MAX_LINGUE]
    print("tolti:", dict(tolti), "| lingue:", {l: len(cand[l]) for l in lingue}, flush=True)
    out = {"aggiornato": OGGI.isoformat(), "mesi": f"{INIZIO:%Y-%m}/{FINE - timedelta(days=1):%Y-%m}", "lingue": {}}
    for l in lingue:
        lista = sorted(cand[l], key=lambda k: -(arch[k][4] or 0))[:PER_LINGUA]
        wiki = WIKI.get(l, l)
        tit = titoli_wiki(lista, wiki)
        if len(tit) < 0.2 * len(lista) and wiki != "en":      # Wikipedia della lingua assente o quasi: si usa l'inglese
            wiki = "en"
            tit = titoli_wiki(lista, wiki)
        with ThreadPoolExecutor(max_workers=3) as pool:
            v = dict(zip(tit, pool.map(lambda k: visite(wiki, tit[k]), tit)))
        persi = sum(1 for x in v.values() if x is None)
        ordine = sorted(lista, key=lambda k: (-(v.get(k) or 0), -(arch[k][4] or 0)))[:TENUTE]
        (it, en) = (nomi.get(l) or Counter({(None, None): 1})).most_common(1)[0][0]
        out["lingue"][l] = {"nome_it": it or en or l, "nome_en": en or l, "wiki": wiki, "candidati": len(cand[l]),
                            "letture_fallite": persi, "opere": [[k, v.get(k) or 0] for k in ordine]}
        print(f"  {l} ({it}): {len(cand[l])} opere, visite su {wiki}.wikipedia, letture fallite {persi}", flush=True)
    (S / "scaffali_lingua.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"fatto in {int(time.time() - inizio) // 60} minuti")
    return 0


if __name__ == "__main__":
    sys.exit(main())
