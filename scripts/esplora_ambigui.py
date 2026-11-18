#!/usr/bin/env python3
"""Analisi esplorativa (18/11/2026): 20 autori «ambigui» in SBN estratti a caso. Non cambia le regole né il sito.

Per ogni autore si rifà il riconoscimento (stesse regole di produzione, solo per leggere le schede candidate)
e si raccolgono titoli da fonti la cui identità è GIÀ verificata, cioè collegate all'autore da un codice in
Wikidata, mai da una ricerca per nome:
  - Wikidata: opere con autore = lui (P50);
  - Wikipedia: le pagine collegate all'elemento Wikidata (testo della voce);
  - BnF: notizie collegate al codice BnF (P268), SRU author2bib;
  - BNE: notizie collegate al codice BNE (P950), SRU authority_id;
  - GND/DNB: notizie collegate al codice GND (P227), tramite lobid.org;
  - Open Library: opere collegate al codice Open Library (P648).
Per ogni scheda SBN candidata si leggono titoli, lingua e anni di pubblicazione.
Gli anni fuori dalla vita dell'autore si SEGNALANO soltanto (possono essere date sbagliate o ristampe):
nessuna scheda si esclude per questo. Il giudizio finale si dà a mano, con la prova concreta.
Scrive docs/esplora-ambigui/prove.json.
"""
import json
import pathlib
import random
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import riconosci_sbn  # noqa: E402
import sbn  # noqa: E402
from arricchisci import sparql  # noqa: E402

RADICE = pathlib.Path(__file__).resolve().parent.parent
D = RADICE / "docs" / "esplora-ambigui"
SEME = 20261118
UA = "publicdomain-radar/1.0 (https://github.com/mnovali90-byte/publicdomain)"


def scarica(url, tentativi=3, json_=False):
    for t in range(tentativi):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json" if json_ else "*/*"})
            testo = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
            time.sleep(1)
            return json.loads(testo) if json_ else testo
        except Exception as e:
            ultimo = e
            time.sleep(3 * (t + 1))
    return {"errore": str(ultimo)[:100]}


def autori_noti():
    out = {}
    for f in sorted((RADICE / "data").glob("*[0-9][0-9][0-9][0-9].json")):
        if not f.name.startswith(("us-", "anniversari-")):
            d = json.loads(f.read_text(encoding="utf-8"))
            for a in d.get("autori", []):
                out.setdefault(a["wikidata"], a)
    return out


def wikidata(q):
    r = sparql(f"""SELECT ?p396 ?viaf ?ps ?al ?bnf ?bne ?gnd ?ol ?art WHERE {{
      OPTIONAL {{ wd:{q} wdt:P396 ?p396 }} OPTIONAL {{ wd:{q} wdt:P214 ?viaf }} OPTIONAL {{ wd:{q} wdt:P742 ?ps }}
      OPTIONAL {{ wd:{q} skos:altLabel ?al FILTER(LANG(?al) IN ("it","en")) }}
      OPTIONAL {{ wd:{q} wdt:P268 ?bnf }} OPTIONAL {{ wd:{q} wdt:P950 ?bne }} OPTIONAL {{ wd:{q} wdt:P227 ?gnd }}
      OPTIONAL {{ wd:{q} wdt:P648 ?ol }} OPTIONAL {{ ?art schema:about wd:{q} ; schema:isPartOf ?w . FILTER(CONTAINS(STR(?w), "wikipedia.org")) }} }}""")
    out = {k: set() for k in ("p396", "viaf", "ps", "al", "bnf", "bne", "gnd", "ol", "art")}
    for b in r:
        for k in out:
            if k in b:
                out[k].add(b[k]["value"])
    time.sleep(1)
    opere = sparql(f"""SELECT DISTINCT ?l WHERE {{ ?w wdt:P50 wd:{q} . ?w rdfs:label ?l .
      FILTER(LANG(?l) IN ("it","en","fr","de","es","cs","ca","pl","pt","mul")) }} LIMIT 300""")
    time.sleep(1)
    return {k: sorted(v) for k, v in out.items()}, sorted({x["l"]["value"] for x in opere})


def wikipedia(url):
    """Testo della voce (wikitesto) di una pagina collegata all'elemento Wikidata: titoli in corsivo ed elenchi."""
    m = re.match(r"https://([a-z\-]+)\.wikipedia\.org/wiki/(.+)", url)
    if not m:
        return []
    api = f"https://{m.group(1)}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "parse", "page": urllib.parse.unquote(m.group(2)), "prop": "wikitext", "format": "json", "formatversion": "2"})
    d = scarica(api, json_=True)
    testo = (d.get("parse") or {}).get("wikitext", "") if isinstance(d, dict) else ""
    titoli = re.findall(r"''+([^'\n]{3,120}?)''+", testo)
    righe = [re.sub(r"[\[\]{}|'*#]", "", r).strip() for r in re.findall(r"^\*+([^\n]{3,200})$", testo, re.M)]
    return list(dict.fromkeys(titoli + righe))[:150]


def bnf(codice):
    rid = re.sub(r"\D", "", codice or "")[:8]
    if len(rid) != 8:
        return []
    url = "https://catalogue.bnf.fr/api/SRU?" + urllib.parse.urlencode({"version": "1.2", "operation": "searchRetrieve",
          "query": f'bib.author2bib all "{rid}"', "recordSchema": "dublincore", "maximumRecords": "50"})
    t = scarica(url)
    return list(dict.fromkeys(re.sub(r"\s*/.*$", "", x).strip() for x in re.findall(r"<dc:title>([^<]+)</dc:title>", t if isinstance(t, str) else "")))


