#!/usr/bin/env python3
"""Controlli sui conteggi dei cataloghi prima che arrivino sul sito (fase 0 del piano qualità, 17/11/2026).

Gira dopo sbn.py, bnf.py e alma.py e prima di pagine.py. Per ogni autore e ogni catalogo
(sbn_it, bnf_fr, bne_es, bl_en) controlla che i numeri non si contraddicano:
  - le registrazioni «dal 2000» non possono superare il totale;
  - se ce n'è almeno una dal 2000, la più recente non può essere prima del 2000;
  - la più recente non può essere nel futuro.
Un dato che non passa NON si cancella e NON si sostituisce con quello del mese prima (sarebbe lasciare
online l'errore): resta nel file con "stato": "da_verificare" e il motivo, e il sito non mostra i numeri.
Vale anche per i dati già presenti nei file, non solo per quelli nuovi.

Sospensioni a mano (data/sospesi_manuali.json): collegamenti non dimostrati, per esempio un codice di Wikidata
che porta a una scheda con titoli non dell'autore. Valgono anche se il catalogo dice zero registrazioni e
restano finché il caso non è chiarito e tolto dal file.

Scrive il riepilogo in data/controlli.json (quanti dati passano e quali sono sospesi).
"""
import datetime as dt
import json
import pathlib
import sys

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
CATALOGHI = ("sbn_it", "bnf_fr", "bne_es", "bl_en", "loc_en")


def problemi(v, anno_oggi):
    """Elenco dei motivi per cui un conteggio non si può pubblicare (vuoto se va bene)."""
    out = []
    tot, d, ult = v.get("edizioni"), v.get("dal_2000"), v.get("ultimo")
    if not isinstance(tot, int) or tot < 0:
        out.append("totale mancante o negativo")
        return out
    if d is not None and (not isinstance(d, int) or d < 0):
        out.append("«dal 2000» non valido")
    elif d is not None and d > tot:
        out.append(f"«dal 2000» ({d}) maggiore del totale ({tot})")
    if d and ult is not None and ult < 2000:
        out.append(f"{d} registrazioni dal 2000 ma la più recente sarebbe del {ult}")
    if ult is not None and ult > anno_oggi:
        out.append(f"anno più recente nel futuro ({ult})")
    return out


def main():
    anno_oggi = dt.date.today().year
    file = [f for f in sorted(DATA.glob("*[0-9][0-9][0-9][0-9].json")) if not f.name.startswith(("us-", "anniversari-"))]
    conta = {k: {"controllati": 0, "ok": 0, "sospesi": 0} for k in CATALOGHI}
    sospesi, visti = [], set()
    f_man = DATA / "sospesi_manuali.json"
    manuali = {(x["wikidata"], x["catalogo"]): x["motivo"] for x in (json.loads(f_man.read_text(encoding="utf-8")) if f_man.exists() else [])}
    for f in file:
        p = json.loads(f.read_text(encoding="utf-8"))
        cambiato = False
        for a in p["autori"]:
            for k in CATALOGHI:
                v = (a.get("traduzioni") or {}).get(k)
                manuale = manuali.get((a["wikidata"], k))
                if not isinstance(v, dict) or (not v.get("trovato") and not manuale):
                    continue
                motivi = ([f"collegamento non dimostrato: {manuale}"] if manuale else []) + (problemi(v, anno_oggi) if v.get("trovato") else [])
                prima = (v.get("stato"), v.get("motivo"), v.get("sospeso_manuale"))
                if motivi:
                    v["stato"], v["motivo"] = "da_verificare", "; ".join(motivi)
                else:
                    v.pop("stato", None); v.pop("motivo", None)
                if manuale:
                    v["sospeso_manuale"] = True
                else:
                    v.pop("sospeso_manuale", None)
                cambiato |= prima != (v.get("stato"), v.get("motivo"), v.get("sospeso_manuale"))
                if (a["wikidata"], k) in visti:      # lo stesso autore compare in più file: si conta una volta
                    continue
                visti.add((a["wikidata"], k))
                conta[k]["controllati"] += 1
                if motivi:
                    conta[k]["sospesi"] += 1
                    sospesi.append({"wikidata": a["wikidata"], "nome": a["nome"], "catalogo": k, "motivo": v["motivo"],
                                    "edizioni": v.get("edizioni"), "dal_2000": v.get("dal_2000"), "ultimo": v.get("ultimo")})
                else:
                    conta[k]["ok"] += 1
        if cambiato:
            f.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
    rapporto = {"controllato": dt.date.today().isoformat(), "per_catalogo": conta,
                "sospesi": sorted(sospesi, key=lambda x: (x["catalogo"], x["nome"]))}
    (DATA / "controlli.json").write_text(json.dumps(rapporto, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, c in conta.items():
        print(f"controlli {k}: {c['controllati']} autori, {c['ok']} passano, {c['sospesi']} sospesi (da verificare)")
    if sospesi:
        print(f"::warning::{len(sospesi)} conteggi sospesi: il sito non li mostra (data/controlli.json)", file=sys.stderr)


if __name__ == "__main__":
    main()
