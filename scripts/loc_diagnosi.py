#!/usr/bin/env python3
"""Library of Congress (USA): diagnosi dei servizi prima di costruire qualcosa. Solo lettura.
Prova: 1) codice LC dell'autore da Wikidata (P244) -> intestazione ufficiale da id.loc.gov; 2) catalogo LC via SRU
(lx2.loc.gov) cercando quell'intestazione; 3) API JSON di loc.gov. Scrive docs/campione-loc/diagnosi.json."""
import json, pathlib, sys, time, urllib.parse, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from arricchisci import sparql  # noqa: E402
UA = "publicdomain-radar/1.0 (https://github.com/mnovali90-byte/publicdomain)"
def get(url, n=4000):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        t = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace"); time.sleep(1); return t[:n]
    except Exception as e:
        return "ERRORE " + str(e)[:200]
qs = ["Q42511", "Q38757", "Q273055", "Q358442"]   # H. G. Wells, Brecht, Ray Cummings, F. W. Harvey
cod = {}
for b in sparql("SELECT ?a ?v WHERE { VALUES ?a { " + " ".join("wd:" + q for q in qs) + " } ?a wdt:P244 ?v }"):
    cod[b["a"]["value"].rsplit("/", 1)[-1]] = b["v"]["value"]
out = {"codici": cod}
for q, c in cod.items():
    out[f"idloc {q}"] = get(f"https://id.loc.gov/authorities/names/{c}.json", 3000)
    out[f"idloc label {q}"] = get(f"https://id.loc.gov/authorities/names/{c}.html", 600)
w = cod.get("Q42511")
sru = "http://lx2.loc.gov:210/LCDB?" + urllib.parse.urlencode({"version": "1.1", "operation": "searchRetrieve",
      "query": 'bath.personalName="Wells, H. G. (Herbert George), 1866-1946"', "maximumRecords": "2", "recordSchema": "marcxml"})
out["sru_lx2"] = get(sru, 5000)
out["sru_lx2_https"] = get(sru.replace("http://lx2.loc.gov:210", "https://lx2.loc.gov:210"), 2000)
out["locgov_json"] = get("https://www.loc.gov/books/?" + urllib.parse.urlencode({"fa": "contributor:wells, h. g. (herbert george)", "fo": "json", "c": "1"}), 4000)
pathlib.Path(__file__).resolve().parent.parent.joinpath("docs", "campione-loc", "diagnosi.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