def bne(codice):
    if not re.fullmatch(r"[A-Za-z0-9]+", codice or ""):
        return []
    url = "https://catalogo.bne.es/view/sru/34BNE_INST?" + urllib.parse.urlencode({"version": "1.2", "operation": "searchRetrieve",
          "query": f"alma.authority_id={codice}", "recordSchema": "marcxml", "maximumRecords": "50"})
    t = scarica(url)
    return list(dict.fromkeys(x.strip(" /:") for x in re.findall(r'tag="245"[^>]*>\s*<subfield code="a">([^<]+)<', t if isinstance(t, str) else "")))


def gnd(codice):
    url = "https://lobid.org/resources/search?" + urllib.parse.urlencode(
        {"q": f'contribution.agent.id:"https://d-nb.info/gnd/{codice}"', "format": "json", "size": "50"})
    d = scarica(url, json_=True)
    return list(dict.fromkeys(x.get("title", "") for x in (d.get("member") or []) if isinstance(d, dict) and x.get("title")))


def openlibrary(codice):
    d = scarica(f"https://openlibrary.org/authors/{codice}/works.json?limit=100", json_=True)
    return list(dict.fromkeys(x.get("title", "") for x in (d.get("entries") or []) if isinstance(d, dict)))


def scheda_sbn(uri):
    r = sbn.interroga(f"SELECT DISTINCT ?t ?d ?l ?ruolo WHERE {{ ?w <{sbn.BF}contribution> ?c . ?c <{sbn.BF}agent> <{uri}> . "
                      f"?w <{sbn.BF}title> ?tt . ?tt <{sbn.BF}mainTitle> ?t . "
                      f"OPTIONAL {{ ?c <{sbn.BF}role> ?ruolo }} OPTIONAL {{ ?w <{sbn.BF}language> ?lg . ?lg <{sbn.VAL}> ?l }} "
                      f"OPTIONAL {{ ?w <{sbn.BF}hasInstance> ?i . ?i <{sbn.BF}provisionActivity> ?pa . ?pa <{sbn.BF}date> ?d }} }} LIMIT 80")
    time.sleep(sbn.PAUSA)
    out = {}
    for x in r:
        t = x["t"]["value"][:120]
        e = out.setdefault(t, {"anni": set(), "lingue": set(), "ruoli": set()})
        if "d" in x:
            e["anni"].add(x["d"]["value"])
        if "l" in x:
            e["lingue"].add(x["l"]["value"].rsplit("/", 1)[-1])
        if "ruolo" in x:
            e["ruoli"].add(x["ruolo"]["value"].rsplit("/", 1)[-1])
    return {t: {k: sorted(v) for k, v in e.items()} for t, e in out.items()}


