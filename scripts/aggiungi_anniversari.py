"""Aggiunge al calendario anniversari le voci scelte a mano in data/anniversari_aggiunte.json.

Per ogni voce: date di Wikidata (nascita P569 o morte P570, con la conversione dal calendario giuliano),
seconda fonte Wikipedia (inglese e italiano, più la lingua dell'autore se c'è): la data deve comparire nel testo o
nel riquadro della voce. Se Wikipedia dà un giorno diverso la voce NON entra e finisce nel resoconto.
Poi le schede (come anniversari.py), l'unione con data/anniversari-<anno>.json e le pagine del calendario.
Resoconto in docs/stima-sito/anniv-aggiunte.json.
"""
import json, pathlib, re, sys, time, urllib.parse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import anniversari as A

DATA = A.DATA
LINGUE = ["en", "it", "fr", "de", "es"]


def scarica(u):
    """Come json_url, ma con attese lunghe quando il servizio risponde «troppe richieste» (429)."""
    import urllib.request, urllib.error
    for t in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=A.UA), timeout=60) as f:
                return json.load(f)
        except urllib.error.HTTPError as e:
            time.sleep(30 * (t + 1) if e.code == 429 else 5)
        except Exception:
            time.sleep(5 * (t + 1))
    return None


def entita(qids):
    out = {}
    for i in range(0, len(qids), 40):
        r = scarica("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
            "action": "wbgetentities", "ids": "|".join(qids[i:i + 40]), "props": "labels|descriptions|claims|sitelinks", "format": "json"}))
        out.update((r or {}).get("entities", {}))
        time.sleep(2)
    return out


def _vecchia_entita(qids):
    r = A.json_url("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
        "action": "wbgetentities", "ids": "|".join(qids), "props": "labels|descriptions|claims|sitelinks", "format": "json"}))
    return (r or {}).get("entities", {})


def cerca(nome, prop, anno):
    r = scarica("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
        "action": "wbsearchentities", "search": nome, "language": "en", "type": "item", "limit": 7, "format": "json"}))
    ids = [x["id"] for x in (r or {}).get("search", [])]
    for q, e in entita(ids).items():
        for c in e.get("claims", {}).get(prop, []):
            t = c["mainsnak"].get("datavalue", {}).get("value", {}).get("time", "")
            if t[1:5] == str(anno):
                return q
    return None


def data_wd(e, prop):
    out = set()
    for c in e.get("claims", {}).get(prop, []):
        v = c["mainsnak"].get("datavalue", {}).get("value", {})
        t, pr = v.get("time", ""), v.get("precision", 0)
        m = re.match(r"\+(\d{4})-(\d\d)-(\d\d)", t)
        if not m or pr < 11:
            continue
        y, mo, d = int(m[1]), int(m[2]), int(m[3])
        if v.get("calendarmodel", "").endswith("Q1985786"):
            g = A.giuliano_a_gregoriano(y, mo, d); y, mo, d = g.year, g.month, g.day
        out.add((y, mo, d))
    return out


def date_wikipedia(titolo, lg, anno):
    """Tutte le date (mese, giorno) dell'anno atteso nell'inizio della voce e nel riquadro."""
    r = scarica(f"https://{lg}.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main", "redirects": 1,
        "titles": titolo, "format": "json", "formatversion": 2}))
    try:
        t = r["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"][:12000]
    except Exception:
        return None
    mesi = A.MESI_L[lg]
    nomi = "|".join(sorted(mesi, key=len, reverse=True))
    out = set()
    for m in re.finditer(rf"\|\s*{anno}\s*\|\s*(\d{{1,2}})\s*\|\s*(\d{{1,2}})", t):      # {{birth date|1902|1|20}}
        out.add((int(m[1]), int(m[2])))
    for m in re.finditer(rf"\b(\d{{1,2}})(?:º|°|er|\.)?\s+(?:de\s+)?({nomi})\s+(?:de\s+)?{anno}\b", t, re.I):
        out.add((mesi[m[2].lower()], int(m[1])))
    for m in re.finditer(rf"\b({nomi})\s+(\d{{1,2}}),?\s+{anno}\b", t, re.I):
        out.add((mesi[m[1].lower()], int(m[2])))
    for m in re.finditer(rf"{anno}-(\d\d)-(\d\d)", t):
        out.add((int(m[1]), int(m[2])))
    return out


