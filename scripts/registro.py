"""REGISTRO UNICO: lettura dei dati decisi, in un posto solo (20/11/2026).
Chi deve sapere l'anno USA di un'opera chiama anni_usa(): niente più due file letti in modi diversi.
La regola che decide sta in scripts/regole.py (anno_usa_confermato)."""
import json
from pathlib import Path

from regole import anno_usa_confermato, anno_prima_pubblicazione

R = Path(__file__).resolve().parent.parent


def _leggi(p, vuoto):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return vuoto


def voci_usa():
    """Le verifiche grezze dei due raccoglitori: {opera: [(origine, voce)]}.
      - liste dei prossimi anni: scripts/verifica_anni_usa.py -> data/us-anni-verificati.json (per anno di lista);
      - opere dello Storico libere solo negli USA: storico/verifica_anni.py -> data/storico/anni_verificati.json."""
    out = {}
    for q, v in _leggi(R / "data" / "storico" / "anni_verificati.json", {}).items():
        out.setdefault(q, []).append(("storico", v))
    for anno, voci in _leggi(R / "data" / "us-anni-verificati.json", {}).items():
        for q, v in voci.items():
            out.setdefault(q, []).append(("lista", v))
    # 22/11/2026: anche le liste della Duke (data/storico/duke.json, storico/duke.py) contano come seconda fonte;
    # prima servivano solo ad aggiungere opere mancanti, e per esempio Il grande Gatsby restava senza conferma
    for anno, x in _leggi(R / "data" / "storico" / "duke.json", {}).items():
        for b in x.get("libri", []):
            q = (b.get("wd") or {}).get("qid")
            if q and isinstance(b.get("pub"), int):
                out.setdefault(q, []).append(("duke", ["ok", b["pub"], "duke"]))
    # 23/11/2026: opere tolte dalle liste USA perché due fonti le danno uscite per intero prima (applica_registro_liste.py)
    pp = _leggi(R / "data" / "verifiche_opere.json", {}).get("prima_pubblicazione") or {}
    for x in (_leggi(R / "data" / "registro" / "liste_spostati.json", {}).get("usa_gia_libere") or []):
        if x.get("qid") and isinstance(x.get("uscita"), int):
            p = pp.get(x["qid"]) or {}
            y = anno_prima_pubblicazione(p.get("anno"), x["uscita"])
            f = ("prima pubblicazione: " + p["dove"]["it"]) if p.get("anno") else "due fonti: " + ", ".join(x.get("fonti", []))
            out.setdefault(x["qid"], []).append(("libere", ["prima", y, f]))
    # 23/11/2026: decisioni con le fonti sulle opere delle liste USA (data/verifiche_opere.json, «usa_lista»)
    for q, x in (_leggi(R / "data" / "verifiche_opere.json", {}).get("usa_lista") or {}).items():
        vl = x.get("versione_libera") or {}
        if isinstance(vl.get("anno"), int) and len(vl.get("fonti", [])) >= 2:
            out.setdefault(q, []).append(("libere", ["prima", vl["anno"], "due fonti: " + "; ".join(f["nome"] if isinstance(f, dict) else f for f in vl["fonti"])]))
        if x.get("esito") == "sposta" and isinstance(x.get("anno"), int) and len(x.get("fonti", [])) >= 2:
            out.setdefault(q, []).append(("cataloghi", ["ok", x["anno"], "due fonti: " + "; ".join(f["nome"] if isinstance(f, dict) else f for f in x["fonti"])]))
        if isinstance(x.get("conferma"), int) and len(x.get("fonti", [])) >= 2:
            out.setdefault(q, []).append(("cataloghi", ["ok", x["conferma"], "due fonti: " + "; ".join(f["nome"] if isinstance(f, dict) else f for f in x["fonti"])]))
    # 23/11/2026: anni provati da due cataloghi (data/verifiche_opere.json, verifica delle opere approvata da Marco)
    for k, x in (_leggi(R / "data" / "verifiche_opere.json", {}).get("opere") or {}).items():
        if x.get("opera") and isinstance(x.get("entro"), int):
            out.setdefault(x["opera"], []).append(("cataloghi", ["ok", x["entro"], "cataloghi: " + "; ".join(x.get("fonti", []))]))
    return out


NOMI_FONTI = {"duke": ("Duke University, Public Domain Day", "https://web.law.duke.edu/cspd/publicdomainday/"),
              "k10plus": ("K10plus (catalogo collettivo tedesco)", "https://kxp.k10plus.de/"),
              "wikipedia": ("Wikipedia", None),
              "cce": ("Catalog of Copyright Entries", "https://onlinebooks.library.upenn.edu/cce/"),
              "loc": ("Library of Congress", "https://catalog.loc.gov/"),
              "openlibrary": ("Open Library", "https://openlibrary.org/"),
              "isfdb": ("ISFDB", "https://www.isfdb.org/"),
              "bnf": ("BnF", "https://catalogue.bnf.fr/"), "dnb": ("DNB", "https://portal.dnb.de/")}


