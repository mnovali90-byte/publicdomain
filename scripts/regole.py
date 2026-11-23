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
    # 23/11/2026: uscita per intero prima dell'anno della lista, provato da due fonti (scripts/applica_registro_liste.py)
    certe = [v for o_, v in voci if o_ == "libere" and isinstance(v[1], int)]
    if certe:
        v = min(certe, key=lambda x: x[1])
        return [v[1], v[2], False, None, True]
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


# =====================================================================================================================
# REGOLE PER PAESE (21/11/2026, dopo il caso Milne): durate, Spagna, «morti per la Francia», USA, paesi alleati.
# Prima erano copiate in schede, home, radar e Già pubblici (con liste di paesi diverse tra loro). Ora stanno qui e basta:
# il Python le importa; le pagine nel browser usano assets/regole.js, che è SCRITTO DA QUESTO FILE (esporta_js) e
# controllato identico da scripts/prova_regole.py. Non scrivere numeri come +71, +81, +96 in altri file.
# =====================================================================================================================
PAESI_70 = ("it", "fr", "de", "uk")   # Direttiva 2006/116/CE art. 1 (e Regno Unito, CDPA 1988 s. 12): 70 anni dalla morte
ANNI_DOPO_MORTE = 70
# Spagna: per chi è morto prima del 7 dicembre 1987 vale la legge del 1879 (80 anni, art. 6; LPI, disposizione transitoria
# quarta). Con il solo anno di morte, chi è morto nel 1987 lo trattiamo da prudenti come «80 anni».
SPAGNA_80_FINO_AL = 1987
SPAGNA_ANNI_VECCHI = 80
# Francia, «mort pour la France»: 30 anni in più (Code de la propriété intellectuelle, art. L123-10). Elenco: storico/mpf.py.
MPF_ANNI_IN_PIU = 30
# USA: 95 anni dalla pubblicazione per le opere uscite prima del 1978 (17 U.S.C. § 304): libera il 1° gennaio dell'anno pub+96.
USA_ANNI = 95
# Trattato di pace con l'Italia (Parigi, 10/2/1947), allegato XV, parte A, punto 3 (testo inglese: legislation.gov.uk,
# The Treaty of Peace (Italy) Order 1948, SI 1948/117): per i diritti dei cittadini delle Potenze alleate in vigore in Italia
# allo scoppio della guerra non conta il periodo fino all'entrata in vigore del trattato (15/9/1947).
# DECISIONE DI MARCO (22/11/2026, dopo la ricerca nel registro delle prove): in Italia la data è quella dei 70 anni anche
# per gli autori dei paesi alleati, perché i tribunali non hanno applicato questa proroga oltre i 70 anni (Il Piccolo
# Principe libero dal 1/1/2015: Tribunale di Milano n. 2826/2021, Corte d'appello di Milano n. 2994/2022; Cassazione
# Sezioni Unite n. 49783/2009). Resta solo una NOTA, per le opere uscite prima del 10 giugno 1940 (diritti già in vigore
# allo scoppio della guerra), finché la proroga massima (poco più di 7 anni; per prudenza 8) potrebbe essere in corso.
PROROGA_ALLEATI = 8
ALLEATI_OPERE_FINO_AL = 1940
# Potenze alleate e associate del Trattato (preambolo; Albania per adesione), con tutti i nomi con cui Wikidata indica la
# cittadinanza: italiano storico, italiano attuale (radar), inglese (Storico). Unione delle tre liste che c'erano prima.
ALLEATI_1947 = frozenset({
    # italiano
    "Regno Unito", "Regno Unito di Gran Bretagna e Irlanda", "Regno d'Inghilterra", "Galles", "Scozia", "Stati Uniti",
    "Unione Sovietica", "Impero russo", "Repubblica Socialista Federativa Sovietica Russa", "Russia sovietica", "Russia",
    "RSS Ucraina", "Ucraina", "RSS Bielorussa", "Bielorussia", "Repubblica Socialista Sovietica Georgiana", "Georgia",
    "Armenia", "Azerbaigian", "Kazakistan", "Uzbekistan", "Cina", "Repubblica di Cina", "Francia", "Australia", "Belgio",
    "Brasile", "Canada", "Cecoslovacchia", "Prima Repubblica cecoslovacca", "Repubblica Socialista Cecoslovacca",
    "Repubblica Ceca", "Etiopia", "Impero d'Etiopia", "Grecia", "Regno di Grecia", "India", "Impero anglo-indiano",
    "Dominion dell'India", "Pakistan", "Bangladesh", "Paesi Bassi", "Regno dei Paesi Bassi", "Nuova Zelanda", "Polonia",
    "Seconda Repubblica di Polonia", "Repubblica Popolare di Polonia", "Sudafrica", "Unione Sudafricana", "Jugoslavia",
    "Regno di Jugoslavia", "Repubblica federale popolare di Jugoslavia", "Repubblica Socialista Federale di Jugoslavia",
    "Regno dei Serbi, Croati e Sloveni", "Serbia", "Albania",
    # inglese
    "United Kingdom", "United Kingdom of Great Britain and Ireland", "Kingdom of England", "Wales", "Scotland",
    "United States", "United States of America", "Soviet Union", "Russian Empire", "Russian Soviet Federative Socialist Republic",
    "Ukrainian Soviet Socialist Republic", "Byelorussian Soviet Socialist Republic", "Georgian Soviet Socialist Republic",
    "Armenian Soviet Socialist Republic", "Azerbaijan Soviet Socialist Republic", "China", "Republic of China (1912–1949)",
    "Republic of China", "France", "French Third Republic", "Australia", "Belgium", "Brazil", "Canada", "Czechoslovakia",
    "First Czechoslovak Republic", "Ethiopia", "Ethiopian Empire", "Greece", "Kingdom of Greece", "India", "British Raj",
    "Dominion of India", "Pakistan", "Netherlands", "Kingdom of the Netherlands", "New Zealand", "Poland",
    "Second Polish Republic", "Polish People's Republic", "South Africa", "Union of South Africa", "Yugoslavia",
    "Kingdom of Yugoslavia", "Kingdom of Serbs, Croats and Slovenes", "Federal People's Republic of Yugoslavia",
    "Socialist Federal Republic of Yugoslavia", "Serbia", "Albania",
})


