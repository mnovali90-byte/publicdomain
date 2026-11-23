"""Conteggio per una decisione di Marco (23/11/2026): quanti autori di saggistica entrerebbero nelle liste se si
includessero storici, filosofi, economisti, giuristi e critici. SOLO RAPPORTO: non cambia liste né sito.

Per ogni lista (ANNI=2027,2028; Europa e Spagna) cerca su Wikidata le persone (P31 Q5) morte nell'anno giusto
(regole.morti_liberi_nel) con una di queste professioni (P106) e almeno un'opera scritta su Wikidata (un elemento con
P50 = la persona), che non sono già nelle liste. Ordina per numero di Wikipedia in cui hanno una pagina.
Scrive docs/conteggio-saggisti.md e data/registro/conteggio_saggisti.json."""
import glob, json, os, sys, time
from datetime import date
from pathlib import Path

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "scripts"))
import verifica as V    # noqa: E402  (sparql con i tentativi)
import regole as RG     # noqa: E402

PROF = {"Q201788": "storico", "Q4964182": "filosofo", "Q188094": "economista", "Q185351": "giurista",
        "Q4263842": "critico letterario", "Q6430706": "critico", "Q1792450": "critico d'arte"}
SCRITTORI_WD = {"Q36180", "Q6625963", "Q49757", "Q214917", "Q11774202", "Q333634"}   # come scripts/aggiorna.py


def nelle_liste():
    q = set()
    for f in glob.glob(str(R / "data" / "[0-9][0-9][0-9][0-9].json")) + glob.glob(str(R / "data" / "es-[0-9][0-9][0-9][0-9].json")):
        q |= {a["wikidata"] for a in json.load(open(f, encoding="utf-8")).get("autori", [])}
    return q


def cerca(morte):
    out = {}
    for occ, nome in PROF.items():
        for r in V.sparql(f"""SELECT ?p ?pLabel (COUNT(DISTINCT ?o) AS ?opere) WHERE {{
                 ?p wdt:P106 wd:{occ} ; wdt:P31 wd:Q5 ; wdt:P570 ?m .
                 FILTER(?m >= "{morte}-01-01T00:00:00Z"^^xsd:dateTime && ?m < "{morte + 1}-01-01T00:00:00Z"^^xsd:dateTime)
                 ?o wdt:P50 ?p .
                 SERVICE wikibase:label {{ bd:serviceParam wikibase:language "it,en,mul,de,fr,es". }}
               }} GROUP BY ?p ?pLabel"""):
            q = r["p"]["value"].rsplit("/", 1)[-1]
            x = out.setdefault(q, {"qid": q, "nome": r.get("pLabel", {}).get("value", q), "professioni": [],
                                   "opere_wikidata": int(r["opere"]["value"])})
            if nome not in x["professioni"]:
                x["professioni"].append(nome)
        time.sleep(2)
    qids = sorted(out)
    for i in range(0, len(qids), 50):   # 50 per volta: con 200 Wikidata non rispondeva (giro del 23/11/2026)
        v = " ".join("wd:" + q for q in qids[i:i + 50])
        for r in V.sparql(f"""SELECT ?a (COUNT(DISTINCT ?art) AS ?n) WHERE {{ VALUES ?a {{ {v} }}
                 ?art schema:about ?a ; schema:isPartOf ?w . ?w wikibase:wikiGroup "wikipedia" }} GROUP BY ?a"""):
            out[r["a"]["value"].rsplit("/", 1)[-1]]["wikipedia"] = int(r["n"]["value"])
        for r in V.sparql(f"""SELECT DISTINCT ?a WHERE {{ VALUES ?a {{ {v} }} VALUES ?s {{ {' '.join('wd:' + s for s in SCRITTORI_WD)} }} ?a wdt:P106 ?s }}"""):
            out[r["a"]["value"].rsplit("/", 1)[-1]]["anche_scrittore"] = True
        time.sleep(1)
    return out


def main():
    liste = nelle_liste()
    ris, md = {}, ["# Conteggio degli autori di saggistica (" + date.today().isoformat() + ")", "",
                   "Solo rapporto per una decisione di Marco: niente entra nelle liste. Script `scripts/conta_saggisti.py`.", "",
                   "Chi conta: morto nell'anno della lista, con professione su Wikidata fra " + ", ".join(sorted(set(PROF.values()))) +
                   ", almeno un'opera scritta su Wikidata (P50), non già nelle liste.",
                   "«Anche scrittore»: ha già una professione da scrittore su Wikidata ma è stato escluso dalla regola della lista "
                   "(scripts/regola_lista.py), di solito perché la descrizione dice «storico», «filosofo»...", ""]
    for anno in [int(a) for a in os.environ.get("ANNI", "2027,2028").split(",")]:
        for tipo, nome in (("it", "Europa"), ("es", "Spagna")):
            morte = RG.morti_liberi_nel(anno, tipo)
            c = [x for x in cerca(morte).values() if x["qid"] not in liste]
            c.sort(key=lambda x: (-x.get("wikipedia", 0), -x["opere_wikidata"]))
            ris[f"{anno}-{nome.lower()}"] = {"morte": morte, "candidati": c}
            md += [f"## Lista {anno}, {nome}: morti nel {morte}", "",
                   f"- Entrerebbero: **{len(c)}** (con 10 o più Wikipedia: {sum(1 for x in c if x.get('wikipedia', 0) >= 10)}; "
                   f"anche scrittore su Wikidata: {sum(1 for x in c if x.get('anche_scrittore'))})", "",
                   "I 20 più noti (per numero di Wikipedia):", "",
                   "| Autore | Professioni | Wikipedia | Opere su Wikidata | Anche scrittore |", "|---|---|---|---|---|"]
            for x in c[:20]:
                md.append(f"| {x['nome']} ([{x['qid']}](https://www.wikidata.org/wiki/{x['qid']})) | {', '.join(x['professioni'])} | "
                          f"{x.get('wikipedia', 0)} | {x['opere_wikidata']} | {'sì' if x.get('anche_scrittore') else ''} |")
            md.append("")
    json.dump({"aggiornato": date.today().isoformat(), **ris},
              open(R / "data" / "registro" / "conteggio_saggisti.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    (R / "docs" / "conteggio-saggisti.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print({k: len(v["candidati"]) for k, v in ris.items()})


if __name__ == "__main__":
    main()
