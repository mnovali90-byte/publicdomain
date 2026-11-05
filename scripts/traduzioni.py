#!/usr/bin/env python3
"""
Controlla, con Open Library, in quali lingue esistono le opere di ciascun autore.

Per ogni autore (i più noti di ogni anno) fa UNA richiesta a Open Library, cerca le
sue opere (le più pubblicate per prime) e conta in quante esistono edizioni in
italiano, inglese, spagnolo, francese, tedesco.

Il risultato è un'indicazione, non un verdetto:
  - "esiste almeno un'edizione" non dice se la traduzione è buona o recente;
  - Open Library non conosce tutte le edizioni: zero può voler dire "non registrata";
  - il nome è l'unico aggancio, quindi si accettano solo opere il cui autore
    ha esattamente quel nome (gli omonimi vengono scartati).

Scrive, per ogni autore, il campo "traduzioni" nei file data/<anno>.json:
  {"opere": N, "con_lingua": N, "per_lingua": {"it": n, "en": n, ...},
   "parziale": bool, "fonte": "Open Library", "ts": "AAAA-MM-GG"}

Cache in data/cache_traduzioni.json (una voce vale 45 giorni).

Seconda fonte, per l'italiano: Google Libri (API Volumes), cercando per TITOLO ITALIANO
dell'opera (preso da Wikidata) e cognome dell'autore. Cercare per autore non funziona:
Google mostra prima i libri in inglese. Per ogni autore si controllano le 3 opere più
note (quelle con più pagine Wikimedia) e si contano le edizioni con lingua = italiano.
Scrive "google_it" dentro "traduzioni":
  {"opere_controllate": k, "opere_con_edizione": j, "edizioni": n, "ultimo": anno|None,
   "per_opera": [{"titolo", "n", "ultimo"}], "fonte": "Google Libri"}
Cache in data/cache_google.json (45 giorni). La chiave gratuita è nella variabile
GOOGLE_BOOKS_KEY (segreto del repository). Il limite gratuito è circa 1000 richieste al
giorno: ogni giro ne fa al massimo GB_MAX_RICHIESTE e il resto arriva al giro dopo.
"""
import concurrent.futures
import datetime as dt
import json
import os
import pathlib
import re
import sys
import time
import unicodedata
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from arricchisci import http_json  # noqa: E402  (stessa gestione di errori e tentativi)

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
CACHE = DATA_DIR / "cache_traduzioni.json"
VALIDITA_GIORNI = 45
PER_ANNO = int(os.environ.get("TRADUZIONI_PER_ANNO", "300"))   # quanti autori per anno
LAVORATORI = 2
PAUSA = 1.0               # secondi tra due richieste dello stesso lavoratore (cortesia verso Open Library)
BUDGET_MINUTI = float(os.environ.get("BUDGET_MINUTI_TRAD", "40"))
FINE_LAVORO = time.time() + BUDGET_MINUTI * 60
LIMITE = 100              # opere lette per autore
LINGUE = {"ita": "it", "eng": "en", "spa": "es", "fre": "fr", "ger": "de"}   # codici MARC usati da Open Library
URL = "https://openlibrary.org/search.json?"


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", s.lower()).split()


def stesso_autore(nome, nomi_trovati):
    """Il nome cercato e uno dei nomi dell'opera devono avere le stesse parole (ordine libero)."""
    voluto = sorted(norm(nome))
    return any(sorted(norm(n)) == voluto for n in nomi_trovati or [])


def conta_lingue(nome, risposta):
    """Dalla risposta di Open Library: quante opere dell'autore, e in quante lingue."""
    docs = [d for d in (risposta or {}).get("docs", []) if stesso_autore(nome, d.get("author_name"))]
    per_lingua = {v: 0 for v in LINGUE.values()}
    con_lingua = 0
    for d in docs:
        lingue = set(d.get("language") or [])
        if lingue:
            con_lingua += 1
        for marc, breve in LINGUE.items():
            if marc in lingue:
                per_lingua[breve] += 1
    return {
        "opere": len(docs),
        "con_lingua": con_lingua,
        "per_lingua": per_lingua,
        "parziale": int((risposta or {}).get("numFound", 0)) > LIMITE,
        "fonte": "Open Library",
    }


