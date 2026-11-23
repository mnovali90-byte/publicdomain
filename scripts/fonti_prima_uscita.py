"""Dati più ricchi per l'incrocio delle fonti sulle opere USA (decisione di Marco, 23/11/2026). NON CAMBIA IL SITO.

Per ogni opera delle liste USA (LISTE=2027,2028) raccoglie:
  1. da Wikidata, sull'opera e sulle sue edizioni (P629): la data di pubblicazione (P577), la rivista o il giornale di
     prima uscita (P1433, «pubblicato in»), la lingua (P407);
  2. la bibliografia nazionale nella LINGUA ORIGINALE dell'opera, col titolo originale (P1476 nella lingua dell'opera):
     - tedesco: K10plus (la DNB blocca le richieste da GitHub, prova del 19/11/2026: K10plus contiene anche i dati DNB);
     - francese: BnF; spagnolo: BNE (catalogo Alma, SRU); italiano: SBN (archivio SPARQL pubblico) se risponde;
     l'anno dell'edizione più vecchia con lo stesso titolo e lo stesso autore.
Scrive data/fonti_prima_uscita.json {qid: {"lingua", "titolo", "wikidata": {...}, "catalogo": {"fonte", "anno", "record"}}}.
Lo leggono regole.incrocio_opera (via scripts/collaudo_incrocio.py e scripts/incrocio_opere.py)."""
import html, json, os, re, sys, time, urllib.parse
from pathlib import Path

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "scripts"))
import verifica_anni_usa as VU   # noqa: E402  (bnf, k10plus, lettura con i tentativi, confronto dei titoli)

LINGUE = {"Q150": "fr", "Q188": "de", "Q1321": "es", "Q652": "it", "Q1860": "en"}
BUDGET = float(os.environ.get("BUDGET_MINUTI", "40")) * 60


def wikidata(qids):
    out = {q: {"p577": [], "riviste": [], "edizioni": [], "lingue": [], "titoli": {}} for q in qids}
    for i in range(0, len(qids), 80):
        v = " ".join("wd:" + q for q in qids[i:i + 80])
        q1 = f"""SELECT ?o ?d ?riv ?rivLabel ?rd ?lg ?t WHERE {{ VALUES ?o {{ {v} }}
                  OPTIONAL {{ ?o wdt:P577 ?d }} OPTIONAL {{ ?o wdt:P407 ?lg }} OPTIONAL {{ ?o wdt:P1476 ?t }}
                  OPTIONAL {{ ?o p:P1433 ?st . ?st ps:P1433 ?riv . OPTIONAL {{ ?st pq:P577 ?rd }} }}
                  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,fr,de,es,it". }} }}"""
        q2 = f"""SELECT ?o ?ed ?d ?lg ?riv WHERE {{ VALUES ?o {{ {v} }} ?ed wdt:P629 ?o .
                  OPTIONAL {{ ?ed wdt:P577 ?d }} OPTIONAL {{ ?ed wdt:P407 ?lg }} OPTIONAL {{ ?ed wdt:P1433 ?riv }} }}"""
        for r in sparql(q1):
            q = r["o"]["value"].rsplit("/", 1)[-1]; x = out[q]
            if "d" in r: x["p577"].append(r["d"]["value"][:10])
            if "lg" in r: x["lingue"].append(r["lg"]["value"].rsplit("/", 1)[-1])
            if "t" in r: x["titoli"][r["t"].get("xml:lang", "?")] = r["t"]["value"]
            if "riv" in r: x["riviste"].append({"rivista": r.get("rivLabel", {}).get("value"), "data": r.get("rd", {}).get("value", "")[:10] or None})
        for r in sparql(q2):
            q = r["o"]["value"].rsplit("/", 1)[-1]
            out[q]["edizioni"].append({"data": r.get("d", {}).get("value", "")[:10] or None,
                                       "lingua": r.get("lg", {}).get("value", "").rsplit("/", 1)[-1] or None,
                                       "rivista": bool(r.get("riv"))})
        time.sleep(1)
    for x in out.values():
        x["p577"] = sorted(set(x["p577"])); x["lingue"] = sorted(set(x["lingue"]))
    return out


