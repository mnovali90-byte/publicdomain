"""Cittadinanza (Wikidata P27) per TUTTI gli autori delle liste, non solo per gli scrittori arricchiti (21/11/2026).

Perché: la nota sul Trattato di pace (scripts/regole.py, nota_trattato) dipende dalla cittadinanza. Senza questo passo,
«non nota» voleva dire spesso solo «non l'abbiamo chiesta» (gli autori non scrittori non passano da scripts/arricchisci.py). Qui si chiede a Wikidata per tutti quelli senza `paesi`, con le stesse
etichette italiane dell'arricchimento. Chi resta senza paese, su Wikidata il paese non ce l'ha davvero: si scrive
`paesi: []` e `paesi_fonte: "P27 assente"`, così si distingue da «non chiesto».

Non tocca chi ha già `paesi`. Se Wikidata non risponde, lascia il file com'è."""
import glob, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}


def sparql(q):
    for t in range(3):
        try:
            u = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"})
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120) as r:
                return json.load(r)["results"]["bindings"]
        except Exception as e:
            print("  Wikidata:", e, file=sys.stderr)
            time.sleep(10 * (t + 1))
    return None


def main():
    for f in sorted(glob.glob(str(RADICE / "data" / "[0-9]*.json")) + glob.glob(str(RADICE / "data" / "es-[0-9]*.json"))):
        p = Path(f)
        d = json.loads(p.read_text(encoding="utf-8"))
        manca = [a for a in d.get("autori", []) if not a.get("paesi") and not a.get("paesi_fonte")]
        if not manca:
            print(p.name, "nessuno da fare"); continue
        trovati = {}
        ok = True
        for i in range(0, len(manca), 150):
            v = " ".join("wd:" + a["wikidata"] for a in manca[i:i + 150])
            r = sparql(f"""SELECT ?a ?paeseLabel WHERE {{ VALUES ?a {{ {v} }} ?a wdt:P27 ?paese.
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "it,en,mul". }} }}""")
            if r is None:
                ok = False; break
            for x in r:
                q = x["a"]["value"].rsplit("/", 1)[-1]
                l = x.get("paeseLabel", {}).get("value")
                if l and not re.fullmatch(r"Q\d+", l):
                    trovati.setdefault(q, [])
                    if l not in trovati[q]:
                        trovati[q].append(l)
            time.sleep(1)
        if not ok:
            print(p.name, "Wikidata non ha risposto: file lasciato com'è"); continue
        for a in manca:
            a["paesi"] = trovati.get(a["wikidata"], [])
            a["paesi_fonte"] = "P27" if a["paesi"] else "P27 assente"
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print(p.name, f"senza paese: {len(manca)}, trovati su Wikidata: {sum(1 for a in manca if a['paesi'])}, "
                      f"davvero senza cittadinanza: {sum(1 for a in manca if not a['paesi'])}")


if __name__ == "__main__":
    main()
