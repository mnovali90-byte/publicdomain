"""Titoli, nomi, descrizioni e pagine Wikipedia in tedesco, francese e spagnolo per Già pubblici e il calendario (26/11/2026).

Serve a tradurre tutto il sito nelle tre lingue (decisione di Marco, 26/11/2026). Solo dati aperti di Wikidata (CC0):
- per ogni autore delle liste, ogni opera e autore di Già pubblici (data/storico/pagina.json) e ogni voce del calendario (data/anniversari-<anno>.json):
  etichetta, descrizione breve e pagina Wikipedia in de/fr/es, se esistono (se mancano, la pagina usa il titolo originale);
- per le voci del calendario anche paese, genere e lingua (P27, P136, P407) con le etichette nelle tre lingue,
  come le righe «chi è / cos'è» che il calendario ha già in italiano e inglese.
Scrive solo data/lingue_etichette.json: non tocca liste, date, regole né pagine.
Uso: python3 scripts/etichette_lingue.py
"""
import glob, json, sys, time, urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arricchisci as A   # http_json, PAUSA

RADICE = Path(__file__).resolve().parent.parent
LINGUE = ("de", "fr", "es")
USCITA = RADICE / "data" / "lingue_etichette.json"


def qid_sito():
    gp = json.loads((RADICE / "data" / "storico" / "pagina.json").read_text(encoding="utf-8"))
    q = {r[0] for r in gp.get("opere", []) if r and str(r[0]).startswith("Q")}
    q |= {a[0] for a in gp.get("autori", []) if a and str(a[0]).startswith("Q")}
    cal = set()
    for f in glob.glob(str(RADICE / "data" / "anniversari-*.json")):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        for v in d.get("voci", []):
            cal.add(v["qid"])
            if v.get("autore_qid"):
                q.add(v["autore_qid"])
    # 26/11/2026: anche gli autori delle liste (radar e pagine paese): descrizione breve nella lingua
    for f in glob.glob(str(RADICE / "data" / "*.json")):
        import re
        if re.fullmatch(r"(es-)?\d{4}\.json", Path(f).name):
            q |= {a["wikidata"] for a in json.loads(Path(f).read_text(encoding="utf-8")).get("autori", []) if a.get("wikidata")}
    return q | cal, cal


def entita(qids):
    out = {}
    qids = sorted(qids)
    for i in range(0, len(qids), 50):
        url = ("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=sitelinks/urls|descriptions|labels"
               "&languages=de|fr|es&sitefilter=dewiki|frwiki|eswiki&ids=" + "|".join(qids[i:i + 50]))
        d = A.http_json(url) or {}
        for q, e in d.get("entities", {}).items():
            r = {}
            for l in LINGUE:
                lab = ((e.get("labels") or {}).get(l) or {}).get("value")
                des = ((e.get("descriptions") or {}).get(l) or {}).get("value")
                wik = ((e.get("sitelinks") or {}).get(l + "wiki") or {}).get("url")
                if lab or des or wik:
                    r[l] = [lab, des, wik]
            if r:
                out[q] = r
        time.sleep(A.PAUSA)
        if i % 1000 == 0:
            print(f"  {i}/{len(qids)}", flush=True)
    return out


def dettagli_calendario(cal):
    """Paese (P27), genere (P136), lingua (P407) delle voci del calendario, con le etichette in de/fr/es."""
    out = {}
    cal = sorted(cal)
    for i in range(0, len(cal), 80):
        vals = " ".join("wd:" + q for q in cal[i:i + 80])
        sel = " ".join(f"?{p}_{l}" for p in ("paese", "genere", "lingua") for l in LINGUE)
        opt = "\n".join(f'OPTIONAL {{ ?x wdt:{pp} ?{p} . ?{p} rdfs:label ?{p}_{l} FILTER(LANG(?{p}_{l})="{l}") }}'
                        for p, pp in (("paese", "P27"), ("genere", "P136"), ("lingua", "P407")) for l in LINGUE)
        q = f"SELECT ?x {sel} WHERE {{ VALUES ?x {{ {vals} }}\n{opt} }}"
        d = A.http_json("https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(q)) or {}
        for b in (d.get("results") or {}).get("bindings", []):
            x = b["x"]["value"].rsplit("/", 1)[1]
            for p in ("paese", "genere", "lingua"):
                for l in LINGUE:
                    v = (b.get(f"{p}_{l}") or {}).get("value")
                    if v:
                        lst = out.setdefault(x, {}).setdefault(l, {}).setdefault(p, [])
                        if v not in lst:
                            lst.append(v)
        time.sleep(A.PAUSA)
    return out


def main():
    tutti, cal = qid_sito()
    print(f"Codici: {len(tutti)} (calendario {len(cal)})", flush=True)
    ent = entita(tutti)
    det = dettagli_calendario(cal)
    USCITA.write_text(json.dumps({"nota": "Etichette, descrizioni e pagine Wikipedia in de/fr/es da Wikidata (CC0), per Già pubblici e il calendario. "
                                          "Scritto da scripts/etichette_lingue.py.", "voci": ent, "calendario": det},
                                 ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    for l in LINGUE:
        print(l, "etichette", sum(1 for v in ent.values() if l in v and v[l][0]), "descrizioni", sum(1 for v in ent.values() if l in v and v[l][1]),
              "wikipedia", sum(1 for v in ent.values() if l in v and v[l][2]))


if __name__ == "__main__":
    main()