GB_URL = "https://www.googleapis.com/books/v1/volumes?"
GB_CACHE = DATA_DIR / "cache_google.json"
GB_CHIAVE = os.environ.get("GOOGLE_BOOKS_KEY", "")
GB_PAUSA = 0.4 if GB_CHIAVE else 1.5
GB_OPERE = 3
GB_MAX_RICHIESTE = int(os.environ.get("GB_MAX_RICHIESTE", "350"))


def cognome(nome):
    p = norm(nome)
    return p[-1] if p else ""


def conta_google_opera(nome, risposta):
    """Edizioni in italiano trovate per un'opera: lingua = it e il cognome dell'autore tra gli autori."""
    voluto = cognome(nome)
    n, anni = 0, []
    for it in (risposta or {}).get("items") or []:
        v = it.get("volumeInfo") or {}
        if v.get("language") != "it":
            continue
        if not any(voluto in norm(a) for a in v.get("authors") or []):
            continue
        n += 1
        m = re.match(r"(\d{4})", str(v.get("publishedDate") or ""))
        if m:
            anni.append(int(m.group(1)))
    return n, (max(anni) if anni else None)


def opere_da_controllare(a):
    viste, out = set(), []
    for o in sorted(a.get("opere") or [], key=lambda o: -(o.get("sl") or 0)):
        t = (o.get("titolo") or "").strip()
        if not t or re.fullmatch(r"Q\d+", t) or " ".join(norm(t)) in viste:
            continue
        viste.add(" ".join(norm(t)))
        out.append(t)
        if len(out) == GB_OPERE:
            break
    return out


def interroga_google(a, http=None):
    """Un autore: una richiesta per ognuna delle sue opere più note."""
    http = http or http_json
    per_opera = []
    for t in opere_da_controllare(a):
        q = {"q": f'intitle:"{t}" inauthor:{cognome(a["nome"])}', "maxResults": 20}
        if GB_CHIAVE:
            q["key"] = GB_CHIAVE
        r = http(GB_URL + urllib.parse.urlencode(q), tentativi=3)
        time.sleep(GB_PAUSA)
        n, ultimo = conta_google_opera(a["nome"], r)
        per_opera.append({"titolo": t, "n": n, "ultimo": ultimo})
    anni = [x["ultimo"] for x in per_opera if x["ultimo"]]
    return {"opere_controllate": len(per_opera), "opere_con_edizione": sum(1 for x in per_opera if x["n"]),
            "edizioni": sum(x["n"] for x in per_opera), "ultimo": max(anni) if anni else None,
            "per_opera": per_opera, "fonte": "Google Libri"}


def elabora_google(oggi, pacchetti, interroga_fn=None):
    """Google Libri, in sequenza. Si ferma al limite di richieste o ai primi errori ripetuti."""
    interroga_fn = interroga_fn or interroga_google
    cache = json.loads(GB_CACHE.read_text(encoding="utf-8")) if GB_CACHE.exists() else {}
    da_fare = []
    for _, p in pacchetti:
        da_fare += [a for a in candidati(p) if a.get("opere") and not e_recente(cache.get(a["wikidata"]), oggi)]
    print(f"google libri: {len(da_fare)} autori da controllare", file=sys.stderr)
    fatti = errori = richieste = 0
    for a in da_fare:
        if time.time() > FINE_LAVORO or richieste >= GB_MAX_RICHIESTE:
            print("  limite del giro raggiunto: il resto al prossimo giro", file=sys.stderr)
            break
        try:
            voce = interroga_fn(a)
            richieste += voce["opere_controllate"]
            voce["ts"] = oggi.isoformat()
            cache[a["wikidata"]] = voce
            fatti += 1
        except Exception as e:
            errori += 1
            print(f"  {a['nome']}: {e}", file=sys.stderr)
            if errori >= 5 and fatti < errori:
                print("  Google Libri non risponde (limite di richieste?): mi fermo, i dati già presi restano.", file=sys.stderr)
                break
        if fatti % 20 == 19:
            GB_CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    GB_CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    print(f"google libri: {fatti} nuovi, {errori} errori, {richieste} richieste, {len(cache)} in cache", file=sys.stderr)
    return cache


