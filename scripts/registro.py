"""REGISTRO UNICO: lettura dei dati decisi, in un posto solo (20/11/2026).
Chi deve sapere l'anno USA di un'opera chiama anni_usa(): niente più due file letti in modi diversi.
La regola che decide sta in scripts/regole.py (anno_usa_confermato)."""
import json
from pathlib import Path

from regole import anno_usa_confermato

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
    for x in (_leggi(R / "data" / "registro" / "liste_spostati.json", {}).get("usa_gia_libere") or []):
        if x.get("qid") and isinstance(x.get("uscita"), int):
            out.setdefault(x["qid"], []).append(("libere", ["prima", x["uscita"], "due fonti: " + ", ".join(x.get("fonti", []))]))
    # 23/11/2026: anni provati da due cataloghi (data/verifiche_opere.json, verifica delle opere approvata da Marco)
    for k, x in (_leggi(R / "data" / "verifiche_opere.json", {}).get("opere") or {}).items():
        if x.get("opera") and isinstance(x.get("entro"), int):
            out.setdefault(x["opera"], []).append(("cataloghi", ["ok", x["entro"], "cataloghi: " + "; ".join(x.get("fonti", []))]))
    return out


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
