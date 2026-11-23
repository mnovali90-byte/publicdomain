"""Controllo automatico degli autori «una fonte» delle liste 2027 (deciso da Marco, 23/11/2026). NON CAMBIA IL SITO.

Quali autori: quelli di data/2027.json e data/es-2027.json che nel registro (data/registro/autori.json) hanno esito
«una_fonte», cioè l'anno di morte viene solo da Wikidata.
Fonti di confronto, abbinate con il codice che Wikidata stesso dà all'autore (niente abbinamenti per nome):
- Open Library: codice autore P648 -> https://openlibrary.org/authors/<codice>.json, campo death_date;
- Project Gutenberg: codice autore P1938 -> catalogo RDF in file unico (rdf-files.tar.bz2), data di morte dell'autore
  (23/11/2026: le pagine autore lette una per una non rispondevano da GitHub).
Scrive solo il rapporto: docs/registro/confronto-una-fonte-2027.md (i disaccordi, con i link) e
data/registro/confronto_una_fonte.json (tutti i risultati). Niente si corregge in automatico: i disaccordi li decide
Marco, e chi va cambiato si mette a mano in data/verifiche_manuali.json («fonti_aggiunte»)."""
import html, json, os, re, sys, time
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verifica as V   # noqa: E402  (sparql e lettura con i tentativi, come il registro)

R = Path(__file__).resolve().parent.parent
LISTE = ["2027", "es-2027"]
BUDGET = float(os.environ.get("BUDGET_MINUTI", "30"))


def autori():
    reg = json.load(open(R / "data" / "registro" / "autori.json", encoding="utf-8"))["autori"]
    out = {}
    for nome in LISTE:
        for a in json.load(open(R / "data" / f"{nome}.json", encoding="utf-8"))["autori"]:
            v = reg.get(a["wikidata"]) or {}
            if v.get("e") == "una_fonte":
                x = out.setdefault(a["wikidata"], {"nome": a.get("nome"), "morte": v.get("m"), "liste": []})
                x["liste"].append(nome)
    return out


def codici(qids):
    out = {}
    for i in range(0, len(qids), 150):
        v = " ".join("wd:" + q for q in qids[i:i + 150])
        for r in V.sparql(f"SELECT ?a ?ol ?pg WHERE {{ VALUES ?a {{ {v} }} OPTIONAL {{ ?a wdt:P648 ?ol }} OPTIONAL {{ ?a wdt:P1938 ?pg }} }}"):
            q = r["a"]["value"].rsplit("/", 1)[-1]
            c = out.setdefault(q, {"ol": set(), "pg": set()})
            if "ol" in r and r["ol"]["value"].endswith("A"):
                c["ol"].add(r["ol"]["value"])
            if "pg" in r:
                c["pg"].add(r["pg"]["value"])
    return out


def leggi(url, tipo="application/json"):
    t = V.get(url, tipo)          # tre tentativi, come il registro; None se la pagina non c'è
    if t is None:
        raise RuntimeError("pagina inesistente: " + url)
    return t


def morte_ol(c):
    d = json.loads(leggi(f"https://openlibrary.org/authors/{c}.json"))
    return V.anno(d.get("death_date")), d.get("name")


CATALOGO_PG = "https://www.gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2"
PG = {}


def catalogo_pg():
    """Gutenberg in file unico (23/11/2026, una sola prova: le pagine autore da GitHub non rispondevano).
    Il catalogo RDF (un archivio con una scheda per libro) dà per ogni autore il codice e le date:
    <pgterms:agent rdf:about="2009/agents/58849"> ... <pgterms:deathdate ...>1956</pgterms:deathdate>."""
    import tarfile, urllib.request
    req = urllib.request.Request(CATALOGO_PG, headers=V.UA)
    with urllib.request.urlopen(req, timeout=120) as r, tarfile.open(fileobj=r, mode="r|bz2") as t:
        for m in t:
            if not m.isfile():
                continue
            testo = t.extractfile(m).read().decode("utf-8", "replace")
            for a in re.finditer(r'<pgterms:agent rdf:about="[^"]*/agents/(\d+)">(.*?)</pgterms:agent>', testo, re.S):
                if a.group(1) in PG:
                    continue
                nome = re.search(r"<pgterms:name>(.*?)</pgterms:name>", a.group(2), re.S)
                morte = re.search(r"<pgterms:deathdate[^>]*>(-?\d+)</pgterms:deathdate>", a.group(2))
                PG[a.group(1)] = (int(morte.group(1)) if morte else None, html.unescape(nome.group(1)) if nome else "")


