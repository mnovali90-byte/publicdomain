"""Prova (20/11/2026): coautori. Non cambia il sito. Scrive docs/stima-sito/prova-coautori.json.

A. Opere con più autori in cui almeno un «autore» non ha data di morte (oggi l'opera risulta non libera in Europa):
   che cosa sono quelle voci su Wikidata? persona (Q5), gruppo/duo, pseudonimo, valore sconosciuto.
B. Opere più importanti (scaffali e liste di Già pubblici): collaboratori segnati in altri campi di Wikidata
   (P86 compositore, P87 librettista, P767 collaboratore, P110 illustratore, P1779 possibile autore) con la data di
   morte. Quante opere oggi date libere in Europa (tutti gli autori P50 morti da più di 70 anni) avrebbero un
   collaboratore morto dopo?"""
import json, re, sys, time, urllib.parse, urllib.request
from collections import Counter
from datetime import date
from pathlib import Path

R = Path(__file__).resolve().parent.parent
S = R / "data" / "storico"
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
Y = date.today().year
CAMPI = {"P86": "compositore", "P87": "librettista", "P767": "collaboratore", "P110": "illustratore", "P1779": "possibile autore"}


def sparql(q):
    for t in range(6):
        try:
            u = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"})
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90))["results"]["bindings"]
        except Exception:
            time.sleep(20 * (t + 1))
    return None


def main():
    arch = {}
    for f in sorted((S / "ricerca").glob("*.json")):
        for r in json.loads(f.read_text(encoding="utf-8"))["opere"]:
            arch.setdefault(r[0], r)
    out = {}
    # A
    multi = [r for r in arch.values() if len(r[5]) >= 2 and any(a[2] is None for a in r[5]) and any(a[2] is not None for a in r[5])]
    senza = sorted({a[0] for r in multi for a in r[5] if a[2] is None and re.fullmatch(r"Q\d+", a[0] or "")})
    tipi = {}
    for i in range(0, len(senza), 200):
        v = " ".join("wd:" + q for q in senza[i:i + 200])
        for x in sparql(f"SELECT ?a ?t ?tLabel WHERE {{ VALUES ?a {{ {v} }} OPTIONAL {{ ?a wdt:P31 ?t }} SERVICE wikibase:label {{ bd:serviceParam wikibase:language \"en\". }} }}") or []:
            a = x["a"]["value"].rsplit("/", 1)[-1]
            tipi.setdefault(a, set()).add(x.get("tLabel", {}).get("value", "?"))
        time.sleep(1)
    c = Counter()
    esempi = {}
    for r in multi:
        for a in r[5]:
            if a[2] is None:
                k = "valore sconosciuto" if not re.fullmatch(r"Q\d+", a[0] or "") else ", ".join(sorted(tipi.get(a[0], {"?"})))
                c[k] += 1
                esempi.setdefault(k, []).append(f"{r[1]} — {a[1]}")
    out["A_opere"] = len(multi)
    out["A_tipi_delle_voci_senza_morte"] = c.most_common(40)
    out["A_esempi"] = {k: v[:8] for k, v in esempi.items()}
    # B: opere degli scaffali (opere.json + scaffali_lingua.json)
    importanti = set()
    o = json.loads((S / "opere.json").read_text(encoding="utf-8"))
    importanti |= {x["qid"] for x in (o["opere"] if isinstance(o, dict) else o)}
    try:
        sl = json.loads((S / "scaffali_lingua.json").read_text(encoding="utf-8"))
        importanti |= {q for x in sl["lingue"].values() for q, _ in x["opere"]}
    except Exception:
        pass
    importanti = sorted(q for q in importanti if q in arch)
    collab = {}
    for i in range(0, len(importanti), 200):
        v = " ".join("wd:" + q for q in importanti[i:i + 200])
        q = f"""SELECT ?w ?p ?c ?cLabel ?morte WHERE {{ VALUES ?w {{ {v} }} VALUES ?p {{ {" ".join("wdt:" + k for k in CAMPI)} }}
          ?w ?p ?c. OPTIONAL {{ ?c wdt:P570 ?morte }} SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}"""
        for x in sparql(q) or []:
            w = x["w"]["value"].rsplit("/", 1)[-1]
            p = x["p"]["value"].rsplit("/", 1)[-1]
            m = re.match(r"^-?(\d{4})", x.get("morte", {}).get("value", ""))
            collab.setdefault(w, []).append((CAMPI.get(p, p), x.get("cLabel", {}).get("value"), int(m.group(1)) if m else None))
        time.sleep(1)
    soglia = Y - 71
    cambiano = []
    for w, cc in collab.items():
        r = arch[w]
        libera_oggi = r[5] and all(a[3] or (a[2] is not None and a[2] <= soglia) for a in r[5])
        dopo = [x for x in cc if x[2] is None or x[2] > soglia]
        if libera_oggi and dopo:
            cambiano.append({"opera": r[1], "titolo_it": r[2], "wikipedia": r[4], "autori": [(a[1], a[2]) for a in r[5]],
                             "collaboratori_dopo": dopo})
    cambiano.sort(key=lambda x: -(x["wikipedia"] or 0))
    out["B_opere_importanti"] = len(importanti)
    out["B_con_collaboratori"] = len(collab)
    out["B_per_campo"] = Counter(x[0] for cc in collab.values() for x in cc).most_common()
    out["B_libere_oggi_ma_collaboratore_morto_dopo"] = len(cambiano)
    out["B_esempi"] = cambiano[:60]
    (R / "docs" / "stima-sito" / "prova-coautori.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if not k.endswith("esempi")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
