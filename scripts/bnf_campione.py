#!/usr/bin/env python3
"""BnF, punto 1 del piano (18/11/2026): campione di sviluppo e risultato attuale congelato. Solo lettura.

1. CONGELA il risultato attuale di bnf.py per tutti gli autori candidati (data/cache_bnf.json + codice BnF di Wikidata)
   in docs/campione-bnf/bnf-base-2026-11-18.json, prima di qualsiasi modifica.
2. SCEGLIE 60 autori di sviluppo (seme fisso): 20 trovati, 20 con codice ma zero notizie in francese, 20 senza codice.
3. RACCOGLIE LE PROVE per il controllo a mano, distinguendo gli errori tecnici (il servizio non risponde) dai risultati:
   - con codice: la scheda d'autore BnF (nome, varianti, anni, fonti) per confrontare l'identità con Wikidata;
     quante notizie sono collegate in tutte le lingue e in francese; per 30 notizie in francese: titolo, anno, lingue,
     e COME è collegato l'autore (ruolo come autore o collaboratore, oppure solo come soggetto del libro);
   - senza codice: le schede d'autore BnF con quel nome (anche senza accenti), con anni e qualche titolo in francese.
Scrive docs/campione-bnf/prove.json.
"""
import json
import pathlib
import random
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import bnf  # noqa: E402
from arricchisci import sparql  # noqa: E402

RADICE = pathlib.Path(__file__).resolve().parent.parent
D = RADICE / "docs" / "campione-bnf"
SEME = 20261118
SRU = "https://catalogue.bnf.fr/api/SRU"
UA = "publicdomain-radar/1.0 (https://github.com/mnovali90-byte/publicdomain)"


class ErroreTecnico(Exception):
    pass


def sru(query, schema="unimarcXchange", n=0):
    url = SRU + "?" + urllib.parse.urlencode({"version": "1.2", "operation": "searchRetrieve", "query": query,
                                              "recordSchema": schema, "maximumRecords": str(n)})
    ultimo = None
    for t in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            testo = urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")
            time.sleep(1)
            m = re.search(r"numberOfRecords>(\d+)<", testo)
            if not m:
                raise ValueError("risposta senza numero di risultati: " + (re.findall(r"<sd:message>([^<]+)", testo) or [testo[:80]])[0])
            return int(m.group(1)), testo
        except Exception as e:
            ultimo = e
            time.sleep(4 * (t + 1))
    raise ErroreTecnico(str(ultimo)[:150])


def record(testo):
    """Divide la risposta in notizie; per ognuna {tag: [ {codice: [valori]} ]}."""
    out = []
    for r in re.findall(r"<srw:recordData>(.*?)</srw:recordData>", testo, re.S):
        campi = {}
        for tag, corpo in re.findall(r'<(?:\w+:)?datafield[^>]*tag="(\d{3})"[^>]*>(.*?)</(?:\w+:)?datafield>', r, re.S):
            sub = {}
            for c, v in re.findall(r'<(?:\w+:)?subfield code="(\w)">([^<]*)<', corpo):
                sub.setdefault(c, []).append(v)
            campi.setdefault(tag, []).append(sub)
        for tag, v in re.findall(r'<(?:\w+:)?controlfield tag="(\d{3})">([^<]*)<', r):
            campi.setdefault(tag, []).append({"_": [v]})
        ark = re.search(r"ark:/12148/cb(\d{8}\w)", r)
        campi["_ark"] = ark.group(1) if ark else None
        out.append(campi)
    return out


def primo(campi, tag, codice):
    for f in campi.get(tag, []):
        if f.get(codice):
            return f[codice][0]
    return None


def scheda_autore(rec):
    nome = " ".join(x for x in (primo(rec, "200", "a"), primo(rec, "200", "b")) if x)
    return {"ark": rec.get("_ark"), "nome": nome, "anni": primo(rec, "200", "f") or primo(rec, "103", "a"),
            "varianti": [" ".join(f.get("a", []) + f.get("b", [])) for f in rec.get("400", [])][:8],
            "fonti": [x for f in rec.get("810", []) for x in f.get("a", [])][:5],
            "nota": [x for f in rec.get("300", []) for x in f.get("a", [])][:2]}


def notizie_collegate(rid, n=30):
    """Notizie in francese collegate al codice: titolo, anno, lingue e come è collegato l'autore."""
    tot, testo = sru(f'bib.author2bib all "{rid}" and bib.language any "fre"', n=n)
    out = []
    for rec in record(testo):
        come = []
        for tag in ("700", "701", "702", "710", "711", "712"):
            for f in rec.get(tag, []):
                if any(rid in x for x in f.get("3", [])):
                    come.append(f"{tag} ruolo {','.join(f.get('4', [])) or '?'}")
        for tag in ("600", "601", "602", "604", "605", "606", "607"):
            for f in rec.get(tag, []):
                if any(rid in x for x in f.get("3", [])):
                    come.append(f"{tag} soggetto")
        out.append({"titolo": (primo(rec, "200", "a") or "")[:110], "anno": primo(rec, "210", "d") or primo(rec, "214", "d"),
                    "lingue": [x for f in rec.get("101", []) for x in f.get("a", [])], "collegato_come": come or ["non trovato nella notizia"]})
    return tot, out


def senza_accenti(t):
    return "".join(c for c in unicodedata.normalize("NFKD", t or "") if not unicodedata.combining(c))


