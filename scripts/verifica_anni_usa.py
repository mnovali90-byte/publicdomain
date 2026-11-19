"""Verifica dell'anno di uscita per le liste USA del Public Domain Day (data/us-2027.json, data/us-2028.json).

Metodo: docs/metodo-anni-opere.md, sezione «Liste USA del Public Domain Day». Fonti:
  1. Duke (liste del Public Domain Day degli anni passati)
  2. Registro del copyright USA (Catalog of Copyright Entries, libri, trascritto dalla New York Public Library, CC0)
  3. Open Library   4. Library of Congress
  5. Biblioteca nazionale della lingua dell'opera, sul titolo originale: BnF (francese), K10plus, catalogo collettivo tedesco (tedesco)
Per ogni fonte si prende l'edizione più vecchia con lo stesso titolo (e lo stesso autore).

Esiti per la lista del 2027 (libri del 1931):
  - "ok"    : almeno una fonte ha un'edizione del 1931;
  - "prima" : una fonte AUTOREVOLE (Duke, registro del copyright, BnF, K10plus) ha un'edizione più vecchia e nessuna
              ha il 1931 → la lista mette il libro nell'anno sbagliato; Open Library e Library of Congress da sole
              non bastano (prova del 19/11/2026: Open Library dà «Death in the Afternoon» al 1920);
  - "nd"    : nessuna conferma.
Scrive data/us-anni-verificati.json {anno_lista: {qid: [esito, anno, fonte, data, fonti_provate, {fonte: anno}]}}
e il riepilogo in docs/stima-sito/us-anni.json. Gira con stima.yml (passo.txt = verifica_anni_usa).
"""
import html, json, os, re, sys, time, urllib.parse, urllib.request
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "storico"))
import verifica_anni as va   # noqa: E402  (Open Library e Library of Congress, come per lo Storico)

parole, UA = va.parole, va.UA
BUDGET = float(os.environ.get("BUDGET_MINUTI_USA", "50")) * 60
RICONTROLLA = 30   # giorni: un libro non confermato si ricontrolla dopo un mese, non a ogni giro
OGGI = date.today().isoformat()
AUTOREVOLI = ("duke", "cce", "bnf", "k10plus")
CCE_RAW = "https://raw.githubusercontent.com/NYPL/catalog_of_copyright_entries_project/master/xml/"
CCE_FILE = {}   # anno -> file del volume: si legge dall'elenco del repository NYPL (i nomi dei file non seguono una regola)
CCE_API = "https://api.github.com/repos/NYPL/catalog_of_copyright_entries_project/contents/xml/"
FONTI_KO = Counter()   # richieste fallite per fonte: se una fonte non risponde mai, va detto (docs/da-decidere.md)
LINGUA = {"Q150": "fr", "Q188": "de"}
ARTICOLI = {"the", "a", "an", "le", "la", "les", "l", "un", "une", "der", "die", "das", "ein", "eine"}


def scarica(u, timeout=60, prove=4):
    for t in range(prove):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout).read()
        except Exception as e:
            ultimo = e
            time.sleep(5 * (t + 1))
    print("non scaricato:", u[:120], ultimo)
    FONTI_KO[urllib.parse.urlparse(u).netloc] += 1
    return None


def file_cce(anni):
    """Nome del file XML di ogni volume (es. 1931 -> 1931/1931_v28.xml), letto dall'elenco del repository."""
    for y in anni:
        if y in CCE_FILE:
            continue
        x = scarica(CCE_API + str(y), timeout=60)
        if not x:
            continue
        nomi = [f["name"] for f in json.loads(x) if f.get("type") == "file" and f["name"].endswith(".xml")]
        if nomi:
            CCE_FILE[y] = f"{y}/{sorted(nomi)[0]}"
    return CCE_FILE


def senza_articolo(w):
    return w[1:] if len(w) > 1 and w[0] in ARTICOLI else w


