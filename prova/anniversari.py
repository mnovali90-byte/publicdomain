"""Anniversari letterari per l'anno ANNO da Wikidata (bozza per controllo a mano)."""
import json, urllib.request, urllib.parse, time, re, sys
ANNO = 2027
U = "https://query.wikidata.org/sparql"
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
OCC = "wd:Q6625963 wd:Q49757 wd:Q214917 wd:Q4853732 wd:Q15949613 wd:Q11774202"  # romanziere, poeta, drammaturgo, scrittore per ragazzi, novellista, saggista
CL = "wd:Q8261 wd:Q49084 wd:Q25379 wd:Q5185279 wd:Q571 wd:Q7725634 wd:Q149537"
ETA = [50, 75, 100, 125, 150, 175, 200, 250, 300, 400]
SL_P, SL_O = 30, 15

def q(s):
    for t in range(3):
        try:
            r = urllib.request.Request(U + "?" + urllib.parse.urlencode({"query": s, "format": "json"}), headers=UA)
            return json.load(urllib.request.urlopen(r, timeout=70))["results"]["bindings"]
        except Exception as e:
            print("err", str(e)[:80], file=sys.stderr); time.sleep(8 * (t + 1))
    return None

def intervallo(y):
    return f'"{y:04d}-01-01T00:00:00Z"^^xsd:dateTime', f'"{y+1:04d}-01-01T00:00:00Z"^^xsd:dateTime'

def persone(prop, y):
    a, b = intervallo(y)
    return q(f'''SELECT ?p ?pLabel ?pit ?desc ?d ?pr ?sl WHERE {{ VALUES ?o {{ {OCC} }}
 ?p wdt:P106 ?o; wdt:P31 wd:Q5; p:{prop}/psv:{prop} [wikibase:timeValue ?d; wikibase:timePrecision ?pr].
 FILTER(?d>={a} && ?d<{b}) ?p wikibase:sitelinks ?sl. FILTER(?sl>={SL_P})
 OPTIONAL {{ ?p rdfs:label ?pit FILTER(LANG(?pit)="it") }} OPTIONAL {{ ?p schema:description ?desc FILTER(LANG(?desc)="en") }}
 SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}''')

def opere(y):
    a, b = intervallo(y)
    return q(f'''SELECT ?p ?pLabel ?pit ?desc ?auth ?d ?pr ?sl WHERE {{ VALUES ?c {{ {CL} }}
 ?p wdt:P31 ?c; p:P577/psv:P577 [wikibase:timeValue ?d; wikibase:timePrecision ?pr].
 FILTER(?d>={a} && ?d<{b}) ?p wikibase:sitelinks ?sl. FILTER(?sl>={SL_O})
 OPTIONAL {{ ?p wdt:P50 ?au. ?au rdfs:label ?auth FILTER(LANG(?auth)="en") }}
 OPTIONAL {{ ?p rdfs:label ?pit FILTER(LANG(?pit)="it") }} OPTIONAL {{ ?p schema:description ?desc FILTER(LANG(?desc)="en") }}
 SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}''')

voci = {}
for et in ETA:
    y = ANNO - et
    for tipo, fn in (("nascita", lambda y: persone("P569", y)), ("morte", lambda y: persone("P570", y)), ("prima edizione", opere)):
        r = fn(y)
        if r is None:
            print("FALLITA", tipo, y); continue
        for x in r:
            nome = x["pLabel"]["value"]
            if re.fullmatch(r"Q\d+", nome): continue
            k = (tipo, x["p"]["value"].rsplit("/", 1)[-1])
            v = voci.setdefault(k, {"tipo": tipo, "qid": k[1], "nome": nome, "it": x.get("pit", {}).get("value"),
                "desc": x.get("desc", {}).get("value"), "autore": x.get("auth", {}).get("value"),
                "data": x["d"]["value"][:10], "prec": int(x["pr"]["value"]), "pagine": int(x["sl"]["value"]), "anni": et})
        time.sleep(1.5)
        print(f"{et} {tipo} {y}: {sum(1 for k in voci if k[0]==tipo and voci[k]['anni']==et)}", flush=True)
json.dump(list(voci.values()), open("prova/anniversari.json", "w"), ensure_ascii=False)
print("=== ELENCO ===")
for v in sorted(voci.values(), key=lambda v: (v["data"][5:] if v["prec"] >= 11 else "99", -v["pagine"])):
    g = v["data"][5:] if v["prec"] >= 11 else "anno?"
    print(f'{g:>6} | {v["anni"]:>3}a {v["tipo"]:<14} | {v["nome"]} {("— "+v["autore"]) if v["autore"] else ""} | sl{v["pagine"]} | {v["data"][:4]} | {(v["desc"] or "")[:60]}')
print("TOTALE", len(voci))