def candidati_nome(nome):
    parole = [re.sub(r"[^\w\-]", "", p) for p in nome.split() if len(p.strip(".")) > 1]
    if not parole:
        return []
    forme = list(dict.fromkeys([" ".join(parole), senza_accenti(" ".join(parole))]))
    trovati = {}
    for f in forme:
        tot, testo = sru(f'aut.accesspoint all "{f}"', n=15)
        for rec in record(testo):
            s = scheda_autore(rec)
            if s["ark"]:
                trovati.setdefault(s["ark"], s)
    for s in list(trovati.values())[:8]:
        rid = re.sub(r"\D", "", s["ark"])[:8]
        try:
            s["notizie_fr"], esempi = notizie_collegate(rid, n=8)
            s["titoli_fr"] = [f'{x["titolo"]} ({x["anno"]})' for x in esempi]
        except ErroreTecnico as e:
            s["errore_tecnico"] = str(e)
    return list(trovati.values())


def main():
    D.mkdir(parents=True, exist_ok=True)
    cache = json.loads((RADICE / "data" / "cache_bnf.json").read_text(encoding="utf-8"))
    autori = {}
    for f in sorted((RADICE / "data").glob("*[0-9][0-9][0-9][0-9].json")):
        if f.name.startswith(("us-", "anniversari-", "es-")):
            continue
        for a in bnf.candidati(json.loads(f.read_text(encoding="utf-8"))):
            autori.setdefault(a["wikidata"], a)
    qs = sorted(autori)
    wd = {q: {"p268": [], "viaf": [], "alias": [], "opere": []} for q in qs}
    for i in range(0, len(qs), 50):
        v = " ".join("wd:" + q for q in qs[i:i + 50])
        for b in sparql(f"""SELECT ?a ?bnf ?viaf ?al WHERE {{ VALUES ?a {{ {v} }} OPTIONAL {{ ?a wdt:P268 ?bnf }}
              OPTIONAL {{ ?a wdt:P214 ?viaf }} OPTIONAL {{ ?a skos:altLabel ?al FILTER(LANG(?al) IN ("fr","en")) }} }}"""):
            k = b["a"]["value"].rsplit("/", 1)[-1]
            for c, ch in (("bnf", "p268"), ("viaf", "viaf"), ("al", "alias")):
                if c in b and b[c]["value"] not in wd[k][ch]:
                    wd[k][ch].append(b[c]["value"])
        time.sleep(2)
    base = {"congelato": "2026-11-18", "nota": "risultato di bnf.py prima di qualsiasi modifica (fase BnF, punto 1)",
            "autori": {q: {"nome": autori[q]["nome"], "nascita": autori[q].get("nascita"), "morte": autori[q].get("morte"),
                           "p268_oggi": wd[q]["p268"], "cache": cache.get(q)} for q in qs}}
    (D / "bnf-base-2026-11-18.json").write_text(json.dumps(base, ensure_ascii=False, indent=1), encoding="utf-8")
    gruppi = {"trovato": [q for q in qs if (cache.get(q) or {}).get("trovato")],
              "codice, zero in francese": [q for q in qs if (cache.get(q) or {}).get("metodo") and not cache[q].get("trovato")],
              "senza codice": [q for q in qs if not (cache.get(q) or {}).get("metodo")]}
    rnd = random.Random(SEME)
    scelti = [(q, g) for g, lista in gruppi.items() for q in rnd.sample(lista, min(20, len(lista)))]
    print({g: len(x) for g, x in gruppi.items()}, flush=True)
    prove = []
    for n, (q, g) in enumerate(scelti, 1):
        a, w = autori[q], wd[q]
        r = {"n": n, "qid": q, "nome": a["nome"], "nascita": a.get("nascita"), "morte": a.get("morte"), "paesi": a.get("paesi"),
             "gruppo": g, "cache": cache.get(q), "p268": w["p268"], "alias": w["alias"][:6]}
        try:
            opere = sparql(f"""SELECT DISTINCT ?l WHERE {{ ?w wdt:P50 wd:{q} . ?w rdfs:label ?l .
              FILTER(LANG(?l) IN ("fr","en","it","de","es","mul")) }} LIMIT 60""")
            r["opere_wikidata"] = sorted({x["l"]["value"] for x in opere})[:25]
            time.sleep(1)
        except Exception as e:
            r["opere_wikidata"] = [f"errore: {e}"[:80]]
        try:
            if w["p268"]:
                r["schede_codice"] = []
                for c in w["p268"]:
                    rid = re.sub(r"\D", "", c)[:8]
                    tot, testo = sru(f'aut.persistentid all "ark:/12148/cb{c}"', n=1)
                    sch = scheda_autore(record(testo)[0]) if tot else {"ark": None, "nome": "(nessuna scheda con questo codice)"}
                    sch["codice"] = c
                    sch["notizie_tutte_lingue"], _ = sru(f'bib.author2bib all "{rid}"')
                    sch["notizie_fr"], sch["esempi_fr"] = notizie_collegate(rid) if sch["notizie_tutte_lingue"] else (0, [])
                    r["schede_codice"].append(sch)
            else:
                r["candidati_per_nome"] = candidati_nome(a["nome"])
        except ErroreTecnico as e:
            r["errore_tecnico"] = str(e)
        prove.append(r)
        print(n, g, a["nome"], "codici" if w["p268"] else "nome", r.get("errore_tecnico", ""), flush=True)
    (D / "prove.json").write_text(json.dumps({"seme": SEME, "gruppi": {g: len(x) for g, x in gruppi.items()}, "autori": prove},
                                             ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
