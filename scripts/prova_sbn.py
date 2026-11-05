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
BF = "http://id.loc.gov/ontologies/bibframe/"
V = "http://viaf.org/viaf/2467372"
ag = mostra("agente via VIAF", f"SELECT ?a WHERE {{ ?a <http://www.w3.org/2002/07/owl#sameAs> <{V}> }} LIMIT 5")
w = "http://triplestore.iccu.sbn.it/resource/IT-ICCU-CFI-0558156#Work"
inst = "http://triplestore.iccu.sbn.it/resource/IT-ICCU-CFI-0558156#Instance"
mostra("nodo lingua", f"SELECT ?l ?p ?o WHERE {{ <{w}> <{BF}language> ?l . ?l ?p ?o }} LIMIT 12")
mostra("nodo pubblicazione", f"SELECT ?pa ?p ?o WHERE {{ <{inst}> <{BF}provisionActivity> ?pa . ?pa ?p ?o }} LIMIT 20", 20)
mostra("nodo contributo", f"SELECT ?c ?p ?o WHERE {{ <{w}> <{BF}contribution> ?c . ?c ?p ?o }} LIMIT 20", 20)
mostra("nodo titolo", f"SELECT ?t ?p ?o WHERE {{ <{w}> <{BF}title> ?t . ?t ?p ?o }} LIMIT 10")
