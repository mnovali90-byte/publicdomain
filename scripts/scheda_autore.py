"""Scheda di un autore che manca dalle liste perché Wikidata sbaglia l'anno di morte (decisione di Marco, 23/11/2026:
Dehkhoda, Wikidata 1959, Encyclopaedia Iranica e Rekhta 1956). NON CAMBIA LE LISTE NÉ IL SITO.

Costruisce la scheda come la costruiscono aggiorna.py e arricchisci.py (stessi dati, stesse funzioni: Wikidata,
Wikipedia, Commons) e la scrive in data/registro/schede_proposte.json. L'inserimento nella lista lo fa poi
data/morti_corrette.json (scripts/verifica.py, regola delle due fonti), dopo che Marco ha visto la fotografia.
Uso: QID=Q470931 python3 scripts/scheda_autore.py"""
import datetime as dt
import json, os, sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "scripts"))
import arricchisci as A    # noqa: E402
import regola_lista        # noqa: E402


def base(q):
    righe = A.sparql(f"""SELECT ?nome ?nascita ?morte ?sl ?profLabel ?descrizione WHERE {{
      BIND(wd:{q} AS ?a) ?a wikibase:sitelinks ?sl .
      OPTIONAL {{ ?a wdt:P569 ?nascita }} OPTIONAL {{ ?a wdt:P570 ?morte }} OPTIONAL {{ ?a wdt:P106 ?prof }}
      OPTIONAL {{ ?a rdfs:label ?nome FILTER(LANG(?nome) = "it") }}
      OPTIONAL {{ ?a schema:description ?descrizione FILTER(LANG(?descrizione) = "en") }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "it,en,mul". }} }}""")
    if not righe:
        raise SystemExit(f"{q}: Wikidata non risponde")
    r0 = righe[0]
    return {"wikidata": q, "nome": r0.get("nome", {}).get("value") or q,
            "nascita": (r0.get("nascita", {}).get("value") or "")[:10] or None,
            "morte": (r0.get("morte", {}).get("value") or "")[:10] or None,
            "pagine_wikipedia": int(r0["sl"]["value"]),
            "professioni": sorted({r["profLabel"]["value"] for r in righe if r.get("profLabel")}),
            "descrizione": r0.get("descrizione", {}).get("value"),
            "url": f"https://www.wikidata.org/wiki/{q}"}


def main():
    oggi = dt.date.today()
    out_p = R / "data" / "registro" / "schede_proposte.json"
    try:
        out = json.load(open(out_p, encoding="utf-8"))
    except Exception:
        out = {"nota": "Schede proposte (scripts/scheda_autore.py): non sono nelle liste finché Marco non approva.", "autori": {}}
    cache = A.carica_cache()
    for q in os.environ.get("QID", "Q470931").split(","):
        a = base(q)
        A.arricchisci_gruppo([a], cache, oggi)
        voce = cache.get(q, {})
        for k in ("bio", "bio_url", "bio_lingua", "bios", "opere", "n_opere", "generi", "visite_12m", "visite_it", "visite_en",
                  "visite_es", "visite_de", "visite_fr", "gutenberg", "foto", "paesi", "lingue"):
            if voce.get(k) not in (None, [], ""):
                a[k] = voce[k]
        a.setdefault("n_opere", 0)
        a["candidato"] = regola_lista.candidato(a, a.get("descrizione"))
        a["letterario"] = a["candidato"] and regola_lista.scrittore(a, a.get("descrizione"))
        a["tipo_catalogo"] = [A.TIPO_CATALOGO[p] for p in a["professioni"] if p in A.TIPO_CATALOGO]
        out["autori"][q] = {"scheda": a, "fatto": oggi.isoformat()}
        print(q, a["nome"], "| professioni:", a["professioni"], "| descrizione:", a.get("descrizione"),
              "| letterario:", a["letterario"], "| opere:", a.get("n_opere"), "| visite:", a.get("visite_12m"))
    json.dump(out, open(out_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
