#!/usr/bin/env python3
"""Library of Congress (USA), diagnosi 2: indici del catalogo SRU (lx2.loc.gov) con l'intestazione ufficiale presa da
id.loc.gov tramite il codice LC di Wikidata (P244). Solo lettura. Scrive docs/campione-loc/diagnosi.json."""
import json, pathlib, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from arricchisci import sparql  # noqa: E402
UA = "publicdomain-radar/1.0 (https://github.com/mnovali90-byte/publicdomain)"
SRU = "http://lx2.loc.gov:210/LCDB"
def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        t = urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace"); time.sleep(1); return t
    except Exception as e:
        return "ERRORE " + str(e)[:200]
def etichetta(codice):
    t = get(f"https://id.loc.gov/authorities/names/{codice}.json")
    try:
        for x in json.loads(t):
            if x.get("@id", "").endswith("/" + codice) and "http://www.loc.gov/mads/rdf/v1#authoritativeLabel" in x:
                return x["http://www.loc.gov/mads/rdf/v1#authoritativeLabel"][0]["@value"]
    except Exception as e:
        return "ERRORE " + str(e)[:80]
def sru(q, n=0):
    t = get(SRU + "?" + urllib.parse.urlencode({"version": "1.1", "operation": "searchRetrieve", "query": q, "maximumRecords": str(n), "recordSchema": "marcxml"}))
    m = re.search(r"numberOfRecords>(\d+)<", t)
    return (int(m.group(1)) if m else None), (re.findall(r"<diag:message>([^<]+)|<message>([^<]+)", t)[:1]), t
nomi = ["H. G. Wells", "Ray Cummings", "F. W. Harvey", "Hugh Lofting"]
out = {}
for nome in nomi:
    r = sparql(f'SELECT ?a ?v ?n ?m WHERE {{ ?a rdfs:label "{nome}"@en ; wdt:P244 ?v ; wdt:P569 ?n ; wdt:P570 ?m . }} LIMIT 3')
    if not r:
        out[nome] = "nessun codice"; continue
    cod = r[0]["v"]["value"]; lab = etichetta(cod)
    x = {"qid": r[0]["a"]["value"].rsplit("/", 1)[-1], "codice": cod, "intestazione": lab}
    for k, q in {"personalName": f'bath.personalName="{lab}"', "creator": f'dc.creator="{lab}"',
                 "personalName+eng": f'bath.personalName="{lab}" and dc.language=eng',
                 "personalName+eng2": f'bath.personalName="{lab}" and bath.language=eng',
                 "personalName+2000": f'bath.personalName="{lab}" and dc.date>1999',
                 "name": f'bath.name="{lab}"'}.items():
        n, msg, _ = sru(q); x[k] = [n, msg]
    n, _, t = sru(f'bath.personalName="{lab}"', 40)
    come = []
    for rec in re.findall(r"<record xmlns[^>]*>(.*?)</record>", t, re.S):
        campi = [tag for tag, corpo in re.findall(r'tag="(\d{3})"[^>]*>(.*?)</datafield>', rec, re.S)
                 if tag in ("100", "700", "600", "800", "400", "245") and lab.split(",")[0] in corpo]
        lang = (re.findall(r'tag="008">([^<]*)<', rec) or [""])[0][35:38]
        come.append(f"{lang} {','.join(campi)}")
    x["come_collegato_40"] = come
    out[nome] = x
pathlib.Path(__file__).resolve().parent.parent.joinpath("docs", "campione-loc", "diagnosi.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
