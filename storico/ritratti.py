"""Ritratti per la classifica «Autori» della pagina Già pubblici: immagine Wikidata (P18) da Wikimedia Commons,
con autore della foto e licenza (letti dalla pagina del file su Commons). Scrive data/storico/ritratti.json.

Solo per gli autori che possono entrare in classifica (almeno 3 opere tra le più note). Un ritratto già trovato si
ricontrolla dopo 90 giorni. La pagina mostra la miniatura da Commons (Special:FilePath, 240 px) e mette nei crediti
autore e licenza di ogni foto che non è in pubblico dominio.
"""
import json, re, sys, time, urllib.parse, urllib.request
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

S = Path(__file__).resolve().parent.parent / "data" / "storico"
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
RINFRESCA = 90


def j(url, tentativi=4):
    for t in range(tentativi):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90))
        except Exception as e:
            print("riprovo:", e)
            time.sleep(5 * (t + 1))
    return None


def main():
    O = json.loads((S / "opere.json").read_text(encoding="utf-8"))["opere"]
    conta = Counter(a["qid"] for o in O for a in o["autori"])
    voluti = [q for q, n in conta.items() if n >= 3]
    try:
        cache = json.loads((S / "ritratti.json").read_text(encoding="utf-8"))
    except Exception:
        cache = {}
    limite = (date.today() - timedelta(days=RINFRESCA)).isoformat()
    da_fare = [q for q in voluti if q not in cache or (cache[q] or {}).get("d", "") < limite]
    print(f"autori in classifica possibile: {len(voluti)}, da controllare: {len(da_fare)}")
    for i in range(0, len(da_fare), 80):
        blocco = da_fare[i:i + 80]
        q = "SELECT ?p ?img WHERE { VALUES ?p { %s } ?p wdt:P18 ?img }" % " ".join("wd:" + x for x in blocco)
        r = j("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"}))
        if r is None:
            continue
        img = {}
        for b in r["results"]["bindings"]:
            img.setdefault(b["p"]["value"].rsplit("/", 1)[-1], urllib.parse.unquote(b["img"]["value"].rsplit("/", 1)[-1]))
        oggi = date.today().isoformat()
        for x in blocco:
            if x not in img:
                cache[x] = {"d": oggi, "url": None}
        file = list(img.items())
        for k in range(0, len(file), 40):
            parte = file[k:k + 40]
            m = j("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
                "action": "query", "titles": "|".join("File:" + f for _, f in parte), "prop": "imageinfo",
                "iiprop": "extmetadata", "format": "json", "formatversion": "2"}))
            if m is None:
                continue
            norm = {n["from"]: n["to"] for n in m["query"].get("normalized", [])}
            pagine = {p["title"]: p for p in m["query"]["pages"]}
            for qa, f in parte:
                t = norm.get("File:" + f, "File:" + f)
                p = pagine.get(t)
                if not p or "imageinfo" not in p:
                    continue
                em = p["imageinfo"][0].get("extmetadata", {})
                lic = em.get("LicenseShortName", {}).get("value", "")
                aut = re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", em.get("Artist", {}).get("value", ""))).strip()
                aut = re.sub(r"(Unknown(?: [a-z]+)?)\1", r"\1", re.sub(r"^(.{4,}?)\s*\1(?=$|[\s(;,])", r"\1", aut))   # Commons ripete il nome due volte (visibile e nascosto): «Unknown authorUnknown author» (20/11/2026)
                nome = t[5:].replace(" ", "_")
                cache[qa] = {"d": oggi, "url": "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(nome) + "?width=240",
                             "pagina": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(t.replace(" ", "_")),
                             "licenza": lic, "autore": aut[:120]}
            time.sleep(1)
        time.sleep(2)
    # nella pagina vanno solo i ritratti trovati
    (S / "ritratti.json").write_text(json.dumps(cache, ensure_ascii=False, indent=0), encoding="utf-8")
    print("ritratti trovati:", sum(1 for v in cache.values() if v and v.get("url")))


if __name__ == "__main__":
    main()