def anni_protezione(morte, paese):
    """Anni di protezione dopo la morte: 70, o 80 in Spagna per chi è morto entro il 1987."""
    return SPAGNA_ANNI_VECCHI if paese == "es" and morte <= SPAGNA_80_FINO_AL else ANNI_DOPO_MORTE


def anno_libero(morte, paese, mpf=False):
    """Anno (1° gennaio) in cui le opere di un autore morto nell'anno `morte` diventano libere nel paese."""
    anni = anni_protezione(morte, paese) + (MPF_ANNI_IN_PIU if paese == "fr" and mpf else 0)
    return morte + anni + 1


def morti_liberi_nel(anno, paese):
    """Anno di morte degli autori che diventano liberi il 1° gennaio `anno` nel paese (regola senza eccezioni)."""
    m = anno - ANNI_DOPO_MORTE - 1
    if paese == "es" and anno - SPAGNA_ANNI_VECCHI - 1 <= SPAGNA_80_FINO_AL:
        m = anno - SPAGNA_ANNI_VECCHI - 1
    return m


def anno_libero_usa(pubblicazione):
    return pubblicazione + USA_ANNI + 1


def pubblicate_libere_usa_nel(anno):
    return anno - USA_ANNI - 1


def paesi_alleati(paesi):
    return [p for p in (paesi or []) if p in ALLEATI_1947]


def nota_trattato_flag(alleato, morte, oggi_anno, anno_opera=None):
    """True se accanto alla data italiana va la nota sul Trattato di pace: autore di un paese alleato, opera uscita entro
    il 1940 (o anno non noto), e la proroga massima potrebbe essere ancora in corso. La data NON cambia (decisione 22/11/2026)."""
    if morte is None or not alleato:
        return False
    if anno_opera is not None and anno_opera > ALLEATI_OPERE_FINO_AL:
        return False
    return anno_libero(morte, "it") + PROROGA_ALLEATI > oggi_anno


def nota_trattato(paesi, morte, oggi_anno, anno_opera=None):
    return nota_trattato_flag(bool(paesi_alleati(paesi)), morte, oggi_anno, anno_opera)


