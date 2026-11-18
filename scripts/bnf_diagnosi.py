#!/usr/bin/env python3
"""Diagnosi dei servizi BnF prima di costruire il campione (solo lettura). Scrive docs/campione-bnf/diagnosi.json."""
import json, pathlib, time, urllib.parse, urllib.request
UA = "publicdomain-radar/1.0 (https://github.com/mnovali90-byte/publicdomain)"
SRU = "https://catalogue.bnf.fr/api/SRU"
def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        t = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace"); time.sleep(1); return t[:6000]
    except Exception as e:
        return "ERRORE " + str(e)[:200]
def sru(q, schema="dublincore", n=3):
    return get(SRU + "?" + urllib.parse.urlencode({"version": "1.2", "operation": "searchRetrieve", "query": q, "recordSchema": schema, "maximumRecords": str(n)}))
out = {
 # Brecht: P268 = 11893382s (codice BnF di Wikidata)
 "aut_persistentid": sru('aut.persistentid all "ark:/12148/cb11893382s"', "unimarc", 1),
 "aut_recordid": sru('aut.recordid any "11893382"', "unimarc", 1),
 "aut_accesspoint": sru('aut.accesspoint all "Brecht Bertolt"', "dublincore", 3),
 "aut_accesspoint_intermarc": sru('aut.accesspoint all "Shimoni David"', "intermarc", 3),
 "bib_author2bib_dc": sru('bib.author2bib all "11893382" and bib.language any "fre"', "dublincore", 2),
 "bib_author2bib_unimarc": sru('bib.author2bib all "11893382" and bib.language any "fre"', "unimarc", 1),
 "explain": get(SRU + "?version=1.2&operation=explain")[:6000],
 "databnf": get("https://data.bnf.fr/sparql?" + urllib.parse.urlencode({"query": 'PREFIX foaf: <http://xmlns.com/foaf/0.1/> SELECT ?p ?o WHERE { <http://data.bnf.fr/ark:/12148/cb11893382s#about> ?p ?o } LIMIT 40', "format": "application/sparql-results+json"})),
}
pathlib.Path(__file__).resolve().parent.parent.joinpath("docs", "campione-bnf", "diagnosi.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
