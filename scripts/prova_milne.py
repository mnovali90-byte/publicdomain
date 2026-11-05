import sys
sys.path.insert(0, "scripts")
import sbn
for nome, n, m in (("A. A. Milne", "1882-01-18", "1956-01-31"), ("B. R. Ambedkar", "1891-04-14", "1956-12-06")):
    cogn = nome.split()[-1]
    r = sbn.interroga(f'SELECT DISTINCT ?a ?l WHERE {{ ?a <{sbn.LAB}> ?l . ?l bif:contains "\'{cogn}\'" . FILTER(CONTAINS(STR(?a), "/resource/Agent/")) }} LIMIT 1000')
    print(nome, "schede col cognome:", len(r))
    for x in r:
        l = x["l"]["value"]
        if sbn.nome_compatibile(nome, l):
            print("  compatibile:", x["a"]["value"].rsplit("/",1)[-1], "|", l, "| anni:", sbn.anni_compatibili(l, n, m))