def morte_pg(c):
    if c not in PG:
        raise RuntimeError("autore non nel catalogo Gutenberg")
    return PG[c]


def main():
    inizio = time.time()
    aut = autori()
    qids = sorted(aut)
    print("autori «una fonte» in", ", ".join(LISTE), ":", len(qids), flush=True)
    cod = codici(qids)
    try:
        catalogo_pg()
        print("catalogo Gutenberg: autori letti", len(PG), flush=True)
    except Exception as e:
        print("catalogo Gutenberg non letto:", e, flush=True)
    righe, conta = {}, Counter()
    for q in qids:
        c = cod.get(q, {"ol": set(), "pg": set()})
        r = {"nome": aut[q]["nome"], "wikidata": aut[q]["morte"], "liste": aut[q]["liste"], "ol": {}, "pg": {}}
        for nf, leggi_f in (("ol", morte_ol), ("pg", morte_pg)):
            for k in sorted(c[nf]):
                if nf == "pg":
                    try:
                        y, etichetta = leggi_f(k); r[nf][k] = {"morte": y, "etichetta": etichetta}
                    except Exception as e:
                        r[nf][k] = {"errore": str(e)[:120]}
                    continue
                if time.time() - inizio > BUDGET * 60:
                    r[nf][k] = {"errore": "tempo finito"}; conta["tempo finito"] += 1; continue
                try:
                    y, etichetta = leggi_f(k)
                    r[nf][k] = {"morte": y, "etichetta": etichetta}
                except Exception as e:
                    r[nf][k] = {"errore": str(e)[:120]}
                time.sleep(0.5)
        anni = [x["morte"] for nf in ("ol", "pg") for x in r[nf].values() if isinstance(x.get("morte"), int)]
        r["esito"] = ("senza codici" if not (c["ol"] or c["pg"]) else "senza anno" if not anni
                      else "d'accordo" if all(y == r["wikidata"] for y in anni) else "disaccordo")
        conta[r["esito"]] += 1
        righe[q] = r
    (R / "data" / "registro").mkdir(parents=True, exist_ok=True)
    json.dump({"aggiornato": date.today().isoformat(), "liste": LISTE, "conteggi": dict(conta), "autori": righe},
              open(R / "data" / "registro" / "confronto_una_fonte.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    link = {"ol": "https://openlibrary.org/authors/{}", "pg": "https://www.gutenberg.org/ebooks/author/{}"}
    nomi = {"ol": "Open Library", "pg": "Project Gutenberg"}
    md = [f"# Autori «una fonte» 2027: confronto con Open Library e Project Gutenberg ({date.today().isoformat()})", "",
          "Solo rapporto: niente si corregge in automatico. Script: `scripts/confronta_una_fonte.py`.", "",
          f"- Autori controllati: {len(qids)} (liste {', '.join(LISTE)}, esito «una_fonte» nel registro).",
          "- Abbinamento con i codici che Wikidata dà all'autore (Open Library P648, Gutenberg P1938), mai per nome.", ""]
    md += [f"- {k}: {v}" for k, v in sorted(conta.items())]
    md += ["", "## Disaccordi", "", "| Autore (Wikidata) | Liste | Wikidata | Altre fonti |", "|---|---|---|---|"]
    for q, r in sorted(righe.items(), key=lambda t: t[1]["nome"] or t[0]):
        if r["esito"] != "disaccordo":
            continue
        altre = "; ".join(f"[{nomi[nf]}]({link[nf].format(k)}): {x.get('morte')}" for nf in ("ol", "pg") for k, x in r[nf].items() if x.get("morte"))
        md.append(f"| {r['nome']} ([{q}](https://www.wikidata.org/wiki/{q})) | {', '.join(r['liste'])} | {r['wikidata']} | {altre} |")
    (R / "docs" / "registro" / "confronto-una-fonte-2027.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("esiti:", dict(conta), f"| {time.time() - inizio:.0f} s")


if __name__ == "__main__":
    main()
