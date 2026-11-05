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
SAME = "http://www.w3.org/2002/07/owl#sameAs"
LAB = "http://www.w3.org/2000/01/rdf-schema#label"
VAL = "http://www.w3.org/1999/02/22-rdf-syntax-ns#value"
def agenti_viaf(v):
    return f"?a <{SAME}> <http://viaf.org/viaf/{v}> . FILTER(CONTAINS(STR(?a), \"/resource/Agent/\"))"
def agenti_nome(parola, esatto):
    return f"?a <{LAB}> ?l . ?l bif:contains \"'{parola}'\" . FILTER(STR(?l) = \"{esatto}\" && CONTAINS(STR(?a), \"/resource/Agent/\"))"
for nome, filtro in [("Brecht via VIAF", agenti_viaf("2467372")), ("Wilder via nome", agenti_nome("wilder", "Wilder, Laura Ingalls")), ("Walser via nome", agenti_nome("walser", "Walser, Robert"))]:
    mostra(f"{nome}: lingue delle opere", f"SELECT ?lang (COUNT(DISTINCT ?w) AS ?n) WHERE {{ {filtro} ?c <{BF}agent> ?a . ?w <{BF}contribution> ?c . ?w <{BF}language> ?ln . ?ln <{VAL}> ?lang }} GROUP BY ?lang ORDER BY DESC(?n) LIMIT 8")
    mostra(f"{nome}: date delle edizioni in italiano", f"SELECT (COUNT(DISTINCT ?i) AS ?edizioni) (MAX(?d) AS ?ultima) WHERE {{ {filtro} ?c <{BF}agent> ?a . ?w <{BF}contribution> ?c . ?w <{BF}language> ?ln . ?ln <{VAL}> <http://id.loc.gov/vocabulary/languages/ita> . ?w <{BF}hasInstance> ?i . ?i <{BF}provisionActivity> ?pa . ?pa a <{BF}Publication> . ?pa <{BF}date> ?d . FILTER(REGEX(?d, \"^[0-9]{{4}}$\")) }}")
