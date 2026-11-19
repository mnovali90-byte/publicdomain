"""Prova (19/11/2026): perché «A Room of One's Own» (Woolf, 1929) non è nella nostra lista USA del 1929?
Prende la voce Wikidata dalla pagina della Wikipedia inglese (collegamento sicuro, niente ricerca per titolo) e ne legge
tipo (P31), forma (P7937), genere (P136), date (P577), numero di Wikipedia, etichette. Stesso controllo per altri
saggi e libri non romanzo del 1929-1932. Scrive docs/stima-sito/prova-saggi.json."""
import json, sys, urllib.parse
from pathlib import Path
R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "scripts"))
import opere  # noqa: E402

PAGINE = ["A Room of One's Own", "A Preface to Morals", "Civilization and Its Discontents", "The Revolt of the Masses",
          "Coming of Age in Samoa", "Good-Bye to All That", "Letters to a Young Poet", "Brave New World", "Rope (play)"]
CLASSI = set(opere.CLASSI)


def main():
    d = opere.get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "wbgetentities", "sites": "enwiki", "titles": "|".join(PAGINE), "props": "claims|sitelinks|labels",
         "languages": "en|it", "format": "json"}))
    out = {}
    ids = lambda cl, p: [c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") for c in cl.get(p, [])]
    for q, e in (d or {}).get("entities", {}).items():
        cl = e.get("claims", {})
        tipo, forma = ids(cl, "P31"), ids(cl, "P7937")
        r = {"qid": q, "etichetta_en": e.get("labels", {}).get("en", {}).get("value"),
             "P31_tipo": tipo, "P7937_forma": forma, "P136_genere": ids(cl, "P136"),
             "P577_date": [c["mainsnak"].get("datavalue", {}).get("value", {}).get("time") for c in cl.get("P577", [])],
             "wikipedia": len(e.get("sitelinks", {})),
             "la_nostra_domanda_lo_prende": bool(CLASSI & set(tipo)) or ("Q47461344" in tipo and bool(CLASSI & set(forma)))}
        out[r["etichetta_en"] or q] = r
        print(json.dumps(r, ensure_ascii=False))
    # nomi leggibili dei tipi
    tutti = sorted({x for r in out.values() for k in ("P31_tipo", "P7937_forma", "P136_genere") for x in r[k] if x})
    n = opere.get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "wbgetentities", "ids": "|".join(tutti[:50]), "props": "labels", "languages": "it|en", "format": "json"}))
    nomi = {q: (e.get("labels", {}).get("it") or e.get("labels", {}).get("en") or {}).get("value") for q, e in (n or {}).get("entities", {}).items()}
    print("nomi dei tipi:", json.dumps(nomi, ensure_ascii=False))
    (R / "docs" / "stima-sito" / "prova-saggi.json").write_text(json.dumps({"opere": out, "nomi_tipi": nomi, "classi_cercate": sorted(CLASSI)}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