# =====================================================================================================================
# REGOLE PER OPERA (22/11/2026, passo 2 di docs/giri-automatici.md). Prima stavano solo dentro storico/pagina.html
# (funzioni stato e liberaUe). Spostate qui SENZA cambiare il risultato: storico/pagina.html usa il gemello in
# assets/regole.js (statoOpera, liberaUeOpera, annoOperaCredibile) e scripts/prova_regole.py controlla che i due diano
# lo stesso risultato su tutte le opere di Già pubblici. Le correzioni giuridiche si fanno dopo, una per volta.
# Opera «normalizzata» (come la vede Già pubblici dopo il registro unico dei coautori):
#   {"q", "y": anno di uscita o None, "yd": anno Duke o 0, "antica": None | "a mano" | "creazione" | "anonima",
#    "au": [{"q", "m": anno di morte o None, "an": antico, "inc": 0/1/2 incertezza, "sc": coautore senza data, "al": alleato}]}
# Risultato: {"s": "si" | "dal" | "ver" | "nd", "y": anno in cui si libera (con "dal"), "note": [chiavi dei testi]}
# =====================================================================================================================
OPERA_VECCHIA_ANNI = 170        # opera uscita più di 170 anni fa: libera in Europa anche senza sapere degli autori
OPERA_VECCHIA_ANNI_ES = 180     # in Spagna, per prudenza (80 anni dalla morte invece di 70)
ANNO_DATI_PRIMA_MORTE = 90      # un anno di uscita 90 anni prima della morte di tutti gli autori è un errore dei dati
ANNO_DATI_DOPO_MORTE = 150      # e 150 anni dopo è un'edizione moderna (la «Repubblica» di Platone, 1963)
USA_NOTA_RECENTE = 10           # negli USA, nota «libera da poco» per chi si è liberato negli ultimi 10 anni
# Regno Unito, CDPA 1988, allegato 1, par. 12: opere inedite alla fine del 1988 di autori morti prima del 1969 protette
# fino al 31/12/2039; le opere postume uscite prima del 1989: 50 anni dalla pubblicazione.
UK_LEGGE_1988 = 1989
UK_MORTI_PRIMA_DEL = 1969
UK_2039_LIBERO = 2040
UK_POSTUME_ANNI = 50
FR_GUERRA = (1939, 1945)        # nota sulle proroghe di guerra francesi per i morti in questi anni


def _vecchio(anno_x, oggi, paese="it"):
    return anno_x <= oggi - (OPERA_VECCHIA_ANNI_ES if paese == "es" else OPERA_VECCHIA_ANNI) - 1


def anno_opera_credibile(y, au):
    """L'anno di uscita, o None se è un errore dei dati (troppo prima o troppo dopo la morte di tutti gli autori)."""
    if y is None:
        return None
    morti = [a["m"] for a in au if not a.get("an") and a.get("m") is not None]
    if morti and len(morti) == len(au) and y < min(morti) - ANNO_DATI_PRIMA_MORTE:
        return None
    if morti and all(a.get("an") or (a.get("m") is not None and y > a["m"] + ANNO_DATI_DOPO_MORTE) for a in au):
        return None
    return y


def anno_deciso(q, y, decise):
    """L'anno di uscita da usare: quello deciso nel registro delle opere (data/registro/opere.json, «opere»; scripts/registro.py,
    opere_decise) se c'è ed è un anno di uscita, altrimenti y. Una regola sola per tutte le pagine (23/11/2026)."""
    d = (decise or {}).get(q)
    if d and d.get("tipo") == "uscita" and isinstance(d.get("anno"), int):
        return d["anno"]
    return y


def libera_ue_opera(o, oggi):
    """Libera in Europa per la regola dei 70 anni (serve alla regola USA della seconda fonte)."""
    if o.get("antica"):
        return True
    if o.get("y") is not None and _vecchio(o["y"], oggi):
        return True
    au = o.get("au") or []
    return bool(au) and all(a.get("an") or (not a.get("sc") and a.get("inc") != 2 and a.get("m") is not None
                                            and anno_libero(a["m"], "it") <= oggi) for a in au)


