#!/usr/bin/env python3
"""Prove in più per il controllo a mano del campione SBN: per gli autori senza un codice SBN sicuro,
cerca nel triplestore le schede che contengono TUTTE le parole del nome (non solo il cognome),
e le schede per ogni pseudonimo e alias di Wikidata. Scrive docs/campione/sbn-prove-extra.json."""
import json, pathlib, re, sys, time, unicodedata
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sbn  # noqa: E402

RADICE = pathlib.Path(__file__).resolve().parent.parent
base = json.loads(sorted((RADICE / "docs" / "campione").glob("sbn-base-*.json"))[-1].read_text(encoding="utf-8"))["autori"]

def parole(t):
    t = unicodedata.normalize("NFKD", t or ""); t = "".join(c for c in t if not unicodedata.combining(c))
    return [p for p in re.findall(r"[A-Za-z]{3,}", t)]

def cerca(nome):
    p = parole(nome)
    if not p:
        return []
    cond = " and ".join(f"'{x}'" for x in p[:4])
    try:
        r = sbn.interroga(f'SELECT DISTINCT ?a ?l WHERE {{ ?a <{sbn.LAB}> ?l . ?l bif:contains "{cond}" . '
                          f'FILTER(CONTAINS(STR(?a), "/resource/Agent/")) }} LIMIT 30')
    except Exception as e:
        return [("errore", str(e)[:80])]
    time.sleep(sbn.PAUSA)
    return [(x["a"]["value"].rsplit("/", 1)[-1], x["l"]["value"]) for x in r]

out = {}
for q, a in base.items():
    if any(p["nel_triplestore"] for p in a["p396"]):
        continue
    forme = [a["nome"]] + a["wikidata"].get("pseudonimi", []) + a["wikidata"].get("alias", [])
    viste, ris = set(), {}
    for f in forme:
        k = " ".join(sorted(x.lower() for x in parole(f)))
        if not k or k in viste:
            continue
        viste.add(k)
        ris[f] = cerca(f)
    out[q] = {"nome": a["nome"], "anni": f'{(a["nascita"] or "?")[:4]}-{(a["morte"] or "?")[:4]}', "ricerche": ris}
    print(a["nome"], {f: len(v) for f, v in ris.items()}, flush=True)
(RADICE / "docs" / "campione" / "sbn-prove-extra.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