def stesso_titolo(trovato, cercato):
    a, b = senza_articolo(parole(trovato)), senza_articolo(parole(cercato))
    return bool(b) and a[:len(b)] == b


# ---------- registro del copyright USA ----------
def indice_cce(anni=None):
    idx = {}
    if anni:
        file_cce(anni)
    for y, f in CCE_FILE.items():
        x = scarica(CCE_RAW + f, timeout=180)
        if not x:
            for ramo in ("main",):
                x = scarica(CCE_RAW.replace("/master/", f"/{ramo}/") + f, timeout=180)
        if not x:
            continue
        for e in re.findall(r"<copyrightEntry\b.*?</copyrightEntry>", x.decode("utf-8", "replace"), re.S):
            t = re.search(r"<title>(.*?)</title>", e, re.S)
            if not t:
                continue
            tw = senza_articolo(parole(html.unescape(re.sub("<[^>]+>", "", t.group(1)))))
            au = set(parole(html.unescape(" ".join(re.findall(r"<authorName>(.*?)</authorName>", e)))))
            ds = [int(d) for d in re.findall(r'<pubDate date="(\d{4})', e)] or \
                 [int(d) for d in re.findall(r'<regDate date="(\d{4})', e)]
            if tw and ds:
                idx.setdefault(tw[0], []).append((tw, au, min(ds)))
    print("registro del copyright: voci", sum(map(len, idx.values())))
    return idx


def cce(idx, o, cognomi):
    tw = senza_articolo(parole(re.sub(r"\s*\(.*?\)\s*$", "", o["titolo"])))
    if not tw:
        return None
    anni = [a for t, au, a in idx.get(tw[0], []) if t[:len(tw)] == tw and (not cognomi or any(c in au for c in cognomi))]
    return min(anni) if anni else None


