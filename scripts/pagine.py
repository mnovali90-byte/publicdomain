#!/usr/bin/env python3
"""Crea una pagina statica per ogni autore letterario con abbastanza contenuto, più gli indici e la sitemap.

Le pagine sono fatte solo con i dati già scaricati dalle fonti aperte (nessun testo scritto da un'AI).
Una pagina nasce solo se l'autore ha una biografia E almeno un'opera: le pagine vuote non servono a chi
legge e Google le tratta come spam.

Esce in: autore/<nome>/ (italiano), en/author/<nome>/ (inglese, solo se esiste la biografia inglese),
i due indici e sitemap.xml. Le pagine inglesi non mostrano opere, paesi e professioni, perché in Wikidata
hanno etichette italiane: meglio meno contenuto che contenuto in due lingue.
"""
from controlli import problemi as problemi_conteggio  # noqa: E402
import datetime
import glob
import html
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
SITO = "https://publicdomainradar.com"
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
MESI_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
NOMI_LINGUA = {"it": {"it": "italiano", "en": "inglese", "es": "spagnolo", "de": "tedesco", "fr": "francese"},
               "en": {"it": "Italian", "en": "English", "es": "Spanish", "de": "German", "fr": "French"}}
PERCORSO = {"it": "autore", "en": "en/author"}   # cartella delle pagine, per lingua


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def pulisci(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>", "", str(s or ""))).strip()


def migliaia(n, lang="it"):
    return f"{int(n):,}".replace(",", "." if lang == "it" else ",")


def data_l(lang, anno):
    return f"1° {MESI[0]} {anno}" if lang == "it" else f"1 January {anno}"


def slug_base(nome):
    t = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def anno_di(iso):
    m = re.match(r"^(-?\d{1,4})", str(iso or ""))
    return int(m.group(1)) if m else None


def iso_valida(iso):
    return bool(re.match(r"^\d{4}(-\d{2}(-\d{2})?)?$", str(iso or "")))


def bio_di(a, lang="it"):
    """Pagina italiana: biografia in italiano se c'è, altrimenti in inglese (come la scheda del sito).
    Pagina inglese: solo biografia inglese (niente testi in due lingue)."""
    if lang == "en":
        b = (a.get("bios") or {}).get("en")
        return {"testo": pulisci(b["testo"]), "url": b.get("url"), "lingua": "en"} if b and b.get("testo") else None
    for l in ("it", "en"):
        b = (a.get("bios") or {}).get(l)
        if b and b.get("testo"):
            return {"testo": pulisci(b["testo"]), "url": b.get("url"), "lingua": l}
    if a.get("bio"):
        return {"testo": pulisci(a["bio"]), "url": a.get("bio_url"), "lingua": a.get("bio_lingua") or "it"}
    return None


def abbastanza_contenuto(a, lang="it"):
    return bool(a.get("letterario") and bio_di(a, lang) and a.get("opere") and anno_di(a.get("morte")))


def paese_per_paese(D, lang="it"):
    """Stesse regole della scheda del sito (bloccoPaesi in index.html): vanno tenute allineate."""
    d = lambda y: data_l(lang, y)
    if lang == "en":
        return [
            f"EU (base rule), Germany and the United Kingdom: from {d(D + 71)}.",
            f"France: from {d(D + 71)}. Wartime extensions are not added to the 70 years (French Court of Cassation, 2007). Exception: authors who «died for France» get 30 more years.",
            f"Italy: from {d(D + 71)}. The 6-year wartime extension was repealed in 1996. For authors from Allied countries in the Second World War the term can be longer (1947 Peace Treaty): check case by case.",
            (f"Spain: not before {d(D + 81)} (80 years after death, because the author died before 1987; the law does not say how the year is counted)."
             if D < 1987 else f"Spain: from {d(D + 71)}."),
        ]
    return [
        f"UE (base), Germania e Regno Unito: dal {d(D + 71)}.",
        f"Francia: dal {d(D + 71)}. Le proroghe di guerra non si sommano ai 70 anni (Cassazione francese, 2007). Eccezione: gli autori «morti per la Francia» hanno 30 anni in più.",
        f"Italia: dal {d(D + 71)}. La proroga di guerra di 6 anni è stata abrogata nel 1996. Per gli autori di paesi alleati nella Seconda guerra mondiale la durata può essere più lunga (Trattato di pace del 1947): va verificato caso per caso.",
        (f"Spagna: non prima del {d(D + 81)} (80 anni dalla morte, perché è morto prima del 1987; la legge non dice come si conta l'anno)."
         if D < 1987 else f"Spagna: dal {d(D + 71)}."),
    ]


CSS = """
:root{--ink:#0C0C10;--carta:#F7F7F4;--vermiglio:#FF4326;--vermiglio-testo:#C2301A;--muto:#5C5C66;--riquadro:#E4E2DA;--notte:#1C1C24;
--display:'Big Shoulders Display',Impact,'Arial Narrow',sans-serif;--testo:'Instrument Sans',system-ui,sans-serif;--mono:'DM Mono',ui-monospace,Menlo,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--carta);color:var(--ink);font-family:var(--testo);line-height:1.6;-webkit-text-size-adjust:100%}
a{color:var(--vermiglio-testo)}
.barra{background:var(--ink);color:#fff;padding:14px 20px;font-family:var(--mono);font-size:13px;letter-spacing:.08em;text-transform:uppercase;display:flex;justify-content:space-between;gap:16px}
.barra a{color:#fff;text-decoration:none}
main{max-width:780px;margin:0 auto;padding:32px 20px 72px}
h1{font-family:var(--display);font-weight:900;font-size:clamp(40px,9vw,76px);line-height:.95;text-transform:uppercase;margin:8px 0 12px}
h2{font-family:var(--mono);font-weight:500;font-size:13px;letter-spacing:.1em;text-transform:uppercase;color:var(--muto);margin:40px 0 10px;border-top:2px solid var(--ink);padding-top:12px}
.sotto{color:var(--muto);font-size:14px}
.lead{font-size:19px}
ul{padding-left:20px}li{margin:6px 0}
table{border-collapse:collapse;width:100%;font-size:15px}td,th{border-bottom:1px solid var(--riquadro);padding:8px 6px;text-align:left}
figure{margin:0 0 20px}figure img{max-width:100%;max-height:420px;display:block;background:var(--riquadro)}figcaption{font-size:12px;color:var(--muto);margin-top:6px}
.cta{display:inline-block;margin-top:28px;padding:12px 18px;border:1.5px solid var(--ink);color:var(--ink);text-decoration:none;font-family:var(--mono);font-size:13px;text-transform:uppercase;letter-spacing:.06em}
main:has(.sa){max-width:720px;padding:20px 0 72px}
.sa-et{font-family:var(--mono);font-weight:500;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muto);margin:0;padding:0 24px}
.sa-head{display:flex;gap:18px;align-items:flex-end;padding:18px 24px 8px}
.sa-foto{flex:none;width:104px;height:132px;background:var(--riquadro);overflow:hidden}
.sa-foto img{width:100%;height:100%;object-fit:cover;object-position:50% 20%;display:block}
.sa-ini{display:flex;align-items:flex-start;padding:4px 8px;font-family:var(--display);font-weight:900;font-size:64px;line-height:1;color:#D2CFC4}
.sa h1{font-size:clamp(40px,10vw,64px);line-height:.9;margin:0}
.sa-desc{margin:8px 0 0;font-size:15px;line-height:1.4;color:var(--muto)}
.sa-credito{padding:0 24px;margin:0;font-family:var(--mono);font-size:11px;color:var(--muto)}
.sa-libero{padding:18px 24px 30px}
.libero-blocco{background:var(--vermiglio);color:var(--ink);padding:20px 22px}
.lb-et{font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase}
.lb-data{font-family:var(--display);font-weight:900;font-size:clamp(36px,9vw,52px);line-height:.95;text-transform:uppercase;margin:6px 0}
.lb-sotto{font-size:15px}
.lb-ver{margin:12px 0 0;display:flex;gap:10px;align-items:flex-start;font-size:14px;line-height:1.45;color:var(--muto)}
.lb-ver svg{flex:none;margin-top:2px;color:var(--ink)}
.lb-altri{margin-top:18px;border-top:1px solid var(--riquadro);border-bottom:1px solid var(--riquadro)}
.lb-altri summary{padding:12px 0;font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;cursor:pointer}
.lb-altri ul{list-style:none;margin:0;padding:0 0 4px}.lb-altri li{margin:0;padding:6px 0;font-size:15px;line-height:1.45}
.sa-sez{padding:28px 24px;border-top:1px solid #D9D6CC}
.sa-sez h2{margin:0 0 16px;border:0;padding:0;font-size:12px;letter-spacing:.14em}
.sa-bio{margin:0;font-size:17px;line-height:1.55}
.sa-sez a{color:var(--ink)}
.sa-nota{margin:12px 0 0;font-size:14px;line-height:1.5;color:var(--muto)}
.sa-testo{margin:0 0 10px;font-size:15px;line-height:1.55}
.sa-opere{list-style:none;margin:0;padding:0}
.sa-opere li{display:flex;justify-content:space-between;gap:16px;margin:0;padding:10px 0;border-bottom:1px solid #D9D6CC;font-size:17px;line-height:1.35}
.sa-opere .anno{flex:none;font-family:var(--mono);font-size:13px;color:var(--muto)}
.ed-boxes{display:flex;gap:12px;flex-wrap:wrap}.ed-box{flex:1;min-width:140px;background:var(--riquadro);padding:14px 16px}
.ed-box b{display:block;font-family:var(--display);font-weight:900;font-size:40px;line-height:1}.ed-box span{font-size:14px}
.sa-barra{display:flex;flex-direction:column;gap:8px;margin-bottom:18px}.sa-bn{font-size:17px;font-weight:600}
.sa-asta{height:10px;background:var(--riquadro)}.sa-asta i{display:block;height:10px;background:var(--vermiglio)}
.sa-val{font-size:14px;color:var(--muto)}.sa-val b{color:var(--ink)}
.sa-azioni{padding:8px 24px 0}
.sa-salva{display:flex;align-items:center;justify-content:center;height:56px;background:var(--ink);color:var(--carta);text-decoration:none;font-family:var(--mono);font-size:13px;letter-spacing:.12em;text-transform:uppercase}
footer{background:var(--ink);color:#B9B9C6;font-size:13px;padding:32px 20px}footer p{max-width:780px;margin:0 auto 10px}footer a{color:#fff}
"""

TESTA = """<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<title>{titolo}</title>
<meta name="description" content="{descr}">
<link rel="canonical" href="{url}">
{alterne}<meta property="og:type" content="{og_tipo}">
<meta property="og:site_name" content="Public Domain Radar">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{titolo}">
<meta property="og:description" content="{descr}">
<meta name="twitter:card" content="summary">
{jsonld}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@900&family=Instrument+Sans:wght@400;600&family=DM+Mono:wght@500&display=swap" rel="stylesheet">
<style>{css}</style>
<!-- contatore visite senza cookie (GoatCounter) -->
<script data-goatcounter="https://pdr.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</head>
<body>
<div class="barra"><a href="{home}" aria-label="Public Domain Radar">@@MARCHIO@@</a>{altra_lingua}</div>
"""

from marchio import marchio_html, CSS_MARCHIO
TESTA = TESTA.replace("@@MARCHIO@@", marchio_html(104))
CSS += CSS_MARCHIO

PIEDE = {
    "it": """<footer>
<p>Un progetto di Marco Novali · <a href="https://www.linkedin.com/in/marconovali" rel="me noopener" target="_blank">LinkedIn</a></p>
<p>Fonti: Wikidata (CC0), Wikipedia (testi CC BY-SA, con link alla pagina d'origine), Wikimedia Commons (ritratti, ciascuno con la sua licenza), Open Library, catalogo SBN. Dati aperti, aggiornati ogni mese in automatico; possono contenere errori.</p>
<p>Le date sono un calcolo indicativo dalle norme elencate nel <a href="/#regole-paesi">riquadro delle regole</a>. Non è consulenza legale: prima di pubblicare va controllato nella legge del paese.</p>
<p>Chi usa questi dati lo fa sotto la propria responsabilità. Le date sono indicative e riguardano le opere originali: traduzioni, illustrazioni ed edizioni recenti hanno diritti propri. Per un'edizione commerciale chiedi un parere a un esperto di diritto d'autore. <a href="https://github.com/mnovali90-byte/publicdomain/issues">Hai trovato un errore? Segnalalo</a>.</p>
<p><a href="/">Tutti gli autori</a> · <a href="/pubblico-dominio-@@ANNO@@/">Pubblico dominio @@ANNO@@</a> · <a href="/autore/">Indice degli autori</a> · <a href="https://github.com/mnovali90-byte/publicdomain">Codice e dati su GitHub</a></p>
</footer>
</body>
</html>
""",
    "en": """<footer>
<p>A project by Marco Novali · <a href="https://www.linkedin.com/in/marconovali" rel="me noopener" target="_blank">LinkedIn</a></p>
<p>Sources: Wikidata (CC0), Wikipedia (text CC BY-SA, linked to the original page), Wikimedia Commons (portraits, each with its own licence), Open Library, SBN catalogue. Open data, updated automatically every month; it may contain errors.</p>
<p>The dates are an indicative calculation from the rules listed in the <a href="/en/#regole-paesi">rules box</a>. Not legal advice: check the law of the country before publishing.</p>
<p>Anyone using this data does so at their own risk. The dates are indicative and refer to the original works: translations, illustrations and recent editions have their own rights. For a commercial edition, ask a copyright expert for advice. <a href="https://github.com/mnovali90-byte/publicdomain/issues">Found an error? Report it</a>.</p>
<p><a href="/en/">All authors</a> · <a href="/en/public-domain-@@ANNO@@/">Public domain @@ANNO@@</a> · <a href="/en/author/">Author index</a> · <a href="https://github.com/mnovali90-byte/publicdomain">Code and data on GitHub</a></p>
</footer>
</body>
</html>
""",
}


ANNO_PROSSIMO = datetime.date.today().year + 1   # l'anno del prossimo 1° gennaio
PIEDE = {k: v.replace("@@ANNO@@", str(ANNO_PROSSIMO)) for k, v in PIEDE.items()}


# Il calendario compare nel sito solo quando esiste data/calendario_ok (approvazione di Marco).
CALENDARIO_ON = (RADICE / "data" / "calendario_ok").exists()
if CALENDARIO_ON:
    try:
        _cal = max(json.loads((RADICE / "data" / "calendari_approvati.json").read_text(encoding="utf-8"))["anni"])
    except Exception:
        _cal = 2027
    PIEDE["it"] = PIEDE["it"].replace('<a href="/autore/">', f'<a href="/calendario/{_cal}/">Calendario anniversari</a> · <a href="/autore/">', 1)
    PIEDE["en"] = PIEDE["en"].replace('<a href="/en/author/">', f'<a href="/en/calendar/{_cal}/">Anniversaries calendar</a> · <a href="/en/author/">', 1)


def url_pagina(lang, slug=""):
    return f"{SITO}/{PERCORSO[lang]}/{slug + '/' if slug else ''}"


def alterne(lang, slug):
    """Collegamenti tra la pagina italiana e quella inglese (hreflang). Solo se esistono tutte e due."""
    if slug is None:
        return ""
    return (f'<link rel="alternate" hreflang="it" href="{url_pagina("it", slug)}">\n'
            f'<link rel="alternate" hreflang="en" href="{url_pagina("en", slug)}">\n')


NOMI_FONTE = {"it": {"wikidata": "Wikidata", "gnd": "Biblioteca nazionale tedesca (GND)", "loc": "Library of Congress"},
              "en": {"wikidata": "Wikidata", "gnd": "German National Library (GND)", "loc": "Library of Congress"}}


def blocco_verifica(a, lang):
    """Quante fonti indipendenti confermano l'anno di morte (scritto da scripts/verifica.py)."""
    v = a.get("verifica")
    if not v:
        return []
    it = lang == "it"
    fv = v.get("fonti", {})
    nomi = [NOMI_FONTE[lang][k] for k in fv if k in NOMI_FONTE[lang]]
    if v["esito"] == "verificato":
        t = (f"Anno di morte confermato da {len(nomi)} fonti indipendenti: {', '.join(nomi)}." if it
             else f"Year of death confirmed by {len(nomi)} independent sources: {', '.join(nomi)}.")
        return [f'<p class="sotto">{esc(t)}</p>\n']
    if v["esito"] == "nazionale":
        n = v.get("nazionale", {})
        t = (f"Anno di morte controllato a mano su una fonte del paese dell'autore ({n.get('fonte')}), perché le altre fonti non concordavano." if it
             else f"Year of death checked by hand against a source from the author's country ({n.get('fonte')}), because the other sources disagreed.")
        return [f'<p class="sotto">{esc(t)} <a href="{esc(n.get("url", ""))}" rel="noopener">{"Fonte" if it else "Source"}</a></p>\n']
    if v["esito"] == "documentato":
        cit = ", ".join(v.get("citate", {}))
        t = (f"Anno di morte documentato: Wikidata lo riporta citando {cit}. Le biblioteche nazionali che consultiamo non hanno questo autore." if it
             else f"Year of death documented: Wikidata gives it citing {cit}. The national libraries we check do not hold this author.")
        return [f'<p class="sotto">{esc(t)}</p>\n']
    if v["esito"] == "discorde":
        el = ", ".join([f"{NOMI_FONTE[lang][k]} {y}" for k, y in fv.items() if k in NOMI_FONTE[lang]]
                       + [f"{k} {y}" for k, y in v.get("citate", {}).items()])
        t = (f"Da verificare: le fonti non concordano sull'anno di morte ({el}). Le date qui sopra usano Wikidata." if it
             else f"To verify: the sources disagree on the year of death ({el}). The dates above use Wikidata.")
        return [f'<p><strong>{esc(t)}</strong></p>\n']
    t = ("Anno di morte da una sola fonte (Wikidata), senza fonti citate: le biblioteche nazionali consultate non lo riportano." if it
         else "Year of death from a single source (Wikidata), with no cited source: the national libraries we check do not record it.")
    return [f'<p class="sotto">{esc(t)}</p>\n']


def blocco_illustrazioni(a, lang):
    """Le illustrazioni (e le traduzioni) hanno diritti propri: si liberano con la morte di chi le ha fatte."""
    it = lang == "it"
    out = [f"<h2>{'Illustrazioni e traduzioni' if it else 'Illustrations and translations'}</h2>\n"]
    ill = [x for x in (a.get("illustratori") or []) if x.get("nome")]
    if ill:
        out.append("<ul>\n")
        for x in ill:
            if x.get("morte"):
                quando = (f"libere nell'UE dal {data_l(lang, x['morte'] + 71)}" if it else f"free in the EU from {data_l(lang, x['morte'] + 71)}")
                morto = f"morto nel {x['morte']}" if it else f"died {x['morte']}"
                r = f"{x['opera']}: illustrazioni di {x['nome']} ({morto}), {quando}" if it else f"{x['opera']}: illustrations by {x['nome']} ({morto}), {quando}"
            else:
                r = (f"{x['opera']}: illustrazioni di {x['nome']}, data di morte non nota" if it
                     else f"{x['opera']}: illustrations by {x['nome']}, year of death unknown")
            out.append(f"<li>{esc(r)}</li>\n")
        out.append("</ul>\n")
    out.append('<p class="sotto">' + (
        "Le date di questa pagina valgono per i testi originali. Illustrazioni e traduzioni hanno diritti propri, "
        "che durano 70 anni dalla morte dell'illustratore o del traduttore: un libro può avere il testo libero e i disegni ancora protetti."
        if it else
        "The dates on this page apply to the original texts. Illustrations and translations have their own rights, "
        "lasting 70 years after the death of the illustrator or translator: a book can have a free text and still-protected drawings.") + "</p>\n")
    return out


# Stati dell'epoca -> paese di oggi: stessa tabella della scheda del sito (PAESI in index.html), da tenere allineata
PAESI_MODERNI = {
    "Germania": ["reich tedesco", "impero tedesco", "repubblica di weimar", "germania nazista", "repubblica democratica tedesca", "germania ovest", "germania est", "confederazione germanica"],
    "Regno Unito": ["regno unito di gran bretagna e irlanda", "regno unito di gran bretagna e irlanda del nord", "inghilterra", "impero britannico"],
    "India": ["impero anglo-indiano", "dominion dell'india", "india britannica", "raj britannico"],
    "Italia": ["regno d'italia", "regno di sardegna", "repubblica sociale italiana"],
    "Russia": ["impero russo", "unione sovietica", "repubblica socialista federativa sovietica russa"],
    "Austria": ["impero austriaco", "austria-ungheria", "impero austro-ungarico", "cisleitania"],
    "Francia": ["terza repubblica francese", "seconda repubblica francese", "francia di vichy", "impero francese"],
    "Spagna": ["regno di spagna", "seconda repubblica spagnola", "stato spagnolo"],
    "Stati Uniti": ["stati uniti d'america"],
    "Giappone": ["impero giapponese", "impero del giappone"],
    "Cina": ["repubblica di cina", "impero cinese", "dinastia qing"],
    "Bielorussia": ["rss bielorussa", "repubblica socialista sovietica bielorussa"],
    "Ucraina": ["rss ucraina", "repubblica socialista sovietica ucraina"],
    "Georgia": ["rss georgiana", "repubblica socialista sovietica georgiana", "repubblica democratica di georgia"],
    "Armenia": ["rss armena", "repubblica socialista sovietica armena", "prima repubblica di armenia"],
    "Azerbaigian": ["rss azera", "repubblica socialista sovietica azera", "repubblica democratica di azerbaigian"],
    "Estonia": ["rss estone"],
    "Lettonia": ["rss lettone"],
    "Lituania": ["rss lituana"],
    "Kazakistan": ["rss kazaka"],
    "Uzbekistan": ["rss uzbeka"],
    "Moldavia": ["rss moldava"],
    "Paesi Bassi": ["regno dei paesi bassi"],
    "Polonia": ["seconda repubblica di polonia", "repubblica popolare di polonia", "regno del congresso"],
    "Danimarca": ["regno di danimarca"],
    "Egitto": ["regno d'egitto"],
    "Iraq": ["regno dell'iraq"],
    "Ungheria": ["regno d'ungheria", "repubblica popolare d'ungheria"],
    "Romania": ["regno di romania", "repubblica socialista di romania"],
    "Grecia": ["regno di grecia"],
    "Belgio": ["regno del belgio"],
    "Svezia": ["regno di svezia"],
    "Norvegia": ["regno di norvegia"],
}
POST_SOVIETICI = set(['Bielorussia', 'Ucraina', 'Georgia', 'Armenia', 'Azerbaigian', 'Estonia', 'Lettonia', 'Lituania', 'Kazakistan', 'Uzbekistan', 'Moldavia'])
_MODERNO = {v: k for k, lista in PAESI_MODERNI.items() for v in lista}


def paesi_moderni(lista):
    norm = lambda x: unicodedata.normalize("NFD", str(x)).encode("ascii", "ignore").decode().lower()
    out = []
    for x in lista or []:
        m = _MODERNO.get(norm(x), x)
        if m not in out:
            out.append(m)
    if "Russia" in out and any(x in POST_SOVIETICI for x in out):   # Bielorussia, non anche «Russia» per via dell'Impero russo
        out.remove("Russia")
    return out


RANGHI = {}   # (wikidata, misura) -> (posizione, totale): calcolati in main() come nella classifica del sito


def calcola_ranghi(pacchetto):
    lett = [x for x in pacchetto["autori"] if x.get("letterario") and x.get("n_opere", 1) > 0 and not re.fullmatch(r"Q\d+", x["nome"])]
    for m, campo in (("it", "visite_it"), ("en", "visite_en"), ("int", "pagine_wikipedia")):
        ordine = sorted(lett, key=lambda x: (-(x.get("indice_" + m) if x.get("indice_" + m) is not None else -1), -(x.get(campo) or 0),
                                             -(x.get("pagine_wikipedia") or 0), x["nome"]))
        for r, x in enumerate(ordine, 1):
            RANGHI.setdefault((x["wikidata"], m), (r, len(ordine)))


def iniziali_nome(nome):
    p = [w for w in re.split(r"[\s().,]+", nome) if w]
    return ((p[0][:1] + p[-1][:1]) if len(p) > 1 else (p[0][:2] if p else "?")).upper()


def scheda_statica(a, lang, bd):
    """Corpo della pagina autore, con lo stesso disegno della scheda del sito (mockup approvato)."""
    it = lang == "it"
    nome = pulisci(a["nome"])
    nasc, D = anno_di(a.get("nascita")), anno_di(a.get("morte"))
    T = (lambda x, y: x) if it else (lambda x, y: y)
    o = ['<div class="sa">\n', f'<p class="sa-et">{T("Scheda autore", "Author card")}</p>\n<header class="sa-head">\n']
    foto = a.get("foto") or {}
    if foto.get("url"):
        o.append(f'<div class="sa-foto"><img src="{esc(foto["url"])}" alt="{T("Ritratto di", "Portrait of")} {esc(nome)}" loading="lazy"></div>\n')
    else:
        o.append(f'<div class="sa-foto sa-ini" aria-hidden="true">{esc(iniziali_nome(nome))}</div>\n')
    desc = [f"{nasc if nasc else '?'} – {D}"]
    if it and a.get("professioni"):
        desc.append(", ".join(a["professioni"][:2]))
    if it and a.get("paesi"):
        desc.append(", ".join(paesi_moderni(a["paesi"])[:2]))
    o.append(f'<div><h1>{esc(nome)}</h1>\n<p class="sa-desc">{esc(" · ".join(desc))}</p></div>\n</header>\n')
    if foto.get("url"):
        cap = " · ".join(x for x in (pulisci(foto.get("autore")), pulisci(foto.get("licenza"))) if x)
        pag = f' <a href="{esc(foto["pagina"])}" rel="noopener">Wikimedia Commons</a>' if foto.get("pagina") else ""
        o.append(f'<p class="sa-credito">{T("Foto", "Photo")}: {esc(cap)}{pag}</p>\n')
    # la risposta principale
    giorni = (datetime.date(D + 71, 1, 1) - datetime.date.today()).days
    quando = (T(f"tra {migliaia(giorni)} giorni", f"in {migliaia(giorni, lang)} days") if giorni > 0 else T("già libero", "already free"))
    o.append('<div class="sa-libero">\n<div class="libero-blocco">'
             f'<div class="lb-et">{T("Libero in Italia dal", "Free in the UK and the EU from")}</div>'
             f'<div class="lb-data">{data_l(lang, D + 71)}</div>'
             f'<div class="lb-sotto">{quando} · {T(f"anno di morte {D}", f"died in {D}")}</div></div>\n')
    v = a.get("verifica") or {}
    if v.get("esito") == "verificato":
        nomi = [NOMI_FONTE[lang][k] for k in v.get("fonti", {}) if k in NOMI_FONTE[lang]]
        o.append('<p class="lb-ver"><svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" '
                 'stroke-linecap="round" stroke-linejoin="round"><path d="M4 12l5 5L20 6"/></svg><span>'
                 + esc(T(f"Anno di morte confermato da {len(nomi)} fonti: {', '.join(nomi)}.", f"Year of death confirmed by {len(nomi)} sources: {', '.join(nomi)}."))
                 + "</span></p>\n")
    else:
        o += [x.replace('<p class="sotto">', '<p class="lb-ver">') for x in blocco_verifica(a, lang)]
    o.append(f'<details class="lb-altri"><summary>{T("Negli altri paesi", "In other countries")}</summary>\n<ul>\n')
    o += [f"<li>{esc(r)}</li>\n" for r in paese_per_paese(D, lang)]
    o.append(f"<li>{esc(T('USA: dipende dall’anno di pubblicazione di ogni opera (95 anni).', 'USA: depends on the publication year of each work (95 years).'))}</li>\n")
    o.append(f'</ul>\n<p class="sa-nota">{T("Calcolo indicativo, dalle norme del sito. Non è consulenza legale.", "Indicative calculation, based on the rules on the site. Not legal advice.")}</p></details>\n</div>\n')
    sez = lambda tit, corpo: f'<section class="sa-sez">\n<h2>{tit}</h2>\n{corpo}</section>\n'
    if bd:
        ln = f'<a href="{esc(bd["url"])}" rel="noopener">{T("Continua su Wikipedia", "Continue on Wikipedia")}</a>' if bd.get("url") else ""
        o.append(sez(T("Chi era", "Who they were"), f'<p class="sa-bio">{esc(bd["testo"])}</p>\n{ln}\n<p class="sa-nota">{T("Testo da Wikipedia, licenza CC BY-SA.", "Text from Wikipedia, licence CC BY-SA.")}</p>\n'))
    opere = [(x.get("titolo") if it else x.get("titolo_en"), x.get("anno")) for x in a.get("opere", [])[:10]]
    opere = [(t, y) for t, y in opere if t]
    if opere:
        righe = "".join(f'<li><span>{esc(t)}</span>' + (f'<span class="anno">{esc(y)}</span>' if y else "") + "</li>\n" for t, y in opere)
        extra = (f'<p class="sa-nota">{T(f"Su {migliaia(a["n_opere"])} opere registrate in Wikidata, qui le più note.", f"Of {migliaia(a["n_opere"], lang)} works recorded in Wikidata, the best known.")}</p>\n'
                 if a.get("n_opere", 0) > len(opere) else "")
        o.append(sez(T("Opere principali", "Main works"), f'<ul class="sa-opere">\n{righe}</ul>\n{extra}'))
    g = ((a.get("traduzioni") or {}).get("sbn_it") if it else (a.get("traduzioni") or {}).get("bl_en"))
    if g and g.get("trovato") and (g.get("stato") == "da_verificare" or problemi_conteggio(g, datetime.date.today().year)):
        o.append(sez(T("Registrazioni in italiano", "Records in English"),
                     f'<p class="sa-nota">{esc(T("Dati in verifica: per questo autore i numeri del catalogo si contraddicono, quindi non li mostriamo finché non sono corretti.", "Data under review: for this author the catalogue figures contradict each other, so we do not show them until they are fixed."))}</p>\n'))
    elif g and g.get("trovato"):
        box = lambda num, et: f'<div class="ed-box"><b>{migliaia(num, lang)}</b><span>{esc(et)}</span></div>'
        ult = f" · {T('più recente con anno certo:', 'latest with a certain year:')} {g['ultimo']}" if g.get("ultimo") else ""
        nota = (T("Registrazioni bibliografiche in italiano collegate all'autore nel catalogo SBN, comprese ristampe e antologie. Per ora comprendono anche altre collaborazioni (traduzioni, curatele, prefazioni), non solo i testi di cui è autore.", "")
                if it else "Bibliographic records in English linked to the author in the British Library catalogue, searched by surname and years of birth and death: some records catalogued differently may be missed. For now they also include other contributions (translations, editing, prefaces).")
        if it and g.get("metodo") == "nome":
            nota += " Autore riconosciuto solo dal nome: il conteggio può essere impreciso."
        o.append(sez(T("Registrazioni in italiano", "Records in English"),
                     f'<div class="ed-boxes">{box(g["edizioni"], T("registrazioni in italiano", "records in English"))}{box(g.get("dal_2000", 0), T("con anno dal 2000", "dated 2000 or later") + ult)}</div>\n<p class="sa-nota">{esc(nota)}</p>\n'))
    barre = []
    for m, campo, etich in ((("it", "visite_it", T("In Italia", "")),) if it else (("en", "visite_en", "In the English-speaking world"),)) + (("int", "pagine_wikipedia", T("Nel mondo", "Worldwide")),):
        idx = a.get("indice_" + m)
        if idx is None:
            continue
        val = a.get(campo) or 0
        testo = (T(f"pagina Wikipedia in {val} lingue", f"Wikipedia page in {val} languages") if m == "int"
                 else T(f"{migliaia(val)} visite su Wikipedia in 12 mesi", f"{migliaia(val, lang)} Wikipedia views in 12 months") if val
                 else T("nessuna pagina in italiano", "no page in English"))
        rg = RANGHI.get((a["wikidata"], m))
        pos = f' · <b>{T(f"{rg[0]}° su {rg[1]}", f"#{rg[0]} of {rg[1]}")}</b>' if rg else ""
        barre.append(f'<div class="sa-barra"><div class="sa-bn">{etich}</div><div class="sa-asta"><i style="width:{max(0, min(100, idx))}%"></i></div>'
                     f'<div class="sa-val">{esc(testo)}{pos}</div></div>\n')
    if barre:
        o.append(sez(T("Quanto è conosciuto", "How well known"), "".join(barre)
                     + f'<p class="sa-nota">{T("Misura la curiosità per l’autore (visite alle pagine Wikipedia), non le vendite dei suoi libri.", "Measures curiosity about the author (Wikipedia page views), not sales of their books.")}</p>\n'))
    ill = "".join(blocco_illustrazioni(a, lang)[1:]).replace('<p class="sotto">', '<p class="sa-testo">')
    o.append(sez(T("Prima di pubblicare", "Before publishing"), ill + f'<p class="sa-nota">{T("Calcolo indicativo, non consulenza legale.", "Indicative calculation, not legal advice.")}</p>\n'))
    o.append("</div>\n")
    return "".join(o)


def pagina_autore(a, slug, lang, ha_altra):
    nome = pulisci(a["nome"])
    nasc, mor = anno_di(a.get("nascita")), anno_di(a.get("morte"))
    anni = f"{nasc if nasc else '?'} – {mor}"
    D = mor
    bd = bio_di(a, lang)
    url = url_pagina(lang, slug)
    it = lang == "it"
    if it:
        titolo = f"{nome} ({anni}): quando entra in pubblico dominio · Public Domain Radar"
        descr = (f"{nome} è morto nel {D}: nell'UE le sue opere sono libere dal {data_l(lang, D + 71)}. "
                 f"Date per Italia, Francia, Germania e Spagna, edizioni italiane in SBN e opere principali, da dati aperti.")
    else:
        titolo = f"{nome} ({anni}): when the works enter the public domain · Public Domain Radar"
        descr = (f"{nome} died in {D}: in the EU the works are free from {data_l(lang, D + 71)}. "
                 f"Dates for the UK, Italy, France, Germany and Spain, and online interest, from open data.")
    persona = {"@context": "https://schema.org", "@type": "Person", "name": nome, "url": url,
               "sameAs": [u for u in (bd.get("url") if bd else None, a.get("url")) if u]}
    if iso_valida(a.get("nascita")):
        persona["birthDate"] = a["nascita"]
    if iso_valida(a.get("morte")):
        persona["deathDate"] = a["morte"]
    briciole = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Public Domain Radar", "item": SITO + ("/" if it else "/en/")},
        {"@type": "ListItem", "position": 2, "name": "Autori" if it else "Authors", "item": url_pagina(lang)},
        {"@type": "ListItem", "position": 3, "name": nome, "item": url}]}
    jsonld = "".join('<script type="application/ld+json">' + json.dumps(j, ensure_ascii=False).replace("</", "<\\/") + "</script>\n" for j in (persona, briciole))
    altra = ""
    if ha_altra:
        altra = (f'<a href="{url_pagina("en" if it else "it", slug)}" hreflang="{"en" if it else "it"}">{"English" if it else "Italiano"}</a>')
    out = [TESTA.format(lang=lang, titolo=esc(titolo), descr=esc(descr), url=url, alterne=alterne(lang, slug) if ha_altra else "",
                        og_tipo="profile", jsonld=jsonld, css=CSS, home="/" if it else "/en/", altra_lingua=altra), "<main>\n"]
    out.append(scheda_statica(a, lang, bd))

    cta = f'/#/autore/{esc(a["wikidata"])}' if it else f'/en/#/autore/{esc(a["wikidata"])}'
    out.append(f'<p class="sa-azioni"><a class="sa-salva" href="{cta}">{"Apri la scheda nel radar" if it else "Open the card in the radar"}</a></p>\n')
    out.append("</main>\n" + PIEDE[lang])
    return "".join(out)