def main():
    cfg = json.loads((DATA / "anniversari_aggiunte.json").read_text(encoding="utf-8"))
    anno_cal = cfg["anno"]
    f = DATA / f"anniversari-{anno_cal}.json"
    cal = json.loads(f.read_text(encoding="utf-8"))
    gia = {(v["tipo"], v["qid"]) for v in cal["voci"]}
    resoconto, nuove = [], []
    tutte = entita([x["qid"] for x in cfg["voci"] if x.get("qid")])
    for x in cfg["voci"]:
        prop = "P569" if x["tipo"] == "nascita" else "P570"
        q = x.get("qid") or cerca(x["cerca"], prop, x["anno"])
        if not q:
            resoconto.append({"voce": x.get("nota"), "esito": "non trovata su Wikidata"}); continue
        if (x["tipo"], q) in gia:
            resoconto.append({"voce": x.get("nota"), "qid": q, "esito": "già nel calendario"}); continue
        e = tutte.get(q) or entita([q]).get(q)
        if not e:
            resoconto.append({"voce": x.get("nota"), "qid": q, "esito": "Wikidata non ha risposto: da rifare"}); continue
        anno_ev = anno_cal - x["anni"]
        date = {(mo, d) for y, mo, d in data_wd(e, prop) if y == anno_ev}
        if len(date) != 1:
            resoconto.append({"voce": x.get("nota"), "qid": q, "esito": f"date Wikidata non univoche: {sorted(date)}"}); continue
        mg = next(iter(date))
        conferme, altre = [], set()
        for lg in LINGUE:
            sl = e.get("sitelinks", {}).get(lg + "wiki")
            if not sl:
                continue
            dw = date_wikipedia(sl["title"], lg, anno_ev)
            time.sleep(1)
            if dw is None:
                continue
            if mg in dw:
                conferme.append(lg)
            else:
                altre |= dw
        if not conferme:
            resoconto.append({"voce": x.get("nota"), "qid": q, "esito": "non confermata da Wikipedia", "wikidata": mg, "wikipedia": sorted(altre)}); continue
        lab = lambda l: (e.get("labels", {}).get(l) or {}).get("value")
        v = {"tipo": x["tipo"], "qid": q, "nome": lab("en") or lab("it"), "it": lab("it"), "desc": (e.get("descriptions", {}).get("en") or {}).get("value"),
             "autore": None, "autore_qid": None, "anno": anno_ev, "anni": x["anni"], "pagine": len(e.get("sitelinks", {})),
             "mese": mg[0], "giorno": mg[1], "fonte_data": "wikidata+wikipedia (" + ",".join(conferme) + "); aggiunta a mano 19/11/2026"}
        nuove.append(v)
        resoconto.append({"voce": x.get("nota"), "qid": q, "esito": "aggiunta", "data": mg, "confermata_da": conferme})
    sch = A.schede_voci(nuove) if nuove else {}
    for v in nuove:
        v["scheda"] = sch.get(v["qid"])
    cal["voci"] += nuove
    cal["voci"].sort(key=lambda v: ((v["mese"] or 13), (v["giorno"] or 99), -v["pagine"]))
    f.write_text(json.dumps(cal, ensure_ascii=False, indent=1), encoding="utf-8")
    pathlib.Path("docs/stima-sito").mkdir(parents=True, exist_ok=True)
    pathlib.Path("docs/stima-sito/anniv-aggiunte.json").write_text(json.dumps(resoconto, ensure_ascii=False, indent=1), encoding="utf-8")
    import calendario
    calendario.crea_calendario()
    print(json.dumps(resoconto, ensure_ascii=False, indent=1))
    print(f"aggiunte: {len(nuove)}; voci nel calendario: {len(cal['voci'])}")


if __name__ == "__main__":
    main()
