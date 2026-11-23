"""Riverifica dei «confermati» della lista USA con la regola di oggi (decisione di Marco, 23/11/2026). NON CAMBIA IL SITO.

Il campione dei «conferma» 2028 (docs/campione-conferma-2028.md) ha mostrato che l'anno del libro, senza la prima
uscita in rivista, può sbagliare. Qui si rifà passare per regole.incrocio_opera ogni opera che il 20/11/2026 era stata
segnata «ok» in data/us-anni-verificati.json ed è ancora nella lista. Scrive docs/riverifica-confermati-us-<anno>.md:
quante restano «conferma» e quante scendono a «da decidere», queste in ordine di visite (da passare per
docs/ricerca-web.md). Uso: LISTA=2027 python3 scripts/riverifica_confermati.py"""
import json, os, sys
from collections import Counter
from pathlib import Path

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "scripts"))
import regole as RG   # noqa: E402
from incrocio_opere import extra_da_file, LINGUE   # noqa: E402


def main():
    anno = os.environ.get("LISTA", "2027")
    lista = {o["qid"]: o for o in json.load(open(R / "data" / f"us-{anno}.json", encoding="utf-8"))["opere"]}
    ver = json.load(open(R / "data" / "us-anni-verificati.json", encoding="utf-8")).get(anno, {})
    a_mano = json.load(open(R / "data" / "verifiche_opere.json", encoding="utf-8")).get("usa_lista", {})
    pub = RG.pubblicate_libere_usa_nel(int(anno))
    ex = extra_da_file(R)
    righe, conta = [], Counter()
    for q, v in ver.items():
        if v[0] != "ok" or q not in lista:
            continue
        o = lista[q]
        extra = v[6] if len(v) > 6 and isinstance(v[6], dict) else {}
        e_, voci = ex.get(q, ({}, []))
        r = RG.incrocio_opera(pub, LINGUE.get((o.get("lingua") or {}).get("en")), v[5] if len(v) > 5 else {},
                              extra.get("puntate"), extra.get("date_wikidata") or (e_.get("p577") or None),
                              fatti=RG.fatti_da_ricerca(voci, pub) if voci else None, extra=e_)
        e = r["esito"]
        conta[e] += 1
        righe.append((e, o.get("titolo_it") or o.get("titolo"), q, r["motivo"], o.get("visite_en") or 0,
                      "sì" if q in a_mano else "", ", ".join(v[4]) if len(v) > 4 and isinstance(v[4], list) else ""))
    md = [f"# Riverifica dei confermati: lista USA {anno} (libri del {pub})", "",
          "Solo rapporto: niente cambia nel sito. Opere segnate «ok» il 20/11/2026 e ancora in lista, ripassate per "
          "`regole.incrocio_opera` con la regola del 23/11/2026 (per confermare serve una prima pubblicazione documentata).", "",
          f"- Opere: {len(righe)}"] + [f"- {k}: {n}" for k, n in sorted(conta.items())] + [
          "- «Già a mano»: l'opera è anche fra le decisioni a mano del 23/11/2026 (data/verifiche_opere.json), che valgono più della regola.",
          "", "| Esito | Opera | Perché | Visite (en) | Già a mano | Fonti provate il 20/11 |", "|---|---|---|---|---|---|"]
    for e, t, q, m, vis, mano, f in sorted(righe, key=lambda x: (x[0] != "da decidere", -x[4])):
        md.append(f"| {e} | {t} ({q}) | {m} | {vis} | {mano} | {f} |")
    (R / "docs" / f"riverifica-confermati-us-{anno}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(dict(conta))


if __name__ == "__main__":
    main()
