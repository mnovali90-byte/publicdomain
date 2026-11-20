"""Campione degli scaffali «per lingua» di Già pubblici (20/11/2026). Non cambia il sito.

Oggi lo scaffale di una lingua prende solo le opere tra le 3.000 più famose al mondo (data/storico/opere.json).
Qui si prova la regola nuova:
  1. chi entra: TUTTE le opere dell'archivio (data/storico/ricerca, circa 82.500) scritte in quella lingua, secondo
     Wikidata (P407), con le varianti storiche unite (italiano antico, toscano → italiano; francese antico → francese…);
  2. solo libri e testi letterari (tipo P31 in una lista di tipi letterari);
  3. ordine: visite da persone alla Wikipedia di quella lingua, ultimi 12 mesi chiusi, con la regola anti-picchi
     (ogni mese al massimo 3 volte la mediana: docs/metodo-classifica.md).
Confronta i primi 30 di oggi e di domani per italiano, francese, tedesco, spagnolo e inglese.
Scrive docs/stima-sito/prova-scaffali.json e .md."""
import glob, json, statistics, time, urllib.error, urllib.parse, urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

R = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
OGGI = date.today()
FINE = OGGI.replace(day=1)
INIZIO = date(FINE.year - 1, FINE.month, 1)
LINGUE = ["it", "fr", "de", "es", "en"]
NOMI = {"it": "Italiano", "fr": "Francese", "de": "Tedesco", "es": "Spagnolo", "en": "Inglese"}
# varianti storiche da unire, riconosciute dall'etichetta inglese della lingua su Wikidata
VARIANTI = {
    "it": ("italian", "tuscan", "florentine", "vulgar latin italian", "old italian"),
    "fr": ("french", "old french", "middle french", "anglo-norman"),
    "de": ("german", "middle high german", "early new high german", "old high german"),
    "es": ("spanish", "old spanish", "castilian"),
    "en": ("english", "middle english", "early modern english"),
}
ESCLUSE = ("creole", "sign language", "swiss german", "pennsylvania", "low german")
TIPI = {"Q7725634", "Q571", "Q8261", "Q25379", "Q49084", "Q5185279", "Q35760", "Q116476516", "Q47461344", "Q482",
        "Q37484", "Q1279564", "Q149537", "Q12308638", "Q1371849", "Q182357", "Q4184", "Q2831984"}
# tipi da escludere anche se l'opera ha un tipo letterario (riconosciuti dall'etichetta inglese del tipo): campione del
# 20/11/2026, entravano Costituzione USA, Siete Partidas, dizionari, manuali, inni nazionali
NON_LIBRI = ("constitution", "law", "legal", "statute", "treaty", "declaration", "charter", "manual", "dictionary",
             "encyclopedia", "gazetteer", "anthem", "hymn", "religious text", "scripture", "sacred", "liturgical",
             "prayer", "catechism", "creed", "encyclical", "papal bull", "edict", "decree", "atlas", "almanac", "speech",
             "sermon", "song", "libretto", "ballet", "opera")
CODICI = {"fro": "fr", "frm": "fr", "xno": "fr", "gmh": "de", "goh": "de", "enm": "en", "osp": "es", "ita": "it"}
# opera letteraria, libro, romanzo, teatro, racconto, raccolta di poesie, saggio, opera drammatica, opera scritta, poesia,
# poema epico, raccolta di racconti, novella, poema, sonetto(?), poema in prosa, ballata, … (lista da rivedere col campione)


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


def lingua_di(etichetta):
    e = (etichetta or "").lower()
    if any(x in e for x in ESCLUSE):
        return None
    for l, vs in VARIANTI.items():
        if e in vs or any(e == v or e.startswith(v + " ") or e.endswith(" " + v) for v in vs):
            return l
    return None


def mesi(lingua, titolo):
    t = urllib.parse.quote(titolo.replace(" ", "_"), safe="")
    d = get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{lingua}.wikipedia/all-access/user/{t}/monthly/"
            f"{INIZIO:%Y%m%d}00/{FINE - timedelta(days=1):%Y%m%d}00")
    if d is None:
        return None
    return [i["views"] for i in d.get("items", [])][:12] or [0]


