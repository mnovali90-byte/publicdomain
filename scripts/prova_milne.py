import sys, json
sys.path.insert(0, "scripts")
import sbn
LAB, BF, SAME, VAL, ITA = sbn.LAB, sbn.BF, sbn.SAME, sbn.VAL, sbn.ITA
q = lambda s: sbn.interroga(s)
print("VIAF:", sbn.codici_viaf(["Q207036"]))
for t in ("Milne", "milne"):
    r = q(f'SELECT DISTINCT ?a ?l WHERE {{ ?a <{LAB}> ?l . ?l bif:contains "\'{t}\'" . FILTER(CONTAINS(STR(?a), "/resource/Agent/")) }} LIMIT 300')
    print(t, len(r))
    for x in r:
        if "lan" in x["l"]["value"].lower() or "a. a" in x["l"]["value"].lower():
            n = q(f'SELECT (COUNT(DISTINCT ?w) AS ?n) WHERE {{ VALUES ?a {{ <{x["a"]["value"]}> }} ?c <{BF}agent> ?a . ?w <{BF}contribution> ?c . ?w <{BF}language> ?ln . ?ln <{VAL}> <{ITA}> }}')[0]["n"]["value"]
            print("  ", x["a"]["value"], "|", x["l"]["value"], "| it:", n)
    break
