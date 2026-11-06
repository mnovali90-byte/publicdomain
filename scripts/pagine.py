#!/usr/bin/env python3
"""Crea una pagina statica per ogni autore letterario con abbastanza contenuto, più l'indice e la sitemap.

Le pagine sono fatte solo con i dati già scaricati dalle fonti aperte (nessun testo scritto da un'AI).
Una pagina nasce solo se l'autore ha una biografia E almeno un'opera: le pagine vuote non servono a chi
legge e Google le tratta come spam. Esce in: autore/<nome>/index.html, autore/index.html, sitemap.xml.
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
NOMI_LINGUA = {"it": "italiano", "en": "inglese", "es": "spagnolo", "de": "tedesco", "fr": "francese"}


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def pulisci(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>", "", str(s or ""))).strip()


def migliaia(n):
    return f"{int(n):,}".replace(",", ".")


def data_it(anno, mese=1, giorno=1):
    return f"{giorno}{'°' if giorno == 1 else ''} {MESI[mese - 1]} {anno}"


def slug_base(nome):
    t = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def anno_di(iso):
    m = re.match(r"^(-?\d{1,4})", str(iso or ""))
    return int(m.group(1)) if m else None


def iso_valida(iso):
    return bool(re.match(r"^\d{4}(-\d{2}(-\d{2})?)?$", str(iso or "")))


def bio_di(a):
    """Biografia in italiano se c'è, altrimenti in inglese (come la scheda del sito)."""
    for l in ("it", "en"):
        b = (a.get("bios") or {}).get(l)
        if b and b.get("testo"):
            return {"testo": pulisci(b["testo"]), "url": b.get("url"), "lingua": l}
    if a.get("bio"):
        return {"testo": pulisci(a["bio"]), "url": a.get("bio_url"), "lingua": a.get("bio_lingua") or "it"}
    return None


def abbastanza_contenuto(a):
    return bool(a.get("letterario") and bio_di(a) and a.get("opere") and anno_di(a.get("morte")))


def paese_per_paese(D):
    """Stesse regole della scheda del sito (bloccoPaesi in index.html): vanno tenute allineate."""
    fine = datetime.date(D + 70 + 8, 12, 31) + datetime.timedelta(days=120)
    fr_estesa = f"{MESI[fine.month - 1]} {fine.year}"
    righe = [
        f"UE (base) e Germania: dal {data_it(D + 71)}.",
        f"Francia: dal {data_it(D + 71)}. Per le opere pubblicate prima del 3 settembre 1939 la proroga di guerra sposta la data a circa {fr_estesa}.",
        f"Italia: dal {data_it(D + 71)}. Se la proroga di 6 anni (opere pubblicate prima del 1945) si somma ai 70 anni: dal {data_it(D + 77)}. "
        "Per gli autori dei paesi alleati può esserci una proroga in più.",
    ]
    if D < 1987:
        righe.append(f"Spagna: non prima del {data_it(D + 81)} (80 anni dalla morte, perché è morto prima del 1987; la legge non dice come si conta l'anno).")
    else:
        righe.append(f"Spagna: dal {data_it(D + 71)}.")
    return righe


CSS = """
:root{--ink:#0C0C10;--carta:#F7F7F4;--vermiglio:#FF4326;--vermiglio-testo:#C2301A;--muto:#5C5C66;--riquadro:#E4E2DA;--notte:#1C1C24;
--display:'Big Shoulders Display',Impact,'Arial Narrow',sans-serif;--testo:'Instrument Sans',system-ui,sans-serif;--mono:'DM Mono',ui-monospace,Menlo,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--carta);color:var(--ink);font-family:var(--testo);line-height:1.6;-webkit-text-size-adjust:100%}
a{color:var(--vermiglio-testo)}
.barra{background:var(--ink);color:#fff;padding:14px 20px;font-family:var(--mono);font-size:13px;letter-spacing:.08em;text-transform:uppercase}
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
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titolo}</title>
<meta name="description" content="{descr}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_tipo}">
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
<div class="barra"><a href="/"><i></i>Public Domain Radar</a></div>
"""

PIEDE = """<footer>
<p>Fonti: Wikidata (CC0), Wikipedia (testi CC BY-SA, con link alla pagina d'origine), Wikimedia Commons (ritratti, ciascuno con la sua licenza), Open Library, catalogo SBN. Dati aperti, aggiornati ogni mese in automatico.</p>
<p>Le date sono un calcolo indicativo dalle norme elencate nel <a href="/#regole-paesi">riquadro delle regole</a>. Non è consulenza legale: prima di pubblicare va controllato nella legge del paese.</p>
<p><a href="/">Tutti gli autori</a> · <a href="/autore/">Indice degli autori</a> · <a href="https://github.com/mnovali90-byte/publicdomain">Codice e dati su GitHub</a></p>
</footer>
</body>
</html>
"""


