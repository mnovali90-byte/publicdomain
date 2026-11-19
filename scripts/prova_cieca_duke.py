"""Prova alla cieca contro la Duke (19/11/2026, rifatta dopo le correzioni del metodo).

1. Lista: scripts/opere.py, stessa funzione delle liste USA (opere_anno_sicuro: un tipo alla volta; tipi in più: saggio,
   opera drammatica, «opera scritta» con autore; per le opere a puntate conta la data più recente).
2. Verifica: scripts/verifica_anni_usa.py, verifica_opera, SENZA la Duke (registro del copyright, BnF, K10plus,
   Wikipedia inglese e ISFDB per riviste e puntate, Open Library, Library of Congress).
3. Solo alla fine si apre la lista Duke e si confronta: per codice Wikidata, oppure per titolo (senza articolo) con lo
   stesso cognome o con titolo identico (pseudonimi come «Ellery Queen»).
Salva la lista completa con gli esiti: docs/stima-sito/prova-cieca-duke-<anno>.json.
"""
import json, os, sys, time
from collections import Counter
from pathlib import Path

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "scripts"))
import opere                     # noqa: E402
import verifica_anni_usa as vu   # noqa: E402

ANNO = int(os.environ.get("ANNO_PROVA", "2025"))
P = ANNO - 96
BUDGET = 100 * 60


def norm(t):
    return vu.senza_articolo(vu.parole(t))


def main():
    inizio = time.time()
    ops = opere.opere_anno_sicuro(P)
    ops.sort(key=lambda o: -o["pagine"])
    print("opere da Wikidata:", len(ops))
    if len(ops) < 20 or opere.FALLITE:
        raise SystemExit(f"Wikidata non ha risposto per {opere.FALLITE}: prova NON valida, non scrivo risultati.")
    idx = vu.indice_cce(range(P - 3, P + 3))
    orig = vu.originali([o["qid"] for o in ops])
    esiti = {}
    for o in ops:
        if time.time() - inizio > BUDGET:
            break
        esiti[o["qid"]] = vu.verifica_opera(o, P, {}, idx, orig)   # {} = niente Duke
    print("controllate:", len(esiti), Counter(e[0] for e in esiti.values()))

    dk = json.loads((R / "data" / "storico" / "duke.json").read_text(encoding="utf-8"))[str(ANNO)]["libri"]
    per_qid = {o["qid"]: o for o in ops}
    confronto = []
    for l in dk:
        o = per_qid.get((l.get("wd") or {}).get("qid"))
        come = "codice Wikidata" if o else None
        if not o:
            tw, cg = norm(l["titolo"]), set(vu.parole(l["autore"]))
            for x in ops:
                tx = norm(x["titolo"])
                n_ = min(len(tw), len(tx), 3)
                if n_ and tx[:n_] == tw[:n_]:
                    stesso_autore = any(set(vu.parole(a["nome"])) & cg for a in x.get("autori", []))
                    if stesso_autore or tx == tw:
                        o, come = x, ("titolo e autore" if stesso_autore else "titolo identico")
                        break
        e = esiti.get(o["qid"]) if o else None
        confronto.append({"duke": f'{l["titolo"]} — {l["autore"]}', "trovato_come": come,
                          "nostro_titolo": o["titolo"] if o else None, "nostro_esito": e[0] if e else None,
                          "fonte": e[2] if e else None, "extra": e[6] if e else None})
    lista = []
    for o in ops:
        e = esiti.get(o["qid"]) or [None] * 7
        lista.append({"qid": o["qid"], "titolo": o["titolo"], "autori": [a["nome"] for a in o.get("autori", [])],
                      "wikipedia": o["pagine"], "date_wikidata": o.get("date_wikidata"), "esito": e[0], "anno": e[1],
                      "fonte": e[2], "trovati": e[5], "extra": e[6]})
    out = {"anno": ANNO, "anno_pubblicazione": P, "nostra_lista": len(ops), "controllate": len(esiti),
           "nostri_esiti": dict(Counter(e[0] for e in esiti.values())),
           "nostre_conferme_per_fonte": dict(Counter(e[2] for e in esiti.values() if e[0] == "ok")),
           "duke_libri": len(dk), "duke_trovati": sum(1 for c in confronto if c["trovato_come"]),
           "duke_confermati": sum(1 for c in confronto if c["nostro_esito"] == "ok"),
           "confronto": confronto, "lista_completa": lista}
    (R / "docs" / "stima-sito" / f"prova-cieca-duke-{ANNO}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k not in ("confronto", "lista_completa")}, ensure_ascii=False))
    for c in confronto:
        print(c)


if __name__ == "__main__":
    main()