def pagina_indice(voci, lang):
    it = lang == "it"
    url = url_pagina(lang)
    titolo = "Indice degli autori in pubblico dominio · Public Domain Radar" if it else "Index of authors entering the public domain · Public Domain Radar"
    descr = (f"{len(voci)} autori con la data di pubblico dominio paese per paese (UE, Italia, Francia, Germania, Spagna), da dati aperti." if it else
             f"{len(voci)} authors with the public-domain date country by country (EU, Italy, France, Germany, Spain), from open data.")
    out = [TESTA.format(lang=lang, titolo=esc(titolo), descr=esc(descr), url=url, alterne="", og_tipo="website", jsonld="", css=CSS,
                        home="/" if it else "/en/", altra_lingua=""), "<main>\n",
           f"<h1>{'Indice degli autori' if it else 'Index of authors'}</h1>\n",
           f'<p class="lead">' + (f"{len(voci)} autori con una pagina dedicata: biografia, opere e data di pubblico dominio paese per paese." if it else
                                  f"{len(voci)} authors with a dedicated page: biography, Italian editions and the public-domain date country by country.") + "</p>\n"]
    lettera = None
    for nome, slug, anni in voci:
        k = (nome[:1] or "#").upper()
        if k != lettera:
            if lettera is not None:
                out.append("</ul>\n")
            out.append(f"<h2>{esc(k)}</h2>\n<ul>\n")
            lettera = k
        out.append(f'<li><a href="/{PERCORSO[lang]}/{slug}/">{esc(nome)}</a> <span class="sotto">{esc(anni)}</span></li>\n')
    out.append("</ul>\n</main>\n" + PIEDE[lang])
    return "".join(out)


