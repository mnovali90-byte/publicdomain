"""Incrocio delle fonti sulle opere di una lista USA (passo 2 di docs/verifica-opere.md, regola regole.incrocio_opera).
NON CAMBIA IL SITO: scrive solo il rapporto docs/incrocio-us-<anno>.md, con le opere che il sistema decide da solo
e quelle «da decidere» (che vanno controllate a mano con le fonti). Le decisioni restano in data/verifiche_opere.json.
Uso: LISTA=2028 python3 scripts/incrocio_opere.py  (legge data/us-<anno>.json e data/us-anni-verificati.json)."""
import json, os, sys
from collections import Counter
from pathlib import Path

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "scripts"))
import regole as RG   # noqa: E402


def extra_da_file(R):
    """data/fonti_prima_uscita.json (scripts/fonti_prima_uscita.py) e i risultati della ricerca sul web
    (docs/ricerca-web/risultati.json, docs/ricerca-web.md): {qid: (extra, voci)}."""
    import json as _j
    out = {}
    try:
        fp = _j.load(open(R / "data" / "fonti_prima_uscita.json", encoding="utf-8")).get("opere", {})
    except Exception:
        fp = {}
    anno = lambda s: int(s[:4]) if s and s[:4].isdigit() else None
    for q, x in fp.items():
        w = x.get("wikidata") or {}
        out[q] = ({"originale": x.get("catalogo") if (x.get("catalogo") or {}).get("anno") else None,
                   "riviste": [anno(r.get("data")) for r in w.get("riviste", []) if anno(r.get("data"))],
                   "edizioni": [anno(e.get("data")) for e in w.get("edizioni", []) if anno(e.get("data"))],
                   "p577": [anno(d) for d in w.get("p577", []) if anno(d)]}, [])
    try:
        ric = _j.load(open(R / "docs" / "ricerca-web" / "risultati.json", encoding="utf-8")).get("voci", [])
    except Exception:
        ric = []
    for v in ric:
        out.setdefault(v.get("qid"), ({}, []))[1].append(v)
    return out

LINGUE = {"English": "en", "German": "de", "French": "fr"}


def main():
    anno = os.environ.get("LISTA", "2028")
    lista = json.load(open(R / "data" / f"us-{anno}.json", encoding="utf-8"))
    ver = json.load(open(R / "data" / "us-anni-verificati.json", encoding="utf-8")).get(anno, {})
    pub = RG.pubblicate_libere_usa_nel(int(anno))
    ex = extra_da_file(R)
    conta, righe = Counter(), []
    for o in lista["opere"]:
        v = ver.get(o["qid"]) or []
        extra = v[6] if len(v) > 6 and isinstance(v[6], dict) else {}
        e_, voci = ex.get(o["qid"], ({}, []))
        r = RG.incrocio_opera(pub, LINGUE.get((o.get("lingua") or {}).get("en")), v[5] if len(v) > 5 else {},
                              extra.get("puntate"), extra.get("date_wikidata") or (e_.get("p577") or None),
                              fatti=RG.fatti_da_ricerca(voci, pub) if voci else None, extra=e_)
        conta[r["esito"]] += 1
        righe.append((r["esito"], o.get("titolo_it") or o.get("titolo"), o["qid"], r.get("anno"), r["motivo"], o.get("visite_en") or 0))
    md = [f"# Incrocio delle fonti: lista USA {anno} (libri del {pub})", "",
          "Solo rapporto: niente cambia nel sito. Regola `regole.incrocio_opera`, collaudata in docs/collaudo-incrocio.md.", "",
          f"- Opere: {len(righe)}"] + [f"- {k}: {n}" for k, n in sorted(conta.items())] + [
          "", "| Esito | Opera | Anno | Perché | Visite (en) |", "|---|---|---|---|---|"]
    for e, t, q, y, m, vis in sorted(righe, key=lambda x: (x[0] == "da decidere", -x[5])):
        md.append(f"| {e} | {t} ({q}) | {y or ''} | {m} | {vis} |")
    (R / "docs" / f"incrocio-us-{anno}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(dict(conta))
    for r_ in righe:
        if r_[0] != "da decidere":
            print(r_)


if __name__ == "__main__":
    main()
