#!/usr/bin/env python3
"""Misura un metodo di riconoscimento sul campione SBN congelato (docs/campione), confrontandolo con gli esiti
controllati a mano. Uso: python scripts/campione_valuta.py fase3  -> docs/campione/sbn-fase3.json"""
import collections, json, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import riconosci_sbn  # noqa: E402

RADICE = pathlib.Path(__file__).resolve().parent.parent
C = RADICE / "docs" / "campione"
nome_prova = sys.argv[1] if len(sys.argv) > 1 else "prova"
base = json.loads(sorted(C.glob("sbn-base-*.json"))[-1].read_text(encoding="utf-8"))["autori"]
titoli = json.loads((C / "sbn-titoli.json").read_text(encoding="utf-8"))
esiti = {int(k): v for k, v in json.loads((C / "sbn-esiti.json").read_text(encoding="utf-8")).items()}
paesi = {}
for f in (RADICE / "data").glob("*[0-9][0-9][0-9][0-9].json"):
    if not f.name.startswith(("us-", "anniversari-")):
        for a in json.loads(f.read_text(encoding="utf-8"))["autori"]:
            paesi.setdefault(a["wikidata"], a.get("paesi") or [])

def breve(u):
    return u.rsplit("/", 1)[-1].replace("IT-ICCU-", "").replace("-", "")

righe, conta = [], collections.Counter()
for i, (q, a) in enumerate(base.items(), 1):
    e, sch, vecchio, nota = esiti[i]
    giuste = set(sch.split())
    w = a["wikidata"]
    autore = {"nome": a["nome"], "nascita": a.get("nascita"), "morte": a.get("morte"), "p396": w.get("p396", []),
              "viaf": w.get("viaf", []), "alias": (w.get("pseudonimi") or []) + (w.get("alias") or []),
              "opere": (titoli.get(q) or {}).get("opere_wikidata", []), "paesi": paesi.get(q, [])}
    t0 = time.time()
    try:
        r = riconosci_sbn.riconosci(autore)
    except Exception as ex:
        r = {"stato": "errore", "errore": str(ex)[:120], "schede": [], "prove": {}}
    nuove = {breve(u) for u in r["schede"]}
    etich = " ".join(r.get("prove", {}).values()).lower()
    if e == "C":
        if not giuste:   # confermato senza codice (Saldías): si controlla l'etichetta
            esito = "trovato" if nuove and a["nome"].split()[-1].lower().replace("í", "i") in etich else ("mancato" if not nuove else "scheda diversa")
        elif nuove & giuste:
            esito = "trovato" + (" con schede in più" if nuove - giuste else "")
        else:
            esito = "scheda diversa" if nuove else "mancato"
    elif e == "A":
        esito = "falso positivo" if nuove else "giusto (assente)"
    else:
        esito = "irrisolto: " + ("collegato" if nuove else "niente")
    conta[esito.split(":")[0] if e == "I" else esito] += 1
    righe.append({"n": i, "qid": q, "nome": a["nome"], "manuale": e, "prima": vecchio, "dopo": esito, "stato": r["stato"],
                  "metodo": r.get("metodo"), "schede": sorted(nuove), "in_piu": sorted(nuove - giuste) if giuste else [],
                  "prove": r.get("prove", {}), "ambigue": r.get("ambigue", {}), "secondi": round(time.time() - t0, 1)})
    print(f"{i:3} {a['nome'][:34]:34} {e} prima={vecchio:2} dopo={esito} [{r.get('metodo')}]", flush=True)
(C / f"sbn-{nome_prova}.json").write_text(json.dumps({"prova": nome_prova, "conteggi": conta, "autori": righe}, ensure_ascii=False, indent=1), encoding="utf-8")
print("CONTEGGI", dict(conta))
