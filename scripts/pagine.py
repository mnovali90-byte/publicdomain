#!/usr/bin/env python3
"""Crea una pagina statica per ogni autore letterario con abbastanza contenuto, più gli indici e la sitemap.

Le pagine sono fatte solo con i dati già scaricati dalle fonti aperte (nessun testo scritto da un'AI).
Una pagina nasce solo se l'autore ha una biografia E almeno un'opera: le pagine vuote non servono a chi
legge e Google le tratta come spam.

Esce in: autore/<nome>/ (italiano), en/author/<nome>/ (inglese, solo se esiste la biografia inglese),
i due indici e sitemap.xml. Le pagine inglesi non mostrano opere, paesi e professioni, perché in Wikidata
hanno etichette italiane: meglio meno contenuto che contenuto in due lingue.
"""
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
    fine = datetime.date(D + 70 + 8, 12, 31) + datetime.timedelta(days=120)
    d = lambda y: data_l(lang, y)
    if lang == "en":
        return [
            f"EU (base rule) and Germany: from {d(D + 71)}.",
            f"France: from {d(D + 71)}. For works published before 3 September 1939 the wartime extension moves the date to about {MESI_EN[fine.month - 1]} {fine.year}.",
            f"Italy: from {d(D + 71)}. If the 6-year extension (works published before 1945) is added to the 70 years: from {d(D + 77)}. "
            "For authors from Allied countries there may be a further extension.",
            (f"Spain: not before {d(D + 81)} (80 years after death, because the author died before 1987; the law does not say how the year is counted)."
             if D < 1987 else f"Spain: from {d(D + 71)}."),
        ]
    return [
        f"UE (base) e Germania: dal {d(D + 71)}.",
        f"Francia: dal {d(D + 71)}. Per le opere pubblicate prima del 3 settembre 1939 la proroga di guerra sposta la data a circa {MESI[fine.month - 1]} {fine.year}.",
        f"Italia: dal {d(D + 71)}. Se la proroga di 6 anni (opere pubblicate prima del 1945) si somma ai 70 anni: dal {d(D + 77)}. "
        "Per gli autori dei paesi alleati può esserci una proroga in più.",
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
.barra i{display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--vermiglio);margin-right:10px}
main{max-width:780px;margin:0 auto;padding:32px 20px 72px}
h1{font-family:var(--display);font-weight:900;font-size:clamp(40px,9vw,76px);line-height:.95;text-transform:uppercase;margin:8px 0 12px}
h2{font-family:var(--mono);font-weight:500;font-size:13px;letter-spacing:.1em;text-transform:uppercase;color:var(--muto);margin:40px 0 10px;border-top:2px solid var(--ink);padding-top:12px}
.sotto{color:var(--muto);font-size:14px}
.lead{font-size:19px}
ul{padding-left:20px}li{margin:6px 0}
table{border-collapse:collapse;width:100%;font-size:15px}td,th{border-bottom:1px solid var(--riquadro);padding:8px 6px;text-align:left}
figure{margin:0 0 20px}figure img{max-width:100%;max-height:420px;display:block;background:var(--riquadro)}figcaption{font-size:12px;color:var(--muto);margin-top:6px}
.cta{display:inline-block;margin-top:28px;padding:12px 18px;border:1.5px solid var(--ink);color:var(--ink);text-decoration:none;font-family:var(--mono);font-size:13px;text-transform:uppercase;letter-spacing:.06em}
footer{background:var(--ink);color:#B9B9C6;font-size:13px;padding:32px 20px}footer p{max-width:780px;margin:0 auto 10px}footer a{color:#fff}
"""

TESTA = """<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
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
</head>
<body>
<div class="barra"><a href="{home}"><i></i>Public Domain Radar</a>{altra_lingua}</div>
"""

PIEDE = {
    "it": """<footer>
<p>Fonti: Wikidata (CC0), Wikipedia (testi CC BY-SA, con link alla pagina d'origine), Wikimedia Commons (ritratti, ciascuno con la sua licenza), Open Library, catalogo SBN. Dati aperti, aggiornati ogni mese in automatico; possono contenere errori.</p>
<p>Le date sono un calcolo indicativo dalle norme elencate nel <a href="/#regole-paesi">riquadro delle regole</a>. Non è consulenza legale: prima di pubblicare va controllato nella legge del paese.</p>
<p><a href="/">Tutti gli autori</a> · <a href="/autore/">Indice degli autori</a> · <a href="https://github.com/mnovali90-byte/publicdomain">Codice e dati su GitHub</a></p>
</footer>
</body>
</html>
""",
    "en": """<footer>
<p>Sources: Wikidata (CC0), Wikipedia (text CC BY-SA, linked to the original page), Wikimedia Commons (portraits, each with its own licence), Open Library, SBN catalogue. Open data, updated automatically every month; it may contain errors.</p>
<p>The dates are an indicative calculation from the rules listed in the <a href="/en/#regole-paesi">rules box</a>. Not legal advice: check the law of the country before publishing.</p>
<p><a href="/en/">All authors</a> · <a href="/en/author/">Author index</a> · <a href="https://github.com/mnovali90-byte/publicdomain">Code and data on GitHub</a></p>
</footer>
</body>
</html>
""",
}


def url_pagina(lang, slug=""):
    return f"{SITO}/{PERCORSO[lang]}/{slug + '/' if slug else ''}"


def alterne(lang, slug):
    """Collegamenti tra la pagina italiana e quella inglese (hreflang). Solo se esistono tutte e due."""
    if slug is None:
        return ""
    return (f'<link rel="alternate" hreflang="it" href="{url_pagina("it", slug)}">\n'
            f'<link rel="alternate" hreflang="en" href="{url_pagina("en", slug)}">\n')


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
        titolo = f"{nome} ({anni}): when it enters the public domain · Public Domain Radar"
        descr = (f"{nome} died in {D}: in the EU the works are free from {data_l(lang, D + 71)}. "
                 f"Dates for Italy, France, Germany and Spain, Italian editions in SBN and online interest, from open data.")
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
    foto = a.get("foto") or {}
    if foto.get("url"):
        cap = " · ".join(x for x in (pulisci(foto.get("autore")), pulisci(foto.get("licenza"))) if x)
        pag = f' <a href="{esc(foto["pagina"])}" rel="noopener">Wikimedia Commons</a>' if foto.get("pagina") else ""
        out.append(f'<figure><img src="{esc(foto["url"])}" alt="{"Ritratto di" if it else "Portrait of"} {esc(nome)}" loading="lazy"><figcaption>{esc(cap)}{pag}</figcaption></figure>\n')
    out.append(f"<h1>{esc(nome)}</h1>\n<p class=\"sotto\">{esc(anni)}")
    if it:   # paesi e professioni sono etichette italiane di Wikidata: solo nella pagina italiana
        if a.get("paesi"):
            out.append(" · " + esc(", ".join(a["paesi"])))
        if a.get("professioni"):
            out.append(" · " + esc(", ".join(a["professioni"][:4])))
    out.append("</p>\n")
    if it:
        out.append(f'<p class="lead">Morto nel {D}, nell\'Unione europea le sue opere sono libere dal <strong>{data_l(lang, D + 71)}</strong>. '
                   "Altri paesi hanno regole diverse, qui sotto.</p>\n")
    else:
        out.append(f'<p class="lead">Died in {D}, in the European Union the works are free from <strong>{data_l(lang, D + 71)}</strong>. '
                   "Other countries have different rules, below.</p>\n")

    out.append(f"<h2>{'Da quando è libero, paese per paese' if it else 'Free from when, country by country'}</h2>\n<ul>\n")
    out += [f"<li>{esc(r)}</li>\n" for r in paese_per_paese(D, lang)]
    out.append('</ul>\n<p class="sotto">' + ("Calcolo indicativo, dalle norme del riquadro in fondo alla pagina. Non è consulenza legale."
               if it else "Indicative calculation, based on the rules in the box at the bottom of the page. Not legal advice.") + "</p>\n")

    sbn = (a.get("traduzioni") or {}).get("sbn_it")
    if sbn:
        out.append(f"<h2>{'Edizioni italiane nel catalogo SBN' if it else 'Italian editions in the SBN catalogue'}</h2>\n")
        if sbn.get("trovato"):
            if it:
                r = f"{migliaia(sbn['edizioni'])} registrazioni in italiano"
                if sbn.get("ultimo"):
                    r += f" · la più recente: {sbn['ultimo']}"
                r += f" · {migliaia(sbn.get('dal_2000', 0))} dal 2000"
            else:
                r = f"{migliaia(sbn['edizioni'], lang)} records in Italian"
                if sbn.get("ultimo"):
                    r += f" · latest: {sbn['ultimo']}"
                r += f" · {migliaia(sbn.get('dal_2000', 0), lang)} since 2000"
            out.append(f"<p><strong>{esc(r)}</strong></p>\n")
            if sbn.get("metodo") == "nome_anni":
                out.append('<p class="sotto">' + ("Autore riconosciuto dal nome e confermato dagli anni di nascita e morte."
                           if it else "Author matched by name and confirmed by birth and death years.") + "</p>\n")
            elif sbn.get("metodo") == "nome":
                out.append('<p class="sotto">' + ("Autore riconosciuto solo dal nome: il conteggio può essere impreciso."
                           if it else "Author matched by name only: the count may be inaccurate.") + "</p>\n")
            if sbn.get("sospetto"):
                out.append('<p class="sotto">' + ("Da verificare: autore molto noto con pochissime edizioni in SBN. Può essere schedato con un altro nome."
                           if it else "To verify: a very well-known author with very few SBN editions. They may be catalogued under another name.") + "</p>\n")
        else:
            out.append("<p><strong>" + ("Nessuna registrazione trovata in SBN" if it else "No record found in SBN") + "</strong></p>\n")
        out.append('<p class="sotto">' + ("Conta le registrazioni del catalogo nazionale delle biblioteche (SBN): è un indizio di quanto è già stato pubblicato, non un elenco di libri in commercio."
                   if it else "Counts records of the Italian national library catalogue (SBN): a hint of how much has already been published, not a list of books on sale.") + "</p>\n")

    visite = [(l, a.get("visite_" + l)) for l in ("it", "en", "es", "de", "fr") if a.get("visite_" + l) is not None]
    if visite:
        out.append(f"<h2>{'Quanto è letto' if it else 'How widely read'}</h2>\n<table>\n<tr><th>{'Wikipedia in' if it else 'Wikipedia in'}</th>"
                   f"<th>{'Visite negli ultimi 12 mesi' if it else 'Views in the last 12 months'}</th></tr>\n")
        out += [f"<tr><td>{NOMI_LINGUA[lang][l]}</td><td>{migliaia(v, lang) if v else ('nessuna pagina' if it else 'no page')}</td></tr>\n" for l, v in visite]
        out.append("</table>\n")

    if it:   # i titoli delle opere sono etichette italiane di Wikidata: solo nella pagina italiana
        out.append("<h2>Opere principali</h2>\n<ul>\n")
        for o in a["opere"][:10]:
            riga = esc(o.get("titolo"))
            if o.get("anno"):
                riga += f" ({esc(o['anno'])})"
            if o.get("generi"):
                riga += f' <span class="sotto">· {esc(", ".join(o["generi"][:2]))}</span>'
            out.append(f"<li>{riga}</li>\n")
        out.append("</ul>\n")
        if a.get("n_opere", 0) > len(a["opere"][:10]):
            out.append(f'<p class="sotto">Su {migliaia(a["n_opere"])} opere registrate in Wikidata, qui le più note.</p>\n')
    elif a.get("n_opere"):
        out.append(f"<h2>Works</h2>\n<p>{migliaia(a['n_opere'], lang)} works are recorded in Wikidata for this author.</p>\n")

    if bd:
        if it:
            l = "italiano" if bd["lingua"] == "it" else "inglese"
            ln = f'<a href="{esc(bd["url"])}" rel="noopener">Wikipedia in {l}</a>' if bd.get("url") else "Wikipedia"
            out.append(f'<h2>Chi era</h2>\n<p>{esc(bd["testo"])}</p>\n<p class="sotto">Testo da {ln}, licenza CC BY-SA.</p>\n')
        else:
            ln = f'<a href="{esc(bd["url"])}" rel="noopener">English Wikipedia</a>' if bd.get("url") else "Wikipedia"
            out.append(f'<h2>Who they were</h2>\n<p>{esc(bd["testo"])}</p>\n<p class="sotto">Text from {ln}, licence CC BY-SA.</p>\n')

    cta = f'/#/autore/{esc(a["wikidata"])}' if it else f'/en/#/autore/{esc(a["wikidata"])}'
    out.append(f'<p><a class="cta" href="{cta}">{"Apri la scheda completa nel radar" if it else "Open the full card in the radar"}</a></p>\n')
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


def crea_home_inglese():
    """en/index.html: la stessa app di index.html, con intestazione in inglese. Sull'indirizzo /en/ l'app parte in inglese."""
    s = (RADICE / "index.html").read_text(encoding="utf-8")
    cambi = [
        ('<html lang="it">', '<html lang="en">'),
        (re.search(r"<title>.*?</title>", s).group(0), "<title>Public Domain Radar · authors entering the public domain</title>"),
        (re.search(r'<meta name="description" content="[^"]*">', s).group(0),
         '<meta name="description" content="Which authors enter the public domain on the next 1 January, with the term rules of Italy, France, Germany and Spain read from official legal texts. Open data from Wikidata, Wikipedia and SBN, updated monthly.">'),
        ('<link rel="canonical" href="https://publicdomainradar.com/">', '<link rel="canonical" href="https://publicdomainradar.com/en/">'),
        ('<meta property="og:url" content="https://publicdomainradar.com/">', '<meta property="og:url" content="https://publicdomainradar.com/en/">'),
        ('<meta property="og:title" content="Public Domain Radar · autori che entrano in pubblico dominio">', '<meta property="og:title" content="Public Domain Radar · authors entering the public domain">'),
        (re.search(r'<meta property="og:description" content="[^"]*">', s).group(0),
         '<meta property="og:description" content="Which authors become free on 1 January, country by country, with open data and official legal sources.">'),
        (re.search(r'<meta name="twitter:description" content="[^"]*">', s).group(0),
         '<meta name="twitter:description" content="Which authors become free on 1 January, country by country, with open data and official legal sources.">'),
        ('{"@type":"WebSite","name":"Public Domain Radar","url":"https://publicdomainradar.com/"', '{"@type":"WebSite","name":"Public Domain Radar","url":"https://publicdomainradar.com/en/"'),
    ]
    for a, b in cambi:
        if a not in s:
            raise RuntimeError("index.html è cambiato: la home inglese non trova " + a[:50])
        s = s.replace(a, b, 1)
    (RADICE / "en").mkdir(exist_ok=True)
    (RADICE / "en" / "index.html").write_text(s, encoding="utf-8")


def file_autori():
    """Solo i file degli autori (2027.json, es-2027.json); us-*.json sono le opere."""
    return [f for f in sorted(glob.glob(str(RADICE / "data" / "*.json")))
            if re.fullmatch(r"(es-)?\d{4}\.json", Path(f).name)]


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

    crea_home_inglese()
    righe = [f"  <url><loc>{SITO}/</loc><lastmod>{oggi}</lastmod><changefreq>monthly</changefreq></url>",
             f"  <url><loc>{SITO}/en/</loc><lastmod>{oggi}</lastmod><changefreq>monthly</changefreq></url>",
             f"  <url><loc>{url_pagina('it')}</loc><lastmod>{oggi}</lastmod><changefreq>monthly</changefreq></url>",
             f"  <url><loc>{url_pagina('en')}</loc><lastmod>{oggi}</lastmod><changefreq>monthly</changefreq></url>"]
    righe += [f"  <url><loc>{u}</loc><lastmod>{oggi}</lastmod></url>" for u in sorted(urls)]
    (RADICE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(righe) + "\n</urlset>\n", encoding="utf-8")
    print(f"Pagine create: {len(voci['it'])} in italiano, {len(voci['en'])} in inglese (su {len(autori)} autori con biografia e opere)")


if __name__ == "__main__":
    sys.exit(main())
