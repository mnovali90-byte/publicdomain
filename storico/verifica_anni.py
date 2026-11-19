"""Seconda fonte per l'anno di uscita delle opere che lo Storico dà per libere SOLO negli USA, e solo grazie all'anno.

Perché (19/11/2026): l'anno viene da Wikidata e nessuno lo controllava. Esempio: le «Poesie di Svendborg» di Brecht
risultavano del 1926 (quindi libere negli USA), ma sono uscite nel 1939.

Regola (fissata prima di vedere i risultati):
  - l'opera è libera negli USA solo se una seconda fonte conferma che è uscita entro il limite (oggi il 1930):
    la Duke (liste del Public Domain Day) oppure Open Library (anno di prima pubblicazione, per titolo e autore);
  - se la seconda fonte dà un anno dopo il limite, o non trova l'opera: «da verificare».
Scrive data/storico/anni_verificati.json: {qid: [esito, anno_seconda_fonte, fonte]} con esito "ok" | "no" | "nd".
La pagina «Già pubblici» legge questo file: senza «ok» l'opera è «da verificare» negli USA.
Gira dentro gia-pubblici.yml; riprende da dove era rimasta (le opere già controllate non si ricontrollano per 90 giorni).
"""
import json, re, sys, time, unicodedata, urllib.parse, urllib.request
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
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.findall(r"[a-z0-9]+", t)


def libera_ue(r):
    au = r[5]
    if r[3] is not None and r[3] <= Y - 171:
        return True
    return bool(au) and all((a[2] is not None and a[2] <= Y - 71) or a[3] for a in au)


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
    resta = [q for q in lista if q not in fatto or (fatto[q][2] != "duke" and fatto[q][3] < vecchio)]
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
                fatto[q] = [esito, anno, "openlibrary", oggi]
    f.write_text(json.dumps(fatto, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    from collections import Counter
    c = Counter(v[0] for q, v in fatto.items() if q in lista)
    print(f"esiti: {dict(c)}; ancora da controllare: {len(lista) - sum(c.values())}")
    if len(lista) - sum(c.values()) > 0:
        Path(".verifica_incompleta").write_text("1")


if __name__ == "__main__":
    main()