def pagina_autore(a, slug, oggi):
    nome = pulisci(a["nome"])
    nasc, mor = anno_di(a.get("nascita")), anno_di(a.get("morte"))
    anni = f"{nasc if nasc else '?'} – {mor}"
    D = mor
    bd = bio_di(a)
    url = f"{SITO}/autore/{slug}/"
    titolo = f"{nome} ({anni}): quando entra in pubblico dominio · Public Domain Radar"
    descr = (f"{nome} è morto nel {D}: nell'UE le sue opere sono libere dal {data_it(D + 71)}. "
             f"Date per Italia, Francia, Germania e Spagna, edizioni italiane in SBN e opere principali, da dati aperti.")
    persona = {"@context": "https://schema.org", "@type": "Person", "name": nome, "url": url,
               "sameAs": [u for u in (bd.get("url") if bd else None, a.get("url")) if u]}
    if iso_valida(a.get("nascita")):
        persona["birthDate"] = a["nascita"]
    if iso_valida(a.get("morte")):
        persona["deathDate"] = a["morte"]
    briciole = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Public Domain Radar", "item": SITO + "/"},
        {"@type": "ListItem", "position": 2, "name": "Autori", "item": SITO + "/autore/"},
        {"@type": "ListItem", "position": 3, "name": nome, "item": url}]}
    jsonld = "".join('<script type="application/ld+json">' + json.dumps(j, ensure_ascii=False).replace("</", "<\\/") + "</script>\n" for j in (persona, briciole))
    out = [TESTA.format(titolo=esc(titolo), descr=esc(descr), url=url, og_tipo="profile", jsonld=jsonld, css=CSS), "<main>\n"]
    foto = a.get("foto") or {}
    if foto.get("url"):
        cap = " · ".join(x for x in (pulisci(foto.get("autore")), pulisci(foto.get("licenza"))) if x)
        pag = f' <a href="{esc(foto["pagina"])}" rel="noopener">Wikimedia Commons</a>' if foto.get("pagina") else ""
        out.append(f'<figure><img src="{esc(foto["url"])}" alt="Ritratto di {esc(nome)}" loading="lazy"><figcaption>{esc(cap)}{pag}</figcaption></figure>\n')
    out.append(f"<h1>{esc(nome)}</h1>\n<p class=\"sotto\">{esc(anni)}")
    if a.get("paesi"):
        out.append(" · " + esc(", ".join(a["paesi"])))
    if a.get("professioni"):
        out.append(" · " + esc(", ".join(a["professioni"][:4])))
    out.append("</p>\n")
    out.append(f'<p class="lead">Morto nel {D}, nell\'Unione europea le sue opere sono libere dal <strong>{data_it(D + 71)}</strong>. '
               "Altri paesi hanno regole diverse, qui sotto.</p>\n")

    out.append("<h2>Da quando è libero, paese per paese</h2>\n<ul>\n")
    out += [f"<li>{esc(r)}</li>\n" for r in paese_per_paese(D)]
    out.append('</ul>\n<p class="sotto">Calcolo indicativo, dalle norme del riquadro in fondo alla pagina. Non è consulenza legale.</p>\n')

    sbn = (a.get("traduzioni") or {}).get("sbn_it")
    if sbn:
        out.append("<h2>Edizioni italiane nel catalogo SBN</h2>\n")
        if sbn.get("trovato"):
            r = f"{migliaia(sbn['edizioni'])} registrazioni in italiano"
            if sbn.get("ultimo"):
                r += f" · la più recente: {sbn['ultimo']}"
            r += f" · {migliaia(sbn.get('dal_2000', 0))} dal 2000"
            out.append(f"<p><strong>{esc(r)}</strong></p>\n")
            if sbn.get("metodo") == "nome_anni":
                out.append('<p class="sotto">Autore riconosciuto dal nome e confermato dagli anni di nascita e morte.</p>\n')
            elif sbn.get("metodo") == "nome":
                out.append('<p class="sotto">Autore riconosciuto solo dal nome: il conteggio può essere impreciso.</p>\n')
            if sbn.get("sospetto"):
                out.append('<p class="sotto">Da verificare: autore molto noto con pochissime edizioni in SBN. Può essere schedato con un altro nome.</p>\n')
        else:
            out.append("<p><strong>Nessuna registrazione trovata in SBN</strong></p>\n")
        out.append('<p class="sotto">Conta le registrazioni del catalogo nazionale delle biblioteche (SBN): è un indizio di quanto è già stato pubblicato, non un elenco di libri in commercio.</p>\n')

    visite = [(l, a.get("visite_" + l)) for l in ("it", "en", "es", "de", "fr") if a.get("visite_" + l) is not None]
    if visite:
        out.append("<h2>Quanto è letto</h2>\n<table>\n<tr><th>Wikipedia in</th><th>Visite negli ultimi 12 mesi</th></tr>\n")
        out += [f"<tr><td>{NOMI_LINGUA[l]}</td><td>{migliaia(v) if v else 'nessuna pagina'}</td></tr>\n" for l, v in visite]
        out.append("</table>\n")

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

    if bd:
        l = "italiano" if bd["lingua"] == "it" else "inglese"
        ln = f'<a href="{esc(bd["url"])}" rel="noopener">Wikipedia in {l}</a>' if bd.get("url") else "Wikipedia"
        out.append(f'<h2>Chi era</h2>\n<p>{esc(bd["testo"])}</p>\n<p class="sotto">Testo da {ln}, licenza CC BY-SA.</p>\n')

    out.append(f'<p><a class="cta" href="/#/autore/{esc(a["wikidata"])}">Apri la scheda completa nel radar</a></p>\n')
    out.append("</main>\n" + PIEDE)
    return "".join(out)


