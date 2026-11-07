"""Pagine del calendario degli anniversari letterari (italiano e inglese), con .ics e .csv.
Legge data/anniversari-<anno>.json (scritto da anniversari.py). Chiamato da pagine.py."""
import csv
import datetime
import html
import io
import json
import re
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
SITO = "https://publicdomainradar.com"
MESI = {"it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
        "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}
BREVI = {"it": ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"],
         "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}
ANNI_RECENTE = 2015   # «edizione italiana recente» = ultima edizione in SBN dal 2015 in poi

T = {
    "it": {
        "html": "it", "titolo": "Calendario degli anniversari letterari {a}: nascite, morti e prime edizioni · Public Domain Radar",
        "descr": "Gli anniversari letterari del {a}: nascite, morti e prime edizioni con anniversario tondo, giorno per giorno. Per editori, librai e creator. Dati aperti, con calendario .ics e tabella CSV.",
        "occ": "Anniversari letterari · {a}", "h1a": "Cosa ricordare nel ", "lead": "Nascite, morti e prime edizioni con anniversario tondo. Per ognuno: le edizioni italiane dell'autore nel catalogo SBN e un testo pronto per un post. Per editori, librai e creator.",
        "ics": "Aggiungi al tuo calendario (.ics)", "csv": "Scarica la tabella (CSV)",
        "mese": "Mese", "tipo": "Tipo", "tutti": "Tutti", "tutte": "Tutte", "senza": "Senza edizione italiana recente",
        "tipi": {"prima edizione": "Prima edizione", "nascita": "Nascita", "morte": "Morte"},
        "filtri_tipo": [("prima edizione", "Prime edizioni"), ("nascita", "Nascite"), ("morte", "Morti")],
        "anni": "{n} anni", "voce": "voce", "voci": "voci", "durante": "Durante l'anno", "nd": "giorno non noto", "soloanno": "{a} · solo anno",
        "sbn": "Edizioni italiane dell'autore (SBN)", "sbn_n": "{n} edizioni · ultima: {u}", "sbn_zero": "nessuna trovata in SBN", "sbn_poche": "poche trovate ({n}, ultima: {u}): da verificare", "sbn_senza_anno": "{n} edizioni",
        "copia": "Copia testo per un post →", "copiato": "Copiato ✓", "aggiungi": "Aggiungi al calendario →",
        "pdd": "Public Domain Day", "pdd_txt": "Entrano in pubblico dominio in Europa gli autori morti nel {eu}, e negli USA le opere pubblicate nel {us}.", "pdd_link": "Vedi l'elenco →",
        "vuoto": "Nessuna voce con questi filtri.",
        "fine_h": "Un calendario che si aggiorna da solo", "fine_p": "Sottoscrivi il calendario in Google Calendar, Apple Calendar o Outlook: gli anniversari con una data precisa arrivano da soli. Le voci di cui si conosce solo l'anno restano nella tabella CSV.",
        "nota": "Dati da fonti aperte (Wikidata, catalogo SBN), possono contenere errori. Le prime edizioni sono quelle riportate da Wikidata; per molte si conosce solo l'anno. Le edizioni SBN contano le registrazioni dell'autore in italiano: non dicono se un titolo è ancora in commercio. Controlla sempre la data prima di usarla in una campagna.",
        "navt": [("Autori", "/"), ("Opere USA", "/#/us/{a}"), ("Calendario", None)], "altra": ("EN", "/en/calendar/{a}/"),
        "home": "/", "piede": "piede", "post_n": "{e} anni fa, il {g} {m} {y}, nasceva {nome}.", "post_n0": "{e} anni fa, nel {y}, nasceva {nome}.",
        "post_m": "{e} anni fa, il {g} {m} {y}, moriva {nome}.", "post_m0": "{e} anni fa, nel {y}, moriva {nome}.",
        "post_p": "{e} anni fa, il {g} {m} {y}, usciva «{nome}»{aut}.", "post_p0": "{e} anni fa, nel {y}, usciva «{nome}»{aut}.", "di": " di ",
        "ev_n": "Nascita di {nome} ({e} anni)", "ev_m": "Morte di {nome} ({e} anni)", "ev_p": "Prima edizione di «{nome}» ({e} anni)",
        "csv_cols": ["tipo", "nome", "autore", "anni", "anno_evento", "data", "edizioni_italiane_autore", "ultima_edizione_italiana", "fonte_wikidata"],
    },
    "en": {
        "html": "en", "titolo": "Literary anniversaries {a}: births, deaths and first editions calendar · Public Domain Radar",
        "descr": "Literary anniversaries of {a}: births, deaths and first editions with a round anniversary, day by day. For publishers, booksellers and creators. Open data, with .ics calendar and CSV table.",
        "occ": "Literary anniversaries · {a}", "h1a": "What to remember in ", "lead": "Births, deaths and first editions with a round anniversary. For each: the author's Italian editions in the SBN catalogue and a ready text for a post. For publishers, booksellers and creators.",
        "ics": "Add to your calendar (.ics)", "csv": "Download the table (CSV)",
        "mese": "Month", "tipo": "Type", "tutti": "All", "tutte": "All", "senza": "No recent Italian edition",
        "tipi": {"prima edizione": "First edition", "nascita": "Birth", "morte": "Death"},
        "filtri_tipo": [("prima edizione", "First editions"), ("nascita", "Births"), ("morte", "Deaths")],
        "anni": "{n} years", "voce": "entry", "voci": "entries", "durante": "During the year", "nd": "day unknown", "soloanno": "{a} · year only",
        "sbn": "Author's Italian editions (SBN)", "sbn_n": "{n} editions · latest: {u}", "sbn_zero": "none found in SBN", "sbn_poche": "few found ({n}, latest: {u}): to be checked", "sbn_senza_anno": "{n} editions",
        "copia": "Copy text for a post →", "copiato": "Copied ✓", "aggiungi": "Add to calendar →",
        "pdd": "Public Domain Day", "pdd_txt": "Authors who died in {eu} enter the public domain in Europe, and works published in {us} in the USA.", "pdd_link": "See the list →",
        "vuoto": "No entries with these filters.",
        "fine_h": "A calendar that updates itself", "fine_p": "Subscribe in Google Calendar, Apple Calendar or Outlook: the anniversaries with an exact date arrive by themselves. Entries where only the year is known stay in the CSV table.",
        "nota": "Data from open sources (Wikidata, SBN catalogue), it may contain errors. First editions are those recorded in Wikidata; for many only the year is known. SBN counts the author's records in Italian: it does not say whether a title is still in print. Always check the date before using it in a campaign.",
        "navt": [("Authors", "/en/"), ("Works USA", "/en/#/us/{a}"), ("Calendar", None)], "altra": ("IT", "/calendario/{a}/"),
        "home": "/en/", "piede": "piede", "post_n": "{e} years ago, on {m} {g}, {y}, {nome} was born.", "post_n0": "{e} years ago, in {y}, {nome} was born.",
        "post_m": "{e} years ago, on {m} {g}, {y}, {nome} died.", "post_m0": "{e} years ago, in {y}, {nome} died.",
        "post_p": "{e} years ago, on {m} {g}, {y}, “{nome}”{aut} was first published.", "post_p0": "{e} years ago, in {y}, “{nome}”{aut} was first published.", "di": " by ",
        "ev_n": "Birth of {nome} ({e} years)", "ev_m": "Death of {nome} ({e} years)", "ev_p": "First edition of “{nome}” ({e} years)",
        "csv_cols": ["type", "name", "author", "years", "event_year", "date", "author_italian_editions", "latest_italian_edition", "wikidata"],
    },
}

CSS_CAL = """
:root{--ink:#0C0C10;--carta:#F7F7F4;--verm:#FF4326;--vt:#C2301A;--muto:#5C5C66;--notte:#1C1C24;--verde:#0E3B2E;--riq:#E4E2DA;
--display:'Big Shoulders Display',Impact,'Arial Narrow',sans-serif;--testo:'Instrument Sans',system-ui,sans-serif;--mono:'DM Mono',ui-monospace,Menlo,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--carta);color:var(--ink);font-family:var(--testo);line-height:1.5;-webkit-text-size-adjust:100%}
a{color:inherit}
.barra{background:var(--ink);color:#fff;padding:18px clamp(20px,4vw,48px);display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;font-family:var(--mono);font-weight:500;font-size:12px;letter-spacing:.14em;text-transform:uppercase}
.barra a{color:#8E8E9B;text-decoration:none;margin-left:16px}.barra a:first-child{margin-left:0;color:#fff}
.barra i{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--verm);margin-right:10px}
.barra .on{color:#fff;border-bottom:2px solid var(--verm);padding-bottom:3px}
.barra span a:hover{color:#fff}
.hero{background:var(--ink);color:#fff;padding:clamp(36px,6vw,72px) 0 clamp(36px,5vw,56px);position:relative;overflow:hidden}
.hero:after{content:"";position:absolute;right:-8vw;top:60px;width:32vw;height:32vw;max-width:420px;max-height:420px;border-radius:50%;background:var(--verm)}
.in{max-width:1120px;margin:0 auto;padding:0 clamp(20px,4vw,48px);position:relative;z-index:1}
.occ{font:500 13px var(--mono);letter-spacing:.14em;text-transform:uppercase;margin:0 0 16px}
h1{font:900 clamp(48px,10vw,120px)/.88 var(--display);text-transform:uppercase;margin:0 0 20px;max-width:10ch}
h1 em{font-style:normal;color:var(--verm)}
.lead{max-width:36rem;color:#D2CFC4;font-size:18px;margin:0 0 26px}
.abb{display:inline-flex;gap:12px;flex-wrap:wrap}
.btn{display:inline-block;padding:14px 20px;font:500 13px var(--mono);letter-spacing:.08em;text-transform:uppercase;text-decoration:none;border:2px solid #fff;color:#fff;background:none;cursor:pointer}
.btn.p{background:#fff;color:var(--ink)}
.filtri{background:#fff;border-bottom:1px solid var(--riq);position:sticky;top:0;z-index:5}
.filtri .in{display:flex;flex-wrap:wrap;gap:12px 34px;padding-top:12px;padding-bottom:12px;align-items:center}
.gr{display:flex;flex-wrap:wrap;gap:6px;align-items:center}.gr>span{font:500 11px var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--muto);margin-right:6px}
.ch{font:500 12px var(--mono);letter-spacing:.05em;text-transform:uppercase;padding:0 12px;min-height:44px;border:1.5px solid var(--ink);background:#fff;color:var(--ink);cursor:pointer}
.ch[aria-pressed="true"]{background:var(--ink);color:#fff}
.mese{padding:clamp(40px,6vw,72px) 0 0}
.mese h2{font:900 clamp(40px,7vw,80px)/.9 var(--display);text-transform:uppercase;margin:0 0 6px;display:flex;justify-content:space-between;align-items:baseline;border-bottom:3px solid var(--ink);padding-bottom:10px}
.mese h2 small{font:500 12px var(--mono);letter-spacing:.1em;color:var(--muto)}
.ev{display:grid;grid-template-columns:96px 1fr 270px;gap:6px 24px;padding:22px 0;border-bottom:1px solid var(--riq)}
.gg{font:900 64px/.85 var(--display);color:var(--ink)}.gg.nd{font-size:34px;color:var(--muto)}
.gg small{display:block;font:500 11px var(--mono);letter-spacing:.1em;color:var(--muto);margin-top:6px;text-transform:uppercase}
.tipo{font:500 11px var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--vt);margin-bottom:4px}
.tipo b{background:var(--ink);color:#fff;padding:3px 8px;margin-right:8px;font-weight:500;letter-spacing:.08em}
.ev h3{font:900 clamp(26px,3.6vw,38px)/1 var(--display);text-transform:uppercase;margin:0 0 4px}
.ev .au{color:var(--muto);margin:0 0 10px}
.az{font-size:14px;color:#33333B;border-left:3px solid var(--verm);padding-left:12px;align-self:start}
.az b{display:block;font:500 11px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muto);margin-bottom:4px}
.az a,.az button{display:inline-block;margin-top:8px;font:500 12px var(--mono);letter-spacing:.06em;text-transform:uppercase;background:none;border:0;padding:6px 0;color:var(--vt);cursor:pointer;text-decoration:underline;text-underline-offset:3px}
.spec{background:var(--verm);color:var(--ink);padding:26px 28px;margin:26px 0 0;display:grid;grid-template-columns:96px 1fr;gap:24px}
.spec h3{font:900 clamp(30px,4vw,46px)/1 var(--display);text-transform:uppercase;margin:0 0 6px}
.spec p{margin:0 0 10px;max-width:40rem}.spec a{font:500 13px var(--mono);letter-spacing:.06em;text-transform:uppercase}
.spec a+a{margin-left:18px}
.fine{background:var(--ink);color:#fff;margin-top:72px;padding:clamp(44px,6vw,72px) 0}
.fine h2{font:900 clamp(34px,6vw,64px)/.95 var(--display);text-transform:uppercase;margin:0 0 14px}
.fine p{max-width:38rem;color:#D2CFC4}
.nota{font-size:13px;color:var(--muto);padding:22px 0 0;max-width:46rem}
.vuoto{padding:40px 0;color:var(--muto)}
footer{background:var(--ink);color:#B9B9C6;font-size:13px;padding:32px 20px}footer p{max-width:780px;margin:0 auto 10px}footer a{color:#fff}
[hidden]{display:none!important}
@media(max-width:820px){.filtri{position:static}.ev{grid-template-columns:70px 1fr}.ev .az{grid-column:2}.gg{font-size:50px}.spec{grid-template-columns:1fr}.hero:after{width:60vw;height:60vw;right:-22vw;top:40px}}
"""


def esc(s):
    return html.escape(str(s), quote=True)


def nome_di(v, lang):
    return (v.get("it") if lang == "it" and v.get("it") else v["nome"]).strip()


def autore_di(v):
    return v.get("autore") or ""


def eta_txt(v):
    return v["anni"]


def testo_post(v, lang):
    t = T[lang]
    k = {"nascita": "n", "morte": "m", "prima edizione": "p"}[v["tipo"]]
    aut = (t["di"] + autore_di(v)) if v["tipo"] == "prima edizione" and autore_di(v) else ""
    base = dict(e=v["anni"], y=v["anno"], nome=nome_di(v, lang), aut=aut)
    if v.get("mese"):
        return t["post_" + k].format(g=v["giorno"], m=MESI[lang][v["mese"] - 1], **base)
    return t["post_" + k + "0"].format(**base)


def evento_ics(v, lang, anno):
    t = T[lang]
    k = {"nascita": "ev_n", "morte": "ev_m", "prima edizione": "ev_p"}[v["tipo"]]
    return t[k].format(nome=nome_di(v, lang), e=v["anni"])


def ics_testo(vv, lang, anno):
    def e(s):
        return str(s).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
    righe = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Public Domain Radar//Literary anniversaries//" + lang.upper(),
             "CALSCALE:GREGORIAN", "X-WR-CALNAME:" + e("Public Domain Radar · " + T[lang]["occ"].format(a=anno)),
             "X-WR-TIMEZONE:Europe/Rome"]
    ora = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    for v in vv:
        if not v.get("mese"):
            continue
        try:
            d = datetime.date(anno, v["mese"], v["giorno"])
        except ValueError:
            continue
        fine = d + datetime.timedelta(days=1)
        righe += ["BEGIN:VEVENT", f"UID:{v['tipo'].replace(' ', '')}-{v['qid']}-{anno}@publicdomainradar.com", f"DTSTAMP:{ora}",
                  f"DTSTART;VALUE=DATE:{d:%Y%m%d}", f"DTEND;VALUE=DATE:{fine:%Y%m%d}",
                  "SUMMARY:" + e(evento_ics(v, lang, anno)), "DESCRIPTION:" + e(testo_post(v, lang) + " https://publicdomainradar.com"),
                  "TRANSP:TRANSPARENT", "END:VEVENT"]
    righe.append("END:VCALENDAR")
    return "\r\n".join(righe) + "\r\n"


def csv_testo(vv, lang, anno):
    t = T[lang]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(t["csv_cols"])
    for v in vv:
        d = f"{anno}-{v['mese']:02d}-{v['giorno']:02d}" if v.get("mese") else ""
        s = v.get("sbn") or {}
        w.writerow([t["tipi"][v["tipo"]], nome_di(v, lang), autore_di(v) if v["tipo"] == "prima edizione" else "", v["anni"], v["anno"], d,
                    s.get("edizioni", ""), s.get("ultimo", ""), "https://www.wikidata.org/wiki/" + v["qid"]])
    return "\ufeff" + buf.getvalue()


def scheda(v, lang, anno):
    t = T[lang]
    nome = nome_di(v, lang)
    orig = v["nome"] if v["nome"] != nome else ""
    dat = v.get("mese")
    if dat:
        gg = f'<div class="gg">{v["giorno"]}<small>{BREVI[lang][v["mese"] - 1]}</small></div>'
    else:
        gg = f'<div class="gg nd">?<small>{esc(t["soloanno"].format(a=anno))}</small></div>'
    s = v.get("sbn")
    sbn_html = ""
    recente = 0
    attendibile = False
    if s is not None:
        ed = s.get("edizioni") or 0
        # molto noto ma quasi nessuna edizione trovata: quasi sempre è un errore di abbinamento, non si mostra
        attendibile = not (v["pagine"] >= 40 and ed <= 3) and not (v["tipo"] == "prima edizione" and ed == 0)
        if attendibile:
            if ed >= 4:
                testo = t["sbn_n"].format(n=ed, u=s["ultimo"]) if s.get("ultimo") else t["sbn_senza_anno"].format(n=ed)
            elif ed:
                testo = t["sbn_poche"].format(n=ed, u=s.get("ultimo") or "?")
            else:
                testo = t["sbn_zero"]
            recente = 1 if (s.get("ultimo") or 0) >= ANNI_RECENTE else 0
            sbn_html = f'<b>{esc(t["sbn"])}</b>{esc(testo)}<br>'
    azioni = ""
    if dat:
        azioni += f'<button type="button" class="aggiungi" data-ics="{esc(v["tipo"])}-{v["qid"]}">{esc(t["aggiungi"])}</button><br>'
    azioni += f'<button type="button" class="copia" data-testo="{esc(testo_post(v, lang))}">{esc(t["copia"])}</button>'
    au = ""
    if v["tipo"] == "prima edizione":
        au = esc(autore_di(v)) + (f' · <i>{esc(orig)}</i>' if orig else "")
        au = f'<p class="au">{au}</p>' if au else ""
    elif orig:
        au = f'<p class="au"><i>{esc(orig)}</i></p>'
    return (f'<div class="ev" data-tipo="{esc(v["tipo"])}" data-mese="{v.get("mese") or 0}" data-vecchia="{1 if (attendibile and not recente) else 0}" '
            f'data-id="{esc(v["tipo"])}-{v["qid"]}" data-ics-d="{anno}{v["mese"]:02d}{v["giorno"]:02d}" data-ics-t="{esc(evento_ics(v, lang, anno))}">'
            f'{gg}<div><div class="tipo"><b>{esc(t["tipi"][v["tipo"]])}</b>{esc(t["anni"].format(n=v["anni"]))} · {v["anno"]}</div>'
            f'<h3>{esc(nome)}</h3>{au}</div><div class="az">{sbn_html}{azioni}</div></div>'
            if dat else
            f'<div class="ev" data-tipo="{esc(v["tipo"])}" data-mese="0" data-vecchia="{1 if (attendibile and not recente) else 0}" data-id="{esc(v["tipo"])}-{v["qid"]}">'
            f'{gg}<div><div class="tipo"><b>{esc(t["tipi"][v["tipo"]])}</b>{esc(t["anni"].format(n=v["anni"]))} · {v["anno"]}</div>'
            f'<h3>{esc(nome)}</h3>{au}</div><div class="az">{sbn_html}{azioni}</div></div>')


def pagina(dati, lang):
    from pagine import TESTA, PIEDE  # evita l'import circolare all'avvio
    anno = dati["anno"]
    t = T[lang]
    vv = dati["voci"]
    url = f"{SITO}{'/en/calendar' if lang == 'en' else '/calendario'}/{anno}/"
    eu, us = anno - 71, anno - 96
    spec_it = (f'<div class="spec"><div class="gg">1<small>{BREVI[lang][0]}</small></div><div><h3>{esc(t["pdd"])}</h3>'
               f'<p>{esc(t["pdd_txt"].format(eu=eu, us=us))}</p>'
               f'<a href="{"/en" if lang == "en" else ""}/#/{anno}">{"Authors" if lang == "en" else "Autori"} →</a>'
               f'<a href="{"/en" if lang == "en" else ""}/#/us/{anno}">{"Works USA" if lang == "en" else "Opere USA"} →</a></div></div>')
    mesi = {}
    for v in vv:
        mesi.setdefault(v.get("mese") or 0, []).append(v)
    corpo = []
    ordine = list(range(1, 13)) + [0]
    for m in ordine:
        elenco = mesi.get(m, [])
        extra = spec_it if m == 1 else ""
        if not elenco and not extra:
            continue
        titolo = MESI[lang][m - 1] if m else t["durante"]
        n = len(elenco)
        sotto = f"{n} {t['voce'] if n == 1 else t['voci']}" + (f" · {t['nd']}" if m == 0 else "")
        elenco.sort(key=lambda v: ((v.get("giorno") or 0), -v["pagine"]))
        corpo.append(f'<section class="mese" data-mese="{m}"><h2>{esc(titolo.capitalize() if m else titolo)} <small>{esc(sotto)}</small></h2>{extra}'
                     + "".join(scheda(v, lang, anno) for v in elenco) + "</section>")
    mesi_btn = "".join(f'<button type="button" class="ch" data-mese="{m}" aria-pressed="false">{BREVI[lang][m - 1]}</button>' for m in range(1, 13))
    tipi_btn = "".join(f'<button type="button" class="ch" data-tipo="{k}" aria-pressed="false">{esc(n)}</button>' for k, n in t["filtri_tipo"])
    base_ics = f"{url}anniversari-{anno}.ics" if lang == "it" else f"{url}anniversaries-{anno}.ics"
    base_csv = f"anniversari-{anno}.csv" if lang == "it" else f"anniversaries-{anno}.csv"
    ics_nome = base_ics.rsplit("/", 1)[-1]
    nav = "".join((f'<a class="on" href="{url}">{n}</a>' if h is None else f'<a href="{h.format(a=anno)}">{n}</a>') for n, h in t["navt"])
    altra_lingua = f'<span>{nav}<a href="{t["altra"][1].format(a=anno)}" hreflang="{"en" if lang == "it" else "it"}">{t["altra"][0]}</a></span>'
    faq_ld = ""
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": t["titolo"].format(a=anno), "url": url, "inLanguage": lang,
          "dateModified": dati.get("generato"), "isPartOf": {"@type": "WebSite", "name": "Public Domain Radar", "url": SITO + ("/en/" if lang == "en" else "/")}}
    jsonld = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    alt = (f'<link rel="alternate" hreflang="it" href="{SITO}/calendario/{anno}/">\n<link rel="alternate" hreflang="en" href="{SITO}/en/calendar/{anno}/">\n')
    testa = TESTA.format(lang=lang, titolo=esc(t["titolo"].format(a=anno)), descr=esc(t["descr"].format(a=anno)), url=url, alterne=alt,
                         og_tipo="website", jsonld=jsonld, css=CSS_CAL, home=t["home"], altra_lingua=altra_lingua)
    js = """<script>
(function(){
var st={mese:0,tipo:"",vecchia:false};
var evs=[].slice.call(document.querySelectorAll(".ev"));
function applica(){
  var visibili=0;
  evs.forEach(function(e){
    var ok=(!st.mese||e.dataset.mese==st.mese)&&(!st.tipo||e.dataset.tipo===st.tipo)&&(!st.vecchia||e.dataset.vecchia==="1");
    e.hidden=!ok; if(ok)visibili++;
  });
  [].slice.call(document.querySelectorAll(".mese")).forEach(function(s){
    var n=s.querySelectorAll(".ev:not([hidden])").length, spec=s.querySelector(".spec");
    s.hidden=!n&&!(spec&&!st.tipo&&!st.vecchia&&(!st.mese||s.dataset.mese==st.mese));
  });
  document.getElementById("vuoto").hidden=visibili>0;
}
function gruppo(attr,chiave){
  [].slice.call(document.querySelectorAll(".ch["+attr+"]")).forEach(function(b){
    b.addEventListener("click",function(){
      var on=b.getAttribute("aria-pressed")==="true";
      [].slice.call(document.querySelectorAll(".ch["+attr+"]")).forEach(function(x){x.setAttribute("aria-pressed","false")});
      if(!on){b.setAttribute("aria-pressed","true");st[chiave]=b.getAttribute(attr)}else st[chiave]=chiave==="mese"?0:"";
      applica();
    });
  });
}
gruppo("data-mese","mese");gruppo("data-tipo","tipo");
var bv=document.getElementById("vecchia");
bv.addEventListener("click",function(){st.vecchia=!st.vecchia;bv.setAttribute("aria-pressed",st.vecchia);applica()});
[].slice.call(document.querySelectorAll(".copia")).forEach(function(b){
  b.addEventListener("click",function(){
    var t=b.dataset.testo+" https://publicdomainradar.com", orig=b.textContent;
    var fine=function(){b.textContent=COPIATO;setTimeout(function(){b.textContent=orig},1800)};
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(fine,function(){window.prompt("",t)})}else{window.prompt("",t)}
  });
});
[].slice.call(document.querySelectorAll(".aggiungi")).forEach(function(b){
  b.addEventListener("click",function(){
    var e=b.closest(".ev"),d=e.dataset.icsD,t=e.dataset.icsT;
    var f=new Date(Date.UTC(+d.slice(0,4),+d.slice(4,6)-1,+d.slice(6,8)+1)),fs=f.getUTCFullYear()+("0"+(f.getUTCMonth()+1)).slice(-2)+("0"+f.getUTCDate()).slice(-2);
    var x=["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Public Domain Radar//EN","BEGIN:VEVENT","UID:"+e.dataset.id+"@publicdomainradar.com","DTSTAMP:"+d+"T000000Z","DTSTART;VALUE=DATE:"+d,"DTEND;VALUE=DATE:"+fs,"SUMMARY:"+t.replace(/[,;]/g,function(c){return "\\\\"+c}),"END:VEVENT","END:VCALENDAR"].join("\\r\\n");
    var a=document.createElement("a");a.href=URL.createObjectURL(new Blob([x],{type:"text/calendar"}));a.download=e.dataset.id+".ics";document.body.appendChild(a);a.click();a.remove();
  });
});
})();
</script>""".replace("COPIATO", json.dumps(t["copiato"]))
    out = [testa]
    out.append(f"""<header class="hero"><div class="in">
<p class="occ">{esc(t["occ"].format(a=anno))}</p>
<h1>{esc(t["h1a"])}<em>{anno}</em></h1>
<p class="lead">{esc(t["lead"])}</p>
<div class="abb"><a class="btn p" href="{ics_nome}">{esc(t["ics"])}</a><a class="btn" href="{base_csv}">{esc(t["csv"])}</a></div>
</div></header>
<div class="filtri"><div class="in">
<div class="gr" role="group"><span>{esc(t["mese"])}</span>{mesi_btn}</div>
<div class="gr" role="group"><span>{esc(t["tipo"])}</span>{tipi_btn}</div>
<div class="gr"><button type="button" class="ch" id="vecchia" aria-pressed="false">{esc(t["senza"])}</button></div>
</div></div>
<main class="in">
""")
    out += corpo
    out.append(f'<p class="vuoto" id="vuoto" hidden>{esc(t["vuoto"])}</p>\n<p class="nota">{esc(t["nota"])}</p>\n</main>\n')
    out.append(f"""<section class="fine"><div class="in"><h2>{esc(t["fine_h"])}</h2><p>{esc(t["fine_p"])}</p><a class="btn p" href="{ics_nome}">{esc(t["ics"])}</a></div></section>
{js}
""")
    out.append(PIEDE[lang])
    return "".join(out), url


def crea_calendario():
    """Scrive le pagine IT/EN con .ics e .csv per ogni anno con dati. Restituisce gli indirizzi."""
    urls = []
    for f in sorted((RADICE / "data").glob("anniversari-[0-9][0-9][0-9][0-9].json")):
        dati = json.loads(f.read_text(encoding="utf-8"))
        if not dati.get("voci"):
            continue
        anno = dati["anno"]
        for lang in ("it", "en"):
            html_, url = pagina(dati, lang)
            d = RADICE / ("en/calendar" if lang == "en" else "calendario") / str(anno)
            d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text(html_, encoding="utf-8")
            nome = f"anniversari-{anno}" if lang == "it" else f"anniversaries-{anno}"
            (d / f"{nome}.ics").write_text(ics_testo(dati["voci"], lang, anno), encoding="utf-8", newline="")
            (d / f"{nome}.csv").write_text(csv_testo(dati["voci"], lang, anno), encoding="utf-8", newline="")
            urls.append(url)
    return urls
