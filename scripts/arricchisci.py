#!/usr/bin/env python3
"""Arricchisce gli autori letterari con biografia, opere, popolarità.

Legge data/<anno>.json (prodotto da aggiorna.py) e per gli autori con una qualifica
letteraria precisa (romanziere, poeta, drammaturgo, saggista) aggiunge:

  bio            prime frasi della pagina Wikipedia (it, altrimenti en), con link alla fonte
  opere          opere principali da Wikidata (titolo, anno)
  generi         generi delle opere da Wikidata
  visite_12m     visite alla pagina Wikipedia negli ultimi 12 mesi (it + en)
  gutenberg      download dei libri su Project Gutenberg (se l'autore c'è)
  indice         popolarità 0-100 (60% visite, 20% pagine Wikimedia, 20% Gutenberg)

Fonti: Wikidata (CC0), Wikipedia e API Wikimedia, Gutendex/Project Gutenberg.
Niente è scritto a memoria: se un dato non si trova, il campo resta vuoto.
Una cache in data/cache_arricchimento.json evita di ripetere richieste recenti.
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "PublicDomainTool/0.1 (https://github.com/mnovali90-byte/publicdomain)"
DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
CACHE = DATA_DIR / "cache_arricchimento.json"
SPARQL = "https://query.wikidata.org/sparql"
LETTERARI = {"romanziere", "poeta", "drammaturgo", "saggista"}
TIPO_CATALOGO = {"drammaturgo": "Teatro", "poeta": "Poesia", "romanziere": "Romanzo", "saggista": "Saggi"}
VALIDITA_GIORNI = 20      # una voce in cache più recente di così non viene riscaricata
PAUSA = 0.25              # secondi tra una richiesta e l'altra
PESI = {"visite": 0.6, "pagine": 0.2, "gutenberg": 0.2}


# ---------------------------------------------------------------- rete

def http_json(url, tentativi=4, accetta_404=True):
    """Scarica un JSON. 404 -> None. Altri errori: riprova, poi solleva."""
    ultimo = None
    for t in range(tentativi):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404 and accetta_404:
                return None
            ultimo = e
            attesa = int(e.headers.get("Retry-After", 0) or 0) or 5 * (t + 1)
        except Exception as e:
            ultimo = e
            attesa = 5 * (t + 1)
        time.sleep(attesa)
    raise RuntimeError(f"{url[:120]} -> {ultimo}")


def sparql(query):
    url = SPARQL + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    return http_json(url, tentativi=4, accetta_404=False)["results"]["bindings"]


# ---------------------------------------------------------------- Wikidata

def titoli_wikipedia(codici):
    """{codice: {'it': titolo, 'en': titolo}} per un gruppo di autori."""
    valori = " ".join("wd:" + c for c in codici)
    q = f"""
