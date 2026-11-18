#!/usr/bin/env python3
"""Verifica di loc.py su 40 autori NUOVI (non nel campione di sviluppo docs/campione-loc), prima del rilascio. 18/11/2026.
  congela -> impronta di loc.py
  prove   -> per ogni autore: codici LC, intestazioni, e TUTTE le notizie trovate (fino a 2000) con tutte le voci
             d'autore e di soggetto, lingua e anno, senza applicare la regola di conteggio
  (a mano: docs/verifica-loc/esiti.json: per ogni autore le intestazioni che sono sue)
  misura  -> la regola di loc.py sulle stesse notizie contro gli esiti a mano: notizie sue in inglese contate o perse,
             notizie di altri contate; più errori tecnici."""
import collections, hashlib, json, pathlib, random, re, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import alma  # noqa: E402
import loc  # noqa: E402

RADICE = pathlib.Path(__file__).resolve().parent.parent
import os
D = RADICE / "docs" / os.environ.get("VERIFICA_DIR", "verifica-loc")
SEME = int(os.environ.get("VERIFICA_SEME", "20261122"))


def impronte():
    return {"scripts/loc.py": hashlib.sha256((RADICE / "scripts" / "loc.py").read_bytes()).hexdigest()}


def congela():
    D.mkdir(parents=True, exist_ok=True)
    c = subprocess.run(["git", "rev-parse", "HEAD"], cwd=RADICE, capture_output=True, text=True).stdout.strip()
    (D / "regole-congelate.json").write_text(json.dumps({"commit": c, "sha256": impronte()}, indent=1), encoding="utf-8")


def grezze(lab):
    out, start = [], 1
    while True:
        tot, recs = loc.pagina(lab, start)
        for rec in recs:
            voci = [f"{tag}: " + " ".join(v for c, v in re.findall(r'code="(\w)">([^<]*)<', corpo) if c in "abcdq")
                    for tag, corpo in re.findall(r'tag="(100|700|800|600)"[^>]*>(.*?)</datafield>', rec, re.S)]
            f008 = (re.findall(r'tag="008">([^<]*)<', rec) or [""])[0]
            tit = (re.findall(r'tag="245"[^>]*>\s*<subfield code="a">([^<]*)<', rec) or [""])[0]
            out.append({"titolo": tit[:80], "lingua": f008[35:38], "anno": f008[7:11], "voci": voci})
        start += 50
        if start > tot or start > loc.MASSIMO:
            return tot, out


def prove():
    D.mkdir(parents=True, exist_ok=True)
    autori = {}
    for f in sorted((RADICE / "data").glob("*[0-9][0-9][0-9][0-9].json")):
        if not f.name.startswith(("us-", "anniversari-")):
            for a in alma.candidati(json.loads(f.read_text(encoding="utf-8"))):
                autori.setdefault(a["wikidata"], a)
    usati = {r["qid"] for r in json.loads((RADICE / "docs" / "campione-loc" / "prove.json").read_text(encoding="utf-8"))["autori"]}
    if D.name != "verifica-loc":       # le verifiche successive escludono anche la prima (diventata di sviluppo)
        usati |= {r["qid"] for r in json.loads((RADICE / "docs" / "verifica-loc" / "campione.json").read_text(encoding="utf-8"))["autori"]}
    cod = loc.codici_lc(sorted(autori))
    scelti = random.Random(SEME).sample(sorted(q for q in cod if q not in usati), 40)
    out = []
    for n, q in enumerate(scelti, 1):
        a = autori[q]
        r = {"n": n, "qid": q, "nome": a["nome"], "anni": f'{str(a.get("nascita"))[:4]}-{str(a.get("morte"))[:4]}', "codici": cod[q]}
        try:
            r["intestazioni"] = {c: loc.intestazione(c) for c in cod[q]}
            r["notizie"] = {}
            for c, lab in r["intestazioni"].items():
                if lab:
                    tot, recs = grezze(lab)
                    r["notizie"][lab] = {"totale": tot, "notizie": recs}
        except loc.ErroreTecnico as e:
            r["errore_tecnico"] = str(e)
        out.append(r)
        print(n, a["nome"], r.get("intestazioni"), {k: v["totale"] for k, v in r.get("notizie", {}).items()}, r.get("errore_tecnico", ""), flush=True)
    (D / "campione.json").write_text(json.dumps({"seme": SEME, "autori": out}, ensure_ascii=False, indent=1), encoding="utf-8")


def misura():
    fermo = json.loads((D / "regole-congelate.json").read_text(encoding="utf-8"))
    if fermo["sha256"] != impronte():
        sys.exit("le regole sono cambiate dopo il congelamento: questo campione non vale più come verifica")
    camp = json.loads((D / "campione.json").read_text(encoding="utf-8"))["autori"]
    esiti = json.loads((D / "esiti.json").read_text(encoding="utf-8"))
    tot, righe = collections.Counter(), []
    for a in camp:
        sue = set(esiti[a["qid"]]["intestazioni_sue"])
        cc = collections.Counter()
        for lab, blocco in a.get("notizie", {}).items():
            for x in blocco["notizie"]:
                vera = x["lingua"] == "eng" and any(v.split(": ", 1)[0] in ("100", "700", "800") and v.split(": ", 1)[1] in sue for v in x["voci"])
                contata = x["lingua"] == "eng" and any(v.split(": ", 1)[0] in ("100", "700", "800") and loc.chiave(v.split(": ", 1)[1]) == loc.chiave(lab) for v in x["voci"])
                cc[("sua in inglese" if vera else "non sua o non in inglese", "contata" if contata else "non contata")] += 1
        tot.update(cc)
        righe.append({"n": a["n"], "nome": a["nome"], "notizie": {f"{k[0]}, {k[1]}": v for k, v in cc.items()}, "errore_tecnico": a.get("errore_tecnico")})
        print(a["n"], a["nome"], dict(cc), a.get("errore_tecnico", ""), flush=True)
    (D / "misura.json").write_text(json.dumps({"regole": fermo, "totale": {f"{k[0]}, {k[1]}": v for k, v in tot.items()}, "autori": righe},
                                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("TOTALE", dict(tot))


if __name__ == "__main__":
    {"congela": congela, "prove": prove, "misura": misura}[sys.argv[1]]()
