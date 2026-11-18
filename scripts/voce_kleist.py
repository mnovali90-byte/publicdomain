"""Prepara la voce di Heinrich von Kleist (nascita, 250 anni) per il calendario 2027 già approvato, con i dati di Wikidata."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import anniversari as A
info = A.sparql('''SELECT ?sl ?it ?desc WHERE { wd:Q28494 wikibase:sitelinks ?sl OPTIONAL { wd:Q28494 rdfs:label ?it FILTER(LANG(?it)="it") } OPTIONAL { wd:Q28494 schema:description ?desc FILTER(LANG(?desc)="en") } }''')[0]
v = {"tipo": "nascita", "qid": "Q28494", "nome": "Heinrich von Kleist", "it": A.g(info, "it"), "desc": A.g(info, "desc"),
     "autore": None, "autore_qid": None, "anno": 1777, "anni": 250, "pagine": int(A.g(info, "sl")), "mese": 10, "giorno": 18,
     "fonte_data": "verifica: Wikidata e Britannica (18 ottobre 1777); il Kleist-Museum indica il 10 o il 18 ottobre"}
v["scheda"] = A.schede_voci([v]).get("Q28494")
pathlib.Path("docs/stima-sito/kleist_voce.json").write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(v, ensure_ascii=False))
