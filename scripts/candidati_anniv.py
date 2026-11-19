"""Lista da rivedere a mano per il calendario anniversari 2027 (non cambia il sito).

Rete larga: nascite e morti con anniversario tondo nel 2027 di chi su Wikidata ha un mestiere letterario,
compreso «writer» (Q36180), con almeno 15 pagine Wikipedia, SENZA l'esclusione automatica di chi ha anche altri
mestieri. Poi per ognuno il verdetto della regola già verificata per la lista principale (scripts/regola_lista.py:
mestiere letterario nella descrizione di Wikidata), solo come aiuto: decide Marco.

Scrive docs/stima-sito/anniv-candidati.json e docs/stima-sito/anniv-candidati.md (un elenco per mese, con fonte:
la scheda Wikidata della persona, dove sta la data).
"""
import json, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import anniversari as A
import regola_lista as R

ANNO = 2027
OUT = pathlib.Path("docs/stima-sito")
OCC = A.OCC + " wd:Q36180"
PROF = {"Q6625963": "romanziere", "Q49757": "poeta", "Q214917": "drammaturgo", "Q11774202": "saggista"}
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]


def domanda(prop, y):
    a, b = A.estremi(y)
    return A.sparql(f'''SELECT ?p ?pLabel ?pit ?desc ?o ?d ?pr ?cal ?sl WHERE {{ VALUES ?o {{ {OCC} }}
 ?p wdt:P106 ?o; wdt:P31 wd:Q5; p:{prop}/psv:{prop} [wikibase:timeValue ?d; wikibase:timePrecision ?pr; wikibase:timeCalendarModel ?cal].
 FILTER(?d>={a} && ?d<{b}) ?p wikibase:sitelinks ?sl. FILTER(?sl>=15)
 FILTER NOT EXISTS {{ ?p wdt:{prop} ?altra. FILTER(?altra<{a} || ?altra>={b}) }}
 OPTIONAL {{ ?p rdfs:label ?pit FILTER(LANG(?pit)="it") }} OPTIONAL {{ ?p schema:description ?desc FILTER(LANG(?desc)="en") }}
 SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}''')


def main():
    cal = json.loads(pathlib.Path("data/anniversari-2027.json").read_text(encoding="utf-8"))["voci"]
    nel_cal = {(v["tipo"], v["qid"]) for v in cal}
    per, falliti = {}, []
    for eta in A.ETA:
        for tipo, prop in (("nascita", "P569"), ("morte", "P570")):
            r = domanda(prop, ANNO - eta)
            time.sleep(1)
            if r is None:
                falliti.append(f"{tipo} {eta}"); continue
            for x in r:
                k = (tipo, A.qid(A.g(x, "p")))
                v = per.setdefault(k, {"tipo": tipo, "qid": k[1], "nome": A.g(x, "pit") or A.g(x, "pLabel"), "desc": A.g(x, "desc") or "",
                                       "anni": eta, "anno": ANNO - eta, "pagine": int(A.g(x, "sl")), "occ": set(), "giorni": set()})
                v["occ"].add(A.qid(A.g(x, "o")))
                v["giorni"].add(A.giorno(x))
    voci = []
    for v in per.values():
        if not v["nome"] or v["nome"].startswith("Q"):
            continue
        gs = {g for g in v["giorni"] if g}
        v["mese"], v["giorno"] = next(iter(gs)) if len(gs) == 1 else (None, None)
        v["scrittore"] = R.scrittore({"professioni": [PROF[o] for o in v["occ"] if o in PROF]}, v["desc"])
        v["gia_nel_calendario"] = (v["tipo"], v["qid"]) in nel_cal
        v["occ"] = sorted(v["occ"]); del v["giorni"]
        voci.append(v)
    voci.sort(key=lambda v: ((v["mese"] or 13), -v["pagine"]))
    nuovi = [v for v in voci if not v["gia_nel_calendario"]]
    out = {"anno": ANNO, "falliti": falliti, "totale": len(voci), "gia_nel_calendario": len(voci) - len(nuovi),
           "nuovi": len(nuovi), "nuovi_scrittori_per_regola": sum(v["scrittore"] for v in nuovi), "voci": voci}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "anniv-candidati.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    righe = [f"# Candidati anniversari {ANNO} da rivedere a mano", "",
             f"Rete larga da Wikidata: mestieri letterari compreso «writer», almeno 15 pagine Wikipedia, nascite e morti con "
             f"anniversario tondo. Fuori dal calendario attuale: **{len(nuovi)}**, di cui {out['nuovi_scrittori_per_regola']} "
             f"scrittori secondo la regola della lista principale (✓). Fonte di ogni data: la scheda Wikidata linkata.", ""]
    for m in list(range(1, 13)) + [None]:
        lista = [v for v in nuovi if v["mese"] == m]
        if not lista:
            continue
        righe += [f"## {MESI[m - 1] if m else 'giorno non noto'} ({len(lista)})", "",
                  "| regola | data | chi | anniversario | pagine | descrizione Wikidata |", "|---|---|---|---|---|---|"]
        for v in lista:
            data = f"{v['giorno']}/{v['mese']}/{v['anno']}" if v["mese"] else str(v["anno"])
            righe.append(f"| {'✓' if v['scrittore'] else '·'} | {data} | [{v['nome']}](https://www.wikidata.org/wiki/{v['qid']}) | "
                         f"{v['tipo']} {v['anni']} anni | {v['pagine']} | {v['desc'].replace('|', '/')} |")
        righe.append("")
    (OUT / "anniv-candidati.md").write_text("\n".join(righe), encoding="utf-8")
    print(json.dumps({k: out[k] for k in out if k != "voci"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
