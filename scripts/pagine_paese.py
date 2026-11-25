"""Pagine paese (ristrutturazione del 25/11/2026, mockup «pagine vere» approvato da Marco): una pagina per paese,
/pubblico-dominio/<paese>/ e /en/public-domain/<country>/, più l'indice /pubblico-dominio/ e /en/public-domain/.

Costruite con i pezzi della pagina dell'anno (pagine.pagina_landing): stessa testata, stesse righe «Indice» con i ritratti,
stesso JS_ANNO, stesso piede. Ogni pagina ha solo gli scrittori di quel paese (niente elenchi ripetuti tra paesi).
Le regole di legge vengono dal riquadro delle regole del radar (radar/index.html, costante REGOLE): un posto solo.
I conteggi sono quelli della pagina dell'anno; gli elenchi escludono data/fuori_classifica.json come le vetrine.
Si lancia da scripts/pagine.py (main) dopo la pagina dell'anno."""
import json
import re
import subprocess
from pathlib import Path

import pagine as P
import regole as R

RADICE = P.RADICE
esc = P.esc

PAESI = {   # chiave: (nome it, nome en, slug it, slug en, «in …» it, «in …» en, nazionalità su Wikidata, aggettivo it, aggettivo en)
    "it": ("Italia", "Italy", "italia", "italy", "in Italia", "in Italy", ["Italia", "Regno d'Italia"], "italiani", "Italian"),
    "fr": ("Francia", "France", "francia", "france", "in Francia", "in France", ["Francia"], "francesi", "French"),
    "de": ("Germania", "Germany", "germania", "germany", "in Germania", "in Germany",
           ["Germania", "Germania Ovest", "Germania Est", "Repubblica di Weimar", "Impero tedesco"], "tedeschi", "German"),
    "es": ("Spagna", "Spain", "spagna", "spain", "in Spagna", "in Spain", ["Spagna"], "spagnoli", "Spanish"),
    "uk": ("Regno Unito", "United Kingdom", "regno-unito", "united-kingdom", "nel Regno Unito", "in the United Kingdom",
           ["Regno Unito", "Regno Unito di Gran Bretagna e Irlanda"], "britannici", "British"),
    "us": ("Stati Uniti", "United States", "stati-uniti", "united-states", "negli Stati Uniti", "in the United States", [], "", ""),
}
ORDINE = ["it", "fr", "de", "es", "uk", "us"]
NOME_REGOLE = {"it": "Italia", "fr": "Francia", "de": "Germania", "es": "Spagna", "uk": "Regno Unito"}
NORMA = {"it": "Legge 633/1941, art. 25", "fr": "Code de la propriété intellectuelle, L123-1", "de": "Urheberrechtsgesetz, §64",
         "es": "Ley de 10 de enero de 1879, art. 6", "uk": "CDPA 1988, s. 12", "us": "17 U.S.C. § 304"}


def url_paese(k, lang):
    p = PAESI[k]
    return f"{P.SITO}/pubblico-dominio/{p[2]}/" if lang == "it" else f"{P.SITO}/en/public-domain/{p[3]}/"


def url_indice(lang):
    return f"{P.SITO}/pubblico-dominio/" if lang == "it" else f"{P.SITO}/en/public-domain/"


def regole_radar():
    """Le voci del riquadro delle regole del radar, lette dalla pagina stessa (un posto solo)."""
    h = (RADICE / "radar" / "index.html").read_text(encoding="utf-8")
    i = h.index("const REGOLE = ["); j = h.index("];", i) + 2
    js = h[i:j] + "\nprocess.stdout.write(JSON.stringify(REGOLE));"
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout
    return {r["paese"]["it"]: r["voci"] for r in json.loads(out)}


def anni_di(k):
    return R.anni_protezione(R.morti_liberi_nel(P.ANNO_PROSSIMO, k if k != "uk" else "it"), "es" if k == "es" else "it")


def testi(k, lang, anno, morti):
    """Riquadri «cosa significa davvero» e domande, per paese: solo regole già scritte nel riquadro del radar e nelle pagine."""
    it = lang == "it"
    T = (lambda a, b: a) if it else (lambda a, b: b)
    base = (T("Il testo, non l'edizione", "The text, not the edition"),
            T("È libero il testo originale. Le traduzioni recenti, le illustrazioni e le edizioni curate hanno diritti propri: per tradurre un autore serve una traduzione nuova, o una già libera.",
              "The original text is free. Recent translations, illustrations and edited editions have their own rights: to translate an author you need a new translation, or one that is already free."))
    consulenza = (T("È consulenza legale?", "Is this legal advice?"),
                  T("No. Sono informazioni generali costruite da dati aperti e possono contenere errori. Prima di pubblicare controlla la legge e i fatti per il tuo paese e la tua edizione.",
                    "No. It is general information built from open data, and it may contain errors. Before publishing, check the law and the facts for your country and your edition."))
    trad = (T("Le traduzioni sono libere insieme all'originale?", "Are translations free together with the original?"),
            T("No. Il testo originale sì; le traduzioni già pubblicate hanno diritti propri, che durano 70 anni dalla morte del traduttore.",
              "No. The original text is; translations already published have their own rights, which last 70 years after the translator's death."))
    tre = {
        "it": [base,
               (T("La proroga di guerra non c'è più", "The wartime extension is gone"),
                T("La proroga di 6 anni del 1945 è stata abrogata dalla legge 52/1996, art. 17: non si somma più ai 70 anni.",
                  "The 6-year extension of 1945 was repealed by Law 52/1996, Art. 17: it is no longer added to the 70 years.")),
               (T("Gli autori americani", "American authors"),
                T("In Italia conta la morte dell'autore anche per loro: la Cassazione ha applicato i 70 anni a un autore statunitense (caso Zorro).",
                  "In Italy the author's death counts for them too: the Court of Cassation applied the 70 years to a US author (the Zorro case)."))],
        "fr": [base,
               (T("Le proroghe di guerra", "The wartime extensions"),
                T("La Cassazione ha deciso che i 70 anni le comprendono, salvo durate più lunghe già in corso il 1° luglio 1995 (casi Monet e Boldini).",
                  "The Court of Cassation ruled that the 70 years include them, unless a longer term was already running on 1 July 1995 (Monet and Boldini cases).")),
               (T("Morti per la Francia", "Died for France"),
                T("Hanno 30 anni in più (L123-10). Se si sommino ai 70 la Cassazione non l'ha deciso: sulle schede li indichiamo a parte.",
                  "They get 30 more years (L123-10). Whether these are added to the 70 the Court of Cassation has not decided: we flag them on the author pages."))],
        "de": [base,
               (T("Dalla fine dell'anno", "From the end of the year"),
                T(f"I 70 anni partono dalla fine dell'anno in cui l'autore è morto (§69): chi è morto nel {morti} è libero dal 1° gennaio {anno}.",
                  f"The 70 years start at the end of the year the author died (§69): anyone who died in {morti} is free from 1 January {anno}.")),
               (T("Dipende da dove pubblichi", "It depends where you publish"),
                T("Lo stesso libro può essere libero negli Stati Uniti e protetto in Germania, o il contrario.",
                  "The same book can be free in the United States and protected in Germany, or the other way round."))],
        "es": [base,
               (T("80 anni, non 70", "80 years, not 70"),
                T(f"Per chi è morto prima del 7 dicembre 1987 vale ancora la legge del 1879: in Spagna nel {anno} entrano gli autori morti nel {morti}.",
                  f"For authors who died before 7 December 1987 the 1879 law still applies: in Spain, authors who died in {morti} enter in {anno}.")),
               (T("Dipende da dove pubblichi", "It depends where you publish"),
                T("Un autore morto nel 1956 è libero in Italia, Francia, Germania e Regno Unito dal 2027, in Spagna solo dal 2037.",
                  "An author who died in 1956 is free in Italy, France, Germany and the UK from 2027, in Spain only from 2037."))],
        "uk": [base,
               (T("La regola del 2039", "The 2039 rule"),
                T("Le opere rimaste inedite a fine 1988, di autori morti prima del 1969, sono protette fino al 31 dicembre 2039.",
                  "Works still unpublished at the end of 1988, by authors who died before 1969, are protected until 31 December 2039.")),
               (T("La veste tipografica", "The typographical arrangement"),
                T("L'impaginazione di un'edizione ha un diritto suo di 25 anni: un testo libero non autorizza a fotografare un'edizione recente.",
                  "The layout of an edition has its own right for 25 years: a free text does not allow you to photocopy a recent edition."))],
    }
    faq = {
        "it": [trad, (T("Cos'è la proroga del Trattato di pace?", "What is the Peace Treaty extension?"),
                      T("Per gli autori dei paesi alleati (non per gli italiani) il periodo di guerra non conta nella durata (Trattato di pace del 1947, allegato XV). I tribunali finora non l'hanno applicata oltre i 70 anni; sulle schede lo segnaliamo.",
                        "For authors from the Allied countries (not for Italians) the war years do not count towards the term (1947 Peace Treaty, Annex XV). Courts have not applied it beyond the 70 years so far; we flag it on the author pages."))],
        "fr": [trad],
        "de": [trad],
        "es": [(T(f"Perché in Spagna entrano gli autori morti nel {morti}?", f"Why do authors who died in {morti} enter in Spain?"),
                T("Per chi è morto prima del 7 dicembre 1987 la legge spagnola applica ancora gli 80 anni della legge del 1879 (Ley de Propiedad Intelectual, disposizione transitoria quarta).",
                  "For authors who died before 7 December 1987, Spanish law still applies the 80 years of the 1879 law (Ley de Propiedad Intelectual, fourth transitional provision).")), trad],
        "uk": [(T("Le opere straniere hanno la stessa durata?", "Do foreign works have the same term?"),
                T("Se il paese d'origine non è il Regno Unito e l'autore non è britannico, vale la durata del paese d'origine, se più breve (sezione 12(6)).",
                  "If the country of origin is not the UK and the author is not British, the term of the country of origin applies, if shorter (section 12(6)).")), trad],
    }
    return tre[k], faq[k] + [consulenza]


