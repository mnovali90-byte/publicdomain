"""Perché Heinrich von Kleist (Q28494, 250 anni dalla nascita nel 2027) non è nel calendario."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import anniversari as A
date = A.sparql('''SELECT ?d ?pr ?cal ?rank WHERE { wd:Q28494 p:P569 ?s . ?s psv:P569 [wikibase:timeValue ?d; wikibase:timePrecision ?pr; wikibase:timeCalendarModel ?cal]; wikibase:rank ?rank }''')
prof = A.sparql('''SELECT ?o ?oLabel WHERE { wd:Q28494 wdt:P106 ?o SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } }''')
info = A.sparql('''SELECT ?sl ?it ?desc WHERE { wd:Q28494 wikibase:sitelinks ?sl OPTIONAL { wd:Q28494 rdfs:label ?it FILTER(LANG(?it)="it") } OPTIONAL { wd:Q28494 schema:description ?desc FILTER(LANG(?desc)="en") } }''')
opere = A.sparql('''SELECT ?lib ?libLabel ?s2 WHERE { ?lib wdt:P50 wd:Q28494; wikibase:sitelinks ?s2 SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } }''')
occ = set(A.OCC.split()); bad = set(A.NON_LETT.split())
out = {"date": date, "professioni": [{"q": p["o"]["value"].rsplit("/", 1)[-1], "nome": p.get("oLabel", {}).get("value"),
        "letteraria": "wd:" + p["o"]["value"].rsplit("/", 1)[-1] in occ, "non_letteraria": "wd:" + p["o"]["value"].rsplit("/", 1)[-1] in bad} for p in (prof or [])],
       "info": info, "opere_con_P50": [(o.get("libLabel", {}).get("value"), o["s2"]["value"]) for o in (opere or [])]}
pathlib.Path("docs/stima-sito/kleist.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False)[:3000])
