"""Collaudo alla cieca dell'incrocio delle fonti (regole.incrocio_opera) sulle opere USA decise a mano il 23/11/2026.
NON CAMBIA IL SITO. Passo 1: le risposte del sistema si calcolano leggendo SOLO i dati raccolti in automatico
(data/us-anni-verificati.json, e la lingua dell'opera dalla lista com'era prima delle decisioni, commit c50a23324).
Passo 2: solo dopo si leggono le decisioni (data/verifiche_opere.json «usa_lista» e le opere tolte stamattina in
data/registro/liste_spostati.json) e si confrontano. Regola di Marco: 0 risposte sbagliate; «da decidere» è ammesso.
Scrive docs/collaudo-incrocio.md."""
import json, subprocess, sys
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
PRIMA = "c50a23324"   # le liste USA del 22/11/2026 sera, prima delle decisioni


def lista_vecchia(anno):
    t = subprocess.run(["git", "show", f"{PRIMA}:data/us-{anno}.json"], capture_output=True, text=True, cwd=R).stdout
    return {o["qid"]: o for o in json.loads(t)["opere"]}


def risposte(qids):
    ver = json.load(open(R / "data" / "us-anni-verificati.json", encoding="utf-8"))
    ex = extra_da_file(R)
    out = {}
    for anno, voci in ver.items():
        vecchia = lista_vecchia(anno)
        pub = RG.pubblicate_libere_usa_nel(int(anno))
        for q in qids:
            if q not in voci or q in out:
                continue
            v = voci[q]
            extra = v[6] if len(v) > 6 and isinstance(v[6], dict) else {}
            lingua = LINGUE.get(((vecchia.get(q) or {}).get("lingua") or {}).get("en"))
            e_, ricerca = ex.get(q, ({}, []))
            dw = extra.get("date_wikidata") or (e_.get("p577") or None)
            r = RG.incrocio_opera(pub, lingua, v[5] if len(v) > 5 else {}, extra.get("puntate"), dw,
                                  fatti=RG.fatti_da_ricerca(ricerca, pub) if ricerca else None, extra=e_)
            out[q] = {**r, "lista": anno, "titolo": (vecchia.get(q) or {}).get("titolo")}
    return out


def verita():
    man = json.load(open(R / "data" / "verifiche_opere.json", encoding="utf-8"))["usa_lista"]
    out = {}
    for q, m in man.items():
        e = m["esito"]
        out[q] = ("esce" if e == "tolta" else "sposta" if e == "sposta"
                  else "nota" if (m.get("nota") or m.get("versione_libera")) else "conferma", m.get("titolo"))
    for x in json.load(open(R / "data" / "registro" / "liste_spostati.json", encoding="utf-8"))["usa_gia_libere"]:
        out.setdefault(x["qid"], ("esce", x.get("titolo")))
    return out


def main():
    # le opere del collaudo: si prendono solo i codici, le decisioni si leggono dopo
    qids = sorted(verita())
    ris = risposte(qids)              # passo 1: senza le decisioni
    ver = verita()                    # passo 2: le decisioni
    conta, righe = Counter(), []
    for q in qids:
        r = ris.get(q) or {"esito": "da decidere", "motivo": "nessun dato raccolto"}
        giusto, tit = ver[q]
        es = "da decidere" if r["esito"] == "da decidere" else ("giusta" if r["esito"] == giusto else "SBAGLIATA")
        conta[es] += 1
        righe.append((es, q, tit, r["esito"], giusto, r["motivo"]))
    md = ["# Collaudo alla cieca dell'incrocio delle fonti (23/11/2026)", "",
          "Solo prova: niente cambia nel sito. Script `scripts/collaudo_incrocio.py`, regola `regole.incrocio_opera`.", "",
          f"- Opere: {len(qids)} (le 50 decise in «usa_lista» più le opere tolte stamattina che non sono già fra quelle).",
          f"- Giuste: {conta['giusta']} · Sbagliate: {conta['SBAGLIATA']} · Da decidere: {conta['da decidere']}",
          f"- Esito del collaudo: {'PASSATO' if not conta['SBAGLIATA'] else 'NON PASSATO'} (regola: 0 sbagliate).", "",
          "| Esito | Opera | Sistema | Decisione | Perché (sistema) |", "|---|---|---|---|---|"]
    for es, q, tit, s_, g, mot in sorted(righe, key=lambda t: (t[0] != "SBAGLIATA", t[0] != "giusta", t[2] or "")):
        md.append(f"| {es} | {tit} ({q}) | {s_} | {g} | {mot} |")
    (R / "docs" / "collaudo-incrocio.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(dict(conta))
    for r in righe:
        if r[0] != "da decidere":
            print(r)


if __name__ == "__main__":
    main()
