"""Prova veloce (non cambia il sito): la Library of Congress risponde alle domande per titolo e autore di verifica_anni.py?"""
import json, pathlib, sys, urllib.parse, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "storico"))
import verifica_anni as V
casi = [["x", "The Highwayman", "", 1906, 0, [["q", "Alfred Noyes", 1958, 0, 0, 0]], 0],
        ["x", "Svendborg poems", "", 1926, 0, [["q", "Bertolt Brecht", 1956, 0, 0, 0]], 0],
        ["x", "Jeeves and the Hard-boiled Egg", "", 1917, 0, [["q", "P. G. Wodehouse", 1975, 0, 0, 0]], 0],
        ["x", "The Sun Also Rises", "", 1926, 0, [["q", "Ernest Hemingway", 1961, 0, 0, 0]], 0]]
out = {}
for r in casi:
    out[r[1]] = V.library_of_congress(r)
q = 'bath.title="The Sun Also Rises" and bath.name="Hemingway"'
u = V.SRU + "?" + urllib.parse.urlencode({"version": "1.1", "operation": "searchRetrieve", "query": q, "maximumRecords": "2", "recordSchema": "marcxml"})
out["grezzo"] = urllib.request.urlopen(urllib.request.Request(u, headers=V.UA), timeout=90).read().decode("utf-8", "replace")[:1500]
pathlib.Path("docs/stima-sito/prova-lc-anni.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1))
