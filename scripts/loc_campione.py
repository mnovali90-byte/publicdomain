#!/usr/bin/env python3
"""USA, Library of Congress: campione di sviluppo (18/11/2026). Solo lettura, non cambia il sito.

Metodo da provare (come per la BnF, dal codice e non dal nome):
  1. codice LC dell'autore in Wikidata (P244) -> intestazione ufficiale da id.loc.gov («Wells, H. G. (Herbert George), 1866-1946»);
  2. catalogo LC (SRU lx2.loc.gov) con bath.personalName = quell'intestazione;
  3. il catalogo non filtra per lingua né per anno: si scaricano le notizie e si contano quelle in inglese (campo 008),
     e quante dal 2000.
Prove raccolte per il controllo a mano: per ogni notizia, le voci d'autore (100/700) e di soggetto (600) che contengono
il cognome, con la lingua e l'anno. Distingue i risultati dagli errori tecnici (il servizio non risponde).
Campione: 40 autori estratti a caso tra gli autori del sito con codice LC, più tutti quelli senza codice contati a parte.
Scrive docs/campione-loc/prove.json."""
import json, pathlib, random, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import alma  # noqa: E402
from arricchisci import sparql  # noqa: E402

RADICE = pathlib.Path(__file__).resolve().parent.parent
D = RADICE / "docs" / "campione-loc"
SRU = "http://lx2.loc.gov:210/LCDB"
UA = "publicdomain-radar/1.0 (https://github.com/mnovali90-byte/publicdomain)"
SEME = 20261118


class ErroreTecnico(Exception):
    pass


def get(url, tentativi=4):
    ultimo = None
    for t in range(tentativi):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            x = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "replace")
            time.sleep(2)
            return x
        except Exception as e:
            ultimo = e
            time.sleep(6 * (t + 1))
    raise ErroreTecnico(str(ultimo)[:150])


def etichetta(codice):
    t = get(f"https://id.loc.gov/authorities/names/{codice}.json")
    for x in json.loads(t):
        if x.get("@id", "").endswith("/" + codice) and "http://www.loc.gov/mads/rdf/v1#authoritativeLabel" in x:
            return x["http://www.loc.gov/mads/rdf/v1#authoritativeLabel"][0]["@value"]
    return None


def notizie(lab, cognome, massimo=1000):
    out, start, tot = [], 1, None
    while True:
        t = get(SRU + "?" + urllib.parse.urlencode({"version": "1.1", "operation": "searchRetrieve", "query": f'bath.personalName="{lab}"',
                                                    "maximumRecords": "50", "startRecord": str(start), "recordSchema": "marcxml"}))
        m = re.search(r"numberOfRecords>(\d+)<", t)
        if not m:
            raise ErroreTecnico("risposta senza numero di risultati: " + t[:100])
        tot = int(m.group(1))
        for rec in re.findall(r"<record xmlns[^>]*>(.*?)</record>", t, re.S):
            voci = []
            for tag, corpo in re.findall(r'tag="(100|700|600|800)"[^>]*>(.*?)</datafield>', rec, re.S):
                testo = " ".join(v for c, v in re.findall(r'code="(\w)">([^<]*)<', corpo) if c in "abcdq")
                if cognome.lower() in testo.lower():
                    voci.append(f"{tag}: {testo}")
            f008 = (re.findall(r'tag="008">([^<]*)<', rec) or [""])[0]
            tit = (re.findall(r'tag="245"[^>]*>\s*<subfield code="a">([^<]*)<', rec) or [""])[0]
            out.append({"titolo": tit[:90], "lingua": f008[35:38], "anno": f008[7:11], "voci": voci})
        start += 50
        if start > tot or start > massimo or not tot:
            break
    return tot, out


def main():
    D.mkdir(parents=True, exist_ok=True)
    autori = {}
    for f in sorted((RADICE / "data").glob("*[0-9][0-9][0-9][0-9].json")):
        if not f.name.startswith(("us-", "anniversari-")):
            for a in alma.candidati(json.loads(f.read_text(encoding="utf-8"))):
                autori.setdefault(a["wikidata"], a)
    qs = sorted(autori)
    cod = {}
    for i in range(0, len(qs), 60):
        for b in sparql("SELECT ?a ?v WHERE { VALUES ?a { " + " ".join("wd:" + q for q in qs[i:i + 60]) + " } ?a wdt:P244 ?v }"):
            cod.setdefault(b["a"]["value"].rsplit("/", 1)[-1], []).append(b["v"]["value"])
        time.sleep(2)
    con = [q for q in qs if q in cod]
    scelti = random.Random(SEME).sample(con, 40)
    out = {"autori_sito": len(qs), "con_codice_lc": len(con), "senza_codice": len(qs) - len(con), "autori": []}
    for n, q in enumerate(scelti, 1):
        a = autori[q]
        r = {"n": n, "qid": q, "nome": a["nome"], "anni": f'{str(a.get("nascita"))[:4]}-{str(a.get("morte"))[:4]}', "codici": cod[q]}
        try:
            r["intestazioni"] = {c: etichetta(c) for c in cod[q]}
            lab = next((l for l in r["intestazioni"].values() if l), None)
            if lab:
                tot, recs = notizie(lab, lab.split(",")[0])
                r.update({"totale": tot, "lette": len(recs), "inglese": sum(1 for x in recs if x["lingua"] == "eng"),
                          "inglese_dal_2000": sum(1 for x in recs if x["lingua"] == "eng" and x["anno"].isdigit() and int(x["anno"]) >= 2000),
                          "notizie": recs[:60]})
        except ErroreTecnico as e:
            r["errore_tecnico"] = str(e)
        out["autori"].append(r)
        print(n, a["nome"], r.get("intestazioni"), r.get("totale"), r.get("inglese"), r.get("errore_tecnico", ""), flush=True)
    (D / "prove.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
