"""Thema, passo 1 (26/11/2026, ok di Marco): raccoglie da Wikidata, per tutte le opere della ricerca di Già pubblici,
i dati strutturati su cui lo script assegna i codici Thema con tabelle di corrispondenza (niente lettura di testi).

Per ogni opera: genere (P136), forma (P7937), tipo (P31), argomento (P921), luogo della storia (P840),
periodo (P2408), «edizione di» (P629), «pubblicato in» (P1433), descrizioni brevi it/en, presenza della voce
Wikipedia it/en e della pagina Wikisource tedesca. I valori sono codici Wikidata (Q...), non parole.

Scrive in docs/stima-sito/prova-thema/catalogo/:
- opere.jsonl.gz: una riga per opera
- valori.json: ogni valore con nome inglese e italiano, proprietà e quante opere lo usano (base delle tabelle)
- rapporto.md
Non cambia il sito.
"""
import glob, gzip, json, time, urllib.parse, urllib.request
from collections import Counter, defaultdict
from pathlib import Path

CART = Path("docs/stima-sito/prova-thema/catalogo")
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; Thema)", "Accept": "application/json"}
PROP = {"P136": "genere", "P7937": "forma", "P31": "tipo", "P921": "argomento", "P840": "luogo", "P2408": "periodo",
        "P629": "edizione_di", "P1433": "pubblicato_in"}


def scarica(url, dati=None, tentativi=5):
    for i in range(tentativi):
        try:
            req = urllib.request.Request(url, data=dati, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except Exception as e:
            if getattr(e, "code", 0) == 404:
                return None
            time.sleep(5 * (i + 1))
    return None


def opere_catalogo():
    q = set()
    for f in glob.glob("data/storico/per_autore/*.json"):
        for righe in json.load(open(f, encoding="utf8")).values():
            for r in righe:
                if str(r[0]).startswith("Q"):
                    q.add(r[0])
    return sorted(q, key=lambda x: int(x[1:]))


def main():
    CART.mkdir(parents=True, exist_ok=True)
    qs = opere_catalogo()
    dati = {q: {"q": q} for q in qs}
    usi = defaultdict(Counter)
    for i in range(0, len(qs), 50):
        j = scarica("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=claims|descriptions|sitelinks"
                    "&languages=it|en&sitefilter=itwiki|enwiki|dewikisource&ids=" + "|".join(qs[i:i + 50]))
        for q, e in (j or {}).get("entities", {}).items():
            d = dati.get(q)
            if d is None:
                continue
            for p, k in PROP.items():
                v = []
                for c in e.get("claims", {}).get(p, []):
                    x = c.get("mainsnak", {}).get("datavalue", {}).get("value")
                    if isinstance(x, dict) and "id" in x and x["id"] not in v:
                        v.append(x["id"])
                if v:
                    d[k] = v
                    for x in v:
                        usi[k][x] += 1
            for l in ("it", "en"):
                x = e.get("descriptions", {}).get(l)
                if x:
                    d["descr_" + l] = x["value"]
            s = e.get("sitelinks", {})
            d["wiki"] = [k for k in ("itwiki", "enwiki", "dewikisource") if k in s]
        if i % 5000 == 0:
            print("opere lette:", i, flush=True)
        time.sleep(0.5)
    # nomi dei valori (inglese e italiano)
    tutti = sorted({x for c in usi.values() for x in c})
    nomi = {}
    for i in range(0, len(tutti), 50):
        j = scarica("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=labels&languages=en|it&ids=" + "|".join(tutti[i:i + 50]))
        for q, e in (j or {}).get("entities", {}).items():
            l = e.get("labels", {})
            nomi[q] = [l.get("en", {}).get("value", ""), l.get("it", {}).get("value", "")]
        time.sleep(0.5)
    with gzip.open(CART / "opere.jsonl.gz", "wt", encoding="utf8") as f:
        for q in qs:
            f.write(json.dumps(dati[q], ensure_ascii=False) + "\n")
    valori = {k: [{"q": x, "en": nomi.get(x, ["", ""])[0], "it": nomi.get(x, ["", ""])[1], "opere": n} for x, n in c.most_common()]
              for k, c in usi.items()}
    (CART / "valori.json").write_text(json.dumps(valori, ensure_ascii=False, indent=0))
    n = len(qs)
    conta = lambda f: sum(1 for d in dati.values() if f(d))
    righe = ["# Thema, passo 1: dati strutturati per tutto il catalogo", "", f"- Opere: {n}"]
    for k in PROP.values():
        c = usi.get(k, Counter())
        top = sum(v for _, v in c.most_common(200))
        righe.append(f"- {k}: {conta(lambda d: k in d)} opere, {len(c)} valori diversi; i 200 più usati coprono {top}/{sum(c.values()) or 1} usi")
    righe += [f"- con descrizione breve it o en: {conta(lambda d: 'descr_it' in d or 'descr_en' in d)}",
              f"- con voce Wikipedia it o en: {conta(lambda d: 'itwiki' in d.get('wiki', []) or 'enwiki' in d.get('wiki', []))}",
              f"- con pagina Wikisource tedesca: {conta(lambda d: 'dewikisource' in d.get('wiki', []))}",
              f"- senza nessun dato: {conta(lambda d: len(d) <= 2 and not d.get('wiki'))}"]
    (CART / "rapporto.md").write_text("\n".join(righe) + "\n")
    print("\n".join(righe))


if __name__ == "__main__":
    main()
