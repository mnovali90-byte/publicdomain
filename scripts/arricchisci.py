#!/usr/bin/env python3
"""Arricchisce gli autori letterari con biografia, opere, popolarità.

Legge data/<anno>.json (prodotto da aggiorna.py) e per gli autori con una qualifica
letteraria precisa (romanziere, poeta, drammaturgo, saggista) aggiunge:

  bio            prime frasi della pagina Wikipedia (it, altrimenti en), con link alla fonte
  opere          opere principali da Wikidata (titolo, anno)
  generi         generi delle opere da Wikidata
  visite_it/en   visite alla pagina Wikipedia italiana / inglese negli ultimi 12 mesi (0 = nessuna pagina)
  visite_12m     somma delle due
  gutenberg      download dei libri su Project Gutenberg (se l'autore c'è)
  indice_it/en/int  tre misure 0-100 rispetto alla lista dell'anno: visite it, visite en, lingue con una pagina
  indice         vecchia media pesata, non più usata dal sito
  foto           ritratto da Wikimedia Commons con licenza e autore (se esiste)
  paesi, lingue  cittadinanza e lingue dell'autore da Wikidata

Fonti: Wikidata (CC0), Wikipedia e API Wikimedia, Gutendex/Project Gutenberg.
Niente è scritto a memoria: se un dato non si trova, il campo resta vuoto.
Una cache in data/cache_arricchimento.json evita di ripetere richieste recenti.
"""
import argparse
import concurrent.futures
import os
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
LINGUE_VISITE = ("it", "en", "es", "de", "fr")   # lingue di Wikipedia di cui si contano le visite
PAUSA = 0.25              # secondi tra una richiesta e l'altra (per ciascun lavoratore)
LAVORATORI = 5            # autori elaborati in parallelo
BUDGET_MINUTI = float(os.environ.get("BUDGET_MINUTI", "100"))   # oltre questo tempo si salva e si riprende al giro dopo
FLAG_INCOMPLETO = pathlib.Path(".incompleto")
FINE_LAVORO = time.time() + BUDGET_MINUTI * 60
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

def dati_base(codici):
    """Per un gruppo di autori: titoli delle pagine Wikipedia, immagine di Commons,
    paesi di cittadinanza, lingue. {codice: {...}}"""
    valori = " ".join("wd:" + c for c in codici)
    q = f"""
SELECT ?a ?it ?en ?es ?de ?fr ?img ?paeseLabel ?linguaLabel WHERE {{
  VALUES ?a {{ {valori} }}
  OPTIONAL {{ ?pit schema:about ?a ; schema:isPartOf <https://it.wikipedia.org/> ; schema:name ?it }}
  OPTIONAL {{ ?pen schema:about ?a ; schema:isPartOf <https://en.wikipedia.org/> ; schema:name ?en }}
  OPTIONAL {{ ?pes schema:about ?a ; schema:isPartOf <https://es.wikipedia.org/> ; schema:name ?es }}
  OPTIONAL {{ ?pde schema:about ?a ; schema:isPartOf <https://de.wikipedia.org/> ; schema:name ?de }}
  OPTIONAL {{ ?pfr schema:about ?a ; schema:isPartOf <https://fr.wikipedia.org/> ; schema:name ?fr }}
  OPTIONAL {{ ?a wdt:P18 ?img }}
  OPTIONAL {{ ?a wdt:P27 ?paese }}
  OPTIONAL {{ ?a (wdt:P103|wdt:P1412) ?lingua }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "it,en,mul". }}
}}"""
    out = {}
    for r in sparql(q):
        c = r["a"]["value"].rsplit("/", 1)[-1]
        d = out.setdefault(c, {"titoli": {}, "img": None, "paesi": [], "lingue": []})
        d["titoli"] = {l: r.get(l, {}).get("value") or d["titoli"].get(l) for l in LINGUE_VISITE}
        if r.get("img") and not d["img"]:
            d["img"] = urllib.parse.unquote(r["img"]["value"].rsplit("/", 1)[-1])
        for chiave, campo in (("paesi", "paeseLabel"), ("lingue", "linguaLabel")):
            v = r.get(campo, {}).get("value")
            if v and not re.fullmatch(r"Q\d+", v) and v not in d[chiave]:
                d[chiave].append(v)
    return out


