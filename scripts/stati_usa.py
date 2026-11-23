"""Tre stati della lista USA (docs/criteri.md, decisione di Marco del 23/11/2026): «verificata», «edizione», «da_confermare».
stati_anno(anno) è usato da scripts/pagine.py (etichette e conteggio nelle pagine delle liste, ok di Marco del 23/11/2026),
così le pagine calcolano sempre lo stato con gli stessi dati e la stessa regola (regole.stato_usa_lista).
Uso a mano: LISTE=2027,2028 python3 scripts/stati_usa.py  → scrive data/registro/stati_usa.json e i numeri."""
import json, os, sys
from collections import Counter
from pathlib import Path

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "scripts"))
import regole as RG   # noqa: E402
from incrocio_opere import extra_da_file, LINGUE   # noqa: E402


def stati_anno(anno):
    """{qid: stato} per la lista USA dell'anno (opere di data/us-<anno>.json)."""
    anno = str(anno)
    f = R / "data" / f"us-{anno}.json"
    if not f.exists():
        return {}
    ver_all = json.load(open(R / "data" / "us-anni-verificati.json", encoding="utf-8"))
    man = json.load(open(R / "data" / "verifiche_opere.json", encoding="utf-8")).get("usa_lista", {})
    ex = extra_da_file(R)
    pub = RG.pubblicate_libere_usa_nel(int(anno))
    ver = ver_all.get(anno, {})
    st = {}
    for o in json.load(open(f, encoding="utf-8"))["opere"]:
        q = o["qid"]
        v = ver.get(q) or [None]
        extra = v[6] if len(v) > 6 and isinstance(v[6], dict) else {}
        e_, voci = ex.get(q, ({}, []))
        r = RG.incrocio_opera(pub, LINGUE.get((o.get("lingua") or {}).get("en")), v[5] if len(v) > 5 else {},
                              extra.get("puntate"), extra.get("date_wikidata") or (e_.get("p577") or None),
                              fatti=RG.fatti_da_ricerca(voci, pub) if voci else None, extra=e_)
        st[q] = RG.stato_usa_lista(man.get(q), r["esito"], v[0])
    return st


def main():
    out = {}
    for anno in os.environ.get("LISTE", "2027").split(","):
        st = stati_anno(anno)
        out[anno] = st
        print(anno, len(st), dict(Counter(st.values())))
    json.dump(out, open(R / "data" / "registro" / "stati_usa.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
