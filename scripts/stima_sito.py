"""Stima dell'accuratezza e della copertura del sito (18/11/2026). Solo misura: non cambia dati né regole.
Scrive in docs/stima-sito/:
- us_date.json: per le opere di data/us-2027.json tutte le date di pubblicazione (P577) in Wikidata
- autori_mancanti.json: persone morte nel 1956 con una professione che discende da «scrittore» (Q36180)
  in Wikidata e almeno 3 pagine Wikimedia, che NON sono in data/2027.json
- descrizioni.json: descrizione Wikidata (en, it) e tutte le professioni degli autori di data/2027.json
- morti_multiple.json: autori di data/2027.json con più anni di morte in Wikidata
- wp_1956.json: persone della sezione Deaths di «1956 in literature» (Wikipedia inglese) con il codice Wikidata
- duke_2026.html: la pagina Public Domain Day 2026 della Duke (riferimento esterno per gli USA)
- us_1930.json: le opere che la regola del sito sceglierebbe per il 1930 (da confrontare con la Duke)
"""
import json, pathlib, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import opere

OUT = pathlib.Path("docs/stima-sito"); OUT.mkdir(parents=True, exist_ok=True)
UA = "PublicDomainTool/0.1 (https://github.com/mnovali90-byte/publicdomain)"

def get(url, tent=4):
    for t in range(tent):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/sparql-results+json, application/json, text/html"})
            return urllib.request.urlopen(req, timeout=180).read().decode("utf-8", "replace")
        except Exception as e:
            print("  riprovo:", e, file=sys.stderr); time.sleep(10 * (t + 1))
    return None

def sparql(q):
    t = get("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"}))
    time.sleep(2)
    return json.loads(t)["results"]["bindings"] if t else None

def salva(nome, x):
    (OUT / nome).write_text(json.dumps(x, ensure_ascii=False, indent=1), encoding="utf-8"); print("scritto", nome, file=sys.stderr)

def a_pezzi(lista, n):
    for i in range(0, len(lista), n): yield lista[i:i + n]

# 1. date di pubblicazione delle opere USA 2027
us = json.load(open("data/us-2027.json"))["opere"]
date = {}
for g in a_pezzi([o["qid"] for o in us], 80):
    r = sparql("SELECT ?w ?d WHERE { VALUES ?w { %s } ?w wdt:P577 ?d }" % " ".join("wd:" + q for q in g)) or []
    for b in r: date.setdefault(b["w"]["value"].rsplit("/", 1)[-1], []).append(b["d"]["value"][:10])
salva("us_date.json", {o["qid"]: {"titolo": o["titolo"], "date": sorted(set(date.get(o["qid"], [])))} for o in us})

# 2. descrizioni e professioni complete degli autori 2027
au = json.load(open("data/2027.json"))["autori"]
desc = {}
for g in a_pezzi([a["wikidata"] for a in au], 100):
    r = sparql("""SELECT ?a ?den ?dit (GROUP_CONCAT(DISTINCT ?pl; separator="|") AS ?prof) (GROUP_CONCAT(DISTINCT STR(YEAR(?m)); separator="|") AS ?morti) WHERE {
      VALUES ?a { %s }
      OPTIONAL { ?a schema:description ?den FILTER(LANG(?den)="en") }
      OPTIONAL { ?a schema:description ?dit FILTER(LANG(?dit)="it") }
      OPTIONAL { ?a wdt:P106 ?p. ?p rdfs:label ?pl FILTER(LANG(?pl)="en") }
      OPTIONAL { ?a wdt:P570 ?m } } GROUP BY ?a ?den ?dit""" % " ".join("wd:" + q for q in g)) or []
    for b in r:
        k = b["a"]["value"].rsplit("/", 1)[-1]
        desc[k] = {"en": b.get("den", {}).get("value"), "it": b.get("dit", {}).get("value"),
                   "professioni": b.get("prof", {}).get("value", "").split("|"), "anni_morte": sorted(set(b.get("morti", {}).get("value", "").split("|")) - {""})}
salva("descrizioni.json", desc)
salva("morti_multiple.json", {k: v["anni_morte"] for k, v in desc.items() if len(v["anni_morte"]) > 1})

