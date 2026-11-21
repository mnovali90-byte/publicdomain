"""Seconda fonte per l'anno di uscita delle opere che lo Storico dà per libere SOLO negli USA, e solo grazie all'anno.

Perché (19/11/2026): l'anno viene da Wikidata e nessuno lo controllava. Esempio: le «Poesie di Svendborg» di Brecht
risultavano del 1926 (quindi libere negli USA), ma sono uscite nel 1939.

Metodo (docs/metodo-anni-opere.md, fissato prima di vedere i risultati):
  - l'opera è libera negli USA solo se almeno una fonte indipendente da Wikidata conferma che ne esiste
    un'edizione uscita entro il limite (oggi il 1930), con lo stesso titolo e lo stesso autore. Fonti, in ordine:
      1. Duke (liste del Public Domain Day), 2. Open Library (anno di prima pubblicazione),
      3. catalogo della Library of Congress (anno di pubblicazione di ogni edizione, campo 008);
  - le fonti servono a confermare, non a smentire: un anno più tardo vuol dire solo che quella fonte non ha
    l'edizione più vecchia. Senza conferma l'opera resta «da verificare».
Scrive data/storico/anni_verificati.json: {qid: [esito, anno, fonte, data, fonti_provate]} con esito "ok" | "no" | "nd".
La pagina «Già pubblici» legge questo file: senza «ok» l'opera è «da verificare» negli USA.
Gira dentro gia-pubblici.yml; riprende da dove era rimasta (le opere già controllate non si ricontrollano per 90 giorni).
"""
import os, sys, html, json, re, sys, time, unicodedata, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

S = Path(__file__).resolve().parent.parent / "data" / "storico"
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
Y = date.today().year
LIMITE = Y - 96
BUDGET = float(sys.argv[1]) if len(sys.argv) > 1 else 15   # minuti
RINFRESCA = 90


def parole(t):
    t = (t or "").replace("’", "").replace("'", "")   # «One’s» e «One's» devono dare la stessa parola (20/11/2026)
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.findall(r"[a-z0-9]+", t)


_TIPI = None


def libera_ue(r):
    """Libera in Europa: la stessa regola di tutto il sito (scripts/regole.py, autori_che_contano), niente copie."""
    global _TIPI
    if r[3] is not None and r[3] <= Y - 171:
        return True
    if _TIPI is None:
        try:
            _TIPI = json.loads((S / "coautori.json").read_text(encoding="utf-8")).get("autori", {})
        except Exception:
            _TIPI = {}
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "scripts"))
    from regole import autori_che_contano, opera_antica
    from registro import dati_eta
    cre, antiche = dati_eta()
    grezzi = [{"qid": a[0], "nome": a[1], "morte": a[2], "antico": bool(a[3])} for a in r[5]]
    if opera_antica(r[0], grezzi, r[3], cre.get(r[0]), antiche, Y):
        return True
    au = autori_che_contano([{"qid": a[0], "nome": a[1], "morte": a[2], "antico": bool(a[3])} for a in r[5]], _TIPI, Y)
    return bool(au) and all(a.get("antico") or (a.get("morte") is not None and a["morte"] <= Y - 71) for a in au)


def da_controllare():
    tutte = {}
    for f in sorted((S / "ricerca").glob("*.json")):
        for r in json.loads(f.read_text(encoding="utf-8"))["opere"]:
            tutte.setdefault(r[0], r)
    return {q: r for q, r in tutte.items() if r[3] is not None and r[3] <= LIMITE and not libera_ue(r)}


def duke():
    out = {}
    try:
        d = json.loads((S / "duke.json").read_text(encoding="utf-8"))
        for anno in d.values():
            for v in anno.get("libri", []):
                if v.get("wd"):
                    out[v["wd"]["qid"]] = v["pub"]
    except Exception as e:
        print("Duke non letta:", e)
    return out


