"""PROVA – OPERE DALLE FONTI (22/11/2026, richiesta di Marco: «Wikidata non è la fonte primaria»). Non cambia il sito.

Domanda: se per le opere principali delle schede prendiamo i dati dai cataloghi delle biblioteche nazionali invece che da
Wikidata, cosa cambia? In particolare:
  1. collaboratori, coautori e illustratori scritti sul frontespizio o nelle schede di catalogo che Wikidata non segna
     (casi noti: Ruth Berlau per «Il cerchio di gesso del Caucaso», E. H. Shepard per «Winnie-the-Pooh»);
  2. l'anno della prima edizione: quanto spesso coincide con l'anno di Wikidata.

Fonti, per ogni opera (titolo originale da Wikidata se c'è, poi titolo inglese e titolo della scheda, più il cognome):
  - Library of Congress (catalogo SRU, MARC): campo 245 $c (dicitura di responsabilità), 100/700 (persone, date, ruolo);
  - K10plus, catalogo collettivo tedesco (SRU, MARC; la DNB blocca le richieste da GitHub): stessi campi;
  - BnF (SRU, UNIMARC) per gli autori francesi: 200 $f/$g, 700/701/702.
Solo le edizioni con lo stesso titolo dell'opera (non le traduzioni con altro titolo). I traduttori, i curatori e gli
autori di prefazioni non contano. Le date delle persone vengono dal catalogo stesso (700 $d, 701 $f).

Campione: gli autori «letterari» della lista del prossimo 1° gennaio più letti, le prime opere di ciascuno, più Brecht e
Milne (casi noti). I gruppi di autori si alternano, così se il tempo finisce il campione resta vario.

Scrive docs/prova-opere/risultati.json e docs/prova-opere/riepilogo.md. Gira con .github/workflows/prova-opere.yml.
"""
import html, json, os, re, sys, time, urllib.parse
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "storico"))
sys.path.insert(0, str(R / "scripts"))
import verifica_anni as va        # noqa: E402  (Library of Congress, titoli originali)
import verifica_anni_usa as vu    # noqa: E402  (scarica, campi, record, stesso_titolo)
import pagine as pg               # noqa: E402  (coautori che il sito usa oggi: Wikidata + coautori manuali)
import regole as RG               # noqa: E402

BUDGET = float(os.environ.get("BUDGET_MINUTI", "55")) * 60
N_AUTORI = int(os.environ.get("N_AUTORI", "60"))
N_OPERE = int(os.environ.get("N_OPERE", "4"))
SEMPRE = ["Q38757", "Q207036"]   # Brecht, Milne: casi noti (Hauptmann, Berlau, Shepard)
USCITA = R / "docs" / "prova-opere"
FR = {"Francia", "Terza Repubblica francese", "Quarta Repubblica francese", "Belgio"}

# ruoli che contano per il diritto d'autore del testo o delle immagini; esclusi traduttori, curatori, prefatori, interpreti
RUOLO = [
    ("illustratore", r"\bill\b|illustr|zeichn|drawings|dessins|decorations|bilder"),
    ("collaboratore", r"\bctb\b|\bclb\b|mitarb|mitwirk|collabor|unter mitarbeit|avec la collaboration|in collaboration|\bco-?author|coauteur|coautore|mitverf"),
    ("autore", r"\baut\b|author|verfasser|auteur|\b070\b"),
    ("musica", r"\bcmp\b|compos|komponist|musik|music|\b230\b"),
]
ESCLUSI = r"\btrl\b|übers|uebers|transl|tradu|\bedt\b|hrsg|herausg|editor|éd\.|\baui\b|vorwort|nachw|introd|préf|pref|\bprf\b|\bnrt\b|\b730\b|\b340\b|\b080\b"


def parole(t):
    return va.parole(t)


def ruolo_di(testo):
    t = (testo or "").lower()
    if re.search(ESCLUSI, t):
        return None
    for nome, rx in RUOLO:
        if re.search(rx, t):
            return nome
    return None


