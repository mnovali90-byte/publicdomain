"""Pagine del calendario degli anniversari letterari (italiano e inglese), con .ics e .csv.
Legge data/anniversari-<anno>.json (scritto da anniversari.py). Chiamato da pagine.py."""
import csv
import datetime
import html
import io
import json
from urllib.parse import quote
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import schede as SCH
import regole as R  # noqa: E402  (regole per paese in un posto solo)

RADICE = Path(__file__).resolve().parent.parent
SITO = "https://publicdomainradar.com"
MESI = {"it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
        "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}
BREVI = {"it": ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"],
         "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}

T = {
    "it": {
        "html": "it", "titolo": "Anniversari letterari {a}: scrittori, libri e ricorrenze giorno per giorno · Public Domain Radar",
        "descr": "Le ricorrenze letterarie del {a}, mese per mese: scrittori nati e morti 50, 100, 150 anni fa e libri usciti per la prima volta. Con calendario .ics e tabella CSV, da dati aperti.",
        "occ": "Anniversari letterari · {a}", "h1a": "Cosa ricordare nel ", "lead": "Le ricorrenze letterarie da ricordare: nascite, morti e prime edizioni con anniversario tondo, giorno per giorno. Ogni voce ha una scheda da condividere.",
        "ics": "Aggiungi al tuo calendario (.ics)", "csv": "Scarica la tabella (CSV)",
        "mese": "Mese", "tipo": "Tipo", "tutti": "Tutti", "tutte": "Tutte", "eta": "Anniversario", "piu": "oltre 200", "filtri": "Filtri", "attivi": "attivi",
        "tipi": {"prima edizione": "Prima edizione", "nascita": "Nascita", "morte": "Morte"},
        "filtri_tipo": [("prima edizione", "Prime edizioni"), ("nascita", "Nascite"), ("morte", "Morti")],
        "anni": "{n} anni", "voce": "voce", "voci": "voci", "durante": "Durante l'anno", "nd": "giorno non noto", "soloanno": "{a} · solo anno",
        "gp": "Dove è già libero", "wiki": "Leggi su Wikipedia →", "orig": "Titolo originale", "opere": "Opere principali", "nobel": "Nobel per la letteratura {y}",
        "copia": "Copia testo per un post →", "copiato": "Copiato ✓", "aggiungi": "Aggiungi al calendario →",
        "pdd": "Public Domain Day", "pdd_txt": "Entrano in pubblico dominio in Italia, Francia, Germania e Regno Unito gli autori morti nel {eu}, e negli USA le opere pubblicate nel {us}.", "pdd_link": "Vedi l'elenco →",
        "vuoto": "Nessuna voce con questi filtri.",
        "fine_h": "Un calendario che si aggiorna da solo", "fine_p": "Sottoscrivi il calendario in Google Calendar, Apple Calendar o Outlook: gli anniversari con una data precisa arrivano da soli. Le voci di cui si conosce solo l'anno restano nella tabella CSV.",
        "nota": "Dati da fonti aperte (Wikidata, Wikipedia): possono contenere errori. Per molte opere si conosce solo l'anno di pubblicazione, e per alcune ricorrenze le fonti indicano date diverse. Controlla sempre la data prima di usarla in una campagna.",
        "navt": [("Autori", "/radar/"), ("Opere USA", "/radar/#/us/{a}"), ("Calendario", None), ("Già pubblici", "/gia-pubblici/")], "altra": ("EN", "/en/calendar/{a}/"),
        "home": "/", "piede": "piede", "post_n": "{e} anni fa, il {g} {m} {y}, nasceva {nome}.", "post_n0": "{e} anni fa, nel {y}, nasceva {nome}.",
        "post_m": "{e} anni fa, il {g} {m} {y}, moriva {nome}.", "post_m0": "{e} anni fa, nel {y}, moriva {nome}.",
        "post_p": "{e} anni fa, il {g} {m} {y}, usciva «{nome}»{aut}.", "post_p0": "{e} anni fa, nel {y}, usciva «{nome}»{aut}.", "di": " di ",
        "ev_n": "Nascita di {nome} ({e} anni)", "ev_m": "Morte di {nome} ({e} anni)", "ev_p": "Prima edizione di «{nome}» ({e} anni)",
        "csv_cols": ["tipo", "nome", "autore", "anni", "anno_evento", "data", "wikidata"],
    },
    "en": {
        "html": "en", "titolo": "Literary and book anniversaries {a}: authors and books, month by month · Public Domain Radar",
        "descr": "Literary and book anniversaries of {a}, month by month: authors born and died 50, 100, 150 years ago and books first published. With .ics calendar and CSV table, from open data.",
        "occ": "Literary anniversaries · {a}", "h1a": "What to remember in ", "lead": "Literary anniversaries worth remembering: births, deaths and first editions with a round anniversary, day by day. Every entry has a short profile and a card to share.",
        "ics": "Add to your calendar (.ics)", "csv": "Download the table (CSV)",
        "mese": "Month", "tipo": "Type", "tutti": "All", "tutte": "All", "eta": "Anniversary", "piu": "over 200", "filtri": "Filters", "attivi": "active",
        "tipi": {"prima edizione": "First edition", "nascita": "Birth", "morte": "Death"},
        "filtri_tipo": [("prima edizione", "First editions"), ("nascita", "Births"), ("morte", "Deaths")],
        "anni": "{n} years", "voce": "entry", "voci": "entries", "durante": "During the year", "nd": "day unknown", "soloanno": "{a} · year only",
        "gp": "Where it is already free", "wiki": "Read on Wikipedia →", "orig": "Original title", "opere": "Main works", "nobel": "Nobel Prize in Literature {y}",
        "copia": "Copy text for a post →", "copiato": "Copied ✓", "aggiungi": "Add to calendar →",
        "pdd": "Public Domain Day", "pdd_txt": "Authors who died in {eu} enter the public domain in Italy, France, Germany and the UK, and works published in {us} in the USA.", "pdd_link": "See the list →",
        "vuoto": "No entries with these filters.",
        "fine_h": "A calendar that updates itself", "fine_p": "Subscribe in Google Calendar, Apple Calendar or Outlook: the anniversaries with an exact date arrive by themselves. Entries where only the year is known stay in the CSV table.",
        "nota": "Data from open sources (Wikidata, Wikipedia): it may contain errors. For many works only the year of publication is known, and for some anniversaries sources give different dates. Always check the date before using it in a campaign.",
        "navt": [("Authors", "/en/radar/"), ("Works USA", "/en/radar/#/us/{a}"), ("Calendar", None), ("Already public", "/en/already-public/")], "altra": ("IT", "/calendario/{a}/"),
        "home": "/en/", "piede": "piede", "post_n": "{e} years ago, on {m} {g}, {y}, {nome} was born.", "post_n0": "{e} years ago, in {y}, {nome} was born.",
        "post_m": "{e} years ago, on {m} {g}, {y}, {nome} died.", "post_m0": "{e} years ago, in {y}, {nome} died.",
        "post_p": "{e} years ago, on {m} {g}, {y}, “{nome}”{aut} was first published.", "post_p0": "{e} years ago, in {y}, “{nome}”{aut} was first published.", "di": " by ",
        "ev_n": "Birth of {nome} ({e} years)", "ev_m": "Death of {nome} ({e} years)", "ev_p": "First edition of “{nome}” ({e} years)",
        "csv_cols": ["type", "name", "author", "years", "event_year", "date", "wikidata"],
    },
}

CSS_CAL = (Path(__file__).resolve().parent / "stile_cal.css").read_text()


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


_GP = None


def cerca_gia_pubblici(v, lang):
    """Indirizzo di Già pubblici con la ricerca dell'opera o dell'autore, se c'è (dati: data/storico/pagina.json)."""
    global _GP
    if _GP is None:
        f = RADICE / "data" / "storico" / "pagina.json"
        d = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"opere": [], "autori": []}
        _GP = ({r[0]: (r[2] or r[1], r[1]) for r in d.get("opere", []) if not (len(r) > 10 and r[10])}, {a[0]: a[1] for a in d.get("autori", [])})
    opere, autori = _GP
    base = "/gia-pubblici/#" if lang == "it" else "/en/already-public/#"
    if v["tipo"] == "prima edizione" and v["qid"] in opere:
        return base + quote(opere[v["qid"]][0 if lang == "it" else 1])
    if v["tipo"] != "prima edizione" and v["qid"] in autori:
        return base + quote(nome_di(v, lang))
    return None


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
    # 25/11/2026 (Marco: «Promessi sposi, Manzoni, Machiavelli»): chi è già in pubblico dominio ha il collegamento a Già pubblici,
    # che si apre con la ricerca già fatta. Prima di Wikipedia, che resta come fonte.
    gp = cerca_gia_pubblici(v, lang)
    if gp:
        righe.append(f'<a class="gp" href="{gp}">{esc(t["gp"])}</a>')
    wiki = sc.get("wiki") or ((v.get("scheda") or {}).get("en" if lang == "it" else "it") or {}).get("wiki")
    if wiki:
        righe.append(f'<a href="{esc(wiki)}" rel="noopener" target="_blank">{esc(t["wiki"])}</a>')
    return "".join(righe)


def scheda(v, lang, anno):
    """Una voce: riga (giorno, nome, tipo) + dettagli nascosti che il pannello mostra. Tutto il testo resta nella pagina."""
    t = T[lang]
    nome = nome_di(v, lang)
    orig = v["nome"] if v["nome"] != nome else ""
    dat = v.get("mese") and v.get("giorno")
    gg = f'{v["giorno"]:02d}' if dat else "—"
    if dat:
        quando = f'{v["giorno"]} {MESI[lang][v["mese"] - 1]} {anno}' if lang == "it" else f'{v["giorno"]} {MESI[lang][v["mese"] - 1]} {anno}'
    elif v.get("mese"):
        quando = f'{MESI[lang][v["mese"] - 1]} {anno} · {t["nd"]}'
    else:
        quando = t["soloanno"].format(a=anno)
    azioni = ""
    if dat:
        azioni += f'<button type="button" class="aggiungi">{esc(t["aggiungi"])}</button>'
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
    sc = (v.get("scheda") or {})
    wiki = (sc.get(lang) or {}).get("wiki") or (sc.get("en" if lang == "it" else "it") or {}).get("wiki")
    w_attr = f' data-w="{esc(wiki)}"' if wiki else ""
    eta = v["anni"]
    return (f'<div class="ev" data-tipo="{esc(v["tipo"])}" data-mese="{v.get("mese") or 0}" data-eta="{eta}" '
            f'data-id="{esc(v["tipo"])}-{v["qid"]}" data-q="{esc(quando)}" data-y="{v["anno"]}"{extra}{sc_attr}{w_attr}>'
            f'<span class="gg">{gg}</span><h3 class="nm">{esc(nome)}</h3>'
            f'<span class="tp"><b>{esc(t["tipi"][v["tipo"]])}</b> · {esc(t["anni"].format(n=eta))}</span>'
            f'<div class="det">{au}<div class="az">{info_html(v, lang)}</div><div class="az2">{azioni}</div></div></div>')


def pagina(dati, lang):
    from pagine import testa_scheda, piede_scheda, marchio_html  # evita l'import circolare all'avvio
    anno = dati["anno"]
    t = T[lang]
    it = lang == "it"
    vv = dati["voci"]
    url = f"{SITO}{'/en/calendar' if lang == 'en' else '/calendario'}/{anno}/"
    eu, us = R.morti_liberi_nel(anno, "it"), R.pubblicate_libere_usa_nel(anno)
    app = "/en/radar/" if lang == "en" else "/radar/"
    spec = (f'<div class="ev pdd" data-tipo="pdd" data-mese="1" data-q="{esc(("1° gennaio " if it else "1 January ") + str(anno))}">'
            f'<span class="gg">01</span><h3 class="nm">{esc(t["pdd"])}</h3><span class="tp"><b>{"Pubblico dominio" if it else "Public domain"}</b></span>'
            f'<div class="det"><p class="pdt">{esc(t["pdd_txt"].format(eu=eu, us=us))}</p>'
            # 25/11/2026: diretti alle pagine (prima passavano dal radar, che non è indicizzato e rimanda comunque qui)
            f'<a href="{"/en/public-domain-" if lang == "en" else "/pubblico-dominio-"}{anno}/">{"Authors" if lang == "en" else "Autori"} →</a>'
            f'<a href="{"/en/public-domain/united-states/" if lang == "en" else "/pubblico-dominio/stati-uniti/"}">{"Works USA" if lang == "en" else "Opere USA"} →</a></div></div>')
    mesi = {}
    for v in vv:
        mesi.setdefault(v.get("mese") or 0, []).append(v)
    corpo, nav = [], []
    for m in list(range(1, 13)) + [0]:
        elenco = mesi.get(m, [])
        extra = spec if m == 1 else ""
        if not elenco and not extra:
            continue
        titolo = MESI[lang][m - 1].capitalize() if m else t["durante"]
        n = len(elenco)
        sotto = (f"{anno} · " if m else "") + f"{n} {t['voce'] if n == 1 else t['voci']}" + (f" · {t['nd']}" if m == 0 else "")
        sid = ("mese-" if it else "month-") + str(m) if m else "anno"
        elenco.sort(key=lambda v: ((v.get("giorno") or 99), -v["pagine"]))
        corpo.append(f'<section class="mo" id="{sid}" data-mese="{m}"><h2><span>{esc(titolo)}</span> <small data-s="{esc((f"{anno} · " if m else "") + "# " + t["voci"])}">{esc(sotto)}</small></h2>{extra}'
                     + "".join(scheda(v, lang, anno) for v in elenco) + f'<p class="empty">{esc(t["vuoto"])}</p></section>\n')
        nav.append(f'<a href="#{sid}" data-m="{m}" data-l="{esc((titolo + " " + str(anno)) if m else titolo)}">{esc(BREVI[lang][m - 1] if m else ("Anno" if it else "Year"))}</a>')
    tipi_btn = "".join(f'<button type="button" class="c" data-t="{k}">{esc(n)}</button>' for k, n in t["filtri_tipo"])
    eta_btn = "".join(f'<button type="button" class="c" data-a="{e}">{e}</button>' for e in (50, 75, 100, 125, 150, 175, 200)) + f'<button type="button" class="c" data-a="piu">{esc(t["piu"])}</button>'
    base_ics = f"{url}anniversari-{anno}.ics" if it else f"{url}anniversaries-{anno}.ics"
    base_csv = f"anniversari-{anno}.csv" if it else f"anniversaries-{anno}.csv"
    ics_nome = base_ics.rsplit("/", 1)[-1]
    altra = f'<a href="{t["altra"][1].format(a=anno)}" hreflang="{"en" if it else "it"}">{t["altra"][0]}</a>'
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": t["titolo"].format(a=anno), "url": url, "inLanguage": lang,
          "dateModified": dati.get("generato"), "isPartOf": {"@type": "WebSite", "name": "Public Domain Radar", "url": SITO + ("/en/" if lang == "en" else "/")}}
    jsonld = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    alt = (f'<link rel="alternate" hreflang="it" href="{SITO}/calendario/{anno}/">\n<link rel="alternate" hreflang="en" href="{SITO}/en/calendar/{anno}/">\n')
    cal_lab = ("Calendario " if it else "Calendar ") + str(anno)
    testa = testa_scheda(lang, esc(t["titolo"].format(a=anno)), esc(t["descr"].format(a=anno)), url, alt, jsonld, altra, "@@CNT@@",
                         og_tipo="website", css_extra=CSS_CAL + SCH.CSS, main_cls="calm", body_cls="cal-b")
    testa = testa.replace('<div class="cnt">@@CNT@@</div>', f'<div class="cnt"><span id="cnt" data-l="{esc(cal_lab)}">{esc(cal_lab)}</span></div>')
    testa = testa.replace("@@MARCHIO_S@@", marchio_html(56).replace('<span class="pdr" style="--w:56px">', "").rsplit("</span>", 1)[0])
    h1a = t["h1a"].strip()
    p1, p2 = (h1a.rsplit(" ", 1) if " " in h1a else (h1a, ""))
    out = [testa]
    out.append(f"""<section class="open">
<p class="m k">{esc(t["occ"].format(a=anno))}</p>
<h1 class="h1"><span class="w"><span>{esc(p1)}</span></span> <br><span class="w"><span>{esc(p2)} <em>{anno}</em></span></span></h1>
<p class="say" id="say">{esc(t["lead"])}</p>
<div class="dl"><a href="{ics_nome}">{esc(t["ics"])}</a><a href="{base_csv}">{esc(t["csv"])}</a></div>
</section>
<div class="bar" id="bar"><nav class="months" id="months" aria-label="{"Mesi" if it else "Months"}">{"".join(nav)}</nav><button class="ft" id="ft" type="button">{esc(t["filtri"])} <b id="fn"></b> <span>[+]</span></button></div>
<div class="fp" id="fp"><div class="in">
<span class="m" style="color:var(--grey)">{esc(t["tipo"])}</span><div class="chips">{tipi_btn}</div>
<span class="m" style="color:var(--grey)">{esc(t["eta"])}</span><div class="chips">{eta_btn}</div>
</div></div>
<div class="cal" id="cal">
""")
    out += corpo
    out.append(f"""<section class="ann"><div class="sh m"><h2>{esc(t["fine_h"])}</h2><span>.ics · CSV</span></div><p>{esc(t["fine_p"])}</p>
<div class="dl"><a href="{ics_nome}">{esc(t["ics"])}</a><a href="{base_csv}">{esc(t["csv"])}</a></div></section>
</div>
<aside class="pn" id="pn" aria-live="polite"></aside>
""")
    L = {"anni": "anni" if it else "years", "agg": "Aggiungi al calendario" if it else "Add to calendar", "cond": "Condividi" if it else "Share",
         "pdd_t": "1° gennaio · ogni anno" if it else "1 January · every year"}
    out.append(JS_CAL.replace("@@L@@", json.dumps(L, ensure_ascii=False)))
    out.append(SCH.finestra(lang) + SCH.js(lang, anno))
    out.append(piede_scheda(lang, ("Fonti" if it else "Sources", esc(t["nota"]))))
    return "".join(out), url