# ---------- titolo e lingua originali da Wikidata ----------
def originali(qids):
    out = {}
    for i in range(0, len(qids), 50):
        u = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
            {"action": "wbgetentities", "ids": "|".join(qids[i:i + 50]), "props": "claims|labels", "format": "json"})
        x = scarica(u)
        if not x:
            continue
        for q, e in json.loads(x).get("entities", {}).items():
            cl = e.get("claims", {})
            lingue = [c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") for c in cl.get("P407", [])]
            lg = next((LINGUA[l] for l in lingue if l in LINGUA), None)   # lingua dell'opera (P407), obbligatoria
            titolo = None
            for c in cl.get("P1476", []):   # titolo nella STESSA lingua dell'opera (prova del 19/11: Musil aveva il titolo francese)
                v = c["mainsnak"].get("datavalue", {}).get("value", {})
                if lg and v.get("language") == lg:
                    titolo = v["text"]
            if lg and not titolo:
                titolo = e.get("labels", {}).get(lg, {}).get("value")
            if lg and titolo:
                out[q] = (lg, titolo)
        time.sleep(1)
    return out


# ---------- biblioteche nazionali ----------
def campi(rec, tag):
    return [dict(re.findall(r'<(?:\w+:)?subfield code="(\w)">([^<]*)<', m))
            for m in re.findall(rf'<(?:\w+:)?datafield[^>]*tag="{tag}"[^>]*>(.*?)</(?:\w+:)?datafield>', rec, re.S)]


def controllo(rec, tag):
    return (re.findall(rf'<(?:\w+:)?controlfield tag="{tag}">([^<]*)<', rec) or [""])[0]


def record(x):
    return re.findall(r"<(?:\w+:)?recordData>(.*?)</(?:\w+:)?recordData>", x, re.S)


def bnf(titolo, cognome):
    q = f'bib.title all "{titolo}" and bib.author all "{cognome}"'
    u = "https://catalogue.bnf.fr/api/SRU?" + urllib.parse.urlencode(
        {"version": "1.2", "operation": "searchRetrieve", "query": q, "recordSchema": "unimarcxchange",
         "maximumRecords": "50"})
    x = scarica(u, timeout=90)
    if not x:
        return None, 0
    recs, anni = record(x.decode("utf-8", "replace")), []
    for rec in recs:
        t = " ".join(f.get("a", "") for f in campi(rec, "200"))
        if not stesso_titolo(html.unescape(t), titolo):
            continue
        a = [f.get("a", "")[9:13] for f in campi(rec, "100")]
        a = [int(v) for v in a if v.isdigit()] or \
            [int(m) for f in campi(rec, "210") + campi(rec, "214") for m in re.findall(r"1[5-9]\d\d", f.get("d", ""))]
        anni += a[:1]
    time.sleep(1.5)
    return (min(anni) if anni else None), len(recs)


def k10plus(titolo, cognome, p):
    """Catalogo collettivo tedesco K10plus (GBV/SWB): la DNB blocca le richieste da GitHub (prova del 19/11/2026).
    Si chiedono solo le edizioni dei 3 anni prima e dell'anno della lista, perché i risultati sono centinaia."""
    anni_q = " or ".join(f"pica.jhr={a}" for a in range(p - 3, p + 1))
    q = f'pica.tit="{titolo}" and pica.per="{cognome}" and ({anni_q})'
    u = "https://sru.k10plus.de/opac-de-627?" + urllib.parse.urlencode(
        {"version": "1.1", "operation": "searchRetrieve", "query": q, "recordSchema": "marcxml", "maximumRecords": "100"})
    x = scarica(u, timeout=90)
    if not x:
        return None, 0
    recs, anni = record(x.decode("utf-8", "replace")), []
    for rec in recs:
        t = " ".join(f.get("a", "") + " " + f.get("b", "") for f in campi(rec, "245"))
        if not stesso_titolo(html.unescape(t), titolo):
            continue
        a = controllo(rec, "008")[7:11]
        if a.isdigit():
            anni.append(int(a))
    time.sleep(1)
    return (min(anni) if anni else None), len(recs)


def decidi(trovati, p):
    giusti = [f for f, a in trovati.items() if a == p]
    if giusti:
        ordine = ("duke", "cce", "bnf", "k10plus", "openlibrary", "loc")
        f = min(giusti, key=ordine.index)
        return "ok", p, f
    prima = [(a, f) for f, a in trovati.items() if a is not None and a < p and f in AUTOREVOLI]
    if prima:
        a, f = min(prima)
        return "prima", a, f
    altri = [(a, f) for f, a in trovati.items() if a is not None]
    a, f = min(altri) if altri else (None, None)
    return "nd", a, f


def main():
    inizio = time.time()
    oggi_anno = date.today().year
    nomi = sorted(x.name for x in (R / "data").glob("us-[0-9][0-9][0-9][0-9].json") if int(x.stem[3:]) > oggi_anno)
    pubs = [int(n[3:7]) - 96 for n in nomi]
    # volumi del registro: dall'anno prima della lista più vecchia a due anni dopo la più recente (registrazioni tardive)
    dk, idx = va.duke(), indice_cce(range(min(pubs) - 3, max(pubs) + 3) if pubs else [])
    f = R / "data" / "us-anni-verificati.json"
    try:
        tutto = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        tutto = {}
    liste = {}
    for nome in nomi:
        d = json.loads((R / "data" / nome).read_text(encoding="utf-8"))
        liste[str(d["anno"])] = d
    orig = originali(sorted({o["qid"] for d in liste.values() for o in d["opere"]}))
    print("titoli originali francesi/tedeschi da Wikidata:", Counter(v[0] for v in orig.values()))
    prove_naz = Counter()
    riepilogo = {}
    for chiave, d in liste.items():
        p = d["anno_pubblicazione"]
        fatto = tutto.setdefault(chiave, {})
        for o in d["opere"]:
            q = o["qid"]
            vecchio = fatto.get(q)
            if vecchio and vecchio[0] == "ok" and len(vecchio) > 5 and vecchio[2] != "bnf":   # bnf: si rifà con la lingua giusta
                continue
            if vecchio and len(vecchio) > 5 and vecchio[3] >= (date.today() - timedelta(days=RICONTROLLA)).isoformat() \
                    and not os.environ.get("RIFAI_TUTTO"):
                continue
            if time.time() - inizio > BUDGET:
                break
            cognomi = [parole(a["nome"])[-1] for a in o.get("autori", []) if parole(a["nome"])]
            trovati, provate = {}, []
            if q in dk:
                trovati["duke"] = dk[q]
            provate.append("cce")
            trovati["cce"] = cce(idx, o, cognomi)
            if q in orig and cognomi and p not in trovati.values():
                lg, titolo = orig[q]
                fonte = "bnf" if lg == "fr" else "k10plus"
                anno, n = bnf(titolo, cognomi[0]) if lg == "fr" else k10plus(titolo, cognomi[0], p)
                provate.append(fonte)
                trovati[fonte] = anno
                prove_naz[(fonte, "risposte" if n else "nessun record", "anno trovato" if anno else "-")] += 1
            if p not in trovati.values():
                if vecchio and vecchio[0] == "ok" and vecchio[2] in ("openlibrary", "loc"):   # già confermato dal giro di prima (Open Library o LC)
                    trovati[vecchio[2]] = vecchio[1]
                else:
                    _, a = va.open_library(va_riga(o))
                    provate.append("openlibrary")
                    trovati["openlibrary"] = a
                    if a != p:
                        _, a = va.library_of_congress(va_riga(o))
                        provate.append("loc")
                        trovati["loc"] = a
            esito, anno, fonte = decidi(trovati, p)
            fatto[q] = [esito, anno, fonte, OGGI, provate, {k: v for k, v in trovati.items() if v}]
            time.sleep(0.3)
        f.write_text(json.dumps(tutto, ensure_ascii=False, indent=0), encoding="utf-8")
        voci = [fatto[o["qid"]] for o in d["opere"] if o["qid"] in fatto]
        riepilogo[chiave] = {
            "libri": len(d["opere"]), "controllati": len(voci),
            "esiti": dict(Counter(v[0] for v in voci)),
            "confermati_per_fonte": dict(Counter(v[2] for v in voci if v[0] == "ok")),
            "conferme_per_fonte_anche_doppie": dict(Counter(k for v in voci if len(v) > 5 for k, a in v[5].items() if a == d["anno_pubblicazione"])),
            "piu_vecchi": [[o["titolo"], fatto[o["qid"]][1], fatto[o["qid"]][2]] for o in d["opere"]
                           if o["qid"] in fatto and fatto[o["qid"]][0] == "prima"],
            "non_confermati": [[o["titolo"], orig.get(o["qid"], [None, None])[1], fatto[o["qid"]][5] if len(fatto[o["qid"]]) > 5 else {}]
                               for o in d["opere"] if o["qid"] in fatto and fatto[o["qid"]][0] == "nd"],
        }
        print(chiave, riepilogo[chiave]["esiti"], riepilogo[chiave]["confermati_per_fonte"])
    riepilogo["biblioteche_nazionali"] = {" | ".join(k): v for k, v in prove_naz.items()}
    riepilogo["fonti_non_raggiunte"] = dict(FONTI_KO)
    riepilogo["registro_volumi"] = {str(k): v for k, v in CCE_FILE.items()}
    print("biblioteche nazionali:", dict(prove_naz))
    (R / "docs" / "stima-sito" / "us-anni.json").write_text(json.dumps(riepilogo, ensure_ascii=False, indent=1),
                                                            encoding="utf-8")


def va_riga(o):
    return [o["qid"], o["titolo"], None, None, None, [[a["qid"], a["nome"], None, False] for a in o.get("autori", [])]]


if __name__ == "__main__":
    main()
