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


# =====================================================================================================================
# REGOLE_PAESI PER PAESE (21/11/2026, dopo il caso Milne): durate, Spagna, «morti per la Francia», USA, paesi alleati.
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
# allo scoppio della guerra (o riconosciuti dall'allegato) non conta il periodo dallo scoppio della guerra all'entrata in
# vigore del trattato (15/9/1947), e la durata si allunga di altrettanto. Al massimo poco più di 7 anni: per prudenza 8.
# Riguarda le opere uscite fino al 1947. Quando la cittadinanza non è nota, non possiamo escluderlo: «da verificare».
PROROGA_ALLEATI = 8
ALLEATI_OPERE_FINO_AL = 1947
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


def alleato_o_ignoto(paesi):
    """Il Trattato potrebbe valere: cittadinanza di una Potenza alleata, o cittadinanza non nota (non possiamo escluderlo)."""
    return not paesi or bool(paesi_alleati(paesi))


def italia_da_verificare_flag(alleato_o_ignoto_, morte, oggi_anno, anno_opera=None):
    """True se in Italia la data normale non basta: autore alleato o di paese non noto, opera uscita fino al 1947 (o anno
    non noto), e la proroga massima del Trattato potrebbe non essere ancora finita."""
    if morte is None or not alleato_o_ignoto_:
        return False
    if anno_opera is not None and anno_opera > ALLEATI_OPERE_FINO_AL:
        return False
    return anno_libero(morte, "it") + PROROGA_ALLEATI > oggi_anno


def italia_da_verificare(paesi, morte, oggi_anno, anno_opera=None):
    return italia_da_verificare_flag(alleato_o_ignoto(paesi), morte, oggi_anno, anno_opera)


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
  const alleatoOIgnoto = (paesi) => !paesi || !paesi.length || paesiAlleati(paesi).length > 0;
  const italiaDaVerificareFlag = (flag, morte, oggiAnno, annoOpera) => {
    if (morte === null || morte === undefined || !flag) return false;
    if (annoOpera !== null && annoOpera !== undefined && annoOpera > C.ALLEATI_OPERE_FINO_AL) return false;
    return annoLibero(morte, "it") + C.PROROGA_ALLEATI > oggiAnno;
  };
  const italiaDaVerificare = (paesi, morte, oggiAnno, annoOpera) => italiaDaVerificareFlag(alleatoOIgnoto(paesi), morte, oggiAnno, annoOpera);
  return Object.assign({}, C, { anniProtezione, annoLibero, mortiLiberiNel, annoLiberoUsa, pubblicateLibereUsaNel, paesiAlleati,
    alleatoOIgnoto, italiaDaVerificareFlag, italiaDaVerificare });
})();
"""


def esporta_js(percorso):
    import json
    c = {"ANNI_DOPO_MORTE": ANNI_DOPO_MORTE, "SPAGNA_80_FINO_AL": SPAGNA_80_FINO_AL, "SPAGNA_ANNI_VECCHI": SPAGNA_ANNI_VECCHI,
         "MPF_ANNI_IN_PIU": MPF_ANNI_IN_PIU, "USA_ANNI": USA_ANNI, "PROROGA_ALLEATI": PROROGA_ALLEATI,
         "ALLEATI_OPERE_FINO_AL": ALLEATI_OPERE_FINO_AL, "PAESI_70": list(PAESI_70), "ALLEATI_1947": sorted(ALLEATI_1947)}
    testo = _JS.replace("@@COSTANTI@@", json.dumps(c, ensure_ascii=False))
    from pathlib import Path
    Path(percorso).write_text(testo, encoding="utf-8")
    return testo


def paesi_liberi_insieme(paesi, morte, oggi_anno, mpf=False):
    """Paesi (it, fr, de, uk, es) in cui le opere dell'autore si liberano lo stesso giorno della regola dei 70 anni, senza
    eccezioni da verificare: è l'elenco da scrivere in frasi come «Libero in … dal 1° gennaio». L'Italia esce se va
    verificata (paese alleato o non noto), la Spagna entra solo se la sua data coincide, la Francia esce per i «morti per la
    Francia» (mpf=True)."""
    if morte is None:
        return []
    base = anno_libero(morte, "it")
    out = []
    for p in ("it", "fr", "de", "uk", "es"):
        if p == "it" and italia_da_verificare(paesi, morte, oggi_anno):
            continue
        if anno_libero(morte, p, mpf) != base:
            continue
        out.append(p)
    return out
