"""Controllo automatico contro le invenzioni: ogni codice deve esistere nella lista Thema 1.7
e ogni frase deve comparire, identica, nel testo della fonte indicata."""
import json, sys, importlib, glob, os
sys.path.insert(0, os.path.dirname(__file__))
P = "/home/claude/mnovali90-byte/publicdomain/docs/stima-sito/prova-thema/"
EN = json.load(open("/tmp/thema_en.json"))
D = {d["q"]: d for d in json.load(open(P + "descrizioni.json"))}
CAMPO = {"g": "generi", "f": "forma", "a": "argomenti", "l": "luogo_narrazione", "p": "periodo", "t": "tipo"}

D2 = {d["q"]: d for d in json.load(open(P + "descrizioni2.json"))} if os.path.exists(P + "descrizioni2.json") else {}
FONTI2 = {"OL:a": ("openlibrary", "argomenti"), "OL:l": ("openlibrary", "luoghi"), "OL:p": ("openlibrary", "periodi"), "OL:d": ("openlibrary", "descrizione"),
          "WS": ("wikisource", "categorie"), "GND:c": ("gnd", "categorie"), "GND:f": ("gnd", "forma"), "GND:t": ("gnd", "argomenti")}

def testo(d, f):
    q = d["q"]
    if f.startswith("O:"):
        o = D2.get(q, {}).get("originale", {})
        return testo(dict(o, q="__"), f[2:]) if o else ""
    if f == "PI":
        return D2.get(q, {}).get("pubblicato_in", [])
    if f in FONTI2:
        a, b = FONTI2[f]; return D2.get(q, {}).get(a, {}).get(b, "" if b == "descrizione" else [])
    if f in ("WPen", "WPit"):
        w = d.get("wikipedia_" + f[2:]); return w["testo"] if w else ""
    if f in ("enwd", "itwd"):
        return d.get("descrizione_wikidata_" + f[:2], "")
    return d.get(CAMPO[f], [])

NOMI_FONTE = {"OL": "Open Library", "WS": "Wikisource tedesca (categorie)", "GND": "Biblioteca nazionale tedesca (GND)", "PI": "Wikidata: pubblicato in"}

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
