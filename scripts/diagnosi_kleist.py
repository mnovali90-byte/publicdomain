"""Perché Heinrich von Kleist (250 anni dalla nascita nel 2027) non è nel calendario: legge da Wikidata le sue date e professioni."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import anniversari as A
q = A.sparql('''SELECT ?p ?d ?pr ?cal ?sl ?oLabel WHERE { ?p rdfs:label "Heinrich von Kleist"@de ; wdt:P31 wd:Q5 ; wikibase:sitelinks ?sl .
  OPTIONAL { ?p p:P569/psv:P569 [wikibase:timeValue ?d; wikibase:timePrecision ?pr; wikibase:timeCalendarModel ?cal] }
  OPTIONAL { ?p wdt:P106 ?o } SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } }''')
r = A.q_persone("P569", 1777) or []
dentro = [x for x in r if "Kleist" in (A.g(x, "pLabel") or "")]
out = {"wikidata": q, "nella_ricerca_del_calendario": dentro, "OCC": A.OCC, "NON_LETT": A.NON_LETT, "soglia": A.SOGLIA_PERSONE}
pathlib.Path("docs/stima-sito/kleist.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False)[:3000])
