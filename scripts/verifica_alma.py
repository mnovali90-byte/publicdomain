#!/usr/bin/env python3
"""Verifica del conteggio verificato (voce_alma.py) su autori British Library NUOVI, prima del rilascio. 18/11/2026.
  congela -> impronta di voce_alma.py; la misura non parte se cambia
  prove   -> 40 autori con numeri BL estratti a caso tra quelli NON usati in docs/campione-bl; per ognuno le prime 50
             notizie della ricerca di oggi con tutte le voci d'autore (senza usare la nuova regola)
  (a mano: docs/verifica-alma/esiti.json: per ogni autore, quali voci d'autore sono sue -> ogni notizia è sua o no)
  misura  -> la nuova regola sulle stesse notizie: notizie sue scartate, notizie di altri tenute; più il nuovo conteggio
             completo per autore."""
import collections, datetime as dt, hashlib, json, pathlib, random, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import alma  # noqa: E402
import voce_alma  # noqa: E402
from arricchisci import sparql  # noqa: E402

RADICE = pathlib.Path(__file__).resolve().parent.parent
import os
D = RADICE / "docs" / os.environ.get("VERIFICA_DIR", "verifica-alma")
SEME = int(os.environ.get("VERIFICA_SEME", "20261120"))
CONGELATI = ["scripts/voce_alma.py"]


def impronte():
    return {f: hashlib.sha256((RADICE / f).read_bytes()).hexdigest() for f in CONGELATI}


def congela():
    """Nota: la prima verifica (docs/verifica-alma) ha trovato 41 notizie giuste scartate (voci senza anni): con la
    versione 2 di voce_alma.py quel campione è diventato di sviluppo e la verifica si rifà in docs/verifica-alma2."""
    D.mkdir(parents=True, exist_ok=True)
    c = subprocess.run(["git", "rev-parse", "HEAD"], cwd=RADICE, capture_output=True, text=True).stdout.strip()
    (D / "regole-congelate.json").write_text(json.dumps({"commit": c, "sha256": impronte()}, indent=1), encoding="utf-8")


def alias(qids):
    out = {q: [] for q in qids}
    for i in range(0, len(qids), 50):
        v = " ".join("wd:" + q for q in qids[i:i + 50])
        for b in sparql(f"""SELECT ?a ?x WHERE {{ VALUES ?a {{ {v} }} {{ ?a wdt:P742 ?x }} UNION
              {{ ?a skos:altLabel ?x FILTER(LANG(?x) IN ("en","it","fr","es","de")) }} }}"""):
            k = b["a"]["value"].rsplit("/", 1)[-1]
            if b["x"]["value"] not in out[k]:
                out[k].append(b["x"]["value"])
    return out


def prove():
    D.mkdir(parents=True, exist_ok=True)
    cache = json.loads((RADICE / "data" / "cache_alma.json").read_text(encoding="utf-8"))
    autori = {}
    for f in sorted((RADICE / "data").glob("*[0-9][0-9][0-9][0-9].json")):
        if not f.name.startswith(("us-", "anniversari-")):
            for a in json.loads(f.read_text(encoding="utf-8")).get("autori", []):
                autori.setdefault(a["wikidata"], a)
    usati = {r["qid"] for r in json.loads((RADICE / "docs" / "campione-bl" / "prove.json").read_text(encoding="utf-8"))["autori"]}
    if D.name != "verifica-alma":       # le verifiche successive escludono anche gli autori della prima
        usati |= {r["qid"] for r in json.loads((RADICE / "docs" / "verifica-alma" / "campione.json").read_text(encoding="utf-8"))["autori"]}
    con = sorted(q for q, v in cache.items() if q in autori and q not in usati and (v.get("bl_en") or {}).get("trovato"))
    scelti = random.Random(SEME).sample(con, 40)
    al = alias(scelti)
    out = []
    c = alma.CATALOGHI["bl_en"]
    for n, q in enumerate(scelti, 1):
        a = autori[q]
        k = alma.chiave_nome(a)
        query = f'alma.creator all "{alma._ascii(k)}" and alma.language={c["lingua"]}'
        r = {"n": n, "qid": q, "nome": a["nome"], "nascita": a.get("nascita"), "morte": a.get("morte"), "alias": al[q],
             "oggi": cache[q]["bl_en"], "query": query}
        try:
            t = voce_alma.scarica(c["url"] + "?" + __import__("urllib.parse").parse.urlencode(
                {"version": "1.2", "operation": "searchRetrieve", "query": query, "recordSchema": "marcxml", "maximumRecords": "50"}))
            import re
            recs = []
            for x in re.findall(r"<record xmlns[^>]*>(.*?)</record>", t, re.S):
                voci = [" ".join(v for cc, v in re.findall(r'code="(\w)">([^<]*)<', corpo) if cc in "abcdq")
                        for corpo in re.findall(r'tag="(?:100|700|110|710)"[^>]*>(.*?)</datafield>', x, re.S)]
                tit = (re.findall(r'tag="245"[^>]*>\s*<subfield code="a">([^<]*)<', x) or [""])[0]
                recs.append({"titolo": tit[:100], "voci": voci})
            r["notizie"] = recs
        except voce_alma.ErroreTecnico as e:
            r["errore_tecnico"] = str(e)
        out.append(r)
        print(n, a["nome"], len(r.get("notizie", [])), flush=True)
    (D / "campione.json").write_text(json.dumps({"seme": SEME, "autori": out}, ensure_ascii=False, indent=1), encoding="utf-8")


