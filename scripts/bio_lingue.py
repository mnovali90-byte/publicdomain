"""Biografie, descrizioni e titoli delle opere in tedesco, francese e spagnolo, per gli autori con una scheda (26/11/2026).

Serve alle pagine in quelle lingue (scripts/lingue.py). Stesso metodo delle bio in italiano e inglese (scripts/arricchisci.py):
- biografia = il primo paragrafo della Wikipedia di quella lingua (licenza CC BY-SA, con il link alla pagina), solo se la pagina esiste;
- descrizione breve = la descrizione di Wikidata in quella lingua;
- titoli delle opere = l'etichetta Wikidata in quella lingua delle opere di cui l'autore è autore (P50), abbinate ai titoli che
  la scheda già mostra (stesso titolo inglese o originale).
Scrive solo data/lingue_extra.json: non tocca liste, date, regole né pagine.
Uso: python3 scripts/bio_lingue.py
"""
import json, sys, time, urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arricchisci as A   # http_json, riassunto, PAUSA: le stesse funzioni delle bio in italiano e inglese

RADICE = Path(__file__).resolve().parent.parent
LINGUE = ("de", "fr", "es")
USCITA = RADICE / "data" / "lingue_extra.json"
LISTE = ["2027.json", "es-2027.json", "2028.json", "es-2028.json"]


def autori_con_scheda():
    visti = {}
    for f in LISTE:
        p = RADICE / "data" / f
        if not p.exists():
            continue
        dati = json.loads(p.read_text(encoding="utf-8"))
        for a in dati.get("autori", []):
            if a.get("pagina") and a.get("wikidata"):
                visti[a["wikidata"]] = a
    return visti


def entita(qids):
    """Sitelink, descrizioni ed etichette in de/fr/es, a gruppi di 50."""
    out = {}
    qids = list(qids)
    for i in range(0, len(qids), 50):
        url = ("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=sitelinks|descriptions|labels"
               "&languages=de|fr|es&sitefilter=dewiki|frwiki|eswiki&ids=" + "|".join(qids[i:i + 50]))
        d = A.http_json(url) or {}
        out.update(d.get("entities", {}))
        time.sleep(A.PAUSA)
    return out


def opere_in_lingua(qid):
    """Opere con autore (P50) = qid, con etichetta inglese, originale e nelle tre lingue."""
    q = f"""SELECT ?o ?en ?de ?fr ?es ?orig WHERE {{
      ?o wdt:P50 wd:{qid} .
      OPTIONAL {{ ?o rdfs:label ?en FILTER(LANG(?en)="en") }}
      OPTIONAL {{ ?o rdfs:label ?de FILTER(LANG(?de)="de") }}
      OPTIONAL {{ ?o rdfs:label ?fr FILTER(LANG(?fr)="fr") }}
      OPTIONAL {{ ?o rdfs:label ?es FILTER(LANG(?es)="es") }}
      OPTIONAL {{ ?o wdt:P1476 ?orig }}
    }} LIMIT 400"""
    url = "https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(q)
    d = A.http_json(url) or {}
    time.sleep(A.PAUSA * 4)
    righe = []
    for b in d.get("results", {}).get("bindings", []):
        righe.append({k: b[k]["value"] for k in b})
    return righe


def main():
    autori = autori_con_scheda()
    print(f"autori con scheda: {len(autori)}")
    vecchio = json.loads(USCITA.read_text(encoding="utf-8")) if USCITA.exists() else {}
    ent = entita(autori)
    out = {"nota": __doc__.strip().split("\n")[0], "autori": {}}
    n_bio = {l: 0 for l in LINGUE}
    for q, a in autori.items():
        e = ent.get(q, {})
        prima = (vecchio.get("autori") or {}).get(q, {})
        r = {"bios": dict(prima.get("bios") or {}), "descrizioni": {}, "opere": {}}
        for l in LINGUE:
            d = (e.get("descriptions") or {}).get(l)
            if d:
                r["descrizioni"][l] = d["value"]
            sl = (e.get("sitelinks") or {}).get(f"{l}wiki")
            if sl and l not in r["bios"]:
                b = A.riassunto(l, sl["title"])
                if b:
                    r["bios"][l] = b
        for l in LINGUE:
            n_bio[l] += l in r["bios"]
        # titoli delle opere: abbinati per titolo inglese o originale a quelli che la scheda mostra già
        mostrati = {(o.get("titolo_en") or "").strip().lower(): o.get("titolo") for o in a.get("opere", [])}
        mostrati.update({(o.get("titolo") or "").strip().lower(): o.get("titolo") for o in a.get("opere", [])})
        mostrati.pop("", None)
        if mostrati:
            for w in opere_in_lingua(q):
                chiave = None
                for c in (w.get("en"), w.get("orig")):
                    if c and c.strip().lower() in mostrati:
                        chiave = mostrati[c.strip().lower()]
                        break
                if chiave and chiave not in r["opere"]:
                    r["opere"][chiave] = {l: w[l] for l in LINGUE if w.get(l)}
        out["autori"][q] = r
    USCITA.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("biografie trovate: " + ", ".join(f"{l} {n_bio[l]}" for l in LINGUE))


if __name__ == "__main__":
    main()
