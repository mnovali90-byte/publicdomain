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

LINGUE = {"English": "en", "German": "de", "French": "fr"}


def main():
    anno = os.environ.get("LISTA", "2028")
    lista = json.load(open(R / "data" / f"us-{anno}.json", encoding="utf-8"))
    ver = json.load(open(R / "data" / "us-anni-verificati.json", encoding="utf-8")).get(anno, {})
    pub = RG.pubblicate_libere_usa_nel(int(anno))
    conta, righe = Counter(), []
    for o in lista["opere"]:
        v = ver.get(o["qid"]) or []
        extra = v[6] if len(v) > 6 and isinstance(v[6], dict) else {}
        r = RG.incrocio_opera(pub, LINGUE.get((o.get("lingua") or {}).get("en")), v[5] if len(v) > 5 else {},
                              extra.get("puntate"), extra.get("date_wikidata"))
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
