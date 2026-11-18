#!/usr/bin/env python3
"""Library of Congress, diagnosi 3: accenti nella ricerca e pagine dei risultati. Solo lettura."""
import json, pathlib, re, time, unicodedata, urllib.parse, urllib.request
UA = "publicdomain-radar/1.0 (https://github.com/mnovali90-byte/publicdomain)"
SRU = "http://lx2.loc.gov:210/LCDB"
def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA}); t = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "replace"); time.sleep(2); return t
    except Exception as e:
        return "ERRORE " + str(e)[:150]
def q(lab, start=1, n=0):
    t = get(SRU + "?" + urllib.parse.urlencode({"version": "1.1", "operation": "searchRetrieve", "query": f'bath.personalName="{lab}"', "maximumRecords": str(n), "startRecord": str(start), "recordSchema": "marcxml"}))
    m = re.search(r"numberOfRecords>(\d+)<", t)
    return (int(m.group(1)) if m else t[:150]), len(re.findall(r"<record xmlns", t)), len(re.findall(r"<zs:record>", t)), re.findall(r"nextRecordPosition>(\d+)<", t)
sa = lambda s: "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
out = {}
for lab in ["Riotor, Léon, 1865-1946", "Kōda, Rohan, 1867-1947", "Velimirović, Nikolaj, 1880-1956", "Zápotocký, Antonín, 1884-1957", "Preissová, Gabriela Sekerová, 1862-1946"]:
    out[lab] = {"accenti": q(lab), "senza accenti": q(sa(lab)), "NFD": q(unicodedata.normalize("NFD", lab))}
lg = "Le Gallienne, Richard, 1866-1947"
out["pagine Le Gallienne"] = [q(lg, s, 50) for s in (1, 51, 101)]
out["pagine Le Gallienne 25"] = [q(lg, s, 25) for s in (1, 26, 51, 76, 101)]
pathlib.Path(__file__).resolve().parent.parent.joinpath("docs", "campione-loc", "diagnosi.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