def righe(aut, n, lang):
    """Le righe «Indice» della pagina dell'anno (stesso markup, ritratto da Wikimedia Commons)."""
    it = lang == "it"
    out, crediti = [], []
    for k, a in enumerate(aut[:n]):
        nome = P.pulisci(a["nome"])
        href = f"/autore/{a['pagina']}/" if it else f"/en/author/{a['pagina_en']}/"
        foto = a.get("foto") or {}
        df = ""
        if foto.get("url"):
            df = ' data-f="' + esc(re.sub(r"width=\d+", "width=480", foto["url"])) + '"'
            crediti.append(f'{esc(nome)}: <a href="{esc(foto.get("pagina", ""))}" rel="noopener">{esc(P.pulisci(foto.get("licenza")) or "Wikimedia Commons")}</a>')
        if it:
            ruolo = (a.get("professioni") or [""])[0]
            sotto = f"{P.anno_di(a.get('nascita')) or '?'} – {P._data_lunga(a['morte'], 'it')}"
        else:
            ruolo = re.sub(r"\s*\([^)]*\)\s*$", "", P.pulisci(a.get("descrizione")))
            sotto = f"died {P._data_lunga(a['morte'], 'en')}"
        mt = (esc(ruolo) + "<br>" if ruolo else "") + esc(sotto)
        out.append(f'<li class="row"{df} data-i="{esc(P.iniziali_nome(nome))}"><span class="no">{k + 1:02d}</span>'
                   f'<span class="nm"><a href="{href}">{esc(nome)}</a></span><span class="mt">{mt}</span></li>\n')
    return "".join(out), crediti


def lista_regole(voci, lang, etichetta=None):
    li = []
    for v in voci:
        if v.get("aperto"):
            continue
        f = v.get("f", "")
        if v.get("intero"):   # voci che non sono norme (fonti, date): niente divisione «legge, articolo»
            p_, resto = f, ""
        else:
            p_ = re.sub(r" con l.Italia \(testo francese\)", " del 1947", f.split(",")[0])
            resto = ", ".join(x.strip() for x in f.split(",")[1:])
        a = (f'<a href="{esc(v["u"])}" rel="noopener">{etichetta or ("Leggi la norma →" if lang == "it" else "Read the law →")}</a>' if v.get("u") else "<span></span>")
        li.append(f'<li><span class="p">{esc(p_)}</span><span class="m y">{esc(resto)}</span><span class="r">{esc(v["t"][lang])}</span>{a}</li>\n')
    return '<ul class="where">\n' + "".join(li) + "</ul>\n"


def apri(lang, titolo, descr, url, alt, jsonld, altra, anno, extra_css=""):
    it = lang == "it"
    T = (lambda a, b: a) if it else (lambda a, b: b)
    import datetime
    libero = f"{anno}-01-01"
    gg = max(0, (datetime.date.fromisoformat(libero) - datetime.date.today()).days)
    data_l = T(f"1° gennaio {anno}", f"1 January {anno}")
    cnt = (f'<span id="cnt"><i class="lg">{data_l} · </i><i class="sm">{T(f"1° gen {anno}", f"1 Jan {anno}")} · </i>'
           f'{T("tra", "in")} <b id="pd-giorni" data-d="{libero}" style="font-weight:inherit">{P.migliaia(gg, lang)}</b> {T("giorni", "days")}</span>') if gg > 0 else f'<span id="cnt">{data_l}</span>'
    testa = P.testa_scheda(lang, esc(titolo), esc(descr), url, alt, jsonld, altra, "@@CNT@@", og_tipo="website",
                           css_extra=P.CSS_ANNO + PORTE_CSS + extra_css, main_cls="pdd", body_cls="pdd-b")
    testa = testa.replace('<div class="cnt">@@CNT@@</div>', f'<div class="cnt">{cnt}</div>')
    return testa.replace("@@MARCHIO_S@@", P.marchio_html(56).replace('<span class="pdr" style="--w:56px">', "").rsplit("</span>", 1)[0])


# le «porte» della home (stesso disegno), per «Già liberi» e l'indice dei paesi
PORTE_CSS = (".porte{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));margin-top:0}"
             ".porta{display:flex;flex-direction:column;align-items:center;text-align:center;padding:34px 28px 38px;border-bottom:1px solid var(--hair);text-decoration:none;color:var(--ink)}"
             ".porta:nth-child(odd){border-right:1px solid var(--hair)}.porta .m{color:var(--redt)}"
             ".porta h3{margin:12px 0 12px;font-family:var(--disp);font-weight:800;text-transform:uppercase;font-size:clamp(34px,3.3vw,52px);line-height:.95;padding-top:.08em}"
             ".porta p{margin:0 auto;font-size:16px;line-height:1.55;max-width:40ch}"
             ".porta .go{margin-top:20px;font-family:var(--mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;border-bottom:2px solid var(--red);padding-bottom:4px}"
             ".porta:hover h3{color:var(--red)}.porta .big{font-family:var(--disp);font-weight:900;font-size:clamp(64px,7vw,104px);line-height:.85;color:var(--red)}"
             "@media (max-width:760px){.porte{grid-template-columns:1fr}.porta{padding:28px 0 32px}.porta:nth-child(odd){border-right:0}}")


def sezione(titolo, dx, corpo, cls="sec", id_=""):
    return f'<section class="{cls}"{f" id={chr(34)}{id_}{chr(34)}" if id_ else ""}>\n<div class="sh m"><h2>{titolo}</h2><span>{dx}</span></div>\n{corpo}</section>\n'


def alterne(fn):
    return f'<link rel="alternate" hreflang="it" href="{fn("it")}">\n<link rel="alternate" hreflang="en" href="{fn("en")}">\n'