def _fonte(x, wiki=None, anno=None):
    """Una fonte come {"nome", "link"}: da un codice di catalogo (cce, loc…) o da un testo che contiene il link."""
    import re
    if isinstance(x, dict):
        return {"nome": x.get("nome"), "link": x.get("link")}
    if x in NOMI_FONTI:
        nome, link = NOMI_FONTI[x]
        if x == "wikipedia":
            link = wiki
        return {"nome": nome + (f": {anno}" if anno else ""), "link": link}
    m = re.search(r"https?://\S+", x)
    link = m.group().rstrip(".,;)»") if m else None
    nome = x.replace(m.group(), "").rstrip(" ,;") if m else x
    return {"nome": nome, "link": link}


def _cerca_catalogo(nome, titolo, autore):
    """Link alla ricerca nel catalogo (titolo e cognome dell'autore): i cataloghi non danno un link stabile alla scheda."""
    from urllib.parse import quote
    q = quote(f"{titolo} {(autore or '').split()[-1] if autore else ''}".strip())
    if nome.startswith("Library of Congress"):
        return f"https://www.loc.gov/books/?q={q}"
    if nome.startswith("K10plus"):
        return f"https://kxp.k10plus.de/DB=2.1/CMD?ACT=SRCHA&IKT=1016&TRM={q}"
    if nome.startswith("Bibliothèque nationale") or nome.startswith("BnF"):
        return f"https://catalogue.bnf.fr/rechercher.do?motRecherche={q}"
    return None


