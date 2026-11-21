"""Una tantum (21/11/2026): aggiunge i ritratti degli autori (Wikidata P18, licenza libera su Commons) ai libri USA già
raccolti in data/us-<anno>.json, senza rifare la raccolta, poi ricrea le pagine. Da qui in avanti lo fa scripts/opere.py."""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import opere

for f in sorted(glob.glob("data/us-[0-9]*.json")):
    d = json.load(open(f, encoding="utf8"))
    trovati, tot = opere.foto_autori(d["opere"])
    print(f, "ritratti:", trovati, "su", tot, "autori")
    for o in d["opere"][:12]:
        print("   ", o["titolo"][:40], "|", ", ".join(a["nome"] + (" ✓" if a.get("foto") else " ✗") for a in o.get("autori", [])))
    json.dump(d, open(f, "w", encoding="utf8"), ensure_ascii=False, indent=1)

import pagine
pagine.main()
