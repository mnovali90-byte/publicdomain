"""Prova Thema, giro 2 (26/11/2026, ok di Marco): per le opere difficili (da decidere, senza testo)
e per le sicure meno note cerca altre fonti aperte, SOLO attraverso i collegamenti che Wikidata
dichiara sulla scheda dell'opera (niente ricerca per titolo, per evitare libri sbagliati con lo stesso titolo):

- «edizione o traduzione di» (P629) -> l'opera originale, con descrizioni, Wikipedia it/en, generi, argomenti
- Project Gutenberg (P2034): argomenti della Library of Congress e classificazione LoC
- Open Library (P648): argomenti, luoghi, periodi, descrizione
- Biblioteca nazionale tedesca, GND (P227) tramite lobid.org: categorie e forma dell'opera
- Wikisource tedesca (collegamento della scheda): categorie della pagina (articoli della Gartenlaube)
- «pubblicato in» (P1433), per riconoscere gli articoli di rivista

Scrive docs/stima-sito/prova-thema/descrizioni2.json e rapporto2.md. Non cambia il sito.
"""
import json, re, time, urllib.parse, urllib.request
from pathlib import Path

CART = Path("docs/stima-sito/prova-thema")
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; prova Thema 2)", "Accept": "application/json"}


def scarica(url, json_=True, tentativi=4):
    for i in range(tentativi):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                b = r.read()
                return json.loads(b) if json_ else b.decode("utf-8", "replace")
        except Exception as e:
            if getattr(e, "code", 0) in (404, 410):
                return None
            time.sleep(3 * (i + 1))
    return None


def entita(qs):
    out = {}
    for i in range(0, len(qs), 50):
        j = scarica("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=claims|descriptions|sitelinks|labels"
                    "&languages=it|en&ids=" + "|".join(qs[i:i + 50]))
        out.update((j or {}).get("entities", {}))
        time.sleep(1)
    return out


def valori(e, p):
    r = []
    for c in e.get("claims", {}).get(p, []):
        v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(v, dict) and "id" in v:
            r.append(v["id"])
        elif isinstance(v, str):
            r.append(v)
    return r


def etichette(qs):
    qs = sorted(set(qs))
    out = {}
    for i in range(0, len(qs), 50):
        j = scarica("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=labels&languages=en|it&ids=" + "|".join(qs[i:i + 50]))
        for q, e in (j or {}).get("entities", {}).items():
            l = e.get("labels", {})
            out[q] = (l.get("en") or l.get("it") or {}).get("value", q)
        time.sleep(1)
    return out


