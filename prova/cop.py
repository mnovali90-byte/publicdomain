import json, urllib.request, urllib.parse, time, collections
U="https://query.wikidata.org/sparql"
def q(s):
    for t in range(3):
        try:
            r=urllib.request.Request(U+"?"+urllib.parse.urlencode({"query":s,"format":"json"}),headers={"User-Agent":"PublicDomainRadar/1.0 (https://publicdomainradar.com)"})
            return json.load(urllib.request.urlopen(r,timeout=120))["results"]["bindings"]
        except Exception as e: print("err",e); time.sleep(10)
    return []
CL="wd:Q8261 wd:Q49084 wd:Q25379 wd:Q5185279 wd:Q571 wd:Q7725634 wd:Q149537"
for anno in (1931,1932):
    s=f'''SELECT ?w ?cLabel ?lLabel ?gLabel WHERE {{ VALUES ?c {{ {CL} }} ?w wdt:P31 ?c; wdt:P577 ?d. FILTER(YEAR(?d)={anno})
    ?w wikibase:sitelinks ?sl. FILTER(?sl>=2) OPTIONAL{{?w wdt:P407 ?l}} OPTIONAL{{?w wdt:P136 ?g}}
    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}'''
    r=q(s); W={}
    for x in r:
        w=W.setdefault(x["w"]["value"],{"c":set(),"l":set(),"g":set()})
        w["c"].add(x["cLabel"]["value"])
        if "lLabel" in x: w["l"].add(x["lLabel"]["value"])
        if "gLabel" in x: w["g"].add(x["gLabel"]["value"])
    n=len(W); print("=== ANNO",anno,"opere",n)
    print("con lingua:",sum(1 for v in W.values() if v["l"]),"| con genere:",sum(1 for v in W.values() if v["g"]))
    for nome,k in (("CLASSE","c"),("LINGUA","l"),("GENERE","g")):
        c=collections.Counter(i for v in W.values() for i in v[k]); print(nome,c.most_common(14))