# 3. professioni che discendono da «scrittore» e persone morte nel 1956 che il sito non ha
sotto = sparql("SELECT ?o ?ol WHERE { ?o wdt:P279* wd:Q36180 . OPTIONAL { ?o rdfs:label ?ol FILTER(LANG(?ol)=\"en\") } }") or []
classi = {b["o"]["value"].rsplit("/", 1)[-1]: b.get("ol", {}).get("value") for b in sotto}
print(len(classi), "professioni sotto scrittore", file=sys.stderr)
nostri = {a["wikidata"] for a in au}
trovati = {}
for mese in range(1, 13):
    da = f"1956-{mese:02d}-01"; a_ = "1957-01-01" if mese == 12 else f"1956-{mese + 1:02d}-01"
    r = sparql(f"""SELECT ?p ?pl ?sl ?o WHERE {{ ?p wdt:P570 ?m . hint:Prior hint:rangeSafe true .
      FILTER(?m >= "{da}T00:00:00Z"^^xsd:dateTime && ?m < "{a_}T00:00:00Z"^^xsd:dateTime)
      ?p wdt:P31 wd:Q5 ; wikibase:sitelinks ?sl . FILTER(?sl >= 3) ?p wdt:P106 ?o .
      OPTIONAL {{ ?p rdfs:label ?pl FILTER(LANG(?pl)="en") }} }}""")
    if r is None: print("mese fallito", mese, file=sys.stderr); continue
    for b in r:
        o = b["o"]["value"].rsplit("/", 1)[-1]
        if o not in classi: continue
        k = b["p"]["value"].rsplit("/", 1)[-1]
        if k in nostri: continue
        x = trovati.setdefault(k, {"nome": b.get("pl", {}).get("value", k), "pagine": int(b["sl"]["value"]), "professioni": []})
        if classi[o] not in x["professioni"]: x["professioni"].append(classi[o])
miss = sorted(trovati.items(), key=lambda kv: -kv[1]["pagine"])
for g in a_pezzi([k for k, _ in miss[:400]], 100):
    r = sparql("SELECT ?a ?d WHERE { VALUES ?a { %s } ?a schema:description ?d FILTER(LANG(?d)=\"en\") }" % " ".join("wd:" + q for q in g)) or []
    for b in r: trovati[b["a"]["value"].rsplit("/", 1)[-1]]["descrizione"] = b["d"]["value"]
salva("autori_mancanti.json", {"professioni_sotto_scrittore": len(classi), "mancanti": dict(miss)})

# 4. riferimento esterno: Wikipedia «1956 in literature», sezione Deaths
t = get("https://en.wikipedia.org/w/index.php?title=1956_in_literature&action=raw")
wp = []
if t:
    sez = t.split("==Deaths==")[-1] if "==Deaths==" in t else t.split("== Deaths ==")[-1]
    sez = re.split(r"\n==[^=]", sez)[0]
    titoli = []
    for riga in sez.splitlines():
        m = re.search(r"\[\[([^\]|#]+)", re.sub(r"\[\[(January|February|March|April|May|June|July|August|September|October|November|December)[^\]]*\]\]", "", riga))
        if riga.startswith("*") and m: titoli.append(m.group(1).strip())
    for g in a_pezzi(titoli, 40):
        j = get("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "prop": "pageprops", "ppprop": "wikibase_item", "redirects": 1, "titles": "|".join(g), "format": "json"}))
        if not j: continue
        for p in json.loads(j)["query"]["pages"].values():
            wp.append({"titolo": p.get("title"), "qid": p.get("pageprops", {}).get("wikibase_item")})
salva("wp_1956.json", wp)

# 5. riferimento esterno per gli USA: Duke, Public Domain Day 2026 (opere del 1930), e la regola del sito sul 1930
h = get("https://cspd.law.duke.edu/publicdomainday/2026/") or get("https://web.law.duke.edu/cspd/publicdomainday/2026/")
if h: (OUT / "duke_2026.html").write_text(h, encoding="utf-8")
try:
    salva("us_1930.json", opere.opere_anno(1930))
except Exception as e:
    print("us_1930 fallito:", e, file=sys.stderr)
