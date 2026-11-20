"""Regole del sito in un posto solo (registro unico, approvato da Marco il 20/11/2026).
Chi decide qualcosa (anni di morte, coautori, anni USA) importa le regole da qui: niente copie in altri file."""
import re

# fonte -> biblioteca o dizionario (la stessa fonte con nomi diversi conta una volta)
AUTOREVOLI = {
    "gnd": "GND", "Integrated Authority File": "GND", "Catalog of the German National Library": "GND",
    "loc": "Library of Congress", "Library of Congress Authorities": "Library of Congress",
    "Faceted Application of Subject Terminology": "Library of Congress",
    "BnF authorities": "BnF", "Czech National Authority Database": "Biblioteca nazionale ceca", "IdRef": "IdRef (Francia)",
    "NUKAT": "NUKAT (Polonia)", "Authority Author Files at Russian National Library": "Biblioteca nazionale russa",
    "National Library of Israel Names and Subjects Authority File": "Biblioteca nazionale di Israele",
    "Spanish Biographical Dictionary": "Diccionario Biográfico Español", "Deutsche Biographie": "Deutsche Biographie",
    "Encyclopædia Britannica Online": "Britannica", "Great Norwegian Encyclopedia": "Store norske leksikon",
    "Biographical Dictionary of Georgia": "Dizionario biografico della Georgia", "al-Aʻlām (Dār al-ʻIlm, 2002)": "al-Aʻlām",
    "Österreichische Schriftstellerinnen 1880–1938": "Österreichische Schriftstellerinnen 1880–1938",
    "The Biographical Dictionary of Women in Science": "Biographical Dictionary of Women in Science",
    "The Encyclopedia of Science Fiction": "Encyclopedia of Science Fiction",
    "Oxford Dictionary of National Biography": "Oxford Dictionary of National Biography",
    "Dizionario Biografico degli Italiani": "Dizionario Biografico degli Italiani",
}
# le altre fonti citate con nomi da biblioteca nazionale o da dizionario biografico (ognuna conta per sé);
# non gli aggregatori, che ripetono altre fonti
AUTOREVOLI_RE = re.compile(r"authority file|national library|nationalbibliothek|bibliothèque nationale|biblioteca nacional|"
                           r"biographical dictionary|dictionary of national biography|biographisches lexikon|biografick|"
                           r"dizionario biografico|diccionario biográfico|digitale bibliotheek", re.I)
NON_AUTOREVOLI_RE = re.compile(r"worldcat|snac|viaf|virtual international|wikipedia|wikidata", re.I)


def maggioranza(fv, citate):
    """(anno, [fonti]) se almeno due fonti autorevoli diverse danno lo stesso anno e nessun altro anno ne ha altrettante."""
    voti = {}
    for k, y in list(fv.items()) + list((citate or {}).items()):
        g = AUTOREVOLI.get(k) or (k if AUTOREVOLI_RE.search(k) and not NON_AUTOREVOLI_RE.search(k) else None)
        if g and y:
            voti.setdefault(y, set()).add(g)
    if not voti:
        return None
    ordine = sorted(voti.items(), key=lambda t: -len(t[1]))
    y, g = ordine[0]
    if len(g) >= 2 and all(len(x[1]) < len(g) for x in ordine[1:]):
        return y, sorted(g)
    return None


def decidi_morte(fv, citate):
    """Anno di morte di un autore. fv: {"wikidata": anno principale, "wikidata_altra": altro anno di Wikidata,
    "gnd": anno, "loc": anno}; citate: {fonte citata da Wikidata: anno}.
    Restituisce (esito, anno deciso, fonti autorevoli d'accordo o None).
      verificato: almeno una biblioteca letta da noi, tutte uguali a Wikidata
      documentato: nessuna biblioteca, ma fonti citate da Wikidata tutte uguali
      una_fonte: solo Wikidata
      maggioranza: c'è disaccordo, ma due fonti autorevoli danno ragione a Wikidata
      corretto: due fonti autorevoli danno un altro anno: vale il loro (regola di Marco, 20/11/2026)
      discorde: disaccordo che le fonti autorevoli non risolvono (da verificare; si usa Wikidata)"""
    wd = fv.get("wikidata")
    altre = [y for k, y in fv.items() if k != "wikidata"]
    if any(y != wd for y in altre + list((citate or {}).values())):
        m = maggioranza(fv, citate)
        if m and m[0] == wd:
            return "maggioranza", wd, m[1]
        if m:
            return "corretto", m[0], m[1]
        return "discorde", wd, None
    if any(k in fv for k in ("gnd", "loc")):
        return "verificato", wd, None
    if citate:
        return "documentato", wd, None
    return "una_fonte", wd, None
