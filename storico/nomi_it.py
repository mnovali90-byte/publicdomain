"""Nomi italiani degli autori di Già pubblici (regola decisa da Marco il 21/11/2026, dopo la prova DNB e nomi).

Nell'archivio gli autori hanno il nome inglese di Wikidata («Leo Tolstoy», «Aesop»). Qui si legge da Wikidata
l'etichetta italiana di ogni autore con codice e si tengono solo quelle diverse dall'inglese («Lev Tolstoj», «Esopo»):
data/storico/nomi_it.json = {qid: nome italiano}. La pagina italiana mostra il nome italiano; la ricerca trova tutti e due
(storico/applica_registro.py mette il nome italiano anche nei file della ricerca).
Se Wikidata non risponde resta il file di prima."""
import glob, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coautori import sparql, v, q_  # noqa: E402

CARTELLA = "data/storico"
USCITA = f"{CARTELLA}/nomi_it.json"


def main():
    autori = {}
    for f in glob.glob(f"{CARTELLA}/ricerca/*.json"):
        for r in json.load(open(f, encoding="utf8"))["autori"]:
            if re.fullmatch(r"Q\d+", r[0] or ""):
                autori[r[0]] = r[1]
    qids = sorted(autori)
    print("autori con codice:", len(qids), flush=True)
    if len(qids) < 1000:
        print("troppo pochi autori: non scrivo nulla"); return
    try:
        vecchio = json.load(open(USCITA, encoding="utf8"))
    except Exception:
        vecchio = {}
    out, mancati = {}, 0
    for i in range(0, len(qids), 300):
        v_ = " ".join("wd:" + q for q in qids[i:i + 300])
        r = sparql(f"SELECT ?a ?it WHERE {{ VALUES ?a {{ {v_} }} ?a rdfs:label ?it. FILTER(LANG(?it)='it') }}")
        if r is None:
            mancati += 1
            for q in qids[i:i + 300]:
                if q in vecchio:
                    out[q] = vecchio[q]
            continue
        for x in r:
            q, it = q_(v(x, "a")), (v(x, "it") or "").strip()
            if it and it != autori.get(q) and not re.fullmatch(r"Q\d+", it):
                out[q] = it
        time.sleep(0.5)
    json.dump(dict(sorted(out.items())), open(USCITA, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    print(f"nomi italiani diversi dall'inglese: {len(out)} | blocchi senza risposta: {mancati}")


if __name__ == "__main__":
    main()