def stato_opera(o, c, oggi, mpf=(), verifiche=None):
    """Stato dell'opera nel paese c (it, fr, de, uk, es, us) nell'anno oggi. mpf: qid dei «morti per la Francia»;
    verifiche: registro unico USA {qid: [anno confermato, fonte, solo anni più tardi, anno trovato]}."""
    Y, note, y, au = oggi, [], o.get("y"), o.get("au") or []
    antica = o.get("antica")
    if antica and antica != "anonima":
        return {"s": "si", "note": ["sAntica_antica"], "r": "antico"}
    # opera anonima: in Europa 70 anni dalla pubblicazione (in Spagna, per prudenza, 80); negli USA la solita regola
    if antica == "anonima" and c != "us" and y is not None:
        fine = y + (SPAGNA_ANNI_VECCHI if c == "es" else ANNI_DOPO_MORTE) + 1
        return {"s": "si", "note": ["sAntica_anonima"], "r": "anonima"} if fine <= Y else {"s": "dal", "y": fine, "note": ["sAntica_anonima"], "r": "anonima"}
    if any(a.get("inc") for a in au):
        note.append("sInc")
    if c == "us":
        if o.get("yd"):
            note.append("sDuke")
        # 23/11/2026: senza anno su Wikidata, vale l'anno confermato dal registro USA (es. due cataloghi, data/verifiche_opere.json)
        if y is None and ((verifiche or {}).get(o.get("q")) or [None])[0] is not None:
            y = verifiche[o.get("q")][0]
        # 23/11/2026: un'edizione confermata PIÙ VECCHIA dell'anno di Wikidata prova che l'opera era già uscita prima
        # (regola del registro: vale l'edizione confermata più vecchia; es. Charlie Chan Carries On: CCE 1930, Wikidata 1931)
        _v = (verifiche or {}).get(o.get("q")) or [None]
        if y is not None and _v[0] is not None and _v[0] < y and len(_v) > 4 and _v[4]:
            y = _v[0]   # solo se due fonti indipendenti la danno uscita per intero prima (liste USA, «usa_gia_libere»)
        if y is not None:
            # libera solo negli USA e solo per l'anno: serve una seconda fonte (Duke o Open Library), se no «da verificare»
            if anno_libero_usa(y) <= Y and not libera_ue_opera(o, Y):
                v = (verifiche or {}).get(o.get("q"))
                if v and v[0] is not None and v[0] > pubblicate_libere_usa_nel(Y):
                    return {"s": "dal", "y": anno_libero_usa(v[0]), "note": note, "r": "usa_edizione_confermata"}
                if not v or v[0] is None:
                    return {"s": "ver", "note": note + ["sUsNo" if v and v[2] else "sUsNd"],
                            "y2": v[3] if v and len(v) > 3 else None, "r": "usa_seconda_fonte_mancante"}
            if anno_libero_usa(y) <= Y:
                if anno_libero_usa(y) >= Y - USA_NOTA_RECENTE:
                    note.append("sUsPrima")
                return {"s": "si", "note": note, "r": "usa_95_anni"}
            return {"s": "dal", "y": anno_libero_usa(y), "note": note, "r": "usa_95_anni"}
        if au and all(a.get("an") or (a.get("m") is not None and _vecchio(a["m"], Y)) for a in au):
            return {"s": "si", "senza": True, "note": note, "r": "usa_autori_antichi"}
        return {"s": "nd", "note": note, "r": "usa_anno_mancante"}

    if y is not None and _vecchio(y, Y, c):
        return {"s": "si", "note": note, "r": "uscita_oltre_170_anni"}
    if not au:
        return {"s": "nd", "note": note, "r": "autori_mancanti"}
    fine, dubbio = 0, False
    for a in au:
        if a.get("an"):
            continue
        if a.get("sc"):
            dubbio = True
            continue
        if a.get("m") is None:
            return {"s": "nd", "note": note, "r": "morte_mancante"}
        fine = max(fine, anno_libero(a["m"], c, False))   # i «morti per la Francia» più sotto
    # Regno Unito, regola del 2039: viene PRIMA dei 70 anni, perché per chi è morto tra il 1960 e il 1968 i 70 anni
    # finirebbero prima del 31/12/2039 (correzione del 22/11/2026, trovata dal caso di confine in data/casi_riferimento.json)
    if c == "uk" and y is not None and y >= UK_LEGGE_1988:
        morti = [a["m"] for a in au if not a.get("an") and not a.get("sc") and a.get("m") is not None]
        if morti and y > max(morti) and max(morti) < UK_MORTI_PRIMA_DEL and fine < UK_2039_LIBERO:
            fine = UK_2039_LIBERO
            note = note + ["sUk2039"]
    if fine > Y:
        return {"s": "dal", "y": fine, "note": note, "r": "uk_2039" if "sUk2039" in note else "morte"}
    if dubbio:
        return {"s": "ver", "note": note + ["sCoaut"], "r": "coautore_senza_data"}
    # fonti in disaccordo proprio sul confine dei 70 anni (registro unico, 20/11/2026): non la diamo per libera
    if c != "es" and any(a.get("inc") == 2 for a in au):
        return {"s": "ver", "note": [k for k in note if k != "sInc"] + ["sConfine"], "r": "morte_incerta_sul_confine"}
    if c == "uk":
        morti = [a["m"] for a in au if not a.get("an")]
        if morti:
            ultima = max(morti)
            if y is not None and y > ultima:
                if y < UK_LEGGE_1988 and y + UK_POSTUME_ANNI + 1 > Y:
                    return {"s": "ver", "note": note + ["sUkPostumo"], "r": "uk_postuma"}
            if y is None and ultima < UK_MORTI_PRIMA_DEL:
                note.append("sUkNd")
    # Trattato di pace del 1947: la data italiana resta quella dei 70 anni, con una nota (decisione di Marco, 22/11/2026)
    if c == "it" and any(not a.get("an") and nota_trattato_flag(a.get("al"), a.get("m"), Y, y) for a in au):
        note.append("sAlleato")
    # «morts pour la France»: con il titolo l'opera non è libera in Francia finché non passano 100 anni (lettura prudente)
    if c == "fr" and any(not a.get("an") and a.get("q") in mpf and anno_libero(a["m"], "fr", True) > Y for a in au):
        return {"s": "ver", "note": note + ["sMpf"], "r": "fr_morto_per_la_francia"}
    if c == "fr" and any(not a.get("an") and FR_GUERRA[0] <= a["m"] <= FR_GUERRA[1] and anno_libero(a["m"], "fr", True) > Y for a in au):
        note.append("sFr")
    return {"s": "si", "note": note, "r": "uk_2039" if "sUk2039" in note else "morte"}


