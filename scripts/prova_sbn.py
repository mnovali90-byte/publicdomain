"""Prova temporanea: l'endpoint SPARQL di SBN risponde? Che dati ha su un autore?"""
import json, sys, urllib.parse, urllib.request
EP = "https://triplestore.iccu.sbn.it/sparql"
def q(query):
    url = EP + "?" + urllib.parse.urlencode({"query": query, "format": "application/sparql-results+json"})
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/sparql-results+json", "User-Agent": "publicdomain-radar/1.0"})
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r)
    except Exception as e:
        return {"errore": str(e)[:200]}
def mostra(nome, query):
    r = q(query)
    if "errore" in r:
        print(f"[sbn] {nome}: ERRORE {r['errore']}", file=sys.stderr); return
    righe = r["results"]["bindings"]
    print(f"[sbn] {nome}: {len(righe)} righe", file=sys.stderr)
    for b in righe[:8]:
        print("   [sbn] " + " | ".join(f"{k}={v['value'][:110]}" for k, v in b.items()), file=sys.stderr)
mostra("campione triple", "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 5")
mostra("grafi", "SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } } LIMIT 10")
mostra("tipi", "SELECT ?t (COUNT(*) AS ?n) WHERE { ?s a ?t } GROUP BY ?t ORDER BY DESC(?n) LIMIT 10")
mostra("Brecht (bif:contains)", "SELECT ?s ?p ?o WHERE { ?s ?p ?o . ?o bif:contains \"'brecht'\" } LIMIT 8")
mostra("Brecht (filter)", "SELECT ?s ?p ?o WHERE { ?s ?p ?o . FILTER(isLiteral(?o) && CONTAINS(LCASE(STR(?o)), \"brecht, bertolt\")) } LIMIT 8")
