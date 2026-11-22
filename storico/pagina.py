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
                extra.append([q, r[1], r[2] or "", r[3], 0, ii, v, [], None, r[4] or 0, 1 if r[6] else 0, [v] * 5])
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
    for lang, x in testi.items():
        # piede: regole e fonti, dagli stessi testi della pagina (oggetto T)
        blocco = t[t.index(f"\n{lang}: {{"):]
        regole = json.loads('"' + re.search(r'piede2: "((?:[^"\\]|\\.)*)"', blocco).group(1) + '"')
        fonti = json.loads('"' + re.search(r'piede3: "((?:[^"\\]|\\.)*)"', blocco).group(1) + '"')
        fonti = re.sub(r"^(Fonti|Sources): ", "", fonti)
        e = lambda v: v.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        h1 = " ".join(f'<span class="w"><span>{e(w)}</span></span>' for w in [x["H1"]])
        h_, l_, n_ = x["ALTRA"]
        testa = testa_scheda(lang, e(x["TITLE"]), e(x["DESC"]), x["CANON"], alterne, "", f'<a href="{h_}" hreflang="{l_}">{n_}</a>',
                             "Già pubblici" if lang == "it" else "Already public", og_tipo="website", css_extra=css, main_cls="gia", body_cls="gia-b")
        testa = testa.replace("@@MARCHIO_S@@", marchio_html(56).replace('<span class="pdr" style="--w:56px">', "").rsplit("</span>", 1)[0])
        prova = e(x["PROVA"][0]) + " " + "".join(f'<button type="button">{e(v)}</button>' for v in x["PROVA"][1])
        corpo = t.replace("__LANG__", lang).replace("__SIMBOLI__", sim)
        for k in ("OCC", "LEAD", "CERCA", "CANC", "CHIUDI"):
            corpo = corpo.replace(f"__{k}__", e(x[k]))
        corpo = corpo.replace("__H1__", h1).replace("__PROVA__", prova)
        piede = piede_scheda(lang, ("Fonti e regole" if lang == "it" else "Sources and rules", e(fonti) + "</p><p>" + e(regole)))
        s = testa + corpo + piede
        assert "__" not in re.sub(r"__(proto|dirname)__", "", s).split("<script>")[0], "segnaposto rimasto"
        x["out"].parent.mkdir(parents=True, exist_ok=True)
        x["out"].write_text(s, encoding="utf-8")


if __name__ == "__main__":
    p = dati()
    pagine()
    print(f"pagina: {len(p['opere'])} opere negli scaffali, {p['n_opere']} nella ricerca, {p['n_autori']} autori, "
          f"{len(p['foto'])} ritratti, {len(p['prossimi'])} autori in arrivo")
