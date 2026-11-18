#!/usr/bin/env python3
"""British Library (e i 9 autori BNE trovati per nome): misura del metodo attuale, 18/11/2026. Solo lettura.

Il sito oggi cerca nella British Library «Cognome nascita-morte» nel campo autore (alma.creator) e conta le notizie
in inglese. Qui, per un campione, si scaricano le notizie trovate e si guarda CHI è l'autore in ciascuna:
  - la voce d'autore (campi 100/700) che contiene cognome e anni nello STESSO campo, con il nome di battesimo;
  - se nessun campo li contiene insieme (cognome in una voce, anni in un'altra), la notizia è sospetta.
Per i trovati si confronta anche il nome di battesimo con Wikidata. Per i non trovati si cerca il cognome con il
nome di battesimo SENZA anni, per vedere se l'autore c'è ma è schedato senza date.
Campione: 40 trovati e 20 non trovati a caso tra gli autori con dato BL, più i 9 autori BNE trovati per nome.
Controlla anche che la ricerca BnF con più codici («... or ...») funzioni. Scrive docs/campione-bl/prove.json."""
import json, pathlib, random, re, sys, time, unicodedata, urllib.parse, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import alma  # noqa: E402

RADICE = pathlib.Path(__file__).resolve().parent.parent
D = RADICE / "docs" / "campione-bl"
SEME = 20261118
UA = "publicdomain-radar/1.0 (https://github.com/mnovali90-byte/publicdomain)"


def scarica(url):
    for t in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            x = urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")
            time.sleep(1)
            return x
        except Exception as e:
            ultimo = e
            time.sleep(4 * (t + 1))
    raise RuntimeError(str(ultimo)[:120])


def notizie(base, query, n=50):
    t = scarica(base + "?" + urllib.parse.urlencode({"version": "1.2", "operation": "searchRetrieve", "query": query,
                                                    "recordSchema": "marcxml", "maximumRecords": str(n)}))
    tot = int((re.findall(r"numberOfRecords>(\d+)<", t) or ["-1"])[0])
    out = []
    for r in re.findall(r"<record[^>]*>(.*?)</record>", t, re.S):
        voci = []
        for tag, corpo in re.findall(r'tag="(100|700|110|710)"[^>]*>(.*?)</datafield>', r, re.S):
            sub = dict((c, v) for c, v in re.findall(r'code="(\w)">([^<]*)<', corpo) if c in "adq")
            voci.append(f"{tag}: {sub.get('a', '')} {sub.get('q', '')} {sub.get('d', '')}".strip())
        tit = (re.findall(r'tag="245"[^>]*>\s*<subfield code="a">([^<]*)<', r) or [""])[0]
        f008 = (re.findall(r'tag="008">([^<]*)<', r) or [""])[0]
        out.append({"titolo": tit[:100], "anno": f008[7:11], "lingua": f008[35:38], "voci": voci[:6]})
    return tot, out


def sa(t):
    return "".join(c for c in unicodedata.normalize("NFKD", t or "") if not unicodedata.combining(c)).lower()


def stessa_voce(voci, cognome, nato, morto):
    for v in voci:
        w = sa(v)
        if sa(cognome) in w and nato in w and morto in w:
            return v
    return None


def main():
    D.mkdir(parents=True, exist_ok=True)
    cache = json.loads((RADICE / "data" / "cache_alma.json").read_text(encoding="utf-8"))
    autori = {}
    for f in sorted((RADICE / "data").glob("*[0-9][0-9][0-9][0-9].json")):
        if not f.name.startswith(("us-", "anniversari-")):
            for a in json.loads(f.read_text(encoding="utf-8")).get("autori", []):
                autori.setdefault(a["wikidata"], a)
    con = sorted(q for q, v in cache.items() if q in autori and (v.get("bl_en") or {}).get("trovato"))
    senza = sorted(q for q, v in cache.items() if q in autori and v.get("bl_en") and not v["bl_en"].get("trovato"))
    bne_nome = sorted(q for q, v in cache.items() if q in autori and (v.get("bne_es") or {}).get("metodo") == "nome_anni")
    rnd = random.Random(SEME)
    scelti = [(q, "BL trovato") for q in rnd.sample(con, min(40, len(con)))] + [(q, "BL non trovato") for q in rnd.sample(senza, min(20, len(senza)))] + \
             [(q, "BNE per nome") for q in bne_nome]
    base = {"congelato": "2026-11-18", "BL": {q: cache[q].get("bl_en") for q in con + senza}, "BNE_per_nome": {q: cache[q].get("bne_es") for q in bne_nome}}
    (D / "base-2026-11-18.json").write_text(json.dumps(base, ensure_ascii=False, indent=1), encoding="utf-8")
    out = {"gruppi": {"BL trovati": len(con), "BL non trovati": len(senza), "BNE per nome": len(bne_nome)}, "autori": []}
    for n, (q, g) in enumerate(scelti, 1):
        a = autori[q]
        nato, morto = str(a.get("nascita") or "")[:4], str(a.get("morte") or "")[:4]
        r = {"n": n, "qid": q, "nome": a["nome"], "anni": f"{nato}-{morto}", "gruppo": g, "oggi": cache[q].get("bl_en" if g.startswith("BL") else "bne_es")}
        try:
            if g.startswith("BL"):
                k = alma.chiave_nome(a)
                cat, filtro = "bl_en", f'alma.creator all "{alma._ascii(k)}"'
                cognome = k.split()[0]
            else:
                k = alma.chiave_nome_intero(a)
                cat, filtro = "bne_es", f'alma.creator all "{k}"'
                cognome = alma._ascii(a["nome"]).split()[-1]
            c = alma.CATALOGHI[cat]
            tot, recs = notizie(c["url"], f'{filtro} and alma.language={c["lingua"]}')
            for x in recs:
                x["voce_con_anni"] = stessa_voce(x["voci"], cognome, nato, morto)
            r.update({"query": filtro, "totale": tot, "notizie": recs})
            if g == "BL non trovato":
                p = [x for x in alma._ascii(a["nome"]).split() if len(x.strip(".")) > 1]
                if len(p) > 1:
                    t2, recs2 = notizie(c["url"], f'alma.creator all "{p[0]} {p[-1]}" and alma.language={c["lingua"]}', n=15)
                    r.update({"senza_anni_totale": t2, "senza_anni": recs2})
        except Exception as e:
            r["errore_tecnico"] = str(e)[:150]
        out["autori"].append(r)
        print(n, g, a["nome"], r.get("totale"), r.get("errore_tecnico", ""), flush=True)
    # controllo della ricerca BnF con più codici (Roger Vercel: 16178881k e 119279086)
    try:
        import bnf
        out["bnf_or"] = {"uno": bnf.quanti('bib.author2bib all "11927908" and bib.language any "fre"'),
                         "due": bnf.quanti('(bib.author2bib all "11927908" or bib.author2bib all "16178881") and bib.language any "fre"')}
    except Exception as e:
        out["bnf_or"] = {"errore": str(e)[:150]}
    (D / "prove.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
