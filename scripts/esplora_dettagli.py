#!/usr/bin/env python3
"""Dettagli delle notizie SBN di alcune schede (editore, luogo, pagine, responsabilità): per controllare a mano
che un titolo generico sia accompagnato da altri elementi coerenti. Solo lettura. Scrive docs/esplora-ambigui/dettagli.json."""
import json, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sbn  # noqa: E402
SCHEDE = ["IT-ICCU-LO1V-312466", "IT-ICCU-IEIV-076461", "IT-ICCU-TO0V-080789", "IT-ICCU-CSAV-033853"]
out = {}
for s in SCHEDE:
    u = "http://triplestore.iccu.sbn.it/resource/Agent/" + s
    opere = sbn.interroga(f"SELECT DISTINCT ?w WHERE {{ ?w <{sbn.BF}contribution> ?c . ?c <{sbn.BF}agent> <{u}> }} LIMIT 10")
    time.sleep(sbn.PAUSA)
    out[s] = {}
    for o in opere:
        w = o["w"]["value"]
        r = sbn.interroga(f"""SELECT ?p ?v WHERE {{ {{ <{w}> ?p ?v }} UNION {{ <{w}> <{sbn.BF}hasInstance> ?i . ?i ?p ?v }}
          UNION {{ <{w}> <{sbn.BF}hasInstance> ?i . ?i <{sbn.BF}provisionActivity> ?pa . ?pa ?p ?x . OPTIONAL {{ ?x <{sbn.LAB}> ?lx }} BIND(COALESCE(?lx, ?x) AS ?v) }}
          UNION {{ <{w}> <{sbn.BF}contribution> ?c . ?c ?p ?x . OPTIONAL {{ ?x <{sbn.LAB}> ?lx }} BIND(COALESCE(?lx, ?x) AS ?v) }} }} LIMIT 200""")
        time.sleep(sbn.PAUSA)
        out[s][w] = sorted({(x["p"]["value"].rsplit("/", 1)[-1].rsplit("#", 1)[-1], x["v"]["value"][:200]) for x in r})
(pathlib.Path(__file__).resolve().parent.parent / "docs" / "esplora-ambigui" / "dettagli.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