def sparql(q):
    t = VU.scarica("https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(q), timeout=120)
    return json.loads(t)["results"]["bindings"] if t else []


def bne(titolo, cognome):
    q = f'alma.title="{titolo}" and alma.creator="{cognome}"'
    u = "https://catalogo.bne.es/view/sru/34BNE_INST?" + urllib.parse.urlencode(
        {"version": "1.2", "operation": "searchRetrieve", "query": q, "recordSchema": "marcxml", "maximumRecords": "50"})
    x = VU.scarica(u, timeout=90)
    if not x:
        return None, 0
    recs, anni = VU.record(x.decode("utf-8", "replace")), []
    for rec in recs:
        t = " ".join(f.get("a", "") for f in VU.campi(rec, "245"))
        if not VU.stesso_titolo(html.unescape(t), titolo):
            continue
        a = VU.controllo(rec, "008")[7:11]
        if a.isdigit():
            anni.append(int(a))
    time.sleep(1)
    return (min(anni) if anni else None), len(recs)


def k10plus_tutte(titolo, cognome):
    """K10plus senza filtro sugli anni (VU.k10plus guarda solo i 3 anni prima della lista): l'edizione più vecchia."""
    q = f'pica.tit="{titolo}" and pica.per="{cognome}"'
    u = "https://sru.k10plus.de/opac-de-627?" + urllib.parse.urlencode(
        {"version": "1.1", "operation": "searchRetrieve", "query": q, "recordSchema": "marcxml", "maximumRecords": "100"})
    x = VU.scarica(u, timeout=90)
    if not x:
        return None, 0
    recs, anni = VU.record(x.decode("utf-8", "replace")), []
    for rec in recs:
        t = " ".join(f.get("a", "") + " " + f.get("b", "") for f in VU.campi(rec, "245"))
        if not VU.stesso_titolo(html.unescape(t), titolo):
            continue
        a = VU.controllo(rec, "008")[7:11]
        if a.isdigit():
            anni.append(int(a))
    time.sleep(1)
    return (min(anni) if anni else None), len(recs)


def sbn(titolo, cognome):
    """SBN, archivio SPARQL pubblico (BIBFRAME): istanze con titolo e anno. Se non risponde: None."""
    q = f"""PREFIX bf: <http://id.loc.gov/ontologies/bibframe/>
            SELECT ?anno WHERE {{ ?i bf:title/bf:mainTitle ?t . FILTER(CONTAINS(LCASE(STR(?t)), "{titolo.lower()[:60]}"))
            ?i bf:provisionActivity/bf:date ?anno }} LIMIT 200"""
    t = VU.scarica("https://triplestore.iccu.sbn.it/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"}), timeout=120)
    if not t:
        return None, 0
    anni = [int(m) for r in json.loads(t)["results"]["bindings"] for m in re.findall(r"1[5-9]\d\d", r["anno"]["value"])]
    return (min(anni) if anni else None), len(anni)


def main():
    inizio = time.time()
    opere = {}
    for anno in os.environ.get("LISTE", "2027,2028").split(","):
        for o in json.load(open(R / "data" / f"us-{anno}.json", encoding="utf-8"))["opere"]:
            opere[o["qid"]] = o
    # anche le opere tolte o spostate dalle liste (per il collaudo sulle decisioni del 23/11/2026)
    for x in json.load(open(R / "data" / "registro" / "liste_spostati.json", encoding="utf-8")).get("usa_gia_libere", []):
        opere.setdefault(x["qid"], {"qid": x["qid"], "titolo": x.get("titolo"), "autori": []})
    for x in json.load(open(R / "data" / "registro" / "liste_spostati.json", encoding="utf-8")).get("usa_spostate", []):
        opere.setdefault(x["qid"], x.get("opera") or {"qid": x["qid"], "titolo": x.get("titolo"), "autori": []})
    qids = sorted(opere)
    print("opere:", len(qids), flush=True)
    wd = wikidata(qids)
    out = {}
    for q in qids:
        w = wd[q]
        lg = next((LINGUE[l] for l in w["lingue"] if l in LINGUE), None)
        titolo = w["titoli"].get(lg) if lg else None
        cognome = ((opere[q].get("autori") or [{}])[0].get("nome") or "").split()[-1:] or [""]
        r = {"lingua": lg, "titolo": titolo, "wikidata": w, "catalogo": None}
        if lg in ("de", "fr", "es", "it") and titolo and time.time() - inizio < BUDGET:
            try:
                if lg == "de":
                    (y, n), f = k10plus_tutte(titolo, cognome[0]), "k10plus"
                elif lg == "fr":
                    (y, n), f = VU.bnf(titolo, cognome[0]), "bnf"
                elif lg == "es":
                    (y, n), f = bne(titolo, cognome[0]), "bne"
                else:
                    (y, n), f = sbn(titolo, cognome[0]), "sbn"
                r["catalogo"] = {"fonte": f, "anno": y, "record": n}
            except Exception as e:
                r["catalogo"] = {"errore": str(e)[:150]}
        out[q] = r
    json.dump({"liste": os.environ.get("LISTE", "2027,2028"), "opere": out},
              open(R / "data" / "fonti_prima_uscita.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("con un catalogo nella lingua originale:", sum(1 for x in out.values() if (x["catalogo"] or {}).get("anno")),
          "| con data Wikidata:", sum(1 for x in out.values() if x["wikidata"]["p577"]),
          "| con rivista:", sum(1 for x in out.values() if x["wikidata"]["riviste"]), f"| {time.time() - inizio:.0f} s")


if __name__ == "__main__":
    main()