def open_library(r):
    """Anno di prima pubblicazione su Open Library: il più vecchio tra i risultati con lo stesso titolo e lo stesso autore."""
    titolo = re.sub(r"\s*\(.*?\)\s*$", "", r[1] or "")
    tw = parole(titolo)
    if not tw:
        return "nd", None
    q = {"title": titolo, "fields": "title,author_name,first_publish_year", "limit": 10}
    cognomi = [parole(a[1])[-1] for a in r[5] if parole(a[1])]
    if cognomi:
        q["author"] = r[5][0][1]
    u = "https://openlibrary.org/search.json?" + urllib.parse.urlencode(q)
    for t in range(3):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40))
            break
        except Exception:
            time.sleep(4 * (t + 1))
    else:
        return None, None   # errore di rete: si riprova al giro dopo
    anni = []
    for doc in d.get("docs", []):
        if parole(doc.get("title")) != tw:
            continue
        if cognomi and not any(c in parole(" ".join(doc.get("author_name") or [])) for c in cognomi):
            continue
        if doc.get("first_publish_year"):
            anni.append(doc["first_publish_year"])
    if not anni:
        return "nd", None
    a = min(anni)
    return ("ok" if a <= LIMITE else "no"), a


SRU = "http://lx2.loc.gov:210/LCDB"


def sa(t):
    return "".join(c for c in unicodedata.normalize("NFKD", t or "") if not unicodedata.combining(c))


def library_of_congress(r):
    """Anno più vecchio tra le edizioni del catalogo LC con lo stesso titolo (campo 245) e il cognome dell'autore."""
    titolo = re.sub(r"\s*\(.*?\)\s*$", "", r[1] or "")
    tw = parole(titolo)
    if not tw:
        return "nd", None
    q = f'dc.title="{sa(titolo)}"'   # «bath.name» non è accettato dal catalogo LC (prova del 19/11/2026)
    cognomi = [parole(a[1])[-1] for a in r[5] if parole(a[1])]
    if cognomi:
        q += f' and dc.creator="{cognomi[0]}"'
    x = None
    for domanda in (q,):
        u = SRU + "?" + urllib.parse.urlencode({"version": "1.1", "operation": "searchRetrieve", "query": domanda,
                                               "maximumRecords": "25", "recordSchema": "marcxml"})
        for t in range(4):
            try:
                x = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90).read().decode("utf-8", "replace")
                time.sleep(2.5)   # il servizio chiude le connessioni se si va troppo veloci
                break
            except Exception:
                x = None
                time.sleep(10 * (t + 1))
        if x and "numberOfRecords" in x:
            break
    if not x or "numberOfRecords" not in x:
        return None, None
    anni = []
    for rec in re.findall(r"<record xmlns[^>]*>(.*?)</record>", x, re.S):
        t245 = re.search(r'tag="245"[^>]*>(.*?)</datafield>', rec, re.S)
        if not t245:
            continue
        ta = " ".join(v for c, v in re.findall(r'code="(\w)">([^<]*)<', t245.group(1)) if c in "ab")
        if parole(html.unescape(ta))[:len(tw)] != tw:
            continue
        f008 = (re.findall(r'tag="008">([^<]*)<', rec) or [""])[0]
        if f008[7:11].isdigit():
            anni.append(int(f008[7:11]))
    if not anni:
        return "nd", None
    a = min(anni)
    return ("ok" if a <= LIMITE else "no"), a


# ---------- fonti forti e titolo originale (20/11/2026) ----------
# Prima si cercava solo con il titolo inglese di Wikidata: «Essere e tempo» non si trovava perché nei cataloghi è
# «Sein und Zeit». Ora, per le opere non ancora confermate: titolo originale (lingua dell'opera, P407) su Open Library e
# Library of Congress, più le fonti delle liste (scripts/verifica_anni_usa.py): registro del copyright americano
# (1923-1930), BnF per le opere francesi, K10plus per le tedesche, ISFDB per riviste e racconti (solo se l'anno
# trovato è entro 3 anni da quello di Wikidata: i titoli brevi dei racconti possono coincidere per caso).
LINGUE = {"Q150": "fr", "Q188": "de", "Q652": "it", "Q1321": "es", "Q5146": "pt", "Q7411": "nl", "Q9027": "sv",
          "Q809": "pl", "Q9056": "cs", "Q9067": "hu", "Q9035": "da", "Q9043": "no", "Q1412": "fi", "Q7026": "ca",
          "Q256": "tr", "Q7913": "ro", "Q9288": "he", "Q5287": "ja", "Q7737": "ru"}


