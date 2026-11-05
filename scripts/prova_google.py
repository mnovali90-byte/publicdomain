"""Prova temporanea: quale richiesta a Google Libri trova davvero le edizioni italiane?"""
import json, os, sys, time, urllib.parse, urllib.request
KEY = os.environ.get("GOOGLE_BOOKS_KEY", "")
BASE = "https://www.googleapis.com/books/v1/volumes?"

def chiedi(**q):
    if KEY:
        q["key"] = KEY
    try:
        with urllib.request.urlopen(BASE + urllib.parse.urlencode(q), timeout=60) as r:
            time.sleep(0.5)
            return json.load(r)
    except Exception as e:
        return {"errore": str(e)}

def riassunto(r):
    if "errore" in r:
        return "ERRORE " + r["errore"][:80]
    items = r.get("items") or []
    lingue = {}
    for i in items:
        l = (i.get("volumeInfo") or {}).get("language")
        lingue[l] = lingue.get(l, 0) + 1
    return f"totale={r.get('totalItems')} items={len(items)} lingue={lingue}"

for nome in ["Bertolt Brecht", "Laura Ingalls Wilder"]:
    cons = {
        "A langRestrict=it": dict(q=f'inauthor:"{nome}"', langRestrict="it", maxResults=40),
        "B langRestrict=it + country=IT": dict(q=f'inauthor:"{nome}"', langRestrict="it", country="IT", maxResults=40),
        "C solo country=IT": dict(q=f'inauthor:"{nome}"', country="IT", maxResults=40),
        "D inauthor + parola italiana": dict(q=f'inauthor:"{nome}" traduzione italiano', maxResults=40),
        "E langRestrict=it pagina 2 (start 20)": dict(q=f'inauthor:"{nome}"', langRestrict="it", maxResults=20, startIndex=20),
        "F langRestrict=it pagina 4 (start 60)": dict(q=f'inauthor:"{nome}"', langRestrict="it", maxResults=20, startIndex=60),
    }
    for k, q in cons.items():
        print(f"{nome} | {k}: {riassunto(chiedi(**q))}", file=sys.stderr)