def foto_commons(nome_file):
    """Ritratto da Wikimedia Commons con licenza e autore, oppure None."""
    api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "titles": "File:" + nome_file, "prop": "imageinfo", "format": "json",
        "formatversion": "2", "iiprop": "extmetadata",
        "iiextmetadatafilter": "LicenseShortName|Artist",
    })
    dati = http_json(api)
    time.sleep(PAUSA)
    try:
        meta = dati["query"]["pages"][0]["imageinfo"][0]["extmetadata"]
    except (TypeError, KeyError, IndexError):
        return None
    licenza = meta.get("LicenseShortName", {}).get("value", "").strip()
    if not licenza:
        return None
    autore = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", ""))
    autore = re.sub(r"\s+", " ", autore).strip()[:120]
    nome = urllib.parse.quote(nome_file.replace(" ", "_"))
    return {
        "url": f"https://commons.wikimedia.org/wiki/Special:FilePath/{nome}?width=800",
        "pagina": f"https://commons.wikimedia.org/wiki/File:{nome}",
        "licenza": licenza,
        "autore": autore,
    }


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
        "opere": [{"titolo": o["titolo"], "anno": o["anno"], "generi": sorted(o["generi"]), "sl": o["sl"]}
                  for o in ordinate[:massimo]],
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


def riassunto(lingua, titolo):
    """Riassunto di una pagina Wikipedia nella lingua data, o None."""
    url = f"https://{lingua}.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(titolo.replace(" ", "_"), safe="")
    dati = http_json(url)
    time.sleep(PAUSA)
    if dati and dati.get("extract"):
        pagina = dati.get("content_urls", {}).get("desktop", {}).get("page") or \
            f"https://{lingua}.wikipedia.org/wiki/" + urllib.parse.quote(titolo.replace(" ", "_"))
        return {"testo": accorcia(dati["extract"]), "url": pagina}
    return None


def biografie(titoli, bios=None):
    """Biografia in italiano e in inglese (quelle che esistono). Non rifà quelle già in mano."""
    bios = dict(bios or {})
    for lingua in ("it", "en"):
        if lingua in bios or not titoli.get(lingua):
            continue
        r = riassunto(lingua, titoli[lingua])
        if r:
            bios[lingua] = r
    return bios


def biografia(titoli):
    """Compatibilità: una sola biografia, italiano se esiste altrimenti inglese."""
    bios = biografie(titoli)
    for lingua in ("it", "en"):
        if lingua in bios:
            return {"bio": bios[lingua]["testo"], "bio_url": bios[lingua]["url"], "bio_lingua": lingua}
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


def visite_per_lingua(titoli, oggi=None, lingue=LINGUE_VISITE):
    """Visite agli ultimi 12 mesi, separate per lingua di Wikipedia: {"it": n, "en": n, ...}.
    0 = l'autore non ha una pagina in quella lingua; None = la pagina c'è ma il dato non è arrivato."""
    inizio, fine = mesi_da_considerare(oggi)
    out = {}
    for lingua in lingue:
        t = titoli.get(lingua)
        if not t:
            out[lingua] = 0
            continue
        titolo = urllib.parse.quote(t.replace(" ", "_"), safe="")
        url = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{lingua}.wikipedia/"
               f"all-access/user/{titolo}/monthly/{inizio}/{fine}")
        dati = http_json(url)
        time.sleep(PAUSA)
        out[lingua] = sum(int(i["views"]) for i in dati["items"]) if dati and dati.get("items") else None
    return out


def visite_12_mesi(titoli, oggi=None):
    """Somma it + en (resta per compatibilità con i dati già salvati)."""
    v = visite_per_lingua(titoli, oggi, ("it", "en"))
    noti = [x for x in v.values() if x is not None]
    return sum(noti) if noti else None


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


def _percentili(autori, campo, chiave):
    """Posizione 0-100 di ogni autore rispetto agli altri della lista, su UN solo dato.
    Chi ha 0 (nessuna pagina in quella lingua) prende 0; chi non ha il dato non prende nulla."""
    valori = [a[campo] for a in autori if a.get(campo) is not None]
    for a in autori:
        a.pop(chiave, None)
        v = a.get(campo)
        if v is None or not valori:
            continue
        a[chiave] = 0 if v == 0 else round(100 * percentile(v, valori))