def titoli_originali(qids):
    """{opera: (lingua, titolo nella lingua dell'opera)} da Wikidata (P407 e P1476, altrimenti l'etichetta)."""
    out = {}
    for i in range(0, len(qids), 50):
        u = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
            {"action": "wbgetentities", "ids": "|".join(qids[i:i + 50]), "props": "claims|labels", "format": "json"})
        for t in range(3):
            try:
                d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60))
                break
            except Exception:
                time.sleep(5 * (t + 1))
        else:
            continue
        for q, e in d.get("entities", {}).items():
            cl = e.get("claims", {})
            lingue = [c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") for c in cl.get("P407", [])]
            lg = next((LINGUE[l] for l in lingue if l in LINGUE), None)
            if not lg:
                continue
            titolo = next((c["mainsnak"]["datavalue"]["value"]["text"] for c in cl.get("P1476", [])
                           if c["mainsnak"].get("datavalue", {}).get("value", {}).get("language") == lg), None)
            titolo = titolo or e.get("labels", {}).get(lg, {}).get("value")
            if titolo:
                out[q] = (lg, titolo)
        time.sleep(1)
    return out


def fonti_forti(r, orig, idx, V):
    """(anno confermato entro il limite, fonte, fonti provate) oppure (None, None, provate). V = scripts/verifica_anni_usa."""
    provate, y = [], r[3]
    cognomi = [parole(a[1])[-1] for a in r[5] if parole(a[1] or "")]
    o = {"qid": r[0], "titolo": r[1] or "", "autori": [{"nome": a[1]} for a in r[5]]}
    conf = []
    c = V.cce(idx, o, cognomi)
    provate.append("cce")
    if c and c <= LIMITE:
        conf.append((c, "cce"))
    if r[0] in orig:
        lg, t = orig[r[0]]
        r2 = list(r); r2[1] = t
        e, a = open_library(r2); provate.append("openlibrary:originale")
        if e == "ok":
            conf.append((a, "openlibrary:originale"))
        if not conf:
            e, a = library_of_congress(r2); provate.append("loc:originale")
            if e == "ok":
                conf.append((a, "loc:originale"))
        if not conf and cognomi and lg in ("fr", "de"):
            try:
                a = V.bnf(t, cognomi[0])[0] if lg == "fr" else V.k10plus(t, cognomi[0], min(y + 3, LIMITE))[0]
            except Exception:
                a = None
            provate.append("bnf" if lg == "fr" else "k10plus")
            if a and a <= LIMITE:
                conf.append((a, "bnf" if lg == "fr" else "k10plus"))
    if not conf and cognomi:
        try:
            i_ = V.puntate_isfdb(o, cognomi, LIMITE)
        except Exception:
            i_ = None
        provate.append("isfdb")
        if i_ and i_[0] <= LIMITE and abs(i_[0] - y) <= 3:
            conf.append((i_[0], "isfdb"))
    if conf:
        a, f = min(conf)
        return a, f, provate
    return None, None, provate


def main():
    f = S / "anni_verificati.json"
    try:
        fatto = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        fatto = {}
    lista = da_controllare()
    dk = duke()
    oggi = date.today().isoformat()
    vecchio = (date.today() - timedelta(days=RINFRESCA)).isoformat()
    for q in list(fatto):
        if q not in lista:
            del fatto[q]
    for q in lista:
        if q in dk:
            fatto[q] = ["ok" if dk[q] <= LIMITE else "no", dk[q], "duke", oggi]
    # si ricontrollano dopo 90 giorni solo i dati di Open Library; le conferme di Duke, Library of Congress e fonti
    # forti restano (prima un nuovo «non trovato» di Open Library poteva cancellare una conferma buona)
    resta = [q for q in lista if q not in fatto or (fatto[q][2] == "openlibrary" and fatto[q][3] < vecchio)]
    print(f"da controllare: {len(lista)} (Duke: {sum(1 for q in lista if q in dk)}), mancano: {len(resta)}")
    fine = time.time() + BUDGET * 60

    def uno(q):
        if time.time() > fine:
            return q, None, None
        esito, anno = open_library(lista[q])
        time.sleep(0.5)
        return q, esito, anno
    with ThreadPoolExecutor(max_workers=3) as pool:
        for q, esito, anno in pool.map(uno, resta):
            if esito:
                gia = fatto.get(q, [None] * 5)
                fatto[q] = [esito, anno, "openlibrary", oggi, sorted(set((gia[4] if len(gia) > 4 and gia[4] else []) + ["openlibrary"]))]
    # terza fonte: Library of Congress, solo per le non confermate e non ancora provate lì (una richiesta alla volta)
    lc = [q for q in lista if q in fatto and fatto[q][0] != "ok" and "loc" not in (fatto[q][4] if len(fatto[q]) > 4 else [])]
    print(f"Library of Congress: da provare {len(lc)}")
    for q in lc:
        if time.time() > fine:
            break
        esito, anno = library_of_congress(lista[q])
        provate = (fatto[q][4] if len(fatto[q]) > 4 else [fatto[q][2]]) + ["loc"]
        if esito == "ok":
            fatto[q] = ["ok", anno, "loc", oggi, provate]
        else:
            fatto[q] = fatto[q][:4] + [provate]
        if lc.index(q) % 100 == 0:
            f.write_text(json.dumps(fatto, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    f.write_text(json.dumps(fatto, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    # quarta fase (21/11/2026): titolo originale e fonti forti (fonti_forti, qui sopra), per le non confermate che non
    # ci sono ancora passate; prima le più note. Prova del 20-21/11: 86 confermate su 515, controllo a mano tutto giusto.
    ff = sorted((q for q in lista if q in fatto and fatto[q][0] != "ok"
                 and "forti" not in (fatto[q][4] if len(fatto[q]) > 4 else [])), key=lambda q: -(lista[q][4] or 0))
    print(f"titolo originale e fonti forti: da provare {len(ff)}", flush=True)
    if ff and time.time() < fine:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
        import verifica_anni_usa as V
        orig = titoli_originali(ff[:3000])
        idx = V.indice_cce(list(range(1923, LIMITE + 1)))
        for n, q in enumerate(ff):
            if time.time() > fine:
                break
            a, fonte, prov = fonti_forti(lista[q], orig, idx, V)
            provate = (fatto[q][4] if len(fatto[q]) > 4 else [fatto[q][2]]) + ["forti"]
            fatto[q] = ["ok", a, fonte, oggi, provate] if a else fatto[q][:4] + [provate]
            if n % 100 == 0:
                f.write_text(json.dumps(fatto, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        f.write_text(json.dumps(fatto, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    from collections import Counter
    c = Counter(v[0] for q, v in fatto.items() if q in lista)
    per_fonte = Counter(v[2] for q, v in fatto.items() if q in lista and v[0] == "ok")
    lc_resta = sum(1 for q in lista if q in fatto and fatto[q][0] != "ok" and "loc" not in (fatto[q][4] if len(fatto[q]) > 4 else []))
    ff_resta = sum(1 for q in lista if q in fatto and fatto[q][0] != "ok" and "forti" not in (fatto[q][4] if len(fatto[q]) > 4 else []))
    print(f"esiti: {dict(c)}; confermate per fonte: {dict(per_fonte)}; mai controllate: {len(lista) - sum(c.values())}; "
          f"da provare sulla Library of Congress: {lc_resta}; da provare con il titolo originale: {ff_resta}")
    if len(lista) - sum(c.values()) > 0 or lc_resta > 0 or ff_resta > 0:
        Path(".verifica_incompleta").write_text("1")


if __name__ == "__main__":
    main()
