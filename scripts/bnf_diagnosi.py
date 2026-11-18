#!/usr/bin/env python3
"""Diagnosi dei servizi BnF prima di costruire il campione (solo lettura). Scrive docs/campione-bnf/diagnosi.json."""
import json, pathlib, time, urllib.parse, urllib.request
UA = "publicdomain-radar/1.0 (https://github.com/mnovali90-byte/publicdomain)"
SRU = "https://catalogue.bnf.fr/api/SRU"
def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        t = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace"); time.sleep(1); return t[:20000]
    except Exception as e:
        return "ERRORE " + str(e)[:200]
def sru(q, schema="dublincore", n=3):
    return get(SRU + "?" + urllib.parse.urlencode({"version": "1.2", "operation": "searchRetrieve", "query": q, "recordSchema": schema, "maximumRecords": str(n)}))
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from arricchisci import sparql
cod = {b["a"]["value"].rsplit("/", 1)[-1]: b["v"]["value"] for b in sparql("SELECT ?a ?v WHERE { VALUES ?a { wd:Q38757 wd:Q1374519 } ?a wdt:P268 ?v }")}
br = cod.get("Q38757", "")
rid = "".join(c for c in br if c.isdigit())[:8]
out = {"codici": cod, "explain": get(SRU + "?version=1.2&operation=explain")}
for schema in ("unimarcXchange", "intermarcXchange", "unimarcxchange", "dublincore"):
    for q in (f'aut.persistentid all "ark:/12148/cb{br}"', f'aut.recordid any "{rid}"', f'aut.ark all "ark:/12148/cb{br}"',
              'aut.accesspoint all "Brecht Bertolt"', 'aut.anywhere all "Shimoni David"'):
        out[f"{schema} | {q}"] = sru(q, schema, 1)[:3000]
out["author2bib"] = sru(f'bib.author2bib all "{rid}" and bib.language any "fre"', "dublincore", 2)[:3000]
out["author2bib_n_tutte_lingue"] = sru(f'bib.author2bib all "{rid}"', "dublincore", 0)[:1200]
pathlib.Path(__file__).resolve().parent.parent.joinpath("docs", "campione-bnf", "diagnosi.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