def vita(d):
    """«1906-1974» → (1906, 1974); «1906-» → (1906, None)."""
    a = re.findall(r"(1[5-9]\d\d|20[0-2]\d)", d or "")
    if not a:
        return None, None
    if re.search(r"(1[5-9]\d\d|20[0-2]\d)\s*-\s*$", (d or "").strip(" .,")):
        return int(a[0]), None
    return (int(a[0]), int(a[1])) if len(a) > 1 else (None, int(a[0])) if re.search(r"(d\.|gest|†|mort)", d or "") else (int(a[0]), None)


def dalla_dicitura(testo):
    """Nomi dopo «unter Mitarbeit von», «avec la collaboration de», «illustrated by», «Zeichnungen von»…"""
    out = []
    N = r"([^;:/\[\]()]+)"   # un nome può avere i punti delle iniziali (E. H. Shepard)
    for rx, ruolo in ((r"(?:unter )?mitarbeit (?:von|v\.)\s+" + N, "collaboratore"),
                      (r"mitarbeiter(?:in)?\s*:\s*" + N, "collaboratore"),
                      (r"(?:avec )?la collaboration de\s+" + N, "collaboratore"),
                      (r"in collaboration with\s+" + N, "collaboratore"),
                      (r"(?:illustrated|decorations|drawings|illustrations) by\s+" + N, "illustratore"),
                      (r"(?:illustrations|dessins) de\s+" + N, "illustratore"),
                      (r"(?:zeichnungen|bilder|illustrationen) von\s+" + N, "illustratore")):
        for m in re.finditer(rx, testo, re.I):
            for n in re.split(r",| und | and | et ", m.group(1)):
                n = re.split(r"\s+(?:musik|music|musique|with|mit|avec)\b", n.strip(" ,"), flags=re.I)[0].strip(" ,.")
                if 3 < len(n) < 60:
                    out.append({"nome": n, "nascita": None, "morte": None, "ruolo": ruolo, "da": "dicitura"})
    return out


def persone_marc(rec):
    out = []
    for tag in ("100", "700"):
        for f in vu.campi(rec, tag):
            ruolo = ruolo_di(" ".join([f.get("e", ""), f.get("4", "")])) if (f.get("e") or f.get("4")) else ("autore" if tag == "100" else "collaboratore?")
            if not ruolo or not f.get("a"):
                continue
            n, m = vita(f.get("d"))
            out.append({"nome": html.unescape(f["a"]).strip(" ,."), "nascita": n, "morte": m, "ruolo": ruolo, "da": tag})
    dic = " ".join(html.unescape(f.get("c", "")) for f in vu.campi(rec, "245"))
    return out + dalla_dicitura(dic), dic


def persone_unimarc(rec):
    out = []
    for tag in ("700", "701", "702"):
        for f in vu.campi(rec, tag):
            ruolo = ruolo_di(f.get("4", "")) if f.get("4") else ("autore" if tag in ("700", "701") else "collaboratore?")
            if not ruolo or not f.get("a"):
                continue
            n, m = vita(f.get("f"))
            nome = (html.unescape(f.get("a", "")) + (", " + html.unescape(f["b"]) if f.get("b") else "")).strip(" ,.")
            out.append({"nome": nome, "nascita": n, "morte": m, "ruolo": ruolo, "da": tag})
    dic = " ".join(html.unescape(f.get("f", "") + " " + f.get("g", "")) for f in vu.campi(rec, "200"))
    return out + dalla_dicitura(dic), dic


def sru(base, query, schema, n=50):
    u = base + "?" + urllib.parse.urlencode({"version": "1.1" if "loc.gov" in base or "k10plus" in base else "1.2",
                                              "operation": "searchRetrieve", "query": query,
                                              "recordSchema": schema, "maximumRecords": str(n)})
    x = vu.scarica(u, timeout=90)
    return x.decode("utf-8", "replace") if x else None


