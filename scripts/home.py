"""La home del sito (21/11/2026): il «frontespizio». Scrive index.html (italiano) ed en/index.html (inglese).

Mockup approvato da Marco il 21/11/2026 (prova 1, «frontespizio»): il titolo di un'opera che si libera il prossimo
1° gennaio, in grande come in un frontespizio; sotto «Tutti i diritti riservati» viene barrato e sostituito da
«Libero in Italia, Francia, Germania e Regno Unito / negli Stati Uniti dal 1° gennaio <anno>» (in Spagna gli autori morti prima del 1987 hanno 80 anni: niente «Europa»). Ogni 7 secondi si volta pagina.
Sotto, una parte di solo testo (per chi legge e per Google): i numeri del prossimo 1° gennaio e le porte del sito.
Il radar (lo strumento con i filtri) sta su /radar/ e /en/radar/: i vecchi indirizzi con # ci rimandano lì.

Le opere del frontespizio sono una scelta editoriale (OPERE_UE, OPERE_US) ma titoli, autori e «dove» vengono dai dati:
- Europa: l'autore deve essere nella lista del prossimo anno (data/<anno>.json), cioè morto 70 anni prima;
- Stati Uniti: l'opera deve essere nella lista USA (data/us-<anno>.json) con l'anno CONFERMATO dal registro
  (data/us-anni-verificati.json, stato «ok»). Se manca qualcosa, quella pagina non compare.
Se la scelta non vale per l'anno (cambia il 1° gennaio), si usano gli autori e le opere più letti della lista."""
import json, re, sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import regole as R  # noqa: E402  (regole per paese in un posto solo)

RADICE = Path(__file__).resolve().parent.parent
SITO = "https://publicdomainradar.com"

