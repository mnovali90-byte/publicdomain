"""Dati per la pagina "Storico" di Public Domain Radar: opere già in pubblico dominio negli USA
(pubblicate fino al 1930, cioè 95 anni compiuti), ordinate per interesse della settimana.

Fonti aperte: Wikidata (opere, autori, anno di prima pubblicazione), Wikipedia (visite),
Wikimedia Commons non serve qui. Regola USA: l'anno di pubblicazione + 95 anni.

Scrive in data/storico/:
  opere.json      tutte le opere, con visite della settimana (Wikipedia en + it)
  autori.json     elenco autori per la barra di ricerca (nome, anno di morte, numero di opere)
  playlist.json   le playlist: più letti, per autore ("This is..."), per genere, per lingua, per anno
Una sola regola: si elencano solo opere con anno di prima pubblicazione CERTO su Wikidata.
Se l'aggiornamento si interrompe, le visite non rinfrescate restano quelle della settimana prima.

Si lancia a mano o dalla GitHub Action .github/workflows/storico.yml (ogni lunedì).
"""
import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from opere import CLASSI, GENERI, get, lingua_genere, qid, sparql, val  # noqa: E402

UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
ANNO_DA = int(os.environ.get("STORICO_ANNO_DA", 1900))
ANNO_A = int(os.environ.get("STORICO_ANNO_A", date.today().year - 96))   # 2026 -> 1930
MIN_PAGINE = 3          # lingue con una pagina Wikipedia: taglia le opere sconosciute
MAX_PER_ANNO = 150
BUDGET_MINUTI = float(os.environ.get("BUDGET_MINUTI_STORICO", 60))
USCITA = "data/storico"


def opere_anno(anno_pub):
    classi = " ".join("wd:" + c for c in CLASSI)
    q = f'''SELECT ?w ?wLabel ?wit ?a ?aLabel ?morte ?sl ?en ?itw WHERE {{
      VALUES ?c {{ {classi} }}
      ?w wdt:P31 ?c; wdt:P577 ?d. FILTER(YEAR(?d)={anno_pub})
      ?w wikibase:sitelinks ?sl. FILTER(?sl>={MIN_PAGINE})
      OPTIONAL {{ ?w wdt:P50 ?a. OPTIONAL {{ ?a wdt:P570 ?morte }} }}
      OPTIONAL {{ ?w rdfs:label ?wit FILTER(LANG(?wit)="it") }}
      OPTIONAL {{ ?en schema:about ?w; schema:isPartOf <https://en.wikipedia.org/> }}
      OPTIONAL {{ ?itw schema:about ?w; schema:isPartOf <https://it.wikipedia.org/> }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,it,mul". }} }}'''
    out = {}
    for r in sparql(q):
        k = qid(val(r, "w"))
        o = out.setdefault(k, {"qid": k, "titolo": val(r, "wLabel"), "titolo_it": val(r, "wit"), "anno": anno_pub,
                               "autori": {}, "pagine": int(val(r, "sl")), "wiki_en": None, "wiki_it": None})
        if val(r, "a"):
            a = o["autori"].setdefault(qid(val(r, "a")), {"nome": val(r, "aLabel"), "morte": None})
            if val(r, "morte") and not a["morte"]:
                m = re.match(r"-?(\d{4})", val(r, "morte"))
                a["morte"] = int(m.group(1)) if m else None
        if val(r, "en") and not o["wiki_en"]: o["wiki_en"] = val(r, "en")
        if val(r, "itw") and not o["wiki_it"]: o["wiki_it"] = val(r, "itw")
    res = []
    for o in out.values():
        if re.fullmatch(r"Q\d+", o["titolo"] or ""):
            continue  # senza etichetta leggibile
        o["autori"] = [{"qid": a, "nome": d["nome"], "morte": d["morte"]} for a, d in o["autori"].items()
                       if not re.fullmatch(r"Q\d+", d["nome"] or "")]
        res.append(o)
    res.sort(key=lambda o: -o["pagine"])
    return res[:MAX_PER_ANNO]


def finestra():
    """Gli ultimi 7 giorni completi per cui Wikimedia ha già i dati (di solito si fermano a ieri)."""
    fine = date.today() - timedelta(days=2)
    return fine - timedelta(days=6), fine


def visite_settimana(wiki, url, ini, fine):
    """Visite (persone, non robot) in 7 giorni alla pagina Wikipedia. 0 se la pagina non ha visite; None se errore."""
    if not url:
        return None
    t = urllib.parse.unquote(url.rsplit("/", 1)[-1])
    u = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{wiki}.wikipedia/all-access/user/"
         + urllib.parse.quote(t, safe="") + "/daily/" + ini.strftime("%Y%m%d") + "/" + fine.strftime("%Y%m%d"))
    for tentativo in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30) as r:
                return sum(i["views"] for i in json.load(r).get("items", []))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 0
        except Exception:
            pass
        time.sleep(3 * (tentativo + 1))
    return None


