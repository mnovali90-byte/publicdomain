#!/usr/bin/env python3
"""Fase 2, prova con i titoli: per ogni autore del campione confronta i titoli collegati alle schede SBN
(quella indicata a mano, quelle del sistema, quelle trovate per nome) con le opere che Wikidata gli attribuisce.
Il nome dice «si chiama così», i titoli dicono «è lui». Scrive docs/campione/sbn-titoli.json.
Ricerche extra chieste da Marco: Hans Ganz (scheda TO0V064787) e Alois Čáp (anche senza accenti)."""
import json, pathlib, re, sys, time, unicodedata
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sbn  # noqa: E402
from arricchisci import sparql  # noqa: E402

RADICE = pathlib.Path(__file__).resolve().parent.parent
C = RADICE / "docs" / "campione"
base = json.loads(sorted(C.glob("sbn-base-*.json"))[-1].read_text(encoding="utf-8"))["autori"]
extra = json.loads((C / "sbn-prove-extra.json").read_text(encoding="utf-8"))
import csv
righe = {r["qid"]: r for r in csv.DictReader(open(C / "sbn-campione.csv", encoding="utf-8"))}
URI = "http://triplestore.iccu.sbn.it/resource/Agent/"
STOP = set("the a an of and il lo la i gli le di del della e ed un una de des du le la les et der die das und von ein eine el los las y en".split())

def parole(t):
    t = unicodedata.normalize("NFKD", t or ""); t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return {p for p in re.findall(r"[a-z0-9]{3,}", t) if p not in STOP}

def titoli_sbn(scheda):
    u = scheda if scheda.startswith("http") else URI + scheda
    q = (f"SELECT DISTINCT ?t ?l WHERE {{ ?w <{sbn.BF}contribution> ?c . ?c <{sbn.BF}agent> <{u}> . "
         f"?w <{sbn.BF}title> ?tt . ?tt <{sbn.BF}mainTitle> ?t . OPTIONAL {{ ?w <{sbn.BF}language> ?lg . ?lg <{sbn.VAL}> ?l }} }} LIMIT 40")
    try:
        r = sbn.interroga(q)
    except Exception as e:
        return {"errore": str(e)[:80]}
    time.sleep(sbn.PAUSA)
    lab = sbn.interroga(f"SELECT ?l WHERE {{ <{u}> <{sbn.LAB}> ?l }} LIMIT 3"); time.sleep(sbn.PAUSA)
    return {"etichetta": [x["l"]["value"] for x in lab], "titoli": sorted({x["t"]["value"][:120] for x in r}),
            "lingue": sorted({x["l"]["value"].rsplit("/", 1)[-1] for x in r if "l" in x})}

def opere_wd(q):
    r = sparql(f"""SELECT DISTINCT ?l WHERE {{ ?w wdt:P50 wd:{q} . ?w rdfs:label ?l .
      FILTER(LANG(?l) IN ("it","en","fr","de","es","cs","ca","pl","pt","mul")) }} LIMIT 300""")
    time.sleep(1)
    return sorted({x["l"]["value"] for x in r})

out = {}
for q, a in base.items():
    rg = righe[q]
    schede = set(rg["manuale_schede_corrette"].split()) | {u.rsplit("/", 1)[-1] for u in a["sistema"].get("schede", [])}
    for f, lista in (extra.get(q, {}).get("ricerche") or {}).items():
        for sc, et in lista[:4]:
            if sc != "errore" and parole(a["nome"].split()[-1]) & parole(et):
                schede.add(sc)
    if a["nome"] == "Hans Ganz":
        schede.add("IT-ICCU-TO0V-064787")
    wd = opere_wd(q)
    pw = [parole(t) for t in wd]
    ris = {}
    for s in sorted(schede):
        if not s.startswith("IT-ICCU") and not s.startswith("CNMN"):
            continue
        t = titoli_sbn(s)
        if "titoli" in t:
            comuni = [ti for ti in t["titoli"] if any(len(parole(ti) & p) >= max(1, min(2, len(p))) for p in pw if p)]
            t["titoli_che_tornano"] = comuni
        ris[s] = t
    out[q] = {"nome": a["nome"], "anni": f'{(a["nascita"] or "?")[:4]}-{(a["morte"] or "?")[:4]}',
              "esito_manuale": rg["manuale_esito"], "opere_wikidata": wd[:40], "n_opere_wikidata": len(wd), "schede": ris}
    print(a["nome"], {s: (len(v.get("titoli", [])), len(v.get("titoli_che_tornano", []))) for s, v in ris.items()}, flush=True)

# Alois Čáp: ricerca con e senza accenti
cap = {}
for forma in ("Čáp", "Cap", "Čáp, Alois", "Alois"):
    try:
        r = sbn.interroga(f'SELECT DISTINCT ?a ?l WHERE {{ ?a <{sbn.LAB}> ?l . ?l bif:contains "\'{forma.split(",")[0]}\'" . '
                          f'FILTER(CONTAINS(STR(?a), "/resource/Agent/")) FILTER(CONTAINS(LCASE(STR(?l)), "alois")) }} LIMIT 30')
        cap[forma] = [(x["a"]["value"].rsplit("/", 1)[-1], x["l"]["value"]) for x in r]
    except Exception as e:
        cap[forma] = str(e)[:80]
    time.sleep(sbn.PAUSA)
out["_cap"] = cap
(C / "sbn-titoli.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