def opere_decise():
    """REGISTRO DELLE OPERE (23/11/2026, decisione di Marco): per ogni opera con un anno deciso o una nota, un posto solo
    con anno, fonti (con il link) e note in italiano e inglese. Tutte le pagine leggono anno e note da qui
    (data/registro/opere.json, parte «opere», scritta da storico/registro_opere.py). Chiave: codice Wikidata dell'opera,
    o «autore|titolo della scheda» per le opere senza codice (come data/coautori_manuali.json).
      anno: l'anno deciso; tipo: «uscita» (anno di uscita, vale per tutto il sito) o «entro» (un'edizione esiste entro
      quell'anno: si mostra «entro il …»); anno_lista: l'anno della versione che entra in una lista USA, se è diverso;
      fonti: [{"nome", "link"}]; nota: {"it", "en"} o None; perche: da dove viene la decisione."""
    ver = _leggi(R / "data" / "verifiche_opere.json", {})
    liste = {}
    for f in sorted((R / "data").glob("us-[0-9][0-9][0-9][0-9].json")):
        d = _leggi(f, {})
        for o in d.get("opere", []):
            liste.setdefault(o.get("qid"), (d.get("anno_pubblicazione"), o))
    per_fonte = {}
    for anno, voci in _leggi(R / "data" / "us-anni-verificati.json", {}).items():
        for q, v in voci.items():
            if len(v) > 5 and isinstance(v[5], dict):
                per_fonte.setdefault(q, v[5])
    out = {}
    # 1. anni provati da due cataloghi (verifica delle opere approvata da Marco): un'edizione esiste entro quell'anno
    for k, x in (ver.get("opere") or {}).items():
        if isinstance(x.get("entro"), int):
            fonti = [_fonte(y) for y in x.get("fonti", [])]
            for f in fonti:
                if not f["link"]:
                    f["link"] = _cerca_catalogo(f["nome"], x.get("titolo") or k.split("|", 1)[-1], x.get("autore"))
            out[x.get("opera") or k] = {"anno": x["entro"], "tipo": "entro", "fonti": fonti,
                                        "nota": None, "scheda": k, "perche": "verifica delle opere: due cataloghi (data/verifiche_opere.json)"}
    # 2. opere tolte dalle liste USA perché due fonti le danno uscite per intero prima (scripts/applica_registro_liste.py)
    for x in (_leggi(R / "data" / "registro" / "liste_spostati.json", {}).get("usa_gia_libere") or []):
        q, y = x.get("qid"), x.get("uscita")
        if not q or not isinstance(y, int):
            continue
        pf = per_fonte.get(q, {})
        wiki = x.get("wiki_en") or (liste.get(q, (None, {}))[1] or {}).get("wiki_en")
        fonti = [_fonte(f, wiki, pf.get(f)) for f in x.get("fonti", [])]
        nomi = ", ".join(NOMI_FONTI.get(f, (f,))[0].split(" (")[0].split(",")[0] for f in x.get("fonti", []))
        out[q] = {"anno": y, "tipo": "uscita", "fonti": fonti, "perche": f"tolta dalla lista {x.get('lista')}: già libera per intero",
                  "nota": {"it": f"Negli USA conta l'edizione del {y}, la più vecchia confermata da due fonti ({nomi}): per questo negli USA è già libera.",
                           "en": f"In the US the {y} edition counts, the oldest confirmed by two sources ({nomi}): that is why it is already free in the US."}}
    # 3. decisioni con le fonti sulle opere che restano nelle liste USA («usa_lista»)
    for q, x in (ver.get("usa_lista") or {}).items():
        pub = (liste.get(q) or (None, None))[0]
        vl = x.get("versione_libera") or {}
        e = {"tipo": "uscita", "fonti": [_fonte(y) for y in x.get("fonti", [])], "nota": x.get("nota"),
             "perche": "decisione con le fonti sulla lista USA (data/verifiche_opere.json, «usa_lista»)"}
        n2 = len(x.get("fonti", [])) >= 2
        if x.get("esito") == "tolta" and isinstance(x.get("prima"), int) and n2:
            # già libera per intero: vale la prima uscita, con le fonti e la nota della decisione
            e["anno"], e["perche"] = x["prima"], "tolta dalla lista USA: già libera per intero (data/verifiche_opere.json, «usa_lista»)"
        elif x.get("esito") == "sposta" and isinstance(x.get("anno"), int) and n2:
            # uscita dopo l'anno della lista: va nella lista del suo anno (scripts/applica_registro_liste.py)
            e["anno"], e["perche"] = x["anno"], "spostata nella lista USA del suo anno: uscita dopo (data/verifiche_opere.json, «usa_lista»)"
        elif isinstance(vl.get("anno"), int) and len(vl.get("fonti", [])) >= 2:
            e["anno"] = vl["anno"]
        elif isinstance(x.get("conferma"), int) and len(x.get("fonti", [])) >= 2:
            e["anno"] = x["conferma"]
        else:
            e["anno"], e["tipo"] = None, None   # solo la nota: l'anno resta quello di oggi
        if pub and e.get("anno") and pub != e["anno"]:
            e["anno_lista"] = pub
        out[q] = e
    # 4. prima pubblicazione documentata (rivista o editore con la data): vale quella, i cataloghi confermano (regole.anno_prima_pubblicazione)
    for q, p in (ver.get("prima_pubblicazione") or {}).items():
        if not isinstance(p.get("anno"), int) or len(p.get("fonti", [])) < 2:
            continue
        e = out.get(q) or {"nota": None}
        vecchio = e.get("anno")
        cat = [f for f in e.get("fonti", [])]
        e.update({"anno": anno_prima_pubblicazione(p["anno"], vecchio), "tipo": "uscita",
                  "fonti": [_fonte(y) for y in p["fonti"]] + cat,
                  "perche": "prima pubblicazione documentata (data/verifiche_opere.json, «prima_pubblicazione»)"
                            + (f"; {e['perche']}" if e.get("perche") else "")})
        if (e.get("nota") or {}).get("it", "").startswith("Negli USA conta l'edizione del"):
            e["nota"] = {"it": f"Prima pubblicazione: {p['dove']['it']}. Negli USA è già libera.",
                         "en": f"First published in {p['dove']['en']}. It is already free in the US."}
            altri = [f["nome"].rsplit(":", 1)[0] for f in cat if f["nome"].endswith(f": {vecchio}")]
            if vecchio and vecchio != p["anno"] and altri:
                e["nota"]["it"] += f" {', '.join(altri)} dà il {vecchio}, probabilmente l'anno in cui fu scritta: i cataloghi confermano, ma la prima pubblicazione documentata vale di più." if len(altri) == 1 else f" {', '.join(altri)} danno il {vecchio}, probabilmente l'anno in cui fu scritta: i cataloghi confermano, ma la prima pubblicazione documentata vale di più."
                e["nota"]["en"] += f" {', '.join(altri)} {'gives' if len(altri) == 1 else 'give'} {vecchio}, probably the year it was written: catalogues confirm, but the documented first publication counts for more."
        out[q] = e
    return out


def note_usa():
    """{opera: {"it", "en"}}: le note del registro delle opere (opere_decise), per chi vuole solo le note."""
    return {q: x["nota"] for q, x in opere_decise().items() if x.get("nota")}


def anni_usa():
    """{opera: [anno confermato o None, fonte, solo anni più tardi, anno trovato senza conferma]}, deciso con la regola unica."""
    return {q: anno_usa_confermato(v) for q, v in voci_usa().items()}


def liste_usa():
    """Le verifiche delle liste per anno di lista, come le usano le pagine del Public Domain Day."""
    return _leggi(R / "data" / "us-anni-verificati.json", {})


def dati_eta():
    """(anni di creazione da Wikidata, opere e autori antichi messi a mano) per scripts/regole.py, opera_antica."""
    cre = _leggi(R / "data" / "storico" / "coautori.json", {}).get("creazione", {})
    return cre, _leggi(R / "data" / "opere_antiche.json", {})


def consultazione():
    """Enciclopedie, riviste e giornali da togliere da Già pubblici (deciso da Marco il 21/11/2026)."""
    return _leggi(R / "data" / "storico" / "coautori.json", {}).get("consultazione", {})
