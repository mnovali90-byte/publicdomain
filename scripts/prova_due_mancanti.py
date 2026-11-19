"""Prova (20/11/2026): perché Red Harvest (Q1935469) e A Room of One's Own non entrano nella lista del 1929?
Rifà la domanda di opere.opere_anno classe per classe e dice in quale finiscono, poi chiede a Wikidata P31, P50,
P577 (con precisione) e numero di Wikipedia delle due opere. Scrive docs/stima-sito/prova-due-mancanti.json."""
import json, sys, urllib.parse
from pathlib import Path
R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "scripts"))
import opere  # noqa: E402

CERCA = {"Q1935469": "Red Harvest", "Q1204366": "A Room of One's Own"}


def main():
    out = {"per_classe": {}, "schede": {}}
    for c in opere.CLASSI_USA + ["scritte"]:
        r = opere.opere_anno(1929, [] if c == "scritte" else [c], c == "scritte")
        out["per_classe"][c] = {"opere": len(r), "trovate": [q for q in CERCA if any(o["qid"] == q for o in r)]}
        print(c, len(r), out["per_classe"][c]["trovate"])
    q = """SELECT ?w ?p31 ?a ?d ?prec ?sl WHERE { VALUES ?w { wd:Q1935469 wd:Q1204366 }
      OPTIONAL { ?w wdt:P31 ?p31 } OPTIONAL { ?w wdt:P50 ?a }
      OPTIONAL { ?w p:P577/psv:P577 [ wikibase:timeValue ?d; wikibase:timePrecision ?prec ] }
      ?w wikibase:sitelinks ?sl }"""
    for r in opere.sparql(q):
        k = opere.qid(opere.val(r, "w"))
        s = out["schede"].setdefault(k, {"P31": set(), "P50": set(), "P577": set(), "wikipedia": opere.val(r, "sl")})
        for kk, vv in (("P31", "p31"), ("P50", "a")):
            if opere.val(r, vv): s[kk].add(opere.qid(opere.val(r, vv)))
        if opere.val(r, "d"): s["P577"].add(f'{opere.val(r, "d")} (precisione {opere.val(r, "prec")})')
    out["schede"] = {k: {kk: sorted(v) if isinstance(v, set) else v for kk, v in s.items()} for k, s in out["schede"].items()}
    print(json.dumps(out["schede"], ensure_ascii=False))
    (R / "docs" / "stima-sito" / "prova-due-mancanti.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