# scelta per il 1° gennaio 2027: (wikidata dell'autore, indice dell'opera nella sua scheda)
# 22/11/2026: tolta «L'opera da tre soldi» (coautrice Elisabeth Hauptmann, morta nel 1973: libera dal 2044, Kurt Weill Foundation)
# e non messo «Il cerchio di gesso del Caucaso» (Suhrkamp: «unter Mitarbeit von Ruth Berlau», morta nel 1974; da decidere con Marco)
OPERE_UE = [("Q38757", 1), ("Q207036", 0), ("Q38757", 5), ("Q123075", 0)]
OPERE_US = ["Q1218608", "Q1217475", "Q1070729"]
ORDINE = ["ue0", "ue1", "us0", "ue2", "ue3", "us1", "us2"]
def nota_disegni(pg, a, o):
    """Avvertenza sotto la riga «Libero…»: i disegni originali con diritti propri, dagli stessi dati delle schede e di Già
    pubblici (data/coautori_manuali.json, ruolo «illustratore», con la fonte). Prima era scritta a mano qui (23/11/2026)."""
    D = pg.anno_di(a.get("morte"))
    ill = [(n, m) for n, m in pg.vincoli_opera(a, o)[2].get("ill", []) if m and D and m > D]
    if not ill:
        return None
    n, m = max(ill, key=lambda x: x[1])
    fino = pg.R.anno_libero(m, "it") - 1
    return {"it": f"Solo il testo: i disegni originali di {n} restano protetti fino al {fino}.".replace("E. H. ", "E.\u00a0H.\u00a0"),
            "en": f"The text only: {n}'s original drawings stay protected until {fino}.".replace("E. H. ", "E.\u00a0H.\u00a0")}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _leggi(p, vuoto=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return vuoto


NOMI_P = {"it": {"it": "in Italia", "fr": "in Francia", "de": "in Germania", "uk": "nel Regno Unito", "es": "in Spagna"},
          "en": {"it": "Italy", "fr": "France", "de": "Germany", "uk": "the UK", "es": "Spain"}}


def elenco_paesi(paesi, lang):
    """«in Italia, Francia, Germania e Regno Unito» / «in Italy, France, Germany and the UK»."""
    if not paesi:
        return ""
    if lang == "en":
        n = [NOMI_P["en"][x] for x in paesi]
        return "in " + (", ".join(n[:-1]) + " and " + n[-1] if len(n) > 1 else n[0])
    n = [NOMI_P["it"][x] for x in paesi]
    if len(n) > 1:
        # «in Italia, Francia, Germania e nel Regno Unito»: preposizione solo sul primo, articolo dove serve
        corti = [x.split(" ", 1)[1] if x.startswith("in ") else x for x in n]
        testa = n[0] + "".join(", " + c for c in corti[1:-1])
        return testa + " e " + corti[-1]
    return n[0]


def pagine_frontespizio(anno):
    ue = R.lista_pubblica(_leggi(RADICE / "data" / f"{anno}.json", {}) or {})
    us = _leggi(RADICE / "data" / f"us-{anno}.json", {}) or {}
    ver = (_leggi(RADICE / "data" / "us-anni-verificati.json", {}) or {}).get(str(anno), {})
    pub = us.get("anno_pubblicazione")
    autori = {a["wikidata"]: a for a in ue.get("autori", [])}
    autori_es = {a["wikidata"] for a in R.lista_pubblica(_leggi(RADICE / "data" / f"es-{anno}.json", {}) or {}).get("autori", [])}
    opere_us = {o["qid"]: o for o in us.get("opere", [])}

    def us_ok(q):
        v = ver.get(q)
        return bool(v and v[0] == "ok" and v[1] == pub)
    import pagine as pg   # regola dei coautori, la stessa delle schede (pagine.opera_libera_ue)
    # solo opere davvero libere quel 1° gennaio, non solo autori liberi (22/11/2026: «L'opera da tre soldi» ha come
    # coautrice Elisabeth Hauptmann, morta nel 1973). Se l'opera scelta non è libera, si prende la prossima opera libera
    # dello stesso autore che non sia già nel frontespizio.
    scelte_ue = []
    for q, i in OPERE_UE:
        op = (autori.get(q) or {}).get("opere") or []
        for j in [i] + [j for j in range(len(op)) if j != i]:
            if j < len(op) and (q, j) not in scelte_ue and pg.opera_libera_ue(autori[q], op[j], anno):
                scelte_ue.append((q, j))
                break
    scelte_us = [q for q in OPERE_US if q in opere_us and us_ok(q)]
    if not scelte_ue:   # anno nuovo, scelta non aggiornata: i più letti con un'opera
        cand = sorted((a for a in autori.values() if a.get("letterario") and a.get("opere")), key=lambda a: -(a.get("visite_12m") or 0))
        scelte_ue = [(a["wikidata"], j) for a in cand for j, o in enumerate(a["opere"][:10]) if pg.opera_libera_ue(a, o, anno)][:4]
    if not scelte_us:
        cand = sorted((o for o in opere_us.values() if us_ok(o["qid"])), key=lambda o: -(o.get("visite_en") or 0))
        scelte_us = [o["qid"] for o in cand[:3]]
    pag = {}
    for k, (q, i) in enumerate(scelte_ue):
        a, o = autori[q], autori[q]["opere"][i]
        # La riga dice solo i paesi dove l'autore è davvero libero quel giorno, calcolati dalle regole (Marco, 21/11/2026: «dobbiamo essere precisi»):
        # paesi dal Trattato in poi: regole.py (paesi_liberi_insieme); Spagna solo se l'autore è nella lista spagnola di quell'anno
        # (80 anni per chi è morto prima del 1987). Francia: i «morti per la Francia» riguardano solo i morti 1939-1945, mai l'anno di questa pagina.
        paesi = [p for p in R.paesi_liberi_insieme(a.get("paesi"), int(str(a["morte"])[:4]), date.today().year) if p != "es"] \
            + (["es"] if q in autori_es else [])
        pag[f"ue{k}"] = {"a": a["nome"], "it": o["titolo"], "en": o.get("titolo_en") or o["titolo"], "dove": "ue", "paesi": paesi,
                         "nota": nota_disegni(pg, a, o)}
    for k, q in enumerate(scelte_us):
        o = opere_us[q]
        nomi = [x["nome"] for x in o.get("autori", [])][:2]
        # 23/11/2026: il codice Wikidata dell'opera va nella pagina, così la prova 8 la confronta con il registro delle opere;
        # la nota, se c'è, viene dal registro (la stessa della pagina dell'anno, del radar e di Già pubblici)
        pag[f"us{k}"] = {"a": " e ".join(nomi), "a_en": " and ".join(nomi), "it": o.get("titolo_it") or o["titolo"], "en": o["titolo"], "dove": "us",
                         "q": q, "nota": pg.NOTE_USA.get(q)}
    ordine = [k for k in ORDINE if k in pag] + [k for k in pag if k not in ORDINE]
    return [pag[k] for k in ordine]


def numeri(anno):
    ue = R.lista_pubblica(_leggi(RADICE / "data" / f"{anno}.json", {}) or {})
    es = R.lista_pubblica(_leggi(RADICE / "data" / f"es-{anno}.json", {}) or {})
    us = _leggi(RADICE / "data" / f"us-{anno}.json", {}) or {}
    ver = (_leggi(RADICE / "data" / "us-anni-verificati.json", {}) or {}).get(str(anno), {})
    n = lambda d: sum(1 for a in d.get("autori", []) if a.get("letterario") and a.get("morte"))   # come le pagine dell'anno
    opere = us.get("opere", [])
    return {"ue": n(ue), "es": n(es), "us": len(opere), "us_ok": sum(1 for o in opere if (ver.get(o["qid"]) or ["nd"])[0] == "ok"),
            "pub": us.get("anno_pubblicazione") or R.pubblicate_libere_usa_nel(anno), "aggiornato": ue.get("aggiornato") or ""}


MESI = {"it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
        "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}


def data_lunga(iso, lang):
    try:
        y, m, d = (int(x) for x in iso.split("-"))
    except ValueError:
        return iso
    return f"{d} {MESI[lang][m - 1]} {y}"


def migliaia(n, lang):
    return f"{n:,}".replace(",", "." if lang == "it" else ",")


CSS = r"""
/* il frontespizio (solo questa parte in Garamond); il resto della home usa lo stile del sito (stile_scheda + stile_anno) */
.fronte{--serif:'EB Garamond',Garamond,'Times New Roman',serif;--lento:cubic-bezier(.65,0,.35,1);--matita:#6E6C66;
  font-family:var(--serif);font-feature-settings:'kern','liga','onum';text-rendering:optimizeLegibility;
  display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:110px var(--pad) 64px;min-height:100svh}
.fronte .sc{font-variant-caps:all-small-caps;letter-spacing:.09em}
.fronte .autore{margin:0;font-size:clamp(17px,1.5vw,22px);color:var(--matita)}
.fronte .titolo{margin:.28em auto 0;font-family:var(--serif);font-style:italic;font-weight:400;font-size:clamp(64px,11.5vw,200px);line-height:.92;letter-spacing:-.015em;text-transform:none;text-wrap:balance;max-width:12ch}
.fronte .diritti{margin:clamp(28px,4.5vh,56px) auto 0;font-size:clamp(18px,1.6vw,24px);line-height:1.4;max-width:30ch;min-height:2.8em;text-wrap:balance}
#riga{display:inline}
#riga.vecchia{color:var(--matita);background:linear-gradient(var(--ink),var(--ink)) left 58%/0% 1.5px no-repeat;transition:background-size .8s var(--lento),opacity .4s}
#riga.vecchia.barra{background-size:100% 1.5px}
#riga.vecchia.via{opacity:0}
#riga.nuova{display:inline-block;clip-path:inset(0 100% 0 0);animation:scrivi 1.1s var(--lento) forwards}
@keyframes scrivi{to{clip-path:inset(0 0 0 0)}}
#riga em{font-style:italic}
/* avvertenza sotto la riga (es. disegni di Shepard): fuori dal flusso, così il colophon non si sposta tra una pagina e l'altra */
.foglio{position:relative}
.fronte .avv{position:absolute;left:0;right:0;top:100%;margin:12px auto 0;max-width:48ch;font-size:clamp(14px,1.05vw,16px);line-height:1.45;color:var(--matita);text-wrap:balance;opacity:0;transition:opacity .6s var(--lento)}
.fronte .avv.su{opacity:1}
.foglio{transition:opacity .7s var(--lento),transform .7s var(--lento)}
.foglio.via{opacity:0;transform:translateY(-10px)}
.foglio.arriva{opacity:0;transform:translateY(10px);transition:none}
.colophon{margin-top:clamp(48px,9vh,110px);display:flex;flex-direction:column;align-items:center;gap:22px}
.colophon p{margin:0;font-size:clamp(17px,1.35vw,20px);line-height:1.5;max-width:34ch;text-wrap:balance}
.colophon .giorni{color:var(--red)}
.colophon .folio{font-style:italic;font-size:15px;color:var(--matita)}
/* il pulsante è già quello del sito */
.vai{display:inline-flex;align-items:center;gap:14px;height:56px;padding:0 24px;background:var(--ink);color:var(--paper);text-decoration:none;font-family:var(--mono);font-size:13px;letter-spacing:.1em;text-transform:uppercase;transition:background .3s,color .3s}
.vai:hover{background:var(--red);color:var(--ink)}
.home-sotto .sec:first-child{padding-top:6vh}
.home-sotto .nums{margin:28px 0 0;border-top:0}
/* sotto un frontespizio centrato anche i numeri stanno al centro della loro colonna */
.home-sotto .nums a,.home-sotto .nums a+a{text-align:center;padding:26px 24px 30px}
.home-sotto .nums .c{margin:14px auto 0;max-width:30ch}
@media (max-width:760px){.home-sotto .nums a,.home-sotto .nums a+a{padding:22px 0 24px}}
.porte{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));margin-top:0}
/* come i numeri: ogni sezione al centro della sua cella, con i filetti del sito tra le celle */
.porta{display:flex;flex-direction:column;align-items:center;text-align:center;padding:34px 28px 38px;border-bottom:1px solid var(--hair);text-decoration:none;color:var(--ink)}
.porta:nth-child(odd){border-right:1px solid var(--hair)}
.porta .m{color:var(--redt)}
.porta h3{margin:12px 0 12px;font-family:var(--disp);font-weight:800;text-transform:uppercase;font-size:clamp(34px,3.3vw,52px);line-height:.95;padding-top:.08em}
.porta p{margin:0 auto;font-size:16px;line-height:1.55;max-width:40ch}
.porta .go{margin-top:20px;font-family:var(--mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;border-bottom:2px solid var(--red);padding-bottom:4px}
.porta:hover h3{color:var(--red)}
@media (max-width:760px){.porte{grid-template-columns:1fr}.porta{padding:28px 0 32px}.porta:nth-child(odd){border-right:0}.porta h3{font-size:40px}}
@media (max-width:760px){.fronte .titolo{min-height:1.84em;display:flex;align-items:flex-end;justify-content:center}.fronte .diritti{font-size:18px}}
@media (prefers-reduced-motion:reduce){.fronte *{animation-duration:1ms!important;transition-duration:1ms!important}}
"""

TESTI = {
    "it": dict(
        url=f"{SITO}/", altra='<a href="/en/" hreflang="en">EN</a>', radar="/radar/",
        titolo="Public Domain Radar · Chi diventa libero, e quando",
        descr="Ogni 1° gennaio scadono i diritti di centinaia di scrittori e di libri. Chi diventa libero nel {a} in Europa e negli Stati Uniti, paese per paese, con dati aperti e fonti di legge.",
        diritti="Tutti i diritti riservati.",
        libero={"ue": "Libero {p} <em>dal 1° gennaio {a}.</em>", "us": "Libero negli Stati Uniti <em>dal 1° gennaio {a}.</em>"},
        colophon='Ogni 1° gennaio, in Europa e negli Stati Uniti, scadono i diritti di centinaia di libri. Il prossimo è tra <span class="giorni" id="gg"></span> giorni.',
        cta="Scopri chi si libera nel {a}", folio="{k} di {n}", pagina_anno="/pubblico-dominio-{a}/",
        cnt=('<span id="cnt"><i class="lg">1° gennaio {a} · </i><i class="sm">1° gen {a} · </i>tra {g} giorni</span>'),
        nums=[("scrittori liberi in Italia, Francia, Germania e Regno Unito", "morti nel {m}", "/pubblico-dominio-{a}/#ix1", "ue"),
              ("scrittori liberi in Spagna", "morti nel {me}", "/pubblico-dominio-{a}/", "es"),
              ("libri liberi negli USA", "pubblicati nel {pub} · {usok} con l'anno confermato", "/pubblico-dominio-{a}/#ix2", "us")],
        sez=("Da dove partire", "Le sezioni del sito"), sez_n=("Il 1° gennaio {a}", "Chi diventa libero, e dove"),
        porte=[("/pubblico-dominio-{a}/", "Pubblico dominio {a}", "1° gennaio {a}", "Chi si libera il 1° gennaio, spiegato: i nomi più attesi, i libri americani, le regole paese per paese.", "Leggi"),
               ("/radar/", "Tutti gli autori", "L'elenco completo", "L'elenco completo dei {ue} scrittori del {a}, da filtrare per paese e genere e scaricare in Excel.", "Cerca"),
               ("/gia-pubblici/", "Già pubblici", "Archivio", "Cerca un titolo o un autore: è già libero in Italia, Francia, Germania, Spagna, Regno Unito, USA?", "Cerca"),
               ("/calendario/{a}/", "Calendario {a}", "Anniversari", "Gli anniversari letterari del {a} giorno per giorno, da aggiungere al tuo calendario.", "Apri")],
        fonti=("Fonti", "Wikidata (CC0), Wikipedia, Project Gutenberg, il registro del copyright americano e i cataloghi delle biblioteche nazionali. Liste aggiornate al {agg}."),
        # settimana del Public Domain Day (mockup approvato da Marco il 22/11/2026); la fase la decide scripts/regole.py (fase_sito)
        fasi=dict(cnt_conto="tra {g} giorni", cnt_vigilia="Domani", cnt_festa="Public Domain Day",
                  col_vigilia='A mezzanotte, in Europa e negli Stati Uniti, scadono i diritti di centinaia di libri. Mancano <span class="giorni" id="orologio"></span>.',
                  col_oggi='Da oggi, 1° gennaio {a}, sono liberi <span class="giorni">{ue}</span> scrittori in Italia, Francia, Germania e Regno Unito, <span class="giorni">{es}</span> in Spagna e <span class="giorni">{us}</span> libri negli Stati Uniti.',
                  col_dal='Dal 1° gennaio {a} sono liberi <span class="giorni">{ue}</span> scrittori in Italia, Francia, Germania e Regno Unito, <span class="giorni">{es}</span> in Spagna e <span class="giorni">{us}</span> libri negli Stati Uniti.',
                  cta_vigilia="Chi si libera a mezzanotte", cta_oggi="Scopri chi è libero da oggi", cta_dal="Scopri chi è libero",
                  sez_oggi=("Da oggi, 1° gennaio {a}", "Chi è diventato libero, e dove"), sez_dal=("Dal 1° gennaio {a}", "Chi è diventato libero, e dove"),
                  data_em="dal 1° gennaio {a}.", oggi_em="da oggi."),
    ),
    "en": dict(
        url=f"{SITO}/en/", altra='<a href="/" hreflang="it">IT</a>', radar="/en/radar/",
        titolo="Public Domain Radar · Who becomes free, and when",
        descr="Every 1 January the copyright of hundreds of writers and books expires. Who becomes free in {a} in Europe and the United States, country by country, with open data and legal sources.",
        diritti="All rights reserved.",
        libero={"ue": "Free {p} <em>from 1 January {a}.</em>", "us": "Free in the United States <em>from 1 January {a}.</em>"},
        colophon='Every 1 January, in Europe and the United States, the copyright of hundreds of books expires. The next one is in <span class="giorni" id="gg"></span> days.',
        cta="See who becomes free in {a}", folio="{k} of {n}", pagina_anno="/en/public-domain-{a}/",
        cnt=('<span id="cnt"><i class="lg">1 January {a} · </i><i class="sm">1 Jan {a} · </i>in {g} days</span>'),
        nums=[("writers free in Italy, France, Germany and the UK", "died in {m}", "/en/public-domain-{a}/#ix1", "ue"),
              ("writers free in Spain", "died in {me}", "/en/public-domain-{a}/", "es"),
              ("books free in the USA", "published in {pub} · {usok} with the year confirmed", "/en/public-domain-{a}/#ix2", "us")],
        sez=("Where to start", "The sections of the site"), sez_n=("1 January {a}", "Who becomes free, and where"),
        porte=[("/en/public-domain-{a}/", "Public domain {a}", "1 January {a}", "Who becomes free on 1 January, explained: the most awaited names, the American books, the rules country by country.", "Read"),
               ("/en/radar/", "All authors", "The complete list", "The complete list of the {ue} writers of {a}, to filter by country and genre and download in Excel.", "Search"),
               ("/en/already-public/", "Already public", "Archive", "Search a title or an author: is it already free in Italy, France, Germany, Spain, the UK, the USA?", "Search"),
               ("/en/calendar/{a}/", "Calendar {a}", "Anniversaries", "The literary anniversaries of {a}, day by day, to add to your calendar.", "Open")],
        fonti=("Sources", "Wikidata (CC0), Wikipedia, Project Gutenberg, the US copyright register and national library catalogues. Lists updated on {agg}."),
        fasi=dict(cnt_conto="in {g} days", cnt_vigilia="Tomorrow", cnt_festa="Public Domain Day",
                  col_vigilia='At midnight, in Europe and the United States, the copyright of hundreds of books expires. Time left: <span class="giorni" id="orologio"></span>.',
                  col_oggi='From today, 1 January {a}, <span class="giorni">{ue}</span> writers are free in Italy, France, Germany and the UK, <span class="giorni">{es}</span> in Spain, and <span class="giorni">{us}</span> books in the United States.',
                  col_dal='Since 1 January {a}, <span class="giorni">{ue}</span> writers are free in Italy, France, Germany and the UK, <span class="giorni">{es}</span> in Spain, and <span class="giorni">{us}</span> books in the United States.',
                  cta_vigilia="Who becomes free at midnight", cta_oggi="See who is free from today", cta_dal="See who is free",
                  sez_oggi=("From today, 1 January {a}", "Who has become free, and where"), sez_dal=("Since 1 January {a}", "Who has become free, and where"),
                  data_em="from 1 January {a}.", oggi_em="from today."),
    ),
}


def pagina(lang, anno, P):
    """P: le funzioni del sito (scripts/pagine.py): testa_scheda, piede_scheda, CSS_ANNO, marchio."""
    import datetime
    t = TESTI[lang]
    nu = numeri(anno)
    gg = max(0, (datetime.date(anno, 1, 1) - datetime.date.today()).days)
    fmt = dict(a=anno, a1=anno + 1, ue=migliaia(nu["ue"], lang), m=R.morti_liberi_nel(anno, "it"), me=R.morti_liberi_nel(anno, "es"), pub=nu["pub"], usok=migliaia(nu["us_ok"], lang),
               agg=data_lunga(nu["aggiornato"][:10], lang), g=migliaia(gg, lang))
    pag = [{"a": p.get("a_en", p["a"]) if lang == "en" else p["a"], "t": p[lang], "r": t["libero"][p["dove"]].format(a=anno, p=elenco_paesi(p.get("paesi", []), lang)),
            "n": p["nota"][lang] if p.get("nota") else "", **({"q": p["q"]} if p.get("q") else {})}
           for p in pagine_frontespizio(anno)]
    if not pag:
        raise RuntimeError("home: nessuna opera per il frontespizio")
    alterne = (f'<link rel="alternate" hreflang="it" href="{SITO}/">\n<link rel="alternate" hreflang="en" href="{SITO}/en/">\n'
               f'<link rel="alternate" hreflang="x-default" href="{SITO}/">\n')
    jsonld = ('<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "WebSite", "name": "Public Domain Radar",
              "url": t["url"], "inLanguage": lang, "description": t["descr"].format(a=anno)}, ensure_ascii=False) + "</script>")
    rimando = (f'<script>/* i vecchi indirizzi della home con # (filtri, schede) sono del radar, che ora sta su {t["radar"]} */\n'
               f'if(location.hash.length>1){{location.replace("{t["radar"]}"+location.hash)}}'
               + ('' if lang == 'en' else 'else if(new URLSearchParams(location.search).get("lang")==="en"){location.replace("/en/")}') + '</script>\n')
    testa = P["testa_scheda"](lang, esc(t["titolo"]), esc(t["descr"].format(a=anno)), t["url"], alterne, jsonld, t["altra"],
                              "@@CNT@@", og_tipo="website", css_extra=P["CSS_ANNO"] + CSS, main_cls="pdd", body_cls="pdd-b")
    testa = testa.replace("@@CNT@@", t["cnt"].format(**fmt) if gg else f'<span id="cnt" style="color:var(--redt)">{t["fasi"]["cnt_festa"]}</span>').replace("</head>", '<script src="/assets/regole.js"></script>\n</head>', 1).replace("@@MARCHIO_S@@", P["marchio"]).replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + rimando, 1)
    numeri_html = "".join(f'<a href="{h.format(**fmt)}"><span class="n">{migliaia(nu[k], lang)}</span><span class="c">{esc(c)}</span><span class="m">{esc(m.format(**fmt))}</span></a>'
                          for c, m, h, k in t["nums"] if nu[k])
    porte = "".join(f'<a class="porta" href="{h.format(**fmt)}"><span class="m">{esc(y.format(**fmt))}</span><h3>{esc(x.format(**fmt))}</h3>'
                    f'<p>{esc(d.format(**fmt))}</p><span class="go">{esc(v)} →</span></a>' for h, x, y, d, v in t["porte"])
    primo = pag[0]
    corpo = f"""<section class="fronte" id="pagina" aria-label="{"Frontespizio" if lang == "it" else "Title page"}">
  <div class="foglio" id="foglio" aria-live="polite">
    <p class="autore sc" id="autore">{esc(primo["a"])}</p>
    <h1 class="titolo" id="titolo">{esc(primo["t"])}</h1>
    <p class="diritti"><span id="riga" class="vecchia">{esc(t["diritti"])}</span></p>
    <p class="avv" id="avv"></p>
  </div>
  <div class="colophon">
    <p id="colo">{t["colophon"]}</p>
    <a class="vai" href="{t["pagina_anno"].format(a=anno)}"><span id="cta">{esc(t["cta"].format(a=anno))}</span> <b>→</b></a>
    <span class="folio" id="folio"></span>
  </div>
</section>
<div class="home-sotto">
<section class="sec"><div class="sh m"><h2 id="sezn">{esc(t["sez_n"][0].format(**fmt))}</h2><span id="sezn2">{esc(t["sez_n"][1])}</span></div>
<div class="nums">{numeri_html}</div></section>
<section class="sec"><div class="sh m"><h2>{esc(t["sez"][0])}</h2><span>{esc(t["sez"][1])}</span></div>
<div class="porte">{porte}</div></section>
</div>
<script>
const P={json.dumps(pag, ensure_ascii=False)}, DIRITTI={json.dumps(t["diritti"], ensure_ascii=False)}, FOLIO={json.dumps(t["folio"], ensure_ascii=False)};
const el=s=>document.getElementById(s);
const ANNO={anno}, F={json.dumps({k: (v if isinstance(v, str) else list(v)) for k, v in t["fasi"].items()}, ensure_ascii=False)};
const NUM={json.dumps({"a": str(anno), "ue": migliaia(nu["ue"], lang), "es": migliaia(nu["es"], lang), "us": migliaia(nu["us"], lang)})};
const fmtF=(x)=>Object.keys(NUM).reduce((s,k)=>s.split("{{"+k+"}}").join(NUM[k]),x);
/* fase della settimana del Public Domain Day, calcolata nel browser con la regola unica (scripts/regole.py, fase_sito):
   a mezzanotte la pagina cambia da sola, senza aspettare un giro. Se la pagina è dell'anno già liberato
   (il giro del 7 gennaio non è ancora passato), resta in festa con «dal 1° gennaio». */
function modo(ora){{const fs=window.REGOLE_PAESI?REGOLE_PAESI.faseSito(ora):["conto",ANNO];
  if(ora>=new Date(ANNO,0,1))return ora.getFullYear()===ANNO&&ora.getMonth()===0&&ora.getDate()===1?"oggi":"dal";
  return fs[0]==="vigilia"&&fs[1]===ANNO?"vigilia":"conto";}}
const cnt=document.getElementById("cnt");
function applica(M){{
  if(M==="conto"){{const g=Math.max(0,Math.ceil((new Date(ANNO,0,1)-new Date())/864e5));el("gg").textContent=g;
    if(cnt)cnt.lastChild.textContent=F.cnt_conto.split("{{g}}").join(g.toLocaleString(document.documentElement.lang||"it"));return;}}   // prima restava il numero del giorno in cui era stata fatta la pagina
  if(cnt){{cnt.textContent=M==="vigilia"?F.cnt_vigilia:F.cnt_festa;cnt.style.color=M==="vigilia"?"":"var(--redt)";}}
  el("colo").innerHTML=fmtF(M==="vigilia"?F.col_vigilia:M==="oggi"?F.col_oggi:F.col_dal);
  el("cta").textContent=M==="vigilia"?F.cta_vigilia:M==="oggi"?F.cta_oggi:F.cta_dal;
  if(M!=="vigilia"){{const z=M==="oggi"?F.sez_oggi:F.sez_dal;el("sezn").textContent=fmtF(z[0]);el("sezn2").textContent=z[1];
    if(M==="oggi")P.forEach(p=>{{p.r=p.r.split(fmtF(F.data_em)).join(F.oggi_em)}});return;}}
  const o=el("orologio"),mezz=new Date(ANNO,0,1);
  const tic=()=>{{const s=Math.max(0,Math.floor((mezz-new Date())/1000));
    if(s===0){{clearInterval(t);applica("oggi");return}}   // mezzanotte: la pagina passa da sola alla festa
    o.textContent=Math.floor(s/3600)+":"+String(Math.floor(s%3600/60)).padStart(2,"0")+":"+String(s%60).padStart(2,"0");}};
  const t=setInterval(tic,1000);tic();
}}
applica(modo(new Date()));
const lenta=matchMedia("(prefers-reduced-motion: reduce)").matches;
let i=0;
function mostra(k){{const p=P[k];el("autore").textContent=p.a;el("titolo").textContent=p.t;el("folio").textContent=FOLIO.replace("{{k}}",k+1).replace("{{n}}",P.length);
  const r=el("riga");r.className="vecchia";r.textContent=DIRITTI;const v=el("avv");v.className="avv";v.textContent=p.n||"";}}
function libera(k){{const r=el("riga");r.classList.add("barra");setTimeout(()=>r.classList.add("via"),900);
  setTimeout(()=>{{r.className="nuova";r.innerHTML=P[k].r;}},1350);setTimeout(()=>el("avv").classList.add("su"),2400);}}
function giro(){{const f=el("foglio");mostra(i);f.classList.add("arriva");requestAnimationFrame(()=>requestAnimationFrame(()=>f.classList.remove("arriva")));
  setTimeout(()=>libera(i),1800);
  setTimeout(()=>{{f.classList.add("via");setTimeout(()=>{{f.classList.remove("via");i=(i+1)%P.length;giro();}},700);}},7600);}}
if(lenta){{mostra(0);const r=el("riga");r.className="nuova";r.innerHTML=P[0].r;el("avv").classList.add("su");}}else giro();
</script>
"""
    fonti = (t["fonti"][0], esc(t["fonti"][1].format(**fmt)))
    return testa + corpo + P["piede_scheda"](lang, fonti)


def crea_home(P=None, anno=None):
    """P: dizionario con testa_scheda, piede_scheda, CSS_ANNO, marchio (da scripts/pagine.py). Senza, si importa pagine."""
    import datetime, sys
    if P is None:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import pagine as pg
        from marchio import marchio_html
        P = {"testa_scheda": pg.testa_scheda, "piede_scheda": pg.piede_scheda, "CSS_ANNO": pg.CSS_ANNO,
             "marchio": marchio_html(56).replace('<span class="pdr" style="--w:56px">', "").rsplit("</span>", 1)[0]}
    anno = anno or R.fase_sito(datetime.date.today())[1]   # anno in vetrina: scripts/regole.py (fase_sito)
    (RADICE / "index.html").write_text(pagina("it", anno, P), encoding="utf-8")
    (RADICE / "en").mkdir(exist_ok=True)
    (RADICE / "en" / "index.html").write_text(pagina("en", anno, P), encoding="utf-8")
    print("home: index.html ed en/index.html (frontespizio)")


if __name__ == "__main__":
    crea_home()