def calcola_indici(autori):
    """Tre misure separate, ciascuna su un solo dato (0-100 rispetto alla lista dell'anno):
      indice_it   visite alla pagina Wikipedia italiana (12 mesi)
      indice_en   visite alla pagina Wikipedia inglese (12 mesi)
      indice_int  in quante lingue esiste una pagina Wikimedia sull'autore
    Più "indice": la vecchia media pesata (60% visite it+en, 20% pagine, 20% Gutenberg), tenuta
    solo per i dati vecchi: il sito non la usa più quando ci sono le tre misure."""
    _percentili(autori, "visite_it", "indice_it")
    _percentili(autori, "visite_en", "indice_en")
    for l in ("es", "de", "fr"):
        _percentili(autori, "visite_" + l, "indice_" + l)
    _percentili(autori, "pagine_wikipedia", "indice_int")
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


VERSIONE_CACHE = 2   # 2 = opere con generi, foto, paesi, lingue


def da_aggiornare(voce, oggi):
    """True se mancano dati nuovi (versione vecchia) o se la voce è scaduta."""
    return (voce is None or voce.get("v", 1) < VERSIONE_CACHE or not e_recente(voce, oggi)
            or voce.get("bios_v") != 2        # biografie in italiano e inglese ancora da completare
            or voce.get("visite_v") != 3)     # visite ancora da separare per lingua (3 = anche es, de, fr)


def _autore(a, b, opere_a, vecchia, oggi):
    """Tutti i dati di un autore. Gira in un lavoratore parallelo: non tocca la cache."""
    serve_pesante = not e_recente(vecchia, oggi)
    voce = dict(vecchia)
    voce.update(riassumi_opere(opere_a))
    voce["paesi"], voce["lingue"], voce["titoli"] = b["paesi"], b["lingue"], b["titoli"]
    voce.pop("foto", None)
    if b["img"]:
        try:
            foto = foto_commons(b["img"])
            if foto:
                voce["foto"] = foto
        except Exception as e:
            print(f"  foto non riuscita per {a['nome']}: {e}", file=sys.stderr)
    voce["v"] = VERSIONE_CACHE
    # biografie in italiano e inglese: complete se mancano, rifatte se la parte pesante è scaduta
    if serve_pesante or voce.get("bios_v") != 2:
        bios = {} if serve_pesante else dict(voce.get("bios") or {})
        if not bios and voce.get("bio") and not serve_pesante:   # voce vecchia: una sola biografia
            bios[voce.get("bio_lingua") or "it"] = {"testo": voce["bio"], "url": voce.get("bio_url")}
        try:
            bios = biografie(b["titoli"], bios)
        except Exception as e:
            print(f"  bio non riuscita per {a['nome']}: {e}", file=sys.stderr)
        if bios:
            voce["bios"] = bios
            pref = "it" if "it" in bios else "en"
            voce["bio"], voce["bio_url"], voce["bio_lingua"] = bios[pref]["testo"], bios[pref]["url"], pref
        voce["bios_v"] = 2
    if serve_pesante or voce.get("visite_v") != 3:
        # se le visite it/en sono già in mano (versione 2) si scaricano solo le lingue che mancano
        gia = {} if serve_pesante or voce.get("visite_v") != 2 else {l: voce.get("visite_" + l) for l in ("it", "en") if voce.get("visite_" + l) is not None}
        try:
            v = dict(gia)
            v.update(visite_per_lingua(b["titoli"], oggi, tuple(l for l in LINGUE_VISITE if l not in gia)))
            for l in LINGUE_VISITE:
                voce["visite_" + l] = v[l]
            noti = [v[l] for l in ("it", "en") if v[l] is not None]
            voce["visite_12m"] = sum(noti) if noti else None
            voce["visite_v"] = 3     # un 404 (nessun dato) non si ripete ogni volta; un errore di rete solleva e riprova al giro dopo
        except Exception as e:
            print(f"  visite non riuscite per {a['nome']}: {e}", file=sys.stderr)
    if serve_pesante:
        try:
            voce["gutenberg"] = gutenberg_download(a["nome"], int(a["morte"][:4]))
        except Exception as e:
            print(f"  gutenberg non riuscito per {a['nome']}: {e}", file=sys.stderr)
        voce["ts"] = oggi.isoformat()
    return voce