def wikipedia(e):
    r = {}
    for l in ("it", "en"):
        s = e.get("sitelinks", {}).get(f"{l}wiki")
        if not s:
            continue
        j = scarica(f"https://{l}.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(s["title"].replace(" ", "_"), safe=""))
        if j and j.get("extract"):
            r[f"wikipedia_{l}"] = {"testo": j["extract"], "fonte": j.get("content_urls", {}).get("desktop", {}).get("page", "")}
        time.sleep(0.3)
    return r


def gutenberg(n):
    t = scarica(f"https://www.gutenberg.org/ebooks/{n}.rdf", json_=False)
    if not t:
        return None
    sogg, lcc = [], []
    for blocco in re.findall(r"<dcterms:subject>(.*?)</dcterms:subject>", t, re.S):
        v = re.search(r"<rdf:value>(.*?)</rdf:value>", blocco, re.S)
        if not v:
            continue
        (lcc if "LCC" in blocco else sogg).append(v.group(1).strip())
    scaff = [s.strip() for s in re.findall(r"<pgterms:bookshelf>.*?<rdf:value>(.*?)</rdf:value>", t, re.S)]
    return {"fonte": f"https://www.gutenberg.org/ebooks/{n}", "argomenti_LoC": sogg, "classe_LoC": lcc, "scaffali": scaff}


def openlibrary(ol):
    if ol.endswith("M"):
        j = scarica(f"https://openlibrary.org/books/{ol}.json")
        w = (j or {}).get("works", [{}])[0].get("key")
        if not w:
            return None
        ol = w.rsplit("/", 1)[1]
    j = scarica(f"https://openlibrary.org/works/{ol}.json")
    if not j:
        return None
    d = j.get("description")
    d = d.get("value") if isinstance(d, dict) else d
    r = {"fonte": f"https://openlibrary.org/works/{ol}", "argomenti": j.get("subjects", [])[:25],
         "luoghi": j.get("subject_places", []), "periodi": j.get("subject_times", [])}
    if d:
        r["descrizione"] = d[:1500]
    return r


def gnd(n):
    j = scarica(f"https://lobid.org/gnd/{urllib.parse.quote(n)}.json")
    if not j:
        return None
    lab = lambda xs: [x.get("label") for x in (xs or []) if x.get("label")]
    return {"fonte": f"https://d-nb.info/gnd/{n}", "nome": j.get("preferredName"),
            "categorie": lab(j.get("gndSubjectCategory")), "forma": lab(j.get("formOfWorkAndExpression")),
            "argomenti": lab(j.get("topic")) + lab(j.get("relatedTerm"))}


def wikisource(e):
    s = e.get("sitelinks", {}).get("dewikisource")
    if not s:
        return None
    j = scarica("https://de.wikisource.org/w/api.php?action=query&format=json&prop=categories&clshow=!hidden&cllimit=50&titles="
                + urllib.parse.quote(s["title"]))
    cats = []
    for p in (j or {}).get("query", {}).get("pages", {}).values():
        cats += [c["title"].replace("Kategorie:", "") for c in p.get("categories", [])]
    return {"fonte": "https://de.wikisource.org/wiki/" + urllib.parse.quote(s["title"].replace(" ", "_")), "categorie": cats}


def main():
    qs = json.loads((CART / "obiettivi2.json").read_text())
    E = entita(qs)
    orig = {q: (valori(E.get(q, {}), "P629") or [None])[0] for q in qs}
    EO = entita(sorted({o for o in orig.values() if o}))
    PROP = {"P136": "generi", "P921": "argomenti", "P840": "luogo_narrazione", "P2408": "periodo", "P7937": "forma", "P31": "tipo", "P1433": "pubblicato_in"}
    servono = []
    for e in list(E.values()) + list(EO.values()):
        for p in PROP:
            servono += valori(e, p)
    NOMI = etichette(servono)
    out, conta = [], {k: 0 for k in ("originale", "wp_originale", "gutenberg", "openlibrary", "gnd", "wikisource", "almeno_una")}
    for q in qs:
        e = E.get(q, {})
        r = {"q": q}
        for p, k in PROP.items():
            if p in ("P1433",) and valori(e, p):
                r[k] = [NOMI.get(x, x) for x in valori(e, p)]
        o = orig[q]
        if o and o in EO:
            eo = EO[o]
            ro = {"q": o, "titolo": (eo.get("labels", {}).get("en") or eo.get("labels", {}).get("it") or {}).get("value", o),
                  "fonte": f"https://www.wikidata.org/wiki/{o}"}
            for l in ("it", "en"):
                d = eo.get("descriptions", {}).get(l)
                if d:
                    ro[f"descrizione_wikidata_{l}"] = d["value"]
            for p, k in PROP.items():
                if valori(eo, p):
                    ro[k] = [NOMI.get(x, x) for x in valori(eo, p)]
            ro.update(wikipedia(eo))
            r["originale"] = ro
            conta["originale"] += 1
            conta["wp_originale"] += any(k.startswith("wikipedia_") for k in ro)
        fonti_id = [e] + ([EO[o]] if o and o in EO else [])
        for ee in fonti_id:
            if "gutenberg" not in r and valori(ee, "P2034"):
                g = gutenberg(valori(ee, "P2034")[0])
                if g and (g["argomenti_LoC"] or g["classe_LoC"]):
                    r["gutenberg"] = g
            if "openlibrary" not in r and valori(ee, "P648"):
                x = openlibrary(valori(ee, "P648")[0])
                if x and (x["argomenti"] or x.get("descrizione")):
                    r["openlibrary"] = x
            if "gnd" not in r and valori(ee, "P227"):
                x = gnd(valori(ee, "P227")[0])
                if x and (x["categorie"] or x["forma"] or x["argomenti"]):
                    r["gnd"] = x
            if "wikisource" not in r:
                x = wikisource(ee)
                if x and x["categorie"]:
                    r["wikisource"] = x
            time.sleep(0.5)
        for k in ("gutenberg", "openlibrary", "gnd", "wikisource"):
            conta[k] += k in r
        conta["almeno_una"] += any(k in r for k in ("originale", "gutenberg", "openlibrary", "gnd", "wikisource"))
        out.append(r)
    (CART / "descrizioni2.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    righe = ["# Prova Thema, giro 2: fonti in più tramite i collegamenti di Wikidata", "",
             f"- Opere cercate: {len(qs)} (da decidere, senza testo, sicure meno note)",
             f"- Edizioni o traduzioni ricondotte all'opera originale: {conta['originale']} (con voce Wikipedia dell'originale: {conta['wp_originale']})",
             f"- Con argomenti Gutenberg (Library of Congress): {conta['gutenberg']}",
             f"- Con argomenti o descrizione Open Library: {conta['openlibrary']}",
             f"- Con categorie della biblioteca nazionale tedesca (GND): {conta['gnd']}",
             f"- Con categorie di Wikisource tedesca: {conta['wikisource']}",
             f"- Con almeno una fonte nuova: {conta['almeno_una']}"]
    (CART / "rapporto2.md").write_text("\n".join(righe) + "\n")
    print("\n".join(righe))


if __name__ == "__main__":
    main()
