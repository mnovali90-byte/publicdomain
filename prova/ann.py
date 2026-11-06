import json, urllib.request, urllib.parse, time
U="https://query.wikidata.org/sparql"
def q(s):
    for t in range(3):
        try:
            r=urllib.request.Request(U+"?"+urllib.parse.urlencode({"query":s,"format":"json"}),headers={"User-Agent":"PublicDomainRadar/1.0 (https://publicdomainradar.com)"})
            return json.load(urllib.request.urlopen(r,timeout=90))["results"]["bindings"]
        except Exception as e: print("err",str(e)[:80]); time.sleep(8)
    return []
OCC="wd:Q36180 wd:Q49757 wd:Q6625963 wd:Q214917 wd:Q4853732 wd:Q482980 wd:Q11774202"
CL="wd:Q8261 wd:Q49084 wd:Q25379 wd:Q5185279 wd:Q571 wd:Q7725634 wd:Q149537"
ETA=[25,50,75,100,125,150,175,200,250,300,400]
def persone(prop,y):
    return q(f'''SELECT ?pLabel ?d ?pr ?sl WHERE {{ VALUES ?o {{ {OCC} }} ?p wdt:P106 ?o; wdt:P31 wd:Q5; p:{prop}/psv:{prop} [wikibase:timeValue ?d; wikibase:timePrecision ?pr].
    FILTER(YEAR(?d)={y}) ?p wikibase:sitelinks ?sl. FILTER(?sl>=20) SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,it". }} }}''')
def opere(y):
    return q(f'''SELECT ?pLabel ?d ?pr ?sl WHERE {{ VALUES ?c {{ {CL} }} ?p wdt:P31 ?c; p:P577/psv:P577 [wikibase:timeValue ?d; wikibase:timePrecision ?pr].
    FILTER(YEAR(?d)={y}) ?p wikibase:sitelinks ?sl. FILTER(?sl>=10) SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,it". }} }}''')
tot={"nascita":0,"morte":0,"prima edizione":0}
for et in ETA:
    y=2027-et
    for nome,fn in (("nascita",lambda y:persone("P569",y)),("morte",lambda y:persone("P570",y)),("prima edizione",opere)):
        r=fn(y); W={}
        for x in r:
            k=x["pLabel"]["value"]; W[k]=(int(x["sl"]["value"]),int(x["pr"]["value"]),x["d"]["value"][:10])
        n=len(W); g=sum(1 for v in W.values() if v[1]>=11); tot[nome]+=n
        top=sorted(W.items(),key=lambda kv:-kv[1][0])[:4]
        print(f"{et:>3} anni | {nome:<14} | {y} | {n:>3} voci, {g:>3} con giorno | "+"; ".join(f"{k} ({v[2]})" for k,v in top))
        time.sleep(1)
print("TOTALI",tot)