def pagina_indice(voci, oggi):
    url = f"{SITO}/autore/"
    titolo = "Indice degli autori in pubblico dominio · Public Domain Radar"
    descr = f"{len(voci)} autori con la data di pubblico dominio paese per paese (UE, Italia, Francia, Germania, Spagna), da dati aperti."
    out = [TESTA.format(titolo=esc(titolo), descr=esc(descr), url=url, og_tipo="website", jsonld="", css=CSS), "<main>\n",
           "<h1>Indice degli autori</h1>\n", f'<p class="lead">{len(voci)} autori con una pagina dedicata: biografia, opere e data di pubblico dominio paese per paese.</p>\n']
    lettera = None
    for nome, slug, anni in voci:
        k = (nome[:1] or "#").upper()
        if k != lettera:
            if lettera is not None:
                out.append("</ul>\n")
            out.append(f"<h2>{esc(k)}</h2>\n<ul>\n")
            lettera = k
        out.append(f'<li><a href="/autore/{slug}/">{esc(nome)}</a> <span class="sotto">{esc(anni)}</span></li>\n')
    out.append("</ul>\n</main>\n" + PIEDE)
    return "".join(out)


def main():
    oggi = datetime.date.today()
    autori = {}
    for f in sorted(glob.glob(str(RADICE / "data" / "*[0-9][0-9][0-9][0-9].json"))):
        for a in json.load(open(f, encoding="utf-8"))["autori"]:
            if abbastanza_contenuto(a):
                autori.setdefault(a["wikidata"], a)
    scelti = sorted(autori.values(), key=lambda a: (slug_base(a["nome"]), a["wikidata"]))
    usati = {}
    for a in scelti:
        s = slug_base(a["nome"]) or a["wikidata"].lower()
        usati.setdefault(s, []).append(a)
    cartella = RADICE / "autore"
    if cartella.exists():
        shutil.rmtree(cartella)
    cartella.mkdir()
    voci, urls = [], []
    for s, gruppo in usati.items():
        for a in gruppo:
            slug = s if len(gruppo) == 1 else f"{s}-{a['wikidata'].lower()}"
            d = cartella / slug
            d.mkdir()
            (d / "index.html").write_text(pagina_autore(a, slug, oggi), encoding="utf-8")
            voci.append((pulisci(a["nome"]), slug, f"{anno_di(a.get('nascita')) or '?'} – {anno_di(a['morte'])}"))
            urls.append(f"{SITO}/autore/{slug}/")
    voci.sort(key=lambda v: (slug_base(v[0]), v[1]))
    (cartella / "index.html").write_text(pagina_indice(voci, oggi), encoding="utf-8")
    righe = [f"  <url><loc>{SITO}/</loc><lastmod>{oggi}</lastmod><changefreq>monthly</changefreq></url>",
             f"  <url><loc>{SITO}/autore/</loc><lastmod>{oggi}</lastmod><changefreq>monthly</changefreq></url>"]
    righe += [f"  <url><loc>{u}</loc><lastmod>{oggi}</lastmod></url>" for u in sorted(urls)]
    (RADICE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(righe) + "\n</urlset>\n", encoding="utf-8")
    print(f"Pagine autore create: {len(urls)} (su {len(autori)} con biografia e opere)")


if __name__ == "__main__":
    sys.exit(main())
