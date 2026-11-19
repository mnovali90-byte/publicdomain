"""Prova alla cieca (19/11/2026, richiesta di Marco): rifacciamo la lista USA del 2025 (libri del 1929) con il nostro
metodo, SENZA usare la Duke, e solo dopo la confrontiamo con la lista Duke del 2025.

Come:
  1. lista: stessa query Wikidata di scripts/opere.py (opere con prima pubblicazione nel 1929, almeno 2 Wikipedia);
  2. verifica dell'anno: stesse fonti e stesse regole di scripts/verifica_anni_usa.py, tranne la Duke
     (registro del copyright, BnF, K10plus, Open Library, Library of Congress);
  3. solo alla fine si apre data/storico/duke.json e si confronta.
Scrive docs/stima-sito/prova-cieca-duke-2025.json.
"""
import json, re, sys, time
from collections import Counter
from pathlib import Path

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "scripts"))
import opere                     # noqa: E402
import verifica_anni_usa as vu   # noqa: E402

ANNO, P = 2025, 1929
BUDGET = 48 * 60


def main():
    inizio = time.time()
    # 1. la lista, come per il 2027
    ops = opere.opere_anno(P)
    ops.sort(key=lambda o: -o["pagine"])
    ops = ops[:opere.MAX_OPERE]
    print("opere del 1929 da Wikidata:", len(ops))
    # 2. la verifica, senza Duke
    vu.CCE_FILE = {1928: "1928/1928_v25.xml", 1929: "1929/1929_v26.xml", 1930: "1930/cc271libr_001-2321.xml"}
    idx = vu.indice_cce()
    orig = vu.originali([o["qid"] for o in ops])
    esiti = {}
    for o in ops:
        if time.time() - inizio > BUDGET:
            break
        cognomi = [vu.parole(a["nome"])[-1] for a in o.get("autori", []) if vu.parole(a["nome"])]
        trovati = {"cce": vu.cce(idx, o, cognomi)}
        if o["qid"] in orig and cognomi and P not in trovati.values():
            lg, titolo = orig[o["qid"]]
            if lg == "fr":
                trovati["bnf"] = vu.bnf(titolo, cognomi[0])[0]
            else:
                trovati["k10plus"] = vu.k10plus(titolo, cognomi[0], P)[0]
        if P not in trovati.values():
            trovati["openlibrary"] = vu.va.open_library(vu.va_riga(o))[1]
            if trovati["openlibrary"] != P:
                trovati["loc"] = vu.va.library_of_congress(vu.va_riga(o))[1]
        esiti[o["qid"]] = list(vu.decidi(trovati, P)) + [{k: v for k, v in trovati.items() if v}]
        time.sleep(0.3)
    print("controllate:", len(esiti), Counter(e[0] for e in esiti.values()))

    # 3. solo ora la Duke
    dk = json.loads((R / "data" / "storico" / "duke.json").read_text(encoding="utf-8"))[str(ANNO)]["libri"]
    per_qid = {o["qid"]: o for o in ops}
    confronto = []
    for l in dk:
        q = (l.get("wd") or {}).get("qid")
        o = per_qid.get(q)
        if not o:   # Duke senza Wikidata: si cerca per titolo e cognome
            tw = vu.parole(l["titolo"])[:3]
            cg = vu.parole(l["autore"])[-1:]
            o = next((x for x in ops if vu.parole(x["titolo"])[:3] == tw and
                      any(cg[0] in vu.parole(a["nome"]) for a in x.get("autori", []))), None) if tw and cg else None
        e = esiti.get(o["qid"]) if o else None
        confronto.append({"duke": f'{l["titolo"]} — {l["autore"]}', "nella_nostra_lista": bool(o),
                          "nostro_esito": e[0] if e else None, "fonte": e[2] if e else None,
                          "perche_manca": None if o else "non è in Wikidata come opera del 1929 con almeno 2 Wikipedia"})
    trovati_duke = sum(1 for c in confronto if c["nella_nostra_lista"])
    confermati_duke = sum(1 for c in confronto if c["nostro_esito"] == "ok")
    out = {
        "anno": ANNO, "anno_pubblicazione": P,
        "nostra_lista": len(ops), "controllate": len(esiti),
        "nostri_esiti": dict(Counter(e[0] for e in esiti.values())),
        "nostre_conferme_per_fonte": dict(Counter(e[2] for e in esiti.values() if e[0] == "ok")),
        "duke_libri": len(dk), "duke_nella_nostra_lista": trovati_duke, "duke_confermati_da_noi": confermati_duke,
        "confronto": confronto,
        "nostri_confermati_non_in_duke_primi_40": [
            [o["titolo"], ", ".join(a["nome"] for a in o.get("autori", [])), o["pagine"], esiti[o["qid"]][2]]
            for o in ops if o["qid"] in esiti and esiti[o["qid"]][0] == "ok"
            and o["qid"] not in {(l.get("wd") or {}).get("qid") for l in dk}][:40],
        "nostri_prima": [[o["titolo"], esiti[o["qid"]][1], esiti[o["qid"]][2]] for o in ops
                         if o["qid"] in esiti and esiti[o["qid"]][0] == "prima"],
    }
    (R / "docs" / "stima-sito" / "prova-cieca-duke-2025.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k not in ("confronto", "nostri_confermati_non_in_duke_primi_40")}, ensure_ascii=False))
    for c in confronto:
        print(c)


if __name__ == "__main__":
    main()
