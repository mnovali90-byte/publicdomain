"""GIRO ANNUALE DEGLI AUTORI MANCANTI (proposta del 23/11/2026, docs/giri-automatici.md). NON CAMBIA IL SITO.

Domanda: quali scrittori morti nell'anno della lista NON sono nelle nostre liste? Le liste nascono da Wikidata
(scripts/aggiorna.py: morte P570 nell'anno, professione fra quelle di scrittore). Mancano quindi gli autori a cui
Wikidata non dà la data di morte, la dà in un altro anno, o non dà una professione da scrittore.
Fonti indipendenti dalla nostra domanda a Wikidata:
  1. Wikipedia, categorie dei morti dell'anno in più lingue (en, it, de, fr, es, pl), incrociate con le categorie da
     scrittore della stessa voce (parole come writers, poets, novelists, scrittori, Schriftsteller, écrivain...);
  2. Biblioteca nazionale tedesca (GND, lobid.org): persone con data di morte nell'anno e professione di scrittore.
Per ogni candidato si chiede poi a Wikidata cosa sa (data di morte, professioni, numero di lingue): così il rapporto
dice PERCHÉ manca. Scrive docs/autori-mancanti-<anno>.md e data/registro/autori_mancanti_<anno>.json.
Niente entra nelle liste in automatico: chi va aggiunto si decide con le fonti (data/verifiche_manuali.json).
Uso: ANNO=2027 python3 scripts/autori_mancanti.py (europa: morti nel 1956; Spagna: morti nel 1946)."""
import glob, json, os, re, sys, time, urllib.parse
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verifica as V            # noqa: E402  (lettura con i tentativi e sparql)
import regole as RG             # noqa: E402

R = Path(__file__).resolve().parent.parent
ANNO = int(os.environ.get("ANNO", "2027"))
BUDGET = float(os.environ.get("BUDGET_MINUTI", "40")) * 60
CATEGORIE = {"en": "Category:{m} deaths", "it": "Categoria:Morti nel {m}", "de": "Kategorie:Gestorben {m}",
             "fr": "Catégorie:Décès en {m}", "es": "Categoría:Fallecidos en {m}", "pl": "Kategoria:Zmarli w {m}"}
SCRITTORE = re.compile(r"writer|poet|novelist|dramatist|playwright|essayist|author|scrittor|poet[ie]|romanzier|drammaturg|"
                       r"schriftsteller|dichter|lyriker|autor|écrivain|poète|romancier|dramaturge|escritor|poeta|novelista|"
                       r"pisarz|poeta|prozaik|dramaturg", re.I)
SCRITTORI_WD = {"Q36180", "Q6625963", "Q49757", "Q214917", "Q11774202", "Q333634"}   # le stesse professioni di scripts/aggiorna.py (OCCUPAZIONI)


def nelle_liste():
    q = set()
    for f in glob.glob(str(R / "data" / "[0-9][0-9][0-9][0-9].json")) + glob.glob(str(R / "data" / "es-[0-9][0-9][0-9][0-9].json")):
        q |= {a["wikidata"] for a in json.load(open(f, encoding="utf-8")).get("autori", [])}
    return q


def wiki(lingua, morte, inizio):
    """Membri della categoria dei morti dell'anno: {qid: (titolo, scrittore secondo le categorie)}."""
    api = f"https://{lingua}.wikipedia.org/w/api.php"
    out, cont = {}, {}
    while time.time() - inizio < BUDGET:
        par = {"action": "query", "format": "json", "generator": "categorymembers", "gcmtitle": CATEGORIE[lingua].format(m=morte),
               "gcmnamespace": 0, "gcmlimit": 500, "prop": "pageprops|categories", "ppprop": "wikibase_item",
               "cllimit": "max", "clshow": "!hidden", **cont}
        d = json.loads(V.get(api + "?" + urllib.parse.urlencode(par)) or "{}")
        for p in (d.get("query") or {}).get("pages", {}).values():
            q = (p.get("pageprops") or {}).get("wikibase_item")
            if not q:
                continue
            cats = " ".join(c["title"] for c in p.get("categories", []))
            vecchio = out.get(q, (p["title"], False))
            out[q] = (p["title"], vecchio[1] or bool(SCRITTORE.search(cats)))
        if "continue" not in d:
            break
        cont = d["continue"]
        time.sleep(0.3)
    return out