def pagina_paese_ue(k, lang, REG, liste):
    it = lang == "it"
    T = (lambda a, b: a) if it else (lambda a, b: b)
    nome_it, nome_en, _, _, in_it, in_en, naz, agg_it, agg_en = PAESI[k]
    nome, in_ = T(nome_it, nome_en), T(in_it, in_en)
    anno = P.ANNO_PROSSIMO
    pk = "es" if k == "es" else "ue"
    pacc, pacc2 = liste[(pk, anno)], liste[(pk, anno + 1)]
    morti, morti2 = R.morti_liberi_nel(anno, "es" if k == "es" else "it"), R.morti_liberi_nel(anno + 1, "es" if k == "es" else "it")
    anni = R.anni_protezione(morti, "es" if k == "es" else "it")
    tutti = [a for a in pacc.get("autori", []) if a.get("letterario") and a.get("morte")]
    # 25/11/2026 (Marco): la pagina di un paese elenca TUTTI gli scrittori che diventano liberi in quel paese (la legge vale
    # per autori di ogni nazionalità: Brecht è libero in Italia), in ordine di visite sulla Wikipedia della lingua del paese.
    # In Francia restano fuori i «morti per la Francia» (30 anni in più, L123-10). Gli scrittori del paese sono una lista a parte.
    lingua = {"it": "it", "fr": "fr", "de": "de", "uk": "en", "es": "es"}[k]
    vale = (lambda a: not P.è_mpf(a)) if k == "fr" else (lambda a: True)
    tutti = [a for a in tutti if vale(a)]
    liberi = lambda pc: sorted((a for a in P._letterari(pc, lang) if vale(a)), key=lambda a: -(a.get(f"visite_{lingua}") or 0))
    lib27 = liberi(pacc)   # solo l'anno in vetrina: l'anno dopo ha la sua pagina dal 7 gennaio (Marco, 25/11/2026)
    nazionali = lambda lst: [a for a in lst if set(a.get("paesi") or []) & set(naz)]
    naz27 = nazionali(lib27)
    n_naz = len([a for a in tutti if set(a.get("paesi") or []) & set(naz)])
    app = "/radar/" if it else "/en/radar/"
    url = url_paese(k, lang)
    tre, faq = testi(k, lang, anno, morti)
    titolo = T(f"Pubblico dominio {in_it}: quando un libro diventa libero · Public Domain Radar",
               f"Public domain {in_en}: when a book becomes free · Public Domain Radar")
    descr = T(f"{in_it[0].upper() + in_it[1:]} un'opera diventa libera {anni} anni dopo la morte dell'autore. Gli scrittori che entrano in pubblico dominio nel {anno}, la regola di legge e cosa controllare.",
              f"{in_en[0].upper() + in_en[1:]} a work becomes free {anni} years after the author's death. The writers entering the public domain in {anno}, the legal rule and what to check.")
    jl = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "@id": url, "url": url, "name": titolo, "description": descr, "inLanguage": lang,
         "isPartOf": {"@type": "WebSite", "name": "Public Domain Radar", "url": P.SITO + ("/" if it else "/en/")}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": P.SITO + ("/" if it else "/en/")},
            {"@type": "ListItem", "position": 2, "name": T("Per paese", "By country"), "item": url_indice(lang)},
            {"@type": "ListItem", "position": 3, "name": nome, "item": url}]},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}} for q, r in faq]}]}
    jsonld = '<script type="application/ld+json">' + json.dumps(jl, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    altra = (f'<a href="{url_paese(k, "en").replace(P.SITO, "")}" hreflang="en">EN</a>' if it else f'<a href="{url_paese(k, "it").replace(P.SITO, "")}" hreflang="it">IT</a>')
    out = [apri(lang, titolo, descr, url, alterne(lambda l: url_paese(k, l)), jsonld, altra, anno, CSS_ELENCO)]
    w = lambda t: f'<span class="w"><span>{t}</span></span>'
    out.append(f'<section class="open">\n<nav class="bc m" aria-label="{T("Sei qui", "You are here")}"><a href="{"/" if it else "/en/"}">Home</a> › '
               f'<a href="{url_indice(lang).replace(P.SITO, "")}">{T("Per paese", "By country")}</a> › <span>{esc(nome)}</span></nav>\n'
               f'<p class="m k">{T("Pubblico dominio", "Public domain")} · {esc(nome)}</p>\n'
               f'<h1 class="h1">{w(T("Quando un libro", "When a book"))}<br>{w(T("diventa libero", "becomes free"))}<br>{w(esc(in_))}</h1>\n'
               f'<p class="say" id="say">{esc(T(f"{in_it[0].upper() + in_it[1:]} un’opera diventa libera {anni} anni dopo la morte dell’autore, dal 1° gennaio dell’anno dopo. Chi entra, cosa è già libero e cosa controllare, con le fonti di legge.", f"{in_en[0].upper() + in_en[1:]} a work becomes free {anni} years after the author’s death, from 1 January of the following year. Who enters, what is already free and what to check, with the legal sources."))}</p>\n</section>\n')
    nums = [(anni, T("anni dopo la morte dell'autore", "years after the author's death"), NORMA[k]),
            (len(tutti), T(f"scrittori liberi {in_it} dal 1° gennaio {anno}", f"writers free {in_en} from 1 January {anno}"), T(f"di tutti i paesi, morti nel {morti}", f"from every country, died in {morti}")),
            (n_naz, T(f"di questi sono {agg_it}", f"of them are {agg_en}"), T(f"morti nel {morti}", f"died in {morti}"))]
    out.append('<div class="nums">' + "".join(f'<a href="#ix1"><span class="n">{P.migliaia(x, lang)}</span><span class="c">{esc(c)}</span><span class="m">{esc(m)}</span></a>' for x, c, m in nums) + "</div>\n")
    wl = {"it": "italiano", "fr": "francese", "de": "tedesco", "uk": "inglese", "es": "spagnolo"}[k]
    wl_en = {"it": "Italian", "fr": "French", "de": "German", "uk": "English", "es": "Spanish"}[k]
    # 25/11/2026 (Marco): un elenco solo, completo, con ricerca, «solo del paese» ed Excel, al posto della classifica dei 12
    # e della lista degli scrittori del paese. Gli autori di data/fuori_classifica.json restano nell'elenco completo e nei
    # conteggi, come nel radar (pagine.opera_in_vetrina: escono solo da vetrine e classifiche).
    out.append(elenco_completo(k, lang, sorted(tutti, key=lambda a: -(a.get(f"visite_{lingua}") or 0)), naz, morti, wl, wl_en, in_it, in_en, agg_it, agg_en, anni))
    gp = "/gia-pubblici/" if it else "/en/already-public/"
    cal = f"/calendario/{anno}/" if it else f"/en/calendar/{anno}/"
    out.append(sezione(T(f"Già liberi {in_it}", f"Already free {in_en}"), T("Archivio", "Archive"),
                       f'<div class="porte"><a class="porta" href="{gp}"><span class="m">{T("Già pubblici", "Already public")}</span><h3>{T("Cosa è già libero", "What is already free")}</h3>'
                       f'<p>{T(f"Cerca un titolo o un autore: è già libero {in_it}? Scaffali e classifiche delle opere già libere.", f"Search a title or an author: is it already free {in_en}? Shelves and rankings of works already free.")}</p><span class="go">{T("Cerca →", "Search →")}</span></a>'
                       f'<a class="porta" href="{cal}"><span class="m">{T("Anniversari", "Anniversaries")}</span><h3>{T(f"Calendario {anno}", f"Calendar {anno}")}</h3>'
                       f'<p>{T(f"Gli anniversari letterari del {anno} giorno per giorno.", f"The literary anniversaries of {anno}, day by day.")}</p><span class="go">{T("Apri →", "Open →")}</span></a></div>\n'))
    out.append(sezione(T("La regola, dalla legge", "The rule, from the law"), T("Testi di legge letti alla fonte", "Legal texts read at the source"), lista_regole(REG[NOME_REGOLE[k]], lang)))
    out.append(sezione(T("Cosa significa davvero", "What it really means"), T("Prima di pubblicare", "Before you publish"),
                       '<div class="three">\n' + "".join(f'<div><span class="m">{i + 1:02d}</span><h3>{esc(t)}</h3><p>{esc(x)}</p></div>\n' for i, (t, x) in enumerate(tre)) + "</div>\n"))
    out.append(sezione(T("Le risposte brevi", "The short answers"), T("Domande", "Questions"),
                       "<div>\n" + "".join(f'<div class="acc"><button type="button">{esc(q)}<span>[+]</span></button><div class="bd"><p>{esc(r)}</p></div></div>\n' for q, r in faq) + "</div>\n"))
    out.append(altri_paesi(k, lang))
    out.append('<div class="pf" id="pf" aria-hidden="true"></div>\n')
    out.append(P.JS_ANNO.replace("@@LOC@@", "it-IT" if it else "en-GB"))
    out.append(P.piede_scheda(lang))
    return "".join(out), url


CSS_ELENCO = (".tutti .ctl{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:26px 0 8px}"
              ".tutti .q{flex:1 1 280px;display:flex;align-items:center;gap:10px;border-bottom:2px solid var(--ink);padding:6px 0}"
              ".tutti .q input{border:0;background:transparent;font-family:var(--disp);font-weight:800;text-transform:uppercase;font-size:clamp(24px,3vw,34px);width:100%;outline:0;color:var(--ink);border-radius:0}"
              ".tutti .ch{font-family:var(--mono);font-size:12px;letter-spacing:.1em;text-transform:uppercase;padding:10px 14px;border:1px solid var(--ink);background:transparent;cursor:pointer;color:var(--ink)}"
              ".tutti .ch.on{background:var(--ink);color:var(--paper)}"
              ".tutti ol{list-style:none;margin:18px 0 0;padding:0;border-top:1px solid var(--ink)}"
              ".tutti li{display:grid;grid-template-columns:56px minmax(0,1fr);gap:2px 16px;padding:12px 0;border-bottom:1px solid var(--hair)}"
              ".tutti li .k{grid-row:1/3;font-family:var(--mono);font-size:12px;color:var(--grey);padding-top:6px}"
              ".tutti li .nm{font-size:20px;line-height:1.25}.tutti li .nm a{color:inherit;text-decoration:none;border-bottom:1px solid var(--hair)}"
              ".tutti li .nm a:hover{color:var(--red)}"
              ".tutti li .mt{font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--grey)}"
              ".tutti .conta{font-family:var(--mono);font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--grey);margin-top:14px}"
              ".tutti li[hidden],.tutti [hidden]{display:none}")


def _norm(t):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", t or "") if not unicodedata.combining(c)).lower()


def elenco_completo(k, lang, autori, naz, morti, wl, wl_en, in_it, in_en, agg_it, agg_en, anni):
    """Elenco completo di chi diventa libero nel paese: un elenco solo, ricerca, filtro «solo del paese», Excel (CSV)."""
    it = lang == "it"
    T = (lambda a, b: a) if it else (lambda a, b: b)
    anno = P.ANNO_PROSSIMO
    pag = "pagina" if it else "pagina_en"
    li, n_naz = [], 0
    for i, a in enumerate(autori):
        del_paese = bool(set(a.get("paesi") or []) & set(naz))
        n_naz += del_paese
        nome = P.pulisci(a["nome"])
        if it:
            ruolo = ", ".join((a.get("professioni") or [])[:2])
        else:
            ruolo = re.sub(r"\s*\([^)]*\)\s*$", "", P.pulisci(a.get("descrizione")))
        nome_h = f'<a href="{"/autore/" if it else "/en/author/"}{a[pag]}/">{esc(nome)}</a>' if a.get(pag) else esc(nome)
        li.append(f'<li data-p="{int(del_paese)}" data-n="{esc(_norm(nome))}"><span class="k">{i + 1:03d}</span><span class="nm">{nome_h}</span>'
                  f'<span class="mt">{P.anno_di(a.get("nascita")) or "?"}–{P.anno_di(a.get("morte"))}{(" · " + esc(ruolo)) if ruolo else ""}</span></li>')
    n = P.migliaia(len(autori), lang)
    frase = T(f"{in_it[0].upper() + in_it[1:]} le opere diventano libere {anni} anni dopo la morte dell’autore. Il 1° gennaio {anno} tocca agli scrittori morti nel {morti}, di qualsiasi paese.",
              f"{in_en[0].upper() + in_en[1:]} works become free {anni} years after the author’s death. On 1 January {anno} it is the turn of writers who died in {morti}, from any country.")
    if k == "es":   # gli 80 anni valgono solo per chi è morto prima del 7 dicembre 1987 (riquadro delle regole del radar)
        frase = T(f"In Spagna, per chi è morto prima del 7 dicembre 1987, le opere diventano libere 80 anni dopo la morte dell’autore. Il 1° gennaio {anno} tocca agli scrittori morti nel {morti}, di qualsiasi paese.",
                  f"In Spain, for authors who died before 7 December 1987, works become free 80 years after the author’s death. On 1 January {anno} it is the turn of writers who died in {morti}, from any country.")
    if k == "fr":
        frase += T(" Gli autori «morti per la Francia» hanno 30 anni in più e non sono in questo elenco.", " Authors who «died for France» get 30 more years and are not in this list.")
    testi = {"primi": T("I primi {v} di {n}, in ordine di visite su Wikipedia in " + wl, "The first {v} of {n}, by " + wl_en + " Wikipedia visits"),
             "trovati": T("{n} trovati", "{n} found"), "trovato": T("1 trovato", "1 found"), "file": f"{PAESI[k][2] if it else PAESI[k][3]}-{anno}.csv",
             "intest": T("Numero;Nome;Anni;Professione", "Number;Name;Years;Occupation")}
    js = ("<script>(function(){var L=[].slice.call(document.querySelectorAll('#lista li')),f='tutti',q='',max=30,T=" + json.dumps(testi, ensure_ascii=False) + ";"
          "function nr(t){return t.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase().trim()}"
          "function vai(){var n=0,v=0;L.forEach(function(li){var ok=(f==='tutti'||li.dataset.p==='1')&&(!q||q.every(function(t){return li.dataset.n.split(' ').some(function(w){return w.indexOf(t)===0})}));if(ok)n++;var m=ok&&(q||f!=='tutti'||n<=max);li.hidden=!m;if(m)v++});"
          "document.getElementById('conta').textContent=(q||f!=='tutti')?(n===1?T.trovato:T.trovati.replace('{n}',n)):T.primi.replace('{v}',v).replace('{n}',n);document.getElementById('altri').hidden=v>=n}"
          "document.getElementById('q').addEventListener('input',function(e){q=nr(e.target.value);q=q?q.split(/\\s+/):'';vai()});"
          "[].forEach.call(document.querySelectorAll('.tutti [data-f]'),function(b){b.onclick=function(){f=b.dataset.f;[].forEach.call(document.querySelectorAll('.tutti [data-f]'),function(x){x.classList.toggle('on',x===b);x.setAttribute('aria-pressed',x===b)});vai()}});"
          "document.getElementById('altri').onclick=function(){max=1e9;vai()};"
          "document.getElementById('xls').onclick=function(){var r=[T.intest];L.forEach(function(li){var mt=li.querySelector('.mt').textContent.split(' · ');r.push([li.querySelector('.k').textContent,li.querySelector('.nm').textContent,mt[0],mt.slice(1).join(' · ')].map(function(x){return '\"'+x.replace(/\"/g,'\"\"')+'\"'}).join(';'))});"
          "var a=document.createElement('a');a.href=URL.createObjectURL(new Blob(['\\ufeff'+r.join('\\n')],{type:'text/csv;charset=utf-8'}));a.download=T.file;document.body.appendChild(a);a.click();a.remove()};vai()})();</script>")
    corpo = (f'<p class="say" style="margin-top:22px;font-size:clamp(18px,1.6vw,22px)">{esc(frase)}</p>'
             f'<div class="ctl"><label class="q"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg>'
             f'<input id="q" type="search" placeholder="{T("Cerca un nome", "Search a name")}" aria-label="{T("Cerca un nome", "Search a name")}"></label>'
             f'<button class="ch on" type="button" data-f="tutti" aria-pressed="true">{T("Tutti", "All")} · {n}</button>'
             f'<button class="ch" type="button" data-f="paese" aria-pressed="false">{T(f"Solo {agg_it}", f"{agg_en} only")} · {P.migliaia(n_naz, lang)}</button>'
             f'<button class="ch" type="button" id="xls">{T("Scarica Excel", "Download Excel")}</button></div>'
             f'<p class="conta" id="conta" aria-live="polite"></p><ol id="lista">{"".join(li)}</ol>'
             f'<button class="ch" type="button" id="altri" style="margin-top:18px">{T("Mostra tutti", "Show all")}</button>\n' + js.replace("li.dataset.p==='1'", "li.dataset.p==='1'").replace("f==='tutti'||", "f==='tutti'||") + "\n")
    return sezione(T(f"Chi diventa libero {in_it} nel {anno}", f"Who becomes free {in_en} in {anno}"),
                   T(f"{n} scrittori · morti nel {morti}", f"{n} writers · died in {morti}"), corpo, "sec tutti", "ix1")


def altri_paesi(k, lang):
    it = lang == "it"
    T = (lambda a, b: a) if it else (lambda a, b: b)
    v = "".join(f'<a href="{url_paese(x, lang).replace(P.SITO, "")}">{esc(PAESI[x][0] if it else PAESI[x][1])}</a>' for x in ORDINE if x != k)
    return sezione(T("Gli altri paesi", "The other countries"), T("Ogni paese ha la sua regola", "Each country has its own rule"),
                   f'<nav class="letters" aria-label="{T("Paesi", "Countries")}">{v}</nav>\n')


def pagina_usa(lang, liste):
    it = lang == "it"
    T = (lambda a, b: a) if it else (lambda a, b: b)
    anno = P.ANNO_PROSSIMO
    opere = (liste.get(("us", anno)) or {}).get("opere", [])
    pub = R.pubblicate_libere_usa_nel(anno)
    st = P.stati_usa_anno(anno)
    n_st = {s: sum(1 for o in opere if st.get(o["qid"], "da_confermare") == s) for s in ("verificata", "edizione", "da_confermare")}
    eti = {"verificata": T("Verificato", "Verified"), "edizione": T("Edizione confermata", "Edition confirmed"), "da_confermare": T("Da confermare", "To be confirmed")}
    url = url_paese("us", lang)
    app = "/radar/" if it else "/en/radar/"
    titolo = T(f"Pubblico dominio negli Stati Uniti: i libri del {pub} liberi nel {anno} · Public Domain Radar",
               f"Public domain in the United States: the {pub} books free in {anno} · Public Domain Radar")
    descr = T(f"Negli Stati Uniti conta l'anno di pubblicazione: 95 anni dopo. Tutti i {len(opere)} libri del {pub} che diventano liberi il 1° gennaio {anno}, con lo stato di verifica e le fonti.",
              f"In the United States the publication year counts: 95 years later. All {len(opere)} books from {pub} that become free on 1 January {anno}, with their verification status and sources.")
    faq = [(T(f"Ogni libro del {pub} diventa libero solo ora?", f"Does every {pub} book only become free now?"),
            T("Non sempre. Le opere uscite per la prima volta negli USA senza rinnovo del copyright dopo 28 anni erano già libere prima. Le opere straniere che hanno riavuto la protezione nel 1996 (17 U.S.C. § 104A) durano 95 anni dalla pubblicazione.",
              "Not always. Works first published in the USA whose copyright was not renewed after 28 years were already free earlier. Foreign works that regained protection in 1996 (17 U.S.C. § 104A) last 95 years from publication.")),
           (T("Un libro libero negli USA è libero anche in Italia?", "Is a book free in the USA also free in Europe?"),
            T("Non automaticamente: in Italia conta quando è morto l'autore, anche per gli americani (Cassazione, caso Zorro).",
              "Not automatically: in Italy, France, Germany, Spain and the UK the author's death counts, even for American authors.")),
           (T("È consulenza legale?", "Is this legal advice?"),
            T("No. Sono informazioni generali costruite da dati aperti e possono contenere errori. Prima di pubblicare controlla la legge e i fatti per il tuo paese e la tua edizione.",
              "No. It is general information built from open data, and it may contain errors. Before publishing, check the law and the facts for your country and your edition."))]
    jl = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "@id": url, "url": url, "name": titolo, "description": descr, "inLanguage": lang},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": P.SITO + ("/" if it else "/en/")},
            {"@type": "ListItem", "position": 2, "name": T("Per paese", "By country"), "item": url_indice(lang)},
            {"@type": "ListItem", "position": 3, "name": T("Stati Uniti", "United States"), "item": url}]},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}} for q, r in faq]}]}
    jsonld = '<script type="application/ld+json">' + json.dumps(jl, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    altra = (f'<a href="{url_paese("us", "en").replace(P.SITO, "")}" hreflang="en">EN</a>' if it else f'<a href="{url_paese("us", "it").replace(P.SITO, "")}" hreflang="it">IT</a>')
    out = [apri(lang, titolo, descr, url, alterne(lambda l: url_paese("us", l)), jsonld, altra, anno)]
    w = lambda t: f'<span class="w"><span>{t}</span></span>'
    out.append(f'<section class="open">\n<nav class="bc m" aria-label="{T("Sei qui", "You are here")}"><a href="{"/" if it else "/en/"}">Home</a> › '
               f'<a href="{url_indice(lang).replace(P.SITO, "")}">{T("Per paese", "By country")}</a> › <span>{T("Stati Uniti", "United States")}</span></nav>\n'
               f'<p class="m k">{T("Pubblico dominio · Stati Uniti", "Public domain · United States")}</p>\n'
               f'<h1 class="h1">{w(T("Quando un libro", "When a book"))}<br>{w(T("diventa libero", "becomes free"))}<br>{w(T("negli Stati Uniti", "in the United States"))}</h1>\n'
               f'<p class="say" id="say">{esc(T(f"Negli Stati Uniti conta l’anno della prima uscita, non la morte dell’autore: 95 anni dopo. Il 1° gennaio {anno} tocca ai libri del {pub}, opera per opera, con le fonti.", f"In the United States what counts is the year of first publication, not the author’s death: 95 years later. On 1 January {anno} it is the turn of the {pub} books, work by work, with sources."))}</p>\n</section>\n')
    nums = [(95, T("anni dalla pubblicazione", "years from publication"), "17 U.S.C. § 304"),
            (len(opere), T(f"libri del {pub} liberi dal {anno}", f"{pub} books free from {anno}"), T(f"{n_st['verificata']} verificati, {n_st['edizione']} con l'edizione confermata", f"{n_st['verificata']} verified, {n_st['edizione']} edition confirmed"))]
    out.append('<div class="nums">' + "".join(f'<a href="#ix2"><span class="n">{P.migliaia(x, lang)}</span><span class="c">{esc(c)}</span><span class="m">{esc(m)}</span></a>' for x, c, m in nums) + "</div>\n")
    rr = []
    # in classifica solo i libri «Verificato» e fuori dai fuori classifica (Marco, 25/11/2026); tutti gli altri nel radar con il loro stato
    verif = [o for o in opere if st.get(o["qid"]) == "verificata" and P.opera_in_vetrina(o)]
    for i, o in enumerate(verif):
        chi = ", ".join(P.pulisci(a["nome"]) for a in (o.get("autori") or [])[:2])
        t = (o.get("titolo_it") or o["titolo"]) if it else o["titolo"]
        foto = (o.get("foto") or {}).get("url") if isinstance(o.get("foto"), dict) else None
        df = f' data-f="{esc(re.sub(r"width=\d+", "width=480", foto))}"' if foto else ""
        rr.append(f'<li class="row"{df} data-i="{esc(P.iniziali_nome(chi.split(", ")[0] or "?"))}"><span class="no">{i + 1:02d}</span>'
                  f'<span class="nm"><a href="{app}#/opera/{o["qid"]}">{esc(t)}</a></span><span class="mt">{esc(chi)}<br>{eti["verificata"]}</span></li>\n')
    out.append(sezione(T(f"I libri del {pub} verificati", f"The verified {pub} books"), T("in ordine di visite su Wikipedia", "by Wikipedia visits"),
                       f'<ol class="rows" style="margin-top:28px">\n{"".join(rr)}</ol>\n'
                       f'<a href="{app}#/us/{anno}" class="more">{T(f"Tutti i {len(opere)} libri del {pub}, con il loro stato, nel radar →", f"All {len(opere)} books from {pub}, with their status, in the radar →")}</a>\n', "sec ix", "ix2"))
    leggi = [{"t": {"it": "Opere pubblicate prima del 1978: 95 anni dalla pubblicazione.", "en": "Works published before 1978: 95 years from publication."}, "f": "17 U.S.C. § 304"},
             {"t": {"it": "Le opere straniere che avevano perso la protezione l'hanno riavuta nel 1996, e durano 95 anni dalla pubblicazione.",
                    "en": "Foreign works that had lost protection regained it in 1996, and last 95 years from publication."}, "f": "17 U.S.C. § 104A"}]
    out.append(sezione(T("La regola, dalla legge", "The rule, from the law"), "Copyright Act", lista_regole(leggi, lang)))
    tre = [(eti["verificata"], T("La prima uscita è documentata da due fonti indipendenti o da una scheda del Catalog of Copyright Entries, e nessuna fonte indica un'uscita precedente.",
                                 "First publication is documented by two independent sources or by a Catalog of Copyright Entries record, and no source points to an earlier release.")),
           (eti["edizione"], T("Una fonte diversa da Wikidata conferma l'anno dell'edizione, ma la prima uscita non è ancora verificata.",
                               "A source other than Wikidata confirms the year of the edition, but first publication is not yet verified.")),
           (eti["da_confermare"], T("C'è solo Wikidata: l'anno va ancora confermato.", "Only Wikidata so far: the year still needs confirming."))]
    out.append(sezione(T("Cosa significa davvero", "What it really means"), T("Gli stati delle opere", "The status of each work"),
                       '<div class="three">\n' + "".join(f'<div><span class="m">{i + 1:02d}</span><h3>{esc(t)}</h3><p>{esc(x)}</p></div>\n' for i, (t, x) in enumerate(tre)) + "</div>\n"))
    out.append(sezione(T("Le risposte brevi", "The short answers"), T("Domande", "Questions"),
                       "<div>\n" + "".join(f'<div class="acc"><button type="button">{esc(q)}<span>[+]</span></button><div class="bd"><p>{esc(r)}</p></div></div>\n' for q, r in faq) + "</div>\n"))
    out.append(altri_paesi("us", lang))
    out.append('<div class="pf" id="pf" aria-hidden="true"></div>\n')
    out.append(P.JS_ANNO.replace("@@LOC@@", "it-IT" if it else "en-GB"))
    out.append(P.piede_scheda(lang))
    return "".join(out), url


def pagina_indice(lang, liste):
    it = lang == "it"
    T = (lambda a, b: a) if it else (lambda a, b: b)
    anno = P.ANNO_PROSSIMO
    url = url_indice(lang)
    titolo = T("Pubblico dominio per paese: le regole di Italia, Francia, Germania, Spagna, Regno Unito e Stati Uniti · Public Domain Radar",
               "Public domain by country: the rules of Italy, France, Germany, Spain, the UK and the United States · Public Domain Radar")
    descr = T("In Europa conta quando è morto l'autore, negli Stati Uniti quando è uscito il libro. La regola di ogni paese, con le fonti di legge, e chi entra in pubblico dominio.",
              "In Europe the author's death counts, in the United States the year the book came out. Each country's rule, with legal sources, and who enters the public domain.")
    jl = {"@context": "https://schema.org", "@type": "CollectionPage", "@id": url, "url": url, "name": titolo, "description": descr, "inLanguage": lang}
    jsonld = '<script type="application/ld+json">' + json.dumps(jl, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    altra = (f'<a href="/en/public-domain/" hreflang="en">EN</a>' if it else f'<a href="/pubblico-dominio/" hreflang="it">IT</a>')
    out = [apri(lang, titolo, descr, url, alterne(url_indice), jsonld, altra, anno)]
    w = lambda t: f'<span class="w"><span>{t}</span></span>'
    out.append(f'<section class="open">\n<nav class="bc m" aria-label="{T("Sei qui", "You are here")}"><a href="{"/" if it else "/en/"}">Home</a> › <span>{T("Per paese", "By country")}</span></nav>\n'
               f'<p class="m k">{T("Pubblico dominio · per paese", "Public domain · by country")}</p>\n'
               f'<h1 class="h1">{w(T("Ogni paese", "Each country"))}<br>{w(T("ha la sua", "has its own"))}<br>{w(T("regola", "rule"))}</h1>\n'
               f'<p class="say" id="say">{esc(descr)}</p>\n</section>\n')
    porte = []
    for k in ORDINE:
        nome = PAESI[k][0] if it else PAESI[k][1]
        if k == "us":
            n_ = 95; sotto = T(f"anni dalla pubblicazione · nel {anno} i libri del {R.pubblicate_libere_usa_nel(anno)}", f"years from publication · in {anno} the {R.pubblicate_libere_usa_nel(anno)} books")
        else:
            m = R.morti_liberi_nel(anno, "es" if k == "es" else "it")
            n_ = R.anni_protezione(m, "es" if k == "es" else "it")
            sotto = T(f"anni dopo la morte · nel {anno} i morti nel {m}", f"years after death · in {anno} those who died in {m}")
        porte.append(f'<a class="porta" href="{url_paese(k, lang).replace(P.SITO, "")}"><span class="big">{n_}</span><h3>{esc(nome)}</h3><p>{esc(sotto)}</p><span class="go">{T("Apri →", "Open →")}</span></a>')
    out.append(sezione(T("Sei paesi", "Six countries"), T("Regole lette sui testi di legge", "Rules read from the legal texts"), f'<div class="porte">{"".join(porte)}</div>\n'))
    out.append('<div class="pf" id="pf" aria-hidden="true"></div>\n')
    out.append(P.JS_ANNO.replace("@@LOC@@", "it-IT" if it else "en-GB"))
    out.append(P.piede_scheda(lang))
    return "".join(out), url


def url_come(lang):
    return f"{P.SITO}/come-funziona/" if lang == "it" else f"{P.SITO}/en/how-it-works/"


def pagina_come(lang):
    """«Come funziona»: da dove vengono i dati, come si calcolano le date, quanto siamo sicuri, quando si aggiorna.
    Solo cose già scritte in docs/criteri.md e docs/giri-automatici.md (un posto solo: se cambiano lì, cambiano qui)."""
    it = lang == "it"
    T = (lambda a, b: a) if it else (lambda a, b: b)
    anno = P.ANNO_PROSSIMO
    url = url_come(lang)
    titolo = T("Come funziona Public Domain Radar: fonti, regole e verifiche", "How Public Domain Radar works: sources, rules and checks")
    descr = T("Da dove vengono i dati di Public Domain Radar, come si calcola quando un libro diventa libero, quanto sono sicure le date e quando si aggiornano.",
              "Where Public Domain Radar's data comes from, how we work out when a book becomes free, how certain the dates are and when they are updated.")
    faq = [(T("È consulenza legale?", "Is this legal advice?"),
            T("No. Sono informazioni generali costruite da dati aperti e possono contenere errori. Prima di pubblicare controlla la legge e i fatti per il tuo paese e la tua edizione.",
              "No. It is general information built from open data, and it may contain errors. Before publishing, check the law and the facts for your country and your edition.")),
           (T("Ho trovato un errore: cosa faccio?", "I found an error: what do I do?"),
            T("Segnalalo su GitHub: il codice e i dati del sito sono pubblici, e ogni correzione resta scritta.",
              "Report it on GitHub: the site's code and data are public, and every correction stays on record.")),
           (T("Chi c'è dietro?", "Who is behind it?"),
            T("È un progetto di Marco Novali. I contatti sono in fondo a ogni pagina.", "It is a project by Marco Novali. Contact details are at the bottom of every page."))]
    jl = {"@context": "https://schema.org", "@graph": [
        {"@type": "AboutPage", "@id": url, "url": url, "name": titolo, "description": descr, "inLanguage": lang},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}} for q, r in faq]}]}
    jsonld = '<script type="application/ld+json">' + json.dumps(jl, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    altra = ('<a href="/en/how-it-works/" hreflang="en">EN</a>' if it else '<a href="/come-funziona/" hreflang="it">IT</a>')
    out = [apri(lang, titolo, descr, url, alterne(url_come), jsonld, altra, anno)]
    w = lambda t: f'<span class="w"><span>{t}</span></span>'
    out.append(f'<section class="open">\n<nav class="bc m" aria-label="{T("Sei qui", "You are here")}"><a href="{"/" if it else "/en/"}">Home</a> › <span>{T("Come funziona", "How it works")}</span></nav>\n'
               f'<p class="m k">{T("Il metodo", "The method")}</p>\n'
               f'<h1 class="h1">{w(T("Come", "How"))}<br>{w(T("funziona", "it works"))}</h1>\n'
               f'<p class="say" id="say">{esc(T("Ogni data del sito si calcola da fatti controllati (quando è morto l’autore, quando è uscito il libro) e dalle regole di legge di ogni paese. Ecco da dove vengono i fatti, come li controlliamo e cosa resta da verificare.", "Every date on the site is worked out from checked facts (when the author died, when the book came out) and from each country’s legal rules. Here is where the facts come from, how we check them and what is still to be verified."))}</p>\n</section>\n')
    # elenco completo delle fonti, come nei piedi delle pagine (pagine.py, radar, storico/pagina.html): Marco, 25/11/2026
    fonti = [{"t": {"it": "Autori, date di nascita e di morte, opere, anni di uscita, cittadinanze. Dati liberi (CC0).", "en": "Authors, dates of birth and death, works, publication years, citizenships. Free data (CC0)."}, "f": "Wikidata", "u": "https://www.wikidata.org/"},
             {"t": {"it": "Le visite in 5 lingue, che decidono l'ordine degli elenchi. I testi citati hanno il link alla pagina d'origine (CC BY-SA).", "en": "Page views in 5 languages, which set the order of the lists. Quoted texts link to their source page (CC BY-SA)."}, "f": "Wikipedia", "u": "https://www.wikipedia.org/"},
             {"t": {"it": "Gli anni di morte confermati e le edizioni di ogni autore: SBN (Italia), BnF (Francia), BNE (Spagna), British Library (Regno Unito), Library of Congress (USA), Biblioteca nazionale tedesca (GND). Per gli anni di uscita dei libri americani anche il catalogo collettivo tedesco K10plus.", "en": "Confirmed years of death and each author's editions: SBN (Italy), BnF (France), BNE (Spain), British Library (UK), Library of Congress (USA), German National Library (GND). For the publication years of American books, also the German union catalogue K10plus."}, "f": T("Cataloghi delle biblioteche nazionali", "National library catalogues"), "intero": True},
             {"t": {"it": "Il registro ufficiale del Copyright Office americano, nella trascrizione della New York Public Library (CC0): una sua scheda basta da sola per verificare la prima uscita di un libro.", "en": "The official register of the US Copyright Office, as transcribed by the New York Public Library (CC0): one of its records is enough on its own to verify a book's first publication."}, "f": "Catalog of Copyright Entries"},
             {"t": {"it": "Gli elenchi del Public Domain Day: seconda fonte per gli anni di uscita dei libri americani (CC BY 4.0).", "en": "The Public Domain Day lists: a second source for the publication years of American books (CC BY 4.0)."}, "f": "Duke University", "u": "https://web.law.duke.edu/cspd/publicdomainday/"},
             {"t": {"it": "Le edizioni e gli anni di uscita, per controllare i libri americani.", "en": "Editions and publication years, to check American books."}, "f": "Open Library", "u": "https://openlibrary.org/"},
             {"t": {"it": "I download dei libri già liberi: dicono quanto un autore è letto oggi.", "en": "Downloads of books already free: they show how much an author is read today."}, "f": "Project Gutenberg", "u": "https://www.gutenberg.org/"},
             {"t": {"it": "I ritratti degli autori, ciascuno con la sua licenza.", "en": "The authors' portraits, each with its own licence."}, "f": "Wikimedia Commons", "u": "https://commons.wikimedia.org/"},
             {"t": {"it": "Le regole di durata: ogni norma è letta sul testo ufficiale del suo paese, con il link.", "en": "The term rules: each law is read in its country's official text, with a link."}, "f": T("Testi di legge", "Legal texts"), "u": url_indice(lang).replace(P.SITO, "")}]
    out.append(sezione(T("Da dove vengono i dati", "Where the data comes from"), T("Solo fonti aperte o ufficiali", "Open or official sources only"), lista_regole(fonti, lang, T("Apri →", "Open →"))))
    tre = [(T("Europa: la morte dell'autore", "Europe: the author's death"),
            T("In Italia, Francia, Germania e Regno Unito un'opera è libera 70 anni dopo la morte dell'autore, dal 1° gennaio dell'anno dopo. In Spagna, per chi è morto prima del 1987, gli anni sono 80.",
              "In Italy, France, Germany and the UK a work is free 70 years after the author's death, from 1 January of the following year. In Spain, for authors who died before 1987, it is 80 years.")),
           (T("Stati Uniti: l'uscita del libro", "United States: the book's release"),
            T("Conta l'anno della prima pubblicazione: 95 anni dopo. Per questo controlliamo opera per opera se un libro, o una sua parte, era già uscito prima, per esempio a puntate su una rivista.",
              "The year of first publication counts: 95 years later. That is why we check work by work whether a book, or part of it, came out earlier, for example as a magazine serial.")),
           (T("Le regole in un posto solo", "The rules in one place"),
            T("Le regole di legge sono scritte una volta sola nel codice, con la fonte di ogni norma. Tutte le pagine le leggono da lì, e a ogni aggiornamento una serie di prove ricontrolla che nessuna pagina dica cose diverse.",
              "The legal rules are written once in the code, with the source of each law. Every page reads them from there, and at each update a set of tests checks that no page says anything different."))]
    out.append(sezione(T("Come calcoliamo le date", "How we work out the dates"), f'<a href="{url_indice(lang).replace(P.SITO, "")}">{T("Le regole paese per paese", "The rules country by country")}</a>',
                       '<div class="three">\n' + "".join(f'<div><span class="m">{i + 1:02d}</span><h3>{esc(t)}</h3><p>{esc(x)}</p></div>\n' for i, (t, x) in enumerate(tre)) + "</div>\n"))
    sic = [(T("Anni di morte", "Years of death"),
            T("Quando Wikidata e due fonti autorevoli non concordano, vale l'anno delle due fonti. Quando le fonti si contraddicono, l'autore resta in lista con l'avviso «da verificare».",
              "When Wikidata and two authoritative sources disagree, the two sources win. When the sources contradict each other, the author stays on the list marked «to be checked».")),
           (T("Libri americani", "American books"),
            T("«Verificato» vuol dire prima uscita documentata da due fonti indipendenti o da una scheda del Catalog of Copyright Entries. «Edizione confermata»: una fonte conferma l'anno dell'edizione. «Da confermare»: c'è solo Wikidata.",
              "«Verified» means first publication documented by two independent sources or by a Catalog of Copyright Entries record. «Edition confirmed»: a source confirms the edition year. «To be confirmed»: only Wikidata so far.")),
           (T("Nelle classifiche dei libri americani solo «Verificato»", "Only «Verified» in the American book rankings"),
            T("I libri americani in classifica sono solo quelli con la prima uscita verificata. Gli altri restano negli elenchi completi del radar, con il loro stato.",
              "The American books in the rankings are only those with a verified first publication. The others stay in the radar's full lists, with their status."))]
    out.append(sezione(T("Quanto siamo sicuri", "How certain we are"), T("Certo e da verificare", "Certain and to be checked"),
                       '<div class="three">\n' + "".join(f'<div><span class="m">{i + 1:02d}</span><h3>{esc(t)}</h3><p>{esc(x)}</p></div>\n' for i, (t, x) in enumerate(sic)) + "</div>\n"))
    agg = [{"t": {"it": "L'ordine degli elenchi, con le visite su Wikipedia del mese appena finito.", "en": "The order of the lists, with last month's Wikipedia page views."}, "f": T("Il 1° di ogni mese", "On the 1st of every month")},
           {"t": {"it": "Le liste degli autori e delle opere, con le novità di Wikidata e delle biblioteche.", "en": "The lists of authors and works, with what is new on Wikidata and in the libraries."}, "f": T("Aprile, luglio e ottobre", "April, July and October"), "intero": True},
           {"t": {"it": "Cambia chi è libero: le pagine passano all'anno nuovo e parte il conto alla rovescia per quello dopo.", "en": "Who is free changes: the pages move to the new year and the countdown to the next one starts."}, "f": T("Il 1° gennaio", "On 1 January")}]
    out.append(sezione(T("Quando si aggiorna", "When it is updated"), T("In automatico", "Automatically"), lista_regole(agg, lang)))
    out.append(sezione(T("Le risposte brevi", "The short answers"), T("Domande", "Questions"),
                       "<div>\n" + "".join(f'<div class="acc"><button type="button">{esc(q)}<span>[+]</span></button><div class="bd"><p>{esc(r)}</p></div></div>\n' for q, r in faq) + "</div>\n"))
    out.append('<div class="pf" id="pf" aria-hidden="true"></div>\n')
    out.append(P.JS_ANNO.replace("@@LOC@@", "it-IT" if it else "en-GB"))
    out.append(P.piede_scheda(lang))
    return "".join(out), url


# Shop (mockup approvato da Marco, fatto in un'altra chat il 25/11/2026): i poster sono su Etsy, stampati da Gelato.
# I link restano nel formato publicdomainradar.etsy.com, quello che conta per Share & Save; in inglese senza «/it/».
POSTER = [
    ("alice", "4624523730/alice-was-beginning-to-get-very-tired", "Alice was beginning to get very tired",
     "Alice's Adventures in Wonderland", "Lewis Carroll", 1865),
    ("tale-of-two-cities", "4624515025/it-was-the-best-of-times-a-tale-of-two", "It was the best of times",
     "A Tale of Two Cities", "Charles Dickens", 1859),
]
ETSY = "https://publicdomainradar.etsy.com"
CSS_SHOP = (".shop-hd{display:grid;grid-template-columns:minmax(0,1fr) min(32vw,440px);gap:6vw;align-items:end}"
            ".shop-hd .say{margin:0;max-width:440px}"
            ".facts{margin:22px 0 0;padding:0;list-style:none;border-top:1px solid var(--ink)}"
            ".facts li{display:flex;justify-content:space-between;gap:16px;padding:11px 0;border-bottom:1px solid var(--hair)}.facts .g{color:var(--grey)}"
            ".shopgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,340px),1fr));gap:56px 40px;margin-top:40px;max-width:1000px}"
            ".item{display:flex;flex-direction:column}"
            ".wall{position:relative;background:var(--box,#E4E2DA);aspect-ratio:4/5;display:flex;align-items:center;justify-content:center;overflow:hidden;text-decoration:none}"
            ".wall img{width:62%;height:auto;display:block;box-shadow:0 1px 2px rgba(12,12,16,.18),0 18px 40px -14px rgba(12,12,16,.45);transition:transform 700ms var(--out),box-shadow 700ms var(--out)}"
            ".wall:hover img{transform:translateY(-6px) scale(1.015)}"
            ".info{display:grid;grid-template-columns:1fr auto;gap:4px 16px;margin-top:18px;align-items:baseline}"
            ".info h3{font-family:var(--disp);font-weight:800;text-transform:uppercase;font-size:clamp(24px,1.9vw,30px);line-height:.95;margin:0}"
            ".info .price{font-family:var(--disp);font-weight:800;font-size:clamp(26px,2.3vw,34px);line-height:.95}"
            ".info .who{grid-column:1/-1;margin:4px 0 0;font-size:15px;color:var(--grey)}.info .who em{color:var(--ink)}"
            ".buy{margin-top:18px;display:flex;justify-content:space-between;align-items:center;padding:15px 18px;background:var(--ink);color:var(--paper);text-decoration:none;font-family:var(--mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;position:relative;overflow:hidden}"
            ".buy::before{content:'';position:absolute;inset:0;background:var(--red);transform:translateY(101%);transition:transform 480ms var(--cut)}"
            ".buy span{position:relative}.buy:hover::before{transform:none}"
            ".how{display:grid;grid-template-columns:repeat(3,1fr);gap:40px}"
            ".how .n{font-family:var(--disp);font-weight:800;font-size:56px;line-height:.9;color:var(--red)}"
            ".how p{margin:10px 0 0;font-size:16px;line-height:1.5;max-width:360px}"
            "@media (max-width:900px){.shop-hd{grid-template-columns:1fr;gap:26px}.how{grid-template-columns:1fr;gap:28px}}"
            "@media (prefers-reduced-motion:reduce){.wall img,.buy::before{transition:none}}")


def url_shop(lang):
    return f"{P.SITO}/shop/" if lang == "it" else f"{P.SITO}/en/shop/"


def pagina_shop(lang):
    it = lang == "it"
    T = (lambda a, b: a) if it else (lambda a, b: b)
    url = url_shop(lang)
    titolo = T("Shop: poster tipografici dai libri in pubblico dominio · Public Domain Radar",
               "Shop: typographic posters from public domain books · Public Domain Radar")
    descr = T("Poster tipografici con le prime righe e le frasi famose dei libri in pubblico dominio. Stampati su richiesta, si comprano sul negozio Etsy di Public Domain Radar.",
              "Typographic posters with the opening lines and famous phrases of public domain books. Printed on demand, sold on Public Domain Radar's Etsy shop.")
    lk = lambda c: f"{ETSY}/{'it/' if it else ''}listing/{c}"
    jl = {"@context": "https://schema.org", "@type": "CollectionPage", "@id": url, "url": url, "name": titolo, "description": descr, "inLanguage": lang}
    jsonld = '<script type="application/ld+json">' + json.dumps(jl, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    altra = ('<a href="/en/shop/" hreflang="en">EN</a>' if it else '<a href="/shop/" hreflang="it">IT</a>')
    out = [apri(lang, titolo, descr, url, alterne(url_shop), jsonld, altra, P.ANNO_PROSSIMO, CSS_SHOP)]
    w = lambda t: f'<span class="w"><span>{t}</span></span>'
    out.append(f'<section class="open">\n<nav class="bc m" aria-label="{T("Sei qui", "You are here")}"><a href="{"/" if it else "/en/"}">Home</a> › <span>Shop</span></nav>\n'
               f'<p class="m k">{T("Stampa su richiesta", "Printed on demand")}</p>\n'
               f'<div class="shop-hd"><h1 class="h1">{w("Shop")}</h1><div>'
               f'<p class="say">{esc(T("Poster tipografici con le prime righe e le frasi famose dei libri in pubblico dominio.", "Typographic posters with the opening lines and famous phrases of public domain books."))}</p>'
               f'<ul class="facts m"><li><span>{T("Stampa", "Printing")}</span><span class="g">{T("su richiesta, con Gelato", "on demand, by Gelato")}</span></li>'
               f'<li><span>{T("Acquisto", "Purchase")}</span><span class="g">{T("sul nostro negozio Etsy", "on our Etsy shop")}</span></li>'
               f'<li><span>Poster</span><span class="g">50 × 70 cm</span></li></ul></div></div>\n</section>\n')
    card = []
    for img, cod, frase, opera, autore, anno in POSTER:
        alt = T(f"Poster tipografico: «{frase}…», da {opera} di {autore}", f"Typographic poster: “{frase}…”, from {opera} by {autore}")
        card.append(f'<article class="item"><a class="wall" href="{lk(cod)}" rel="noopener" target="_blank">'
                    f'<img src="/shop/img/{img}.webp" width="900" height="1260" loading="lazy" alt="{esc(alt)}"></a>'
                    f'<div class="info"><h3>{esc(frase)}</h3><span class="price">35 €</span>'
                    f'<p class="who"><em>{esc(opera)}</em> · {esc(autore)} · {anno}</p></div>'
                    f'<a class="buy" href="{lk(cod)}" rel="noopener" target="_blank"><span>{T("Acquista su Etsy", "Buy on Etsy")}</span><span>→</span></a></article>\n')
    out.append(sezione(T("I poster", "The posters"), f'<a href="{ETSY}" rel="noopener" target="_blank">{T("Tutto il negozio su Etsy ↗", "The whole shop on Etsy ↗")}</a>',
                       f'<div class="shopgrid">\n{"".join(card)}</div>\n'))
    passi = [(T("Scegli", "Choose"), T("Ogni poster parte da un libro in pubblico dominio: le prime righe e le frasi più famose, composte solo con la tipografia.",
                                     "Every poster starts from a public domain book: the opening lines and most famous phrases, set in type alone.")),
             (T("Acquista su Etsy", "Buy on Etsy"), T("Il pagamento e l'assistenza passano dal nostro negozio Etsy. Prezzo e spedizione definitivi li vedi lì.",
                                                     "Payment and support go through our Etsy shop. You see the final price and shipping there.")),
             (T("Stampato vicino a te", "Printed near you"), T("Gelato stampa e spedisce solo quando ordini, dal centro di produzione più vicino.",
                                                              "Gelato prints and ships only when you order, from the nearest production centre."))]
    out.append(sezione(T("Come si compra", "How to buy"), T("Tre passaggi", "Three steps"),
                       '<div class="how">' + "".join(f'<div><div class="n">{i + 1:02d}</div><p class="m">{esc(t)}</p><p>{esc(x)}</p></div>' for i, (t, x) in enumerate(passi)) + "</div>\n"))
    out.append('<div class="pf" id="pf" aria-hidden="true"></div>\n')
    out.append(P.JS_ANNO.replace("@@LOC@@", "it-IT" if it else "en-GB"))
    out.append(P.piede_scheda(lang))
    return "".join(out), url


def crea_pagine_paese():
    """Scrive le pagine e restituisce gli indirizzi (per la sitemap)."""
    REG = regole_radar()
    anno = P.ANNO_PROSSIMO
    liste = {}
    for a in (anno, anno + 1):
        liste[("ue", a)] = P.leggi_lista(RADICE / "data" / f"{a}.json")
        fes = RADICE / "data" / f"es-{a}.json"
        liste[("es", a)] = P.leggi_lista(fes) if fes.exists() else {"autori": []}
        fus = RADICE / "data" / f"us-{a}.json"
        liste[("us", a)] = json.load(open(fus, encoding="utf-8")) if fus.exists() else {"opere": []}
    urls = []
    for lang in ("it", "en"):
        pagine = [pagina_indice(lang, liste)] + [pagina_paese_ue(k, lang, REG, liste) for k in ORDINE if k != "us"] + [pagina_usa(lang, liste), pagina_come(lang), pagina_shop(lang)]
        for html_, url in pagine:
            d = RADICE / url.replace(P.SITO + "/", "")
            d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text(html_, encoding="utf-8")
            urls.append(url)
    return urls


if __name__ == "__main__":
    print("\n".join(crea_pagine_paese()))