def testi_app(s, lang):
    """Le frasi dell'app (oggetto TESTI in index.html) per una lingua: {chiave: testo}."""
    inizio = s.index("const TESTI = {")
    j = s.index("\n" + lang + ": {", inizio)
    fine = s.index("\n};", j) if lang == "en" else s.index("\nen: {", j)
    out = {}
    for k, v in re.findall(r'(\w+): "((?:[^"\\]|\\.)*)"', s[j:fine]):
        out.setdefault(k, json.loads('"' + v + '"'))
    return out


def autori_in_vetrina(n=12):
    """I letterari più noti che si liberano il prossimo 1° gennaio (dati del sito), per il testo statico delle home."""
    f = RADICE / "data" / f"{ANNO_PROSSIMO}.json"
    if not f.exists():
        return []
    aut = [a for a in json.load(open(f, encoding="utf-8"))["autori"] if a.get("letterario") and a.get("pagina")]
    aut.sort(key=lambda a: -(a.get("indice_int") or a.get("indice") or 0))
    return aut[:n]


def blocco_statico(lang):
    """Elenco scritto nella pagina: Google lo legge subito; quando l'app parte lo sostituisce col carosello."""
    A = ANNO_PROSSIMO
    aut = autori_in_vetrina()
    if not aut:
        return ""
    if lang == "it":
        tit = f"Chi entra in pubblico dominio il 1° gennaio {A}"
        sotto = f"Autori morti nel {A - 71}: nell'Unione europea le loro opere diventano libere il 1° gennaio {A}."
        voci = "".join(f'<li><a href="/autore/{a["pagina"]}/">{esc(pulisci(a["nome"]))}</a> ({anno_di(a.get("nascita")) or "?"}–{anno_di(a["morte"])})</li>' for a in aut)
        piu = f'<p><a href="/pubblico-dominio-{A}/">Pubblico dominio {A}: tutto quello che diventa libero</a></p>'
    else:
        tit = f"Who enters the public domain on 1 January {A}"
        sotto = f"Authors who died in {A - 71}: in the European Union their works become free on 1 January {A}."
        voci = "".join(f'<li><a href="/en/author/{a["pagina_en"]}/">{esc(pulisci(a["nome"]))}</a> ({anno_di(a.get("nascita")) or "?"}–{anno_di(a["morte"])})</li>' for a in aut if a.get("pagina_en"))
        piu = f'<p><a href="/en/public-domain-{A}/">Public Domain {A}: everything that becomes free</a></p>'
    return (f'<!--statico--><div class="messaggio" style="padding:40px 0"><h2 style="font-size:22px;margin:0 0 8px">{esc(tit)}</h2>'
            f'<p style="margin:0 0 12px">{esc(sotto)}</p><ul style="margin:0;padding-left:20px;line-height:1.7">{voci}</ul>{piu}</div><!--/statico-->')


