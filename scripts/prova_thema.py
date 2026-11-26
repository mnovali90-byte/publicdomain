"""Prova Thema (26/11/2026, ok di Marco): per 200 opere del campione raccoglie SOLO testi con fonte,
su cui poi l'AI sceglie i codici Thema. Non cambia il sito.

Scrive in docs/stima-sito/prova-thema/:
- descrizioni.json: per ogni opera le descrizioni Wikidata (it/en), generi (P136), argomenti (P921),
  luogo della narrazione (P840), periodo (P2408), forma (P7937), e l'inizio della voce Wikipedia (it/en)
  con l'indirizzo della pagina da cui viene.
- thema_<lingua>.json: la lista ufficiale dei codici Thema di EDItEUR (en, it), scaricata così com'è.
- rapporto.md: quante opere hanno trovato almeno un testo.
"""
import json, re, time, urllib.parse, urllib.request
from pathlib import Path

CART = Path("docs/stima-sito/prova-thema")
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; prova Thema)"}


def scarica(url, tentativi=4):
    for i in range(tentativi):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception as e:
            if getattr(e, "code", 0) == 404:
                return None
            time.sleep(3 * (i + 1))
    return None


def sparql(q):
    b = scarica("https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(q))
    return json.loads(b)["results"]["bindings"] if b else []


def lista_thema():
    """Trova sul sito EDItEUR i file della lista Thema in JSON (en, it) e li salva senza toccarli."""
    trovati = {}
    for pagina in ("https://www.editeur.org/151/Thema/", "https://www.editeur.org/152/Thema-Downloads/"):
        h = scarica(pagina)
        if not h:
            continue
        for href in re.findall(r'href="([^"]+)"', h.decode("utf-8", "replace")):
            u = urllib.parse.urljoin(pagina, href)
            if not re.search(r"\.json$", u, re.I) or "thema" not in u.lower():
                continue
            m = re.search(r"_(en|it)\.json$", u, re.I) or re.search(r"[_/-](en|it)[_/.-]", u, re.I)
            if m and m.group(1).lower() not in trovati:
                trovati[m.group(1).lower()] = u
    for l, u in trovati.items():
        b = scarica(u)
        if b:
            (CART / f"thema_{l}.json").write_bytes(b)
    return trovati


def main():
    camp = json.loads((CART / "campione.json").read_text())
    qs = [c["q"] for c in camp]
    dati = {q: {"q": q} for q in qs}
    for i in range(0, len(qs), 50):
        val = " ".join("wd:" + q for q in qs[i:i + 50])
        righe = sparql(f"""SELECT ?w ?p ?vl WHERE {{ VALUES ?w {{ {val} }}
          VALUES ?p {{ wdt:P136 wdt:P921 wdt:P840 wdt:P2408 wdt:P7937 wdt:P31 }}
          ?w ?p ?v. ?v rdfs:label ?vl FILTER(LANG(?vl)="en") }}""")
        nomi = {"P136": "generi", "P921": "argomenti", "P840": "luogo_narrazione", "P2408": "periodo", "P7937": "forma", "P31": "tipo"}
        for r in righe:
            q = r["w"]["value"].rsplit("/", 1)[1]
            k = nomi[r["p"]["value"].rsplit("/", 1)[1]]
            dati[q].setdefault(k, [])
            if r["vl"]["value"] not in dati[q][k]:
                dati[q][k].append(r["vl"]["value"])
        b = scarica("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=descriptions|sitelinks"
                    "&languages=it|en&sitefilter=itwiki|enwiki&ids=" + "|".join(qs[i:i + 50]))
        for q, e in (json.loads(b).get("entities", {}) if b else {}).items():
            for l in ("it", "en"):
                d = e.get("descriptions", {}).get(l)
                if d:
                    dati[q][f"descrizione_wikidata_{l}"] = d["value"]
                s = e.get("sitelinks", {}).get(f"{l}wiki")
                if s:
                    dati[q][f"_voce_{l}"] = s["title"]
        time.sleep(1)
    for q in qs:
        for l in ("it", "en"):
            t = dati[q].pop(f"_voce_{l}", None)
            if not t:
                continue
            b = scarica(f"https://{l}.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(t.replace(" ", "_"), safe=""))
            if b:
                j = json.loads(b)
                if j.get("extract"):
                    dati[q][f"wikipedia_{l}"] = {"testo": j["extract"],
                                                  "fonte": j.get("content_urls", {}).get("desktop", {}).get("page", "")}
            time.sleep(0.3)
    (CART / "descrizioni.json").write_text(json.dumps([dati[q] for q in qs], ensure_ascii=False, indent=1))
    thema = lista_thema()
    conta = lambda f: sum(1 for q in qs if f(dati[q]))
    righe = [
        "# Prova Thema: testi raccolti", "",
        f"- Opere nel campione: {len(qs)} (100 con voci Wikipedia in almeno 20 lingue, 100 meno note)",
        f"- Con inizio voce Wikipedia (it o en): {conta(lambda d: 'wikipedia_it' in d or 'wikipedia_en' in d)}",
        f"- Con almeno un genere Wikidata: {conta(lambda d: d.get('generi'))}",
        f"- Con argomento, luogo o periodo Wikidata: {conta(lambda d: d.get('argomenti') or d.get('luogo_narrazione') or d.get('periodo'))}",
        f"- Con solo la descrizione breve Wikidata: {conta(lambda d: not ('wikipedia_it' in d or 'wikipedia_en' in d) and ('descrizione_wikidata_it' in d or 'descrizione_wikidata_en' in d))}",
        f"- Senza nessun testo: {conta(lambda d: len(d) == 1)}",
        f"- Lista Thema scaricata: {', '.join(f'{l}: {u}' for l, u in thema.items()) or 'NON TROVATA'}",
    ]
    (CART / "rapporto.md").write_text("\n".join(righe) + "\n")
    print("\n".join(righe))


if __name__ == "__main__":
    main()
