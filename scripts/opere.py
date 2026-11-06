"""Opere che entrano in pubblico dominio negli USA (regola: 95 anni dalla pubblicazione).
Fonti aperte: Wikidata (opere con anno di pubblicazione), Wikipedia (visite), Wikimedia Commons (immagini con licenza libera).
Scrive data/us-<anno>.json. Per l'anno X contano le opere pubblicate nell'anno X-96 (95 anni compiuti, libere dal 1 gennaio X)."""
import json, os, re, sys, time, urllib.parse, urllib.request
from datetime import date

UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
ANNI = [2027, 2028]
CLASSI = ["Q8261", "Q49084", "Q25379", "Q5185279", "Q571", "Q7725634", "Q149537"]
MIN_PAGINE = 2
MAX_OPERE = 400
LICENZE_OK = re.compile(r"^(cc0|cc[ -]by|pd|public domain|attribution)", re.I)

def get(url, tentativi=3, timeout=120):
    for t in range(tentativi):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return json.load(r)
        except Exception as e:
            print("  errore", url[:90], e, file=sys.stderr)
            time.sleep(5 * (t + 1))
    return None

def sparql(q):
    d = get("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"}))
    return d["results"]["bindings"] if d else []

def val(x, k):
    return x.get(k, {}).get("value")

def qid(u):
    return u.rsplit("/", 1)[-1] if u else None

def opere_anno(anno_pub):
    classi = " ".join("wd:" + c for c in CLASSI)
    q = f'''SELECT ?w ?wLabel ?wit ?a ?aLabel ?sl ?img ?en WHERE {{
      VALUES ?c {{ {classi} }}
      ?w wdt:P31 ?c; wdt:P577 ?d. FILTER(YEAR(?d)={anno_pub})
      ?w wikibase:sitelinks ?sl. FILTER(?sl>={MIN_PAGINE})
      OPTIONAL {{ ?w wdt:P50 ?a }} OPTIONAL {{ ?w wdt:P18 ?img }}
      OPTIONAL {{ ?w rdfs:label ?wit FILTER(LANG(?wit)="it") }}
      OPTIONAL {{ ?en schema:about ?w; schema:isPartOf <https://en.wikipedia.org/> }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,it,mul". }} }}'''
    righe = sparql(q)
    out = {}
    for r in righe:
        k = qid(val(r, "w"))
        o = out.setdefault(k, {"qid": k, "titolo": val(r, "wLabel"), "titolo_it": val(r, "wit"),
                               "autori": {}, "pagine": int(val(r, "sl")), "immagine": None, "wiki_en": None})
        if val(r, "a"): o["autori"][qid(val(r, "a"))] = val(r, "aLabel")
        if val(r, "img") and not o["immagine"]: o["immagine"] = urllib.parse.unquote(val(r, "img").rsplit("/", 1)[-1])
        if val(r, "en") and not o["wiki_en"]: o["wiki_en"] = val(r, "en")
    res = []
    for o in out.values():
        if re.fullmatch(r"Q\d+", o["titolo"] or ""): continue  # senza etichetta leggibile
        o["autori"] = [{"qid": a, "nome": n} for a, n in o["autori"].items() if not re.fullmatch(r"Q\d+", n or "")]
        res.append(o)
    return res

GENERI = [  # (parola cercata nell'etichetta inglese, chiave)
    ("crime", "giallo"), ("detective", "giallo"), ("mystery", "giallo"), ("thriller", "giallo"),
    ("horror", "horror"), ("weird", "horror"), ("gothic", "horror"),
    ("science fiction", "fantasy_sf"), ("fantasy", "fantasy_sf"), ("dystopian", "fantasy_sf"),
    ("historical", "storico"), ("children", "ragazzi"), ("poetry", "poesia"), ("poem", "poesia"),
    ("essay", "saggio"), ("memoir", "memorie"), ("autobiograph", "memorie"), ("biograph", "memorie"),
    ("satire", "satira"), ("adventure", "avventura"), ("romance", "sentimentale"), ("war", "guerra")]