def edizioni(fonte, titolo, cognome):
    """[(anno, persone, dicitura)] delle edizioni con lo stesso titolo e il cognome dell'autore."""
    if fonte == "loc":
        x = sru(va.SRU, f'dc.title="{va.sa(titolo)}" and dc.creator="{va.sa(cognome)}"', "marcxml", 25)
        time.sleep(2.5)   # il servizio LC chiude le connessioni se si va troppo veloci
        recs = re.findall(r"<record xmlns[^>]*>(.*?)</record>", x or "", re.S)
        leggi, ttag, tsub = persone_marc, "245", "ab"
    elif fonte == "k10plus":
        x = sru("https://sru.k10plus.de/opac-de-627", f'pica.tit="{titolo}" and pica.per="{cognome}"', "marcxml", 100)
        time.sleep(1)
        recs = vu.record(x or "")
        leggi, ttag, tsub = persone_marc, "245", "ab"
    else:
        x = sru("https://catalogue.bnf.fr/api/SRU", f'bib.title all "{titolo}" and bib.author all "{cognome}"', "unimarcxchange", 50)
        time.sleep(1.5)
        recs = vu.record(x or "")
        leggi, ttag, tsub = persone_unimarc, "200", "ae"
    if x is None:
        return None
    out = []
    for rec in recs:
        t = " ".join(v for f in vu.campi(rec, ttag) for c, v in f.items() if c in tsub)
        if not vu.stesso_titolo(html.unescape(t), titolo):
            continue
        if fonte == "bnf":
            a = [f.get("a", "")[9:13] for f in vu.campi(rec, "100")]
            a = [int(v) for v in a if v.isdigit()]
        else:
            a = vu.controllo(rec, "008")[7:11]
            a = [int(a)] if a.isdigit() else []
        persone, dic = leggi(rec)
        out.append({"anno": a[0] if a else None, "persone": persone, "dicitura": dic[:300]})
    return out


def campione():
    anno = RG.fase_sito(date.today())[1]
    ue = json.loads((R / "data" / f"{anno}.json").read_text(encoding="utf-8"))
    aut = [a for a in ue.get("autori", []) if a.get("letterario") and a.get("opere")]
    aut.sort(key=lambda a: -(a.get("visite_12m") or 0))
    scelti = [a for a in aut if a["wikidata"] in SEMPRE] + [a for a in aut if a["wikidata"] not in SEMPRE][:N_AUTORI]
    # opere alternate tra gli autori: prima la 1ª opera di tutti, poi la 2ª…
    out = []
    for i in range(N_OPERE if N_OPERE > 0 else 10):
        for a in scelti:
            if i < len(a["opere"]):
                out.append((a, a["opere"][i]))
    return anno, out


def codice_opera(a, o):
    mie = (pg.COAUT.get("per_autore") or {}).get(a["wikidata"], {})
    chiavi = {tuple(pg._parole(o.get("titolo"))), tuple(pg._parole(o.get("titolo_en")))} - {()}
    wq = next((q for q, w in mie.items() if {tuple(pg._parole(w.get("t"))), tuple(pg._parole(w.get("ti")))} & chiavi), None)
    return wq or next((r[0] for r in pg.opere_storico(a["wikidata"]) if {tuple(pg._parole(r[1])), tuple(pg._parole(r[2]))} & chiavi), None)


def stessa_persona(n1, n2):
    """Stesso cognome e iniziali compatibili: «R. Berlau» = «Berlau, Ruth» = «Ruth Berlau»."""
    a, b = set(parole(n1)), set(parole(n2))
    if not (a and b):
        return False
    if a <= b or b <= a or len(a & b) >= 2:
        return True
    comuni = {w for w in a & b if len(w) > 2}
    if not comuni:
        return False
    ia, ib = {w[0] for w in a - comuni}, {w[0] for w in b - comuni}
    return not ia or not ib or bool(ia & ib)


