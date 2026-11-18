"""Descrizione Wikidata (en, it) e professioni di tutti gli autori di un file dati (per la verifica della regola della lista)."""
import json, os, pathlib, sys, time, urllib.parse, urllib.request
F = os.environ.get("FILE_DATI", "data/2028.json")
OUT = pathlib.Path("docs/regola-lista/descrizioni-" + pathlib.Path(F).stem + ".json")
UA = "PublicDomainTool/0.1 (https://github.com/mnovali90-byte/publicdomain)"
def sparql(q):
    for t in range(4):
        try:
            r = urllib.request.Request("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"}),
                                       headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
            return json.load(urllib.request.urlopen(r, timeout=120))["results"]["bindings"]
        except Exception as e:
            print("riprovo", e, file=sys.stderr); time.sleep(10 * (t + 1))
    return []
au = json.load(open(F))["autori"]; out = {}
for i in range(0, len(au), 100):
    v = " ".join("wd:" + a["wikidata"] for a in au[i:i + 100])
    for b in sparql("""SELECT ?a ?den ?dit (GROUP_CONCAT(DISTINCT ?pl; separator="|") AS ?prof) WHERE { VALUES ?a { %s }
      OPTIONAL { ?a schema:description ?den FILTER(LANG(?den)="en") } OPTIONAL { ?a schema:description ?dit FILTER(LANG(?dit)="it") }
      OPTIONAL { ?a wdt:P106 ?p. ?p rdfs:label ?pl FILTER(LANG(?pl)="en") } } GROUP BY ?a ?den ?dit""" % v):
        out[b["a"]["value"].rsplit("/", 1)[-1]] = {"en": b.get("den", {}).get("value"), "it": b.get("dit", {}).get("value"),
                                                   "professioni": b.get("prof", {}).get("value", "").split("|")}
    time.sleep(2)
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"); print(len(out))
