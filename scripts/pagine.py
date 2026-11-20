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
            f"EU (base rule), Germany and the United Kingdom: from {d(D + 71)}. In the UK, works still unpublished in 1989 stay protected until 31 December 2039.",
            f"France: from {d(D + 71)}. Wartime extensions are not added to the 70 years (French Court of Cassation, 2007). Exception: authors who «died for France» get 30 more years.",
            f"Italy: from {d(D + 71)}. The 6-year wartime extension was repealed in 1996. For authors from Allied countries in the Second World War the term can be longer (1947 Peace Treaty): check case by case.",
            (f"Spain: not before {d(D + 81)} (80 years after death, because the author died before 1987; the law does not say how the year is counted)."
             if D < 1987 else f"Spain: from {d(D + 71)}."),
        ]
    return [
        f"UE (base), Germania e Regno Unito: dal {d(D + 71)}. Nel Regno Unito le opere rimaste inedite fino al 1989 restano protette fino al 31 dicembre 2039.",
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
.usa .us{flex:none;font-family:var(--mono);font-size:12px;padding:2px 8px;border:1px solid #CFCCC2;color:var(--muto);white-space:nowrap}
.usa .us.ok{background:#0E3B2E;border-color:#0E3B2E;color:var(--carta)}.usa .us.ver{background:#F2B705;border-color:#F2B705;color:var(--ink)}
.faq details{border-top:1px solid #D9D6CC;padding:12px 0}.faq summary{cursor:pointer;font-weight:600;font-size:17px}.faq p{margin:8px 0 0;font-size:16px}
.pg{list-style:none;margin:16px 0 0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px}
.pg li{margin:0;background:var(--riquadro);padding:12px 14px;display:flex;flex-direction:column;gap:2px}
.pg .p{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muto)}
.pg .d{font-family:var(--display);font-weight:900;font-size:24px;line-height:1;text-transform:uppercase}
.pg .r{font-size:13px;line-height:1.35;color:var(--muto)}
.pg .ok{background:#0E3B2E;color:var(--carta)}.pg .ok .p,.pg .ok .r{color:#C9D6CF}
.cat{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px}
.cat li{margin:0;display:grid;grid-template-columns:minmax(0,190px) 1fr auto;gap:12px;align-items:center;font-size:15px}
.cat .b{height:10px;background:var(--riquadro)}.cat .b i{display:block;height:10px;background:var(--ink)}
.cat .n{font-family:var(--mono);font-size:13px;white-space:nowrap}
/* scheda autore come nel mockup del 19/11/2026: testata scura larga, risposta in rosso, paesi in riquadri, sezioni con titoli grandi */
main:has(.sa){max-width:none;padding:0 0 72px}
.sa-in{max-width:1180px;margin:0 auto;padding:0 clamp(20px,4vw,48px)}
.sa-top{background:var(--ink);color:var(--carta);padding:28px 0 48px}
.sa-top .sa-et{padding:0;color:var(--vermiglio)}
.sa-top .sa-head{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:32px;align-items:end;padding:14px 0 0}
.sa-top .sa-head>div:not(.sa-foto){order:1}.sa-top .sa-foto{order:2;width:200px;height:240px;background:var(--notte)}
.sa-top .sa-ini{color:#3A3A46;font-size:96px;align-items:center;justify-content:center}
.sa-top h1{font-size:clamp(56px,9vw,120px);line-height:.86;color:var(--carta);overflow-wrap:anywhere;min-width:0}
.sa-top .sa-desc{color:#B9B9C6;font-size:17px}
.sa-top .sa-credito{padding:8px 0 0;text-align:right;color:#8A8A96}.sa-top .sa-credito a{color:#A9A9B6}
.sa-top .sa-libero{padding:28px 0 0}
.sa-top .libero-blocco{padding:26px 30px}.sa-top .lb-data{font-size:clamp(48px,7vw,88px);line-height:.9}
.sa-top .lb-ver,.sa-top .sa-nota{color:#B9B9C6}.sa-top .lb-ver svg{color:var(--carta)}.sa-top a{color:var(--carta)}
.sa-top .pg{grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px}
.sa-top .pg li{background:var(--riquadro);color:var(--ink);min-height:140px;padding:16px 18px 18px;gap:6px}
.sa-top .pg .p{color:var(--ink)}.sa-top .pg .d{font-size:30px}.sa-top .pg .r{margin-top:auto;color:var(--ink)}
.sa-top .pg .primo{background:var(--vermiglio)}
.sa-top .pg .usa,.sa-top .pg .ok{background:#0E3B2E;color:var(--carta)}.sa-top .pg .usa .p,.sa-top .pg .usa .r,.sa-top .pg .ok .p,.sa-top .pg .ok .r{color:var(--carta)}
.sa-resto .sa-sez{padding:56px 0 0;border-top:0}
.sa-resto .sa-sez>*{max-width:900px}
.sa-occ{margin:0;font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--vermiglio-testo)}
.sa-resto .sa-sez h2{font-family:var(--display);font-weight:900;font-size:clamp(36px,5vw,60px);line-height:.92;text-transform:uppercase;letter-spacing:0;color:var(--ink);margin:8px 0 18px;border:0;padding:0}
main:has(.sa) .sa-azioni{max-width:1180px;margin:40px auto 0;padding:0 clamp(20px,4vw,48px)}
@media (max-width:640px){.sa-top .sa-head{grid-template-columns:1fr}.sa-top .sa-foto{order:0;width:120px;height:144px}.sa-top .sa-credito{text-align:left}.sa-top .pg{grid-template-columns:1fr 1fr}}
@media (max-width:560px){.cat li{grid-template-columns:1fr auto}.cat .b{grid-column:1/-1;order:3}}
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
<link href="/assets/fonts/fonts.css" rel="stylesheet">
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
<p>Fonti: Wikidata (CC0), Wikipedia (testi CC BY-SA, con link alla pagina d'origine), Wikimedia Commons (ritratti, ciascuno con la sua licenza), cataloghi nazionali (SBN, BnF, BNE, British Library e Library of Congress). Dati aperti, aggiornati in automatico ogni tre mesi e a dicembre; possono contenere errori.</p>
<p>Le date sono un calcolo indicativo dalle norme elencate nel <a href="/#regole-paesi">riquadro delle regole</a>. Non è consulenza legale: prima di pubblicare va controllato nella legge del paese.</p>
<p>Chi usa questi dati lo fa sotto la propria responsabilità. Le date sono indicative e riguardano le opere originali: traduzioni, illustrazioni ed edizioni recenti hanno diritti propri. Per un'edizione commerciale chiedi un parere a un esperto di diritto d'autore. <a href="https://github.com/mnovali90-byte/publicdomain/issues">Hai trovato un errore? Segnalalo</a>.</p>
<p><a href="/">Tutti gli autori</a> · <a href="/pubblico-dominio-@@ANNO@@/">Pubblico dominio @@ANNO@@</a> · <a href="/autore/">Indice degli autori</a> · <a href="https://github.com/mnovali90-byte/publicdomain">Codice e dati su GitHub</a></p>
</footer>
</body>
</html>
""",
    "en": """<footer>
<p>A project by Marco Novali · <a href="https://www.linkedin.com/in/marconovali" rel="me noopener" target="_blank">LinkedIn</a></p>
<p>Sources: Wikidata (CC0), Wikipedia (text CC BY-SA, linked to the original page), Wikimedia Commons (portraits, each with its own licence), national catalogues (SBN, BnF, BNE, British Library and Library of Congress). Open data, updated automatically every three months and in December; it may contain errors.</p>
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
        _cal = ANNO_PROSSIMO
    PIEDE["it"] = PIEDE["it"].replace('<a href="/autore/">', f'<a href="/calendario/{_cal}/">Calendario anniversari</a> · <a href="/autore/">', 1)
    PIEDE["en"] = PIEDE["en"].replace('<a href="/en/author/">', f'<a href="/en/calendar/{_cal}/">Anniversaries calendar</a> · <a href="/en/author/">', 1)


# Autori tolti da classifiche e vetrine per decisione di Marco (la scheda resta): data/fuori_classifica.json
try:
    FUORI_CLASSIFICA = {x["wikidata"] for x in json.loads((RADICE / "data" / "fuori_classifica.json").read_text(encoding="utf-8"))["autori"]}
except Exception:
    FUORI_CLASSIFICA = set()


def url_pagina(lang, slug=""):
    return f"{SITO}/{PERCORSO[lang]}/{slug + '/' if slug else ''}"


def alterne(lang, slug):
    """Collegamenti tra la pagina italiana e quella inglese (hreflang). Solo se esistono tutte e due."""
    if slug is None:
        return ""
    return (f'<link rel="alternate" hreflang="it" href="{url_pagina("it", slug)}">\n'
            f'<link rel="alternate" hreflang="en" href="{url_pagina("en", slug)}">\n')


NOMI_FONTE = {"it": {"wikidata": "Wikidata", "wikidata_altra": "Wikidata (altra data)", "gnd": "Biblioteca nazionale tedesca (GND)", "loc": "Library of Congress"},
              "en": {"wikidata": "Wikidata", "wikidata_altra": "Wikidata (another date)", "gnd": "German National Library (GND)", "loc": "Library of Congress"}}

# Potenze alleate e associate del Trattato di pace con l'Italia del 1947 (preambolo; Albania per adesione), con i nomi
# che Wikidata dà alla cittadinanza: stessa lista di ALLEATI_1947 in index.html (lì con i nomi attuali). È un indizio.
ALLEATI_1947 = {"Regno Unito", "Regno Unito di Gran Bretagna e Irlanda", "Regno d'Inghilterra", "Galles", "Stati Uniti",
                "Unione Sovietica", "Impero russo", "Repubblica Socialista Federativa Sovietica Russa", "Russia sovietica", "RSS Ucraina",
                "RSS Bielorussa", "Repubblica Socialista Sovietica Georgiana", "Kazakistan", "Cina", "Repubblica di Cina", "Francia",
                "Australia", "Belgio", "Brasile", "Canada", "Cecoslovacchia", "Prima Repubblica cecoslovacca", "Repubblica Socialista Cecoslovacca",
                "Grecia", "India", "Impero anglo-indiano", "Dominion dell'India", "Pakistan", "Regno dei Paesi Bassi", "Nuova Zelanda",
                "Polonia", "Seconda Repubblica di Polonia", "Repubblica Popolare di Polonia", "Sudafrica", "Jugoslavia", "Regno di Jugoslavia",
                "Repubblica federale popolare di Jugoslavia", "Repubblica Socialista Federale di Jugoslavia", "Regno dei Serbi, Croati e Sloveni",
                "Serbia", "Albania"}


def avviso_alleato(a, lang):
    p = [x for x in a.get("paesi", []) if x in ALLEATI_1947]
    if not p:
        return ""
    t = (f"Autore di un paese alleato nella Seconda guerra mondiale ({', '.join(p)}): in Italia la protezione può durare di più "
         "(Trattato di pace del 1947, allegato XV). La data qui sopra non ne tiene conto: va verificata caso per caso." if lang == "it" else
         f"Author from an Allied country in the Second World War ({', '.join(p)}): in Italy protection may last longer "
         "(1947 Peace Treaty, Annex XV). The date above does not take this into account: check case by case.")
    return f'<p><strong>{esc(t)}</strong></p>\n'


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
    if v["esito"] in ("maggioranza", "corretto"):
        au = v.get("autorevoli") or {}
        fa = ", ".join(au.get("fonti", []))
        if v["esito"] == "maggioranza":
            t = (f"Anno di morte {au.get('morte')} confermato da {len(au.get('fonti', []))} fonti autorevoli ({fa}). Altre fonti danno un anno diverso: vale quello su cui concordano le fonti autorevoli." if it
                 else f"Year of death {au.get('morte')} confirmed by {len(au.get('fonti', []))} authoritative sources ({fa}). Other sources give a different year: the one the authoritative sources agree on applies.")
        else:
            t = (f"Anno di morte {au.get('morte')} secondo {len(au.get('fonti', []))} fonti autorevoli ({fa}). Wikidata dice {fv.get('wikidata')}: vale quello delle fonti autorevoli." if it
                 else f"Year of death {au.get('morte')} according to {len(au.get('fonti', []))} authoritative sources ({fa}). Wikidata says {fv.get('wikidata')}: the authoritative sources apply.")
        return [f'<p class="sotto">{esc(t)}</p>\n']
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
    lett = [x for x in pacchetto["autori"] if x.get("letterario") and not re.fullmatch(r"Q\d+", x["nome"])]
    for m, campo in (("it", "visite_it"), ("en", "visite_en"), ("int", "pagine_wikipedia")):
        ordine = sorted(lett, key=lambda x: (-(x.get("indice_" + m) if x.get("indice_" + m) is not None else -1), -(x.get(campo) or 0),
                                             -(x.get("pagine_wikipedia") or 0), x["nome"]))
        for r, x in enumerate(ordine, 1):
            RANGHI.setdefault((x["wikidata"], m), (r, len(ordine)))


def iniziali_nome(nome):
    p = [w for w in re.split(r"[\s().,]+", nome) if w]
    return ((p[0][:1] + p[-1][:1]) if len(p) > 1 else (p[0][:2] if p else "?")).upper()


# Anni delle opere verificati con il metodo di docs/metodo-anni-opere.md (seconda fonte: Duke, Open Library, Library of Congress)
def _leggi(p, x):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return x


from registro import anni_usa, liste_usa  # noqa: E402
ANNI_VER = anni_usa()   # registro unico: anno USA confermato di ogni opera (regola in scripts/regole.py)
_PER_AUT = {}


def _parole(t):
    return re.findall(r"[a-z0-9]+", unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower())


def opere_storico(qid):
    """Le opere dell'autore nello Storico (per collegare un titolo al suo codice Wikidata)."""
    try:
        k = f"{int(qid[1:]) % 100:02d}"
    except ValueError:
        return []
    if k not in _PER_AUT:
        _PER_AUT[k] = _leggi(RADICE / "data" / "storico" / "per_autore" / f"{k}.json", {})
    return _PER_AUT[k].get(qid, [])


def stato_usa(a, o):
    """Stato negli USA di un'opera principale: ('libero', anno) solo con anno confermato da una seconda fonte."""
    y = o.get("anno")
    if not isinstance(y, int):
        return "nd", None
    limite = datetime.date.today().year - 96
    if y > limite:
        return "dal", y + 96
    tw = {tuple(_parole(o.get("titolo"))), tuple(_parole(o.get("titolo_en")))}
    for r in opere_storico(a["wikidata"]):
        if tuple(_parole(r[1])) in tw or tuple(_parole(r[2])) in tw:
            v = ANNI_VER.get(r[0])
            if v and v[0] is not None:
                # confermata un'edizione entro il limite: libera dall'anno di uscita dell'opera; solo edizioni più tarde: dal loro anno
                return ("libero", y + 96) if v[0] <= limite else ("dal", v[0] + 96)
    return "verifica", None


from regole import autori_che_contano  # noqa: E402
COAUT = _leggi(RADICE / "data" / "storico" / "coautori.json", {})
COAUT_MAN = _leggi(RADICE / "data" / "coautori_manuali.json", {}).get("opere", {})


def note_coautori(a, lang):
    """Regola dei coautori (20/11/2026, storico/coautori.py): per le «Opere principali» della scheda, i coautori morti
    dopo l'autore (la data europea dell'opera è la loro), quelli senza data di morte (da verificare) e la musica o il
    libretto ancora protetti. Gruppi ed enti senza membri noti non contano; un gruppo con membri vale per i membri."""
    it = lang == "it"
    T = (lambda x, y: x) if it else (lambda x, y: y)
    D = anno_di(a.get("morte"))
    oggi_a = datetime.date.today().year
    mie = (COAUT.get("per_autore") or {}).get(a["wikidata"], {})
    tipi = COAUT.get("autori") or {}
    note = []
    for o in a.get("opere", [])[:10]:
        t = o.get("titolo") if it else o.get("titolo_en") or o.get("titolo")
        if not t or not D:
            continue
        chiavi = {tuple(_parole(o.get("titolo"))), tuple(_parole(o.get("titolo_en")))} - {()}
        wq = next((q for q, w in mie.items() if {tuple(_parole(w.get("t"))), tuple(_parole(w.get("ti")))} & chiavi), None)
        if not wq:
            wq = next((r[0] for r in opere_storico(a["wikidata"]) if {tuple(_parole(r[1])), tuple(_parole(r[2]))} & chiavi), None)
        w = mie.get(wq) or {}
        co = [list(c) for c in w.get("co", [])]
        for x in COAUT_MAN.get(wq, []):
            co.append([x.get("qid") or "", x["nome"], x.get("morte"), None])
        # regola dei coautori: la stessa di tutto il sito (scripts/regole.py, autori_che_contano)
        au = [{"qid": a["wikidata"], "nome": a["nome"], "morte": D}] + [
            {"qid": c[0] or "man:" + c[1], "nome": c[1], "morte": c[2], "nascita": c[3] if len(c) > 3 else None} for c in co]
        dopo = [x for x in autori_che_contano(au, tipi, oggi_a) if x["qid"] != a["wikidata"]]
        tardi = [(x["nome"], x["morte"]) for x in dopo if x.get("morte") is not None and not x.get("antico") and x["morte"] > D]
        ignoti = [x["nome"] or T("un autore sconosciuto", "an unknown author") for x in dopo if x.get("senza_data")]
        tt = f"«{t}»"
        if tardi:
            nome, m = max(tardi, key=lambda x: x[1])
            es = m + 81 if m < 1987 else m + 71
            note.append(T(f"{tt} è scritta anche da {nome} (morte: {m}): in Europa è libera dal 1° gennaio {m + 71} (in Spagna dal {es}).",
                          f"{tt} was also written by {nome}, who died in {m}: in Europe it is free from 1 January {m + 71} (in Spain from {es})."))
        elif ignoti:
            note.append(T(f"{tt}: tra gli autori c'è anche {', '.join(ignoti)}, di cui Wikidata non dà l'anno di morte. Da verificare.",
                          f"{tt}: the authors also include {', '.join(ignoti)}, whose year of death Wikidata does not give. To be checked."))
        for ruolo, nome, m in w.get("mu", []):
            if not nome:
                continue
            r = {"compositore": T("La musica", "The music"), "librettista": T("Il libretto", "The libretto")}.get(ruolo, ruolo)
            if m is None:
                note.append(T(f"{tt}: {r.lower()} di {nome} ha diritti propri; non sappiamo quando scadono.",
                              f"{tt}: {r.lower()} by {nome} has its own rights; we do not know when they expire."))
            elif m + 71 > oggi_a and m > D:
                note.append(T(f"{tt}: {r.lower()} di {nome} (morte: {m}) ha diritti propri, in Europa fino al 31 dicembre {m + 70}. Il testo segue la data dell'autore.",
                              f"{tt}: {r.lower()} by {nome} (died {m}) has its own rights, in Europe until 31 December {m + 70}. The text follows the author's date."))
    return list(dict.fromkeys(note))   # stessa nota per titoli doppi su Wikidata: una volta sola


def opere_usa(a, lang):
    """Sezione «Negli USA, opera per opera»: solo dati, con il metodo di verifica degli anni."""
    it = lang == "it"
    righe, liberi = [], []
    for o in a.get("opere", [])[:10]:
        t = o.get("titolo") if it else o.get("titolo_en") or o.get("titolo")
        if not t:
            continue
        st, y = stato_usa(a, o)
        if st == "libero":
            et, cl = (f"libero dal {y}" if it else f"free since {y}"), "ok"
            liberi.append(t)
        elif st == "dal":
            et, cl = (f"dal {y}" if it else f"from {y}"), ""
        elif st == "verifica":
            et, cl = ("da verificare" if it else "to be checked"), "ver"
        else:
            et, cl = ("anno non noto" if it else "year unknown"), ""
        anno = o.get("anno") if isinstance(o.get("anno"), int) else ""
        righe.append(f'<li><span>{esc(t)}<span class="anno"> {anno}</span></span><span class="us {cl}">{esc(et)}</span></li>\n')
    if not righe:
        return "", []
    nota = ("Negli USA conta l'anno di uscita di ogni opera (95 anni). «Libero» solo se l'anno di Wikidata è confermato da una "
            "seconda fonte (Duke, Open Library, Library of Congress); altrimenti «da verificare». Le date future usano l'anno di Wikidata."
            if it else
            "In the USA what counts is each work's year of publication (95 years). «Free» only when the Wikidata year is confirmed by a "
            "second source (Duke, Open Library, Library of Congress); otherwise «to be checked». Future dates use the Wikidata year.")
    co = "".join(f'<p class="sa-nota">{esc(x)}</p>\n' for x in note_coautori(a, lang))
    return f'<ul class="sa-opere usa">\n{"".join(righe)}</ul>\n<p class="sa-nota">{esc(nota)}</p>\n{co}', liberi


CATALOGHI = [("sbn_it", "Italia · SBN", "Italy · SBN"), ("bnf_fr", "Francia · BnF", "France · BnF"), ("bne_es", "Spagna · BNE", "Spain · BNE"),
             ("bl_en", "Regno Unito · British Library", "United Kingdom · British Library"), ("loc_en", "USA · Library of Congress", "USA · Library of Congress")]


def catalogi_a_confronto(a, lang):
    """Le registrazioni dell'autore nei cinque cataloghi nazionali, a confronto (stessi controlli del blocco principale)."""
    it = lang == "it"
    tr = a.get("traduzioni") or {}
    righe = []
    for k, n_it, n_en in CATALOGHI:
        g = tr.get(k)
        if not g or not g.get("trovato") or g.get("sospeso_manuale") or g.get("stato") == "da_verificare":
            continue
        if problemi_conteggio(g, datetime.date.today().year):
            continue
        righe.append((n_it if it else n_en, g.get("edizioni", 0), g.get("dal_2000", 0)))
    if len(righe) < 2:
        return ""
    mx = max(x[1] for x in righe) or 1
    li = "".join(f'<li><span>{esc(n)}</span><span class="b"><i style="width:{round(e / mx * 100)}%"></i></span>'
                 f'<span class="n">{migliaia(e, lang)} · {migliaia(d, lang)} {"dal 2000" if it else "since 2000"}</span></li>' for n, e, d in sorted(righe, key=lambda x: -x[1]))
    nota = ("Registrazioni collegate all'autore in ogni catalogo: ogni edizione o ristampa conta una volta, comprese le collaborazioni. "
            "Dicono quanto un autore è già pubblicato in ogni paese." if it else
            "Records linked to the author in each catalogue: each edition or reprint counts once, collaborations included. "
            "They show how much an author is already published in each country.")
    return f'<ul class="cat">{li}</ul>\n<p class="sa-nota">{esc(nota)}</p>\n'


def domande(a, lang):
    """Domande con risposte fatte solo di dati di questo autore (niente frasi uguali in tutte le schede)."""
    it = lang == "it"
    nome = pulisci(a["nome"])
    D = anno_di(a.get("morte"))
    out = []
    T = (lambda x, y: x) if it else (lambda x, y: y)
    if it:
        out.append((f"Quando {nome} entra in pubblico dominio in Italia?",
                    f"Il {data_l(lang, D + 71)}: {nome} è morto nel {D} e in Italia le opere diventano libere 70 anni dopo la morte, "
                    f"dal 1° gennaio dell'anno successivo." + (" Per gli autori di paesi alleati nella Seconda guerra mondiale va verificato caso per caso." if avviso_alleato(a, lang) else "")))
    else:
        out.append((f"When does {nome} enter the public domain?",
                    f"In the UK and the EU on {data_l(lang, D + 71)}: {nome} died in {D}, and the works become free 70 years after death, "
                    f"from 1 January of the following year." + (f" In Spain on {data_l(lang, D + 81)}." if D < 1987 else "")))
    liberi = [t for t in a.get("_liberi_usa", [])]
    if liberi:
        el = ", ".join(liberi[:6])
        out.append((T(f"Quali opere di {nome} sono già libere negli USA?", f"Which works by {nome} are already free in the USA?"),
                    T(f"Tra le opere principali, con l'anno confermato da due fonti: {el}.", f"Among the main works, with the year confirmed by two sources: {el}.")))
    return out


def scheda_statica(a, lang, bd):
    """Corpo della pagina autore, con lo stesso disegno della scheda del sito (mockup approvato)."""
    it = lang == "it"
    nome = pulisci(a["nome"])
    nasc, D = anno_di(a.get("nascita")), anno_di(a.get("morte"))
    T = (lambda x, y: x) if it else (lambda x, y: y)
    prof = ", ".join((a.get("professioni") or [])[:2]) if it else ""
    o = ['<div class="sa">\n<section class="sa-top"><div class="sa-in">\n',
         f'<p class="sa-et">{T("Scheda autore", "Author card")}{(" · " + esc(prof)) if prof else ""}</p>\n<header class="sa-head">\n']
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
    lunga = max((len(w) for w in nome.split()), default=0)   # la parola più lunga deve stare intera accanto al ritratto
    dim = ' style="font-size:clamp(36px,6vw,80px)"' if lunga >= 11 else (' style="font-size:clamp(44px,7.5vw,100px)"' if lunga >= 9 else "")
    o.append(f'<div><h1{dim}>{esc(nome)}</h1>\n<p class="sa-desc">{esc(" · ".join(desc))}</p></div>\n</header>\n')
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
    o.append(avviso_alleato(a, lang))
    # le date paese per paese, visibili e brevi: le regole spiegate stanno in un posto solo (riquadro delle regole)
    oggi_a = datetime.date.today().year
    def tessera(paese, anno, regola, cl=""):
        libero = bool(anno and anno <= oggi_a)
        stato = "ok" if libero else cl
        d = (T("libero", "free") + f" {T('dal', 'since')} {anno}") if libero else (data_l(lang, anno).replace("1° gennaio", "1° gen").replace("1 January", "1 Jan") if anno else T("opera per opera", "work by work"))
        return f'<li class="{stato}"><span class="p">{esc(paese)}</span><span class="d">{esc(d)}</span><span class="r">{esc(regola)}</span></li>'
    ue = T("70 anni dalla morte", "70 years after death")
    fr = ue + (T("; +30 anni se «morto per la Francia»", "; +30 years if «died for France»") if 1939 <= D <= 1945 else "")
    es_y = D + 81 if D < 1987 else D + 71
    es_r = T("80 anni: è morto prima del 1987", "80 years: died before 1987") if D < 1987 else ue
    it_r = ue + (T("; paese alleato: da verificare", "; Allied country: check") if avviso_alleato(a, lang) else "")
    righe_p = [(T("Italia", "Italy"), D + 71, it_r), (T("Francia", "France"), D + 71, fr), (T("Germania", "Germany"), D + 71, ue),
               (T("Regno Unito", "United Kingdom"), D + 71, ue + T("; inediti fino al 2039", "; unpublished works until 2039")),
               (T("Spagna", "Spain"), es_y, es_r), ("USA", None, T("95 anni dall'uscita di ogni opera", "95 years from each work's publication"))]
    if not it:   # in inglese prima i paesi di lingua inglese
        righe_p = [righe_p[3], righe_p[5]] + [righe_p[i] for i in (0, 1, 2, 4)]
    o.append(f'<ul class="pg" aria-label="{T("Paese per paese", "Country by country")}">' + "".join(
        tessera(*x, cl=("primo" if i == 0 else "usa" if x[0] == "USA" else "")) for i, x in enumerate(righe_p)) + "</ul>\n")
    o.append(f'<p class="sa-nota">{T("Calcolo indicativo, non è consulenza legale.", "Indicative calculation, not legal advice.")} '
             f'<a href="{"/" if it else "/en/"}#regole-paesi">{T("Le regole, paese per paese", "The rules, country by country")}</a></p>\n</div>\n'
             '</div></section>\n<div class="sa-in sa-resto">\n')
    sez = lambda tit, corpo, occ=None: (f'<section class="sa-sez">\n' + (f'<p class="sa-occ">{occ}</p>\n' if occ else "") + f'<h2>{tit}</h2>\n{corpo}</section>\n')
    corpo_usa, liberi_usa = opere_usa(a, lang)
    a["_liberi_usa"] = liberi_usa
    if corpo_usa:
        extra = (f'<p class="sa-nota">{T(f"Su {migliaia(a["n_opere"])} opere registrate in Wikidata, qui le più note.", f"Of {migliaia(a["n_opere"], lang)} works recorded in Wikidata, the best known.")}</p>\n'
                 if a.get("n_opere", 0) > 10 else "")
        o.append(sez(T("Opere principali", "Main works"), corpo_usa + extra, T("Negli USA, opera per opera", "In the USA, work by work")))
    g = ((a.get("traduzioni") or {}).get("sbn_it") if it else (a.get("traduzioni") or {}).get("bl_en"))
    if g and g.get("sospeso_manuale"):
        o.append(sez(T("Registrazioni in italiano", "Records in English"),
                     f'<p class="sa-nota">{esc(T("Dati in verifica: non è ancora dimostrato che la scheda del catalogo collegata a questo autore sia davvero sua, quindi non mostriamo i numeri finché non è chiarito.", "Data under review: it is not yet shown that the catalogue record linked to this author is really theirs, so we do not show the figures until this is cleared up."))}</p>\n'))
    elif g and g.get("trovato") and (g.get("stato") == "da_verificare" or problemi_conteggio(g, datetime.date.today().year)):
        o.append(sez(T("Registrazioni in italiano", "Records in English"),
                     f'<p class="sa-nota">{esc(T("Dati in verifica: per questo autore i numeri del catalogo si contraddicono, quindi non li mostriamo finché non sono corretti.", "Data under review: for this author the catalogue figures contradict each other, so we do not show them until they are fixed."))}</p>\n'))
    elif g and g.get("trovato"):
        box = lambda num, et: f'<div class="ed-box"><b>{migliaia(num, lang)}</b><span>{esc(et)}</span></div>'
        ult = f" · {T('più recente con anno certo:', 'latest with a certain year:')} {g['ultimo']}" if g.get("ultimo") else ""
        nota = (T("Registrazioni bibliografiche in italiano collegate all'autore nel catalogo SBN, comprese ristampe e antologie. Comprendono tutte le pubblicazioni collegate alla persona, anche quelle in cui ha collaborato (traduzioni, curatele, prefazioni), non solo i libri scritti da lei: è una misura di quanto è presente nel catalogo.", "")
                if it else "Bibliographic records in English linked to the author in the British Library catalogue, searched by surname and years of birth and death; a record counts only if surname and years belong to the same person. Some records catalogued differently may be missed. They include every publication linked to the person, including those they contributed to (translations, editing, prefaces), not only books they wrote: it measures how present they are in the catalogue.")
        if it and g.get("metodo") == "nome":
            nota += " Autore riconosciuto solo dal nome: il conteggio può essere impreciso."
        elif it and g.get("metodo") == "nome_con_prova":
            nota += " Autore riconosciuto dal nome con una prova in più (anni di nascita e morte, un titolo o un cognome unico nel catalogo), non da un codice."
        cosa = T("Che cos'è una registrazione: la scheda con cui la biblioteca descrive una pubblicazione. Di solito ce n'è una per ogni edizione o ristampa, quindi un libro uscito cinque volte conta cinque. Non sono copie vendute né titoli diversi.", "What a record is: the entry a library uses to describe a publication. There is usually one for each edition or reprint, so a book published five times counts five. Records are not copies sold, nor different titles.")
        o.append(sez(T("Registrazioni in italiano", "Records in English"),
                     f'<div class="ed-boxes">{box(g["edizioni"], T("registrazioni in italiano", "records in English"))}{box(g.get("dal_2000", 0), T("con anno dal 2000", "dated 2000 or later") + ult)}</div>\n<p class="sa-nota">{esc(cosa)}</p>\n<p class="sa-nota">{esc(nota)}</p>\n'))
    cat = catalogi_a_confronto(a, lang)
    if cat:
        o.append(sez(T("Quanto è già pubblicato", "How much is already published"), cat, T("Nei cataloghi nazionali", "In national catalogues")))
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
    faq = domande(a, lang)
    if faq:
        o.append(sez(T("Le risposte brevi", "Short answers"), '<div class="faq">' + "".join(
            f'<details{" open" if i == 0 else ""}><summary>{esc(q)}</summary><p>{esc(r_)}</p></details>' for i, (q, r_) in enumerate(faq)) + "</div>\n", T("Domande", "Questions")))
        fq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r_}} for q, r_ in faq]}
        o.append('<script type="application/ld+json">' + json.dumps(fq, ensure_ascii=False).replace("</", "<\\/") + "</script>\n")
    if bd:
        ln = f'<a href="{esc(bd["url"])}" rel="noopener">{T("Continua su Wikipedia", "Continue on Wikipedia")}</a>' if bd.get("url") else ""
        o.append(sez(T("Chi era", "Who they were"), f'<p class="sa-bio">{esc(bd["testo"])}</p>\n{ln}\n<p class="sa-nota">{T("Testo da Wikipedia, licenza CC BY-SA.", "Text from Wikipedia, licence CC BY-SA.")}</p>\n'))
    ill = "".join(blocco_illustrazioni(a, lang)[1:]).replace('<p class="sotto">', '<p class="sa-testo">')
    o.append(sez(T("Prima di pubblicare", "Before publishing"), ill + f'<p class="sa-nota">{T("Calcolo indicativo, non consulenza legale.", "Indicative calculation, not legal advice.")}</p>\n'))
    o.append("</div>\n</div>\n")   # chiude sa-resto e sa
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
                 f"Date per Italia, Francia, Germania, Spagna, Regno Unito e USA, registrazioni nei cataloghi nazionali e opere principali, da dati aperti.")
    else:
        titolo = f"{nome} ({anni}): when the works enter the public domain · Public Domain Radar"
        descr = (f"{nome} died in {D}: in the EU the works are free from {data_l(lang, D + 71)}. "
                 f"Dates for Italy, France, Germany, Spain, the UK and the USA, records in national catalogues and main works, from open data.")
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
    descr = (f"{len(voci)} autori con la data di pubblico dominio paese per paese (UE, Italia, Francia, Germania, Spagna, Regno Unito), da dati aperti." if it else
             f"{len(voci)} authors with the public-domain date country by country (EU, Italy, France, Germany, Spain, UK), from open data.")
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
    descr = (f"Quali autori entrano in pubblico dominio il 1° gennaio {A}, con le regole di Italia, Francia, Germania, Spagna, Regno Unito e USA "
             f"lette sui testi di legge ufficiali, e le registrazioni nei cataloghi nazionali. Dati aperti, aggiornati ogni tre mesi e a dicembre.")
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
    descr = (f"Which books and authors enter the public domain on 1 January {A}, with the term rules of Italy, France, Germany, Spain, the UK and the USA "
             f"read from official legal texts, and records in national catalogues. Open data, updated every three months and in December.")
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


CSS_PDD = """
main:has(.pd-sez){max-width:none;margin:0;padding:0}
.pd-in{max-width:1180px;margin:0 auto;padding:0 clamp(20px,4vw,48px)}
.pd-hero{background:var(--ink);color:var(--carta);padding:clamp(40px,7vw,80px) 0 clamp(48px,7vw,88px)}
.pd-occ{margin:0;font-family:var(--mono);font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--vermiglio)}
.pd-hero h1{margin:18px 0 0;font-family:var(--display);font-weight:900;font-size:clamp(64px,12vw,168px);line-height:.84;text-transform:uppercase;color:var(--carta);letter-spacing:0;border:0;padding:0}
.pd-hero h1 em{font-style:normal;color:var(--vermiglio)}
.pd-hero .lead{margin:24px 0 0;max-width:640px;font-size:clamp(17px,2vw,20px);line-height:1.5;color:#D2CFC4}
.pd-num{list-style:none;margin:44px 0 0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:2px}
.pd-num li{margin:0;background:var(--notte);padding:22px 24px 24px}
.pd-num li:first-child{background:var(--vermiglio);color:var(--ink)}
.pd-num b{display:block;font-family:var(--display);font-weight:900;font-size:clamp(56px,7vw,96px);line-height:.9}
.pd-num span{display:block;margin-top:10px;font-size:15px;line-height:1.4}
.pd-num li:not(:first-child) span{color:#D2CFC4}
.pd-sez{padding:clamp(56px,7vw,80px) 0 0}
.pd-sez.ultima{padding-bottom:clamp(56px,7vw,80px)}
.pd-et{margin:0;font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--vermiglio-testo)}
.pd-sez h2{margin:10px 0 0;font-family:var(--display);font-weight:900;font-size:clamp(40px,6vw,72px);line-height:.9;text-transform:uppercase;color:var(--ink);letter-spacing:0;border:0;padding:0}
.pd-sez .lead{margin:14px 0 0;max-width:680px;font-size:16px;line-height:1.5}
.pd-aut{list-style:none;margin:28px 0 0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px}
.pd-aut li{margin:0}
.pd-aut a{display:flex;gap:14px;align-items:center;text-decoration:none;color:var(--ink);background:#fff;padding:12px;border:1px solid #E4E2DA}
.pd-aut a:hover{border-color:var(--ink)}
.pd-ft{flex:none;width:64px;height:80px;background:var(--riquadro);overflow:hidden;display:flex;align-items:center;justify-content:center;font-family:var(--display);font-weight:900;font-size:26px;color:#9A978C}
.pd-ft img{width:100%;height:100%;object-fit:cover;object-position:50% 20%;display:block}
.pd-aut b{display:block;font-family:var(--display);font-weight:900;font-size:24px;line-height:.95;text-transform:uppercase}
.pd-aut span{display:block;margin-top:6px;font-size:13px;line-height:1.35;color:var(--muto)}
.pd-cop{list-style:none;margin:28px 0 0;padding:0 0 12px;display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:16px}
.pd-cop li{margin:0}
.pd-cop a{display:flex;flex-direction:column;justify-content:flex-end;aspect-ratio:7/10;padding:16px;text-decoration:none;overflow:hidden}
.pd-cop .t{font-family:var(--display);font-weight:900;line-height:.92;text-transform:uppercase}
.pd-cop .a{margin-top:8px;font-family:var(--mono);font-size:11px;text-transform:uppercase;line-height:1.4}
.pd-bd{display:inline-block;margin-top:8px;padding:3px 8px;font-family:var(--mono);font-size:11px}
.pd-bd.ok{background:#0E3B2E;color:var(--carta)}.pd-bd.ver{background:#F2B705;color:var(--ink)}
.pd-piu{margin:16px 0 0}.pd-piu a{font-weight:600}
.pd-tab{list-style:none;margin:28px 0 0;padding:0;border-top:2px solid var(--ink)}
.pd-tab li{margin:0;display:grid;grid-template-columns:minmax(0,180px) minmax(0,220px) 1fr auto;gap:20px;align-items:baseline;padding:16px 0;border-bottom:1px solid #D9D6CC}
.pd-tab .p{font-family:var(--display);font-weight:900;font-size:28px;line-height:1;text-transform:uppercase}
.pd-tab .c{font-family:var(--mono);font-size:12px;text-transform:uppercase;color:var(--muto)}
.pd-tab .r{font-size:15px;line-height:1.45}
.pd-tab a{font-family:var(--mono);font-size:13px;white-space:nowrap}
.pd-tre{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:28px 0 0}
.pd-tre div{background:#fff;border-top:4px solid var(--ink);padding:20px 22px 24px}
.pd-tre div:first-child{border-top-color:var(--vermiglio)}
.pd-tre h3{margin:0;font-family:var(--display);font-weight:900;font-size:28px;line-height:.95;text-transform:uppercase}
.pd-tre p{margin:12px 0 0;font-size:15px;line-height:1.5}
.pd-faq{margin:24px 0 0;max-width:820px}
.pd-faq details{border-top:1px solid #D9D6CC;padding:14px 0}.pd-faq details:last-child{border-bottom:1px solid #D9D6CC}
.pd-faq summary{cursor:pointer;font-weight:600;font-size:17px}
.pd-faq p{margin:10px 0 0;font-size:16px;line-height:1.55}
.pd-fondo{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:40px}
.pd-fondo p{margin:12px 0 0;font-size:15px;line-height:1.6}.pd-fondo .m{font-size:14px;color:var(--muto)}
.pd-cred{margin:14px 0 0;font-size:12px;line-height:1.5;color:var(--muto)}.pd-cred a{color:var(--muto)}
@media (max-width:760px){.pd-num{grid-template-columns:1fr}.pd-tre{grid-template-columns:1fr}
.pd-tab li{grid-template-columns:1fr;gap:4px}.pd-cop{grid-template-columns:repeat(2,minmax(0,1fr))}}
"""

LETTERARI = {"scrittore", "scrittrice", "poeta", "poetessa", "romanziere", "romanziera", "drammaturgo", "drammaturga",
             "saggista", "novellista", "autore", "autrice"}
COLORI_COP = [("#E9E6DD", "#0C0C10"), ("#FF4326", "#0C0C10"), ("#0E3B2E", "#F7F7F4"), ("#1C1C24", "#F7F7F4")]


def _visite(a):
    return sum((a.get("visite_" + l) or 0) for l in ("it", "en", "fr", "de", "es"))


def _letterari(pacchetto, lang):
    """Scrittori della lista con la loro pagina, in ordine di visite su Wikipedia in 5 lingue (come il resto del sito)."""
    pag = "pagina" if lang == "it" else "pagina_en"
    out = [a for a in pacchetto.get("autori", []) if a.get("letterario") and a.get("morte") and a.get(pag)
           and not a.get("fuori_classifica") and a["wikidata"] not in FUORI_CLASSIFICA
           and LETTERARI & set(a.get("professioni") or [])]
    return sorted(out, key=lambda a: -_visite(a))


def _data_lunga(iso, lang):
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", str(iso or ""))
    if not m:
        return str(anno_di(iso) or "")
    y, mm, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return f"{d} {MESI[mm - 1]} {y}" if lang == "it" else f"{d} {MESI_EN[mm - 1]} {y}"


def parole_t(t):
    return re.sub(r"[^a-z0-9]+", " ", unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().lower()).strip()


def _esempio_duke(anno, ue):
    """Un libro già libero negli USA (lista Duke di un anno passato) il cui autore entra in Europa quest'anno."""
    try:
        dk = json.loads((RADICE / "data" / "storico" / "duke.json").read_text(encoding="utf-8"))
    except Exception:
        return None
    aut = {a["wikidata"]: a for a in ue.get("autori", [])}
    # niente opere teatrali: spesso hanno coautori (es. «L'opera da tre soldi» con Elisabeth Hauptmann), e allora in
    # Europa la data dipende anche da loro
    TEATRO = {"commedia", "dramma", "teatro", "tragedia", "opera", "libretto", "musical"}
    def teatrale(w):
        for a in w.get("autori", []):
            for o in (aut.get(a.get("qid")) or {}).get("opere", []):
                if parole_t(o.get("titolo")) in (parole_t(w.get("titolo_it")), parole_t(w.get("titolo"))) or \
                   parole_t(o.get("titolo_en")) == parole_t(w.get("titolo")):
                    if TEATRO & set(o.get("generi") or []):
                        return True
        return False
    cand = []
    for y, v in dk.items():
        for l in v.get("libri", []):
            w = l.get("wd") or {}
            if int(y) < anno and len(w.get("autori", [])) == 1 and w["autori"][0].get("qid") in aut and not teatrale(w):
                cand.append(((w.get("pagine") or 0), int(y), l["titolo"], w.get("titolo_it")))
    if not cand:
        return None
    _, y, t, t_it = max(cand)
    return y, t, (t_it or t)


def _cop_pdd(href, titolo, sotto, badge):
    c = sum(ord(ch) * (i + 1) for i, ch in enumerate(titolo + sotto)) % 4
    sf, tx = COLORI_COP[c]
    return (f'<li><a href="{href}" style="background:{sf};color:{tx}"><span class="t" style="font-size:{_dim_titolo(titolo, 26)}px">{esc(titolo)}</span>'
            f'<span class="a">{esc(sotto)}</span></a>{badge}</li>\n')


def pagina_landing(anno, pacchetto_ue, opere_us, lang="en", pacchetto_es=None, verificati=None):
    """Pagina del Public Domain Day di <anno> (mockup approvato il 19/11/2026). Solo dati dei file, con le fonti."""
    oggi = datetime.date.today()
    url = url_landing(lang, anno)
    it = lang == "it"
    T = (lambda a, b: a) if it else (lambda a, b: b)
    app = "/" if it else "/en/"
    pub = opere_us["anno_pubblicazione"] if opere_us else anno - 96
    morti = anno - 71
    morti_es = anno - 81
    libero = pacchetto_ue.get("libero_dal") or f"{anno}-01-01"
    verificati = verificati or {}
    aut = _letterari(pacchetto_ue, lang)
    n_ue = sum(1 for a in pacchetto_ue.get("autori", []) if a.get("letterario") and a.get("morte"))
    n_es = sum(1 for a in (pacchetto_es or {}).get("autori", []) if a.get("letterario") and a.get("morte"))
    es_nomi = [pulisci(a["nome"]) for a in _letterari(pacchetto_es or {}, "it")[:3]]
    opere = (opere_us or {}).get("opere", [])
    n_us = len(opere)
    n_us_ok = sum(1 for o in opere if (verificati.get(o["qid"]) or ["nd"])[0] == "ok")
    cogn = lambda nome: pulisci(nome).split()[-1] if nome else ""

    # titolo e descrizione per Google: i nomi più cercati
    _au = [cogn(a["nome"]) for a in aut[:3]]
    _op = []
    for o in opere:
        chi = cogn(o["autori"][0]["nome"]) if o.get("autori") else ""
        if chi in _au:
            continue
        _op.append(((o.get("titolo_it") or o["titolo"]) if it else o["titolo"], chi))
        if len(_op) == 2:
            break
    if it:
        titolo = f"Pubblico dominio {anno}: cosa diventa libero il 1° gennaio · Public Domain Radar"
        descr = f"Gli scrittori e i libri che entrano in pubblico dominio il 1° gennaio {anno}, paese per paese, da dati aperti e con le fonti."
        if len(_au) >= 3 and len(_op) >= 2:
            titolo = f"Pubblico dominio {anno}: {_au[0]}, {_au[1]}, {_op[0][0]} e cosa diventa libero"
            descr = (f"Dal 1° gennaio {anno} in Europa diventano liberi {_au[0]}, {_au[1]}, {_au[2]} e altri scrittori; "
                     f"negli USA {_op[0][0]} ({_op[0][1]}), {_op[1][0]} ({_op[1][1]}) e altri libri del {pub}. Dati aperti, con le fonti.")
    else:
        titolo = f"Public Domain Day {anno}: books and authors that become free on 1 January · Public Domain Radar"
        descr = f"The writers and books entering the public domain on 1 January {anno}, country by country, from open data with sources."
        if len(_au) >= 3 and len(_op) >= 2:
            titolo = f"Public Domain Day {anno}: {_op[0][0]}, {_op[1][0]}, {_au[0]}, {_au[1]} and more"
            descr = (f"Free on 1 January {anno}: {_op[0][0]} ({_op[0][1]}), {_op[1][0]} ({_op[1][1]}) and more US books from {pub}; "
                     f"{_au[0]}, {_au[1]}, {_au[2]} and more writers in Europe and the UK. Open data, with sources.")

    # esempio per «dipende da dove pubblichi» e per le domande
    duke = _esempio_duke(anno, pacchetto_ue)
    non_alleati = [a for a in aut if not set(a.get("paesi") or []) & ALLEATI_1947]
    primo = non_alleati[0] if non_alleati else None

    faq = []
    if it:
        faq.append(("Cos'è il Public Domain Day?",
                    "È il 1° gennaio di ogni anno, il giorno in cui scadono i diritti d'autore delle opere che hanno raggiunto il limite di legge: "
                    "nell'Unione europea e nel Regno Unito 70 anni dalla morte dell'autore (direttiva 2006/116/CE, art. 1), negli USA 95 anni dalla pubblicazione (17 U.S.C. § 304)."))
        faq.append((f"Cosa entra in pubblico dominio nel {anno}?",
                    f"In Italia, Francia, Germania e Regno Unito le opere degli scrittori morti nel {morti}. In Spagna quelle degli scrittori morti nel {morti_es}. "
                    f"Negli USA i libri pubblicati nel {pub}."))
        if n_es and morti_es < 1987:
            faq.append((f"Perché in Spagna entrano gli autori morti nel {morti_es}?",
                        "Per chi è morto prima del 7 dicembre 1987 la legge spagnola applica ancora gli 80 anni della legge del 1879 "
                        "(Ley de Propiedad Intelectual, disposizione transitoria quarta)."))
        if primo:
            faq.append((f"{pulisci(primo['nome'])} si può pubblicare in Italia dal 1° gennaio {anno}?",
                        f"Il testo originale sì: {pulisci(primo['nome'])} è morto nel {anno_di(primo['morte'])}. "
                        "Le traduzioni italiane già pubblicate no, finché non sono libere anche loro: hanno diritti propri, che durano 70 anni dalla morte del traduttore."))
        faq.append((f"Posso pubblicare in Italia un libro uscito negli USA nel {pub}?",
                    f"Non automaticamente. In Italia conta quando è morto l'autore, anche per gli autori americani: la Cassazione ha applicato i 70 anni dalla morte "
                    f"a un autore statunitense anche se negli USA l'opera era già libera (caso Zorro)."))
        faq.append(("È consulenza legale?",
                    "No. Sono informazioni generali costruite da dati aperti e possono contenere errori. Prima di pubblicare controlla la legge e i fatti per il tuo paese e la tua edizione."))
    else:
        faq.append(("What is Public Domain Day?",
                    "It is 1 January of every year, the day copyright expires for works that have reached the legal limit: in the European Union and the UK "
                    "70 years after the author's death (Directive 2006/116/EC, Art. 1), in the USA 95 years after publication (17 U.S.C. § 304)."))
        faq.append((f"What enters the public domain in {anno}?",
                    f"In Italy, France, Germany and the UK, the works of writers who died in {morti}. In Spain, those of writers who died in {morti_es}. "
                    f"In the USA, books published in {pub}."))
        if n_es and morti_es < 1987:
            faq.append((f"Why do authors who died in {morti_es} enter in Spain?",
                        "For authors who died before 7 December 1987, Spanish law still applies the 80 years of the 1879 law "
                        "(Ley de Propiedad Intelectual, fourth transitional provision)."))
        faq.append((f"Is every book published in {pub} really free in the USA?",
                    "Not always. Works first published in the USA whose copyright was not renewed after 28 years were already free earlier. Foreign works that regained "
                    "protection in 1996 (17 U.S.C. § 104A) last 95 years from publication. We call a book free only when a second source confirms the year it came out."))
        faq.append(("Is this legal advice?",
                    "No. It is general information built from open data, and it may contain errors. Before publishing, check the law and the facts for your country and your edition."))

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
                        css=CSS + CSS_PDD, home=app, altra_lingua=altra)]

    # 1. apertura
    n_ = lambda x: migliaia(x, lang)
    nums = [(n_ue, T(f"scrittori liberi in Italia, Francia, Germania e Regno Unito: morti nel {morti}",
                     f"writers free in Italy, France, Germany and the UK: died in {morti}"))]
    if n_es:
        nums.append((n_es, T(f"scrittori liberi in Spagna: morti nel {morti_es}", f"writers free in Spain: died in {morti_es}")))
    if n_us:
        nums.append((n_us, T(f"libri liberi negli USA: pubblicati nel {pub}, {n_us_ok} con l'anno confermato",
                             f"books free in the USA: published in {pub}, {n_us_ok} with the year confirmed")))
    out.append(f"""<header class="pd-hero"><div class="pd-in">
<p class="pd-occ">Public Domain Day · {T("1° gennaio", "1 January")} {anno}<span id="pd-giorni"></span></p>
<h1>{T("Cosa diventa", "What becomes")} <em>{T("libero", "free")}</em> {T("nel", "in")} {anno}</h1>
<p class="lead">{T(f"Il 1° gennaio {anno} scadono i diritti di centinaia di scrittori e libri. Chi, dove e con quali cautele, da dati aperti e con le fonti.",
                   f"On 1 January {anno} copyright expires for hundreds of writers and books. Who, where and with what caveats, from open data with sources.")}</p>
<ul class="pd-num">{"".join(f'<li><b>{n_(x)}</b><span>{esc(t)}</span></li>' for x, t in nums)}</ul>
</div></header>
<main>
""")

    # 2. i nomi più attesi
    if aut:
        out.append(f'<section class="pd-sez"><div class="pd-in">\n<p class="pd-et">{T("Europa e Regno Unito", "Europe and the UK")}</p>\n'
                   f'<h2>{T("I nomi più attesi", "The most awaited names")}</h2>\n'
                   f'<p class="lead">{T(f"Gli scrittori morti nel {morti} più letti su Wikipedia. Dal 1° gennaio i loro testi originali si possono pubblicare senza permesso in Italia, Francia, Germania e Regno Unito.", f"The writers who died in {morti} that are most read on Wikipedia. From 1 January their original texts can be published without permission in Italy, France, Germany and the UK.")}</p>\n<ul class="pd-aut">\n')
        crediti = []
        for a in aut[:8]:
            nome = pulisci(a["nome"])
            href = f"/autore/{a['pagina']}/" if it else f"/en/author/{a['pagina_en']}/"
            foto = a.get("foto") or {}
            if foto.get("url"):
                img = re.sub(r"width=\d+", "width=240", foto["url"])
                ft = f'<span class="pd-ft"><img src="{esc(img)}" alt="" loading="lazy"></span>'
                chi_f = re.sub(r"^(.+?)\1$", r"\1", pulisci(foto.get("autore")))   # Commons a volte ripete il nome due volte
                chi_f = "" if len(chi_f) > 60 else chi_f
                crediti.append(f'{esc(nome)}: <a href="{esc(foto.get("pagina", ""))}" rel="noopener">{esc(" · ".join(x for x in (chi_f, pulisci(foto.get("licenza"))) if x) or "Wikimedia Commons")}</a>')
            else:
                ft = f'<span class="pd-ft" aria-hidden="true">{esc(iniziali_nome(nome))}</span>'
            if it:
                sotto = f"{anno_di(a.get('nascita')) or '?'} – {_data_lunga(a['morte'], 'it')}"
            else:
                d = re.sub(r"\s*\([^)]*\)\s*$", "", pulisci(a.get("descrizione")))
                sotto = (d + " · " if d else "") + f"died {_data_lunga(a['morte'], 'en')}"
            out.append(f'<li><a href="{href}">{ft}<span><b>{esc(nome)}</b><span>{esc(sotto)}</span></span></a></li>\n')
        out.append(f'</ul>\n<p class="pd-piu"><a href="{app}#/{anno}">{T(f"Tutti i {n_(n_ue)} scrittori, con le schede →", f"All {n_(n_ue)} writers, with their pages →")}</a></p>\n')
        if crediti:
            out.append(f'<p class="pd-cred">{T("Ritratti da Wikimedia Commons", "Portraits from Wikimedia Commons")} — {" · ".join(crediti)}</p>\n')
        out.append("</div></section>\n")

    # 3. i libri USA
    if opere:
        out.append(f'<section class="pd-sez"><div class="pd-in">\n<p class="pd-et">{T("Stati Uniti", "United States")}</p>\n'
                   f'<h2>{T(f"I libri del {pub}", f"The books of {pub}")}</h2>\n'
                   f'<p class="lead">{T(f"Negli USA conta l&#39;anno di pubblicazione: il 1° gennaio diventano liberi i libri usciti nel {pub}. Diciamo «confermato» solo quando l&#39;anno è confermato da una fonte diversa da Wikidata (registro del copyright americano, biblioteche nazionali, Open Library, Library of Congress); per gli altri scriviamo «anno da confermare».", f"In the USA what counts is the year of publication: on 1 January books published in {pub} become free. We say «confirmed» only when a source other than Wikidata confirms the year (the US copyright register, national libraries, Open Library, Library of Congress); for the others we say «year to be confirmed».")}</p>\n<ul class="pd-cop">\n')
        for o in opere[:12]:
            t = (o.get("titolo_it") or o["titolo"]) if it else o["titolo"]
            chi = ", ".join(pulisci(a["nome"]) for a in o.get("autori", [])) or "—"
            v_ = verificati.get(o["qid"]) or ["nd"]
            if v_[0] == "ok":
                badge = f'<span class="pd-bd ok">{T(f"{pub} confermato", f"{pub} confirmed")}</span>'
            elif v_[0] == "parziale":   # uscito a puntate fino a un anno dopo: libero per intero più tardi
                badge = f'<span class="pd-bd ver">{T(f"a puntate fino al {v_[1]}", f"serialized until {v_[1]}")}</span>'
            else:
                badge = f'<span class="pd-bd ver">{T("anno da confermare", "year to be confirmed")}</span>'
            out.append(_cop_pdd(f"{app}#/opera/{o['qid']}", t, f"{chi} · {pub}", badge))
        out.append(f'</ul>\n<p class="pd-piu"><a href="{app}#/us/{anno}">{T(f"Tutti i {n_us} libri: {n_us_ok} confermati, {n_us - n_us_ok} da confermare →", f"All {n_us} books: {n_us_ok} confirmed, {n_us - n_us_ok} to be confirmed →")}</a></p>\n</div></section>\n')

    # 4. paese per paese
    righe = [
        (T("Italia", "Italy"), T(f"autori morti nel {morti}", f"authors who died in {morti}"),
         T("70 anni dalla morte. Per gli autori di paesi alleati nella Seconda guerra mondiale va verificato.", "70 years after death. For authors from Allied countries in the Second World War it must be checked."),
         f"{app}#/{anno}", T(f"{n_(n_ue)} scrittori →", f"{n_(n_ue)} writers →")),
        (T("Francia", "France"), T(f"autori morti nel {morti}", f"authors who died in {morti}"),
         T("70 anni; 30 in più per chi è «morto per la Francia».", "70 years; 30 more for authors who «died for France»."),
         f"{app}#/{anno}", T(f"{n_(n_ue)} scrittori →", f"{n_(n_ue)} writers →")),
        (T("Germania", "Germany"), T(f"autori morti nel {morti}", f"authors who died in {morti}"),
         T("70 anni dalla morte.", "70 years after death."), f"{app}#/{anno}", T(f"{n_(n_ue)} scrittori →", f"{n_(n_ue)} writers →")),
        (T("Regno Unito", "United Kingdom"), T(f"autori morti nel {morti}", f"authors who died in {morti}"),
         T("70 anni; le opere uscite dopo il 1988 di autori morti prima del 1969 restano protette fino al 2039.", "70 years; works first published after 1988 by authors who died before 1969 stay protected until 2039."),
         f"{app}#/{anno}", T(f"{n_(n_ue)} scrittori →", f"{n_(n_ue)} writers →")),
    ]
    if n_es:
        nomi = (T(": entrano ", ": in come ") + ", ".join(es_nomi)) if es_nomi else ""
        righe.append(("Spagna" if it else "Spain", T(f"autori morti nel {morti_es}", f"authors who died in {morti_es}"),
                      T(f"80 anni per chi è morto prima del 1987{nomi}.", f"80 years for authors who died before 1987{nomi}."),
                      f"{app}#/{anno}", T(f"{n_(n_es)} scrittori →", f"{n_(n_es)} writers →")))
    if n_us:
        righe.append(("USA", T(f"libri pubblicati nel {pub}", f"books published in {pub}"),
                      T("95 anni dalla pubblicazione, opera per opera.", "95 years after publication, work by work."),
                      f"{app}#/us/{anno}", T(f"{n_us} libri →", f"{n_us} books →")))
    out.append(f'<section class="pd-sez"><div class="pd-in">\n<p class="pd-et">{T("Paese per paese", "Country by country")}</p>\n'
               f'<h2>{T("Chi entra, dove", "Who enters, where")}</h2>\n<ul class="pd-tab">\n')
    for p, c, r, h, l in righe:
        out.append(f'<li><span class="p">{esc(p)}</span><span class="c">{esc(c)}</span><span class="r">{esc(r)}</span><a href="{h}">{esc(l)}</a></li>\n')
    out.append(f'</ul>\n<p class="pd-cred">{T("Regole lette sui testi di legge di ogni paese:", "Rules read from each country&#39;s legal texts:")} <a href="{app}#regole-paesi">{T("il riquadro delle regole", "the rules box")}</a>.</p>\n</div></section>\n')

    # 5. cosa significa davvero
    if duke:
        y, t_en, t_it = duke
        dove = T(f"«{t_it}» è libero negli USA dal {y} e in Europa solo dal {anno}.", f"«{t_en}» has been free in the USA since {y}, and in Europe only from {anno}.")
    else:
        dove = ""
    out.append(f"""<section class="pd-sez"><div class="pd-in">
<p class="pd-et">{T("Prima di pubblicare", "Before you publish")}</p>
<h2>{T("Cosa significa davvero", "What it really means")}</h2>
<div class="pd-tre">
<div><h3>{T("Il testo, non l'edizione", "The text, not the edition")}</h3><p>{T("È libero il testo originale. Le traduzioni recenti, le illustrazioni e le edizioni curate hanno diritti propri: per tradurre un autore serve una traduzione nuova, o una già libera.", "The original text is free. Recent translations, illustrations and edited editions have their own rights: to publish a translation you need a new one, or one that is already free.")}</p></div>
<div><h3>{T("Dipende da dove pubblichi", "It depends where you publish")}</h3><p>{T("Il 1° gennaio non scade tutto insieme ovunque. Lo stesso libro può essere libero negli USA e protetto in Europa, o il contrario.", "On 1 January not everything expires everywhere at once. The same book can be free in the USA and protected in Europe, or the other way round.")} {esc(dove)}</p></div>
<div><h3>{T("Certo e da verificare", "Certain and to be checked")}</h3><p>{T("Segniamo come certo solo ciò che è confermato da più fonti (anni di morte, anni di uscita). Il resto è «da verificare», con il motivo. Le fonti sono elencate in fondo a ogni pagina.", "We mark as certain only what more than one source confirms (years of death, years of publication). The rest is «to be checked», with the reason. Sources are listed at the bottom of every page.")}</p></div>
</div></div></section>
""")

    # 6. domande
    out.append(f'<section class="pd-sez"><div class="pd-in">\n<p class="pd-et">{T("Domande", "Questions")}</p>\n<h2>{T("Le risposte brevi", "The short answers")}</h2>\n<div class="pd-faq">\n')
    for q, r in faq:
        out.append(f"<details><summary>{esc(q)}</summary><p>{esc(r)}</p></details>\n")
    out.append("</div></div></section>\n")

    # 7. calendario, fonti e metodo
    cal = ""
    if CALENDARIO_ON and anno == _cal:
        href = f"/calendario/{anno}/" if it else f"/en/calendar/{anno}/"
        cal = (f'<div><p class="pd-et">{T("Il 1° gennaio, nel calendario", "1 January, in the calendar")}</p><p>'
               f'{T("Il Public Domain Day è la prima voce del", "Public Domain Day is the first entry of the")} <a href="{href}">{T(f"calendario degli anniversari letterari {anno}", f"{anno} literary anniversaries calendar")}</a>.</p></div>')
    metodo = "https://github.com/mnovali90-byte/publicdomain/blob/main/docs/metodo-anni-opere.md"
    out.append(f"""<section class="pd-sez ultima"><div class="pd-in"><div class="pd-fondo">{cal}
<div><p class="pd-et">{T("Fonti e metodo", "Sources and method")}</p><p class="m">{T(
        "Wikidata (CC0) per autori, opere e anni; biblioteche nazionali per confermare gli anni di morte. Per gli anni di uscita dei libri USA: registro del copyright americano (Catalog of Copyright Entries, trascritto dalla New York Public Library, CC0), Duke University (CC BY 4.0), Open Library, Library of Congress, BnF e il catalogo collettivo tedesco K10plus. Visite: Wikipedia in 5 lingue.",
        "Wikidata (CC0) for authors, works and years; national libraries to confirm years of death. For the publication years of US books: the US copyright register (Catalog of Copyright Entries, transcribed by the New York Public Library, CC0), Duke University (CC BY 4.0), Open Library, Library of Congress, BnF and the German union catalogue K10plus. Page views: Wikipedia in 5 languages.")} <a href="{metodo}" rel="noopener">{T("Come confermiamo gli anni", "How we confirm the years")}</a>. {T("Non è consulenza legale.", "Not legal advice.")}</p></div>
</div></div></section>
</main>
""")
    gg = ('d===1?" · domani":" · tra "+d+" giorni"' if it else 'd===1?" · tomorrow":" · in "+d+" days"')
    out.append(f'<script>(function(){{var d=Math.ceil((new Date("{libero}T00:00:00")-new Date())/864e5),e=document.getElementById("pd-giorni");if(e&&d>0)e.textContent={gg}}})();</script>\n')
    out.append(PIEDE[lang])
    return "".join(out), url


def crea_landing():
    """Per ogni anno disponibile: en/public-domain-<anno>/ e pubblico-dominio-<anno>/. Restituisce gli indirizzi."""
    urls = []
    ver = liste_usa()   # registro unico (scripts/registro.py): le verifiche delle liste, per anno
    for f in sorted(glob.glob(str(RADICE / "data" / "[0-9][0-9][0-9][0-9].json"))):
        anno = int(Path(f).stem)
        ue = json.load(open(f, encoding="utf-8"))
        fus = RADICE / "data" / f"us-{anno}.json"
        us = json.load(open(fus, encoding="utf-8")) if fus.exists() else None
        fes = RADICE / "data" / f"es-{anno}.json"
        es = json.load(open(fes, encoding="utf-8")) if fes.exists() else None
        for lang, d in (("en", RADICE / "en" / f"public-domain-{anno}"), ("it", RADICE / f"pubblico-dominio-{anno}")):
            html_, url = pagina_landing(anno, ue, us, lang, es, ver.get(str(anno)))
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

    # guardia (19/11/2026): se i dati non hanno biografie e opere (giro interrotto a metà) non si tocca niente
    if len(autori) < 100:
        print(f"Solo {len(autori)} autori con biografia e opere: dati incompleti, le schede restano come sono.")
        return 1
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
            if q in FUORI_CLASSIFICA:
                a_["fuori_classifica"] = True
            else:
                a_.pop("fuori_classifica", None)
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
    if (RADICE / "gia-pubblici" / "index.html").exists():   # pagina «Già pubblici» (storico/pagina.py)
        landing_urls += [f"{SITO}/gia-pubblici/", f"{SITO}/en/already-public/"]
    righe += [f"  <url><loc>{u}</loc><lastmod>{oggi}</lastmod><changefreq>weekly</changefreq></url>" for u in landing_urls]
    righe += [f"  <url><loc>{u}</loc><lastmod>{oggi}</lastmod></url>" for u in sorted(urls)]
    (RADICE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(righe) + "\n</urlset>\n", encoding="utf-8")
    print(f"Pagine create: {len(voci['it'])} in italiano, {len(voci['en'])} in inglese (su {len(autori)} autori con biografia e opere)")


if __name__ == "__main__":
    sys.exit(main())