def lingua_genere(anno_pub, qids):
    """Lingua originale (P407) e genere (P136) per le opere già scelte. Etichette in italiano e inglese."""
    classi = " ".join("wd:" + c for c in CLASSI)
    q = f'''SELECT ?w ?len ?lit ?gen WHERE {{
      VALUES ?c {{ {classi} }}
      ?w wdt:P31 ?c; wdt:P577 ?d. FILTER(YEAR(?d)={anno_pub})
      OPTIONAL {{ ?w wdt:P407 ?l. ?l rdfs:label ?len FILTER(LANG(?len)="en"). OPTIONAL {{ ?l rdfs:label ?lit FILTER(LANG(?lit)="it") }} }}
      OPTIONAL {{ ?w wdt:P136 ?g. ?g rdfs:label ?gen FILTER(LANG(?gen)="en") }} }}'''
    out = {}
    for r in sparql(q):
        k = qid(val(r, "w"))
        if k not in qids: continue
        o = out.setdefault(k, {"lingua": None, "generi": set()})
        if val(r, "len") and not o["lingua"]:
            en = re.sub(r"^(American|British|Australian|Canadian) ", "", val(r, "len"))
            it = val(r, "lit")
            o["lingua"] = {"en": en, "it": it or en}
        if val(r, "gen"):
            g = val(r, "gen").lower()
            for parola, chiave in GENERI:
                if parola in g: o["generi"].add(chiave); break
    for o in out.values(): o["generi"] = sorted(o["generi"])
    return out

def visite_en(titolo_url):
    t = urllib.parse.unquote(titolo_url.rsplit("/", 1)[-1])
    fine = date.today().replace(day=1)
    ini = date(fine.year - 1, fine.month, 1)
    u = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/"
         + urllib.parse.quote(t, safe="") + "/monthly/" + ini.strftime("%Y%m%d") + "/" + fine.strftime("%Y%m%d"))
    d = get(u, tentativi=2, timeout=30)
    return sum(i["views"] for i in d["items"]) if d and "items" in d else None

def immagine_libera(nome):
    """Restituisce dati dell'immagine solo se la licenza su Commons è libera."""
    u = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=extmetadata|url"
         "&iiurlwidth=400&titles=" + urllib.parse.quote("File:" + nome))
    d = get(u, tentativi=2, timeout=30)
    try:
        p = next(iter(d["query"]["pages"].values()))["imageinfo"][0]
    except Exception:
        return None
    m = p.get("extmetadata", {})
    lic = (m.get("LicenseShortName", {}).get("value") or "").strip()
    if not LICENZE_OK.match(lic) or m.get("NonFree", {}).get("value", "").lower() == "true":
        return None
    autore = re.sub(r"<[^>]+>", "", m.get("Artist", {}).get("value", "") or "").strip()
    return {"file": nome, "url": p.get("thumburl") or p.get("url"),
            "pagina": "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(nome.replace(" ", "_")),
            "licenza": lic, "autore": autore[:120]}

def main():
    os.makedirs("data", exist_ok=True)
    for anno in ANNI:
        pub = anno - 96
        print("Anno", anno, "-> opere pubblicate nel", pub)
        ops = opere_anno(pub)
        print(" trovate", len(ops))
        if len(ops) < 20:
            print(" troppo poche: lascio il file com'è"); continue
        ops.sort(key=lambda o: -o["pagine"])
        ops = ops[:MAX_OPERE]
        lg = lingua_genere(pub, {o["qid"] for o in ops})
        for o in ops:
            x = lg.get(o["qid"], {})
            if x.get("lingua"): o["lingua"] = x["lingua"]
            o["generi"] = x.get("generi", [])
        for o in ops:
            o["visite_en"] = visite_en(o["wiki_en"]) if o["wiki_en"] else None
            if o["immagine"]:
                o["copertina"] = immagine_libera(o["immagine"])
            o.pop("immagine", None)
            time.sleep(0.1)
        ops.sort(key=lambda o: (-(o["visite_en"] or 0), -o["pagine"]))
        with open(f"data/us-{anno}.json", "w", encoding="utf8") as f:
            json.dump({"anno": anno, "anno_pubblicazione": pub, "aggiornato": date.today().isoformat(),
                       "fonte": "Wikidata (CC0), Wikipedia, Wikimedia Commons", "opere": ops}, f, ensure_ascii=False, indent=1)
        print(" scritte", len(ops), "con copertina libera:", sum(1 for o in ops if o.get("copertina")))
    try:
        ind = json.load(open("data/indice.json"))
        ind["opere_us"] = ANNI
        json.dump(ind, open("data/indice.json", "w"), ensure_ascii=False)
    except Exception as e:
        print("indice non aggiornato", e)

if __name__ == "__main__":
    main()