def arricchisci_gruppo(gruppo, cache, oggi):
    """Scarica i dati di un gruppo di autori (max ~25) e li mette in cache.
    Parte leggera (opere, foto, paesi, lingue): sempre. Parte pesante (biografia,
    visite, Gutenberg): solo se la voce è nuova o scaduta. Gli autori del gruppo
    sono elaborati in parallelo."""
    codici = [a["wikidata"] for a in gruppo]
    base = dati_base(codici)
    time.sleep(2)
    opere = opere_wikidata(codici)
    time.sleep(2)
    vuota = {"titoli": {}, "img": None, "paesi": [], "lingue": []}
    with concurrent.futures.ThreadPoolExecutor(max_workers=LAVORATORI) as ex:
        futuri = {a["wikidata"]: ex.submit(_autore, a, base.get(a["wikidata"], vuota),
                                           opere.get(a["wikidata"], []), cache.get(a["wikidata"]) or {}, oggi)
                  for a in gruppo}
        for c, f in futuri.items():
            cache[c] = f.result()


def salva_cache(cache):
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def elabora_anno(percorso, cache, oggi):
    pacchetto = json.loads(percorso.read_text(encoding="utf-8"))
    letterari = [a for a in pacchetto["autori"] if LETTERARI & set(a["professioni"])]
    da_fare = [a for a in letterari if da_aggiornare(cache.get(a["wikidata"]), oggi)]
    print(f"{percorso.name}: {len(letterari)} letterari, {len(da_fare)} da scaricare", file=sys.stderr)
    da_fare.sort(key=lambda a: -a.get("pagine_wikipedia", 0))   # i più noti per primi
    for i in range(0, len(da_fare), 25):
        if time.time() > FINE_LAVORO:
            print("  tempo a disposizione finito: salvo e riprendo al prossimo giro", file=sys.stderr)
            FLAG_INCOMPLETO.write_text("1")
            break
        gruppo = da_fare[i:i + 25]
        print(f"  gruppo {i // 25 + 1}/{(len(da_fare) + 24) // 25}", file=sys.stderr)
        arricchisci_gruppo(gruppo, cache, oggi)
        salva_cache(cache)
    id_letterari = {x["wikidata"] for x in letterari}
    for a in pacchetto["autori"]:
        if a["wikidata"] in id_letterari:
            a["letterario"] = True
            a["tipo_catalogo"] = [TIPO_CATALOGO[p] for p in a["professioni"] if p in TIPO_CATALOGO]
            voce = cache.get(a["wikidata"], {})
            for k in ("bio", "bio_url", "bio_lingua", "bios", "opere", "n_opere", "generi", "visite_12m", "visite_it", "visite_en",
                      "visite_es", "visite_de", "visite_fr", "gutenberg", "foto", "paesi", "lingue"):
                if voce.get(k) not in (None, [], ""):
                    a[k] = voce[k]
            if voce:
                a.setdefault("n_opere", 0)
    calcola_indici([a for a in pacchetto["autori"] if a.get("letterario") and "n_opere" in a])
    pacchetto["letterari"] = len(letterari)
    for chiave, campo in (("paesi", "paesi"), ("lingue", "lingue")):
        conteggio = {}
        for a in pacchetto["autori"]:
            if a.get("letterario") and a.get("n_opere", 0) > 0:
                for v in a.get(campo, []):
                    conteggio[v] = conteggio.get(v, 0) + 1
        pacchetto[chiave] = [{"nome": k, "n": n} for k, n in sorted(conteggio.items(), key=lambda kv: (-kv[1], kv[0]))]
    pacchetto["arricchito"] = oggi.isoformat()
    pacchetto["indice_formula"] = "tre misure separate: visite Wikipedia it, visite Wikipedia en, numero di lingue con una pagina; ciascuna 0-100 rispetto alla lista dell'anno"
    return pacchetto, letterari


def controlla_qualita(letterari, cache):
    """Se quasi nulla è stato trovato, qualcosa non va: meglio un errore chiaro."""
    voci = [cache[a["wikidata"]] for a in letterari if a["wikidata"] in cache]
    if len(voci) < 20:
        return
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
    if FLAG_INCOMPLETO.exists():
        FLAG_INCOMPLETO.unlink()
    file = [f for f in sorted(DATA_DIR.glob("*[0-9][0-9][0-9][0-9].json")) if not f.name.startswith(("us-", "anniversari-"))]
    if a.anno:
        file = [f for f in file if f.stem.endswith(str(a.anno))]
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
    salva_cache(cache)
    print("Arricchimento " + ("INCOMPLETO: continua al prossimo giro." if FLAG_INCOMPLETO.exists() else "completato."))


if __name__ == "__main__":
    main()