def opera_vecchia(anno_x, oggi, paese="it"):
    """True se anno_x (uscita dell'opera o morte dell'autore) è più vecchio di 170 anni (180 in Spagna)."""
    return _vecchio(anno_x, oggi, paese)


def opera_da_riga(r, coautori=None, decise=None):
    """Opera normalizzata (vedi sopra) da una riga dei file dello Storico (ricerca e per_autore):
    [qid, titolo, titolo_it, anno, pagine, [[qid, nome, morte, antico, incerta, alleato]], anno_duke], applicando le
    decisioni del registro unico dei coautori (data/registro/opere.json, «coautori»). Come coautori() in storico/pagina.html."""
    au = [{"q": a[0], "m": a[2] if len(a) > 2 else None, "an": bool(a[3]) if len(a) > 3 else False,
           "inc": (a[4] if len(a) > 4 else 0) or 0, "sc": False, "al": bool(a[5]) if len(a) > 5 else False} for a in (r[5] or [])]
    e, antica = (coautori or {}).get(r[0]), None
    if e:
        for x in e.get("add") or []:
            if not any(a["q"] == x[0] for a in au):
                au.append({"q": x[0], "m": x[2], "an": False, "inc": 0, "sc": False, "al": False})
        au = [a for a in au if a["q"] not in (e.get("x") or [])]
        for a in au:
            if (e.get("m") or {}).get(a["q"]) is not None:
                a["m"] = e["m"][a["q"]]
            if a["q"] in (e.get("sc") or []):
                a["sc"] = True
            if a["q"] in (e.get("an") or []):
                a["an"] = True
        antica = e.get("antica") or None
    return {"q": r[0], "y": anno_deciso(r[0], anno_opera_credibile(r[3], au), decise), "yd": (r[6] if len(r) > 6 else 0) or 0, "antica": antica, "au": au}