SELECT ?a ?it ?en WHERE {{
  VALUES ?a {{ {valori} }}
  OPTIONAL {{ ?pit schema:about ?a ; schema:isPartOf <https://it.wikipedia.org/> ; schema:name ?it }}
  OPTIONAL {{ ?pen schema:about ?a ; schema:isPartOf <https://en.wikipedia.org/> ; schema:name ?en }}
}}"""
    out = {}
    for r in sparql(q):
        c = r["a"]["value"].rsplit("/", 1)[-1]
        out[c] = {"it": r.get("it", {}).get("value"), "en": r.get("en", {}).get("value")}
    return out


def opere_wikidata(codici):
    """{codice: [opere]}: opere collegate all'autore (autore di, opera notevole)."""
    valori = " ".join("wd:" + c for c in codici)
    q = f"""
SELECT ?a ?o ?oLabel ?data ?sl ?genereLabel ?notevole WHERE {{
  VALUES ?a {{ {valori} }}
  {{ ?o wdt:P50 ?a }} UNION {{ ?a wdt:P800 ?o }}
  ?o wikibase:sitelinks ?sl .
  FILTER NOT EXISTS {{ ?o wdt:P31 wd:Q13442814 }}
  OPTIONAL {{ ?o wdt:P577 ?data }}
  OPTIONAL {{ ?o wdt:P136 ?genere }}
  OPTIONAL {{ ?a wdt:P800 ?o . BIND(true AS ?notevole) }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "it,en,mul,de,fr,es". }}
}}"""
    per_autore = {}
    for r in sparql(q):
        a = r["a"]["value"].rsplit("/", 1)[-1]
        o = r["o"]["value"].rsplit("/", 1)[-1]
        titolo = r.get("oLabel", {}).get("value", "")
        if not titolo or re.fullmatch(r"Q\d+", titolo):
            continue
        d = per_autore.setdefault(a, {}).setdefault(o, {
            "titolo": titolo, "anno": None, "sl": int(r["sl"]["value"]),
            "notevole": False, "generi": set(),
        })
        anno = r.get("data", {}).get("value", "")[:4]
        if anno.isdigit() and (d["anno"] is None or int(anno) < d["anno"]):
            d["anno"] = int(anno)
        if r.get("notevole"):
            d["notevole"] = True
        g = r.get("genereLabel", {}).get("value")
        if g and not re.fullmatch(r"Q\d+", g):
            d["generi"].add(g)
    return {a: list(opere.values()) for a, opere in per_autore.items()}


def riassumi_opere(lista, massimo=8):
    """Opere principali (notevoli prima, poi più diffuse) e generi più frequenti."""
    if not lista:
        return {"opere": [], "n_opere": 0, "generi": []}
    ordinate = sorted(lista, key=lambda x: (not x["notevole"], -x["sl"], x["titolo"]))
    conteggio = {}
    for o in lista:
        for g in o["generi"]:
            conteggio[g] = conteggio.get(g, 0) + 1
    generi = [g for g, _ in sorted(conteggio.items(), key=lambda kv: (-kv[1], kv[0]))[:4]]
    return {
        "opere": [{"titolo": o["titolo"], "anno": o["anno"]} for o in ordinate[:massimo]],
        "n_opere": len(lista),
        "generi": generi,
    }


# ---------------------------------------------------------------- Wikipedia

def accorcia(testo, massimo=480):
    """Taglia a fine frase, senza superare 'massimo' caratteri."""
    testo = re.sub(r"\s+", " ", testo).strip()
    if len(testo) <= massimo:
        return testo
    frasi = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý«\"'])", testo)
    out = ""
    for f in frasi:
        if out and len(out) + len(f) + 1 > massimo:
            break
        out = (out + " " + f).strip()
    return out if len(out) <= massimo + 120 else out[:massimo].rsplit(" ", 1)[0] + "…"


def biografia(titoli):
    """Riassunto da Wikipedia: italiano se esiste, altrimenti inglese."""
    for lingua in ("it", "en"):
        t = titoli.get(lingua)
        if not t:
            continue
        url = f"https://{lingua}.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(t.replace(" ", "_"), safe="")
        dati = http_json(url)
        time.sleep(PAUSA)
        if dati and dati.get("extract"):
            pagina = dati.get("content_urls", {}).get("desktop", {}).get("page") or \
                f"https://{lingua}.wikipedia.org/wiki/" + urllib.parse.quote(t.replace(" ", "_"))
            return {"bio": accorcia(dati["extract"]), "bio_url": pagina, "bio_lingua": lingua}
    return {}


def mesi_da_considerare(oggi=None):
    """Primo e ultimo giorno dei 12 mesi completi che precedono il mese in corso."""
    oggi = oggi or dt.date.today()
    fine = oggi.replace(day=1) - dt.timedelta(days=1)
    anno, mese = fine.year - 1, fine.month + 1
    if mese == 13:
        anno, mese = fine.year, 1
    inizio = dt.date(anno, mese, 1)
    return inizio.strftime("%Y%m%d") + "00", fine.strftime("%Y%m%d") + "00"


def visite_12_mesi(titoli, oggi=None):
    inizio, fine = mesi_da_considerare(oggi)
    totale, trovato = 0, False
    for lingua in ("it", "en"):
        t = titoli.get(lingua)
        if not t:
            continue
        titolo = urllib.parse.quote(t.replace(" ", "_"), safe="")
        url = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{lingua}.wikipedia/"
               f"all-access/user/{titolo}/monthly/{inizio}/{fine}")
        dati = http_json(url)
        time.sleep(PAUSA)
        if dati and dati.get("items"):
            totale += sum(int(i["views"]) for i in dati["items"])
            trovato = True
    return totale if trovato else None


# ---------------------------------------------------------------- Gutenberg

def _parole(nome):
    return {p for p in re.split(r"[\s,.\-']+", nome.lower()) if len(p) > 2}


def gutenberg_download(nome, anno_morte):
    """Download totali dei libri di Project Gutenberg dell'autore, riconosciuto
    dal nome e dall'anno di morte. Nessun risultato sicuro -> None."""
    url = "https://gutendex.com/books/?" + urllib.parse.urlencode({"search": nome})
    totale, trovato, pagine = 0, False, 0
    mie = _parole(nome)
    while url and pagine < 3:
        dati = http_json(url)
        time.sleep(PAUSA)
        if not dati:
            break
        for libro in dati.get("results", []):
            for au in libro.get("authors", []):
                if au.get("death_year") == anno_morte and len(mie & _parole(au.get("name", ""))) >= 2:
                    totale += int(libro.get("download_count", 0))
                    trovato = True
                    break
        url = dati.get("next")
        pagine += 1
    return totale if trovato else None


# ---------------------------------------------------------------- indice

def percentile(valore, tutti):
    sotto = sum(1 for v in tutti if v < valore)
    uguali = sum(1 for v in tutti if v == valore)
    return (sotto + 0.5 * uguali) / len(tutti)


def calcola_indici(autori):
    """Indice 0-100: media pesata dei piazzamenti (percentili) nelle componenti disponibili.
    Una componente mancante non pesa come zero: i pesi si ridistribuiscono sulle altre."""
    comp = {
        "visite": [a["visite_12m"] for a in autori if a.get("visite_12m") is not None],
        "pagine": [a["pagine_wikipedia"] for a in autori],
        "gutenberg": [a["gutenberg"] for a in autori if a.get("gutenberg") is not None],
    }
    for a in autori:
        pesi, somma = 0.0, 0.0
        for nome, valori in comp.items():
            campo = {"visite": "visite_12m", "pagine": "pagine_wikipedia", "gutenberg": "gutenberg"}[nome]
            v = a.get(campo)
            if v is None or not valori:
                continue
            somma += PESI[nome] * percentile(v, valori)
            pesi += PESI[nome]
        a["indice"] = round(100 * somma / pesi) if pesi else 0


# ---------------------------------------------------------------- principale

def carica_cache():
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


def e_recente(voce, oggi):
    try:
        return (oggi - dt.date.fromisoformat(voce["ts"])).days < VALIDITA_GIORNI
    except Exception:
        return False


def arricchisci_gruppo(gruppo, cache, oggi):
    """Scarica i dati di un gruppo di autori (max ~25) e li mette in cache."""
    codici = [a["wikidata"] for a in gruppo]
    titoli = titoli_wikipedia(codici)
    time.sleep(2)
    opere = opere_wikidata(codici)
    time.sleep(2)
    for a in gruppo:
        c = a["wikidata"]
        t = titoli.get(c, {})
        voce = {"ts": oggi.isoformat()}
        voce.update(riassumi_opere(opere.get(c, [])))
        try:
            voce.update(biografia(t))
        except Exception as e:
            print(f"  bio non riuscita per {a['nome']}: {e}", file=sys.stderr)
        try:
            voce["visite_12m"] = visite_12_mesi(t, oggi)
        except Exception as e:
            print(f"  visite non riuscite per {a['nome']}: {e}", file=sys.stderr)
        try:
            voce["gutenberg"] = gutenberg_download(a["nome"], int(a["morte"][:4]))
        except Exception as e:
            print(f"  gutenberg non riuscito per {a['nome']}: {e}", file=sys.stderr)
        cache[c] = voce


def elabora_anno(percorso, cache, oggi):
    pacchetto = json.loads(percorso.read_text(encoding="utf-8"))
    letterari = [a for a in pacchetto["autori"] if LETTERARI & set(a["professioni"])]
    da_fare = [a for a in letterari if not (a["wikidata"] in cache and e_recente(cache[a["wikidata"]], oggi))]
    print(f"{percorso.name}: {len(letterari)} letterari, {len(da_fare)} da scaricare", file=sys.stderr)
    for i in range(0, len(da_fare), 25):
        gruppo = da_fare[i:i + 25]
        print(f"  gruppo {i // 25 + 1}/{(len(da_fare) + 24) // 25}", file=sys.stderr)
        arricchisci_gruppo(gruppo, cache, oggi)
    id_letterari = {x["wikidata"] for x in letterari}
    for a in pacchetto["autori"]:
        if a["wikidata"] in id_letterari:
            a["letterario"] = True
            a["tipo_catalogo"] = [TIPO_CATALOGO[p] for p in a["professioni"] if p in TIPO_CATALOGO]
            voce = cache.get(a["wikidata"], {})
            for k in ("bio", "bio_url", "bio_lingua", "opere", "n_opere", "generi", "visite_12m", "gutenberg"):
                if voce.get(k) not in (None, [], ""):
                    a[k] = voce[k]
            a.setdefault("n_opere", 0)
    calcola_indici([a for a in pacchetto["autori"] if a.get("letterario")])
    pacchetto["letterari"] = len(letterari)
    pacchetto["arricchito"] = oggi.isoformat()
    pacchetto["indice_formula"] = "60% visite Wikipedia (12 mesi), 20% pagine Wikimedia, 20% download Project Gutenberg"
    return pacchetto, letterari


def controlla_qualita(letterari, cache):
    """Se quasi nulla è stato trovato, qualcosa non va: meglio un errore chiaro."""
    if len(letterari) < 20:
        return
    voci = [cache.get(a["wikidata"], {}) for a in letterari]
    con_bio = sum(1 for v in voci if v.get("bio"))
    con_visite = sum(1 for v in voci if v.get("visite_12m") is not None)
    print(f"  qualità: bio {con_bio}/{len(voci)}, visite {con_visite}/{len(voci)}", file=sys.stderr)
    if con_bio < 0.2 * len(voci) or con_visite < 0.2 * len(voci):
        raise RuntimeError("Troppi dati mancanti: le fonti non rispondono come previsto.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--anno", type=int, help="solo questo anno di liberazione")
    a = p.parse_args()
    oggi = dt.date.today()
    cache = carica_cache()
    file = sorted(DATA_DIR.glob("[0-9][0-9][0-9][0-9].json"))
    if a.anno:
        file = [f for f in file if f.stem == str(a.anno)]
    if not file:
        sys.exit("Nessun file in data/: lancia prima scripts/aggiorna.py")
    risultati = []
    for f in file:
        pacchetto, letterari = elabora_anno(f, cache, oggi)
        controlla_qualita(letterari, cache)
        risultati.append((f, pacchetto))
    # scrive solo a fine lavoro e solo se i controlli sono passati
    for f, pacchetto in risultati:
        f.write_text(json.dumps(pacchetto, ensure_ascii=False, indent=1), encoding="utf-8")
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    print("Arricchimento completato.")


if __name__ == "__main__":
    main()
