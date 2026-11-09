"""Seconda fonte per l'anno di morte degli autori, e illustratori delle loro opere.

Per ogni autore «letterario» dei file data/<anno>.json:
1. da Wikidata prende i codici dell'autore in due biblioteche nazionali:
   GND (Deutsche Nationalbibliothek, P227) e Library of Congress (P244);
2. legge l'anno di morte scritto nei loro cataloghi (lobid.org per GND, id.loc.gov per LoC);
3. confronta con l'anno di Wikidata e scrive nell'autore:
   "verifica": {"esito": "verificato" | "discorde" | "una_fonte", "fonti": {"wikidata": 1956, "gnd": 1956, "loc": 1956}}
   - verificato: almeno un'altra fonte e tutte uguali a Wikidata
   - discorde: almeno una fonte dà un anno diverso -> il sito lo segnala "da verificare"
   - una_fonte: le biblioteche non hanno l'autore o non scrivono la data
4. da Wikidata prende anche gli illustratori (P110) delle opere dell'autore, con il loro anno di morte:
   "illustratori": [{"opera": "...", "nome": "...", "morte": 1976}]  (le illustrazioni hanno diritti propri).

Le risposte delle biblioteche restano in data/cache_verifica.json e si richiedono di nuovo solo dopo 180 giorni.
Se una fonte non risponde, l'autore resta con le fonti che ci sono: niente si blocca.
"""
import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
DATA = RADICE / "data"
CACHE = DATA / "cache_verifica.json"
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
RINFRESCA = 180
BUDGET_MINUTI = 40


def get(url, accept="application/json", tentativi=3):
    for t in range(tentativi):
        try:
            req = urllib.request.Request(url, headers={**UA, "Accept": accept})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return None
        except Exception:
            pass
        time.sleep(3 * (t + 1))
    raise RuntimeError("non risponde: " + url)


def sparql(q):
    u = "https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(q)
    return json.loads(get(u, "application/sparql-results+json"))["results"]["bindings"]


def val(r, k):
    return r[k]["value"] if k in r else None


def anno(s):
    m = re.search(r"-?\d{4}", s or "")
    return int(m.group(0)) if m else None


def codici_e_illustratori(qids):
    cod, ill = {}, {}
    for i in range(0, len(qids), 80):
        valori = " ".join("wd:" + q for q in qids[i:i + 80])
        for r in sparql(f"""SELECT ?a ?gnd ?loc WHERE {{ VALUES ?a {{ {valori} }}
            OPTIONAL {{ ?a wdt:P227 ?gnd }} OPTIONAL {{ ?a wdt:P244 ?loc }} }}"""):
            q = val(r, "a").rsplit("/", 1)[-1]
            c = cod.setdefault(q, {})
            if val(r, "gnd"): c.setdefault("gnd", val(r, "gnd"))
            if val(r, "loc"): c.setdefault("loc", val(r, "loc"))
        time.sleep(1)
        for r in sparql(f"""SELECT ?a ?wLabel ?iLabel ?morte ?sl WHERE {{ VALUES ?a {{ {valori} }}
            ?w wdt:P50 ?a; wdt:P110 ?i; wikibase:sitelinks ?sl. FILTER(?i != ?a)
            OPTIONAL {{ ?i wdt:P570 ?morte }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "it,en,mul". }} }}"""):
            q = val(r, "a").rsplit("/", 1)[-1]
            nome, opera = val(r, "iLabel"), val(r, "wLabel")
            if re.fullmatch(r"Q\d+", nome or "") or re.fullmatch(r"Q\d+", opera or ""):
                continue
            ill.setdefault(q, []).append({"opera": opera, "nome": nome, "morte": anno(val(r, "morte")), "sl": int(val(r, "sl"))})
        time.sleep(1)
    for q, lista in ill.items():
        visti, pulita = set(), []
        for x in sorted(lista, key=lambda x: -x["sl"]):
            k = (x["opera"], x["nome"])
            if k in visti:
                continue
            visti.add(k)
            pulita.append({"opera": x["opera"], "nome": x["nome"], "morte": x["morte"]})
        ill[q] = pulita[:6]
    return cod, ill


