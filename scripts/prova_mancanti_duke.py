"""Prova (19/11/2026): perché 5 libri della Duke 2025 non risultano nella nostra lista del 1929?
Per ogni libro: la voce Wikidata (dalla Duke, o cercata per titolo), i suoi tipi (P31), le date di pubblicazione
(P577), il numero di Wikipedia, e se la domanda delle liste USA (scripts/opere.py) la trova, classe per classe.
Scrive docs/stima-sito/prova-mancanti-duke.json."""
import json, sys, time, urllib.parse
from pathlib import Path

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "scripts"))
import opere  # noqa: E402

LIBRI = ["A Room of One's Own", "Red Harvest", "Rope", "A Preface to Morals", "The Roman Hat Mystery",
         "Cup of Gold", "All Quiet on the Western Front"]


def cerca(titolo):
    d = opere.get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "wbsearchentities", "search": titolo, "language": "en", "type": "item", "limit": 5, "format": "json"}))
    return [(x["id"], x.get("label"), x.get("description")) for x in (d or {}).get("search", [])]


def scheda(q):
    d = opere.get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "wbgetentities", "ids": q, "props": "claims|sitelinks|labels", "languages": "en", "format": "json"}))
    e = (d or {}).get("entities", {}).get(q, {})
    cl = e.get("claims", {})
    ids = lambda p: [c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") for c in cl.get(p, [])]
    date = [c["mainsnak"].get("datavalue", {}).get("value", {}).get("time") for c in cl.get("P577", [])]
    return {"qid": q, "etichetta": e.get("labels", {}).get("en", {}).get("value"), "P31": ids("P31"),
            "P7937_forma": ids("P7937"), "P577": date, "P50": ids("P50"), "wikipedia": len(e.get("sitelinks", {}))}


def main():
    dk = json.loads((R / "data" / "storico" / "duke.json").read_text(encoding="utf-8"))["2025"]["libri"]
    per_titolo = {l["titolo"]: l for l in dk}
    # la lista come la fa opere.py, classe per classe
    trovate = {}
    classi = list(opere.CLASSI)
    for c in classi:
        opere.CLASSI = [c]
        r = []
        for t in range(3):
            r = opere.opere_anno(1929)
            if r:
                break
            time.sleep(20)
        for o in r:
            trovate.setdefault(o["qid"], []).append(c)
    opere.CLASSI = classi
    out = {"classi_usate": classi, "opere_trovate_1929": len(trovate), "libri": {}}
    for t in LIBRI:
        l = next((v for k, v in per_titolo.items() if k.lower().replace("’", "'").startswith(t.lower()[:12])), None)
        q = ((l or {}).get("wd") or {}).get("qid")
        cand = [] if q else cerca(t)
        schede = [scheda(q)] if q else [scheda(c[0]) for c in cand[:3]]
        out["libri"][t] = {"duke": l and {"titolo": l["titolo"], "autore": l["autore"]}, "qid_dalla_duke": q,
                           "candidati_cercati": cand, "schede": schede,
                           "nella_nostra_lista": {s["qid"]: trovate.get(s["qid"]) for s in schede}}
        print(t, json.dumps(out["libri"][t], ensure_ascii=False)[:600])
        time.sleep(1)
    (R / "docs" / "stima-sito" / "prova-mancanti-duke.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
