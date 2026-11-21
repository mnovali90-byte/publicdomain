"""Regola di ricerca di Già pubblici: sotto quali file (prime due lettere) va messa ogni opera e ogni autore.
Usata da storico/storico.py (giro mensile) e da storico/applica_registro.py (riordino dei file già pronti).
La pagina (storico/pagina.html, funzione chiavi) deve cercare con la stessa regola.

21/11/2026: un'opera va sotto OGNI parola che conta del titolo (originale e italiano), non solo sotto la prima:
prima «Pinocchio» non trovava «Le avventure di Pinocchio», perché il titolo stava solo sotto «le» e «av»."""
import re, unicodedata

ARTICOLI = {"the", "a", "an", "il", "lo", "la", "l", "le", "i", "gli", "un", "una", "uno", "der", "die", "das", "den",
            "ein", "eine", "les", "el", "los", "las", "de", "het"}
# parole che non servono a cercare (articoli, preposizioni, congiunzioni nelle lingue più frequenti dell'archivio)
VUOTE = ARTICOLI | {"and", "of", "in", "on", "at", "to", "for", "with", "by", "from", "or", "di", "del", "della", "dei",
                    "degli", "delle", "dello", "e", "ed", "nel", "nella", "con", "per", "da", "dal", "dalla", "su", "sul",
                    "dem", "des", "und", "von", "zu", "im", "am", "du", "et", "en", "y", "o", "que", "op", "van", "en"}


def norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.findall(r"[a-z0-9]+", t)


def lettera(parola):
    """Le prime due lettere della parola (file più piccoli da scaricare): «promessi» -> «pr»."""
    return parola[:2] if parola and parola[0].isalpha() else "_"


def chiavi_ricerca(testo, autore=False):
    """Lettere (file) sotto cui va cercato un titolo o un autore."""
    p = norm(testo)
    if not p:
        return set()
    if autore:
        return {lettera(p[0]), lettera(p[-1])}
    ks = {lettera(p[0])}
    for w in p:
        if w not in VUOTE and (len(w) >= 3 or w.isdigit()):
            ks.add(lettera(w))
    return ks
