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
    return out


def anni_usa():
    """{opera: [anno confermato o None, fonte, solo anni più tardi, anno trovato senza conferma]}, deciso con la regola unica."""
    return {q: anno_usa_confermato(v) for q, v in voci_usa().items()}


def liste_usa():
    """Le verifiche delle liste per anno di lista, come le usano le pagine del Public Domain Day."""
    return _leggi(R / "data" / "us-anni-verificati.json", {})