def tipiche(s):
    s = s + [0] * (12 - len(s))
    tetto = 3 * statistics.median(s)
    return int(sum(min(x, tetto) for x in s))


def autore(r):
    a = r[5][0][1] if r[5] else ""
    return "anonimo" if (not a or a.startswith("http")) else a


def main():
    archivio = {}
    for f in glob.glob(str(R / "data" / "storico" / "ricerca" / "*.json")):
        for r in json.load(open(f, encoding="utf-8"))["opere"]:
            archivio[r[0]] = r
    qids = sorted(archivio)
    print("opere nell'archivio:", len(qids))
    # 1. lingua, tipo e titoli delle pagine Wikipedia, 400 opere alla volta
    info, falliti, da_rifare = {}, 0, []
    blocchi = [qids[i:i + 250] for i in range(0, len(qids), 250)]
    passata = 0
    while blocchi and passata < 3:   # i blocchi falliti si riprovano fino a 3 volte, più piccoli (20/11/2026: 24 falliti)
      passata += 1
      falliti, da_rifare = 0, []
      for i, blocco in enumerate(blocchi):
        v = " ".join("wd:" + q for q in blocco)
        q = f"""SELECT ?w ?lingLabel ?t ?tLabel ?tl ?pit ?pfr ?pde ?pes ?pen WHERE {{ VALUES ?w {{ {v} }}
          OPTIONAL {{ ?w wdt:P407 ?ling }} OPTIONAL {{ ?w wdt:P31 ?t }}
          OPTIONAL {{ ?w wdt:P1476 ?tit BIND(LANG(?tit) AS ?tl) }}
          OPTIONAL {{ ?ait schema:about ?w; schema:isPartOf <https://it.wikipedia.org/>; schema:name ?pit }}
          OPTIONAL {{ ?afr schema:about ?w; schema:isPartOf <https://fr.wikipedia.org/>; schema:name ?pfr }}
          OPTIONAL {{ ?ade schema:about ?w; schema:isPartOf <https://de.wikipedia.org/>; schema:name ?pde }}
          OPTIONAL {{ ?aes schema:about ?w; schema:isPartOf <https://es.wikipedia.org/>; schema:name ?pes }}
          OPTIONAL {{ ?aen schema:about ?w; schema:isPartOf <https://en.wikipedia.org/>; schema:name ?pen }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}"""
        righe = sparql(q)
        if righe is None:
            falliti += 1
            da_rifare += [blocco[:len(blocco) // 2], blocco[len(blocco) // 2:]]
            continue
        for r in righe:
            k = r["w"]["value"].rsplit("/", 1)[-1]
            x = info.setdefault(k, {"lingue": set(), "tipi": set(), "tipi_nomi": set(), "lingua_titolo": set(), "pagine": {}})
            if "tLabel" in r: x["tipi_nomi"].add(r["tLabel"]["value"].lower())
            if r.get("tl", {}).get("value"): x["lingua_titolo"].add(r["tl"]["value"].split("-")[0].lower())
            if "lingLabel" in r: x["lingue"].add(r["lingLabel"]["value"])
            if "t" in r: x["tipi"].add(r["t"]["value"].rsplit("/", 1)[-1])
            for l in LINGUE:
                if "p" + l in r: x["pagine"][l] = r["p" + l]["value"]
        time.sleep(1)
        if i % 40 == 0:
            print(" passata", passata, "blocco", i, "di", len(blocchi), "falliti", falliti, flush=True)
      blocchi = [b for b in da_rifare if b]
      if blocchi:
          time.sleep(120)
    falliti = sum(len(b) for b in blocchi)
    print("opere senza risposta da Wikidata dopo 3 passate:", falliti)
    etichette = Counter(e for x in info.values() for e in x["lingue"])
    # 2. candidati per lingua
    cand = {l: [] for l in LINGUE}
    scartati_tipo = Counter()
    tolti = Counter()
    for k, x in info.items():
        if archivio[k][6]:
            tolti["esclusi (testi d'odio)"] += 1
            continue
        if any(any(n in t for n in NON_LIBRI) for t in x["tipi_nomi"]):
            tolti["non libri"] += 1
            continue
        tutte = {lingua_di(e) or ("altra:" + e) for e in x["lingue"]}
        ls = {l for l in tutte if l in LINGUE}
        if len(tutte) > 1:
            # più lingue: conta la lingua del titolo originale (Guerra e pace: russo, non francese); senza, tutte
            tit = {CODICI.get(c, c) for c in x["lingua_titolo"]}
            if tit:
                ls = ls & tit
                if not ls:
                    tolti["lingua del titolo fuori da queste 5"] += 1
        for l in ls:
            if not (x["tipi"] & TIPI):
                scartati_tipo[l] += 1
                continue
            if x["pagine"].get(l):
                cand[l].append(k)
    print({l: len(v) for l, v in cand.items()}, "scartati per tipo:", dict(scartati_tipo), "tolti:", dict(tolti))
    # 3. visite: per ogni lingua le 400 opere con più Wikipedia (archivio, colonna 4)
    lavori = []
    for l in LINGUE:
        cand[l].sort(key=lambda k: -(archivio[k][4] or 0))
        lavori += [(k, l) for k in cand[l][:400]]

    def uno(x):
        k, l = x
        time.sleep(0.05)
        return x, mesi(l, info[k]["pagine"][l])
    serie = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        for x, s in pool.map(uno, lavori):
            serie[x] = s
    persi = sum(1 for s in serie.values() if s is None)
    # 4. scaffali di oggi (le 3.000 di data/storico/opere.json)
    o = json.loads((R / "data" / "storico" / "opere.json").read_text(encoding="utf-8"))
    ops = o["opere"] if isinstance(o, dict) else o
    out = {"tolti": dict(tolti), "opere_senza_risposta": falliti, "letture_visite_fallite": persi,
           "etichette_lingua_piu_comuni": etichette.most_common(60), "lingue": {}}
    md = [f"# Campione degli scaffali per lingua — {OGGI}", "",
          f"Opere senza risposta da Wikidata: {falliti}. Tolti: {dict(tolti)}. Letture visite fallite: {persi}. (Se non sono 0 il campione è incompleto.)", ""]
    for l in LINGUE:
        oggi = [x for x in ops if lingua_di((x.get("lingua") or {}).get("en")) == l]
        oggi.sort(key=lambda x: -(x.get("visite_" + l) or 0))
        nuovi = sorted(((k, tipiche(serie[(k, l)]) if serie.get((k, l)) else 0) for k in cand[l][:400]), key=lambda z: -z[1])
        out["lingue"][l] = {"oggi_titoli": len(oggi), "domani_candidati": len(cand[l]),
                            "oggi_primi_30": [x["titolo_it"] or x["titolo"] for x in oggi[:30]],
                            "domani_primi_30": [[archivio[k][2] or archivio[k][1], autore(archivio[k]), v] for k, v in nuovi[:30]]}
        md += [f"## {NOMI[l]}: oggi {len(oggi)} titoli, domani {len(cand[l])} candidati", "",
               "| # | Oggi | Domani (visite tipiche su Wikipedia in questa lingua) |", "|---|---|---|"]
        for i in range(30):
            a = (oggi[i].get("titolo_it") or oggi[i]["titolo"]) if i < len(oggi) else ""
            b = ""
            if i < len(nuovi):
                k, v = nuovi[i]
                b = f"{archivio[k][2] or archivio[k][1]} — {autore(archivio[k])} ({v:,})"
            md.append(f"| {i + 1} | {a} | {b} |")
        md.append("")
    (R / "docs" / "stima-sito" / "prova-scaffali.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (R / "docs" / "stima-sito" / "prova-scaffali.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("fatto")


if __name__ == "__main__":
    main()
