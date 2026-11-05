"""Prova temporanea: cercare le edizioni italiane per TITOLO italiano dell'opera (preso da Wikidata)."""
import json, os, sys, time, urllib.parse, urllib.request
KEY = os.environ.get("GOOGLE_BOOKS_KEY", "")
BASE = "https://www.googleapis.com/books/v1/volumes?"
def chiedi(**q):
    if KEY: q["key"] = KEY
    try:
        with urllib.request.urlopen(BASE + urllib.parse.urlencode(q), timeout=60) as r:
            time.sleep(0.5); return json.load(r)
    except Exception as e:
        return {"errore": str(e)}
prove = [("Laura Ingalls Wilder", "La piccola casa nella prateria"), ("Laura Ingalls Wilder", "La casa nella prateria"),
         ("Bertolt Brecht", "L'opera da tre soldi"), ("Bertolt Brecht", "Madre Coraggio e i suoi figli"),
         ("Robert Walser", "La passeggiata"), ("A. A. Milne", "Winnie Puh")]
for nome, titolo in prove:
    cognome = nome.split()[-1]
    for k, q in {"intitle+inauthor": f'intitle:"{titolo}" inauthor:{cognome}',
                 "intitle+inauthor+it": None}.items():
        if q is None:
            r = chiedi(q=f'intitle:"{titolo}" inauthor:{cognome}', langRestrict="it", maxResults=10)
        else:
            r = chiedi(q=q, maxResults=10)
        if "errore" in r:
            print(f"{nome} | {titolo} | {k}: ERRORE {r['errore'][:80]}", file=sys.stderr); continue
        it = [(i["volumeInfo"].get("title"), i["volumeInfo"].get("authors"), i["volumeInfo"].get("publishedDate")) for i in r.get("items", []) if i["volumeInfo"].get("language") == "it"]
        print(f"{nome} | {titolo} | {k}: totale={r.get('totalItems')} in_italiano={len(it)} es={it[:2]}", file=sys.stderr)
