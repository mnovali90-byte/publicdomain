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

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE / "scripts"))
from marchio import marchio_html, CSS_MARCHIO  # noqa: E402

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
                      o.get("visite_sett", 0), o.get("generi") or [], lk, o.get("pagine", 0), 1 if escl else 0])

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
    for anno in (2027, 2028, 2029):
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

    rit = leggi(S / "ritratti.json", {}) or {}
    foto = {q: {"u": r["url"], "p": r["pagina"], "l": r.get("licenza", ""), "a": r.get("autore", "")}
            for q, r in rit.items() if r and r.get("url") and q in idx}

    pagina = {"aggiornato": O["aggiornato"], "settimana": O["settimana"], "n_opere": len(tutte), "n_autori": len(n_aut),
              "autori": autori, "opere": opere, "lingue": lingue, "foto": foto, "prossimi": prossimi}
    (S / "pagina.json").write_text(json.dumps(pagina, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return pagina


def simboli():
    s = (RADICE / "index.html").read_text(encoding="utf-8")
    m = re.search(r"^const SIMBOLI = (\{.*\});$", s, re.M)
    return m.group(1)


def nav(lang):
    ind = leggi(RADICE / "data" / "indice.json", {"anni": [2027, 2028]})
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
    t = (RADICE / "storico" / "pagina.html").read_text(encoding="utf-8")
    sim = simboli()
    testi = {
        "it": {"TITLE": "Già pubblici: le opere già in pubblico dominio, paese per paese · Public Domain Radar",
               "DESC": "Cerca un titolo o un autore e scopri se è già in pubblico dominio in Italia, Francia, Germania, Spagna e USA, e da quando. Scaffali dei classici più letti, già liberi. Dati aperti da Wikidata.",
               "CANON": "https://publicdomainradar.com/gia-pubblici/", "HOME": "/", "NAV_ARIA": "Navigazione", "out": RADICE / "gia-pubblici" / "index.html"},
        "en": {"TITLE": "Already public: works already in the public domain, country by country · Public Domain Radar",
               "DESC": "Search a title or an author and find out whether it is already in the public domain in Italy, France, Germany, Spain and the USA, and since when. Shelves of the most read classics, already free. Open data from Wikidata.",
               "CANON": "https://publicdomainradar.com/en/already-public/", "HOME": "/en/", "NAV_ARIA": "Navigation", "out": RADICE / "en" / "already-public" / "index.html"},
    }
    for lang, x in testi.items():
        s = t.replace("__LANG__", lang).replace("__SIMBOLI__", sim).replace("__MARCHIO__", marchio_html(150)).replace("__CSS_MARCHIO__", CSS_MARCHIO)
        s = s.replace("__NAV__", nav(lang))
        for k in ("TITLE", "DESC", "CANON", "HOME", "NAV_ARIA"):
            s = s.replace(f"__{k}__", x[k])
        assert "__" not in re.sub(r"__(proto|dirname)__", "", s).split("<script>")[0], "segnaposto rimasto"
        x["out"].parent.mkdir(parents=True, exist_ok=True)
        x["out"].write_text(s, encoding="utf-8")


if __name__ == "__main__":
    p = dati()
    pagine()
    print(f"pagina: {len(p['opere'])} opere negli scaffali, {p['n_opere']} nella ricerca, {p['n_autori']} autori, "
          f"{len(p['foto'])} ritratti, {len(p['prossimi'])} autori in arrivo")
