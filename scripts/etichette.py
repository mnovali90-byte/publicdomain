"""Nomi inglesi di paesi e lingue, presi da Wikidata (non scritti a mano).

I dati degli autori hanno paesi e lingue con l'etichetta italiana di Wikidata ("Reich tedesco", "tedesco").
Per la versione inglese del sito serve il nome inglese: per ogni etichetta italiana si cerca su Wikidata
l'elemento con quell'etichetta (se più d'uno, quello con più pagine Wikipedia) e se ne prende l'etichetta inglese.

Scrive data/etichette_en.json: {"tedesco": "German", "Germania": "Germany", ...}.
Le traduzioni già trovate restano: se Wikidata non risponde non si perde nulla.
"""
import glob
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
FILE = RADICE / "data" / "etichette_en.json"
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)",
      "Accept": "application/sparql-results+json"}


def sparql(q):
    u = "https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(q)
    for t in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90) as r:
                return json.load(r)["results"]["bindings"]
        except Exception as e:
            print("Wikidata non risponde, riprovo:", e)
            time.sleep(10 * (t + 1))
    raise RuntimeError("Wikidata non risponde")


def etichette_italiane():
    voci = set()
    for f in glob.glob(str(RADICE / "data" / "*[0-9][0-9][0-9][0-9].json")):
        if "/us-" in f or "anniversari" in f:
            continue
        for a in json.load(open(f, encoding="utf-8")).get("autori", []):
            voci.update(a.get("paesi") or [])
            voci.update(a.get("lingue") or [])
    # i nomi moderni con cui la pagina raggruppa gli stati storici (oggetto PAESI in index.html)
    s = (RADICE / "index.html").read_text(encoding="utf-8")
    blocco = s[s.index("const PAESI = {"):s.index("};", s.index("const PAESI = {"))]
    voci.update(re.findall(r'^\s*"([^"]+)": \[', blocco, flags=re.M))
    return sorted(v for v in voci if v)


def main():
    try:
        trad = json.loads(FILE.read_text(encoding="utf-8"))
    except Exception:
        trad = {}
    voci = [v for v in etichette_italiane() if v not in trad]
    print("etichette da tradurre:", len(voci))
    for i in range(0, len(voci), 40):
        blocco = voci[i:i + 40]
        valori = " ".join(json.dumps(v, ensure_ascii=False) + "@it" for v in blocco)
        q = f"""SELECT ?it ?en ?sl WHERE {{ VALUES ?it {{ {valori} }}
          ?x rdfs:label ?it; wikibase:sitelinks ?sl; rdfs:label ?en. FILTER(LANG(?en) = "en") }}"""
        try:
            righe = sparql(q)
        except Exception as e:
            print("blocco saltato:", e)
            continue
        migliore = {}
        for r in righe:
            it, en, sl = r["it"]["value"], r["en"]["value"], int(r["sl"]["value"])
            if it not in migliore or sl > migliore[it][1]:
                migliore[it] = (en, sl)
        for it, (en, _) in migliore.items():
            trad[it] = en
        time.sleep(1)
    FILE.write_text(json.dumps(dict(sorted(trad.items())), ensure_ascii=False, indent=1), encoding="utf-8")
    manca = [v for v in etichette_italiane() if v not in trad]
    print(f"tradotte: {len(trad)}; senza traduzione: {len(manca)}", manca[:30])


if __name__ == "__main__":
    main()
