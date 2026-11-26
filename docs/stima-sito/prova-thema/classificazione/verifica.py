"""Controllo automatico contro le invenzioni: ogni codice deve esistere nella lista Thema 1.7
e ogni frase deve comparire, identica, nel testo della fonte indicata."""
import json, sys, importlib, glob, os
sys.path.insert(0, os.path.dirname(__file__))
P = "/home/claude/mnovali90-byte/publicdomain/docs/stima-sito/prova-thema/"
EN = json.load(open("/tmp/thema_en.json"))
D = {d["q"]: d for d in json.load(open(P + "descrizioni.json"))}
CAMPO = {"g": "generi", "f": "forma", "a": "argomenti", "l": "luogo_narrazione", "p": "periodo", "t": "tipo"}

def testo(d, f):
    if f in ("WPen", "WPit"):
        w = d.get("wikipedia_" + f[2:]); return w["testo"] if w else ""
    if f in ("enwd", "itwd"):
        return d.get("descrizione_wikidata_" + f[:2], "")
    return d.get(CAMPO[f], [])

def tutti():
    L = {}
    for f in sorted(glob.glob(os.path.dirname(__file__) + "/lotto*.py")):
        m = importlib.import_module(os.path.basename(f)[:-3]); L.update(m.L)
    return L

if __name__ == "__main__":
    L = tutti(); err = 0
    for q, (st, cod, alt, nota) in L.items():
        d = D.get(q)
        if not d: print("opera fuori campione", q); err += 1; continue
        for c, f, fr in cod:
            if c not in EN: print(q, "CODICE INESISTENTE", c); err += 1
            t = testo(d, f)
            ok = (fr in t) if isinstance(t, str) else (fr in t)
            if not ok: print(q, c, f, "FRASE NON TROVATA:", fr[:70]); err += 1
        for c in alt:
            if c not in EN: print(q, "ALTERNATIVA INESISTENTE", c); err += 1
    print(f"opere classificate: {len(L)} / {len(D)}, errori: {err}")
