"""Le lingue del sito, in un posto solo (26/11/2026).

Come funziona (lo stesso metodo di gettext, lo standard dei siti multilingue):
- nel codice ogni testo fisso è scritto come coppia italiano / inglese: T("Chi diventa libero nel {anno}", "Who becomes free in {anno}", anno=anno).
  Le parti che cambiano (numeri, nomi, date) sono segnaposti tra graffe, riempiti dopo.
- per l'italiano e l'inglese il risultato è esattamente il testo scritto nel codice.
- per le altre lingue il testo inglese fa da chiave: la traduzione sta in testi/<lingua>.json, { "testo inglese": "traduzione" },
  con gli stessi segnaposti. Se manca, esce l'inglese e il testo finisce nell'elenco dei mancanti (testi/mancanti-<lingua>.json).

Per aggiungere una lingua: un file testi/<lingua>.json con le traduzioni. Le pagine non si toccano.
"""
import json
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
TESTI_DIR = RADICE / "testi"
LINGUE_SITO = ("it", "en")          # le lingue con tutte le pagine; le altre arrivano un file alla volta

_cataloghi = {}
_mancanti = {}
_coppie = {}   # testo inglese -> originale italiano, raccolti durante la generazione (per i file di rilettura)


def catalogo(lang):
    if lang not in _cataloghi:
        f = TESTI_DIR / f"{lang}.json"
        _cataloghi[lang] = json.loads(f.read_text(encoding="utf-8")).get("testi", {}) if f.exists() else {}
    return _cataloghi[lang]


def testo(lang, it_txt, en_txt, /, **valori):
    """Il testo nella lingua `lang` («it», «en», …; vero/falso valgono italiano/inglese, per le funzioni che ricevono ancora «it»).
    Senza segnaposti il testo esce com'è scritto (anche con graffe dentro, es. CSS)."""
    if lang is True:
        lang = "it"
    elif lang is False:
        lang = "en"
    if it_txt and en_txt and lang not in ("it", "en"):
        _coppie.setdefault(en_txt, it_txt)
    if lang == "it":
        modello = it_txt
    elif lang == "en":
        modello = en_txt
    elif not en_txt:
        modello = en_txt
    else:
        modello = catalogo(lang).get(en_txt) or None   # vuoto = non ancora tradotto
        if modello is None:
            _mancanti.setdefault(lang, set()).add(en_txt)
            modello = en_txt
    return modello.format(**valori) if valori else modello


def traduttore(lang):
    """La funzione T di una pagina: T(italiano, inglese, **valori)."""
    if lang is True:          # alcune funzioni ricevono ancora «it» (vero/falso) invece della lingua
        lang = "it"
    elif lang is False:
        lang = "en"

    def T(it_txt, en_txt, /, **valori):
        return testo(lang, it_txt, en_txt, **valori)
    return T