def chiave_genere(o):
    return o.get("generi") or []


def costruisci_playlist(ops):
    def top(lista, n):
        return [o["qid"] for o in sorted(lista, key=lambda o: (-o["visite_sett"], -o["pagine"]))[:n]]

    per_autore = {}
    for o in ops:
        for a in o["autori"]:
            per_autore.setdefault(a["qid"], {"nome": a["nome"], "opere": []})["opere"].append(o)
    autori = []
    for k, a in per_autore.items():
        if len(a["opere"]) < 3:
            continue
        autori.append({"qid": k, "nome": a["nome"], "visite_sett": sum(o["visite_sett"] for o in a["opere"]),
                       "opere": top(a["opere"], 30)})
    autori.sort(key=lambda a: -a["visite_sett"])

    generi, lingue, anni = {}, {}, {}
    for o in ops:
        for g in chiave_genere(o):
            generi.setdefault(g, []).append(o)
        if o.get("lingua"):
            lingue.setdefault(o["lingua"]["en"], []).append(o)
        anni.setdefault(str(o["anno"]), []).append(o)
    def gruppi(d, minimo, n=30):
        r = [{"chiave": k, "n": len(v), "opere": top(v, n)} for k, v in d.items() if len(v) >= minimo]
        return sorted(r, key=lambda g: -g["n"])
    return {"piu_letti": top(ops, 50), "autori": autori[:40],
            "generi": gruppi(generi, 5), "lingue": gruppi(lingue, 5), "anni": gruppi(anni, 1, 20)}


def main():
    inizio = time.time()
    os.makedirs(USCITA, exist_ok=True)
    precedenti = {}
    try:
        precedenti = {o["qid"]: o for o in json.load(open(f"{USCITA}/opere.json", encoding="utf8"))["opere"]}
    except Exception:
        pass
    ini, fine = finestra()
    ops = []
    for anno in range(ANNO_DA, ANNO_A + 1):
        lista = opere_anno(anno)
        print(anno, "opere:", len(lista), flush=True)
        if lista:
            lg = lingua_genere(anno, {o["qid"] for o in lista})
            for o in lista:
                x = lg.get(o["qid"], {})
                if x.get("lingua"): o["lingua"] = x["lingua"]
                o["generi"] = x.get("generi", [])
        ops += lista
    if len(ops) < 500:
        print("troppe poche opere trovate (%d): non tocco i file" % len(ops)); sys.exit(1)

    esaurito = False
    ops.sort(key=lambda o: -o["pagine"])  # le più note per prime: se il tempo finisce, mancano le meno note
    for o in ops:
        if time.time() - inizio > BUDGET_MINUTI * 60:
            esaurito = True
        vecchio = precedenti.get(o["qid"], {})
        if esaurito:
            o["visite_en"], o["visite_it"] = vecchio.get("visite_en"), vecchio.get("visite_it")
        else:
            o["visite_en"] = visite_settimana("en", o["wiki_en"], ini, fine)
            o["visite_it"] = visite_settimana("it", o["wiki_it"], ini, fine)
            time.sleep(0.05)
        o["visite_sett"] = (o["visite_en"] or 0) + (o["visite_it"] or 0)
    ops.sort(key=lambda o: (-o["visite_sett"], -o["pagine"]))

    agg = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    meta = {"aggiornato": agg, "settimana": [ini.isoformat(), fine.isoformat()], "interrotto_per_tempo": esaurito,
            "regola": f"USA: opere pubblicate fino al {ANNO_A} (95 anni compiuti)",
            "fonte": "Wikidata (CC0), Wikipedia (visite)", "copertura":
            f"solo opere con anno di prima pubblicazione su Wikidata e almeno {MIN_PAGINE} pagine Wikipedia, "
            f"al massimo {MAX_PER_ANNO} per anno"}
    json.dump({**meta, "opere": ops}, open(f"{USCITA}/opere.json", "w", encoding="utf8"), ensure_ascii=False)

    autori = {}
    for o in ops:
        for a in o["autori"]:
            x = autori.setdefault(a["qid"], {"qid": a["qid"], "nome": a["nome"], "morte": a["morte"], "n_opere": 0, "visite_sett": 0})
            x["n_opere"] += 1
            x["visite_sett"] += o["visite_sett"]
    json.dump({**meta, "autori": sorted(autori.values(), key=lambda a: -a["visite_sett"])},
              open(f"{USCITA}/autori.json", "w", encoding="utf8"), ensure_ascii=False)
    json.dump({**meta, **costruisci_playlist(ops)}, open(f"{USCITA}/playlist.json", "w", encoding="utf8"), ensure_ascii=False)
    print("scritte", len(ops), "opere,", len(autori), "autori; visite aggiornate:", not esaurito)


if __name__ == "__main__":
    main()
