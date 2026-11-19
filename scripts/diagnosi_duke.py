"""Perché 18 libri della Duke mancano o sono senza anno nello Storico: cosa dice Wikidata (tipo, date, edizioni). Solo misura."""
import json, pathlib, sys, time, urllib.parse, urllib.request
UA = "PublicDomainTool/0.1 (https://github.com/mnovali90-byte/publicdomain)"
def sparql(q):
    for t in range(3):
        try:
            r = urllib.request.Request("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"}), headers={"User-Agent": UA})
            return json.load(urllib.request.urlopen(r, timeout=90))["results"]["bindings"]
        except Exception as e:
            print(e, file=sys.stderr); time.sleep(8)
    return []
titoli = ["New Hampshire", "The Prospects of Industrial Civilization", "Rootabaga Pigeons", "The Writing of Fiction", "Enough Rope",
          "Now We Are Six", "Amerika", "Time Regained", "Rope", "A Preface to Morals", "The Secret of the Old Clock", "Private Lives",
          "The Conquest of Happiness", "Desire Under the Elms", "Old New York", "On the Trail of Negro Folk-Songs", "Peter Pan, or The Boy Who Wouldn't Grow Up",
          "Elson Basic Readers"]
out = {}
for t in titoli:
    r = sparql(f'''SELECT ?w ?wLabel ?tipoLabel ?pub ?inc ?edpub ?autLabel ?morte ?sl WHERE {{
      ?w rdfs:label "{t}"@en ; wikibase:sitelinks ?sl . FILTER(?sl >= 1)
      OPTIONAL {{ ?w wdt:P31 ?tipo }} OPTIONAL {{ ?w wdt:P577 ?pub }} OPTIONAL {{ ?w wdt:P571 ?inc }}
      OPTIONAL {{ ?ed wdt:P629 ?w . ?ed wdt:P577 ?edpub }}
      OPTIONAL {{ ?w wdt:P50 ?aut . OPTIONAL {{ ?aut wdt:P570 ?morte }} }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }} LIMIT 60''')
    out[t] = [{k: v["value"] for k, v in x.items()} for x in r]
    time.sleep(1.5)
pathlib.Path("docs/stima-sito/diagnosi-duke.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