def salva_coppie(parte=""):
    """Scrive testi/originali-italiani{parte}.json: per ogni testo inglese del catalogo l'originale italiano (per la rilettura)."""
    (TESTI_DIR / f"originali-italiani{parte}.json").write_text(json.dumps(_coppie, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def salva_mancanti(parte=""):
    """Scrive l'elenco dei testi senza traduzione, una lista per lingua (da chiamare a fine generazione)."""
    for lang in sorted(set(_mancanti) | set(NUOVE)):   # anche vuoto: così l'elenco vecchio non resta
        insieme = _mancanti.get(lang, set())
        TESTI_DIR.mkdir(exist_ok=True)
        (TESTI_DIR / f"mancanti-{lang}{parte}.json").write_text(json.dumps(sorted(insieme), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------------------------------------------
# Lingue in più (26/11/2026): quali pagine esistono in ogni lingua e come si chiamano gli indirizzi.
# Le pagine di una lingua nuova si costruiscono come quelle inglesi (stessi dati, testi dal catalogo testi/<lingua>.json);
# poi localizza_link() porta i collegamenti verso le pagine della stessa lingua, quando esistono. Dove una pagina non
# c'è nella lingua (Già pubblici, calendario, Shop…) il collegamento resta alla versione inglese.
NUOVE = ("de", "fr", "es")                      # lingue con pagine proprie oltre a italiano e inglese (francese e spagnolo dopo)
SIGLE = ("it", "en", "de", "fr", "es")
LOCALE = {"it": "it-IT", "en": "en-GB", "de": "de-DE", "fr": "fr-FR", "es": "es-ES"}
OG_LOCALE = {"it": "it_IT", "en": "en_GB", "de": "de_DE", "fr": "fr_FR", "es": "es_ES"}
CARTELLA = {"de": {"home": "de", "autore": "de/autor", "paesi": "de/gemeinfrei", "anno": "de/gemeinfrei-{anno}", "come": "de/so-funktioniert-es",
                   "shop": "de/shop", "gia": "de/schon-gemeinfrei", "calendario": "de/kalender", "radar": "de/radar"},
            "fr": {"home": "fr", "autore": "fr/auteur", "paesi": "fr/domaine-public", "anno": "fr/domaine-public-{anno}", "come": "fr/comment-ca-marche",
                   "shop": "fr/boutique", "gia": "fr/deja-libres", "calendario": "fr/calendrier", "radar": "fr/radar"},
            "es": {"home": "es", "autore": "es/autor", "paesi": "es/dominio-publico", "anno": "es/dominio-publico-{anno}", "come": "es/como-funciona",
                   "shop": "es/tienda", "gia": "es/ya-libres", "calendario": "es/calendario", "radar": "es/radar"}}
# indirizzo della pagina di ogni paese in ogni lingua (26/11/2026: tutto il sito nelle tre lingue, decisione di Marco)
PAESE_SLUG = {"de": {"it": "italien", "fr": "frankreich", "de": "deutschland", "es": "spanien", "uk": "vereinigtes-koenigreich", "us": "usa"},
              "fr": {"it": "italie", "fr": "france", "de": "allemagne", "es": "espagne", "uk": "royaume-uni", "us": "etats-unis"},
              "es": {"it": "italia", "fr": "francia", "de": "alemania", "es": "espana", "uk": "reino-unido", "us": "estados-unidos"}}
PAESE_EN = {"it": "italy", "fr": "france", "de": "germany", "uk": "united-kingdom", "es": "spain", "us": "united-states"}
# sezioni già costruite nelle lingue in più: i collegamenti alle versioni inglesi di queste passano alla lingua
PRONTE = {"home", "autore", "paesi", "anno", "come", "shop", "radar", "gia", "calendario"}
EN = {"come": "/en/how-it-works/", "shop": "/en/shop/", "gia": "/en/already-public/", "calendario": "/en/calendar/", "radar": "/en/radar/"}
MESI = {"de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"],
        "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
        "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]}


MESI_BREVI = {"de": ["Jan.", "Feb.", "März", "Apr.", "Mai", "Juni", "Juli", "Aug.", "Sep.", "Okt.", "Nov.", "Dez."],
              "fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
              "es": ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sept.", "oct.", "nov.", "dic."]}


def data(lang, g, m, y):
    """Data lunga nelle lingue in più: «1. Januar 2027», «1er janvier 2027», «1 de enero de 2027»."""
    if lang == "de":
        return f"{g}. {MESI['de'][m - 1]} {y}"
    if lang == "fr":
        return f"{'1er' if g == 1 else g} {MESI['fr'][m - 1]} {y}"
    if lang == "es":
        return f"{g} de {MESI['es'][m - 1]} de {y}"
    raise KeyError(lang)


def data_breve(lang, y):
    """«1. Jan. 2027», «1er janv. 2027», «1 ene. 2027»."""
    return {"de": f"1. Jan. {y}", "fr": f"1er janv. {y}", "es": f"1 ene. {y}"}[lang]


# paesi nelle frasi «… in Italia, Francia, Germania e Regno Unito», per lingua (forma con preposizione)
PAESI_IN = {"de": {"it": "in Italien", "fr": "in Frankreich", "de": "in Deutschland", "uk": "im Vereinigten Königreich", "es": "in Spanien"},
            "fr": {"it": "en Italie", "fr": "en France", "de": "en Allemagne", "uk": "au Royaume-Uni", "es": "en Espagne"},
            "es": {"it": "en Italia", "fr": "en Francia", "de": "en Alemania", "uk": "en el Reino Unido", "es": "en España"}}
CONG = {"de": " und ", "fr": " et ", "es": " y "}


def elenco_paesi(lang, paesi):
    """«in Italien, Frankreich, Deutschland und im Vereinigten Königreich», «en Italie, en France, en Allemagne et au Royaume-Uni»,
    «en Italia, Francia, Alemania y el Reino Unido»."""
    n = [PAESI_IN[lang][x] for x in paesi]
    if not n:
        return ""
    if lang == "fr":   # in francese la preposizione si ripete
        return n[0] if len(n) == 1 else ", ".join(n[:-1]) + CONG[lang] + n[-1]
    pref = {"de": "in ", "es": "en "}[lang]
    corti = [x[len(pref):] if x.startswith(pref) else x for x in n]
    if len(n) == 1:
        return n[0]
    return n[0] + "".join(", " + c for c in corti[1:-1]) + CONG[lang] + corti[-1]


def localizza_link(html, lang, autori=(), anni=()):
    """Nelle pagine di una lingua nuova: i collegamenti alle pagine inglesi che esistono anche in questa lingua
    passano alla versione della lingua (schede autore in `autori`, pagine dell'anno in `anni`, paesi, sezioni in PRONTE, home)."""
    import re
    c = CARTELLA[lang]
    aut = set(autori)
    import glob as _g, re as _re
    anni = set(anni) | {int(_re.search(r"(\d{4})", f).group(1)) for f in _g.glob(str(RADICE / "data" / "[0-9][0-9][0-9][0-9].json"))}   # ogni anno con la sua pagina
    html = re.sub(r'href="/en/author/([^/"#]+)/', lambda m: f'href="/{c["autore"]}/{m.group(1)}/' if m.group(1) in aut else m.group(0), html)
    for a in anni:
        html = html.replace(f'href="/en/public-domain-{a}/', f'href="/{c["anno"].format(anno=a)}/')
    for k, s in PAESE_SLUG[lang].items():
        html = html.replace(f'href="/en/public-domain/{PAESE_EN[k]}/', f'href="/{c["paesi"]}/{s}/')
    for sez, u in EN.items():
        if sez in PRONTE:
            html = html.replace(f'href="{u}', f'href="/{c[sez]}/')
    html = html.replace('href="/en/public-domain/"', f'href="/{c["paesi"]}/"').replace('href="/en/"', f'href="/{c["home"]}/"')
    html = html.replace('href="/en/author/"', f'href="/{c["autore"]}/"')   # indice degli autori
    return html


def percorso(lang, en):
    """L'indirizzo nella lingua di una pagina inglese (stesse regole di localizza_link)."""
    return localizza_link(f'href="{en}"', lang, (), range(2020, 2100))[6:-1]


def selettore(lang, indirizzi):
    """Il tasto lingua: IT · EN · DE … (computer), «DE ▾» con l'elenco (telefono). `indirizzi` = {lingua: percorso} delle
    versioni che esistono; la lingua della pagina è segnata, le altre sono collegamenti."""
    voci = []
    for l in SIGLE:
        if l == lang:
            voci.append(f'<a aria-current="true" lang="{l}">{l.upper()}</a>')
        elif l in indirizzi:
            voci.append(f'<a href="{indirizzi[l]}" hreflang="{l}" lang="{l}">{l.upper()}</a>')
    return (f'<div class="lng" id="lng"><button type="button" class="lng-b" aria-haspopup="true" aria-expanded="false">'
            f'{lang.upper()} <span>▾</span></button><span class="lng-l">{"".join(voci)}</span></div>')


CSS_SELETTORE = (".lng{position:relative;display:flex;align-items:center}"
                 ".lng-b{display:none;font:500 12px/1 var(--mono,'DM Mono',monospace);letter-spacing:.12em;background:none;border:0;color:inherit;cursor:pointer;padding:6px 0}.lng-b span{font-size:9px}"
                 ".lng-l{display:flex;gap:14px}.lng-l a{font:500 12px/1 var(--mono,'DM Mono',monospace);letter-spacing:.12em;color:inherit;text-decoration:none;padding:6px 0;border-bottom:2px solid transparent}"
                 ".lng-l a[aria-current]{border-bottom-color:#FF4326}.lng-l a[href]:hover{color:#FF4326}"
                 "@media (max-width:860px){.lng-b{display:block}.lng-l{display:none;position:absolute;top:100%;right:-10px;flex-direction:column;gap:0;background:#F7F7F4;color:#0C0C10;border:1px solid #0C0C10;padding:6px 14px;z-index:60;min-width:64px}"
                 ".lng.on .lng-l{display:flex}.lng-l a{padding:9px 0}}")
# parole lunghe del tedesco («DEUTSCHLAND», «GEMEINFREI») nei titoloni sul telefono: un po' più piccoli, così stanno nella riga
CSS_LINGUA = "@media (max-width:760px){h1.h1{font-size:clamp(48px,14.5vw,104px)}}"
JS_SELETTORE = ("<script>document.addEventListener('click',function(e){var l=document.getElementById('lng');if(!l)return;"
                "var b=e.target.closest('.lng-b');if(b){l.classList.toggle('on');b.setAttribute('aria-expanded',l.classList.contains('on'));}"
                "else if(!e.target.closest('.lng-l'))l.classList.remove('on');});</script>")


def hreflang(indirizzi, sito, x_default=True):
    """<link rel=alternate> per tutte le versioni che esistono; x-default sull'italiano, come oggi (dove c'era)."""
    righe = [f'<link rel="alternate" hreflang="{l}" href="{sito}{indirizzi[l]}">' for l in SIGLE if l in indirizzi]
    if x_default and ("en" in indirizzi or "it" in indirizzi):   # 26/11/2026: la versione di partenza è l'inglese
        righe.append(f'<link rel="alternate" hreflang="x-default" href="{sito}{indirizzi.get("en", indirizzi.get("it"))}">')
    return "\n".join(righe) + "\n"


# ---------------------------------------------------------------------------------------------------------------
# 26/11/2026 (Marco): la home principale è quella inglese. publicdomainradar.com/ = inglese, /it/ = italiano,
# /en/ rimanda a /. Tutte le altre pagine tengono il loro indirizzo. Una passata sola, alla fine della generazione,
# sistema i collegamenti alla home in tutte le pagine (un posto solo, invece di cambiare ogni programma).
def sistema_home(radice):
    import re as _re
    sito = "https://publicdomainradar.com"
    n = 0
    for f in Path(radice).rglob("*.html"):
        if any(x in f.parts for x in (".git", "node_modules", "mockup")) or f.parts[-2:] == ("en", "index.html"):
            continue
        h = f.read_text(encoding="utf-8")
        m = _re.search(r'<html lang="(\w+)"', h)
        lang = m.group(1) if m else ""
        h2 = h
        if lang == "it":   # solo nei collegamenti <a>: le righe hreflang e canonical restano quelle giuste
            h2 = _re.sub(r'(<a\b[^>]*?\bhref=")(?:/|' + _re.escape(sito) + r'/)"', lambda m: m.group(1) + "/it/\"", h2)
        h2 = h2.replace('href="/en/"', 'href="/"').replace(f'href="{sito}/en/"', f'href="{sito}/"')
        if h2 != h:
            f.write_text(h2, encoding="utf-8")
            n += 1
    return n
