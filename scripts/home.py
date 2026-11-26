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
    return {"fr": f"Le texte seulement : les dessins originaux de {n} restent protégés jusqu'en {fino}.".replace("E. H. ", "E.\u00a0H.\u00a0"),
            "es": f"Solo el texto: los dibujos originales de {n} siguen protegidos hasta {fino}.".replace("E. H. ", "E.\u00a0H.\u00a0"),
            "de": f"Nur der Text: Die Originalzeichnungen von {n} bleiben bis {fino} geschützt.".replace("E. H. ", "E.\u00a0H.\u00a0"),
            "it": f"Solo il testo: i disegni originali di {n} restano protetti fino al {fino}.".replace("E. H. ", "E.\u00a0H.\u00a0"),
            "en": f"The text only: {n}'s original drawings stay protected until {fino}.".replace("E. H. ", "E.\u00a0H.\u00a0")}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _leggi(p, vuoto=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return vuoto


NOMI_P = {"it": {"it": "in Italia", "fr": "in Francia", "de": "in Germania", "uk": "nel Regno Unito", "es": "in Spagna"},
          "en": {"it": "Italy", "fr": "France", "de": "Germany", "uk": "the UK", "es": "Spain"},
          "de": {"it": "Italien", "fr": "Frankreich", "de": "Deutschland", "uk": "im Vereinigten Königreich", "es": "Spanien"}}


def elenco_paesi(paesi, lang):
    """«in Italia, Francia, Germania e Regno Unito» / «in Italy, France, Germany and the UK»."""
    if not paesi:
        return ""
    import lingue as L
    if lang in L.PAESI_IN:   # tedesco, francese, spagnolo: una regola sola (scripts/lingue.py)
        return L.elenco_paesi(lang, paesi)
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
    # data/fuori_classifica.json: autori tolti dalle vetrine per decisione di Marco (pagine.FUORI_CLASSIFICA, pagine.opera_in_vetrina)
    scelte_ue = [(q, j) for q, j in scelte_ue if q not in pg.FUORI_CLASSIFICA]
    st_us = pg.stati_usa_anno(anno) if opere_us else {}   # in vetrina solo «Verificato» (Marco, 23 e 25/11/2026)
    in_v = lambda q: pg.opera_in_vetrina(opere_us[q]) and st_us.get(q) == "verificata"   # solo «Verificato» (Marco, 25/11/2026)
    scelte_us = [q for q in OPERE_US if q in opere_us and us_ok(q) and in_v(q)]
    if not scelte_ue:   # anno nuovo, scelta non aggiornata: i più letti con un'opera
        cand = sorted((a for a in autori.values() if a.get("letterario") and a.get("opere") and a["wikidata"] not in pg.FUORI_CLASSIFICA), key=lambda a: -(a.get("visite_12m") or 0))
        scelte_ue = [(a["wikidata"], j) for a in cand for j, o in enumerate(a["opere"][:10]) if pg.opera_libera_ue(a, o, anno)][:4]
    if not scelte_us:
        cand = sorted((o for o in opere_us.values() if us_ok(o["qid"]) and in_v(o["qid"])), key=lambda o: -(o.get("visite_en") or 0))
        scelte_us = [o["qid"] for o in cand[:3]]
    pag = {}
    extra = (_leggi(RADICE / "data" / "lingue_extra.json", {}) or {}).get("autori", {})
    for k, (q, i) in enumerate(scelte_ue):
        a, o = autori[q], autori[q]["opere"][i]
        # La riga dice solo i paesi dove l'autore è davvero libero quel giorno, calcolati dalle regole (Marco, 21/11/2026: «dobbiamo essere precisi»):
        # paesi dal Trattato in poi: regole.py (paesi_liberi_insieme); Spagna solo se l'autore è nella lista spagnola di quell'anno
        # (80 anni per chi è morto prima del 1987). Francia: i «morti per la Francia» riguardano solo i morti 1939-1945, mai l'anno di questa pagina.
        paesi = [p for p in R.paesi_liberi_insieme(a.get("paesi"), int(str(a["morte"])[:4]), date.today().year) if p != "es"] \
            + (["es"] if q in autori_es else [])
        tl = (((extra.get(q) or {}).get("opere") or {}).get(o["titolo"]) or {})   # titoli in tedesco, francese, spagnolo (data/lingue_extra.json)
        pag[f"ue{k}"] = {"a": a["nome"], "it": o["titolo"], "en": o.get("titolo_en") or o["titolo"], "dove": "ue", "paesi": paesi, **{l: v for l, v in tl.items() if v},
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


def _stati_us(anno):
    import pagine as pg
    return pg.stati_usa_anno(anno)


def numeri(anno):
    ue = R.lista_pubblica(_leggi(RADICE / "data" / f"{anno}.json", {}) or {})
    es = R.lista_pubblica(_leggi(RADICE / "data" / f"es-{anno}.json", {}) or {})
    us = _leggi(RADICE / "data" / f"us-{anno}.json", {}) or {}
    ver = (_leggi(RADICE / "data" / "us-anni-verificati.json", {}) or {}).get(str(anno), {})
    n = lambda d: sum(1 for a in d.get("autori", []) if a.get("letterario") and a.get("morte"))   # come le pagine dell'anno
    opere = us.get("opere", [])
    return {"ue": n(ue), "es": n(es), "us": len(opere), "us_ok": sum(1 for o in opere if _stati_us(anno).get(o["qid"]) == "verificata"),   # stesso numero delle pagine 2027 e Stati Uniti (25/11/2026)
            "pub": us.get("anno_pubblicazione") or R.pubblicate_libere_usa_nel(anno), "aggiornato": ue.get("aggiornato") or ""}


MESI = {"it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
        "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}


def data_lunga(iso, lang):
    try:
        y, m, d = (int(x) for x in iso.split("-"))
    except ValueError:
        return iso
    import lingue as L
    if lang in L.MESI:
        return L.data(lang, d, m, y)
    return f"{d} {MESI[lang][m - 1]} {y}"


def migliaia(n, lang):
    return f"{n:,}".replace(",", "." if lang in ("it", "de", "es") else "\u202f" if lang == "fr" else ",")


CSS = r"""
/* 25/11/2026: il vero titolo della pagina per Google e per chi usa un lettore di schermo; il titolo dell'opera che cambia non è più un h1 */
.vh{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}
/* il frontespizio (solo questa parte in Garamond); il resto della home usa lo stile del sito (stile_scheda + stile_anno) */
.fronte{--serif:'EB Garamond',Garamond,'Times New Roman',serif;--lento:cubic-bezier(.65,0,.35,1);--matita:#6E6C66;
  font-family:var(--serif);font-feature-settings:'kern','liga','onum';text-rendering:optimizeLegibility;
  display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:110px var(--pad) 64px;min-height:100svh}
.fronte .sc{font-variant-caps:all-small-caps;letter-spacing:.09em}
.fronte .autore{margin:0;font-size:clamp(17px,1.5vw,22px);color:var(--matita)}
.fronte .titolo{margin:.28em auto 0;font-family:var(--serif);font-style:italic;font-weight:400;font-size:clamp(64px,11.5vw,200px);line-height:1.04;letter-spacing:-.015em;text-transform:none;text-wrap:balance;max-width:12ch}
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
@media (max-width:760px){.fronte .titolo{min-height:2.08em;display:flex;align-items:flex-end;justify-content:center}.fronte .diritti{font-size:18px}}
@media (prefers-reduced-motion:reduce){.fronte *{animation-duration:1ms!important;transition-duration:1ms!important}}
"""

TESTI = {
    "it": dict(
        url=f"{SITO}/it/", altra='<a href="/" hreflang="en">EN</a>', radar="/radar/",
        titolo="Public Domain Radar · Chi diventa libero, e quando",
        descr="Ogni 1° gennaio scadono i diritti di centinaia di scrittori e di libri. Chi diventa libero nel {a} in Europa e negli Stati Uniti, paese per paese, con dati aperti e fonti di legge.",
        diritti="Tutti i diritti riservati.",
        libero={"ue": "Libero {p} <em>dal 1° gennaio {a}.</em>", "us": "Libero negli Stati Uniti <em>dal 1° gennaio {a}.</em>"},
        colophon='Ogni 1° gennaio, in Europa e negli Stati Uniti, scadono i diritti di centinaia di libri. Il prossimo è tra <span class="giorni" id="gg"></span> giorni.',
        cta="Scopri chi si libera nel {a}", folio="{k} di {n}", pagina_anno="/pubblico-dominio-{a}/",
        cnt=('<span id="cnt"><i class="lg">1° gennaio {a} · </i><i class="sm">1° gen {a} · </i>tra {g} giorni</span>'),
        nums=[("scrittori liberi in Italia, Francia, Germania e Regno Unito", "morti nel {m}", "/pubblico-dominio-{a}/#ix1", "ue"),
              ("scrittori liberi in Spagna", "morti nel {me}", "/pubblico-dominio-{a}/", "es"),
              ("libri liberi negli USA", "pubblicati nel {pub} · {usok} verificati", "/pubblico-dominio-{a}/#ix2", "us")],
        sez=("Da dove partire", "Le sezioni del sito"), sez_n=("Il 1° gennaio {a}", "Chi diventa libero, e dove"),
        porte=[("/pubblico-dominio-{a}/", "Pubblico dominio {a}", "1° gennaio {a}", "Chi si libera il 1° gennaio, spiegato: i nomi più attesi, i libri americani, le regole paese per paese.", "Leggi"),
               ("/pubblico-dominio/", "Per paese", "Sei paesi, sei regole", "Italia, Francia, Germania, Spagna, Regno Unito e Stati Uniti: la regola di legge di ogni paese e chi entra in pubblico dominio.", "Scegli"),
               ("/gia-pubblici/", "Già pubblici", "Archivio", "Cerca un titolo o un autore: è già libero in Italia, Francia, Germania, Spagna, Regno Unito, USA?", "Cerca"),
               ("/calendario/{a}/", "Calendario {a}", "Anniversari", "Gli anniversari letterari del {a} giorno per giorno, da aggiungere al tuo calendario.", "Apri"),
               ("/come-funziona/", "Come funziona", "Il metodo", "Da dove vengono i dati, come si calcolano le date e quanto sono sicure.", "Leggi"),
               ("/shop/", "Shop", "Poster", "Poster tipografici con le prime righe dei libri in pubblico dominio, stampati su richiesta.", "Guarda")],
        fonti=("Fonti", "Wikidata (CC0), Wikipedia, Project Gutenberg, il registro del copyright americano, Duke University (CC BY 4.0), Open Library e i cataloghi delle biblioteche nazionali. Liste aggiornate al {agg}."),
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
        url=f"{SITO}/", altra='<a href="/" hreflang="it">IT</a>', radar="/en/radar/",
        titolo="Public Domain Radar · Who becomes free, and when",
        descr="Every 1 January the copyright of hundreds of writers and books expires. Who becomes free in {a} in Europe and the United States, country by country, with open data and legal sources.",
        diritti="All rights reserved.",
        libero={"ue": "Free {p} <em>from 1 January {a}.</em>", "us": "Free in the United States <em>from 1 January {a}.</em>"},
        colophon='Every 1 January, in Europe and the United States, the copyright of hundreds of books expires. The next one is in <span class="giorni" id="gg"></span> days.',
        cta="See who becomes free in {a}", folio="{k} of {n}", pagina_anno="/en/public-domain-{a}/",
        cnt=('<span id="cnt"><i class="lg">1 January {a} · </i><i class="sm">1 Jan {a} · </i>in {g} days</span>'),
        nums=[("writers free in Italy, France, Germany and the UK", "died in {m}", "/en/public-domain-{a}/#ix1", "ue"),
              ("writers free in Spain", "died in {me}", "/en/public-domain-{a}/", "es"),
              ("books free in the USA", "published in {pub} · {usok} verified", "/en/public-domain-{a}/#ix2", "us")],
        sez=("Where to start", "The sections of the site"), sez_n=("1 January {a}", "Who becomes free, and where"),
        porte=[("/en/public-domain-{a}/", "Public domain {a}", "1 January {a}", "Who becomes free on 1 January, explained: the most awaited names, the American books, the rules country by country.", "Read"),
               ("/en/public-domain/", "By country", "Six countries, six rules", "Italy, France, Germany, Spain, the UK and the United States: each country's legal rule and who enters the public domain.", "Choose"),
               ("/en/already-public/", "Already public", "Archive", "Search a title or an author: is it already free in Italy, France, Germany, Spain, the UK, the USA?", "Search"),
               ("/en/calendar/{a}/", "Calendar {a}", "Anniversaries", "The literary anniversaries of {a}, day by day, to add to your calendar.", "Open"),
               ("/en/how-it-works/", "How it works", "The method", "Where the data comes from, how the dates are worked out and how certain they are.", "Read"),
               ("/en/shop/", "Shop", "Posters", "Typographic posters with the opening lines of public domain books, printed on demand.", "Look")],
        fonti=("Sources", "Wikidata (CC0), Wikipedia, Project Gutenberg, the US copyright register, Duke University (CC BY 4.0), Open Library and national library catalogues. Lists updated on {agg}."),
        fasi=dict(cnt_conto="in {g} days", cnt_vigilia="Tomorrow", cnt_festa="Public Domain Day",
                  col_vigilia='At midnight, in Europe and the United States, the copyright of hundreds of books expires. Time left: <span class="giorni" id="orologio"></span>.',
                  col_oggi='From today, 1 January {a}, <span class="giorni">{ue}</span> writers are free in Italy, France, Germany and the UK, <span class="giorni">{es}</span> in Spain, and <span class="giorni">{us}</span> books in the United States.',
                  col_dal='Since 1 January {a}, <span class="giorni">{ue}</span> writers are free in Italy, France, Germany and the UK, <span class="giorni">{es}</span> in Spain, and <span class="giorni">{us}</span> books in the United States.',
                  cta_vigilia="Who becomes free at midnight", cta_oggi="See who is free from today", cta_dal="See who is free",
                  sez_oggi=("From today, 1 January {a}", "Who has become free, and where"), sez_dal=("Since 1 January {a}", "Who has become free, and where"),
                  data_em="from 1 January {a}.", oggi_em="from today."),
    ),
    "de": dict(
        url=f"{SITO}/de/", altra="", radar="/de/radar/",
        titolo="Public Domain Radar · Wer gemeinfrei wird, und wann",
        descr="Jedes Jahr am 1. Januar erlischt das Urheberrecht Hunderter Schriftsteller und Bücher. Wer {a} in Europa und den USA gemeinfrei wird, Land für Land, mit offenen Daten und Gesetzesquellen.",
        diritti="Alle Rechte vorbehalten.",
        libero={"ue": "Gemeinfrei {p} <em>ab 1. Januar {a}.</em>", "us": "Gemeinfrei in den USA <em>ab 1. Januar {a}.</em>"},
        colophon='Jedes Jahr am 1. Januar erlischt in Europa und den USA das Urheberrecht Hunderter Bücher. Der nächste ist in <span class="giorni" id="gg"></span> Tagen.',
        cta="Wer {a} gemeinfrei wird", folio="{k} von {n}", pagina_anno="/de/gemeinfrei-{a}/",
        cnt=('<span id="cnt"><i class="lg">1. Januar {a} · </i><i class="sm">1. Jan. {a} · </i>in {g} Tagen</span>'),
        nums=[("Schriftsteller gemeinfrei in Italien, Frankreich, Deutschland und im Vereinigten Königreich", "gestorben {m}", "/de/gemeinfrei-{a}/#ix1", "ue"),
              ("Schriftsteller gemeinfrei in Spanien", "gestorben {me}", "/de/gemeinfrei-{a}/", "es"),
              ("Bücher gemeinfrei in den USA", "erschienen {pub} · {usok} geprüft", "/de/gemeinfrei-{a}/#ix2", "us")],
        sez=("Wo anfangen", "Die Bereiche der Website"), sez_n=("1. Januar {a}", "Wer gemeinfrei wird, und wo"),
        porte=[("/de/gemeinfrei-{a}/", "Gemeinfrei {a}", "1. Januar {a}", "Wer am 1. Januar gemeinfrei wird, erklärt: die meisterwarteten Namen, die amerikanischen Bücher, die Regeln Land für Land.", "Lesen"),
               ("/de/gemeinfrei/", "Nach Land", "Sechs Länder, sechs Regeln", "Italien, Frankreich, Deutschland, Spanien, das Vereinigte Königreich und die USA: die gesetzliche Regel jedes Landes und wer gemeinfrei wird.", "Wählen"),
               ("/en/already-public/", "Schon gemeinfrei", "Archiv", "Einen Titel oder Autor suchen: Ist er in Italien, Frankreich, Deutschland, Spanien, im Vereinigten Königreich oder in den USA schon frei?", "Suchen"),
               ("/en/calendar/{a}/", "Kalender {a}", "Jahrestage", "Die literarischen Jahrestage {a}, Tag für Tag, für Ihren Kalender.", "Öffnen"),
               ("/en/how-it-works/", "So funktioniert’s", "Die Methode", "Woher die Daten kommen, wie die Daten berechnet werden und wie sicher sie sind.", "Lesen"),
               ("/en/shop/", "Shop", "Poster", "Typografische Poster mit den ersten Zeilen gemeinfreier Bücher, auf Bestellung gedruckt.", "Ansehen")],
        fonti=("Quellen", "Wikidata (CC0), Wikipedia, Project Gutenberg, das US-Urheberrechtsregister, Duke University (CC BY 4.0), Open Library und die Kataloge der Nationalbibliotheken. Listen aktualisiert am {agg}."),
        fasi=dict(cnt_conto="in {g} Tagen", cnt_vigilia="Morgen", cnt_festa="Public Domain Day",
                  col_vigilia='Um Mitternacht erlischt in Europa und den USA das Urheberrecht Hunderter Bücher. Noch: <span class="giorni" id="orologio"></span>.',
                  col_oggi='Ab heute, 1. Januar {a}, sind <span class="giorni">{ue}</span> Schriftsteller in Italien, Frankreich, Deutschland und im Vereinigten Königreich gemeinfrei, <span class="giorni">{es}</span> in Spanien und <span class="giorni">{us}</span> Bücher in den USA.',
                  col_dal='Seit 1. Januar {a} sind <span class="giorni">{ue}</span> Schriftsteller in Italien, Frankreich, Deutschland und im Vereinigten Königreich gemeinfrei, <span class="giorni">{es}</span> in Spanien und <span class="giorni">{us}</span> Bücher in den USA.',
                  cta_vigilia="Wer um Mitternacht gemeinfrei wird", cta_oggi="Wer ab heute gemeinfrei ist", cta_dal="Wer gemeinfrei ist",
                  sez_oggi=("Ab heute, 1. Januar {a}", "Wer gemeinfrei geworden ist, und wo"), sez_dal=("Seit 1. Januar {a}", "Wer gemeinfrei geworden ist, und wo"),
                  data_em="ab 1. Januar {a}.", oggi_em="ab heute."),
    ),
    "fr": dict(
        url=f"{SITO}/fr/", altra="", radar="/fr/radar/",
        titolo="Public Domain Radar · Qui entre dans le domaine public, et quand",
        descr="Chaque 1er janvier, les droits de centaines d'écrivains et de livres expirent. Qui entre dans le domaine public en {a} en Europe et aux États-Unis, pays par pays, avec des données ouvertes et les textes de loi.",
        diritti="Tous droits réservés.",
        libero={"ue": "Libre {p} <em>à partir du 1er janvier {a}.</em>", "us": "Libre aux États-Unis <em>à partir du 1er janvier {a}.</em>"},
        colophon='Chaque 1er janvier, en Europe et aux États-Unis, les droits de centaines de livres expirent. Le prochain est dans <span class="giorni" id="gg"></span> jours.',
        cta="Qui entre dans le domaine public en {a}", folio="{k} sur {n}", pagina_anno="/fr/domaine-public-{a}/",
        cnt=('<span id="cnt"><i class="lg">1er janvier {a} · </i><i class="sm">1er janv. {a} · </i>dans {g} jours</span>'),
        nums=[("écrivains libres en Italie, en France, en Allemagne et au Royaume-Uni", "morts en {m}", "/fr/domaine-public-{a}/#ix1", "ue"),
              ("écrivains libres en Espagne", "morts en {me}", "/fr/domaine-public-{a}/", "es"),
              ("livres libres aux États-Unis", "publiés en {pub} · {usok} vérifiés", "/fr/domaine-public-{a}/#ix2", "us")],
        sez=("Par où commencer", "Les rubriques du site"), sez_n=("1er janvier {a}", "Qui devient libre, et où"),
        porte=[("/fr/domaine-public-{a}/", "Domaine public {a}", "1er janvier {a}", "Qui devient libre le 1er janvier, expliqué : les noms les plus attendus, les livres américains, les règles pays par pays.", "Lire"),
               ("/fr/domaine-public/", "Par pays", "Six pays, six règles", "Italie, France, Allemagne, Espagne, Royaume-Uni et États-Unis : la règle légale de chaque pays et qui entre dans le domaine public.", "Choisir"),
               ("/fr/deja-libres/", "Déjà libres", "Archives", "Cherchez un titre ou un auteur : est-il déjà libre en Italie, en France, en Allemagne, en Espagne, au Royaume-Uni, aux États-Unis ?", "Chercher"),
               ("/fr/calendrier/{a}/", "Calendrier {a}", "Anniversaires", "Les anniversaires littéraires de {a}, jour par jour, à ajouter à votre agenda.", "Ouvrir"),
               ("/fr/comment-ca-marche/", "Comment ça marche", "La méthode", "D'où viennent les données, comment les dates sont calculées et à quel point elles sont sûres.", "Lire"),
               ("/fr/boutique/", "Boutique", "Affiches", "Affiches typographiques avec les premières lignes de livres du domaine public, imprimées à la demande.", "Voir")],
        fonti=("Sources", "Wikidata (CC0), Wikipédia, Project Gutenberg, le registre du copyright américain, Duke University (CC BY 4.0), Open Library et les catalogues des bibliothèques nationales. Listes mises à jour le {agg}."),
        fasi=dict(cnt_conto="dans {g} jours", cnt_vigilia="Demain", cnt_festa="Public Domain Day",
                  col_vigilia='À minuit, en Europe et aux États-Unis, les droits de centaines de livres expirent. Il reste <span class="giorni" id="orologio"></span>.',
                  col_oggi='Depuis aujourd\'hui, 1er janvier {a}, <span class="giorni">{ue}</span> écrivains sont libres en Italie, en France, en Allemagne et au Royaume-Uni, <span class="giorni">{es}</span> en Espagne et <span class="giorni">{us}</span> livres aux États-Unis.',
                  col_dal='Depuis le 1er janvier {a}, <span class="giorni">{ue}</span> écrivains sont libres en Italie, en France, en Allemagne et au Royaume-Uni, <span class="giorni">{es}</span> en Espagne et <span class="giorni">{us}</span> livres aux États-Unis.',
                  cta_vigilia="Qui devient libre à minuit", cta_oggi="Qui est libre depuis aujourd'hui", cta_dal="Qui est libre",
                  sez_oggi=("Depuis aujourd'hui, 1er janvier {a}", "Qui est devenu libre, et où"), sez_dal=("Depuis le 1er janvier {a}", "Qui est devenu libre, et où"),
                  data_em="à partir du 1er janvier {a}.", oggi_em="depuis aujourd'hui."),
    ),
    "es": dict(
        url=f"{SITO}/es/", altra="", radar="/es/radar/",
        titolo="Public Domain Radar · Quién pasa al dominio público, y cuándo",
        descr="Cada 1 de enero expiran los derechos de cientos de escritores y libros. Quién pasa al dominio público en {a} en Europa y Estados Unidos, país por país, con datos abiertos y fuentes legales.",
        diritti="Todos los derechos reservados.",
        libero={"ue": "Libre {p} <em>desde el 1 de enero de {a}.</em>", "us": "Libre en Estados Unidos <em>desde el 1 de enero de {a}.</em>"},
        colophon='Cada 1 de enero, en Europa y Estados Unidos, expiran los derechos de cientos de libros. El próximo es dentro de <span class="giorni" id="gg"></span> días.',
        cta="Quién pasa al dominio público en {a}", folio="{k} de {n}", pagina_anno="/es/dominio-publico-{a}/",
        cnt=('<span id="cnt"><i class="lg">1 de enero de {a} · </i><i class="sm">1 ene. {a} · </i>dentro de {g} días</span>'),
        nums=[("escritores libres en Italia, Francia, Alemania y el Reino Unido", "muertos en {m}", "/es/dominio-publico-{a}/#ix1", "ue"),
              ("escritores libres en España", "muertos en {me}", "/es/dominio-publico-{a}/", "es"),
              ("libros libres en Estados Unidos", "publicados en {pub} · {usok} verificados", "/es/dominio-publico-{a}/#ix2", "us")],
        sez=("Por dónde empezar", "Las secciones del sitio"), sez_n=("1 de enero de {a}", "Quién pasa a ser libre, y dónde"),
        porte=[("/es/dominio-publico-{a}/", "Dominio público {a}", "1 de enero de {a}", "Quién pasa a ser libre el 1 de enero, explicado: los nombres más esperados, los libros estadounidenses, las reglas país por país.", "Leer"),
               ("/es/dominio-publico/", "Por país", "Seis países, seis reglas", "Italia, Francia, Alemania, España, el Reino Unido y Estados Unidos: la regla legal de cada país y quién pasa al dominio público.", "Elegir"),
               ("/es/ya-libres/", "Ya libres", "Archivo", "Busca un título o un autor: ¿ya es libre en Italia, Francia, Alemania, España, el Reino Unido, Estados Unidos?", "Buscar"),
               ("/es/calendario/{a}/", "Calendario {a}", "Aniversarios", "Los aniversarios literarios de {a}, día a día, para añadir a tu calendario.", "Abrir"),
               ("/es/como-funciona/", "Cómo funciona", "El método", "De dónde vienen los datos, cómo se calculan las fechas y cuán seguras son.", "Leer"),
               ("/es/tienda/", "Tienda", "Pósteres", "Pósteres tipográficos con las primeras líneas de libros de dominio público, impresos bajo demanda.", "Ver")],
        fonti=("Fuentes", "Wikidata (CC0), Wikipedia, Project Gutenberg, el registro de copyright estadounidense, Duke University (CC BY 4.0), Open Library y los catálogos de las bibliotecas nacionales. Listas actualizadas el {agg}."),
        fasi=dict(cnt_conto="dentro de {g} días", cnt_vigilia="Mañana", cnt_festa="Public Domain Day",
                  col_vigilia='A medianoche, en Europa y Estados Unidos, expiran los derechos de cientos de libros. Faltan <span class="giorni" id="orologio"></span>.',
                  col_oggi='Desde hoy, 1 de enero de {a}, son libres <span class="giorni">{ue}</span> escritores en Italia, Francia, Alemania y el Reino Unido, <span class="giorni">{es}</span> en España y <span class="giorni">{us}</span> libros en Estados Unidos.',
                  col_dal='Desde el 1 de enero de {a} son libres <span class="giorni">{ue}</span> escritores en Italia, Francia, Alemania y el Reino Unido, <span class="giorni">{es}</span> en España y <span class="giorni">{us}</span> libros en Estados Unidos.',
                  cta_vigilia="Quién pasa a ser libre a medianoche", cta_oggi="Quién es libre desde hoy", cta_dal="Quién es libre",
                  sez_oggi=("Desde hoy, 1 de enero de {a}", "Quién ha pasado a ser libre, y dónde"), sez_dal=("Desde el 1 de enero de {a}", "Quién ha pasado a ser libre, y dónde"),
                  data_em="desde el 1 de enero de {a}.", oggi_em="desde hoy."),
    ),
}


def pagina(lang, anno, P):
    """P: le funzioni del sito (scripts/pagine.py): testa_scheda, piede_scheda, CSS_ANNO, marchio."""
    import datetime, copy
    t = TESTI[lang]
    # 26/11/2026: testi della home riscritti direttamente nella lingua (testi/home-<lingua>.json, percorso -> testo)
    f_ = RADICE / "testi" / f"home-{lang}.json"
    if f_.exists():
        t = json.loads(json.dumps(t))   # copia, con le tuple come liste
        for percorso, v in json.loads(f_.read_text(encoding="utf-8")).items():
            parti, d = percorso.split("."), t
            for x in parti[:-1]:
                d = d[int(x)] if isinstance(d, (list, tuple)) else d[x]
            ult = parti[-1]
            vecchio = d[int(ult)] if isinstance(d, list) else d.get(ult)
            if not isinstance(vecchio, str) or vecchio in ("ue", "es", "us") or vecchio.startswith("/"):
                continue   # codici e indirizzi non si traducono
            if isinstance(d, list):
                d[int(ult)] = v
            else:
                d[ult] = v
    nu = numeri(anno)
    gg = max(0, (datetime.date(anno, 1, 1) - datetime.date.today()).days)
    fmt = dict(a=anno, a1=anno + 1, ue=migliaia(nu["ue"], lang), m=R.morti_liberi_nel(anno, "it"), me=R.morti_liberi_nel(anno, "es"), pub=nu["pub"], usok=migliaia(nu["us_ok"], lang),
               agg=data_lunga(nu["aggiornato"][:10], lang), g=migliaia(gg, lang))
    import lingue as L
    pag = [{"a": p.get("a_en", p["a"]) if lang == "en" else p.get("a_en", p["a"]).replace(" and ", L.CONG[lang]) if lang in L.CONG else p["a"], "t": p.get(lang) or p["en"], "r": t["libero"][p["dove"]].format(a=anno, p=elenco_paesi(p.get("paesi", []), lang)),
            "n": p["nota"][lang] if p.get("nota") else "", **({"q": p["q"]} if p.get("q") else {})}
           for p in pagine_frontespizio(anno)]
    if not pag:
        raise RuntimeError("home: nessuna opera per il frontespizio")
    alterne = (f'<link rel="alternate" hreflang="it" href="{SITO}/">\n<link rel="alternate" hreflang="en" href="{SITO}/en/">\n'
               f'<link rel="alternate" hreflang="x-default" href="{SITO}/">\n')
    case = {"it": "/it/", "en": "/", **{l: f"/{L.CARTELLA[l]['home']}/" for l in L.NUOVE}}
    altra = t["altra"]
    if L.NUOVE:   # 26/11/2026: con le lingue in più, il tasto lingua (IT · EN · DE) e tutte le versioni per Google
        alterne = L.hreflang(case, SITO)
        altra = L.selettore(lang, case)
    # 25/11/2026 (analisi SEO): chi c'è dietro il sito (Organization, con Marco e il suo LinkedIn già in fondo a ogni pagina) legato al WebSite
    org = {"@type": "Organization", "@id": SITO + "/#organizzazione", "name": "Public Domain Radar", "url": SITO + "/", "logo": SITO + "/assets/favicon.svg",
           "founder": {"@type": "Person", "name": "Marco Novali", "sameAs": "https://www.linkedin.com/in/marconovali"}}
    jsonld = ('<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@graph": [org, {"@type": "WebSite", "name": "Public Domain Radar",
              "url": t["url"], "inLanguage": lang, "description": t["descr"].format(a=anno), "publisher": {"@id": SITO + "/#organizzazione"}}]}, ensure_ascii=False) + "</script>")
    rimando = (f'<script>/* i vecchi indirizzi della home con # (filtri, schede) sono del radar, che ora sta su {t["radar"]} */\n'
               f'if(location.hash.length>1){{location.replace("{t["radar"]}"+location.hash)}}'
               + ('' if lang != 'it' else 'else if(new URLSearchParams(location.search).get("lang")==="en"){location.replace("/")}') + '</script>\n')
    testa = P["testa_scheda"](lang, esc(t["titolo"]), esc(t["descr"].format(a=anno)), t["url"], alterne, jsonld, altra,
                              "@@CNT@@", og_tipo="website", css_extra=P["CSS_ANNO"] + CSS, main_cls="pdd", body_cls="pdd-b")
    testa = testa.replace("@@CNT@@", t["cnt"].format(**fmt) if gg else f'<span id="cnt" style="color:var(--redt)">{t["fasi"]["cnt_festa"]}</span>').replace("</head>", '<script src="/assets/regole.js"></script>\n</head>', 1).replace("@@MARCHIO_S@@", P["marchio"]).replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + rimando, 1)
    numeri_html = "".join(f'<a href="{h.format(**fmt)}"><span class="n">{migliaia(nu[k], lang)}</span><span class="c">{esc(c)}</span><span class="m">{esc(m.format(**fmt))}</span></a>'
                          for c, m, h, k in t["nums"] if nu[k])
    # «Dove pubblichi?» (Marco, 25/11/2026): la stessa tendina della pagina dell'anno (scripts/pagine_paese.py, tendina_html)
    import pagine_paese as PP
    tendina = PP.tendina_html(lang)
    porte = "".join(f'<a class="porta" href="{h.format(**fmt)}"><span class="m">{esc(y.format(**fmt))}</span><h3>{esc(x.format(**fmt))}</h3>'
                    f'<p>{esc(d.format(**fmt))}</p><span class="go">{esc(v)} →</span></a>' for h, x, y, d, v in t["porte"])
    primo = pag[0]
    corpo = f"""<section class="fronte" id="pagina" aria-label="{ {"it": "Frontespizio", "de": "Titelseite", "fr": "Page de titre", "es": "Portada"}.get(lang, "Title page") }">
  <h1 class="vh">{ {"it": "Public Domain Radar: chi diventa libero, e quando", "de": "Public Domain Radar: wer gemeinfrei wird, und wann", "fr": "Public Domain Radar : qui entre dans le domaine public, et quand", "es": "Public Domain Radar: quién pasa al dominio público, y cuándo"}.get(lang, "Public Domain Radar: who becomes free, and when") }</h1>
  <div class="foglio" id="foglio" aria-live="polite">
    <p class="autore sc" id="autore">{esc(primo["a"])}</p>
    <p class="titolo" id="titolo">{esc(primo["t"])}</p>
    <p class="diritti"><span id="riga" class="vecchia">{esc(t["diritti"])}</span></p>
    <p class="avv" id="avv"></p>
  </div>
  <div class="colophon">
    <p id="colo">{t["colophon"]}</p>
    {tendina}
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
  // il pulsante è la tendina «Dove pubblichi?»: non cambia con la fase
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
    # 26/11/2026 (Marco): la home principale è quella inglese; l'italiana sta su /it/, /en/ rimanda a /
    (RADICE / "index.html").write_text(pagina("en", anno, P), encoding="utf-8")
    (RADICE / "it").mkdir(exist_ok=True)
    (RADICE / "it" / "index.html").write_text(pagina("it", anno, P), encoding="utf-8")
    (RADICE / "en").mkdir(exist_ok=True)
    import pagine_paese as PP
    (RADICE / "en" / "index.html").write_text(PP.pagina_rimando("/", "en"), encoding="utf-8")
    import lingue as L
    for l in L.NUOVE:   # 26/11/2026: home nelle lingue in più (i collegamenti alle pagine che esistono nella lingua passano lì)
        d = RADICE / L.CARTELLA[l]["home"]
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(L.localizza_link(pagina(l, anno, P), l, (), [anno]), encoding="utf-8")
    print("home: index.html ed en/index.html (frontespizio)")


if __name__ == "__main__":
    crea_home()