def morte_gnd(codice):
    t = get("https://lobid.org/gnd/" + urllib.parse.quote(codice) + ".json")
    if t is None:
        return None
    d = json.loads(t).get("dateOfDeath") or []
    return anno(d[0]) if d else None


def morte_loc(codice):
    t = get("https://id.loc.gov/authorities/names/" + urllib.parse.quote(codice) + ".json")
    if t is None:
        return None
    etichette = []
    io = "http://id.loc.gov/authorities/names/" + codice
    for nodo in json.loads(t):
        if nodo.get("@id") != io:          # il file contiene anche altre schede collegate: solo quella dell'autore
            continue
        for v in nodo.get("http://www.loc.gov/mads/rdf/v1#authoritativeLabel", []):
            etichette.append(v.get("@value", "") if isinstance(v, dict) else str(v))
    for e in etichette:
        m = re.search(r"(\d{4})\??-(\d{4})", e)   # «Brecht, Bertolt, 1898-1956»
        if m:
            return int(m.group(2))
    return None


def main():
    inizio = time.time()
    oggi = dt.date.today()
    try:
        cache = json.load(open(CACHE, encoding="utf-8"))
    except Exception:
        cache = {"gnd": {}, "loc": {}}
    if cache.get("versione_loc") != 2:   # la prima lettura LoC prendeva anche schede collegate: si rilegge
        cache["loc"], cache["versione_loc"] = {}, 2
    file = [f for f in sorted(DATA.glob("*[0-9][0-9][0-9][0-9].json")) if not f.name.startswith(("us-", "anniversari-"))]
    pacchetti = {f: json.load(open(f, encoding="utf-8")) for f in file}
    qids = sorted({a["wikidata"] for p in pacchetti.values() for a in p["autori"] if a.get("letterario")})
    print("autori da verificare:", len(qids))
    cod, ill = codici_e_illustratori(qids)

    fonti = {"gnd": morte_gnd, "loc": morte_loc}
    esauriti = False
    for q in qids:
        for nome_f, leggi in fonti.items():
            c = cod.get(q, {}).get(nome_f)
            if not c:
                continue
            vecchio = cache[nome_f].get(c)
            if vecchio and (oggi - dt.date.fromisoformat(vecchio["controllato"])).days < RINFRESCA:
                continue
            if time.time() - inizio > BUDGET_MINUTI * 60:
                esauriti = True
                continue
            try:
                cache[nome_f][c] = {"morte": leggi(c), "controllato": oggi.isoformat()}
            except Exception as e:
                print(nome_f, c, "non letto:", e)
            time.sleep(0.2)

    conta = {"verificato": 0, "discorde": 0, "una_fonte": 0}
    for f, p in pacchetti.items():
        for a in p["autori"]:
            if not a.get("letterario"):
                continue
            q = a["wikidata"]
            fv = {"wikidata": anno(a.get("morte"))}
            for nome_f in fonti:
                c = cod.get(q, {}).get(nome_f)
                y = (cache[nome_f].get(c) or {}).get("morte") if c else None
                if y:
                    fv[nome_f] = y
            altre = [y for k, y in fv.items() if k != "wikidata"]
            if not altre:
                esito = "una_fonte"
            elif all(y == fv["wikidata"] for y in altre):
                esito = "verificato"
            else:
                esito = "discorde"
            a["verifica"] = {"esito": esito, "fonti": fv}
            conta[esito] += 1
            if ill.get(q):
                a["illustratori"] = ill[q]
            else:
                a.pop("illustratori", None)
        f.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    n_ill = len({a["wikidata"] for p in pacchetti.values() for a in p["autori"] if a.get("illustratori")})
    print("autori con illustratori noti:", n_ill)
    print("esiti (per file, un autore può contare più volte):", conta, "| tempo finito prima del termine:" if esauriti else "")
    discordi = sorted({(a["nome"], json.dumps(a["verifica"]["fonti"])) for p in pacchetti.values() for a in p["autori"]
                       if (a.get("verifica") or {}).get("esito") == "discorde"})
    for n, fv in discordi[:40]:
        print("  DISCORDE:", n, fv)


if __name__ == "__main__":
    sys.exit(main())
