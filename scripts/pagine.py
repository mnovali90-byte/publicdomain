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


# lettere che la normalizzazione non scompone e che prima sparivano dall'indirizzo (21/11/2026: Valdemar Rørdam
# diventava «valdemar-rrdam», Cahit Sıtkı Tarancı «cahit-stk-taranc»; 74 autori nelle liste)
LETTERE = {"ø": "o", "Ø": "O", "ı": "i", "ł": "l", "Ł": "L", "ß": "ss", "æ": "ae", "Æ": "Ae", "œ": "oe", "Œ": "Oe",
           "đ": "d", "Đ": "D", "þ": "th", "Þ": "Th", "ð": "d", "Ð": "D", "ħ": "h", "Ħ": "H", "ŧ": "t", "ĸ": "k"}


def slug_vecchio(nome):
    """Indirizzo come lo si faceva prima del 21/11/2026 (serve per i rimandi dalle schede già pubblicate)."""
    t = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def slug_base(nome):
    return slug_vecchio("".join(LETTERE.get(c, c) for c in nome or ""))


def pagina_rimando(nuovo_url, lang):
    """Pagina al vecchio indirizzo di una scheda: rimanda subito al nuovo, e dice a Google qual è quello giusto."""
    t = "La pagina si è spostata" if lang == "it" else "This page has moved"
    return (f'<!DOCTYPE html>\n<html lang="{lang}"><head><meta charset="utf-8"><title>{t}</title>'
            f'<meta name="robots" content="noindex"><link rel="canonical" href="{nuovo_url}">'
            f'<meta http-equiv="refresh" content="0; url={nuovo_url}"></head>'
            f'<body><p><a href="{nuovo_url}">{nuovo_url}</a></p></body></html>\n')


# date della sitemap (21/11/2026): la data di una pagina è quella in cui il suo contenuto cambia davvero, non quella
# di ogni giro. Il conto alla rovescia («tra 41 giorni») e le date di aggiornamento non contano come cambiamento.
DATE_SITEMAP = RADICE / "data" / "sitemap_date.json"
VOLATILE = [re.compile(p) for p in (r"tra \d+ giorn[oi]", r"in \d+ days?", r"\d+ (giorni|days?) (left|rimasti)",
                                     r'"dateModified": ?"[^"]*"', r"\d{4}-\d{2}-\d{2}")]


