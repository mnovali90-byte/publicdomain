"""Seconda fonte per gli USA nello Storico: i libri delle pagine «Public Domain Day» della Duke (19/11/2026).

Perché: il confronto con la Duke (registro, 19/11/2026) ha trovato 15 libri importanti su 114 che Wikidata non
dà come opere con un anno di pubblicazione (Now We Are Six, Private Lives, Desire Under the Elms...).

Fonte: Center for the Study of the Public Domain, Duke Law School, pagine annuali
https://web.law.duke.edu/cspd/publicdomainday/<anno>/ (CC BY 4.0). Ogni pagina elenca, nella sezione «Books», libri
pubblicati 96 anni prima che entrano nel pubblico dominio USA il 1° gennaio di quell'anno. Ogni riga è
«Autore, Titolo (note)»: il titolo è la parte in corsivo.

Per ogni libro si cerca l'opera in Wikidata (titolo inglese o alias uguale, e un autore con lo stesso cognome).
- trovata e già nello Storico: se lo Storico non ha l'anno, prende quello della Duke; se ce l'ha diverso, si annota
  «anno_duke» (la pagina lo mostrerà come data da verificare);
- trovata ma non nello Storico: entra con l'anno della Duke;
- non trovata: entra lo stesso, con titolo, autore e anno della Duke, senza codice Wikidata.
L'anno della Duke vale solo per gli USA: per l'Europa servono gli anni di morte, che si leggono da Wikidata se c'è.
"""
import html, json, re, sys, time, urllib.parse
from datetime import date

import urllib.request

from opere import qid, sparql, val

UA = {"User-Agent": "PublicDomainTool/0.1 (https://github.com/mnovali90-byte/publicdomain)"}

CARTELLA = "data/storico"
PRIMO_ANNO = 2019          # il primo anno con opere nuove dopo il blocco del 1998


def _pagina(anno):
    for u in (f"https://web.law.duke.edu/cspd/publicdomainday/{anno}/", f"https://cspd.law.duke.edu/publicdomainday/{anno}/"):
        try:     # la pagina è HTML: opere.get legge solo JSON (primo giro del 19/11 finito vuoto per questo)
            return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read().decode("utf-8", "replace")
        except Exception as e:
            print(f"Duke {anno}: {u} non letta ({e})", file=sys.stderr)
    return None


def libri_anno(anno):
    """[(autore, titolo)] dalla sezione Books della pagina di quell'anno; [] se la pagina non c'è ancora."""
    t = _pagina(anno)
    if not t:
        return None
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    teste = [(m.start(), html.unescape(re.sub("<[^>]+>", "", m.group(0))).strip().lower())
             for m in re.finditer(r"<h[1-4][^>]*>.*?</h[1-4]>", t, re.S)]
    i = next((k for k, (_, h) in enumerate(teste) if h.startswith("books")), None)
    if i is None:
        return []
    fine = teste[i + 1][0] if i + 1 < len(teste) else len(t)
    out = []
    for li in re.findall(r"<li[^>]*>(.*?)</li>", t[teste[i][0]:fine], re.S):
        corsivi = re.findall(r"<(?:em|i)>(.*?)</(?:em|i)>", li, re.S)
        if not corsivi:
            continue
        testo = re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", "", li))).strip()
        titolo = re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", "", corsivi[0]))).strip(" ,.")
        autore = testo.split(",")[0].strip()
        autore = re.sub(r"\s*\(.*", "", autore)
        if titolo and autore and titolo not in autore:
            out.append((autore, titolo))
    return out