# =====================================================================================================================
# CALENDARIO DEL SITO (docs/giri-automatici.md, mockup approvato da Marco il 22/11/2026): dalla data di oggi, quale anno è
# in vetrina e in che fase siamo. Tutte le pagine usano questa funzione, niente «anno + 1» sparsi.
#   «vigilia»: 31 dicembre (domani è Public Domain Day), in vetrina l'anno che arriva;
#   «festa»:   dal 1° al 6 gennaio, in vetrina l'anno appena liberato;
#   «conto»:   il resto dell'anno, conto alla rovescia verso il prossimo 1° gennaio.
# =====================================================================================================================
FESTA_FINO_AL = 6   # la festa dura dal 1° al 6 gennaio; il 7 riparte il conto alla rovescia


def fase_sito(oggi):
    """(fase, anno in vetrina) per una data (datetime.date)."""
    if oggi.month == 12 and oggi.day == 31:
        return "vigilia", oggi.year + 1
    if oggi.month == 1 and oggi.day <= FESTA_FINO_AL:
        return "festa", oggi.year
    return "conto", oggi.year + 1


# --- la stessa cosa per il browser: assets/regole.js è scritto da qui. Se cambi una funzione sopra, cambia anche sotto:
#     scripts/prova_regole.py confronta le due versioni su tutti gli autori e su tutti gli anni e si ferma se differiscono.
_JS = """/* SCRITTO DA scripts/regole.py (esporta_js): non modificare a mano. Regole per paese del sito, in un posto solo. */
window.REGOLE_PAESI = (() => {
  const C = @@COSTANTI@@;
  const ALLEATI = new Set(C.ALLEATI_1947);
  const anniProtezione = (morte, paese) => (paese === "es" && morte <= C.SPAGNA_80_FINO_AL ? C.SPAGNA_ANNI_VECCHI : C.ANNI_DOPO_MORTE);
  const annoLibero = (morte, paese, mpf) => morte + anniProtezione(morte, paese) + (paese === "fr" && mpf ? C.MPF_ANNI_IN_PIU : 0) + 1;
  const mortiLiberiNel = (anno, paese) => (paese === "es" && anno - C.SPAGNA_ANNI_VECCHI - 1 <= C.SPAGNA_80_FINO_AL ? anno - C.SPAGNA_ANNI_VECCHI - 1 : anno - C.ANNI_DOPO_MORTE - 1);
  const annoLiberoUsa = (pub) => pub + C.USA_ANNI + 1;
  const pubblicateLibereUsaNel = (anno) => anno - C.USA_ANNI - 1;
  const paesiAlleati = (paesi) => (paesi || []).filter((p) => ALLEATI.has(p));
  const notaTrattatoFlag = (alleato, morte, oggiAnno, annoOpera) => {
    if (morte === null || morte === undefined || !alleato) return false;
    if (annoOpera !== null && annoOpera !== undefined && annoOpera > C.ALLEATI_OPERE_FINO_AL) return false;
    return annoLibero(morte, "it") + C.PROROGA_ALLEATI > oggiAnno;
  };
  const notaTrattato = (paesi, morte, oggiAnno, annoOpera) => notaTrattatoFlag(paesiAlleati(paesi).length > 0, morte, oggiAnno, annoOpera);
  // ---- regole per opera: gemelle di stato_opera, libera_ue_opera, anno_opera_credibile in scripts/regole.py ----
  const vecchio = (x, oggi, paese) => x <= oggi - (paese === "es" ? C.OPERA_VECCHIA_ANNI_ES : C.OPERA_VECCHIA_ANNI) - 1;
  const nn = (v) => v !== null && v !== undefined;
  const annoDeciso = (q, y, decise) => {
    const d = (decise || {})[q];
    return d && d.tipo === "uscita" && Number.isInteger(d.anno) ? d.anno : y;
  };
  const annoOperaCredibile = (y, au) => {
    if (!nn(y)) return null;
    const morti = au.filter((a) => !a.an && nn(a.m)).map((a) => a.m);
    if (morti.length && morti.length === au.length && y < Math.min(...morti) - C.ANNO_DATI_PRIMA_MORTE) return null;
    if (morti.length && au.every((a) => a.an || (nn(a.m) && y > a.m + C.ANNO_DATI_DOPO_MORTE))) return null;
    return y;
  };
  const liberaUeOpera = (o, oggi) => {
    if (o.antica) return true;
    if (nn(o.y) && vecchio(o.y, oggi)) return true;
    return o.au.length > 0 && o.au.every((a) => a.an || (!a.sc && a.inc !== 2 && nn(a.m) && annoLibero(a.m, "it") <= oggi));
  };
  // gemella di fase_sito: d è una Date del browser (ora locale)
  const faseSito = (d) => {
    const m = d.getMonth() + 1, g = d.getDate(), y = d.getFullYear();
    if (m === 12 && g === 31) return ["vigilia", y + 1];
    if (m === 1 && g <= C.FESTA_FINO_AL) return ["festa", y];
    return ["conto", y + 1];
  };
  const statoOpera = (o, c, oggi, mpf, verifiche) => {
    const Y = oggi, note = [], au = o.au || [];
    let y = nn(o.y) ? o.y : null;
    if (o.antica && o.antica !== "anonima") return { s: "si", note: ["sAntica_antica"], r: "antico" };
    if (o.antica === "anonima" && c !== "us" && y !== null) {
      const fine = y + (c === "es" ? C.SPAGNA_ANNI_VECCHI : C.ANNI_DOPO_MORTE) + 1;
      return fine <= Y ? { s: "si", note: ["sAntica_anonima"], r: "anonima" } : { s: "dal", y: fine, note: ["sAntica_anonima"], r: "anonima" };
    }
    if (au.some((a) => a.inc)) note.push("sInc");
    if (c === "us") {
      if (o.yd) note.push("sDuke");
      // 23/11/2026: senza anno su Wikidata, vale l'anno confermato dal registro USA (gemella di stato_opera)
      if (y === null && ((verifiche || {})[o.q] || [null])[0] != null) y = verifiche[o.q][0];
      { const _v = (verifiche || {})[o.q] || [null]; if (y !== null && _v[0] != null && _v[0] < y && _v.length > 4 && _v[4]) y = _v[0]; }
      if (y !== null) {
        if (annoLiberoUsa(y) <= Y && !liberaUeOpera(o, Y)) {
          const v = (verifiche || {})[o.q];
          if (v && v[0] !== null && v[0] > pubblicateLibereUsaNel(Y)) return { s: "dal", y: annoLiberoUsa(v[0]), note, r: "usa_edizione_confermata" };
          if (!v || v[0] === null) return { s: "ver", note: note.concat([v && v[2] ? "sUsNo" : "sUsNd"]), y2: v ? (nn(v[3]) ? v[3] : null) : null, r: "usa_seconda_fonte_mancante" };
        }
        if (annoLiberoUsa(y) <= Y) { if (annoLiberoUsa(y) >= Y - C.USA_NOTA_RECENTE) note.push("sUsPrima"); return { s: "si", note, r: "usa_95_anni" }; }
        return { s: "dal", y: annoLiberoUsa(y), note, r: "usa_95_anni" };
      }
      if (au.length && au.every((a) => a.an || (nn(a.m) && vecchio(a.m, Y)))) return { s: "si", senza: true, note, r: "usa_autori_antichi" };
      return { s: "nd", note, r: "usa_anno_mancante" };
    }
    if (y !== null && vecchio(y, Y, c)) return { s: "si", note, r: "uscita_oltre_170_anni" };
    if (!au.length) return { s: "nd", note, r: "autori_mancanti" };
    let fine = 0, dubbio = false;
    for (const a of au) {
      if (a.an) continue;
      if (a.sc) { dubbio = true; continue; }
      if (!nn(a.m)) return { s: "nd", note, r: "morte_mancante" };
      fine = Math.max(fine, annoLibero(a.m, c, false));
    }
    if (c === "uk" && y !== null && y >= C.UK_LEGGE_1988) {
      const morti = au.filter((a) => !a.an && !a.sc && nn(a.m)).map((a) => a.m);
      if (morti.length && y > Math.max(...morti) && Math.max(...morti) < C.UK_MORTI_PRIMA_DEL && fine < C.UK_2039_LIBERO) { fine = C.UK_2039_LIBERO; note.push("sUk2039"); }
    }
    if (fine > Y) return { s: "dal", y: fine, note, r: note.includes("sUk2039") ? "uk_2039" : "morte" };
    if (dubbio) return { s: "ver", note: note.concat(["sCoaut"]), r: "coautore_senza_data" };
    if (c !== "es" && au.some((a) => a.inc === 2)) return { s: "ver", note: note.filter((k) => k !== "sInc").concat(["sConfine"]), r: "morte_incerta_sul_confine" };
    if (c === "uk") {
      const morti = au.filter((a) => !a.an).map((a) => a.m);
      if (morti.length) {
        const ultima = Math.max(...morti);
        if (y !== null && y > ultima) {
          if (y < C.UK_LEGGE_1988 && y + C.UK_POSTUME_ANNI + 1 > Y) return { s: "ver", note: note.concat(["sUkPostumo"]), r: "uk_postuma" };
        }
        if (y === null && ultima < C.UK_MORTI_PRIMA_DEL) note.push("sUkNd");
      }
    }
    if (c === "it" && au.some((a) => !a.an && notaTrattatoFlag(a.al, a.m, Y, y))) note.push("sAlleato");
    const haMpf = (q) => (mpf && (mpf.has ? mpf.has(q) : mpf.includes(q)));
    if (c === "fr" && au.some((a) => !a.an && haMpf(a.q) && annoLibero(a.m, "fr", true) > Y)) return { s: "ver", note: note.concat(["sMpf"]), r: "fr_morto_per_la_francia" };
    if (c === "fr" && au.some((a) => !a.an && a.m >= C.FR_GUERRA[0] && a.m <= C.FR_GUERRA[1] && annoLibero(a.m, "fr", true) > Y)) note.push("sFr");
    return { s: "si", note, r: note.includes("sUk2039") ? "uk_2039" : "morte" };
  };
  return Object.assign({}, C, { anniProtezione, annoLibero, mortiLiberiNel, annoLiberoUsa, pubblicateLibereUsaNel, paesiAlleati,
    notaTrattatoFlag, notaTrattato, statoOpera, liberaUeOpera, annoOperaCredibile, annoDeciso, faseSito });
})();
"""


