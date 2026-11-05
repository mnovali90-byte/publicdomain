"""Prova temporanea: come si arriva dalle edizioni di SBN all'autore, alla lingua e all'anno?"""
import json, sys, urllib.parse, urllib.request
EP = "https://triplestore.iccu.sbn.it/sparql"
def q(query):
    url = EP + "?" + urllib.parse.urlencode({"query": query, "format": "application/sparql-results+json"})
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/sparql-results+json", "User-Agent": "publicdomain-radar/1.0"})
        with urllib.request.urlopen(req, timeout=100) as r:
            return json.load(r)["results"]["bindings"]
    except Exception as e:
        return "ERRORE " + str(e)[:150]
def mostra(nome, query, n=8):
    r = q(query)
    if isinstance(r, str):
        print(f"[sbn] {nome}: {r}", file=sys.stderr); return []
    print(f"[sbn] {nome}: {len(r)} righe", file=sys.stderr)
    for b in r[:n]:
        print("   [sbn] " + " | ".join(f"{k}={v['value'][-110:]}" for k, v in b.items()), file=sys.stderr)
    return r
ag = mostra("agenti Brecht", "SELECT DISTINCT ?a WHERE { ?a <http://www.w3.org/2000/01/rdf-schema#label> ?l . ?l bif:contains \"'brecht'\" . FILTER(STR(?l) = \"Brecht, Bertolt\" && CONTAINS(STR(?a), \"/Agent/\")) } LIMIT 5")
if ag:
    a = ag[0]["a"]["value"]
    print("[sbn] uso", a, file=sys.stderr)
    mostra("cosa punta all'agente", f"SELECT ?p (COUNT(*) AS ?n) WHERE {{ ?s ?p <{a}> }} GROUP BY ?p LIMIT 10")
    mostra("predicati dell'agente", f"SELECT ?p ?o WHERE {{ <{a}> ?p ?o }} LIMIT 12")
    c = mostra("contributi", f"SELECT ?c WHERE {{ ?c <http://id.loc.gov/ontologies/bibframe/agent> <{a}> }} LIMIT 3")
    if c:
        cc = c[0]["c"]["value"]
        mostra("chi ha quel contributo", f"SELECT ?s ?p WHERE {{ ?s ?p <{cc}> }} LIMIT 5")
        w = q(f"SELECT ?s WHERE {{ ?s <http://id.loc.gov/ontologies/bibframe/contribution> <{cc}> }} LIMIT 1")
        if isinstance(w, list) and w:
            ws = w[0]["s"]["value"]
            mostra("predicati dell'opera/istanza", f"SELECT ?p ?o WHERE {{ <{ws}> ?p ?o }} LIMIT 25", 25)
            mostra("istanze dell'opera", f"SELECT ?i ?p ?o WHERE {{ ?i <http://id.loc.gov/ontologies/bibframe/instanceOf> <{ws}> . ?i ?p ?o }} LIMIT 25", 25)