def main():
    inizio = time.time()
    anno, lista = campione()
    qids = [q for q in {codice_opera(a, o) for a, o in lista} if q and q.startswith("Q")]
    orig = va.titoli_originali(qids)
    out = []
    for a, o in lista:
        if time.time() - inizio > BUDGET:
            break
        D = pg.anno_di(a.get("morte"))
        cognome = (parole(a["nome"]) or [""])[-1]
        wq = codice_opera(a, o)
        titoli = list(dict.fromkeys(t for t in ((orig.get(wq) or (None, None))[1], o.get("titolo_en"), o.get("titolo")) if t))
        fonti = ["loc", "k10plus"] + (["bnf"] if set(a.get("paesi") or []) & FR else [])
        per_fonte, errori = {}, []
        for f in fonti:
            for t in titoli:
                ed = edizioni(f, t, cognome)
                if ed is None:
                    errori.append(f)
                    break
                if ed:
                    per_fonte[f] = {"titolo": t, "edizioni": ed}
                    break
        # persone trovate (esclusa la persona dell'autore), con le fonti che le nominano
        pers = {}
        for f, v in per_fonte.items():
            for e in v["edizioni"]:
                for p in e["persone"]:
                    if stessa_persona(p["nome"], a["nome"]) or (cognome and cognome in parole(p["nome"]) and p["ruolo"] == "autore"):
                        continue
                    k = next((k for k in pers if stessa_persona(k, p["nome"])), p["nome"])
                    x = pers.setdefault(k, {"nome": k, "nascita": None, "morte": None, "ruoli": set(), "fonti": set(), "anni": []})
                    x["nascita"] = x["nascita"] or p["nascita"]
                    x["morte"] = x["morte"] or p["morte"]
                    x["ruoli"].add(p["ruolo"])
                    x["fonti"].add(f)
                    if e["anno"]:
                        x["anni"].append(e["anno"])
        tardi, ignoti, w = pg.vincoli_opera(a, o, anno)
        # solo quello che dice Wikidata (non i coautori manuali): si misura il buco di Wikidata
        nomi_wd = [c[1] for c in w.get("co", [])] + [m[1] for m in w.get("mu", []) if m[1]]
        nomi_man = [x["nome"] for x in pg.COAUT_MAN.get(wq, [])]
        persone = []
        for x in pers.values():
            persone.append({**x, "ruoli": sorted(x["ruoli"]), "fonti": sorted(x["fonti"]), "anni": sorted(set(x["anni"]))[:8],
                            "su_wikidata": any(stessa_persona(x["nome"], n) for n in nomi_wd),
                            "nei_manuali": any(stessa_persona(x["nome"], n) for n in nomi_man),
                            "in_vita_autore": bool(x["anni"]) and D is not None and min(x["anni"]) <= D})
        anni = {f: min((e["anno"] for e in v["edizioni"] if e["anno"]), default=None) for f, v in per_fonte.items()}
        out.append({"autore": a["nome"], "aq": a["wikidata"], "morte": D, "titolo": o.get("titolo"), "opera": wq,
                    "titoli_cercati": titoli, "anno_wikidata": o.get("anno"), "anni_fonti": anni, "errori": errori,
                    "edizioni": {f: len(v["edizioni"]) for f, v in per_fonte.items()}, "persone": persone,
                    "diciture": sorted({e["dicitura"] for v in per_fonte.values() for e in v["edizioni"] if e["dicitura"]})[:6]})
    USCITA.mkdir(parents=True, exist_ok=True)
    (USCITA / "risultati.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=list), encoding="utf-8")
    riepilogo(out, len(lista), time.time() - inizio)


def riepilogo(out, n_lista, secondi):
    trovate = [x for x in out if x["edizioni"]]
    per_f = Counter(f for x in out for f in x["edizioni"])
    err = Counter(f for x in out for f in x["errori"])
    # collaboratori e illustratori nelle edizioni uscite quando l'autore era vivo, che Wikidata non segna
    nuovi = [(x, p) for x in out for p in x["persone"] if not p["su_wikidata"] and p["in_vita_autore"]
             and set(p["ruoli"]) & {"collaboratore", "illustratore", "autore", "musica"}]
    contano = [(x, p) for x, p in nuovi if x["morte"] and p["morte"] and p["morte"] > x["morte"]]
    senza_data = [(x, p) for x, p in nuovi if not p["morte"]]
    anni = [(x, min(v for v in x["anni_fonti"].values() if v)) for x in out if any(x["anni_fonti"].values())]
    con_wd = [(x, a) for x, a in anni if x["anno_wikidata"]]
    uguali = [1 for x, a in con_wd if abs(a - x["anno_wikidata"]) <= 1]
    righe = ["# Prova – opere dalle fonti", "",
             f"Opere nel campione: {n_lista}; controllate: {len(out)} in {secondi / 60:.0f} minuti; trovate in almeno un catalogo: {len(trovate)}.",
             "", "Opere trovate per catalogo: " + ", ".join(f"{k} {v}" for k, v in per_f.most_common()),
             "Errori di rete per catalogo: " + (", ".join(f"{k} {v}" for k, v in err.most_common()) or "nessuno"), "",
             "## Persone che Wikidata non segna (in edizioni uscite quando l'autore era vivo)", "",
             f"- in tutto: {len(nuovi)} (opere: {len({x['titolo'] + x['autore'] for x, _ in nuovi})})",
             f"- morte dopo l'autore, quindi cambiano la data europea se sono coautori o illustratori: {len(contano)}",
             f"- senza data di morte nel catalogo: {len(senza_data)}", ""]
    righe += [f"- {x['autore']}, «{x['titolo']}»: {p['nome']} ({p['nascita'] or '?'}–{p['morte'] or '?'}), "
              f"{'/'.join(p['ruoli'])}, fonti {'/'.join(p['fonti'])}, edizioni {p['anni'][:3]}" for x, p in contano[:60]]
    righe += ["", "## Anno della prima edizione", "",
              f"Opere con un anno da almeno un catalogo: {len(anni)}; con anche l'anno su Wikidata: {len(con_wd)}; "
              f"coincide (±1 anno): {len(uguali)}; diverso: {len(con_wd) - len(uguali)}.", "",
              "Esempi diversi (Wikidata → edizione più vecchia nei cataloghi):", ""]
    righe += [f"- {x['autore']}, «{x['titolo']}»: {x['anno_wikidata']} → {a} {x['anni_fonti']}" for x, a in con_wd
              if abs(a - x["anno_wikidata"]) > 1][:30]
    righe += ["", "## Casi noti", ""]
    for aut, tit, chi in (("Q38757", "L'opera da tre soldi", "Hauptmann"), ("Q38757", "Il cerchio di gesso del Caucaso", "Berlau"),
                          ("Q207036", "Winnie Puh", "Shepard")):
        x = next((x for x in out if x["aq"] == aut and x["titolo"] == tit), None)
        p = next((p for p in (x or {}).get("persone", []) if chi.lower() in " ".join(parole(p["nome"]))), None)
        if not x:
            righe.append(f"- {tit}: non controllata (tempo finito)")
        elif p:
            righe.append(f"- {tit}: {chi} trovata: {p['nome']} ({p['nascita'] or '?'}–{p['morte'] or '?'}), {'/'.join(p['ruoli'])}, fonti {'/'.join(p['fonti'])}")
        else:
            righe.append(f"- {tit}: {chi} NON trovata (edizioni per catalogo: {x['edizioni']}; diciture: {x['diciture'][:2]})")
    (USCITA / "riepilogo.md").write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe[:16]))


if __name__ == "__main__":
    main()