def impronta(percorso):
    import hashlib
    try:
        t = percorso.read_text(encoding="utf-8")
    except Exception:
        return None
    for r_ in VOLATILE:
        t = r_.sub("", t)
    return hashlib.sha1(t.encode("utf-8")).hexdigest()[:16]


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
.sa-risposta{margin:22px 0 0;max-width:46rem;font-size:clamp(18px,2vw,21px);line-height:1.45;color:#F7F7F4}
.sa-risposta b{color:#FF6A52;font-weight:600}
.sa-risposta + .sa-credito{margin-top:10px}
.vic{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr;gap:8px}
@media(min-width:560px){.vic{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(min-width:900px){.vic{grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}}
.vic li{margin:0}
.vic a{display:flex;gap:12px;align-items:center;padding:10px;background:var(--riquadro);color:var(--ink);text-decoration:none;height:100%;transition:background .15s}
.vic a:hover{background:#D9D6CC}
.vf{flex:none;width:48px;height:60px;background:#D2CFC4;overflow:hidden;display:flex;align-items:center;justify-content:center}
.vf img{width:100%;height:100%;object-fit:cover;object-position:50% 20%;display:block}
.vi{font-family:var(--display);font-weight:900;font-size:26px;color:#F7F7F4}
.vt{display:flex;flex-direction:column;min-width:0;line-height:1.25}
.vt b{font-size:16px;font-weight:600}
.vt span{font-family:var(--mono);font-size:11px;letter-spacing:.04em;color:var(--muto);margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.vt .vm{font-family:var(--testo);font-size:13px;letter-spacing:0;margin-top:1px}
.vic-tutti{margin:16px 0 0;font-family:var(--mono);font-size:13px;letter-spacing:.06em;text-transform:uppercase}
.vic-tutti a{color:var(--vermiglio-testo)!important}
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
<p>Le date sono un calcolo indicativo dalle norme elencate nel <a href="/radar/#regole-paesi">riquadro delle regole</a>. Non è consulenza legale: prima di pubblicare va controllato nella legge del paese.</p>
<p>Chi usa questi dati lo fa sotto la propria responsabilità. Le date sono indicative e riguardano le opere originali: traduzioni, illustrazioni ed edizioni recenti hanno diritti propri. Per un'edizione commerciale chiedi un parere a un esperto di diritto d'autore. <a href="https://github.com/mnovali90-byte/publicdomain/issues">Hai trovato un errore? Segnalalo</a>.</p>
<p><a href="/radar/">Tutti gli autori</a> · <a href="/pubblico-dominio-@@ANNO@@/">Pubblico dominio @@ANNO@@</a> · <a href="/autore/">Indice degli autori</a> · <a href="https://github.com/mnovali90-byte/publicdomain">Codice e dati su GitHub</a></p>
</footer>
</body>
</html>
""",
    "en": """<footer>
<p>A project by Marco Novali · <a href="https://www.linkedin.com/in/marconovali" rel="me noopener" target="_blank">LinkedIn</a></p>
<p>Sources: Wikidata (CC0), Wikipedia (text CC BY-SA, linked to the original page), Wikimedia Commons (portraits, each with its own licence), national catalogues (SBN, BnF, BNE, British Library and Library of Congress). Open data, updated automatically every three months and in December; it may contain errors.</p>
<p>The dates are an indicative calculation from the rules listed in the <a href="/en/radar/#regole-paesi">rules box</a>. Not legal advice: check the law of the country before publishing.</p>
<p>Anyone using this data does so at their own risk. The dates are indicative and refer to the original works: translations, illustrations and recent editions have their own rights. For a commercial edition, ask a copyright expert for advice. <a href="https://github.com/mnovali90-byte/publicdomain/issues">Found an error? Report it</a>.</p>
<p><a href="/en/radar/">All authors</a> · <a href="/en/public-domain-@@ANNO@@/">Public domain @@ANNO@@</a> · <a href="/en/author/">Author index</a> · <a href="https://github.com/mnovali90-byte/publicdomain">Code and data on GitHub</a></p>
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


# Trattato di pace del 1947, allegato XV, parte A, punto 3: in Italia non conta il periodo dall'inizio della guerra
# all'entrata in vigore del trattato (15 settembre 1947). Al massimo poco più di 7 anni: per prudenza 8. Finché la data
# normale più questa proroga non è passata, per gli autori dei paesi alleati in Italia scriviamo «da verificare».
PROROGA_ALLEATI = 8


def avviso_alleato(a, lang):
    p = [x for x in a.get("paesi", []) if x in ALLEATI_1947]
    if not p:
        return ""
    t = (f"Autore di un paese alleato nella Seconda guerra mondiale ({', '.join(p)}): in Italia la protezione può durare di più "
         "(Trattato di pace del 1947, allegato XV): per questo in Italia non diamo una data, va verificata opera per opera." if lang == "it" else
         f"Author from an Allied country in the Second World War ({', '.join(p)}): in Italy protection may last longer "
         "(1947 Peace Treaty, Annex XV): so we give no date for Italy, it must be checked work by work.")
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
    # «Quando entra in pubblico dominio?» ora è la frase di risposta in cima alla scheda (frase_risposta, 21/11/2026)
    liberi = [t for t in a.get("_liberi_usa", [])]
    if liberi:
        el = ", ".join(liberi[:6])
        out.append((T(f"Quali opere di {nome} sono già libere negli USA?", f"Which works by {nome} are already free in the USA?"),
                    T(f"Tra le opere principali, con l'anno confermato da due fonti: {el}.", f"Among the main works, with the year confirmed by two sources: {el}.")))
    return out


def frase_risposta(a, lang):
    """La risposta in una frase, sotto il nome (mockup approvato il 21/11/2026): è il testo che Google mostra nei risultati."""
    it = lang == "it"
    nome = pulisci(a["nome"])
    D = anno_di(a.get("morte"))
    oggi = datetime.date.today()
    fut = lambda anno: datetime.date(anno, 1, 1) > oggi
    ue, es = D + 71, (D + 81 if D < 1987 else None)
    alleato = bool(avviso_alleato(a, lang))
    if it:
        paesi = "Francia, Germania e Regno Unito" if alleato else "Italia, Francia, Germania e Regno Unito"
        x = (f"Le opere di {esc(nome)} diventano di pubblico dominio in {paesi} il <b>{data_l(lang, ue)}</b>" if fut(ue)
             else f"Le opere di {esc(nome)} sono di pubblico dominio in {paesi} dal <b>{data_l(lang, ue)}</b>")
        if es:
            if fut(es) == fut(ue):
                x += f"; in Spagna {'il' if fut(es) else 'dal'} {data_l(lang, es)}"
            else:
                x += f"; in Spagna lo diventano il {data_l(lang, es)}"
        x += "."
        if alleato:
            x += " In Italia va verificato: è un autore di un paese alleato nella Seconda guerra mondiale."
        x += " Negli USA dipende dall’anno di uscita di ogni opera."
    else:
        paesi = "the UK, France and Germany" if alleato else "the UK, France, Germany and Italy"
        x = (f"The works of {esc(nome)} enter the public domain in {paesi} on <b>{data_l(lang, ue)}</b>" if fut(ue)
             else f"The works of {esc(nome)} have been in the public domain in {paesi} since <b>{data_l(lang, ue)}</b>")
        if es:
            if fut(es) == fut(ue):
                x += f"; in Spain {'on' if fut(es) else 'since'} {data_l(lang, es)}"
            else:
                x += f"; in Spain they enter it on {data_l(lang, es)}"
        x += "."
        if alleato:
            x += " In Italy it must be checked: the author is from an Allied country in the Second World War."
        x += " In the USA it depends on each work’s publication year."
    return f'<p class="sa-risposta">{x}</p>\n'


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
    o.append(frase_risposta(a, lang))
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
    _all = bool(avviso_alleato(a, lang))
    def tessera(paese, anno, regola, cl=""):
        libero = bool(anno and anno <= oggi_a)
        italia_ver = paese == T("Italia", "Italy") and _all and anno and anno + PROROGA_ALLEATI > oggi_a
        if italia_ver:
            libero = False
        stato = "ok" if libero else cl
        d = (T("libero", "free") + f" {T('dal', 'since')} {anno}") if libero else (data_l(lang, anno).replace("1° gennaio", "1° gen").replace("1 January", "1 Jan") if anno else T("opera per opera", "work by work"))
        if italia_ver:
            d = T("da verificare", "to be checked")   # paese alleato: niente data (Marco, 21/11/2026)
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
             f'<a href="{"/radar/" if it else "/en/radar/"}#regole-paesi">{T("Le regole, paese per paese", "The rules, country by country")}</a></p>\n</div>\n'
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
    o.append(blocco_vicini(a, lang))
    o.append("</div>\n</div>\n")   # chiude sa-resto e sa
    return "".join(o)


# ===================================================================================================
# SCHEDA AUTORE, grafica «Indice» (mockup approvato da Marco il 21/11/2026: rdr-scheda-brecht-indice.html)
# Tutto il testo sta nella pagina (non lo costruisce il browser), così Google lo legge come prima.
# ===================================================================================================
CSS_SCHEDA = (Path(__file__).resolve().parent / "stile_scheda.css").read_text(encoding="utf-8")


def _menu_link(lang):
    it = lang == "it"
    a = ANNO_PROSSIMO
    if it:
        # l'anno dopo (es. 2028) non compare nei menu fino al suo turno, il 1° gennaio (decisione di Marco, 21/11/2026);
        # la pagina resta online per Google. «Il radar» nel menu si chiama «Tutti gli autori».
        v = [(f"/pubblico-dominio-{a}/", f"Pubblico dominio {a}"), ("/radar/", "Tutti gli autori")]
        if CALENDARIO_ON:
            v.append((f"/calendario/{a}/", "Calendario"))
        v += [("/gia-pubblici/", "Già pubblici"), ("/autore/", "Indice degli autori")]
    else:
        v = [(f"/en/public-domain-{a}/", f"Public domain {a}"), ("/en/radar/", "All authors")]
        if CALENDARIO_ON:
            v.append((f"/en/calendar/{a}/", "Calendar"))
        v += [("/en/already-public/", "Already public"), ("/en/author/", "Author index")]
    return v


def testa_scheda(lang, titolo, descr, url, alterne_, jsonld, altra, cnt, og_tipo="profile", css_extra="", main_cls="", body_cls=""):
    it = lang == "it"
    menu = "".join(f'<a href="{h}"><span>{esc(t)}</span></a>' for h, t in _menu_link(lang))
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<title>{titolo}</title>
<meta name="description" content="{descr}">
<link rel="canonical" href="{url}">
{alterne_}<meta property="og:type" content="{og_tipo}">
<meta property="og:site_name" content="Public Domain Radar">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{titolo}">
<meta property="og:description" content="{descr}">
<meta name="twitter:card" content="summary">
{jsonld}
<link href="/assets/fonts/fonts.css" rel="stylesheet">
<style>{CSS_SCHEDA}{css_extra}</style>
<script>document.documentElement.classList.add('js')</script>
<!-- contatore visite senza cookie (GoatCounter) -->
<script data-goatcounter="https://pdr.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</head>
<body{f' class="{body_cls}"' if body_cls else ''}>
<header class="top">
  <a href="{"/" if it else "/en/"}" class="pdr" style="--w:56px" aria-label="Public Domain Radar">@@MARCHIO_S@@</a>
  <div class="cnt">{esc(cnt)}</div>
  <div class="r">{altra}<button id="mbtn" type="button">MENU</button></div>
</header>
<div class="menu" id="menu"><button class="x" id="mx" type="button">{"CHIUDI" if it else "CLOSE"}</button><nav aria-label="{"Sezioni del sito" if it else "Site sections"}">{menu}</nav></div>
<main{f' class="{main_cls}"' if main_cls else ''}>
"""


def piede_scheda(lang, fonti=None):
    it = lang == "it"
    T = (lambda x, y: x) if it else (lambda x, y: y)
    lk = " · ".join(f'<a href="{h}">{esc(t)}</a>' for h, t in _menu_link(lang))
    return f"""</main>
<footer class="end">
  <div><p class="m" style="color:var(--redt)">{fonti[0] if fonti else T("Fonti", "Sources")}</p><p>{fonti[1] if fonti else T("Wikidata (CC0), Wikipedia (testi CC BY-SA, con link alla pagina d'origine), Wikimedia Commons (ritratti, ciascuno con la sua licenza), cataloghi nazionali (SBN, BnF, BNE, British Library e Library of Congress). Dati aperti, aggiornati in automatico ogni tre mesi e a dicembre; possono contenere errori.", "Wikidata (CC0), Wikipedia (text CC BY-SA, linked to the original page), Wikimedia Commons (portraits, each with its own licence), national catalogues (SBN, BnF, BNE, British Library and Library of Congress). Open data, updated automatically every three months and in December; it may contain errors.")}</p>
  <p class="lk">{lk} · <a href="https://github.com/mnovali90-byte/publicdomain">{T("Codice e dati su GitHub", "Code and data on GitHub")}</a></p></div>
  <div><p class="m" style="color:var(--redt)">{T("Prima di pubblicare", "Before publishing")}</p><p>{T('Le date sono un calcolo indicativo dalle norme elencate nel <a href="/radar/#regole-paesi">riquadro delle regole</a>. Non è consulenza legale: prima di pubblicare va controllato nella legge del paese. Riguardano le opere originali: traduzioni, illustrazioni ed edizioni recenti hanno diritti propri. Chi usa questi dati lo fa sotto la propria responsabilità; per un’edizione commerciale chiedi un parere a un esperto di diritto d’autore.', 'The dates are an indicative calculation from the rules listed in the <a href="/en/radar/#regole-paesi">rules box</a>. Not legal advice: check the law of the country before publishing. They refer to the original works: translations, illustrations and recent editions have their own rights. Anyone using this data does so at their own risk; for a commercial edition, ask a copyright expert for advice.')}</p>
  <p>{T("Un progetto di Marco Novali", "A project by Marco Novali")} · <a href="https://www.linkedin.com/in/marconovali" rel="me noopener" target="_blank">LinkedIn</a> · <a href="https://github.com/mnovali90-byte/publicdomain/issues">{T("Hai trovato un errore?", "Found an error?")}</a></p></div>
</footer>
<script>
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
$('#mbtn').onclick=()=>$('#menu').classList.add('on'); $('#mx').onclick=()=>$('#menu').classList.remove('on');
const nm=$('#name'); if(nm) addEventListener('scroll',()=>document.body.classList.toggle('past',nm.getBoundingClientRect().bottom<0),{{passive:true}});
const gg=$('#days'); if(gg){{ const t=new Date(+gg.dataset.y,0,1)-new Date(); if(t>0) gg.textContent=Math.ceil(t/864e5).toLocaleString('{"it-IT" if it else "en-GB"}'); }}
const cat=$('#cat'); if(cat) new IntersectionObserver(([e],o)=>{{ if(e.isIntersecting){{ cat.classList.add('on'); o.disconnect(); }} }},{{threshold:.4}}).observe(cat);
$$('.why button').forEach(b=>b.onclick=()=>{{ const w=b.parentElement; w.classList.toggle('on'); b.querySelector('span').textContent=w.classList.contains('on')?'[–]':'[+]'; }});
$$('.acc button').forEach(b=>b.onclick=()=>{{ const a=b.parentElement; a.classList.toggle('on'); b.querySelector('span').textContent=a.classList.contains('on')?'[–]':'[+]'; }});
$$('#op sup').forEach(s=>s.onclick=()=>{{ const n=$('#nt'+s.dataset.n); if(!n) return; n.scrollIntoView({{behavior:'smooth',block:'center'}}); n.classList.add('hl'); setTimeout(()=>n.classList.remove('hl'),1600); }});
</script>
</body>
</html>
"""


def _paesi_riga(a, lang):
    """Righe «paese per paese»: (paese, anno o None, regola, classe)."""
    it = lang == "it"
    T = (lambda x, y: x) if it else (lambda x, y: y)
    D = anno_di(a.get("morte"))
    ue = T("70 anni dalla morte", "70 years after death")
    fr = ue + (T("; +30 anni se «morto per la Francia»", "; +30 years if «died for France»") if 1939 <= D <= 1945 else "")
    es_y = D + 81 if D < 1987 else D + 71
    es_r = T("80 anni: è morto prima del 1987", "80 years: died before 1987") if D < 1987 else ue
    it_r = ue + (T("; paese alleato: da verificare", "; Allied country: check") if avviso_alleato(a, lang) else "")
    r = [(T("Italia", "Italy"), D + 71, it_r), (T("Francia", "France"), D + 71, fr), (T("Germania", "Germany"), D + 71, ue),
         (T("Regno Unito", "United Kingdom"), D + 71, ue + T("; inediti fino al 2039", "; unpublished works until 2039")),
         (T("Spagna", "Spain"), es_y, es_r), ("USA", None, T("95 anni dall'uscita di ogni opera", "95 years from each work's publication"))]
    if not it:
        r = [r[3], r[5]] + [r[i] for i in (0, 1, 2, 4)]
    return r


def _data_breve(lang, anno):
    return data_l(lang, anno).replace("1° gennaio", "1° gen").replace("1 January", "1 Jan")


def blocco_vicini_n(a, lang):
    """«Altri scrittori liberi dal…» con le foto (grafica nuova); stessi scrittori e stesso ordine di blocco_vicini."""
    q = a["wikidata"]
    it = lang == "it"
    T = (lambda x, y: x) if it else (lambda x, y: y)
    cta = f'<a href="{"/radar/" if it else "/en/radar/"}#/autore/{esc(q)}">{T("Apri nel radar", "Open in the radar")} →</a>'
    if q not in MEMBRI:
        return f'<section class="blk"><span class="m"><b>{T("Nel radar", "In the radar")}</b>{T("Tutti gli autori", "All authors")}</span><div><div class="lnk">{cta}</div></div></section>\n'
    tipo, anno = MEMBRI[q]
    tutti = [x for x in POOL.get((tipo, anno), []) if it or x in EN_OK]
    lista = [x for x in tutti if x != q]
    pa = paesi_moderni(a.get("paesi"))
    c = pa[0] if pa else None
    stessi = [x for x in lista if c and c in paesi_moderni(AUT[x].get("paesi"))[:2]]
    scelti = (stessi + [x for x in lista if x not in stessi])[:6]
    morti = anno - (71 if tipo == "ue" else 81)
    nome = pulisci(a["nome"])
    ordine = (T(f"Prima quelli {del_paese(c)}, poi quelli con la pagina Wikipedia più visitata.", "Same country first, then those whose Wikipedia page gets the most visits.") if stessi
              else T("Prima quelli con la pagina Wikipedia più visitata.", "Those whose Wikipedia page gets the most visits first."))
    if tipo == "ue":
        tit = T(f"Altri scrittori liberi dal 1° gennaio {anno}", f"Other writers free from 1 January {anno}")
        dove = T("in Italia, Francia, Germania e Regno Unito", "in Italy, France, Germany and the UK")
    else:
        tit = T(f"Altri scrittori liberi in Spagna dal 1° gennaio {anno}", f"Other writers free in Spain from 1 January {anno}")
        dove = T("in Spagna", "in Spain")
    lede = T(f"Sono morti nel {morti} come {nome}: {dove} i loro testi originali si possono pubblicare dallo stesso giorno. {ordine}",
             f"They died in {morti}, like {nome}: {dove} their original texts can be published from the same day. {ordine}")
    carte = []
    for x in scelti:
        X = AUT[x]
        nx = pulisci(X["nome"])
        href = f"/autore/{SLUG[x]}/" if it else f"/en/author/{SLUG[x]}/"
        foto = X.get("foto") or {}
        img = (f'<img src="{esc(re.sub(r"width=\d+", "width=400", foto["url"]))}" alt="" loading="lazy">' if foto.get("url")
               else f'<span class="ini-s" aria-hidden="true">{esc(iniziali_nome(nx))}</span>')
        righe = [f"{anno_di(X.get('nascita')) or '?'} – {anno_di(X.get('morte'))}"]
        if it:
            pp = paesi_moderni(X.get("paesi"))
            if pp:
                righe.append(pp[0])
            if X.get("professioni"):
                righe.append(X["professioni"][0])
        else:
            d = re.sub(r"\s*\([^)]*\)\s*$", "", pulisci(X.get("descrizione")))
            if d:
                righe.append(d)
        carte.append(f'<a class="oc" href="{href}"><div class="p">{img}</div><b>{esc(nx)}</b><span>' + "".join(f"<i>{esc(r)}</i>" for r in righe) + "</span></a>")
    tutti_l = ""
    if tipo == "ue":
        dest = f"/pubblico-dominio-{anno}/#autori" if it else f"/en/public-domain-{anno}/#autori"
        tutti_l = f'<a href="{dest}">{T(f"Tutti i {len(tutti)} scrittori del {anno} con una scheda", f"All {len(tutti)} writers of {anno} with a page")} →</a>'
    corpo = (f'<p class="lede">{esc(lede)}</p>\n<div class="others">{"".join(carte)}</div>\n' if carte else "")
    return (f'<section class="blk"><span class="m"><b>{esc(tit)}</b>{T("Stesso anno, stessa data", "Same year, same date")}</span>\n<div>{corpo}'
            f'<div class="lnk">{tutti_l}{cta}</div></div></section>\n')


def scheda_nuova(a, lang, bd):
    """Corpo della pagina autore con la grafica nuova. Stessi dati e stessi testi della scheda di prima, in un altro ordine."""
    it = lang == "it"
    T = (lambda x, y: x) if it else (lambda x, y: y)
    nome = pulisci(a["nome"])
    nasc, D = anno_di(a.get("nascita")), anno_di(a.get("morte"))
    oggi = datetime.date.today()
    o = []
    # percorso in alto
    if a["wikidata"] in MEMBRI and MEMBRI[a["wikidata"]][0] == "ue":
        an = MEMBRI[a["wikidata"]][1]
        su = (f"/pubblico-dominio-{an}/#autori" if it else f"/en/public-domain-{an}/#autori", T(f"← Morti nel {D}", f"← Died in {D}"))
    else:
        su = ("/autore/" if it else "/en/author/", T("← Indice degli autori", "← Author index"))
    prof = ", ".join((a.get("professioni") or [])[:2]) if it else ""
    o.append(f'<div class="crumb"><a href="{su[0]}">{esc(su[1])}</a><span class="m g">{T("Scheda autore", "Author page")}{(" · " + esc(prof)) if prof else ""}</span></div>\n')
    # nome, dati, frase di risposta, ritratto
    parole = nome.split()
    lunga = max((len(w) for w in parole), default=7)
    h1 = "<br>".join(f'<span class="w"><span>{esc(w)}</span></span>' for w in (parole if len(parole) <= 3 else [" ".join(parole[:-1]), parole[-1]]))
    meta = [f"{nasc if nasc else '?'} – {D}"]
    if it and a.get("professioni"):
        meta.append(", ".join(a["professioni"][:2]))
    if it and a.get("paesi"):
        meta.append(", ".join(paesi_moderni(a["paesi"])[:2]))
    if not it:
        dd = re.sub(r"\s*\([^)]*\)\s*$", "", pulisci(a.get("descrizione")))
        if dd:
            meta.append(dd)
    foto = a.get("foto") or {}
    if foto.get("url"):
        ph = f'<div class="ph"><img src="{esc(re.sub(r"width=\d+", "width=800", foto["url"]))}" alt="{T("Ritratto di", "Portrait of")} {esc(nome)}"></div>'
        cap = " · ".join(x for x in (pulisci(foto.get("autore")), pulisci(foto.get("licenza"))) if x)
        pag = f' · <a href="{esc(foto["pagina"])}" rel="noopener">Wikimedia Commons</a>' if foto.get("pagina") else ""
        ph += f'<p class="cap">{T("Foto", "Photo")}: {esc(cap)}{pag}</p>'
    else:
        ph = f'<div class="ph ini" aria-hidden="true">{esc(iniziali_nome(nome))}</div>'
    risp = frase_risposta(a, lang).replace('<p class="sa-risposta">', '<p class="ans">')
    o.append(f'<div class="hd"><div><h1 id="name" style="--k:{lunga}">{h1}</h1>\n<p class="m meta">{esc(" · ".join(meta))}</p>\n{risp}</div>\n<div class="pc">{ph}</div></div>\n')

    # quando è libero
    anno_ue = D + 71
    giorni = (datetime.date(anno_ue, 1, 1) - oggi).days
    dove = T("in Italia", "in the UK and the EU")
    if avviso_alleato(a, lang):
        dove = T("in Francia, Germania e Regno Unito", "in the UK, France and Germany")
    # in grande il conto alla rovescia (Marco, 21/11/2026): la data sta solo nella tabella dei paesi.
    # Se in Europa è già libero ma in Spagna no, si conta verso la Spagna; se è libero dappertutto, «già libero».
    anno_es = D + 81 if D < 1987 else D + 71
    giorni_es = (datetime.date(anno_es, 1, 1) - oggi).days
    if giorni <= 0 and giorni_es > 0:
        dove, giorni, anno_ue_c = T("in Spagna", "in Spain"), giorni_es, anno_es
    else:
        anno_ue_c = anno_ue
    if giorni > 0:
        grande = (f'<span class="m lab-big">{T("Libero", "Free")} {dove} {T("tra", "in")}</span>\n'
                  f'<p class="big"><span id="days" data-y="{anno_ue_c}">{migliaia(giorni, lang)}</span> {T("giorni", "days") if giorni != 1 else T("giorno", "day")}</p>\n')
    else:
        grande = (f'<span class="m lab-big">{T("In Europa e nel Regno Unito", "In Europe and the UK")}</span>\n'
                  f'<p class="big">{T("già libero", "already free")}</p>\n')
    v = a.get("verifica") or {}
    if v.get("esito") == "verificato":
        nomi = [NOMI_FONTE[lang][k] for k in v.get("fonti", {}) if k in NOMI_FONTE[lang]]
        conf = T(f"Anno di morte <b>{D}</b>, confermato da <b>{len(nomi)} fonti</b>: {esc(', '.join(nomi))}.",
                 f"Year of death <b>{D}</b>, confirmed by <b>{len(nomi)} sources</b>: {esc(', '.join(nomi))}.")
        conf = f'<p class="conf">{conf}</p>\n'
    else:
        conf = "".join(x.replace('<p class="sotto">', '<p class="conf">').replace("<p><strong>", '<p class="conf warn"><strong>') for x in blocco_verifica(a, lang))
        conf = f'<p class="conf">{T("Anno di morte", "Year of death")} <b>{D}</b>.</p>\n' + conf
    al = avviso_alleato(a, lang)
    al = f'<div class="all">{al}</div>\n' if al else ""
    corpo_usa = opere_usa_n(a, lang)
    liberi = a.get("_liberi_usa", [])
    righe = []
    primo = True
    for paese, anno, regola in _paesi_riga(a, lang):
        if paese == "USA":
            if liberi:
                el = ", ".join(f"<a href=\"#works\">{esc(t)}</a>" for t in liberi[:4])
                n = len(liberi)
                gia = T(f"Tra le opere principali di {esc(nome)} {'una è già libera' if n == 1 else f'{n} sono già libere'}: {el}; le altre hanno ognuna la sua data, nella tabella <a href=\"#works\">qui sotto ↓</a>",
                        f"Among the main works of {esc(nome)}, {'one is already free' if n == 1 else f'{n} are already free'}: {el}; the others each have their own date, in the table <a href=\"#works\">below ↓</a>")
            elif corpo_usa:
                gia = T('Ogni opera principale ha la sua data, nella tabella <a href="#works">qui sotto ↓</a>', 'Each main work has its own date, in the table <a href="#works">below ↓</a>')
            else:
                gia = T("Per questo autore non abbiamo ancora le date di uscita delle opere.", "We do not have the publication dates of this author's works yet.")
            spieg = T(f"Negli USA non conta la morte dell'autore: ogni libro diventa libero per conto suo, 95 anni dopo la prima uscita. {gia}.",
                      f"In the USA the author's death does not count: each book becomes free on its own, 95 years after first publication. {gia}.")
            righe.append(f'<li class="usa"><span class="c">USA<small>{esc(regola)}</small></span><span class="v">{T("opera per opera", "work by work")}</span><p class="usa-n">{spieg}</p></li>')
            continue
        libero = anno <= oggi.year
        val = (T(f"libero dal {anno}", f"free since {anno}") if libero else _data_breve(lang, anno))
        if paese == T("Italia", "Italy") and al and anno + PROROGA_ALLEATI > oggi.year:
            val, libero = T("da verificare", "to be checked"), False   # paese alleato: niente data, la protezione può durare di più (Marco, 21/11/2026)
        cl = "cur" if primo else ("free" if libero else ("later" if anno > anno_ue else ""))
        primo = False
        righe.append(f'<li class="{cl}"><span class="c">{esc(paese)}<small>{esc(regola)}</small></span><span class="v">{esc(val)}</span></li>')
    o.append(f'<section class="blk" id="dates"><span class="m"><b>{T("Quando è libero", "When it is free")}</b>{T("Paese per paese", "Country by country")}</span>\n<div>'
             f'{grande}{conf}{al}<ul class="ps">{"".join(righe)}</ul>\n<p class="legal">{T("Calcolo indicativo, non è consulenza legale.", "Indicative calculation, not legal advice.")}</p>\n'
             f'<div class="lnk"><a href="{"/radar/" if it else "/en/radar/"}#regole-paesi">{T("Le regole, paese per paese", "The rules, country by country")}</a></div></div></section>\n')

    # chi era
    if bd:
        ln = f' · <a href="{esc(bd["url"])}" rel="noopener">{T("Continua su Wikipedia", "Continue on Wikipedia")}</a>' if bd.get("url") else ""
        o.append(f'<section class="blk"><span class="m"><b>{T("Chi era", "Who they were")}</b>{T("Da Wikipedia", "From Wikipedia")}</span>\n'
                 f'<div><p class="bio">{esc(bd["testo"])}</p>\n<p class="src">{T("Testo da Wikipedia, licenza CC BY-SA", "Text from Wikipedia, licence CC BY-SA")}{ln}</p></div></section>\n')
    # opere principali
    if corpo_usa:
        n_op = a.get("n_opere") or 0
        sotto = (T(f"Le più note delle {migliaia(n_op)} su Wikidata", f"The best known of {migliaia(n_op, lang)} on Wikidata") if n_op > 10
                 else T("Su Wikidata", "On Wikidata"))
        o.append(f'<section class="blk" id="works"><span class="m"><b>{T("Opere principali", "Main works")}</b>{sotto}</span>\n<div>{corpo_usa}</div></section>\n')
    # quanto è già pubblicato
    cat = cataloghi_n(a, lang)
    if cat:
        o.append(f'<section class="blk"><span class="m"><b>{T("Quanto è già pubblicato", "How much is already published")}</b>{T("Nei cataloghi nazionali", "In national catalogues")}</span>\n<div>{cat}</div></section>\n')
    # quanto è conosciuto
    due = []
    for m, campo, etich in ((("it", "visite_it", T("In Italia", "")),) if it else (("en", "visite_en", "In the English-speaking world"),)) + (("int", "pagine_wikipedia", T("Nel mondo", "Worldwide")),):
        if a.get("indice_" + m) is None:
            continue
        val = a.get(campo) or 0
        if m == "int":
            num, sp = str(val), T("lingue con una pagina Wikipedia", "languages with a Wikipedia page")
        elif val:
            num, sp = migliaia(val, lang), T("visite su Wikipedia in 12 mesi", "Wikipedia views in 12 months")
        else:
            num, sp = "—", T("nessuna pagina in italiano", "no page in English")
        rg = RANGHI.get((a["wikidata"], m))
        rk = f'<span class="rk">{T(f"{rg[0]}° su {rg[1]}", f"#{rg[0]} of {rg[1]}")}</span>' if rg else ""
        due.append(f'<div><span class="m g">{esc(etich)}</span><div class="n">{num}</div><p>{esc(sp)}</p>{rk}</div>')
    if due:
        o.append(f'<section class="blk"><span class="m"><b>{T("Quanto è conosciuto", "How well known")}</b>{T("Visite a Wikipedia, non vendite", "Wikipedia views, not sales")}</span>\n<div><div class="two">{"".join(due)}</div><p class="src">{T("Misura la curiosità per l’autore (visite alle pagine Wikipedia), non le vendite dei suoi libri.", "Measures curiosity about the author (Wikipedia page views), not sales of their books.")}</p></div></section>\n')
    # risposte brevi
    faq = domande(a, lang)
    ill = [x for x in (a.get("illustratori") or []) if x.get("nome")]
    r_ill = T("No, non automaticamente. Le date di questa pagina valgono per i testi originali. Illustrazioni e traduzioni hanno diritti propri, che durano 70 anni dalla morte dell'illustratore o del traduttore: un libro può avere il testo libero e i disegni ancora protetti.",
              "Not automatically. The dates on this page apply to the original texts. Illustrations and translations have their own rights, lasting 70 years after the death of the illustrator or translator: a book can have a free text and still-protected drawings.")
    faq.append((T("Traduzioni e illustrazioni sono libere anche loro?", "Are translations and illustrations free too?"), r_ill))
    li_ill = ""
    if ill:
        rr = []
        for x in ill:
            if x.get("morte"):
                quando = T(f"libere nell'UE dal {data_l(lang, x['morte'] + 71)}", f"free in the EU from {data_l(lang, x['morte'] + 71)}")
                rr.append(T(f"{x['opera']}: illustrazioni di {x['nome']} (morto nel {x['morte']}), {quando}", f"{x['opera']}: illustrations by {x['nome']} (died {x['morte']}), {quando}"))
            else:
                rr.append(T(f"{x['opera']}: illustrazioni di {x['nome']}, data di morte non nota", f"{x['opera']}: illustrations by {x['nome']}, year of death unknown"))
        li_ill = "<ul>" + "".join(f"<li>{esc(r)}</li>" for r in rr) + "</ul>"
    acc = []
    for i, (q, r_) in enumerate(faq):
        extra = li_ill if i == len(faq) - 1 else ""
        acc.append(f'<div class="acc"><button type="button">{esc(q)}<span>[+]</span></button><div class="bd"><p>{esc(r_)}</p>{extra}</div></div>')
    o.append(f'<section class="blk"><span class="m"><b>{T("Le risposte brevi", "Short answers")}</b>{T("Domande", "Questions")}</span>\n<div>{"".join(acc)}</div></section>\n')
    fq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r_}} for q, r_ in faq]}
    o.append('<script type="application/ld+json">' + json.dumps(fq, ensure_ascii=False).replace("</", "<\\/") + "</script>\n")
    # altri scrittori
    o.append(blocco_vicini_n(a, lang))
    return "".join(o)


def opere_usa_n(a, lang):
    """Tabella delle opere principali (titolo, anno, stato negli USA) con le note dei coautori come rimandi numerati."""
    it = lang == "it"
    T = (lambda x, y: x) if it else (lambda x, y: y)
    note = note_coautori(a, lang)
    righe, liberi, usate = [], [], []
    for o in a.get("opere", [])[:10]:
        t = o.get("titolo") if it else o.get("titolo_en") or o.get("titolo")
        if not t:
            continue
        st, y = stato_usa(a, o)
        if st == "libero":
            et, cl = T(f"libero dal {y}", f"free since {y}"), "free"
            liberi.append(t)
        elif st == "dal":
            et, cl = T(f"dal {y}", f"from {y}"), ""
        elif st == "verifica":
            et, cl = T("da verificare", "to be checked"), "ver"
        else:
            et, cl = T("anno non noto", "year unknown"), "ver"
        sup = ""
        for n in note:
            if n.startswith(f"«{t}»") and n not in usate:
                usate.append(n)
                sup = f'<sup data-n="{len(usate)}">{len(usate)}</sup>'
                break
        anno = o.get("anno") if isinstance(o.get("anno"), int) else ""
        righe.append(f'<li><span class="t">{esc(t)}{sup}</span><span class="y">{anno}</span><span class="u {cl}">{esc(et)}</span></li>')
    a["_liberi_usa"] = liberi
    if not righe:
        return ""
    for n in note:
        if n not in usate:
            usate.append(n)
    notes = "".join(f'<li id="nt{i}"><b>{i}</b>{esc(n)}</li>' for i, n in enumerate(usate, 1))
    nota = T("Negli USA conta l'anno di uscita di ogni opera (95 anni). «Libero» solo se l'anno di Wikidata è confermato da una seconda fonte (Duke, Open Library, Library of Congress); altrimenti «da verificare». Le date future usano l'anno di Wikidata.",
             "In the USA what counts is each work's year of publication (95 years). «Free» only when the Wikidata year is confirmed by a second source (Duke, Open Library, Library of Congress); otherwise «to be checked». Future dates use the Wikidata year.")
    return (f'<div class="oph m"><span>{T("Titolo", "Title")}</span><span>{T("Anno", "Year")}</span><span>{T("Negli USA", "In the USA")}</span></div>\n'
            f'<ul class="op" id="op">{"".join(righe)}</ul>\n' + (f'<ol class="notes">{notes}</ol>\n' if notes else "") + f'<p class="opn">{esc(nota)}</p>\n')


def cataloghi_n(a, lang):
    """Registrazioni nei cataloghi nazionali come barre (in tutto e dal 2000), con la spiegazione nel [+]."""
    it = lang == "it"
    T = (lambda x, y: x) if it else (lambda x, y: y)
    tr = a.get("traduzioni") or {}
    nomi = {"sbn_it": (T("Italia", "Italy"), "SBN"), "bnf_fr": (T("Francia", "France"), "BnF"), "bne_es": (T("Spagna", "Spain"), "BNE"),
            "bl_en": (T("Regno Unito", "United Kingdom"), "British Library"), "loc_en": ("USA", "Library of Congress")}
    mio = "sbn_it" if it else "bl_en"
    righe, sospesi = [], []
    for k in ("bnf_fr", "sbn_it", "bl_en", "loc_en", "bne_es"):
        g = tr.get(k)
        if not g or not g.get("trovato"):
            continue
        if g.get("sospeso_manuale") or g.get("stato") == "da_verificare" or problemi_conteggio(g, datetime.date.today().year):
            sospesi.append(nomi[k][0])
            continue
        righe.append((k, g.get("edizioni", 0), g.get("dal_2000", 0)))
    if not righe and not sospesi:
        return ""
    righe.sort(key=lambda x: -x[1])
    mx = max([x[1] for x in righe] or [1]) or 1
    html_r = "".join(
        f'<div class="cr{" cur" if k == mio else ""}"><span class="l">{esc(nomi[k][0])}<small>{esc(nomi[k][1])}</small></span>'
        f'<span class="b"><i class="n" style="width:{e / mx * 100:.1f}%"></i><i style="width:{d / mx * 100:.1f}%"></i></span>'
        f'<span class="v">{migliaia(e, lang)} <span>· {migliaia(d, lang)} {T("dal 2000", "since 2000")}</span></span></div>' for k, e, d in righe)
    leg = (f'<div class="cleg"><span><i style="background:var(--ink)"></i>{T("registrazioni in tutto", "records in total")}</span>'
           f'<span><i style="background:var(--box)"></i>{T("di cui dal 2000", "of which since 2000")}</span></div>') if righe else ""
    g = tr.get(mio) or {}
    ult = (T(f" Nel catalogo {nomi[mio][1]}, la più recente con anno certo è del {g['ultimo']}.", f" In the {nomi[mio][1]} catalogue, the latest with a certain year is from {g['ultimo']}.")
           if g.get("ultimo") and mio in [x[0] for x in righe] else "")
    met = ""
    if it and g.get("metodo") == "nome":
        met = " Autore riconosciuto nel catalogo SBN solo dal nome: il conteggio può essere impreciso."
    elif it and g.get("metodo") == "nome_con_prova":
        met = " Autore riconosciuto nel catalogo SBN dal nome con una prova in più (anni di nascita e morte, un titolo o un cognome unico nel catalogo), non da un codice."
    cosa = T("La scheda con cui la biblioteca descrive una pubblicazione. Di solito ce n'è una per ogni edizione o ristampa, quindi un libro uscito cinque volte conta cinque. Non sono copie vendute né titoli diversi. Comprendono tutte le pubblicazioni collegate alla persona, anche quelle in cui ha collaborato (traduzioni, curatele, prefazioni), non solo i libri scritti da lei: è una misura di quanto è presente nel catalogo.",
             "The entry a library uses to describe a publication. There is usually one for each edition or reprint, so a book published five times counts five. Records are not copies sold, nor different titles. They include every publication linked to the person, including those they contributed to (translations, editing, prefaces), not only books they wrote: it measures how present they are in the catalogue.")
    cosa = T("Dicono quanto un autore è già pubblicato in ogni paese. Che cos’è una registrazione: ", "They show how much an author is already published in each country. What a record is: ") + cosa
    if it and "sbn_it" in [x[0] for x in righe]:
        cosa += " Nel catalogo SBN: registrazioni bibliografiche in italiano collegate all'autore, comprese ristampe e antologie."
    if not it and "bl_en" in [x[0] for x in righe]:
        cosa += " In the British Library catalogue the author is searched by surname and years of birth and death; a record counts only if surname and years belong to the same person. Some records catalogued differently may be missed."
    sosp = (f'<p class="cat-n">{esc(T("Dati in verifica per " + ", ".join(sospesi) + ": i numeri del catalogo non sono ancora sicuri, quindi non li mostriamo.", "Data under review for " + ", ".join(sospesi) + ": the catalogue figures are not yet reliable, so we do not show them."))}</p>' if sospesi else "")
    return (f'<div class="cat" id="cat">{html_r}</div>{leg}{sosp}'
            f'<div class="why"><button type="button">{T("Che cos’è una registrazione", "What a record is")} <span>[+]</span></button><p>{esc(cosa + ult + met)}</p></div>\n')


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
        altra = (f'<a href="{url_pagina("en" if it else "it", slug)}" hreflang="{"en" if it else "it"}">{"EN" if it else "IT"}</a>')
    # grafica nuova (21/11/2026): testata, corpo e piede della scheda «Indice»
    cnt = (f"{nome} · libero dal {data_l(lang, D + 71)}" if it else f"{nome} · free from {data_l(lang, D + 71)}")
    out = [testa_scheda(lang, esc(titolo), esc(descr), url, alterne(lang, slug) if ha_altra else "", jsonld, altra, cnt)
           .replace("@@MARCHIO_S@@", marchio_html(56).replace('<span class="pdr" style="--w:56px">', "").rsplit("</span>", 1)[0])]
    out.append(scheda_nuova(a, lang, bd))
    out.append(piede_scheda(lang))
    return "".join(out)


CSS_ANNO = (Path(__file__).resolve().parent / "stile_anno.css").read_text()
CSS_INDICE = (Path(__file__).resolve().parent / "stile_indice.css").read_text()


def pagina_indice(voci, lang):
    """Indice degli autori, grafica «Indice» (mockup rdr-indice-autori.html, approvato da Marco il 21/11/2026).
    L'elenco è tutto scritto nella pagina (Google lo legge); i due filtri, paese e anno, nascondono solo le voci."""
    it = lang == "it"
    T = (lambda x, y: x) if it else (lambda x, y: y)
    url = url_pagina(lang)
    titolo = "Indice degli autori in pubblico dominio · Public Domain Radar" if it else "Index of authors entering the public domain · Public Domain Radar"
    descr = (f"{len(voci)} autori con la data di pubblico dominio paese per paese (UE, Italia, Francia, Germania, Spagna, Regno Unito), da dati aperti." if it else
             f"{len(voci)} authors with the public-domain date country by country (EU, Italy, France, Germany, Spain, UK), from open data.")
    gruppi = {}
    for nome, slug, anni in voci:
        k = unicodedata.normalize("NFD", nome[:1] or "#")[:1].upper()
        if not ("A" <= k <= "Z"):
            k = "#"
        gruppi.setdefault(k, []).append((nome, slug, anni))
    lettere = "".join(f'<a href="#g-{"0" if k == "#" else k}">{k}</a>' for k in gruppi)
    A = ANNO_PROSSIMO
    paesi = [("tutti", T("Tutti", "All")), ("it", T("Italia", "Italy")), ("fr", T("Francia", "France")), ("de", T("Germania", "Germany")),
             ("uk", T("Regno Unito", "United Kingdom")), ("es", T("Spagna", "Spain"))]
    anni_f = [("tutti", T("Tutti gli anni", "All years"))] + [(str(y), T(f"1° gennaio {y}", f"1 January {y}")) for y in (A, A + 1)]
    sel = lambda nid, op: f'<select id="{nid}">' + "".join(f'<option value="{v}">{esc(t)}</option>' for v, t in op) + "</select>"
    lead_n = (f"{len(voci)} autori con una pagina dedicata: biografia, opere e data di pubblico dominio paese per paese." if it else
              f"{len(voci)} authors with a dedicated page: biography, Italian editions and the public-domain date country by country.")
    out = [testa_scheda(lang, esc(titolo), esc(descr), url, "", "", f'<a href="{T("/en/author/", "/autore/")}" hreflang="{T("en", "it")}">{T("EN", "IT")}</a>', "", og_tipo="website", css_extra=CSS_INDICE, main_cls="idx")
           .replace("@@MARCHIO_S@@", marchio_html(56).replace('<span class="pdr" style="--w:56px">', "").rsplit("</span>", 1)[0]),
           '<p class="m" style="color:var(--redt)">Public Domain Radar</p>\n',
           f'<h1>{T("Indice <br>degli autori", "Index <br>of authors")}</h1>\n',
           f'<p class="lead" id="lead">{lead_n}</p>\n',
           f'<div class="bar"><div class="fil"><label>{T("Paese", "Country")} {sel("sp", paesi)}</label>'
           f'<label>{T("Libero dal", "Free from")} {sel("sa", anni_f)}</label></div><nav class="let" id="let" aria-label="{T("Lettere", "Letters")}">{lettere}</nav></div>\n']
    for k, g in gruppi.items():
        li = "".join(f'<li data-m="{esc(anni[-4:])}"><a href="/{PERCORSO[lang]}/{slug}/">{esc(nome)}<span>{esc(anni.replace(" – ", "–"))}</span></a></li>' for nome, slug, anni in g)
        out.append(f'<section class="grp" id="g-{"0" if k == "#" else k}"><h2>{k}</h2><ul class="names">{li}</ul></section>\n')
    out.append(f'<p class="vuoto" id="vuoto">{T("Nessun autore con questi filtri.", "No authors with these filters.")}</p>\n')
    out.append(f'<p class="note">{T("Ogni scheda ha biografia, opere e data di pubblico dominio paese per paese. Dati indicativi, non è consulenza legale.", "Each page has the biography, works and public-domain date country by country. Indicative data, not legal advice.")}</p>\n')
    js = """<script>
(()=>{const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
// In Italia, Francia, Germania e Regno Unito valgono 70 anni dalla morte (libero il 1° gennaio dell'anno morte+71), in Spagna 80 per chi è morto prima del 1987 (morte+81)
const ANNI=[@@A@@,@@B@@], TOT=$$('.names li').length;
let fp='tutti',fa='tutti';
const dopo=p=>p==='es'?[81]:p==='tutti'?[71,81]:[71];
function passa(m){ if(fp==='tutti'&&fa==='tutti') return true; const an=fa==='tutti'?ANNI:[+fa]; return an.some(y=>dopo(fp).some(k=>m===y-k)); }
function render(){ let n=0;
  $$('.grp').forEach(g=>{ let v=0; g.querySelectorAll('li').forEach(li=>{ const ok=passa(+li.dataset.m); li.classList.toggle('no',!ok); if(ok) v++; }); g.classList.toggle('no',!v); n+=v;
    const a=$('#let a[href="#'+g.id+'"]'); if(a) a.style.display=v?'':'none'; });
  $('#lead').textContent=@@LEAD@@;
  $('#vuoto').classList.toggle('on',!n); }
$('#sp').onchange=e=>{fp=e.target.value;render();}; $('#sa').onchange=e=>{fa=e.target.value;render();};
})();
</script>
"""
    lead_js = ("`${n} autori con una pagina dedicata${n<TOT?' tra i '+TOT:''}: biografia, opere e data di pubblico dominio paese per paese.`" if it else
               "`${n} authors with a dedicated page${n<TOT?' out of '+TOT:''}: biography, Italian editions and the public-domain date country by country.`")
    out.append(js.replace("@@A@@", str(A)).replace("@@B@@", str(A + 1)).replace("@@LEAD@@", lead_js))
    out.append(piede_scheda(lang))
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
    f = RADICE / "radar" / "index.html"   # il radar sta su /radar/ dal 21/11/2026; la home è il frontespizio (scripts/home.py)
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
    s = (RADICE / "radar" / "index.html").read_text(encoding="utf-8")
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
    s = sostituisci(s, r'<link rel="canonical" href="https://publicdomainradar.com/radar/">', '<link rel="canonical" href="https://publicdomainradar.com/en/radar/">')
    s = sostituisci(s, r'<meta property="og:url" content="https://publicdomainradar.com/radar/">', '<meta property="og:url" content="https://publicdomainradar.com/en/radar/">')
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
    (RADICE / "en" / "radar").mkdir(parents=True, exist_ok=True)
    (RADICE / "en" / "radar" / "index.html").write_text(s, encoding="utf-8")


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
.al-nav{display:flex;flex-wrap:wrap;gap:4px;margin:18px 0 22px}
.al-nav a{font-family:var(--mono);font-size:13px;width:30px;height:30px;display:flex;align-items:center;justify-content:center;border:1.5px solid var(--ink);color:var(--ink);text-decoration:none}
.al-nav a:hover{background:var(--ink);color:var(--carta)}
.al{columns:2;column-gap:18px}
@media(min-width:960px){.al{columns:3}}
.al-g{break-inside:avoid;margin:0 0 18px}
.al-l{font-family:var(--display);font-weight:900;font-size:30px;line-height:1;margin:0 0 6px;border-bottom:2px solid var(--ink);padding-bottom:4px}
.al-g ul{list-style:none;margin:0;padding:0}
.al-g li{margin:0;padding:6px 0;border-bottom:1px solid var(--riquadro);display:flex;flex-direction:column;line-height:1.3}
.al-g li a{color:var(--ink);font-weight:600;text-decoration:none}
.al-g li a:hover{color:var(--vermiglio-testo);text-decoration:underline}
.al-g li span.m{font-size:inherit;margin:0;display:inline}
.al-g li span{font-family:var(--mono);font-size:11px;color:var(--muto);margin-top:2px}
@media(max-width:639px){.al-g li{padding:5px 0}.al-g li a{font-size:14px}.al-g li span{font-size:10px}.al-g li span.m{display:none}.al-l{font-size:24px}}
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


# --- collegamenti interni (mockup approvato il 21/11/2026): «Altri scrittori liberi dal…» nelle schede,
# elenco di tutti gli scrittori con una scheda nella pagina dell'anno. Riempiti in main().
MEMBRI = {}   # wikidata -> ("ue"|"es", anno in cui diventa libero)
POOL = {}     # ("ue"|"es", anno) -> wikidata degli scrittori con una scheda, dal più letto
AUT = {}      # wikidata -> dati dell'autore
SLUG = {}     # wikidata -> indirizzo della scheda
EN_OK = set()
_MASCHILI_IN_A = {"Canada", "Kenya", "Guatemala", "Nicaragua", "Venezuela", "Panama", "Ghana", "Botswana", "Ruanda", "Malawi"}


def del_paese(p):
    """«del Regno Unito», «dell'India», «della Francia», «degli Stati Uniti»."""
    if p.split()[0] in ("Stati", "Paesi", "Emirati"):
        return "degli " + p
    if p[0] in "AEIOUÀÈÉÌÒÙ":
        return "dell'" + p
    if p.endswith("a") and p not in _MASCHILI_IN_A:
        return "della " + p
    return "del " + p


def _tessera_vicino(q, lang):
    x = AUT[q]
    it = lang == "it"
    nome = pulisci(x["nome"])
    href = f"/autore/{SLUG[q]}/" if it else f"/en/author/{SLUG[q]}/"
    foto = x.get("foto") or {}
    if foto.get("url"):
        ft = f'<span class="vf"><img src="{esc(re.sub(r"width=\d+", "width=160", foto["url"]))}" alt="" loading="lazy"></span>'
    else:
        ft = f'<span class="vf" aria-hidden="true"><span class="vi">{esc(iniziali_nome(nome))}</span></span>'
    sotto = f"{anno_di(x.get('nascita')) or '?'} – {anno_di(x.get('morte'))}"
    if it:
        pa = paesi_moderni(x.get("paesi"))
        sotto += f" · {pa[0]}" if pa else ""
        m = (x.get("professioni") or [""])[0]
    else:
        m = re.sub(r"\s*\([^)]*\)\s*$", "", pulisci(x.get("descrizione")))
    vm = f'<span class="vm">{esc(m)}</span>' if m else ""
    return f'<li><a href="{href}">{ft}<span class="vt"><b>{esc(nome)}</b><span>{esc(sotto)}</span>{vm}</span></a></li>'


def blocco_vicini(a, lang):
    """Sei scrittori che diventano liberi lo stesso giorno: prima dello stesso paese, poi per visite alla pagina Wikipedia."""
    q = a["wikidata"]
    if q not in MEMBRI:
        return ""
    it = lang == "it"
    T = (lambda x, y: x) if it else (lambda x, y: y)
    tipo, anno = MEMBRI[q]
    tutti = [x for x in POOL.get((tipo, anno), []) if it or x in EN_OK]
    lista = [x for x in tutti if x != q]
    if not lista:
        return ""
    pa = paesi_moderni(a.get("paesi"))
    c = pa[0] if pa else None
    stessi = [x for x in lista if c and c in paesi_moderni(AUT[x].get("paesi"))[:2]]
    scelti = (stessi + [x for x in lista if x not in stessi])[:6]
    morti = anno - (71 if tipo == "ue" else 81)
    nome = pulisci(a["nome"])
    if stessi:
        ordine = T(f"Prima quelli {del_paese(c)}, poi quelli con la pagina Wikipedia più visitata.", "Same country first, then those whose Wikipedia page gets the most visits.")
    else:
        ordine = T("Prima quelli con la pagina Wikipedia più visitata.", "Those whose Wikipedia page gets the most visits first.")
    if tipo == "ue":
        tit = T(f"Altri scrittori liberi dal 1° gennaio {anno}", f"Other writers free from 1 January {anno}")
        dove = T("in Italia, Francia, Germania e Regno Unito", "in Italy, France, Germany and the UK")
    else:
        tit = T(f"Altri scrittori liberi in Spagna dal 1° gennaio {anno}", f"Other writers free in Spain from 1 January {anno}")
        dove = T("in Spagna", "in Spain")
    testo = T(f"Sono morti nel {morti} come {nome}: {dove} i loro testi originali si possono pubblicare dallo stesso giorno. {ordine}",
              f"They died in {morti}, like {nome}: {dove} their original texts can be published from the same day. {ordine}")
    o = [f'<section class="sa-sez sa-vicini">\n<p class="sa-occ">{T("Stesso anno, stessa data", "Same year, same date")}</p>\n'
         f'<h2>{tit}</h2>\n<p class="sa-testo">{esc(testo)}</p>\n<ul class="vic">'
         + "".join(_tessera_vicino(x, lang) for x in scelti) + "</ul>\n"]
    if tipo == "ue":
        dest = f"/pubblico-dominio-{anno}/#autori" if it else f"/en/public-domain-{anno}/#autori"
        o.append(f'<p class="vic-tutti"><a href="{dest}">{T(f"Tutti i {len(tutti)} scrittori del {anno} con una scheda →", f"All {len(tutti)} writers of {anno} with a page →")}</a></p>\n')
    o.append("</section>\n")
    return "".join(o)


def _cognome(nome):
    parole = pulisci(nome).replace(",", " ").split()
    return slug_base(parole[-1]) if parole else ""


def elenco_az(aut, lang, morti):
    """Sezione della pagina dell'anno: tutti gli scrittori con una scheda, per cognome, con le lettere per saltare."""
    it = lang == "it"
    T = (lambda x, y: x) if it else (lambda x, y: y)
    pag = "pagina" if it else "pagina_en"
    gruppi = {}
    for a in sorted(aut, key=lambda a: (_cognome(a["nome"]), slug_base(a["nome"]))):
        k = _cognome(a["nome"])[:1].upper()
        gruppi.setdefault(k if k.isalpha() else "#", []).append(a)
    o = [f'<section class="pd-sez" id="autori"><div class="pd-in">\n<p class="pd-et">{T("Europa e Regno Unito · elenco completo", "Europe and the UK · full list")}</p>\n'
         f'<h2>{T("Tutti gli scrittori con una scheda", "All the writers with a page")}</h2>\n'
         f'<p class="lead">{T(f"I {len(aut)} scrittori morti nel {morti} per cui abbiamo una scheda, in ordine di cognome. Ogni scheda ha la data paese per paese, le opere principali e le fonti.", f"The {len(aut)} writers who died in {morti} that have a page, by surname. Each page has the date country by country, the main works and the sources.")}</p>\n'
         f'<nav class="al-nav" aria-label="{T("Lettere", "Letters")}">' + "".join(f'<a href="#al-{k}">{k}</a>' for k in gruppi) + '</nav>\n<div class="al">']
    for k, lista in gruppi.items():
        o.append(f'<div class="al-g" id="al-{k}"><p class="al-l">{k}</p><ul>')
        for a in lista:
            href = f"/autore/{a[pag]}/" if it else f"/en/author/{a[pag]}/"
            m = (a.get("professioni") or [""])[0] if it else re.sub(r"\s*\([^)]*\)\s*$", "", pulisci(a.get("descrizione")))
            mm = f'<span class="m"> · {esc(m)}</span>' if m else ""
            o.append(f'<li><a href="{href}">{esc(pulisci(a["nome"]))}</a><span>{anno_di(a.get("nascita")) or "?"} – {anno_di(a["morte"])}{mm}</span></li>')
        o.append("</ul></div>")
    o.append("</div>\n</div></section>\n")
    return "".join(o)


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
    app = "/radar/" if it else "/en/radar/"
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
    altra = (f'<a href="/en/public-domain-{anno}/" hreflang="en">EN</a>' if it else f'<a href="/pubblico-dominio-{anno}/" hreflang="it">IT</a>')
    gg_ = max(0, (datetime.date.fromisoformat(libero) - oggi).days)
    n_ = lambda x: migliaia(x, lang)
    data_l_ = T(f"1° gennaio {anno}", f"1 January {anno}")
    cnt_html = (f'<span id="cnt"><i class="lg">{data_l_} · </i><i class="sm">{T(f"1° gen {anno}", f"1 Jan {anno}")} · </i>'
                f'{T("tra", "in")} <b id="pd-giorni" data-d="{libero}" style="font-weight:inherit">{migliaia(gg_, lang)}</b> {T("giorni", "days")}</span>') if gg_ > 0 else \
               f'<span id="cnt">{data_l_}</span>'
    testa = testa_scheda(lang, esc(titolo), esc(descr), url, alt, jsonld, altra, "@@CNT@@", og_tipo="website",
                         css_extra=CSS_ANNO, main_cls="pdd", body_cls="pdd-b")
    testa = testa.replace('<div class="cnt">@@CNT@@</div>', f'<div class="cnt">{cnt_html}</div>')
    out = [testa.replace("@@MARCHIO_S@@", marchio_html(56).replace('<span class="pdr" style="--w:56px">', "").rsplit("</span>", 1)[0])]

    # 1. apertura
    w = lambda t: f'<span class="w"><span>{t}</span></span>'
    out.append(f"""<section class="open">
<p class="m k">Public Domain Day · {data_l_}</p>
<h1 class="h1">{w(T("Cosa diventa", "What becomes"))}<br>{w(T("libero", "free"))} {w(T(f"nel {anno}", f"in {anno}"))}</h1>
<p class="say" id="say">{T(f"Il 1° gennaio {anno} scadono i diritti di centinaia di scrittori e libri. Chi, dove e con quali cautele, da dati aperti e con le fonti.",
                   f"On 1 January {anno} copyright expires for hundreds of writers and books. Who, where and with what caveats, from open data with sources.")}</p>
</section>
""")
    nums = [(n_ue, T("scrittori liberi in Italia, Francia, Germania e Regno Unito", "writers free in Italy, France, Germany and the UK"),
             T(f"morti nel {morti}", f"died in {morti}"), "#ix1" if aut else f"{app}#/{anno}")]
    if n_es:
        nums.append((n_es, T("scrittori liberi in Spagna", "writers free in Spain"), T(f"morti nel {morti_es}", f"died in {morti_es}"), f"{app}#/{anno}"))
    if n_us:
        nums.append((n_us, T("libri liberi negli USA", "books free in the USA"),
                     T(f"pubblicati nel {pub} · {n_us_ok} con l'anno confermato", f"published in {pub} · {n_us_ok} with the year confirmed"), "#ix2"))
    out.append('<div class="nums">' + "".join(f'<a href="{h}"><span class="n">{n_(x)}</span><span class="c">{esc(c)}</span><span class="m">{esc(m)}</span></a>'
                                              for x, c, m, h in nums) + "</div>\n")

    # 2. i nomi più attesi
    if aut:
        out.append(f'<section class="sec ix" id="ix1">\n<div class="sh m"><h2>{T("I nomi più attesi", "The most awaited names")}</h2><span>{T(f"Europa e Regno Unito · morti nel {morti}", f"Europe and the UK · died in {morti}")}</span></div>\n'
                   f'<p class="lede">{T(f"Gli scrittori morti nel {morti}, in ordine di visite alla loro pagina Wikipedia negli ultimi 12 mesi (in italiano, inglese, francese, tedesco e spagnolo): misura quanto sono conosciuti oggi, non quanto si vendono i loro libri. Dal 1° gennaio i loro testi originali si possono pubblicare senza permesso in Italia, Francia, Germania e Regno Unito.", f"The writers who died in {morti}, ranked by visits to their Wikipedia page over the last 12 months (in Italian, English, French, German and Spanish): it measures how well known they are today, not how well their books sell. From 1 January their original texts can be published without permission in Italy, France, Germany and the UK.")}</p>\n'
                   '<ol class="rows" style="margin-top:28px">\n')
        crediti = []
        for k, a in enumerate(aut[:8]):
            nome = pulisci(a["nome"])
            href = f"/autore/{a['pagina']}/" if it else f"/en/author/{a['pagina_en']}/"
            foto = a.get("foto") or {}
            df = ""
            if foto.get("url"):
                df = ' data-f="' + esc(re.sub(r"width=\d+", "width=480", foto["url"])) + '"'
                chi_f = re.sub(r"^(.+?)\1$", r"\1", pulisci(foto.get("autore")))   # Commons a volte ripete il nome due volte
                chi_f = "" if len(chi_f) > 60 else chi_f
                crediti.append(f'{esc(nome)}: <a href="{esc(foto.get("pagina", ""))}" rel="noopener">{esc(" · ".join(x for x in (chi_f, pulisci(foto.get("licenza"))) if x) or "Wikimedia Commons")}</a>')
            if it:
                ruolo = (a.get("professioni") or [""])[0]
                sotto = f"{anno_di(a.get('nascita')) or '?'} – {_data_lunga(a['morte'], 'it')}"
            else:
                ruolo = re.sub(r"\s*\([^)]*\)\s*$", "", pulisci(a.get("descrizione")))
                sotto = f"died {_data_lunga(a['morte'], 'en')}"
            mt = (esc(ruolo) + "<br>" if ruolo else "") + esc(sotto)
            out.append(f'<li class="row"{df} data-i="{esc(iniziali_nome(nome))}"><span class="no">{k + 1:02d}</span><span class="nm"><a href="{href}">{esc(nome)}</a></span><span class="mt">{mt}</span></li>\n')
        out.append(f'</ol>\n<a href="#autori" class="more">{T(f"Tutti i {len(aut)} scrittori con una scheda →", f"All {len(aut)} writers with a page →")}</a>'
                   f'<a href="{app}#/{anno}" class="more">{T(f"Tutti gli {n_(n_ue)} nel radar →", f"All {n_(n_ue)} in the radar →")}</a>\n')
        if crediti:
            out.append(f'<p class="cred">{T("Ritratti da Wikimedia Commons", "Portraits from Wikimedia Commons")} — {" · ".join(crediti)}</p>\n')
        out.append("</section>\n")

    # 3. i libri USA
    if opere:
        out.append(f'<section class="sec ix" id="ix2">\n<div class="sh m"><h2>{T(f"I libri del {pub}", f"The books of {pub}")}</h2><span>{T("Stati Uniti · 95 anni dall’uscita", "United States · 95 years from publication")}</span></div>\n'
                   f'<p class="lede">{T(f"Negli USA conta l&#39;anno di pubblicazione: il 1° gennaio diventano liberi i libri usciti nel {pub}. Diciamo «confermato» solo quando l&#39;anno è confermato da una fonte diversa da Wikidata (registro del copyright americano, biblioteche nazionali, Open Library, Library of Congress); per gli altri scriviamo «anno da confermare». In ordine di visite alla pagina del libro su Wikipedia in inglese, negli ultimi 12 mesi.", f"In the USA what counts is the year of publication: on 1 January books published in {pub} become free. We say «confirmed» only when a source other than Wikidata confirms the year (the US copyright register, national libraries, Open Library, Library of Congress); for the others we say «year to be confirmed». Ranked by visits to the book\'s English Wikipedia page over the last 12 months.")}</p>\n'
                   '<ol class="rows" style="margin-top:28px">\n')
        crediti_us, visti_us = [], set()
        for k, o in enumerate(opere[:12]):
            t = (o.get("titolo_it") or o["titolo"]) if it else o["titolo"]
            chi = ", ".join(pulisci(a["nome"]) for a in o.get("autori", [])) or "—"
            v_ = verificati.get(o["qid"]) or ["nd"]
            if v_[0] == "ok":
                badge = esc(T(f"{pub} confermato", f"{pub} confirmed"))
            elif v_[0] == "parziale":   # uscito a puntate fino a un anno dopo: libero per intero più tardi
                badge = f'<span class="tbd">{esc(T(f"a puntate fino al {v_[1]}", f"serialized until {v_[1]}"))}</span>'
            else:
                badge = f'<span class="tbd">{esc(T("anno da confermare", "year to be confirmed"))}</span>'
            # ritratto del primo autore che ne ha uno (le copertine tipografiche non aggiungevano nulla: Marco, 21/11/2026)
            fa = next((a for a in o.get("autori", []) if (a.get("foto") or {}).get("url")), None)
            df = ""
            if fa:
                df = ' data-f="' + esc(fa["foto"]["url"]) + '"'
                if fa["qid"] not in visti_us:
                    visti_us.add(fa["qid"])
                    chi_f = re.sub(r"^(.+?)\1$", r"\1", pulisci(fa["foto"].get("autore")))
                    chi_f = "" if len(chi_f) > 60 else chi_f
                    crediti_us.append(f'{esc(pulisci(fa["nome"]))}: <a href="{esc(fa["foto"].get("pagina", ""))}" rel="noopener">{esc(" · ".join(x for x in (chi_f, pulisci(fa["foto"].get("licenza"))) if x) or "Wikimedia Commons")}</a>')
            out.append(f'<li class="row"{df} data-i="{esc(iniziali_nome(chi.split(", ")[0]))}"><span class="no">{k + 1:02d}</span>'
                       f'<span class="nm"><a href="{app}#/opera/{o["qid"]}">{esc(t)}</a></span><span class="mt">{esc(chi)}<br>{badge}</span></li>\n')
        out.append(f'</ol>\n<a href="{app}#/us/{anno}" class="more">{T(f"Tutti i {n_us} libri: {n_us_ok} confermati, {n_us - n_us_ok} da confermare →", f"All {n_us} books: {n_us_ok} confirmed, {n_us - n_us_ok} to be confirmed →")}</a>\n')
        if crediti_us:
            out.append(f'<p class="cred">{T("Ritratti degli autori da Wikimedia Commons", "Authors\' portraits from Wikimedia Commons")} — {" · ".join(crediti_us)}</p>\n')
        out.append("</section>\n")

    # 4. paese per paese
    righe = [
        (T("Italia", "Italy"), T(f"Autori morti nel {morti}", f"Authors who died in {morti}"),
         T("70 anni dalla morte. Per gli autori di paesi alleati nella Seconda guerra mondiale va verificato.", "70 years after death. For authors from Allied countries in the Second World War it must be checked."),
         f"{app}#/{anno}", T(f"{n_(n_ue)} scrittori →", f"{n_(n_ue)} writers →"), ""),
        (T("Francia", "France"), T(f"Autori morti nel {morti}", f"Authors who died in {morti}"),
         T("70 anni; 30 in più per chi è «morto per la Francia».", "70 years; 30 more for authors who «died for France»."),
         f"{app}#/{anno}", T(f"{n_(n_ue)} scrittori →", f"{n_(n_ue)} writers →"), ""),
        (T("Germania", "Germany"), T(f"Autori morti nel {morti}", f"Authors who died in {morti}"),
         T("70 anni dalla morte.", "70 years after death."), f"{app}#/{anno}", T(f"{n_(n_ue)} scrittori →", f"{n_(n_ue)} writers →"), ""),
        (T("Regno Unito", "United Kingdom"), T(f"Autori morti nel {morti}", f"Authors who died in {morti}"),
         T("70 anni; le opere uscite dopo il 1988 di autori morti prima del 1969 restano protette fino al 2039.", "70 years; works first published after 1988 by authors who died before 1969 stay protected until 2039."),
         f"{app}#/{anno}", T(f"{n_(n_ue)} scrittori →", f"{n_(n_ue)} writers →"), ""),
    ]
    if n_es:
        nomi = (T(": entrano ", ": in come ") + ", ".join(es_nomi)) if es_nomi else ""
        righe.append(("Spagna" if it else "Spain", T(f"Autori morti nel {morti_es}", f"Authors who died in {morti_es}"),
                      T(f"80 anni per chi è morto prima del 1987{nomi}.", f"80 years for authors who died before 1987{nomi}."),
                      f"{app}#/{anno}", T(f"{n_(n_es)} scrittori →", f"{n_(n_es)} writers →"), "es"))
    if n_us:
        righe.append(("USA", T(f"Libri pubblicati nel {pub}", f"Books published in {pub}"),
                      T("95 anni dalla pubblicazione, opera per opera.", "95 years after publication, work by work."),
                      f"{app}#/us/{anno}", T(f"{n_us} libri →", f"{n_us} books →"), "us"))
    out.append(f'<section class="sec">\n<div class="sh m"><h2>{T("Chi entra, dove", "Who enters, where")}</h2>'
               f'<span>{T("Regole lette sui testi di legge di ogni paese:", "Rules read from each country&#39;s legal texts:")} <a href="{app}#regole-paesi">{T("il riquadro delle regole", "the rules box")}</a></span></div>\n<ul class="where">\n')
    for p_, c, r, h, l, cl in righe:
        cls = f' class="{cl}"' if cl else ""
        out.append(f'<li{cls}><span class="p">{esc(p_)}</span><span class="m y">{esc(c)}</span><span class="r">{esc(r)}</span><a href="{h}">{esc(l)}</a></li>\n')
    out.append("</ul>\n</section>\n")

    # 5. cosa significa davvero
    if duke:
        y, t_en, t_it = duke
        dove = T(f"«{t_it}» è libero negli USA dal {y} e in Europa solo dal {anno}.", f"«{t_en}» has been free in the USA since {y}, and in Europe only from {anno}.")
    else:
        dove = ""
    out.append(f"""<section class="sec">
<div class="sh m"><h2>{T("Cosa significa davvero", "What it really means")}</h2><span>{T("Prima di pubblicare", "Before you publish")}</span></div>
<div class="three">
<div><span class="m">01</span><h3>{T("Il testo, non l'edizione", "The text, not the edition")}</h3><p>{T("È libero il testo originale. Le traduzioni recenti, le illustrazioni e le edizioni curate hanno diritti propri: per tradurre un autore serve una traduzione nuova, o una già libera.", "The original text is free. Recent translations, illustrations and edited editions have their own rights: to publish a translation you need a new one, or one that is already free.")}</p></div>
<div><span class="m">02</span><h3>{T("Dipende da dove pubblichi", "It depends where you publish")}</h3><p>{T("Il 1° gennaio non scade tutto insieme ovunque. Lo stesso libro può essere libero negli USA e protetto in Europa, o il contrario.", "On 1 January not everything expires everywhere at once. The same book can be free in the USA and protected in Europe, or the other way round.")} {esc(dove)}</p></div>
<div><span class="m">03</span><h3>{T("Certo e da verificare", "Certain and to be checked")}</h3><p>{T("Segniamo come certo solo ciò che è confermato da più fonti (anni di morte, anni di uscita). Il resto è «da verificare», con il motivo. Le fonti sono elencate in fondo a ogni pagina.", "We mark as certain only what more than one source confirms (years of death, years of publication). The rest is «to be checked», with the reason. Sources are listed at the bottom of every page.")}</p></div>
</div>
</section>
""")

    # 6. domande
    out.append(f'<section class="sec">\n<div class="sh m"><h2>{T("Le risposte brevi", "The short answers")}</h2><span>{T("Domande", "Questions")}</span></div>\n<div>\n')
    for q, r in faq:
        out.append(f'<div class="acc"><button type="button">{esc(q)}<span>[+]</span></button><div class="bd"><p>{esc(r)}</p></div></div>\n')
    out.append("</div>\n</section>\n")

    # 7. tutti gli scrittori con una scheda (collegamenti interni verso ogni scheda)
    if aut:
        pag = "pagina" if it else "pagina_en"
        gruppi = {}
        for a in sorted(aut, key=lambda a: (_cognome(a["nome"]), slug_base(a["nome"]))):
            k = _cognome(a["nome"])[:1].upper()
            gruppi.setdefault(k if k.isalpha() else "#", []).append(a)
        out.append(f'<section class="sec" id="autori">\n<div class="sh m"><h2>{T("Tutti gli scrittori con una scheda", "All the writers with a page")}</h2>'
                   f'<span>{T(f"{len(aut)} · in ordine di cognome", f"{len(aut)} · by surname")}</span></div>\n'
                   f'<p class="lede">{T(f"I {len(aut)} scrittori morti nel {morti} per cui abbiamo una scheda, in ordine di cognome. Ogni scheda ha la data paese per paese, le opere principali e le fonti.", f"The {len(aut)} writers who died in {morti} that have a page, by surname. Each page has the date country by country, the main works and the sources.")}</p>\n'
                   f'<nav class="letters" aria-label="{T("Lettere", "Letters")}">' + "".join(f'<a href="#al-{k}">{k}</a>' for k in gruppi) + '</nav>\n<div class="az">')
        for k, lista in gruppi.items():
            out.append(f'<div class="L" id="al-{k}"><b>{k}</b>')
            for a in lista:
                href = f"/autore/{a[pag]}/" if it else f"/en/author/{a[pag]}/"
                m = (a.get("professioni") or [""])[0] if it else re.sub(r"\s*\([^)]*\)\s*$", "", pulisci(a.get("descrizione")))
                mm = " · " + esc(m) if m else ""
                out.append(f'<a href="{href}">{esc(pulisci(a["nome"]))}<span>{anno_di(a.get("nascita")) or "?"} – {anno_di(a["morte"])}{mm}</span></a>')
            out.append("</div>")
        out.append("</div>\n</section>\n")

    # 8. fonti e metodo (nel piede) e calendario
    cal = ""
    if CALENDARIO_ON and anno == _cal:
        href = f"/calendario/{anno}/" if it else f"/en/calendar/{anno}/"
        cal = (f' {T("Il Public Domain Day è la prima voce del", "Public Domain Day is the first entry of the")} <a href="{href}">{T(f"calendario degli anniversari letterari {anno}", f"{anno} literary anniversaries calendar")}</a>.')
    metodo = "https://github.com/mnovali90-byte/publicdomain/blob/main/docs/metodo-anni-opere.md"
    fonti = (T("Fonti e metodo", "Sources and method"), T(
        "Wikidata (CC0) per autori, opere e anni; biblioteche nazionali per confermare gli anni di morte. Per gli anni di uscita dei libri USA: registro del copyright americano (Catalog of Copyright Entries, trascritto dalla New York Public Library, CC0), Duke University (CC BY 4.0), Open Library, Library of Congress, BnF e il catalogo collettivo tedesco K10plus. Visite: Wikipedia in 5 lingue.",
        "Wikidata (CC0) for authors, works and years; national libraries to confirm years of death. For the publication years of US books: the US copyright register (Catalog of Copyright Entries, transcribed by the New York Public Library, CC0), Duke University (CC BY 4.0), Open Library, Library of Congress, BnF and the German union catalogue K10plus. Page views: Wikipedia in 5 languages.")
        + f' <a href="{metodo}" rel="noopener">{T("Come confermiamo gli anni", "How we confirm the years")}</a>.' + cal)
    out.append('<div class="pf" id="pf" aria-hidden="true"></div>\n')
    out.append(JS_ANNO.replace("@@LOC@@", "it-IT" if it else "en-GB"))
    out.append(piede_scheda(lang, fonti))
    return "".join(out), url


JS_ANNO = """<script>
(()=>{const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const RM=matchMedia('(prefers-reduced-motion: reduce)').matches, COV=['c-red','c-box','c-ink','c-pap'];
const g=$('#pd-giorni'); if(g){ const d=Math.ceil((new Date(g.dataset.d+'T00:00:00')-new Date())/864e5); if(d>0) g.textContent=d.toLocaleString('@@LOC@@'); }
const say=$('#say'); say.innerHTML=say.textContent.split(' ').map(w=>'<span class="w">'+w+'</span>').join(' ');
function ink(){ const ws=$$('#say .w'), r=say.getBoundingClientRect(); const p=Math.min(1,Math.max(0,(innerHeight*.95-r.top)/(r.height+innerHeight*.3))); const k=RM?999:Math.round(p*ws.length); ws.forEach((w,i)=>w.classList.toggle('on',i<k)); }
const esc=t=>String(t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let act=null;
function face(r){ const i=$$('.row').indexOf(r);
  return r.dataset.f?'<img src="'+r.dataset.f+'" alt="" onerror="this.remove()">':'<div class="cv c-box"><span></span><b>'+esc(r.dataset.i||'')+'</b><span></span></div>'; }
function setAct(r){ if(r===act) return; act=r; $$('.row').forEach(x=>x.classList.toggle('on',x===r));
  $$('#pf .ly').forEach(l=>{ l.classList.remove('on'); l.classList.add('off'); setTimeout(()=>l.remove(),300); });
  const ly=document.createElement('div'); ly.className='ly'; ly.innerHTML=face(r); $('#pf').appendChild(ly);
  requestAnimationFrame(()=>requestAnimationFrame(()=>ly.classList.add('on'))); }
function pick(){ const pr=$('#pf').getBoundingClientRect(), mid=pr.height?pr.top+pr.height/2:innerHeight*.52; let inside=null;   /* la riga accesa è quella all'altezza del ritratto */
  $$('.ix').forEach(s=>{ const ol=s.querySelector('.rows').getBoundingClientRect(); if(ol.top<mid&&ol.bottom>mid) inside=s; });
  document.body.classList.toggle('ix-in',!!inside); if(!inside) return;
  let best=null,bd=1e9; inside.querySelectorAll('.row').forEach(r=>{ const b=r.getBoundingClientRect(), d=Math.abs(b.top+b.height/2-mid); if(d<bd){bd=d;best=r;} });
  if(best) setAct(best); }
$$('.row').forEach(r=>r.addEventListener('mouseenter',()=>{ if(matchMedia('(hover:hover)').matches) setAct(r); }));
$('#mbtn').addEventListener('click',()=>document.body.classList.add('menu-on')); $('#mx').addEventListener('click',()=>document.body.classList.remove('menu-on'));
let tk=false; function frame(){ tk=false; ink(); pick(); }
addEventListener('scroll',()=>{ if(!tk){tk=true;requestAnimationFrame(frame);} },{passive:true}); addEventListener('resize',frame); frame();
})();
</script>
"""


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

    AUT.update(autori)
    SLUG.update(slug_di)
    EN_OK.update(en_ok)
    for f in file_autori():
        st = Path(f).stem
        tipo, anno_f = ("es", int(st[3:])) if st.startswith("es-") else ("ue", int(st))
        for a_ in json.load(open(f, encoding="utf-8"))["autori"]:
            q = a_["wikidata"]
            if q not in slug_di:
                continue
            MEMBRI.setdefault(q, (tipo, anno_f))
            if (a_.get("letterario") and a_.get("morte") and q not in FUORI_CLASSIFICA and not a_.get("fuori_classifica")
                    and LETTERARI & set(a_.get("professioni") or [])):
                POOL.setdefault((tipo, anno_f), []).append(q)
    for k_ in POOL:
        POOL[k_].sort(key=lambda q: -_visite(AUT[q]))

    # guardia (19/11/2026): se i dati non hanno biografie e opere (giro interrotto a metà) non si tocca niente
    if len(autori) < 100:
        print(f"Solo {len(autori)} autori con biografia e opere: dati incompleti, le schede restano come sono.")
        return 1
    # rimandi dai vecchi indirizzi: si ricordano in data/indirizzi_vecchi.json e si riscrivono a ogni giro
    f_rim = RADICE / "data" / "indirizzi_vecchi.json"
    rimandi = _leggi(f_rim, {})
    esistenti = {l: {p.name for p in (RADICE / PERCORSO[l]).iterdir() if p.is_dir()} if (RADICE / PERCORSO[l]).exists() else set()
                 for l in ("it", "en")}
    for q, a in autori.items():
        vecchio = slug_vecchio(a["nome"])
        if vecchio and vecchio != slug_di[q] and any(vecchio in esistenti[l] for l in esistenti):
            rimandi[vecchio] = slug_di[q]
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
    for vecchio, nuovo in rimandi.items():
        for l in ("it", "en"):
            if (RADICE / PERCORSO[l] / nuovo).exists() and not (RADICE / PERCORSO[l] / vecchio).exists():
                (RADICE / PERCORSO[l] / vecchio).mkdir()
                (RADICE / PERCORSO[l] / vecchio / "index.html").write_text(pagina_rimando(url_pagina(l, nuovo), l), encoding="utf-8")
    f_rim.write_text(json.dumps(rimandi, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
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
    import home   # la home (frontespizio), italiano e inglese: scripts/home.py
    home.crea_home({"testa_scheda": testa_scheda, "piede_scheda": piede_scheda, "CSS_ANNO": CSS_ANNO,
                    "marchio": marchio_html(56).replace('<span class="pdr" style="--w:56px">', "").rsplit("</span>", 1)[0]})
    if CALENDARIO_ON:
        import calendario
        landing_urls += calendario.crea_calendario()
    date_s = _leggi(DATE_SITEMAP, {})
    nuove_date = {}

    def data_di(u):
        imp = impronta(RADICE / u[len(SITO):].strip("/") / "index.html")
        prima = date_s.get(u)
        d = prima[1] if prima and prima[0] == imp else str(oggi)
        nuove_date[u] = [imp, d]
        return d
    righe = [f"  <url><loc>{u}</loc><lastmod>{data_di(u)}</lastmod><changefreq>monthly</changefreq></url>"
             for u in (f"{SITO}/", f"{SITO}/en/", f"{SITO}/radar/", f"{SITO}/en/radar/", url_pagina('it'), url_pagina('en'))]
    if (RADICE / "gia-pubblici" / "index.html").exists():   # pagina «Già pubblici» (storico/pagina.py)
        landing_urls += [f"{SITO}/gia-pubblici/", f"{SITO}/en/already-public/"]
    righe += [f"  <url><loc>{u}</loc><lastmod>{data_di(u)}</lastmod><changefreq>weekly</changefreq></url>" for u in landing_urls]
    righe += [f"  <url><loc>{u}</loc><lastmod>{data_di(u)}</lastmod></url>" for u in sorted(urls)]
    DATE_SITEMAP.write_text(json.dumps(nuove_date, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    (RADICE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(righe) + "\n</urlset>\n", encoding="utf-8")
    print(f"Pagine create: {len(voci['it'])} in italiano, {len(voci['en'])} in inglese (su {len(autori)} autori con biografia e opere)")


if __name__ == "__main__":
    sys.exit(main())