def esporta_js(percorso):
    import json
    c = {"ANNI_DOPO_MORTE": ANNI_DOPO_MORTE, "SPAGNA_80_FINO_AL": SPAGNA_80_FINO_AL, "SPAGNA_ANNI_VECCHI": SPAGNA_ANNI_VECCHI,
         "MPF_ANNI_IN_PIU": MPF_ANNI_IN_PIU, "USA_ANNI": USA_ANNI, "PROROGA_ALLEATI": PROROGA_ALLEATI,
         "ALLEATI_OPERE_FINO_AL": ALLEATI_OPERE_FINO_AL, "PAESI_70": list(PAESI_70), "ALLEATI_1947": sorted(ALLEATI_1947),
         "OPERA_VECCHIA_ANNI": OPERA_VECCHIA_ANNI, "OPERA_VECCHIA_ANNI_ES": OPERA_VECCHIA_ANNI_ES, "ANNO_DATI_PRIMA_MORTE": ANNO_DATI_PRIMA_MORTE,
         "ANNO_DATI_DOPO_MORTE": ANNO_DATI_DOPO_MORTE, "USA_NOTA_RECENTE": USA_NOTA_RECENTE, "UK_LEGGE_1988": UK_LEGGE_1988,
         "UK_MORTI_PRIMA_DEL": UK_MORTI_PRIMA_DEL, "UK_2039_LIBERO": UK_2039_LIBERO, "UK_POSTUME_ANNI": UK_POSTUME_ANNI, "FR_GUERRA": list(FR_GUERRA),
         "FESTA_FINO_AL": FESTA_FINO_AL}
    testo = _JS.replace("@@COSTANTI@@", json.dumps(c, ensure_ascii=False))
    from pathlib import Path
    Path(percorso).write_text(testo, encoding="utf-8")
    return testo


def paesi_liberi_insieme(paesi, morte, oggi_anno, mpf=False):
    """Paesi (it, fr, de, uk, es) in cui le opere dell'autore si liberano lo stesso giorno della regola dei 70 anni: è
    l'elenco da scrivere in frasi come «Libero in … dal 1° gennaio». La Spagna entra solo se la sua data coincide, la Francia
    esce per i «morti per la Francia» (mpf=True). (oggi_anno e paesi restano per compatibilità: dal 22/11/2026 l'Italia c'è sempre.)"""
    if morte is None:
        return []
    base = anno_libero(morte, "it")
    out = []
    for p in ("it", "fr", "de", "uk", "es"):
        if anno_libero(morte, p, mpf) != base:
            continue
        out.append(p)
    return out