def metti_statico(s, lang):
    s = re.sub(r"<!--statico-->.*?<!--/statico-->", "", s, flags=re.S)
    a = '<div id="eroe">'
    if a not in s:
        raise RuntimeError("index.html è cambiato: manca il riquadro #eroe")
    return s.replace(a, a + blocco_statico(lang), 1)


def sostituisci(s, schema, nuovo):
    s2, n = re.subn(schema, lambda m: nuovo, s, count=1)
    if not n:
        raise RuntimeError("index.html è cambiato: non trovo " + schema[:50])
    return s2


def aggiorna_home_italiana():
    """Titolo, descrizione e testo statico della home con l'anno del prossimo 1° gennaio (parola chiave «pubblico dominio <anno>»)."""
    A = ANNO_PROSSIMO
    f = RADICE / "index.html"
    s = f.read_text(encoding="utf-8")
    tit = f"Pubblico dominio {A}: gli autori che diventano liberi · Public Domain Radar"
    descr = (f"Quali autori entrano in pubblico dominio il 1° gennaio {A}, con le regole di Italia, Francia, Germania e Spagna "
             f"lette sui testi di legge ufficiali. Dati aperti da Wikidata, Wikipedia e SBN, aggiornati ogni mese.")
    breve = f"Quali autori diventano liberi il 1° gennaio {A}, paese per paese, con dati aperti e fonti di legge ufficiali."
    s = sostituisci(s, r"<title>.*?</title>", f"<title>{esc(tit)}</title>")
    s = sostituisci(s, r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{esc(descr)}">')
    s = sostituisci(s, r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{esc(tit)}">')
    s = sostituisci(s, r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{esc(breve)}">')
    s = sostituisci(s, r'<meta name="twitter:description" content="[^"]*">', f'<meta name="twitter:description" content="{esc(breve)}">')
    i = s.index("const TESTI = {")
    s = s[:i] + re.sub(r'titolo: "[^"]*"', 'titolo: ' + json.dumps(tit, ensure_ascii=False), s[i:], count=1)
    s = metti_statico(s, "it")
    f.write_text(s, encoding="utf-8")


def crea_home_inglese():
    """en/index.html: la stessa app di index.html, con testi già in inglese nel codice della pagina (così Google la legge in inglese)."""
    A = ANNO_PROSSIMO
    s = (RADICE / "index.html").read_text(encoding="utf-8")
    en = testi_app(s, "en")
    tit = f"Public Domain {A}: books and authors entering the public domain · Public Domain Radar"
    descr = (f"Which books and authors enter the public domain on 1 January {A}, with the term rules of Italy, France, Germany and Spain "
             f"read from official legal texts. Open data from Wikidata, Wikipedia and SBN, updated monthly.")
    breve = f"Which books and authors become free on 1 January {A}, country by country, with open data and official legal sources."
    s = s.replace('<html lang="it">', '<html lang="en">', 1)
    s = sostituisci(s, r"<title>.*?</title>", f"<title>{esc(tit)}</title>")
    s = sostituisci(s, r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{esc(descr)}">')
    s = sostituisci(s, r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{esc(tit)}">')
    s = sostituisci(s, r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{esc(breve)}">')
    s = sostituisci(s, r'<meta name="twitter:description" content="[^"]*">', f'<meta name="twitter:description" content="{esc(breve)}">')
    s = sostituisci(s, r'<link rel="canonical" href="https://publicdomainradar.com/">', '<link rel="canonical" href="https://publicdomainradar.com/en/">')
    s = sostituisci(s, r'<meta property="og:url" content="https://publicdomainradar.com/">', '<meta property="og:url" content="https://publicdomainradar.com/en/">')
    s = sostituisci(s, r'\{"@type":"WebSite","name":"Public Domain Radar","url":"https://publicdomainradar.com/"',
                    '{"@type":"WebSite","name":"Public Domain Radar","url":"https://publicdomainradar.com/en/"')
    i = s.index("const TESTI = {")
    j = s.index("\nen: {", i)
    s = s[:j] + re.sub(r'titolo: "[^"]*"', 'titolo: ' + json.dumps(tit, ensure_ascii=False), s[j:], count=1)
    # i testi fissi della pagina (data-t) già in inglese, prima che parta l'app
    def trad(m):
        k = m.group(2)
        v = en.get(k)
        if v is None or "{" in v:
            return m.group(0)
        return m.group(1) + esc(v)
    s = re.sub(r'(<[^>]*\bdata-t="(\w+)"[^>]*>)([^<]*)(?=<)', trad, s)
    s = metti_statico(s, "en")
    (RADICE / "en").mkdir(exist_ok=True)
    (RADICE / "en" / "index.html").write_text(s, encoding="utf-8")


def file_autori():
    """Solo i file degli autori (2027.json, es-2027.json); us-*.json sono le opere."""
    return [f for f in sorted(glob.glob(str(RADICE / "data" / "*.json")))
            if re.fullmatch(r"(es-)?\d{4}\.json", Path(f).name)]


CSS_LANDING = """
body{background:var(--carta)}
.lp-in{max-width:1120px;margin:0 auto;padding:0 clamp(20px,4vw,48px)}
.lp-hero{background:var(--ink);color:#fff;padding:clamp(48px,9vw,112px) 0 clamp(56px,9vw,104px);position:relative;overflow:hidden}
.lp-hero:after{content:"";position:absolute;right:-8vw;top:-10vw;width:46vw;height:46vw;max-width:620px;max-height:620px;border-radius:50%;background:var(--vermiglio);opacity:.95}
.lp-hero .lp-in{position:relative;z-index:1}
.lp-occ{font-family:var(--mono);font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:#fff;margin:0 0 22px}
.lp-occ i{display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--vermiglio);margin-right:10px;box-shadow:0 0 0 2px #fff}
.lp-hero h1{font-size:clamp(56px,13vw,176px);line-height:.86;margin:0 0 26px;color:#fff;max-width:11ch;mix-blend-mode:normal}
.lp-hero h1 em{font-style:normal;color:var(--vermiglio);text-shadow:0 0 0 #000}
.lp-hero .lead{font-size:clamp(18px,2.2vw,22px);max-width:34rem;color:#E4E2DA;margin:0 0 34px}
.lp-cont{display:inline-flex;align-items:baseline;gap:14px;margin:0 0 34px;padding:14px 20px;border:1.5px solid #fff;background:var(--ink)}
.lp-cont b{font-family:var(--display);font-weight:900;font-size:clamp(44px,7vw,72px);line-height:1;color:#fff}
.lp-cont span{font-family:var(--mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#B9B9C6}
.lp-bott{display:flex;flex-wrap:wrap;gap:14px}
.lp-b{display:inline-block;padding:16px 24px;font-family:var(--mono);font-size:13px;letter-spacing:.08em;text-transform:uppercase;text-decoration:none;border:2px solid #fff}
.lp-b1{background:#fff;color:var(--ink)}.lp-b1:hover{background:var(--vermiglio);border-color:var(--vermiglio)}
.lp-b2{background:var(--ink);color:#fff}.lp-b2:hover{background:#fff;color:var(--ink)}
.lp-sez{padding:clamp(56px,8vw,104px) 0}
.lp-sez h2{font-family:var(--display);font-weight:900;font-size:clamp(36px,6.5vw,72px);line-height:.95;text-transform:uppercase;color:var(--ink);letter-spacing:0;margin:0 0 14px;border:0;padding:0}
.lp-occh{font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--vermiglio-testo);margin:0 0 12px}
.lp-sez .lead{max-width:40rem;color:#33333B}
.lp-due{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:36px}
.lp-card{border:2px solid var(--ink);padding:clamp(22px,3vw,36px);display:flex;flex-direction:column;background:#fff}
.lp-card.us{background:var(--ink);color:#fff;border-color:var(--ink)}
.lp-num{font-family:var(--display);font-weight:900;font-size:clamp(96px,14vw,168px);line-height:.8;color:var(--vermiglio)}
.lp-card h3{font-family:var(--mono);font-weight:500;font-size:13px;letter-spacing:.1em;text-transform:uppercase;margin:14px 0 6px}
.lp-card .gr{font-family:var(--display);font-weight:900;font-size:clamp(26px,3.4vw,38px);line-height:1;text-transform:uppercase;margin:0 0 12px}
.lp-card p{margin:0 0 18px;font-size:16px}
.lp-card a{margin-top:auto;font-family:var(--mono);font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:inherit;font-weight:500}
.lp-card.us a{color:#fff}
.lp-gr{display:grid;grid-template-columns:repeat(auto-fill,minmax(168px,1fr));gap:16px;margin-top:34px}
.lp-cop{aspect-ratio:2/3;padding:16px;display:flex;flex-direction:column;justify-content:space-between;text-decoration:none;transition:transform .15s;overflow:hidden}
.lp-cop:hover{transform:translateY(-5px)}
.lp-cop .t{font-family:var(--display);font-weight:900;line-height:.92;text-transform:uppercase;overflow-wrap:normal;word-break:normal}
.lp-cop .a{font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;line-height:1.4}
.c0{background:var(--vermiglio);color:var(--ink)}.c1{background:#E9E6DD;color:var(--ink)}.c2{background:#0E3B2E;color:var(--carta)}.c3{background:var(--notte);color:var(--carta)}
.lp-piu{margin-top:26px}
.lp-piu a{font-family:var(--mono);font-size:13px;letter-spacing:.06em;text-transform:uppercase;font-weight:500}
.lp-scuro{background:var(--notte);color:#fff}
.lp-scuro h2{color:#fff}.lp-scuro .lead{color:#D2CFC4}.lp-scuro .lp-occh{color:var(--vermiglio)}
.lp-aut{margin-top:34px;display:grid;grid-template-columns:1fr 1fr;column-gap:48px}
.lp-aut a{display:flex;justify-content:space-between;align-items:baseline;gap:16px;padding:16px 0;border-top:1px solid #4A4A58;text-decoration:none;color:#fff}
.lp-aut a:hover b{color:var(--vermiglio)}
.lp-aut b{font-family:var(--display);font-weight:900;font-size:clamp(24px,3vw,34px);line-height:1;text-transform:uppercase}
.lp-aut span{font-family:var(--mono);font-size:12px;color:#B9B9C6;white-space:nowrap}
.lp-pass{display:grid;grid-template-columns:repeat(3,1fr);gap:28px;margin-top:34px}
.lp-pass div{border-top:3px solid var(--ink);padding-top:14px}
.lp-pass b{font-family:var(--display);font-weight:900;font-size:56px;line-height:1;color:var(--vermiglio)}
.lp-pass h3{font-family:var(--mono);font-weight:500;font-size:13px;letter-spacing:.1em;text-transform:uppercase;margin:8px 0 6px}
.lp-pass p{margin:0;font-size:16px}
.lp-faq{margin-top:30px;max-width:46rem}
.lp-faq details{border-top:1px solid var(--ink);padding:16px 0}.lp-faq details:last-child{border-bottom:1px solid var(--ink)}
.lp-faq summary{cursor:pointer;font-weight:600;font-size:18px;list-style:none;display:flex;justify-content:space-between;gap:16px}
.lp-faq summary::-webkit-details-marker{display:none}
.lp-faq summary:after{content:"+";font-family:var(--mono);font-size:22px;line-height:1}
.lp-faq details[open] summary:after{content:"–"}
.lp-faq p{margin:12px 0 0;max-width:40rem}
.lp-fin{background:var(--vermiglio);color:var(--ink);padding:clamp(56px,8vw,96px) 0}
.lp-fin h2{font-family:var(--display);font-weight:900;text-transform:uppercase;letter-spacing:0;line-height:.95;border:0;padding:0;margin:0 0 16px;color:var(--ink);font-size:clamp(34px,6vw,64px)}
.lp-fin p{font-size:19px;max-width:36rem;margin:0 0 26px}
.lp-fin .lp-b{background:var(--ink);color:#fff;border-color:var(--ink)}.lp-fin .lp-b:hover{background:#fff;color:var(--ink)}
.lp-nota{font-size:13px;color:var(--muto);margin-top:30px;max-width:46rem}
@media(max-width:760px){.lp-due,.lp-aut,.lp-pass{grid-template-columns:1fr}.lp-hero:after{opacity:.9;right:-26vw;top:-14vw;width:70vw;height:70vw}.lp-gr{grid-template-columns:repeat(2,1fr)}}
@media(prefers-reduced-motion:reduce){.lp-cop{transition:none}}
"""


def _dim_titolo(t, base=30):
    l = len(t)
    dim = base if l <= 12 else int(base * .8) if l <= 24 else int(base * .64) if l <= 40 else int(base * .52)
    lunga = max((len(w) for w in t.split()), default=1)
    return max(14, min(dim, int(100 / (0.5 * lunga))))


def _cop(href, titolo, sotto):
    c = sum(ord(ch) * (i + 1) for i, ch in enumerate(titolo + sotto)) % 4
    return (f'<a class="lp-cop c{c}" href="{href}"><span class="t" style="font-size:{_dim_titolo(titolo)}px">{esc(titolo)}</span>'
            f'<span class="a">{esc(sotto)}</span></a>\n')


def url_landing(lang, anno):
    return f"{SITO}/en/public-domain-{anno}/" if lang == "en" else f"{SITO}/pubblico-dominio-{anno}/"


def pagina_landing(anno, pacchetto_ue, opere_us, lang="en"):
    """Pagina «Public domain <anno>» / «Pubblico dominio <anno>»: dati e regole già verificati nel sito."""
    oggi = datetime.date.today()
    url = url_landing(lang, anno)
    pub = opere_us["anno_pubblicazione"] if opere_us else anno - 96
    morti = anno - 71
    libero = pacchetto_ue.get("libero_dal") or f"{anno}-01-01"
    it = lang == "it"
    app = "/" if it else "/en/"
    # Nomi più cercati, per il titolo e la descrizione che si vedono su Google: chi cerca vuole sapere QUALI libri.
    _aut = [x for x in pacchetto_ue.get("autori", []) if x.get("letterario") and x.get("morte")]
    _aut.sort(key=lambda x: -((x.get("visite_it") or 0) if it else (x.get("indice_int") or x.get("indice") or 0)))
    _cogn = lambda nome: nome.split()[-1] if nome else ""
    _au = [_cogn(x["nome"]) for x in _aut[:3]]
    _op = []
    for o in (opere_us or {}).get("opere", []):
        chi = _cogn(o["autori"][0]["nome"]) if o.get("autori") else ""
        if chi in _au:  # niente nomi ripetuti (es. Brecht autore e Brecht opera)
            continue
        t = (o.get("titolo_it") or o["titolo"]) if it else o["titolo"]
        _op.append((t, chi))
        if len(_op) == 2:
            break
    _n_us = len((opere_us or {}).get("opere", [])); _n_ue = len(_aut)
    if it:
        titolo = f"Pubblico dominio {anno}: cosa diventa libero il 1° gennaio · Public Domain Radar"
        descr = (f"Le opere (USA) e gli autori (Europa) che entrano in pubblico dominio il 1° gennaio {anno}, dai dati aperti. "
                 f"Due regole spiegate in parole semplici, con le fonti.")
        if len(_au) >= 3 and len(_op) >= 2:
            titolo = f"Pubblico dominio {anno}: {_au[0]}, {_au[1]}, {_op[0][0]} e cosa diventa libero"
            descr = (f"Dal 1° gennaio {anno} in Europa diventano liberi {_au[0]}, {_au[1]}, {_au[2]} e altri {_n_ue - 3} autori; "
                     f"negli USA {_op[0][0]} ({_op[0][1]}), {_op[1][0]} ({_op[1][1]}) e altre {_n_us - 2} opere. Dati aperti, con le fonti.")
        faq = [
            (f"Cosa entra in pubblico dominio nel {anno}?",
             f"Dipende dal paese. Negli USA le opere pubblicate nel {pub} (95 anni dalla pubblicazione, 17 U.S.C. § 304). "
             f"Nell'Unione europea le opere degli autori morti nel {morti} (vita dell'autore + 70 anni, direttiva 2006/116/CE, art. 1)."),
            ("Perché USA ed Europa sono diversi?",
             "Usano regole diverse. Gli USA contano dall'anno in cui l'opera è stata pubblicata, l'Europa dall'anno in cui è morto l'autore. "
             "Così un libro può essere libero in un posto e ancora protetto nell'altro."),
            (f"Posso pubblicare in Italia un libro uscito nel {pub}?",
             f"Non automaticamente. In Italia conta quando è morto l'autore, anche per gli autori americani: la Cassazione ha applicato i 70 anni dalla morte "
             f"a un autore statunitense anche se negli USA l'opera era già libera (caso Zorro). Un libro del {pub} di Virginia Woolf (morta nel 1941) è già libero, "
             f"uno di Dashiell Hammett (morto nel 1961) lo sarà solo dal 2032. Alcuni paesi hanno regole proprie (la Spagna 80 anni per chi è morto prima del 1987): va verificato caso per caso."),
            ("Una traduzione italiana di un'opera libera è libera anche lei?",
             "No. La traduzione ha diritti propri, che durano 70 anni dalla morte del traduttore. Libero è il testo originale: per pubblicarlo in italiano serve una traduzione nuova o una già libera."),
            ("È consulenza legale?",
             "No. Sono informazioni generali costruite da dati aperti e possono contenere errori. Prima di pubblicare controlla la legge e i fatti per il tuo paese e la tua edizione."),
            ("Da dove vengono i dati?",
             "Wikidata (CC0), Wikipedia (testi CC BY-SA, sempre con il link alla pagina) e Wikimedia Commons (ogni immagine con la sua licenza). "
             "Le leggi sono lette sui testi ufficiali. Il sito si aggiorna da solo ogni mese."),
        ]
    else:
        titolo = f"Public Domain {anno}: books and authors that become free on 1 January · Public Domain Radar"
        descr = (f"The works (USA) and authors (Europe) entering the public domain on 1 January {anno}, from open data. "
                 f"Two rules explained in plain words, with sources.")
        if len(_au) >= 3 and len(_op) >= 2:
            titolo = f"Public Domain {anno}: {_op[0][0]}, {_op[1][0]}, {_au[0]}, {_au[1]} and more"
            descr = (f"Free on 1 January {anno}: {_op[0][0]} ({_op[0][1]}), {_op[1][0]} ({_op[1][1]}) and {_n_us - 2} more US books; "
                     f"{_au[0]}, {_au[1]}, {_au[2]} and {_n_ue - 3} more authors in Europe and the UK. Open data, with sources.")
        faq = [
            (f"What enters the public domain in {anno}?",
             f"It depends on the country. In the USA, works published in {pub} (95 years after publication, 17 U.S.C. § 304). "
             f"In the European Union, the works of authors who died in {morti} (author's life + 70 years, Directive 2006/116/EC, Art. 1)."),
            ("Why are the USA and Europe different?",
             "They use different rules. The USA counts from the year a work was published. Europe counts from the year the author died. "
             "So a book can be free in one place and still protected in the other."),
            (f"Can I publish a book from {pub} in Europe or the UK?",
             f"Not automatically. In Europe what matters is when the author died: a book from {pub} by Virginia Woolf (died 1941) is already free, while one by "
             f"Dashiell Hammett (died 1961) is protected until 2031 under the 70-year rule. The EU directive lets protection end earlier for non-EU works (Art. 7), "
             f"but countries apply it differently: in Italy the Court of Cassation applied 70 years even to a US author. The UK applies the shorter term of the "
             f"country of origin (section 12(6)), unless the book was also published in the UK at the same time, as many American novels were. "
             f"Some countries have their own rules (Spain gives 80 years to authors who died before 1987): check case by case."),
            (f"Is every work published in {pub} really free in the USA?",
             "Not always. Works first published in the USA whose copyright was not renewed after 28 years were already free earlier. Foreign works that regained protection in 1996 (17 U.S.C. § 104A) "
             "last 95 years from publication, but only if they were still protected in their country of origin and the author was from a member country. "
             "Our list shows works that probably become free; it is not a legal clearance."),
            ("Is this legal advice?",
             "No. It is general information built from open data, and it may contain errors. Before publishing, check the law and the facts for your country and your edition."),
            ("Where does the data come from?",
             "Wikidata (CC0), Wikipedia (text CC BY-SA, always linked to the page) and Wikimedia Commons (each image with its own licence). "
             "The laws are read from the official texts. The site updates itself every month."),
        ]
    jl = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "@id": url, "url": url, "name": titolo, "description": descr, "inLanguage": lang,
         "dateModified": str(oggi), "isPartOf": {"@type": "WebSite", "name": "Public Domain Radar", "url": SITO + app}},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q,
                                             "acceptedAnswer": {"@type": "Answer", "text": r}} for q, r in faq]}]}
    jsonld = '<script type="application/ld+json">' + json.dumps(jl, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    alt = (f'<link rel="alternate" hreflang="it" href="{url_landing("it", anno)}">\n'
           f'<link rel="alternate" hreflang="en" href="{url_landing("en", anno)}">\n')
    altra = (f'<a href="/en/public-domain-{anno}/">English</a>' if it else f'<a href="/pubblico-dominio-{anno}/">Italiano</a>')
    out = [TESTA.format(lang=lang, titolo=esc(titolo), descr=esc(descr), url=url, alterne=alt, og_tipo="website", jsonld=jsonld,
                        css=CSS + CSS_LANDING, home=app, altra_lingua=altra)]
    T = (lambda a, b: a) if it else (lambda a, b: b)
    out.append(f"""<header class="lp-hero"><div class="lp-in">
<p class="lp-occ"><i></i>{T("Public Domain Day · 1° gennaio", "Public Domain Day · 1 January")} {anno}</p>
<h1>{T("Cosa diventa libero nel", "What becomes free in")} <em>{anno}</em></h1>
<p class="lead">{T(f"Le opere e gli autori che entrano in pubblico dominio il 1° gennaio {anno}, negli USA e in Europa. Dati aperti, spiegati in parole semplici, aggiornati ogni mese.", f"The works and authors that enter the public domain on 1 January {anno}, in the USA and in Europe. Open data, explained in plain words, updated every month.")}</p>
<div class="lp-cont" id="cont"><b id="giorni">{anno}</b><span id="giorni-et">{T("1° gennaio", "1 January")}</span></div>
<div class="lp-bott"><a class="lp-b lp-b1" href="{app}#/us/{anno}">{T("Le opere (USA)", "See the works (USA)")}</a><a class="lp-b lp-b2" href="{app}#/{anno}">{T("Gli autori (Europa)", "See the authors (Europe)")}</a></div>
</div></header>
""")
    out.append(f"""<section class="lp-sez"><div class="lp-in">
<p class="lp-occh">{T("Due regole, due elenchi", "Two rules, two lists")}</p>
<h2>{T("Dipende da dove pubblichi", "It depends where you publish")}</h2>
<p class="lead">{T("Gli USA guardano quando è uscita l'opera. L'Europa guarda quando è morto l'autore. Per questo gli elenchi sono due.", "The USA looks at when a work was published. Europe looks at when the author died. That is why there are two lists.")}</p>
<div class="lp-due">
<div class="lp-card us"><div class="lp-num">95</div><h3>{T("USA · opere", "USA · works")}</h3><p class="gr">{T("Anni dalla pubblicazione", "Years after publication")}</p>
<p>{T(f"Le opere pubblicate nel <b>{pub}</b> ancora protette diventano libere il 1° gennaio {anno}. Regola: 17 U.S.C. § 304.", f"Works published in <b>{pub}</b> that were still protected become free on 1 January {anno}. Rule: 17 U.S.C. § 304.")}</p><a href="{app}#/us/{anno}">{T("Sfoglia le opere →", "Browse the works →")}</a></div>
<div class="lp-card"><div class="lp-num">70</div><h3>{T("Europa e Regno Unito · autori", "Europe and UK · authors")}</h3><p class="gr">{T("Anni dalla morte dell'autore", "Years after the author's death")}</p>
<p>{T(f"Gli autori morti nel <b>{morti}</b> diventano liberi il 1° gennaio {anno}. Alcuni paesi hanno regole proprie: ogni scheda autore mostra la data paese per paese.", f"Authors who died in <b>{morti}</b> become free on 1 January {anno}. Some countries have their own rules, so each author page shows the date country by country.")}</p><a href="{app}#/{anno}">{T("Sfoglia gli autori →", "Browse the authors →")}</a></div>
</div></div></section>
""")
    if opere_us and opere_us.get("opere"):
        out.append(f'<section class="lp-sez" style="padding-top:0"><div class="lp-in">\n<p class="lp-occh">{T("USA · pubblicate nel", "USA · published in")} {pub}</p>\n'
                   f'<h2>{T(f"Le opere più lette che si liberano nel {anno}", f"The most read works entering in {anno}")}</h2>\n'
                   f'<p class="lead">{T("In ordine di quanto se ne legge su Wikipedia in inglese.", "Ranked by how much people read about them on English Wikipedia.")}</p>\n<div class="lp-gr">\n')
        for o in opere_us["opere"][:12]:
            aut = ", ".join(a["nome"] for a in o.get("autori", [])) or "—"
            out.append(_cop(f"{app}#/opera/{o['qid']}", o["titolo"], f"{aut} · {pub}"))
        out.append(f'</div>\n<p class="lp-piu"><a href="{app}#/us/{anno}">{T("Tutte le", "All")} {len(opere_us["opere"])} {T("opere", "works")} →</a></p>\n</div></section>\n')
    aut = [a for a in pacchetto_ue.get("autori", []) if a.get("letterario") and a.get("morte")]
    aut.sort(key=lambda a: -((a.get("visite_it") or 0) if it else (a.get("indice_int") or a.get("indice") or 0)))
    if aut:
        out.append(f'<section class="lp-sez lp-scuro"><div class="lp-in">\n<p class="lp-occh">{T("Europa · morti nel", "Europe · died in")} {morti}</p>\n'
                   f'<h2>{T(f"Gli autori che entrano nel {anno}", f"The authors entering in {anno}")}</h2>\n<p class="lead">{T(f"Scrittori morti nel {morti}, in ordine di interesse in Italia.", f"Writers who died in {morti}, ranked by international interest.")}</p>\n<div class="lp-aut">\n')
        for a in aut[:12]:
            pag = a.get("pagina") if it else a.get("pagina_en")
            href = (f"/autore/{pag}/" if it else f"/en/author/{pag}/") if pag else f"{app}#/autore/{a['wikidata']}"
            anni = f"{anno_di(a.get('nascita')) or '?'} – {anno_di(a['morte'])}"
            out.append(f'<a href="{href}"><b>{esc(pulisci(a["nome"]))}</b><span>{esc(anni)}</span></a>\n')
        out.append(f'</div>\n<p class="lp-piu"><a href="{app}#/{anno}" style="color:#fff">{T("Tutti gli autori →", "All authors →")}</a></p>\n</div></section>\n')
    out.append(f"""<section class="lp-sez"><div class="lp-in">
<p class="lp-occh">{T("Come funziona", "How it works")}</p>
<h2>{T("Dati aperti, niente a occhio", "Open data, no guesswork")}</h2>
<div class="lp-pass">
<div><b>01</b><h3>{T("Letto da fonti aperte", "Read from open sources")}</h3><p>{T("Autori e opere vengono da Wikidata, l'interesse dalle visite a Wikipedia. Niente è scritto a mano.", "Authors and works come from Wikidata, interest from Wikipedia page views. Nothing is typed by hand.")}</p></div>
<div><b>02</b><h3>{T("Regole dalla legge", "Rules from the law")}</h3><p>{T("Le regole sulla durata sono lette sui testi di legge ufficiali. Quello che non abbiamo potuto verificare è dichiarato nel sito.", "The term rules are read from the official legal texts. What we could not verify is declared on the site.")}</p></div>
<div><b>03</b><h3>{T("Si aggiorna da solo", "Updated by itself")}</h3><p>{T("Ogni mese l'elenco viene ricostruito da capo. Vedi sempre la data dell'ultimo aggiornamento.", "Every month the whole list is rebuilt. You always see the last update date.")}</p></div>
</div></div></section>
""")
    out.append(f'<section class="lp-sez" style="padding-top:0"><div class="lp-in">\n<p class="lp-occh">{T("Domande", "Questions")}</p>\n<h2>{T("Il pubblico dominio, in parole semplici", "Public domain, in plain words")}</h2>\n<div class="lp-faq">\n')
    for q, r in faq:
        out.append(f"<details><summary>{esc(q)}</summary><p>{esc(r)}</p></details>\n")
    out.append(f'</div>\n<p class="lp-nota">{T("Informazioni generali, non consulenza legale. I dati vengono da fonti aperte e possono contenere errori: prima di pubblicare controlla la legge del tuo paese.", "General information, not legal advice. The data comes from open sources and may contain errors: before publishing, check the law for your country.")}</p>\n</div></section>\n')
    giorni_et = ('d===1?"giorno":"giorni"', '"Libero"', f'"dal 1° gennaio {anno}"') if it else ('d===1?"day to go":"days to go"', '"Free"', f'"since 1 January {anno}"')
    out.append(f"""<section class="lp-fin"><div class="lp-in">
<h2>{T("Stai scegliendo cosa ripubblicare?", "Choosing what to republish?")}</h2>
<p>{T("Pensato per editori, traduttori e agenti: chi diventa libero, quanto è letto e la data paese per paese.", "Built for editors, translators and agents: see who becomes free, how much they are read, and the date country by country.")}</p>
<a class="lp-b" href="{app}">{T("Apri lo strumento completo", "Open the full tool")}</a>
</div></section>
<script>(function(){{var t=new Date("{libero}T00:00:00"),d=Math.ceil((t-new Date())/864e5),b=document.getElementById("giorni"),l=document.getElementById("giorni-et");if(!b||!l)return;if(d>0){{b.textContent=d;l.textContent={giorni_et[0]}}}else{{b.textContent={giorni_et[1]};l.textContent={giorni_et[2]}}}}})();</script>
""")
    out.append(PIEDE[lang])
    return "".join(out), url


def crea_landing():
    """Per ogni anno disponibile: en/public-domain-<anno>/ e pubblico-dominio-<anno>/. Restituisce gli indirizzi."""
    urls = []
    for f in sorted(glob.glob(str(RADICE / "data" / "[0-9][0-9][0-9][0-9].json"))):
        anno = int(Path(f).stem)
        ue = json.load(open(f, encoding="utf-8"))
        fus = RADICE / "data" / f"us-{anno}.json"
        us = json.load(open(fus, encoding="utf-8")) if fus.exists() else None
        for lang, d in (("en", RADICE / "en" / f"public-domain-{anno}"), ("it", RADICE / f"pubblico-dominio-{anno}")):
            html_, url = pagina_landing(anno, ue, us, lang)
            d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text(html_, encoding="utf-8")
            urls.append(url)
    return urls


def main():
    oggi = datetime.date.today()
    autori = {}
    for f in file_autori():
        for a in json.load(open(f, encoding="utf-8"))["autori"]:
            if abbastanza_contenuto(a):
                autori.setdefault(a["wikidata"], a)
    scelti = sorted(autori.values(), key=lambda a: (slug_base(a["nome"]), a["wikidata"]))
    usati = {}
    for a in scelti:
        usati.setdefault(slug_base(a["nome"]) or a["wikidata"].lower(), []).append(a)
    slug_di = {}
    for s_, gruppo in usati.items():
        for a_ in gruppo:
            slug_di[a_["wikidata"]] = s_ if len(gruppo) == 1 else f"{s_}-{a_['wikidata'].lower()}"
    en_ok = {q for q, a in autori.items() if abbastanza_contenuto(a, "en")}
    for f in file_autori():
        calcola_ranghi(json.load(open(f, encoding="utf-8")))

    for l in ("it", "en"):
        cartella = RADICE / PERCORSO[l]
        if cartella.exists():
            shutil.rmtree(cartella)
        cartella.mkdir(parents=True)
    voci = {"it": [], "en": []}
    urls = []
    for q, a in autori.items():
        slug = slug_di[q]
        for l in ("it", "en"):
            if l == "en" and q not in en_ok:
                continue
            d = RADICE / PERCORSO[l] / slug
            d.mkdir()
            (d / "index.html").write_text(pagina_autore(a, slug, l, ha_altra=(q in en_ok)), encoding="utf-8")
            voci[l].append((pulisci(a["nome"]), slug, f"{anno_di(a.get('nascita')) or '?'} – {anno_di(a['morte'])}"))
            urls.append(url_pagina(l, slug))
    for l in ("it", "en"):
        voci[l].sort(key=lambda v: (slug_base(v[0]), v[1]))
        (RADICE / PERCORSO[l] / "index.html").write_text(pagina_indice(voci[l], l), encoding="utf-8")

    # il sito usa il nome nell'indirizzo della scheda e linka la pagina dedicata: serve sapere quale autore ne ha una
    for f in file_autori():
        pacchetto = json.load(open(f, encoding="utf-8"))
        for a_ in pacchetto["autori"]:
            q = a_["wikidata"]
            if q in slug_di:
                a_["pagina"] = slug_di[q]
            else:
                a_.pop("pagina", None)
            if q in en_ok:
                a_["pagina_en"] = slug_di[q]
            else:
                a_.pop("pagina_en", None)
        Path(f).write_text(json.dumps(pacchetto, ensure_ascii=False, indent=1), encoding="utf-8")

    aggiorna_home_italiana()
    crea_home_inglese()
    landing_urls = crea_landing()
    if CALENDARIO_ON:
        import calendario
        landing_urls += calendario.crea_calendario()
    righe = [f"  <url><loc>{SITO}/</loc><lastmod>{oggi}</lastmod><changefreq>monthly</changefreq></url>",
             f"  <url><loc>{SITO}/en/</loc><lastmod>{oggi}</lastmod><changefreq>monthly</changefreq></url>",
             f"  <url><loc>{url_pagina('it')}</loc><lastmod>{oggi}</lastmod><changefreq>monthly</changefreq></url>",
             f"  <url><loc>{url_pagina('en')}</loc><lastmod>{oggi}</lastmod><changefreq>monthly</changefreq></url>"]
    righe += [f"  <url><loc>{u}</loc><lastmod>{oggi}</lastmod><changefreq>weekly</changefreq></url>" for u in landing_urls]
    righe += [f"  <url><loc>{u}</loc><lastmod>{oggi}</lastmod></url>" for u in sorted(urls)]
    (RADICE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(righe) + "\n</urlset>\n", encoding="utf-8")
    print(f"Pagine create: {len(voci['it'])} in italiano, {len(voci['en'])} in inglese (su {len(autori)} autori con biografia e opere)")


if __name__ == "__main__":
    sys.exit(main())