def interroga(nome):
    q = URL + urllib.parse.urlencode({
        "author": nome, "limit": LIMITE, "sort": "editions",
        "fields": "key,title,language,author_name,first_publish_year,edition_count",
    })
    r = http_json(q)
    time.sleep(PAUSA)
    return conta_lingue(nome, r)


def e_recente(voce, oggi):
    try:
        return (oggi - dt.date.fromisoformat(voce["ts"])).days < VALIDITA_GIORNI
    except Exception:
        return False


def carica_cache():
    return json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}


def salva_cache(cache):
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def candidati(pacchetto):
    """I più noti dell'anno: prima per indice di popolarità (se c'è), poi per pagine Wikimedia."""
    lista = [a for a in pacchetto["autori"] if a.get("letterario") and a.get("n_opere", 1) > 0 and not re.fullmatch(r"Q\d+", a["nome"])]
    lista.sort(key=lambda a: (-(a.get("indice") if a.get("indice") is not None else -1), -a.get("pagine_wikipedia", 0)))
    return lista[:PER_ANNO]


def elabora(oggi, interroga_fn=interroga):
    cache = carica_cache()
    file = sorted(DATA_DIR.glob("[0-9][0-9][0-9][0-9].json"))
    pacchetti = [(f, json.loads(f.read_text(encoding="utf-8"))) for f in file]
    da_fare = []
    for _, p in pacchetti:
        da_fare += [a for a in candidati(p) if not e_recente(cache.get(a["wikidata"]), oggi)]
    print(f"traduzioni: {len(da_fare)} autori da controllare", file=sys.stderr)
    errori = fatti = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=LAVORATORI) as ex:
        for i in range(0, len(da_fare), 20):
            if time.time() > FINE_LAVORO:
                print("  tempo finito: il resto al prossimo giro", file=sys.stderr)
                break
            gruppo = da_fare[i:i + 20]
            futuri = {a["wikidata"]: (a, ex.submit(interroga_fn, a["nome"])) for a in gruppo}
            for c, (a, f) in futuri.items():
                try:
                    voce = f.result()
                    voce["ts"] = oggi.isoformat()
                    cache[c] = voce
                    fatti += 1
                except Exception as e:
                    errori += 1
                    print(f"  {a['nome']}: {e}", file=sys.stderr)
            salva_cache(cache)
    if fatti + errori >= 10 and errori > fatti:
        raise RuntimeError("Open Library non risponde come previsto: non scrivo nulla.")
    gb = elabora_google(oggi, pacchetti)
    ci_sono = 0
    for f, p in pacchetti:
        for a in p["autori"]:
            voce = cache.get(a["wikidata"])
            if voce:
                a["traduzioni"] = {k: v for k, v in voce.items()}
                ci_sono += 1
            g = gb.get(a["wikidata"])
            if g:
                a.setdefault("traduzioni", {})["google_it"] = {k: v for k, v in g.items() if k != "ts"}
        p["traduzioni_aggiornato"] = oggi.isoformat()
        f.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
    salva_cache(cache)
    print(f"traduzioni: {ci_sono} autori con dati ({fatti} nuovi, {errori} errori)", file=sys.stderr)


if __name__ == "__main__":
    elabora(dt.date.today())
