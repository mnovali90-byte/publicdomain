"""Regola nuova per la lista principale (chi è uno scrittore), 18/11/2026. Usa la descrizione e le professioni di Wikidata.

scrittore(a) è vero se:
  1. la descrizione inglese di Wikidata nomina un mestiere letterario (writer, novelist, poet, playwright, author...),
     anche dopo un altro mestiere («Peruvian artist and poet»); ma se prima c'è un mestiere non letterario e la parola
     letteraria è solo «author» («German chemist and author»), serve anche una professione letteraria in Wikidata;
  2. oppure la descrizione non nomina nessun mestiere (o manca) e l'autore ha una professione letteraria in Wikidata
     (romanziere, poeta, drammaturgo, saggista);
  3. oppure la descrizione nomina solo mestieri non letterari (painter, chess player, bishop, jurist...), ma l'autore
     ha una professione letteraria e almeno 5 opere in Wikidata (chi è soprattutto altro ma ha scritto molto: Ambedkar).
  «editorial writer» (giornalista) non conta come mestiere letterario.
"""
import re

LETTERARI = r"writer|penwoman|novelist|poet|poetess|playwright|dramatist|author|authoress|essayist|humorist|satirist|storyteller|man of letters|fabulist|librettist|diarist|memoirist|lyricist|scriptwriter|prose"
NEUTRI = r"journalist|translator|critic|editor|publicist|columnist|literary|scholar|philologist|teacher|educator|professor"
NON_LETT = (r"painter|artist|sculptor|illustrator|architect|chess|actor|actress|singer|composer|musician|pianist|organist|conductor|"
            r"dancer|film|director|producer|bishop|archbishop|priest|saint|rabbi|monk|missionary|theologian|cleric|pastor|lama|"
            r"politician|statesperson|statesman|diplomat|minister|king|queen|prince|princess|noble|aristocrat|activist|suffragist|"
            r"revolutionary|rebel|soldier|officer|general|admiral|military|pilot|physician|doctor|psychiatrist|psychologist|surgeon|"
            r"scientist|chemist|physicist|biologist|zoologist|entomologist|botanist|geologist|astronomer|mathematician|engineer|"
            r"inventor|economist|jurist|lawyer|judge|historian|archaeologist|anthropologist|ethnologist|folklorist|sociologist|"
            r"philosopher|educator|businessperson|businessman|banker|explorer|athlete|footballer|cricketer|sportsperson|cyclist|"
            r"librarian|grammarian|sexologist|occultist|cartoonist|caricaturist|photographer|lexicographer|linguist|orientalist")
PROF_LETTERARIE = {"romanziere", "poeta", "drammaturgo", "saggista"}


def _primo(desc):
    """Il primo mestiere nominato nella descrizione: ("lett", parola), ("non", parola) o (None, None)."""
    d = (desc or "").lower()
    trovati = []
    for tipo, pat in (("lett", LETTERARI), ("non", NON_LETT)):
        for m in re.finditer(r"\b(" + pat + r")", d):
            trovati.append((m.start(), tipo, m.group(1)))
    if not trovati:
        return None, None
    trovati.sort()
    return trovati[0][1], trovati[0][2]


def candidato(a, desc):
    """Chi va arricchito (opere, biografia...) perché potrebbe essere uno scrittore: il verdetto lo dà scrittore()."""
    d = (desc or "").lower()
    return bool(PROF_LETTERARIE & set(a.get("professioni") or [])) or bool(re.search(r"\b(" + LETTERARI + r")", d))


def scrittore(a, desc):
    d = re.sub(r"editorial writer", "journalist", (desc or "").lower())
    prof = PROF_LETTERARIE & set(a.get("professioni") or [])
    n = a.get("n_opere") or 0
    lett = re.search(r"\b(" + LETTERARI + r")", d)
    non = re.search(r"\b(" + NON_LETT + r")", d)
    if lett:
        solo_author = not re.search(r"\b(" + LETTERARI.replace("author|authoress|", "") + r")", d)
        if non and non.start() < lett.start() and solo_author:
            return bool(prof)
        return True
    if non:
        return bool(prof) and n >= 5
    return bool(prof)