JS_CAL = """<script>
(()=>{const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)], L=@@L@@;
const RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
const say=$('#say'); say.innerHTML=say.textContent.split(' ').map(w=>'<span class="w">'+w+'</span>').join(' ');
function ink(){ const ws=$$('#say .w'), r=say.getBoundingClientRect(); const p=Math.min(1,Math.max(0,(innerHeight*.95-r.top)/(r.height+innerHeight*.3))); const k=RM?999:Math.round(p*ws.length); ws.forEach((w,i)=>w.classList.toggle('on',i<k)); }
const esc=t=>String(t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let act=null;
function panel(r){ if(r===act) return; act=r; $$('.ev').forEach(x=>x.classList.toggle('on',x===r));
  const d=r.querySelector('.det'); let h;
  if(r.classList.contains('pdd')){
    const ls=[...d.querySelectorAll('a')].map(a=>'<a href="'+a.getAttribute('href')+'">'+esc(a.textContent)+'</a>').join('');
    h='<span class="m t">'+esc(L.pdd_t)+'</span><div class="big" style="font-size:clamp(60px,6vw,96px)">PD DAY</div><p class="d">'+esc(r.dataset.q)+'</p><p class="pdt">'+esc(d.querySelector('.pdt').textContent)+'</p><div class="acts">'+ls+'</div>';
  } else {
    const au=d.querySelector('.au'), inf=d.querySelector('.az');
    let acts='';
    if(d.querySelector('.aggiungi')) acts+='<button type="button" data-x="aggiungi">'+esc(L.agg)+' <span>+</span></button>';
    if(d.querySelector('.crea')) acts+='<button type="button" data-x="crea">'+esc(L.cond)+' <span>→</span></button>';
    const gp=d.querySelector('a.gp'); if(gp) acts+='<a href="'+esc(gp.getAttribute('href'))+'">'+esc(gp.textContent)+' <span>→</span></a>';
    if(r.dataset.w) acts+='<a href="'+esc(r.dataset.w)+'" target="_blank" rel="noopener">Wikipedia <span>↗</span></a>';
    h='<span class="m t">'+esc(r.querySelector('.tp b').textContent)+' · '+r.dataset.y+'</span><div class="big">'+r.dataset.eta+'<small>'+L.anni+'</small></div><p class="d">'+esc(r.dataset.q)+'</p>'
     +'<p class="who"><b>'+esc(r.querySelector('.nm').textContent)+'</b>'+(au?'<br>'+au.innerHTML:'')+'</p>'+(inf&&inf.innerHTML?'<div class="inf">'+inf.innerHTML+'</div>':'')+(acts?'<div class="acts">'+acts+'</div>':'');
  }
  const pn=$('#pn'); $$('#pn .ly').forEach(l=>{ l.classList.add('out'); setTimeout(()=>l.remove(),320); });
  const ly=document.createElement('div'); ly.className='ly'; ly.innerHTML=h; pn.appendChild(ly);
  requestAnimationFrame(()=>requestAnimationFrame(()=>ly.classList.add('on')));
  ly.querySelectorAll('[data-x]').forEach(b=>b.onclick=()=>{ const o=d.querySelector('.'+b.dataset.x); if(o) o.click(); });
}
let curM=null;
function pick(){ const mid=innerHeight*(innerWidth<=860?.42:.5);
  const cal=$('#cal').getBoundingClientRect(), inside=cal.top<mid&&cal.bottom>mid;
  document.body.classList.toggle('cal-in',inside);
  let best=null,bd=1e9;
  $$('.ev:not(.hide)').forEach(r=>{ const b=r.getBoundingClientRect(); if(b.bottom<0||b.top>innerHeight) return; const d=Math.abs(b.top+b.height/2-mid); if(d<bd){bd=d;best=r;} });
  if(inside&&best) panel(best);
  let m=null; $$('.mo').forEach(s=>{ if(s.getBoundingClientRect().top<mid) m=s; });
  if(m!==curM){ curM=m; const id=m?m.id:''; $$('#months a').forEach(a=>a.classList.toggle('on',a.getAttribute('href')==='#'+id));
    const on=$('#months a[href="#'+id+'"]'); if(on){ const nav=$('#months'); nav.scrollTo({left:nav.scrollLeft+(on.getBoundingClientRect().left-nav.getBoundingClientRect().left)-(nav.clientWidth-on.offsetWidth)/2,behavior:RM?'auto':'smooth'}); }
    const c=$('#cnt'), lab=on?on.dataset.l:c.dataset.l;
    c.style.transform='translateY(-100%)'; setTimeout(()=>{ c.textContent=lab; c.style.transition='none'; c.style.transform='translateY(100%)'; requestAnimationFrame(()=>{ c.style.transition=''; c.style.transform=''; }); },190); }
}
$$('.ev').forEach(r=>{ r.addEventListener('click',e=>{ if(!e.target.closest('a,button')) panel(r); }); r.addEventListener('mouseenter',()=>{ if(matchMedia('(hover:hover)').matches) panel(r); }); });
const F={t:new Set(),a:new Set()};
function applyF(){
  $$('.ev:not(.pdd)').forEach(r=>{ const e=+r.dataset.eta; const okT=!F.t.size||F.t.has(r.dataset.tipo); const okA=!F.a.size||F.a.has(String(e))||(F.a.has('piu')&&e>200); r.classList.toggle('hide',!(okT&&okA)); });
  $$('.pdd').forEach(r=>r.classList.toggle('hide',F.t.size+F.a.size>0));
  $$('.mo').forEach(s=>{ const n=s.querySelectorAll('.ev:not(.hide):not(.pdd)').length, sm=s.querySelector('h2 small'), vis=s.querySelectorAll('.ev:not(.hide)').length;
    s.classList.toggle('none',vis===0); sm.dataset.o=sm.dataset.o||sm.textContent; sm.textContent=(F.t.size+F.a.size)?sm.dataset.s.replace('#',n):sm.dataset.o;
    const a=$('#months a[href="#'+s.id+'"]'); if(a) a.classList.toggle('off',vis===0); });
  const k=F.t.size+F.a.size; $('#fn').textContent=k?'· '+k:''; act=null; pick(); }
$$('#fp button.c').forEach(b=>b.onclick=()=>{ const set=b.dataset.t?F.t:F.a, v=b.dataset.t||b.dataset.a; set.has(v)?set.delete(v):set.add(v); b.classList.toggle('on'); applyF(); });
$('#ft').onclick=()=>{ const on=$('#fp').classList.toggle('on'); document.body.classList.toggle('f-on',on); $('#ft span').textContent=on?'[–]':'[+]'; };
$$('.aggiungi').forEach(b=>b.addEventListener('click',()=>{
  const e=b.closest('.ev'),d=e.dataset.icsD,t=e.dataset.icsT;
  const f=new Date(Date.UTC(+d.slice(0,4),+d.slice(4,6)-1,+d.slice(6,8)+1)),fs=f.getUTCFullYear()+('0'+(f.getUTCMonth()+1)).slice(-2)+('0'+f.getUTCDate()).slice(-2);
  const x=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Public Domain Radar//EN','BEGIN:VEVENT','UID:'+e.dataset.id+'@publicdomainradar.com','DTSTAMP:'+d+'T000000Z','DTSTART;VALUE=DATE:'+d,'DTEND;VALUE=DATE:'+fs,'SUMMARY:'+t.replace(/[,;]/g,c=>'\\\\'+c),'END:VEVENT','END:VCALENDAR'].join('\\r\\n');
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([x],{type:'text/calendar'}));a.download=e.dataset.id+'.ics';document.body.appendChild(a);a.click();a.remove(); }));
$('#mbtn').addEventListener('click',()=>document.body.classList.add('menu-on')); $('#mx').addEventListener('click',()=>document.body.classList.remove('menu-on'));
let tk=false; function frame(){ tk=false; ink(); pick(); }
addEventListener('scroll',()=>{ if(!tk){tk=true;requestAnimationFrame(frame);} },{passive:true}); addEventListener('resize',frame); frame();
})();
</script>
"""


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