def risolvi(autore, titolo):
    """L'opera in Wikidata con quel titolo (etichetta o alias inglese) e un autore con lo stesso cognome."""
    cognome = re.sub(r"[^\w\s'-]", "", autore).split()[-1].lower() if autore.split() else ""
    t = titolo.replace('"', '\\"')
    r = sparql(f'''SELECT ?w ?wLabel ?wit ?sl ?a ?aLabel ?morte ?en ?itw WHERE {{
      {{ ?w rdfs:label "{t}"@en }} UNION {{ ?w skos:altLabel "{t}"@en }}
      ?w wdt:P50 ?a ; wikibase:sitelinks ?sl .
      {{ ?a rdfs:label ?al FILTER(LANG(?al) = "en") }} UNION {{ ?a wdt:P742 ?al }}   # anche lo pseudonimo (Ellery Queen)
      FILTER(CONTAINS(LCASE(STR(?al)), "{cognome}"))
      OPTIONAL {{ ?a wdt:P570 ?morte }}
      OPTIONAL {{ ?w rdfs:label ?wit FILTER(LANG(?wit)="it") }}
      OPTIONAL {{ ?en schema:about ?w; schema:isPartOf <https://en.wikipedia.org/> }}
      OPTIONAL {{ ?itw schema:about ?w; schema:isPartOf <https://it.wikipedia.org/> }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,mul". }} }} LIMIT 20''') or []
    if not r:
        return None
    r.sort(key=lambda x: -int(val(x, "sl") or 0))
    k = qid(val(r[0], "w"))
    autori = {}
    for x in r:
        if qid(val(x, "w")) != k:
            continue
        a = autori.setdefault(qid(val(x, "a")), {"qid": qid(val(x, "a")), "nome": val(x, "aLabel"), "morte": None})
        m = re.match(r"-?(\d{4})", val(x, "morte") or "")
        if m and (a["morte"] is None or int(m.group(1)) > a["morte"]):
            a["morte"] = int(m.group(1))
    x = r[0]
    return {"qid": k, "titolo": val(x, "wLabel"), "titolo_it": val(x, "wit"), "pagine": int(val(x, "sl") or 0),
            "wiki_en": val(x, "en"), "wiki_it": val(x, "itw"), "autori": list(autori.values())}


def carica(anno_corrente):
    """Libri della Duke dal 2019 a oggi, già cercati in Wikidata. Cache in data/storico/duke.json: le pagine degli
    anni passati non cambiano; quella dell'anno in corso si rilegge una volta al mese."""
    f = f"{CARTELLA}/duke.json"
    try:
        cache = json.load(open(f, encoding="utf8"))
    except Exception:
        cache = {}
    oggi = date.today()
    for anno in range(PRIMO_ANNO, anno_corrente + 1):
        c = cache.get(str(anno))
        if c and (anno < anno_corrente or (oggi - date.fromisoformat(c["letto"])).days < 30):
            # libri non trovati in Wikidata: si riprovano una volta con la ricerca nuova (pseudonimi, 21/11/2026)
            for v in c["libri"]:
                if not v.get("wd") and v.get("riprovato") != "pseudonimi":
                    v["wd"] = risolvi(v["autore"], v["titolo"])
                    v["riprovato"] = "pseudonimi"
                    time.sleep(1)
            continue
        libri = libri_anno(anno)
        if libri is None:
            continue
        voci = []
        for autore, titolo in libri:
            v = {"autore": autore, "titolo": titolo, "pub": anno - 96, "wd": risolvi(autore, titolo)}
            voci.append(v)
            time.sleep(1)
        cache[str(anno)] = {"letto": oggi.isoformat(), "libri": voci}
        print(f"Duke {anno}: {len(voci)} libri, {sum(1 for v in voci if v['wd'])} trovati in Wikidata")
    json.dump(cache, open(f, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    return [v for a in sorted(cache) for v in cache[a]["libri"]]


def integra(tutte, libri):
    """Aggiunge o completa le opere dello Storico con i libri della Duke (vedi la spiegazione in cima)."""
    completate = aggiunte = senza_codice = 0
    for v in libri:
        wd = v["wd"]
        if wd and wd["qid"] in tutte:
            o = tutte[wd["qid"]]
            if not o.get("anno"):
                o["anno"] = v["pub"]; completate += 1
            elif o["anno"] != v["pub"]:
                o["anno_duke"] = v["pub"]
            o["fonte_usa"] = "duke"
        elif wd:
            tutte[wd["qid"]] = {"qid": wd["qid"], "titolo": wd["titolo"] or v["titolo"], "titolo_it": wd["titolo_it"],
                                "anno": v["pub"], "autori": wd["autori"], "pagine": wd["pagine"],
                                "wiki_en": wd["wiki_en"], "wiki_it": wd["wiki_it"], "fonte_usa": "duke"}
            aggiunte += 1
        else:
            k = "duke-" + str(v["pub"]) + "-" + re.sub(r"[^a-z0-9]+", "-", v["titolo"].lower()).strip("-")[:60]
            tutte[k] = {"qid": k, "titolo": v["titolo"], "titolo_it": None, "anno": v["pub"],
                        "autori": [{"qid": "duke-a-" + re.sub(r"[^a-z0-9]+", "-", v["autore"].lower()).strip("-"), "nome": v["autore"], "morte": None}], "pagine": 0,
                        "wiki_en": None, "wiki_it": None, "fonte_usa": "duke"}
            senza_codice += 1
    print(f"Duke: {completate} anni completati, {aggiunte} opere aggiunte, {senza_codice} senza codice Wikidata")