def misura():
    fermo = json.loads((D / "regole-congelate.json").read_text(encoding="utf-8"))
    if fermo["sha256"] != impronte():
        sys.exit("le regole sono cambiate dopo il congelamento: questo campione non vale più come verifica")
    camp = json.loads((D / "campione.json").read_text(encoding="utf-8"))["autori"]
    esiti = json.loads((D / "esiti.json").read_text(encoding="utf-8"))
    righe, tot = [], collections.Counter()
    c = alma.CATALOGHI["bl_en"]
    for a in camp:
        mie = set(esiti[a["qid"]]["voci_sue"])
        cogn = voce_alma.cognomi(a["nome"], a["alias"])
        nato, morto = str(a["nascita"])[:4], str(a["morte"])[:4]
        cc = collections.Counter()
        for x in a.get("notizie", []):
            vera = any(v in mie for v in x["voci"]) or x["titolo"] in esiti[a["qid"]].get("titoli_suoi", [])
            tenuta = voce_alma.sua(x["voci"], cogn, nato, morto, voce_alma.iniziali(a["nome"], a["alias"]))
            cc[("sua" if vera else "di altri", "tenuta" if tenuta else "scartata")] += 1
        try:
            nuovo = voce_alma.conta_verificato(c["url"], a["query"], a["nome"], a["alias"], a["nascita"], a["morte"], dt.date.today().year)
        except voce_alma.ErroreTecnico as e:
            nuovo = {"errore_tecnico": str(e)}
        tot.update(cc)
        righe.append({"n": a["n"], "nome": a["nome"], "oggi": a["oggi"].get("edizioni"), "nuovo": nuovo,
                      "notizie": {f"{k[0]}, {k[1]}": v for k, v in cc.items()}})
        print(a["n"], a["nome"], a["oggi"].get("edizioni"), "->", nuovo.get("edizioni"), dict(cc), flush=True)
    (D / "misura.json").write_text(json.dumps({"regole": fermo, "totale_notizie": {f"{k[0]}, {k[1]}": v for k, v in tot.items()},
                                                "autori": righe}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("TOTALE", dict(tot))


def sviluppo():
    """Prima del congelamento: la nuova regola sui 69 autori già controllati (docs/campione-bl), per vedere se toglie
    gli errori trovati (Harvey, i 3 BNE) e tiene pseudonimi e veri nomi (Dion Fortune, Karl M. Baer, Rerich)."""
    D.mkdir(parents=True, exist_ok=True)
    prove_bl = json.loads((RADICE / "docs" / "campione-bl" / "prove.json").read_text(encoding="utf-8"))["autori"]
    autori = {}
    for f in sorted((RADICE / "data").glob("*[0-9][0-9][0-9][0-9].json")):
        if not f.name.startswith(("us-", "anniversari-")):
            for a in json.loads(f.read_text(encoding="utf-8")).get("autori", []):
                autori.setdefault(a["wikidata"], a)
    al = alias([r["qid"] for r in prove_bl])
    out = []
    for r in prove_bl:
        if not r.get("query") or not (r.get("oggi") or {}).get("trovato"):
            continue
        a = autori[r["qid"]]
        cat = "bl_en" if r["gruppo"].startswith("BL") else "bne_es"
        c = alma.CATALOGHI[cat]
        try:
            v = voce_alma.conta_verificato(c["url"], f'{r["query"]} and alma.language={c["lingua"]}', a["nome"], al[r["qid"]],
                                           a.get("nascita"), a.get("morte"), dt.date.today().year)
        except voce_alma.ErroreTecnico as e:
            v = {"errore_tecnico": str(e)}
        out.append({"nome": a["nome"], "catalogo": cat, "oggi": r["oggi"].get("edizioni"), "nuovo": v, "alias": al[r["qid"]][:5]})
        print(a["nome"], cat, r["oggi"].get("edizioni"), "->", v.get("edizioni"), v.get("scartate"), flush=True)
    (D / "sviluppo.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    {"congela": congela, "prove": prove, "misura": misura, "sviluppo": sviluppo}[sys.argv[1]]()
