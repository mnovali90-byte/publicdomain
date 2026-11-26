"""Pagina «Già pubblici» (/gia-pubblici/ e /en/already-public/): prepara i dati per la pagina e scrive le due pagine.

Non usa la rete: legge quello che storico.py ha già scaricato.
  data/storico/pagina.json      le opere più note (scaffali e classifiche), gli autori, le lingue, i ritratti, gli autori
                                in arrivo (per dire «non è ancora libero, diventa libero il ...»)
  data/storico/per_autore/NN.json  tutte le opere di ogni autore, divise in 100 file per codice Wikidata
                                (la pagina scarica solo il file dell'autore cercato)
  gia-pubblici/index.html, en/already-public/index.html   dalla stessa traccia storico/pagina.html

Le regole per paese stanno nella pagina (funzione stato), così ricerca e scaffali usano la stessa regola.
I ritratti arrivano da data/storico/ritratti.json, scritto da storico/ritratti.py (quello sì usa la rete).
"""
import json, os, re, sys
from pathlib import Path
from datetime import date

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE / "scripts"))
from marchio import marchio_html, CSS_MARCHIO  # noqa: E402
import regole as R  # noqa: E402  (calendario del sito: fase_sito)

S = RADICE / "data" / "storico"


def leggi(p, predefinito=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return predefinito


def dati():
    O = leggi(S / "opere.json")
    esc = leggi(RADICE / "data" / "storico_esclusioni.json", {})
    no_o, no_a = set(esc.get("qid", {})), set(esc.get("autori_qid", {}))
    autori, idx = [], {}
    lingue = {}
    opere = []
    for o in O["opere"]:
        ii = []
        for a in o["autori"]:
            if a["qid"] not in idx:
                idx[a["qid"]] = len(autori)
                autori.append([a["qid"], a["nome"], a.get("morte"), 1 if a.get("antico") else 0, a.get("morte_incerta", 0) or 0, a.get("alleato", 0) or 0])
            ii.append(idx[a["qid"]])
        lk = None
        if o.get("lingua"):
            lk = o["lingua"]["en"]
            it = o["lingua"].get("it") or lk
            lingue.setdefault(lk, {}).setdefault(it, 0)
            lingue[lk][it] += 1
        escl = o["qid"] in no_o or any(a["qid"] in no_a for a in o["autori"])
        opere.append([o["qid"], o["titolo"], o.get("titolo_it") or "", o.get("anno"), o.get("anno_duke") or 0, ii,
                      o.get("visite_sett", 0), o.get("generi") or [], lk, o.get("pagine", 0), 1 if escl else 0,
                      [o.get("visite_" + l) for l in ("it", "en", "fr", "de", "es")]])   # visite per lingua (None = non misurata)

    # per ogni lingua il nome italiano più frequente («inglese», non «inglese britannico»)
    lingue = {k: [k, max(v, key=v.get)[:1].upper() + max(v, key=v.get)[1:]] for k, v in lingue.items()}

    # tutte le opere della ricerca: per contare e per i file per autore
    tutte, n_aut = {}, set()
    for f in sorted((S / "ricerca").glob("*.json")):
        d = leggi(f, {})
        for r in d.get("opere", []):
            tutte.setdefault(r[0], r)
        for r in d.get("autori", []):
            n_aut.add(r[0])
    per = {}
    for r in tutte.values():
        for a in r[5]:
            per.setdefault(a[0], []).append(r)
    cart = S / "per_autore"
    cart.mkdir(exist_ok=True)
    for f in cart.glob("*.json"):
        f.unlink()
    file = {}
    for q, rr in per.items():
        try:
            k = f"{int(q[1:]) % 100:02d}"
        except ValueError:
            continue
        rr.sort(key=lambda r: -(r[4] or 0))
        file.setdefault(k, {})[q] = rr
    for k, d in file.items():
        (cart / f"{k}.json").write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # autori che non sono ancora liberi ma hanno la scheda nel radar
    prossimi, visti = [], set()
    # dall'anno in vetrina (scripts/regole.py, fase_sito): nella settimana della festa restano anche gli appena liberati,
    # finché lo Storico (il 2 del mese) non porta le loro opere nell'elenco
    for anno in range(R.fase_sito(date.today())[1], date.today().year + 4):
        d = leggi(RADICE / "data" / f"{anno}.json")
        if not d:
            continue
        for a in d.get("autori", []):
            if not a.get("pagina") or a["wikidata"] in visti:
                continue
            m = re.match(r"-?\d+", a.get("morte") or "")
            if not m:
                continue
            visti.add(a["wikidata"])
            prossimi.append({"w": a["wikidata"], "n": a["nome"], "m": int(m.group()), "p": a["pagina"], "pe": a.get("pagina_en")})

    # scaffali per lingua (storico/scaffali_lingua.py): opere dall'archivio intero, ordinate per visite nella lingua
    scaffali, extra = {}, []
    SL = leggi(S / "scaffali_lingua.json", {}) or {}
    gia = {o[0] for o in opere}
    for l, x in (SL.get("lingue") or {}).items():
        ids = []
        for q, v in x.get("opere", []):
            r = tutte.get(q)
            if not r:
                continue
            if q not in gia:
                ii = []
                for a in r[5]:
                    if a[0] not in idx:
                        idx[a[0]] = len(autori)
                        autori.append([a[0], a[1], a[2], a[3] if len(a) > 3 else 0, a[4] if len(a) > 4 else 0, a[5] if len(a) > 5 else 0])
                    ii.append(idx[a[0]])
                # 25/11/2026: v qui è la visita MENSILE sulla Wikipedia della lingua originale (scaffali_lingua.py), non le visite
                # settimanali nelle 5 lingue delle altre opere. Prima veniva copiata in tutte e 5 le lingue e queste opere salivano
                # nelle classifiche (Faust I: 206.578 «in ogni lingua»). Ora: niente visite misurate per le classifiche; lo
                # scaffale della loro lingua le ordina comunque con il suo numero (campo «o» qui sotto).
                extra.append([q, r[1], r[2] or "", r[3], 0, ii, 0, [], None, r[4] or 0, 1 if r[6] else 0, [None] * 5])
                gia.add(q)
            ids.append([q, v])
        scaffali[l] = {"n": [x.get("nome_it"), x.get("nome_en")], "c": x.get("candidati", 0), "w": x.get("wiki"), "o": ids}
    opere += extra

    rit = leggi(S / "ritratti.json", {}) or {}
    foto = {q: {"u": r["url"], "p": r["pagina"], "l": r.get("licenza", ""), "a": r.get("autore", "")}
            for q, r in rit.items() if r and r.get("url") and q in idx}

    pagina = {"aggiornato": O["aggiornato"], "settimana": O["settimana"], "n_opere": len(tutte), "n_autori": len(n_aut),
              "autori": autori, "opere": opere, "lingue": lingue, "foto": foto, "prossimi": prossimi,
              "scaffali_lingua": scaffali, "n_principali": len(opere) - len(extra)}
    (S / "pagina.json").write_text(json.dumps(pagina, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return pagina


def simboli():
    s = (RADICE / "radar" / "index.html").read_text(encoding="utf-8")
    m = re.search(r"^const SIMBOLI = (\{.*\});$", s, re.M)
    return m.group(1)


def nav(lang):
    ind = leggi(RADICE / "data" / "indice.json", {"anni": [date.today().year + 1, date.today().year + 2]})
    try:
        cal = max(leggi(RADICE / "data" / "calendari_approvati.json")["anni"])
    except Exception:
        cal = ind["anni"][0]
    pre = "/en" if lang == "en" else ""
    voci = [f'<a href="{pre}/#/{a}">{a}</a>' for a in ind["anni"]]
    voci.append(f'<a class="forte" href="{pre}/calendar/{cal}/">Calendar</a>' if lang == "en" else f'<a class="forte" href="/calendario/{cal}/">Calendario</a>')
    voci.append('<a class="on" href="/en/already-public/" aria-current="page">Already public</a>' if lang == "en"
                else '<a class="on" href="/gia-pubblici/" aria-current="page">Già pubblici</a>')
    it_on, en_on = ('class="on" ', '') if lang == "it" else ('', 'class="on" ')
    voci.append(f'<span class="lingue"><a {it_on}href="/gia-pubblici/" hreflang="it" lang="it">IT</a><a {en_on}href="/en/already-public/" hreflang="en" lang="en">EN</a></span>')
    return "".join(voci)


def pagine():
    from pagine import testa_scheda, piede_scheda   # grafica comune del sito (scripts/pagine.py)
    t = (RADICE / "storico" / "pagina.html").read_text(encoding="utf-8")
    css = (RADICE / "storico" / "stile_gia.css").read_text(encoding="utf-8")
    sim = simboli()
    testi = {
        "it": {"TITLE": "Già pubblici: le opere già in pubblico dominio, paese per paese · Public Domain Radar",
               "DESC": "Cerca un titolo o un autore e scopri se è già in pubblico dominio in Italia, Francia, Germania, Spagna e USA, e da quando. Scaffali dei classici più visitati su Wikipedia, già liberi. Dati aperti da Wikidata.",
               "CANON": "https://publicdomainradar.com/gia-pubblici/", "ALTRA": ("/en/already-public/", "en", "EN"),
               "OCC": "Storico del pubblico dominio", "H1": "È già libero?", "CERCA": "Cerca un titolo o un autore", "CANC": "Cancella", "CHIUDI": "Chiudi",
               "LEAD": "Scrivi un titolo o un autore. Ti diciamo se si può già pubblicare e da quando, paese per paese.",
               "PROVA": ("Prova:", ["Kafka", "Orwell", "Il grande Gatsby", "Brecht", "Frankenstein"]),
               "out": RADICE / "gia-pubblici" / "index.html"},
        "en": {"TITLE": "Already public: works already in the public domain, country by country · Public Domain Radar",
               "DESC": "Search a title or an author and find out whether it is already in the public domain in Italy, France, Germany, Spain and the USA, and since when. Shelves of the classics most visited on Wikipedia, already free. Open data from Wikidata.",
               "CANON": "https://publicdomainradar.com/en/already-public/", "ALTRA": ("/gia-pubblici/", "it", "IT"),
               "OCC": "Public domain archive", "H1": "Is it free yet?", "CERCA": "Search a title or an author", "CANC": "Clear", "CHIUDI": "Close",
               "LEAD": "Type a title or an author. We tell you whether it can already be published, and since when, country by country.",
               "PROVA": ("Try:", ["Kafka", "Orwell", "The Great Gatsby", "Brecht", "Frankenstein"]),
               "out": RADICE / "en" / "already-public" / "index.html"},
    }
    alterne = ('<link rel="alternate" hreflang="it" href="https://publicdomainradar.com/gia-pubblici/">\n'
               '<link rel="alternate" hreflang="en" href="https://publicdomainradar.com/en/already-public/">\n'
               '<link rel="alternate" hreflang="x-default" href="https://publicdomainradar.com/gia-pubblici/">\n')
    # 26/11/2026: lingue in più (scripts/lingue.py). Testi dal catalogo testi/<lingua>.json, con l'inglese come chiave.
    import lingue as L
    case = {"it": "/gia-pubblici/", "en": "/en/already-public/", **{l: f"/{L.CARTELLA[l]['gia']}/" for l in L.NUOVE}}
    if L.NUOVE:
        alterne = L.hreflang(case, "https://publicdomainradar.com")
    for l in L.NUOVE:
        tt = lambda it_, en_: L.testo(l, it_, en_)
        I, E_ = testi["it"], testi["en"]
        testi[l] = {k: tt(I[k], E_[k]) for k in ("TITLE", "DESC", "OCC", "H1", "CERCA", "CANC", "CHIUDI", "LEAD")}
        testi[l].update({"CANON": "https://publicdomainradar.com" + case[l], "PROVA": (tt(I["PROVA"][0], E_["PROVA"][0]), ["Kafka", "Orwell", "Gatsby", "Brecht", "Frankenstein"]),
                         "out": RADICE / L.CARTELLA[l]["gia"] / "index.html"})
    T_en = None
    for lang, x in testi.items():
        # piede: regole e fonti, dagli stessi testi della pagina (oggetto T)
        blocco = t[t.index(f"\n{lang if lang in ('it', 'en') else 'en'}: {{"):]
        regole = json.loads('"' + re.search(r'piede2: "((?:[^"\\]|\\.)*)"', blocco).group(1) + '"')
        fonti = json.loads('"' + re.search(r'piede3: "((?:[^"\\]|\\.)*)"', blocco).group(1) + '"')
        fonti = re.sub(r"^(Fonti|Sources): ", "", fonti)
        e = lambda v: v.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        h1 = " ".join(f'<span class="w"><span>{e(w)}</span></span>' for w in [x["H1"]])
        h_, l_, n_ = x.get("ALTRA") or ("", "", "")
        altra = L.selettore(lang, case) if L.NUOVE else f'<a href="{h_}" hreflang="{l_}">{n_}</a>'
        testa = testa_scheda(lang, e(x["TITLE"]), e(x["DESC"]), x["CANON"], alterne, "", altra,
                             L.testo(lang, "Già pubblici", "Already public"), og_tipo="website", css_extra=css, main_cls="gia", body_cls="gia-b")
        testa = testa.replace("@@MARCHIO_S@@", marchio_html(56).replace('<span class="pdr" style="--w:56px">', "").rsplit("</span>", 1)[0])
        prova = e(x["PROVA"][0]) + " " + "".join(f'<button type="button">{e(v)}</button>' for v in x["PROVA"][1])
        corpo = t.replace("__LANG__", lang).replace("__SIMBOLI__", sim)
        for k in ("OCC", "LEAD", "CERCA", "CANC", "CHIUDI"):
            corpo = corpo.replace(f"__{k}__", e(x[k]))
        corpo = corpo.replace("__H1__", h1).replace("__PROVA__", prova)
        if lang not in ("it", "en"):
            fonti, regole = L.testo(lang, "", fonti), L.testo(lang, "", regole)
            # T[lingua]: i testi inglesi della pagina tradotti dal catalogo (le funzioni restano quelle inglesi, l'elenco usa la congiunzione della lingua)
            i0 = t.index("const T = {"); i1 = t.index("\n}};", i0) + 4
            import subprocess
            en = json.loads(subprocess.run(["node", "-e", t[i0:i1] + "\nprocess.stdout.write(JSON.stringify(T.en));"], capture_output=True, text=True, check=True).stdout)
            def albero(v):
                return L.testo(lang, "", v) if isinstance(v, str) and v else [albero(z) for z in v] if isinstance(v, list) else {k: albero(z) for k, z in v.items()} if isinstance(v, dict) else v
            cong = {"de": " und ", "fr": " et ", "es": " y "}[lang]
            mesi = json.dumps(L.MESI.get(lang) or [])
            agg = (f"\nT[{json.dumps(lang)}] = Object.assign({{}}, T.en, {json.dumps(albero(en), ensure_ascii=False)}, "
                   f"{{ elenco: (x) => x.length > 1 ? x.slice(0, -1).join(\", \") + {json.dumps(cong)} + x[x.length - 1] : x.join(\"\"), "
                   f"dateFmt: (a, b) => a.getDate() + \"–\" + b.toLocaleDateString({json.dumps(L.LOCALE[lang])}, {{ day: \"numeric\", month: \"long\", year: \"numeric\" }}) }});")
            j = corpo.index("\n}};", corpo.index("const T = {")) + 4
            corpo = corpo[:j] + agg + corpo[j:]
            trad = {}
            for it_, en_ in re.findall(r'L2\("((?:[^"\\]|\\.)*)", "((?:[^"\\]|\\.)*)"\)', t):
                if en_:
                    trad[en_] = L.testo(lang, it_, en_)
            for g_it, g_en in zip(re.findall(r'(\w+): "([^"]+)"', t[t.index("const GENERI = { it:"):t.index("\n  en:", t.index("const GENERI = { it:"))]),
                                  re.findall(r'(\w+): "([^"]+)"', t[t.index("\n  en:", t.index("const GENERI = { it:")):t.index("}[LING", t.index("const GENERI = { it:"))])):
                trad[g_en[1]] = L.testo(lang, g_it[1], g_en[1])
            c = L.CARTELLA[lang]
            link = {"/en/": f"/{c['home']}/", "/": f"/{c['home']}/"}
            sch = (leggi(RADICE / "data" / f"radar_{lang}.json", {}) or {}).get("schede", {})
            corpo = corpo.replace("<script>", f'<script>window.TRAD_LINGUA = {json.dumps(trad, ensure_ascii=False)}; '
                                  f'window.LINK_LINGUA = Object.assign({json.dumps(link)}, {json.dumps({"/en/author/" + v.rstrip("/").rsplit("/", 1)[1] + "/": v for v in sch.values()})});</script>\n<script>', 1)
            # titoli delle opere nella lingua (Wikidata), letti dalla pagina all'avvio
            et_ = (leggi(RADICE / "data" / "lingue_etichette.json", {}) or {}).get("voci", {})
            tit = {r[0]: et_[r[0]][lang][0] for r in (leggi(S / "pagina.json", {}) or {}).get("opere", []) if (et_.get(r[0]) or {}).get(lang, [None])[0]}
            (S / f"titoli_{lang}.json").write_text(json.dumps(tit, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        piede = piede_scheda(lang, (L.testo(lang, "Fonti e regole", "Sources and rules"), e(fonti) + "</p><p>" + e(regole)))
        s = testa + corpo + piede
        assert "__" not in re.sub(r"__(proto|dirname)__", "", s).split("<script>")[0], "segnaposto rimasto"
        x["out"].parent.mkdir(parents=True, exist_ok=True)
        if lang not in ("it", "en"):
            s = L.localizza_link(s, lang, {v.rstrip("/").rsplit("/", 1)[1] for v in sch.values()}, [R.fase_sito(date.today())[1]])
        x["out"].write_text(s, encoding="utf-8")


if __name__ == "__main__":
    p = dati()
    pagine()
    import lingue as L
    L.sistema_home(RADICE)   # home inglese principale (scripts/lingue.py)
    L.salva_mancanti("-gia")
    L.salva_coppie("-gia")   # testi di Già pubblici senza traduzione: testi/mancanti-<lingua>-gia.json
    print(f"pagina: {len(p['opere'])} opere negli scaffali, {p['n_opere']} nella ricerca, {p['n_autori']} autori, "
          f"{len(p['foto'])} ritratti, {len(p['prossimi'])} autori in arrivo")
