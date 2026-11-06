import json, urllib.request, urllib.parse, time
U="https://query.wikidata.org/sparql"
CLASSI={"romanzo":"Q8261","racconto":"Q49084","opera teatrale":"Q25379","poesia":"Q5185279","libro":"Q571","raccolta poesie":"Q7725634"}
def q(s):
    for t in range(3):
        try:
            r=urllib.request.Request(U+"?"+urllib.parse.urlencode({"query":s,"format":"json"}),headers={"User-Agent":"PublicDomainRadar/1.0 (https://publicdomainradar.com)"})
            return json.load(urllib.request.urlopen(r,timeout=120))["results"]["bindings"]
        except Exception as e:
            print("err",e); time.sleep(10)
    return []
tot={}
for nome,c in CLASSI.items():
    s=f'''SELECT ?w ?wLabel ?aLabel ?sl ?img WHERE {{ ?w wdt:P31 wd:{c}; wdt:P577 ?d. FILTER(YEAR(?d)=1931)
    ?w wikibase:sitelinks ?sl. OPTIONAL{{?w wdt:P50 ?a}} OPTIONAL{{?w wdt:P18 ?img}}
    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,it". }} }}'''
    r=q(s)
    for x in r: tot[x["w"]["value"]]=(nome,x["wLabel"]["value"],x.get("aLabel",{}).get("value","-"),int(x["sl"]["value"]),"img" in x)
print("OPERE 1931 TOTALI",len(tot))
for m in (1,3,10): print("con almeno",m,"pagine Wikipedia:",sum(1 for v in tot.values() if v[3]>=m))
print("con immagine P18:",sum(1 for v in tot.values() if v[4]))
print("senza autore:",sum(1 for v in tot.values() if v[2]=="-"))
for v in sorted(tot.values(),key=lambda v:-v[3])[:25]: print(v)
