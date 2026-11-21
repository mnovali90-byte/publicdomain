"""Autori «morti per la Francia» (21/11/2026). Scrive data/registro/mpf.json.

In Francia chi è dichiarato «mort pour la France» ha 30 anni di protezione in più (Code de la propriété
intellectuelle, art. L123-10). Su Wikidata il titolo è «premio ricevuto» (P166) = mort pour la France (Q3324507).
Prova del 21/11/2026 (docs/registro-prove.md): i 22 autori marcati a mano su Wikisource francese lo hanno tutti,
ma l'elenco di Wikidata non è completo (manca per esempio Louis Pergaud): chi non c'è non è per forza libero.
Si tengono solo i nostri autori (Già pubblici, 2027, 2028). Se Wikidata non risponde resta il file di prima."""
import glob, json, os, sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coautori as C  # noqa: E402  (sparql con i tentativi)

MPF = "Q3324507"
USCITA = "data/registro/mpf.json"


def main():
    nostri = set()
    for f in glob.glob("data/storico/ricerca/*.json"):
        nostri.update(r[0] for r in json.load(open(f, encoding="utf8"))["autori"])
    for f in ("data/2027.json", "data/2028.json"):
        if os.path.exists(f):
            nostri.update(a["wikidata"] for a in json.load(open(f, encoding="utf8"))["autori"])
    r = C.sparql(f"""SELECT ?p (YEAR(MIN(?m)) AS ?anno) WHERE {{ ?p wdt:P166 wd:{MPF}. OPTIONAL {{ ?p wdt:P570 ?m. }} }} GROUP BY ?p""")
    if r is None:
        print("Wikidata non risponde: resta il file di prima")
        return
    tutti = {C.q_(C.v(x, "p")): (int(C.v(x, "anno")) if C.v(x, "anno") else None) for x in r}
    autori = {q: a for q, a in sorted(tutti.items()) if q in nostri}
    os.makedirs(os.path.dirname(USCITA), exist_ok=True)
    json.dump({"aggiornato": date.today().isoformat(),
               "fonte": f"Wikidata (CC0): P166 = {MPF} «mort pour la France»; regola: Code de la propriété intellectuelle, art. L123-10",
               "su_wikidata": len(tutti), "autori": autori},
              open(USCITA, "w", encoding="utf8"), ensure_ascii=False, indent=0)
    print(f"{len(tutti)} persone con il titolo su Wikidata, {len(autori)} tra i nostri autori")


if __name__ == "__main__":
    main()
