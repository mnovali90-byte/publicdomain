"""Prova (20/11/2026), non cambia il sito. Tre misure sullo Storico, decise con Marco:
1. ENCICLOPEDIE E RIVISTE (da togliere da Già pubblici): opere dell'archivio che su Wikidata sono enciclopedie,
   dizionari, periodici, riviste, giornali, riviste scientifiche, manuali di stile, almanacchi (P31 o sottoclassi).
2. TESTI ANTICHI SENZA AUTORE: opere senza autore con data (anonimo, «valore sconosciuto», «vari autori», enti,
   divinità) con la data di creazione (P571) e la prima data di pubblicazione (P577) di Wikidata, da rivedere a mano.
3. TITOLO ORIGINALE: le opere libere solo negli USA e non confermate, cercate con il titolo originale e le fonti forti
   (storico/verifica_anni.py, fonti_forti). Conferme = edizione entro il 1930, stesso titolo, stesso autore.
Scrive docs/stima-sito/prova-pulizia.json."""
import glob, json, os, re, sys, time
from collections import Counter
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storico")]
import verifica_anni as va      # noqa: E402
import verifica_anni_usa as V   # noqa: E402
import coautori as C            # noqa: E402  (sparql con i tentativi)

inizio = time.time()
BUDGET = 115 * 60
arch = C.archivio()
qids = sorted(q for q in arch if re.fullmatch(r"Q\d+", q))
out = {}

# 1. enciclopedie e riviste
CLASSI = {"Q5292": "enciclopedia", "Q23622": "dizionario", "Q1002697": "periodico", "Q41298": "rivista", "Q11032": "giornale",
          "Q5633421": "rivista scientifica", "Q737498": "rivista accademica", "Q1135389": "manuale di stile", "Q29934": "almanacco",
          "Q13136": "opera di consultazione", "Q1371849": "dizionario biografico"}
vals_c = " ".join("wd:" + c for c in CLASSI)
ref, ko = {}, 0
for i in range(0, len(qids), 300):
    v = " ".join("wd:" + q for q in qids[i:i + 300])
    r = C.sparql(f"SELECT ?o ?c WHERE {{ VALUES ?o {{ {v} }} VALUES ?c {{ {vals_c} }} ?o wdt:P31/wdt:P279* ?c. }}")
    if r is None:
        ko += 1; continue
    for x in r:
        ref.setdefault(C.q_(C.v(x, "o")), set()).add(CLASSI[C.q_(C.v(x, "c"))])
    time.sleep(0.5)
out["consultazione"] = {"pezzi_mancati": ko, "n": len(ref),
                        "opere": sorted(([q, arch[q][2] or arch[q][1], sorted(t), arch[q][4]] for q, t in ref.items()), key=lambda x: -(x[3] or 0))}
print("enciclopedie e riviste:", len(ref), "| pezzi mancati", ko, flush=True)

# 2. testi senza autore con data
def senza_autore(r):
    return not r[5] or all(a[2] is None and not a[3] for a in r[5])
anon = [q for q in qids if senza_autore(arch[q])]
date_, ko = {}, 0
for i in range(0, len(anon), 300):
    v = " ".join("wd:" + q for q in anon[i:i + 300])
    r = C.sparql(f"SELECT ?o (MIN(?c) AS ?creato) (MIN(?p) AS ?pubbl) WHERE {{ VALUES ?o {{ {v} }} "
                 f"OPTIONAL {{ ?o wdt:P571 ?c }} OPTIONAL {{ ?o wdt:P577 ?p }} }} GROUP BY ?o")
    if r is None:
        ko += 1; continue
    for x in r:
        date_[C.q_(C.v(x, "o"))] = [C.anno(C.v(x, "creato")), C.anno(C.v(x, "pubbl"))]
    time.sleep(0.5)
out["senza_autore"] = {"pezzi_mancati": ko, "n": len(anon),
                       "opere": sorted(([q, arch[q][2] or arch[q][1], [a[1] for a in arch[q][5]][:2], arch[q][3]] + date_.get(q, [None, None])
                                        for q in anon), key=lambda x: -(arch[x[0]][4] or 0))}
print("senza autore con data:", len(anon), "| pezzi mancati", ko, flush=True)

# 3. titolo originale
ver = json.load(open("data/storico/anni_verificati.json", encoding="utf8"))
lista = va.da_controllare()
da_fare = sorted((q for q, v in ver.items() if v[0] in ("nd", "no") and q in lista and q not in ref),
                 key=lambda q: -(arch[q][4] or 0))     # prima le più note
orig = va.titoli_originali(da_fare)
idx = V.indice_cce(list(range(1923, va.LIMITE + 1)))
print("da provare:", len(da_fare), "| con titolo originale:", len(orig), flush=True)
conta, conferme, fatte = Counter(), [], 0
for q in da_fare:
    if time.time() - inizio > BUDGET:
        break
    a, f, provate = va.fonti_forti(arch[q], orig, idx, V)
    fatte += 1
    if a:
        conta["confermate"] += 1; conta["per fonte: " + f] += 1
        conferme.append([q, arch[q][2] or arch[q][1], orig.get(q, [None, None])[1], [x[1] for x in arch[q][5]][:2], arch[q][3], f, a, arch[q][4]])
    else:
        conta["niente"] += 1
    if fatte % 200 == 0:
        print(fatte, dict(conta), flush=True)
out["titolo_originale"] = {"fatte": fatte, "su": len(da_fare), "con_titolo_originale": len(orig), "esiti": dict(conta), "conferme": conferme}
out["minuti"] = int((time.time() - inizio) / 60)
json.dump(out, open("docs/stima-sito/prova-pulizia.json", "w", encoding="utf8"), ensure_ascii=False, indent=0)
print("fatto in", out["minuti"], "minuti |", dict(conta), "| fatte", fatte, "su", len(da_fare))
