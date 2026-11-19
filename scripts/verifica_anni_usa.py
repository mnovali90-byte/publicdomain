"""Verifica dell'anno di uscita per le liste USA del Public Domain Day (data/us-2027.json, data/us-2028.json).

Stesso metodo dello Storico (docs/metodo-anni-opere.md), stesse fonti e stesso ordine:
  1. Duke (liste del Public Domain Day degli anni passati), 2. Open Library, 3. catalogo della Library of Congress.
Per ogni libro si cerca l'edizione più vecchia con lo stesso titolo e lo stesso autore.

Esiti, per la lista del 2027 (libri del 1931):
  - "ok"    : una fonte conferma un'edizione del 1931 → il libro diventa libero negli USA il 1° gennaio 2027;
  - "prima" : una fonte ha un'edizione PIÙ VECCHIA (es. 1929) → il libro è probabilmente già libero, la lista lo mette
              nell'anno sbagliato; se la fonte è la Duke è sicuro;
  - "nd"    : nessuna fonte conferma il 1931 (non trovato, oppure solo edizioni più recenti, che non smentiscono).
Senza «ok» la pagina scrive «anno da confermare».
Scrive data/us-anni-verificati.json {anno_lista: {qid: [esito, anno_trovato, fonte, data, fonti_provate]}}
e il riepilogo in docs/stima-sito/us-anni.json. Gira con stima.yml (passo.txt = verifica_anni_usa).
"""
import json, sys, time
from collections import Counter
from datetime import date
from pathlib import Path

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "storico"))
import verifica_anni as va   # noqa: E402  (funzioni Open Library / Library of Congress dello Storico)

BUDGET = 50 * 60
OGGI = date.today().isoformat()


def riga(o):
    # stesso formato usato dalle funzioni dello Storico: r[1] titolo, r[5] autori [qid, nome, ...]
    return [o["qid"], o["titolo"], None, None, None, [[a["qid"], a["nome"], None, False] for a in o.get("autori", [])]]


def esito(anno, p):
    if anno is None:
        return "nd"
    return "ok" if anno == p else ("prima" if anno < p else "nd")


def main():
    inizio = time.time()
    dk = va.duke()
    f = R / "data" / "us-anni-verificati.json"
    try:
        tutto = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        tutto = {}
    riepilogo = {}
    for lista in ("us-2027.json", "us-2028.json"):
        d = json.loads((R / "data" / lista).read_text(encoding="utf-8"))
        p, chiave = d["anno_pubblicazione"], str(d["anno"])
        fatto = tutto.setdefault(chiave, {})
        for o in d["opere"]:
            q = o["qid"]
            if q in fatto and fatto[q][0] in ("ok", "prima"):
                continue
            if q in dk:
                fatto[q] = [esito(dk[q], p) if dk[q] <= p else "nd", dk[q], "duke", OGGI, ["duke"]]
                if fatto[q][0] != "nd":
                    continue
            provate, trovati = [], []
            if time.time() - inizio > BUDGET:
                break
            _, a = va.open_library(riga(o))
            provate.append("openlibrary")
            if a:
                trovati.append((a, "openlibrary"))
            if not any(x == p for x, _ in trovati):
                _, a = va.library_of_congress(riga(o))
                provate.append("loc")
                if a:
                    trovati.append((a, "loc"))
            buoni = [t for t in trovati if t[0] <= p]
            if buoni:
                a, fonte = min(buoni)
                fatto[q] = [esito(a, p), a, fonte, OGGI, provate]
            else:
                a, fonte = min(trovati) if trovati else (None, None)
                fatto[q] = ["nd", a, fonte, OGGI, provate]
            time.sleep(0.5)
        f.write_text(json.dumps(tutto, ensure_ascii=False, indent=0), encoding="utf-8")
        c = Counter(fatto[o["qid"]][0] for o in d["opere"] if o["qid"] in fatto)
        riepilogo[chiave] = {
            "libri": len(d["opere"]), "controllati": sum(c.values()), "esiti": dict(c),
            "confermati_per_fonte": dict(Counter(fatto[o["qid"]][2] for o in d["opere"]
                                                 if o["qid"] in fatto and fatto[o["qid"]][0] == "ok")),
            "piu_vecchi": [[o["titolo"], fatto[o["qid"]][1], fatto[o["qid"]][2]] for o in d["opere"]
                           if o["qid"] in fatto and fatto[o["qid"]][0] == "prima"],
            "primi_20_per_visite": [[o["titolo"], o.get("visite_en"), fatto.get(o["qid"], ["?"])[0],
                                     fatto.get(o["qid"], [None, None])[1]] for o in d["opere"][:20]],
        }
        print(chiave, riepilogo[chiave]["esiti"], riepilogo[chiave]["confermati_per_fonte"])
    (R / "docs" / "stima-sito" / "us-anni.json").write_text(json.dumps(riepilogo, ensure_ascii=False, indent=1),
                                                            encoding="utf-8")


if __name__ == "__main__":
    main()
