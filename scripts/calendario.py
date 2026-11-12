"""Pagine del calendario degli anniversari letterari (italiano e inglese), con .ics e .csv.
Legge data/anniversari-<anno>.json (scritto da anniversari.py). Chiamato da pagine.py."""
import csv
import datetime
import html
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import schede as SCH

RADICE = Path(__file__).resolve().parent.parent
SITO = "https://publicdomainradar.com"
MESI = {"it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
        "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}
BREVI = {"it": ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"],
         "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}

T = {
    "it": {
        "html": "it", "titolo": "Calendario degli anniversari letterari {a}: nascite, morti e prime edizioni · Public Domain Radar",
        "descr": "Gli anniversari letterari del {a}: nascite, morti e prime edizioni con anniversario tondo, giorno per giorno. Dati aperti, con calendario .ics e tabella CSV.",
        "occ": "Anniversari letterari · {a}", "h1a": "Cosa ricordare nel ", "lead": "Le ricorrenze letterarie da ricordare: nascite, morti e prime edizioni con anniversario tondo, giorno per giorno. Ogni voce ha una scheda da condividere.",
        "ics": "Aggiungi al tuo calendario (.ics)", "csv": "Scarica la tabella (CSV)",
        "mese": "Mese", "tipo": "Tipo", "tutti": "Tutti", "tutte": "Tutte", "eta": "Anniversario", "piu": "oltre 200",
        "tipi": {"prima edizione": "Prima edizione", "nascita": "Nascita", "morte": "Morte"},
        "filtri_tipo": [("prima edizione", "Prime edizioni"), ("nascita", "Nascite"), ("morte", "Morti")],
        "anni": "{n} anni", "voce": "voce", "voci": "voci", "durante": "Durante l'anno", "nd": "giorno non noto", "soloanno": "{a} · solo anno",
        "wiki": "Leggi su Wikipedia →", "orig": "Titolo originale", "opere": "Opere principali", "nobel": "Nobel per la letteratura {y}",
        "copia": "Copia testo per un post →", "copiato": "Copiato ✓", "aggiungi": "Aggiungi al calendario →",
        "pdd": "Public Domain Day", "pdd_txt": "Entrano in pubblico dominio in Europa gli autori morti nel {eu}, e negli USA le opere pubblicate nel {us}.", "pdd_link": "Vedi l'elenco →",
        "vuoto": "Nessuna voce con questi filtri.",
        "fine_h": "Un calendario che si aggiorna da solo", "fine_p": "Sottoscrivi il calendario in Google Calendar, Apple Calendar o Outlook: gli anniversari con una data precisa arrivano da soli. Le voci di cui si conosce solo l'anno restano nella tabella CSV.",
        "nota": "Dati da fonti aperte (Wikidata, Wikipedia): possono contenere errori. Per molte opere si conosce solo l'anno di pubblicazione, e per alcune ricorrenze le fonti indicano date diverse. Controlla sempre la data prima di usarla in una campagna.",
        "navt": [("Autori", "/"), ("Opere USA", "/#/us/{a}"), ("Calendario", None)], "altra": ("EN", "/en/calendar/{a}/"),
        "home": "/", "piede": "piede", "post_n": "{e} anni fa, il {g} {m} {y}, nasceva {nome}.", "post_n0": "{e} anni fa, nel {y}, nasceva {nome}.",
        "post_m": "{e} anni fa, il {g} {m} {y}, moriva {nome}.", "post_m0": "{e} anni fa, nel {y}, moriva {nome}.",
        "post_p": "{e} anni fa, il {g} {m} {y}, usciva «{nome}»{aut}.", "post_p0": "{e} anni fa, nel {y}, usciva «{nome}»{aut}.", "di": " di ",
        "ev_n": "Nascita di {nome} ({e} anni)", "ev_m": "Morte di {nome} ({e} anni)", "ev_p": "Prima edizione di «{nome}» ({e} anni)",
        "csv_cols": ["tipo", "nome", "autore", "anni", "anno_evento", "data", "wikidata"],
    },
    "en": {
        "html": "en", "titolo": "Literary anniversaries {a}: births, deaths and first editions calendar · Public Domain Radar",
        "descr": "Literary anniversaries of {a}: births, deaths and first editions with a round anniversary, day by day. Open data, with .ics calendar and CSV table.",
        "occ": "Literary anniversaries · {a}", "h1a": "What to remember in ", "lead": "Literary anniversaries worth remembering: births, deaths and first editions with a round anniversary, day by day. Every entry has a short profile and a card to share.",
        "ics": "Add to your calendar (.ics)", "csv": "Download the table (CSV)",
        "mese": "Month", "tipo": "Type", "tutti": "All", "tutte": "All", "eta": "Anniversario", "piu": "oltre 200",
        "tipi": {"prima edizione": "First edition", "nascita": "Birth", "morte": "Death"},
        "filtri_tipo": [("prima edizione", "First editions"), ("nascita", "Births"), ("morte", "Deaths")],
        "anni": "{n} years", "voce": "entry", "voci": "entries", "durante": "During the year", "nd": "day unknown", "soloanno": "{a} · year only",
        "wiki": "Read on Wikipedia →", "orig": "Original title", "opere": "Main works", "nobel": "Nobel Prize in Literature {y}",
        "copia": "Copy text for a post →", "copiato": "Copied ✓", "aggiungi": "Add to calendar →",
        "pdd": "Public Domain Day", "pdd_txt": "Authors who died in {eu} enter the public domain in Europe, and works published in {us} in the USA.", "pdd_link": "See the list →",
        "vuoto": "No entries with these filters.",
        "fine_h": "A calendar that updates itself", "fine_p": "Subscribe in Google Calendar, Apple Calendar or Outlook: the anniversaries with an exact date arrive by themselves. Entries where only the year is known stay in the CSV table.",
        "nota": "Data from open sources (Wikidata, Wikipedia): it may contain errors. For many works only the year of publication is known, and for some anniversaries sources give different dates. Always check the date before using it in a campaign.",
        "navt": [("Authors", "/en/"), ("Works USA", "/en/#/us/{a}"), ("Calendar", None)], "altra": ("IT", "/calendario/{a}/"),
        "home": "/en/", "piede": "piede", "post_n": "{e} years ago, on {m} {g}, {y}, {nome} was born.", "post_n0": "{e} years ago, in {y}, {nome} was born.",
        "post_m": "{e} years ago, on {m} {g}, {y}, {nome} died.", "post_m0": "{e} years ago, in {y}, {nome} died.",
        "post_p": "{e} years ago, on {m} {g}, {y}, “{nome}”{aut} was first published.", "post_p0": "{e} years ago, in {y}, “{nome}”{aut} was first published.", "di": " by ",
        "ev_n": "Birth of {nome} ({e} years)", "ev_m": "Death of {nome} ({e} years)", "ev_p": "First edition of “{nome}” ({e} years)",
        "csv_cols": ["type", "name", "author", "years", "event_year", "date", "wikidata"],
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
.ev{display:grid;grid-template-columns:96px 1fr 230px;gap:6px 24px;padding:22px 0;border-bottom:1px solid var(--riq)}
.gg{font:900 64px/.85 var(--display);color:var(--ink)}.gg.nd{font-size:34px;color:var(--muto)}
.gg small{display:block;font:500 11px var(--mono);letter-spacing:.1em;color:var(--muto);margin-top:6px;text-transform:uppercase}
.tipo{font:500 11px var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--vt);margin-bottom:4px}
.tipo b{background:var(--ink);color:#fff;padding:3px 8px;margin-right:8px;font-weight:500;letter-spacing:.08em}
.ev h3{font:900 clamp(26px,3.6vw,38px)/1.12 var(--display);text-transform:uppercase;margin:0 0 4px;padding-top:12px}
.ev .au{color:var(--muto);margin:0 0 10px}
.az{font-size:15px;line-height:1.45;color:#33333B;border-left:3px solid var(--verm);padding-left:14px;display:flex;flex-direction:column;gap:6px;margin-top:12px;max-width:44rem}
.az b{font:500 11px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muto);font-weight:500}
.az .nobel{align-self:flex-start;font:500 11px var(--mono);letter-spacing:.08em;text-transform:uppercase;background:var(--ink);color:#fff;padding:3px 8px}
.az a{align-self:flex-start;font:500 12px var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--vt);text-decoration:underline;text-underline-offset:3px;padding:4px 0}
.az2{display:flex;flex-direction:column;align-items:flex-start;gap:6px;align-self:start;margin-top:12px}
.az2 button{font:500 12px var(--mono);letter-spacing:.06em;text-transform:uppercase;background:none;border:0;padding:4px 0;color:var(--vt);cursor:pointer;text-decoration:underline;text-underline-offset:3px;text-align:left}
.spec{background:var(--verm);color:var(--ink);padding:26px 0 30px;margin:26px 0 0;display:grid;grid-template-columns:96px 1fr;gap:6px 24px;box-shadow:-16px 0 0 var(--verm),16px 0 0 var(--verm)}
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
@media(max-width:820px){.filtri{position:static}.ev{grid-template-columns:70px 1fr}.ev .az2{grid-column:2;flex-direction:row;flex-wrap:wrap;gap:4px 20px;margin-top:0}.gg{font-size:50px}.spec{grid-template-columns:70px 1fr}.hero:after{width:60vw;height:60vw;right:-22vw;top:40px}}
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
    if v.get("mese") and v.get("giorno"):
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
        if not (v.get("mese") and v.get("giorno")):
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
        d = f"{anno}-{v['mese']:02d}-{v['giorno']:02d}" if v.get("mese") and v.get("giorno") else (f"{anno}-{v['mese']:02d}" if v.get("mese") else "")
        w.writerow([t["tipi"][v["tipo"]], nome_di(v, lang), autore_di(v) if v["tipo"] == "prima edizione" else "", v["anni"], v["anno"], d,
                    "https://www.wikidata.org/wiki/" + v["qid"]])
    return "\ufeff" + buf.getvalue()


def info_html(v, lang):
    """Colonna destra: chi è / cos'è, in poche righe (da Wikidata e Wikipedia)."""
    t = T[lang]
    sc = ((v.get("scheda") or {}).get(lang)) or {}
    righe = []
    if v["tipo"] == "prima edizione":
        det = [x for x in (", ".join(sc.get("generi") or []), sc.get("lingua")) if x]
        if det:
            righe.append(f'<b>{esc(" · ".join(det))}</b>')
        orig = sc.get("titolo_orig")
        if orig and orig.strip().lower() != nome_di(v, lang).lower():
            righe.append(f'<span>{esc(t["orig"])}: <i>{esc(orig)}</i></span>')
    else:
        det = []
        if sc.get("paesi"):
            det.append(", ".join(sc["paesi"][-1:]))
        if sc.get("nato") and sc.get("morto"):
            det.append(f'{sc["nato"]}–{sc["morto"]}')
        elif sc.get("nato"):
            det.append(("nato nel " if lang == "it" else "born ") + str(sc["nato"]))
        if det:
            righe.append(f'<b>{esc(" · ".join(det))}</b>')
    if sc.get("desc"):
        righe.append(f'<span>{esc(sc["desc"][:1].upper() + sc["desc"][1:])}</span>')
    if v["tipo"] != "prima edizione" and sc.get("opere"):
        righe.append(f'<span>{esc(t["opere"])}: {esc(", ".join(sc["opere"]))}</span>')
    if sc.get("nobel"):
        righe.append(f'<span class="nobel">{esc(t["nobel"].format(y=sc["nobel"]))}</span>')
    wiki = sc.get("wiki") or ((v.get("scheda") or {}).get("en" if lang == "it" else "it") or {}).get("wiki")
    if wiki:
        righe.append(f'<a href="{esc(wiki)}" rel="noopener" target="_blank">{esc(t["wiki"])}</a>')
    return "".join(righe)


def scheda(v, lang, anno):
    t = T[lang]
    nome = nome_di(v, lang)
    orig = v["nome"] if v["nome"] != nome else ""
    dat = v.get("mese") and v.get("giorno")
    if dat:
        gg = f'<div class="gg">{v["giorno"]}<small>{BREVI[lang][v["mese"] - 1]}</small></div>'
    elif v.get("mese"):
        gg = f'<div class="gg nd">—<small>{BREVI[lang][v["mese"] - 1]}</small></div>'
    else:
        gg = f'<div class="gg nd">?<small>{esc(t["soloanno"].format(a=anno))}</small></div>'
    azioni = ""
    if dat:
        azioni += f'<button type="button" class="aggiungi" data-ics="{esc(v["tipo"])}-{v["qid"]}">{esc(t["aggiungi"])}</button>'
    if dat:
        azioni += f'<button type="button" class="crea">{esc(SCH.TESTI[lang]["crea"])}</button>'
    au = ""
    if v["tipo"] == "prima edizione":
        au = esc(autore_di(v)) + (f' · <i>{esc(orig)}</i>' if orig else "")
        au = f'<p class="au">{au}</p>' if au else ""
    elif orig:
        au = f'<p class="au"><i>{esc(orig)}</i></p>'
    sc_attr = ""
    if dat:
        sc_attr = f' data-sc="{esc(json.dumps(SCH.dati_scheda(v, lang, t, MESI[lang], nome, autore_di(v), ((v.get("scheda") or {}).get(lang)) or {}), ensure_ascii=False))}"'
    extra = f' data-ics-d="{anno}{v["mese"]:02d}{v["giorno"]:02d}" data-ics-t="{esc(evento_ics(v, lang, anno))}"' if dat else ""
    info = info_html(v, lang)
    return (f'<div class="ev" data-tipo="{esc(v["tipo"])}" data-mese="{v.get("mese") or 0}" data-eta="{v["anni"]}" '
            f'data-id="{esc(v["tipo"])}-{v["qid"]}"{extra}{sc_attr}>'
            f'{gg}<div><div class="tipo"><b>{esc(t["tipi"][v["tipo"]])}</b>{esc(t["anni"].format(n=v["anni"]))} · {v["anno"]}</div>'
            f'<h3>{esc(nome)}</h3>{au}<div class="az">{info}</div></div><div class="az2">{azioni}</div></div>')


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
        elenco.sort(key=lambda v: ((v.get("giorno") or 99), -v["pagine"]))
        corpo.append(f'<section class="mese" data-mese="{m}"><h2>{esc(titolo.capitalize() if m else titolo)} <small>{esc(sotto)}</small></h2>{extra}'
                     + "".join(scheda(v, lang, anno) for v in elenco) + "</section>")
    mesi_btn = "".join(f'<button type="button" class="ch" data-mese="{m}" aria-pressed="false">{BREVI[lang][m - 1]}</button>' for m in range(1, 13))
    eta_btn = "".join(f'<button type="button" class="ch" data-eta="{e}" aria-pressed="false">{e}</button>' for e in (50, 75, 100, 125, 150, 175, 200)) + f'<button type="button" class="ch" data-eta="piu" aria-pressed="false">{esc(t["piu"])}</button>'
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
                         og_tipo="website", jsonld=jsonld, css=CSS_CAL + SCH.CSS + __import__('marchio').CSS_MARCHIO, home=t["home"], altra_lingua=altra_lingua)
    js = """<script>
(function(){
var st={mese:0,tipo:"",eta:""};
var evs=[].slice.call(document.querySelectorAll(".ev"));
function applica(){
  var visibili=0;
  evs.forEach(function(e){
    var ok=(!st.mese||e.dataset.mese==st.mese)&&(!st.tipo||e.dataset.tipo===st.tipo)&&(!st.eta||(st.eta==="piu"?+e.dataset.eta>200:e.dataset.eta===st.eta));
    e.hidden=!ok; if(ok)visibili++;
  });
  [].slice.call(document.querySelectorAll(".mese")).forEach(function(s){
    var n=s.querySelectorAll(".ev:not([hidden])").length, spec=s.querySelector(".spec");
    s.hidden=!n&&!(spec&&!st.tipo&&!st.eta&&(!st.mese||s.dataset.mese==st.mese));
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
gruppo("data-mese","mese");gruppo("data-tipo","tipo");gruppo("data-eta","eta");
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
<div class="gr" role="group"><span>{esc(t["eta"])}</span>{eta_btn}</div>
</div></div>
<main class="in">
""")
    out += corpo
    out.append(f'<p class="vuoto" id="vuoto" hidden>{esc(t["vuoto"])}</p>\n<p class="nota">{esc(t["nota"])}</p>\n</main>\n')
    out.append(f"""<section class="fine"><div class="in"><h2>{esc(t["fine_h"])}</h2><p>{esc(t["fine_p"])}</p><a class="btn p" href="{ics_nome}">{esc(t["ics"])}</a></div></section>
{js}
{SCH.finestra(lang)}{SCH.js(lang, anno)}
""")
    out.append(PIEDE[lang])
    return "".join(out), url


def anni_approvati():
    """Anni approvati da Marco (data/calendari_approvati.json): solo questi vanno sul sito."""
    try:
        return set(json.loads((RADICE / "data" / "calendari_approvati.json").read_text(encoding="utf-8"))["anni"])
    except Exception:
        return set()


def crea_calendario():
    """Scrive le pagine IT/EN con .ics e .csv per ogni anno con dati. Restituisce gli indirizzi."""
    urls = []
    approvati = anni_approvati()
    for f in sorted((RADICE / "data").glob("anniversari-[0-9][0-9][0-9][0-9].json")):
        dati = json.loads(f.read_text(encoding="utf-8"))
        if not dati.get("voci"):
            continue
        anno = dati["anno"]
        if anno not in approvati:
            print(f"calendario {anno}: pronto ma non ancora approvato, resta fuori dal sito")
            continue
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