def anni_fuori(scheda, nato, morto):
    """Solo segnalazione: anni di pubblicazione prima della nascita (o prima dei 10 anni). Le date dopo la morte
    sono normali (ristampe, traduzioni) e non si segnalano."""
    fuori = []
    for t, e in scheda.items():
        for a in e["anni"]:
            m = re.match(r"^(\d{4})$", a)
            if m and nato and int(m.group(1)) < nato + 10:
                fuori.append(f"{t} ({a})")
    return fuori


def main():
    D.mkdir(parents=True, exist_ok=True)
    cache = json.loads((RADICE / "data" / "cache_sbn.json").read_text(encoding="utf-8"))
    autori = autori_noti()
    ambigui = sorted(q for q, v in cache.items() if v.get("v") == 7 and (v.get("riconoscimento") or v.get("stato")) == "ambiguo" and q in autori)
    scelti = random.Random(SEME).sample(ambigui, 20)
    out = {"seme": SEME, "popolazione_ambigui": len(ambigui), "autori": []}
    for n, q in enumerate(scelti, 1):
        a = autori[q]
        w, opere = wikidata(q)
        nato = int(str(a.get("nascita"))[:4]) if str(a.get("nascita") or "")[:4].isdigit() else None
        morto = int(str(a.get("morte"))[:4]) if str(a.get("morte") or "")[:4].isdigit() else None
        r = riconosci_sbn.riconosci({"nome": a["nome"], "nascita": a.get("nascita"), "morte": a.get("morte"), "paesi": a.get("paesi") or [],
                                     "p396": w["p396"], "viaf": w["viaf"], "alias": w["ps"] + w["al"], "opere": opere})
        fonti = {"wikidata_opere": opere,
                 "wikipedia": {u: wikipedia(u) for u in w["art"][:4]},
                 "bnf": {c: bnf(c) for c in w["bnf"][:1]},
                 "bne": {c: bne(c) for c in w["bne"][:1]},
                 "gnd": {c: gnd(c) for c in w["gnd"][:1]},
                 "openlibrary": {c: openlibrary(c) for c in w["ol"][:1]}}
        cand = {}
        for u, l in (r.get("ambigue") or {}).items():
            s = scheda_sbn(u)
            confronti = {}
            for nome_f, v in fonti.items():
                lista = v if isinstance(v, list) else [t for x in v.values() for t in x]
                t = riconosci_sbn.titolo_torna(list(s), lista)
                if t:
                    confronti[nome_f] = t
            cand[u.rsplit("/", 1)[-1]] = {"etichetta": l, "titoli": s, "titoli_che_tornano": confronti,
                                          "anni_prima_della_nascita": anni_fuori(s, nato, morto)}
        out["autori"].append({"n": n, "qid": q, "nome": a["nome"], "nascita": a.get("nascita"), "morte": a.get("morte"),
                              "paesi": a.get("paesi"), "codici": {k: w[k] for k in ("bnf", "bne", "gnd", "ol", "viaf")},
                              "wikipedia": w["art"], "stato_oggi": r["stato"], "candidati": cand,
                              "fonti_quanti_titoli": {k: (len(v) if isinstance(v, list) else {c: len(x) for c, x in v.items()}) for k, v in fonti.items()},
                              "fonti": fonti})
        print(n, a["nome"], r["stato"], {k: v["titoli_che_tornano"] for k, v in cand.items()}, flush=True)
    (D / "prove.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