def gnd(morte):
    """Persone della GND con morte nell'anno e una professione da scrittore: {nome: (gnd, anno)} (senza codice Wikidata
    quando la GND non lo dà)."""
    out, da = {}, 0
    q = f'dateOfDeath:{morte}* AND professionOrOccupation.label:(Schriftsteller* OR Lyriker* OR Dramatiker* OR Erzähler* OR Dichter*)'
    while True:
        u = "https://lobid.org/gnd/search?" + urllib.parse.urlencode({"q": q, "format": "json", "size": 100, "from": da})
        d = json.loads(V.get(u) or "{}")
        for m in d.get("member", []):
            wd = [x.get("id", "").rsplit("/", 1)[-1] for x in m.get("sameAs", []) if "wikidata.org" in x.get("id", "")]
            out[m.get("gndIdentifier")] = {"nome": m.get("preferredName"), "qid": wd[0] if wd else None}
        da += 100
        if da >= (d.get("totalItems") or 0) or da > 5000:
            break
        time.sleep(0.3)
    return out


def wikidata(qids):
    info = {}
    for i in range(0, len(qids), 200):
        v = " ".join("wd:" + q for q in qids[i:i + 200])
        for r in V.sparql(f"""SELECT ?a ?m ?p ?sl WHERE {{ VALUES ?a {{ {v} }} ?a wikibase:sitelinks ?sl .
                               OPTIONAL {{ ?a wdt:P570 ?m }} OPTIONAL {{ ?a wdt:P106 ?p }} }}"""):
            q = r["a"]["value"].rsplit("/", 1)[-1]
            x = info.setdefault(q, {"morti": set(), "prof": set(), "lingue": int(r["sl"]["value"])})
            if "m" in r:
                y = V.anno(r["m"]["value"])
                if y:
                    x["morti"].add(y)
            if "p" in r:
                x["prof"].add(r["p"]["value"].rsplit("/", 1)[-1])
    return info


def main():
    inizio = time.time()
    liste = nelle_liste()
    out = {}
    for tipo in ("it", "es"):
        morte = RG.morti_liberi_nel(ANNO, tipo)
        cand = defaultdict(lambda: {"fonti": set(), "titoli": {}})
        for lg in CATEGORIE:
            for q, (tit, scr) in wiki(lg, morte, inizio).items():
                if scr and q not in liste:
                    cand[q]["fonti"].add(f"Wikipedia {lg}"); cand[q]["titoli"][lg] = tit
        for g, x in gnd(morte).items():
            if x["qid"] and x["qid"] not in liste:
                cand[x["qid"]]["fonti"].add("GND"); cand[x["qid"]]["titoli"].setdefault("gnd", x["nome"])
        info = wikidata(sorted(cand))
        righe = []
        for q, c in cand.items():
            w = info.get(q, {"morti": set(), "prof": set(), "lingue": 0})
            if not w["morti"]:
                perche = "Wikidata non ha la data di morte"
            elif morte not in w["morti"]:
                perche = f"Wikidata dà un altro anno di morte ({', '.join(map(str, sorted(w['morti'])))})"
            elif not (w["prof"] & SCRITTORI_WD):
                perche = "Wikidata non lo segna come scrittore"
            else:
                perche = "altro (da controllare: professione o regola della lista)"
            righe.append({"qid": q, "nome": next(iter(c["titoli"].values())), "fonti": sorted(c["fonti"]), "perche": perche,
                          "lingue": w["lingue"], "morti_wikidata": sorted(w["morti"])})
        righe.sort(key=lambda r: (-len(r["fonti"]), -r["lingue"]))
        out["europa" if tipo == "it" else "spagna"] = {"morte": morte, "candidati": righe}
    json.dump({"aggiornato": date.today().isoformat(), "anno": ANNO, **out},
              open(R / "data" / "registro" / f"autori_mancanti_{ANNO}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    md = [f"# Autori mancanti nelle liste {ANNO} ({date.today().isoformat()})", "",
          "Solo rapporto: niente entra nelle liste in automatico. Script `scripts/autori_mancanti.py`.", "",
          "Candidati: scrittori morti nell'anno secondo Wikipedia (categorie dei morti dell'anno, en it de fr es pl, con una "
          "categoria da scrittore) o secondo la GND, che non sono nelle nostre liste. Prima quelli con più fonti.", ""]
    for k, x in out.items():
        md += [f"## {'Europa' if k == 'europa' else 'Spagna'}: morti nel {x['morte']}", "",
               f"Candidati: {len(x['candidati'])}", "", "| Autore | Fonti | Lingue Wikipedia | Perché manca |", "|---|---|---|---|"]
        md += [f"| {r['nome']} ([{r['qid']}](https://www.wikidata.org/wiki/{r['qid']})) | {', '.join(r['fonti'])} | {r['lingue']} | {r['perche']} |"
               for r in x["candidati"][:300]]
        md.append("")
    (R / "docs" / f"autori-mancanti-{ANNO}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print({k: len(x["candidati"]) for k, x in out.items()}, f"| {time.time() - inizio:.0f} s")


if __name__ == "__main__":
    main()
