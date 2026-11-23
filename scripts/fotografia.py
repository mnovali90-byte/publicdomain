"""FOTOGRAFIA DELLO STATO GIURIDICO (passo 3 di docs/giri-automatici.md, 22/11/2026).

Per ogni opera di Già pubblici e per ogni autore delle liste del radar salva, paese per paese, il risultato
(libero / dal / da verificare / non determinato), il perché (la regola usata) e i dati usati (anno di uscita,
anni di morte, fonte USA). In cima: la data, l'anno su cui è calcolata e la versione delle regole
(impronta di assets/regole.js, che scripts/regole.py scrive: se cambia una regola o una costante, cambia l'impronta).

Serve a scripts/confronta_fotografia.py: a ogni giro la fotografia nuova si confronta con la vecchia e si vede subito
chi cambia stato e perché (dato corretto, regola cambiata, o cambio atteso del 1° gennaio).

Uso: python3 scripts/fotografia.py [uscita.json] [--anno 2027]
     senza argomenti scrive data/fotografia.json.gz (compressa: circa 1,7 MB) con l'anno di oggi; con --anno simula un altro anno (prova del cambio d'anno).
"""
import glob, gzip, hashlib, json, re, sys
from datetime import date
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE / "scripts"))
import regole as R  # noqa: E402

PAESI = ["it", "fr", "de", "uk", "es", "us"]
PAESI_AUTORE = ["it", "fr", "de", "uk", "es"]


def leggi(p, vuoto):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return vuoto


def versione_regole():
    return hashlib.sha1(R.esporta_js(RADICE / "assets" / "regole.js").encode("utf-8")).hexdigest()[:12]


def fotografia(anno):
    reg = leggi(RADICE / "data" / "registro" / "opere.json", {})
    coaut, ver = reg.get("coautori", {}), reg.get("usa", {})
    mpf = set(leggi(RADICE / "data" / "registro" / "mpf.json", {}).get("autori", {}))
    righe = {}
    for f in sorted(glob.glob(str(RADICE / "data" / "storico" / "ricerca" / "*.json"))):
        for r in leggi(f, {}).get("opere", []):
            righe.setdefault(r[0], r)
    opere = {}
    for q, r in sorted(righe.items()):
        o = R.opera_da_riga(r, coaut, reg.get("opere", {}))
        st = [R.stato_opera(o, c, anno, mpf, ver) for c in PAESI]
        v = ver.get(q)
        opere[q] = {
            "t": r[1],
            "dati": {"y": o["y"], "morti": [a["m"] for a in o["au"]], "antica": o.get("antica"),
                     "usa": v[1] if v and v[0] is not None else None, "mpf": any(a["q"] in mpf for a in o["au"])},
            "stato": {c: [x["s"], x.get("y"), x.get("r")] for c, x in zip(PAESI, st)},
        }
    autori = {}
    for f in sorted(glob.glob(str(RADICE / "data" / "[0-9]*.json")) + glob.glob(str(RADICE / "data" / "es-[0-9]*.json"))):
        for a in leggi(f, {}).get("autori", []):
            m = re.match(r"-?\d+", str(a.get("morte") or ""))
            if not m or a["wikidata"] in autori:
                continue
            morte, e_mpf = int(m.group(0)), a["wikidata"] in mpf
            st = {}
            for c in PAESI_AUTORE:
                y = R.anno_libero(morte, c, e_mpf)
                st[c] = ["si" if y <= anno else "dal", y, ("fr_morto_per_la_francia" if c == "fr" and e_mpf else
                                                           "spagna_80_anni" if R.anni_protezione(morte, c) != R.ANNI_DOPO_MORTE
                                                           else "morte")]
            if R.nota_trattato(a.get("paesi") or [], morte, anno):
                st["it"][2] = "morte_con_nota_trattato"
            autori[a["wikidata"]] = {"t": a.get("nome"), "lista": Path(f).stem,
                                     "dati": {"morte": morte, "mpf": e_mpf, "paesi": a.get("paesi") or []}, "stato": st}
    return {"fatta": date.today().isoformat(), "anno": anno, "regole": versione_regole(),
            "n_opere": len(opere), "n_autori": len(autori), "opere": opere, "autori": autori}


if __name__ == "__main__":
    args = sys.argv[1:]
    anno = date.today().year
    if "--anno" in args:
        i = args.index("--anno")
        anno = int(args[i + 1])
        del args[i:i + 2]
    uscita = Path(args[0]) if args else RADICE / "data" / "fotografia.json.gz"
    f = fotografia(anno)
    testo = json.dumps(f, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    uscita.write_bytes(gzip.compress(testo, 9, mtime=0) if uscita.suffix == ".gz" else testo)
    print(f"fotografia: {f['n_opere']} opere e {f['n_autori']} autori, anno {anno}, regole {f['regole']} -> {uscita}")
