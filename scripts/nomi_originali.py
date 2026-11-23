"""Nomi degli autori che nelle liste hanno solo il codice Wikidata (regola di Marco, 23/11/2026).

scripts/aggiorna.py chiede a Wikidata il nome in poche lingue (it, en, mul, de, fr, es, ru, pl...): se l'autore ha il
nome solo in un'altra lingua (ucraino, georgiano, arabo, ungherese...), nella lista resta il codice (es. «Q20483877»).
Questo script chiede, per quegli autori, il nome in QUALSIASI lingua: il «nome nella lingua nativa» (P1559), le
etichette e gli altri nomi (alias). Sceglie:
  nome: P1559 se c'è; altrimenti un'etichetta in scrittura non latina (di solito è la lingua originale); altrimenti
        un'etichetta in scrittura latina;
  latino: se il nome non è in scrittura latina, un'etichetta in scrittura latina, se Wikidata ne ha una (traslitterazione).
Scrive data/registro/nomi_originali.json: {qid: {"nome", "lingua", "latino", "etichette"}} oppure {qid: {"nessuno": true}}.
Lo applica scripts/applica_registro_liste.py: il nome entra nella lista; chi non ha nome in nessuna lingua resta nei dati
con «senza_nome» e non compare nelle liste pubbliche (regole.autore_visibile)."""
import glob, json, os, re, sys, unicodedata
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verifica as V   # noqa: E402

R = Path(__file__).resolve().parent.parent
USCITA = R / "data" / "registro" / "nomi_originali.json"


def latino(s):
    lettere = [c for c in s if c.isalpha()]
    return bool(lettere) and all("LATIN" in unicodedata.name(c, "") for c in lettere)


def da_cercare():
    out = set()
    for f in glob.glob(str(R / "data" / "[0-9][0-9][0-9][0-9].json")) + glob.glob(str(R / "data" / "es-[0-9][0-9][0-9][0-9].json")):
        for a in json.load(open(f, encoding="utf-8")).get("autori", []):
            if re.fullmatch(r"Q\d+", (a.get("nome") or "").strip() or "Q0"):
                out.add(a["wikidata"])
    return sorted(out)


def main():
    qids = da_cercare()
    print("autori con il solo codice nelle liste:", len(qids))
    dati = {q: {"et": {}, "al": {}, "nat": {}} for q in qids}
    for i in range(0, len(qids), 100):
        v = " ".join("wd:" + q for q in qids[i:i + 100])
        for prop, k in (("rdfs:label", "et"), ("skos:altLabel", "al"), ("wdt:P1559", "nat")):
            for r in V.sparql(f"SELECT ?a ?l WHERE {{ VALUES ?a {{ {v} }} ?a {prop} ?l }}"):
                q = r["a"]["value"].rsplit("/", 1)[-1]
                dati[q][k].setdefault(r["l"].get("xml:lang", "?"), r["l"]["value"])
    out = {}
    for q in qids:
        d = dati[q]
        tutti = {**d["al"], **d["et"]}
        if not (d["nat"] or tutti):
            out[q] = {"nessuno": True}
            continue
        if d["nat"]:
            lingua, nome = next(iter(sorted(d["nat"].items())))
        else:
            non_lat = sorted((l, n) for l, n in tutti.items() if not latino(n))
            lingua, nome = (non_lat or sorted(tutti.items()))[0]
        lat = None if latino(nome) else next((n for l, n in sorted(tutti.items()) if latino(n)), None)
        out[q] = {"nome": nome, "lingua": lingua, "latino": lat, "etichette": d["et"]}
    USCITA.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"aggiornato": date.today().isoformat(), "autori": out}, open(USCITA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = sum(1 for x in out.values() if x.get("nessuno"))
    print(f"con un nome in qualche lingua: {len(out) - n} | senza nome in nessuna lingua: {n}")


if __name__ == "__main__":
    main()
