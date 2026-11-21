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


def morte_dal_registro(qid, morte, registro, anno_ue):
    """Anno di morte che tutte le pagine devono usare: quello deciso nel registro (data/registro/autori.json).
    Restituisce (anno, incerta): incerta 0 = fonti d'accordo; 1 = fonti discordi; 2 = fonti discordi proprio sul
    confine della regola europea (una fonte dice entro anno_ue, un'altra dopo): l'opera va mostrata «da verificare».
    Un autore che non è nel registro tiene il suo anno."""
    v = (registro or {}).get(qid)
    if not v or morte is None:
        return morte, None
    if v.get("e") != "discorde":
        return v["m"], 0
    # contano Wikidata e le fonti autorevoli, non le fonti deboli (Project Gutenberg, IMDb...)
    cit = {k: y for k, y in (v.get("c") or {}).items() if AUTOREVOLI.get(k) or (AUTOREVOLI_RE.search(k) and not NON_AUTOREVOLI_RE.search(k))}
    anni = [y for y in list((v.get("f") or {}).values()) + list(cit.values()) if isinstance(y, int)]
    sul_confine = anni and min(anni) <= anno_ue < max(anni)
    return v["m"], 2 if sul_confine else 1


def autori_che_contano(autori, tipi, anno):
    """REGOLA DEI COAUTORI (approvata da Marco il 20/11/2026), in un posto solo.
    autori: lista di {"qid", "nome", "morte", "antico", "nascita" (facoltativa)}; tipi: data/storico/coautori.json["autori"]
    ({qid: {"t": "p" persona | "g" gruppo/ente, "m": morte più tarda dei membri, "nd": membri senza data, "n": nascita}}).
    Restituisce la lista degli autori che contano, ognuno con eventuali segni:
      "gruppo": True   un gruppo con membri: vale l'anno di morte più tardo dei membri (Ilf e Petrov: 1942);
      "senza_data": True   coautore senza data di morte (o «valore sconosciuto») accanto ad autori con la data: da verificare;
      "antico": True   coautore senza data accanto ad autori tutti antichi o morti da più di 170 anni: antico anche lui.
    Escono dalla lista: chi è nato dopo la morte degli altri autori (ha curato, letto o presentato un'edizione) e i gruppi
    o enti senza membri noti, se ci sono autori persone con la data di morte."""
    out = [dict(a) for a in autori]
    noto = lambda a: a.get("antico") or a.get("morte") is not None
    for a in out:
        t = (tipi or {}).get(a.get("qid")) or {}
        nascita = a.get("nascita") if a.get("nascita") is not None else t.get("n")
        altri = [b["morte"] for b in out if b is not a and b.get("morte") is not None and not b.get("_via")]
        if nascita is not None and altri and nascita > max(altri) and not a.get("antico"):
            a["_via"] = True
            continue
        if noto(a):
            continue
        if t.get("t") == "g":
            if t.get("m") is not None:
                a["morte"], a["gruppo"] = t["m"], True
            elif t.get("nd"):
                a["senza_data"] = True
            else:
                a["_ignora"] = True
        else:
            a["senza_data"] = True
    out = [a for a in out if not a.get("_via")]
    if any(not a.get("_ignora") and noto(a) for a in out):
        out = [a for a in out if not a.get("_ignora")]
    for a in out:
        a.pop("_ignora", None)
    if not any(noto(a) for a in out):
        for a in out:
            a.pop("senza_data", None)
    elif any(a.get("senza_data") for a in out) and all(
            a.get("antico") or a["morte"] <= anno - 171 for a in out if not a.get("senza_data")):
        for a in out:
            if a.pop("senza_data", None):
                a["antico"] = True
    return out


def anno_usa_confermato(voci):
    """ANNO USA DI UN'OPERA (registro unico, 20/11/2026). voci: lista di (origine, voce) dalle due verifiche:
      - "storico" (storico/verifica_anni.py): esito "ok" = una fonte indipendente ha un'edizione uscita entro il limite;
        "no" = le fonti hanno solo edizioni più tarde; "nd" = nessuna conferma;
      - "lista" (scripts/verifica_anni_usa.py): "ok" = uscita nell'anno della lista; "prima" = uscita prima (fonte
        autorevole); "parziale" = a puntate fino a quell'anno; "nd" = nessuna conferma.
    Regola: vale l'edizione confermata più vecchia (basta un'edizione uscita entro il limite, come per la Duke).
    Restituisce [anno confermato o None, fonte, le fonti danno solo anni più tardi (True/False), anno trovato senza conferma]."""
    conf, tardi, trovato = [], False, None
    for origine, v in voci:
        e, y, fonte = v[0], v[1], v[2]
        buono = e == "ok" if origine == "storico" else e in ("ok", "prima", "parziale")
        if buono and isinstance(y, int):
            conf.append((y, fonte))
        elif isinstance(y, int):
            trovato = y if trovato is None else min(trovato, y)
            tardi = tardi or e == "no"
    if conf:
        y, fonte = min(conf)
        return [y, fonte, False, None]
    return [None, None, tardi, trovato]


ANONIMI = {"anonymous", "anonimo", "anonyme", "anonym", "anónimo", "folklore", "unknown", "traditional", "tradizionale"}


def anonimo(qid, nome):
    """Autore dichiarato anonimo o «valore sconosciuto» su Wikidata (non: autore che Wikidata semplicemente non mette)."""
    return bool(re.fullmatch(r"[0-9a-f]{32}", qid or "")) or (nome or "").strip().lower() in ANONIMI


def opera_antica(qid, autori, anno_opera, creazione, antiche, anno):
    """TESTI ANTICHI E OPERE ANONIME (approvato da Marco il 21/11/2026). Motivo per cui l'opera è libera dappertutto
    per età, oppure None.
      "a mano": in data/opere_antiche.json (opera o autore), con la fonte;
      "creazione": Wikidata dà una data di creazione (P571) più vecchia di 171 anni e nessun autore ha una data;
      "anonima": tutti gli autori sono dichiarati anonimi e l'opera è uscita da più di 70 anni. Direttiva 2006/116/CE,
                 art. 1, c. 3: per le opere anonime la protezione dura 70 anni dalla pubblicazione."""
    antiche = antiche or {}
    if qid in antiche.get("opere", {}):
        return "a mano"
    if autori and all(a.get("qid") in antiche.get("autori", {}) or a.get("antico") for a in autori) \
            and any(a.get("qid") in antiche.get("autori", {}) for a in autori):
        return "a mano"
    senza_data = all(a.get("morte") is None and not a.get("antico") for a in autori)
    if senza_data and creazione is not None and creazione <= anno - 171:
        return "creazione"
    if autori and all(anonimo(a.get("qid"), a.get("nome")) for a in autori) and anno_opera is not None and anno_opera <= anno - 71:
        return "anonima"
    return None
