"""Diagnosi (non cambia il sito): quante voci in più entrerebbero negli anniversari 2027 aggiungendo il mestiere
«writer» (Q36180) alla lista OCC di scripts/anniversari.py, e cosa succede abbassando la soglia di notorietà
(numero di pagine Wikipedia, oggi 30).

Stessa domanda a Wikidata dello script (nascite e morti per ogni età tonda, stessa esclusione dei mestieri non
letterari senza libri noti, stessa regola «una sola data nell'anno»), ma con Q36180 e soglia 15, poi si contano
le varianti. Scrive docs/stima-sito/anniv-writer.json e docs/stima-sito/anniv-writer.md.
"""
import json, random, sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import anniversari as A

ANNO = 2027
OUT = pathlib.Path("docs/stima-sito")
OCC_OGGI = set(A.OCC.replace("wd:", "").split())
OCC_TUTTI = A.OCC + " wd:Q36180"
NOMI = ["Nazım Hikmet", "Josephine Tey", "Albert Uderzo", "Federico De Roberto", "Paul Éluard", "Carlo Levi",
        "Clarice Lispector", "Oğuz Atay", "Carlos Drummond de Andrade", "W. S. Merwin"]


def domanda(prop, y):
    a, b = A.estremi(y)
    return A.sparql(f'''SELECT ?p ?pLabel ?o ?d ?pr ?cal ?sl ?bad WHERE {{ VALUES ?o {{ {OCC_TUTTI} }}
 ?p wdt:P106 ?o; wdt:P31 wd:Q5; p:{prop}/psv:{prop} [wikibase:timeValue ?d; wikibase:timePrecision ?pr; wikibase:timeCalendarModel ?cal].
 FILTER(?d>={a} && ?d<{b}) ?p wikibase:sitelinks ?sl. FILTER(?sl>=15)
 FILTER NOT EXISTS {{ ?p wdt:{prop} ?altra. FILTER(?altra<{a} || ?altra>={b}) }}
 OPTIONAL {{ ?p wdt:P106 ?bad. VALUES ?bad {{ {A.NON_LETT} }} FILTER NOT EXISTS {{ ?lib wdt:P50 ?p; wikibase:sitelinks ?s2. FILTER(?s2>=10) }} }}
 SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}''')


def main():
    persone = {}   # (tipo, qid) -> dati
    falliti = []
    for eta in A.ETA:
        for tipo, prop in (("nascita", "P569"), ("morte", "P570")):
            r = domanda(prop, ANNO - eta)
            time.sleep(1)
            if r is None:
                falliti.append((tipo, eta)); continue
            for x in r:
                k = (tipo, A.qid(A.g(x, "p")))
                v = persone.setdefault(k, {"tipo": tipo, "qid": k[1], "nome": A.g(x, "pLabel"), "anni": eta, "anno": ANNO - eta,
                                           "pagine": int(A.g(x, "sl")), "occ": set(), "giorni": set(), "bad": False})
                v["occ"].add(A.qid(A.g(x, "o")))
                v["giorni"].add(A.giorno(x))
                if x.get("bad"):
                    v["bad"] = True
    voci = []
    for v in persone.values():
        if v["bad"] or not v["nome"] or v["nome"].startswith("Q"):
            continue
        gs = {g for g in v["giorni"] if g}
        v["mese"], v["giorno"] = next(iter(gs)) if len(gs) == 1 else (None, None)
        v["solo_writer"] = not (v["occ"] & OCC_OGGI)
        v["occ"] = sorted(v["occ"]); del v["giorni"], v["bad"]
        voci.append(v)
    oggi = [v for v in voci if not v["solo_writer"] and v["pagine"] >= 30]
    piu_w30 = [v for v in voci if v["solo_writer"] and v["pagine"] >= 30]
    piu_w20 = [v for v in voci if v["solo_writer"] and 20 <= v["pagine"] < 30]
    piu_vecchi_20 = [v for v in voci if not v["solo_writer"] and 20 <= v["pagine"] < 30]
    def per_mese(l):
        c = {str(m): 0 for m in range(1, 13)}; c["senza giorno"] = 0
        for v in l:
            c[str(v["mese"]) if v["mese"] else "senza giorno"] += 1
        return c
    random.seed(20261119)
    esempi = random.sample(piu_w30, min(10, len(piu_w30)))
    esempi20 = random.sample(piu_w20, min(10, len(piu_w20)))
    # i dieci nomi della segnalazione: perché mancano
    nomi = {}
    for n in NOMI:
        r = A.sparql(f'''SELECT ?p ?sl ?oLabel ?n ?m WHERE {{ ?p rdfs:label "{n}"@en; wdt:P31 wd:Q5; wikibase:sitelinks ?sl.
          OPTIONAL {{ ?p wdt:P106 ?o }} OPTIONAL {{ ?p wdt:P569 ?n }} OPTIONAL {{ ?p wdt:P570 ?m }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}''') or []
        if not r:
            nomi[n] = None; continue
        p = A.qid(A.g(r[0], "p"))
        rr = [x for x in r if A.qid(A.g(x, "p")) == p]
        nomi[n] = {"qid": p, "pagine": int(A.g(rr[0], "sl")), "mestieri": sorted({A.g(x, "oLabel") for x in rr if A.g(x, "oLabel")}),
                   "nascite": sorted({(A.g(x, "n") or "")[:10] for x in rr if A.g(x, "n")}), "morti": sorted({(A.g(x, "m") or "")[:10] for x in rr if A.g(x, "m")}),
                   "trovato_qui": [f'{v["tipo"]} {v["anni"]} anni, {v["pagine"]} pagine, solo writer: {v["solo_writer"]}' for v in voci if v["qid"] == p]}
        time.sleep(1)
    out = {"anno": ANNO, "falliti": falliti, "oggi_n": len(oggi), "oggi_per_mese": per_mese(oggi),
           "piu_writer_soglia30_n": len(piu_w30), "piu_writer_soglia30_per_mese": per_mese(piu_w30),
           "piu_writer_soglia20_n": len(piu_w20), "piu_writer_soglia20_per_mese": per_mese(piu_w20),
           "piu_mestieri_attuali_soglia20_n": len(piu_vecchi_20),
           "esempi_soglia30": esempi, "esempi_soglia20": esempi20, "dieci_nomi": nomi,
           "tutti_writer_soglia30": sorted(piu_w30, key=lambda v: -v["pagine"])}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "anniv-writer.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in out if not k.startswith("tutti")}, ensure_ascii=False, indent=1)[:6000])


if __name__ == "__main__":
    main()
