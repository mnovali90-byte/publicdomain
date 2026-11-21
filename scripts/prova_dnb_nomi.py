"""Prova (21/11/2026), non cambia il sito. Due misure su Già pubblici, dopo le segnalazioni della revisione grafica:

1. VOCI DI DIZIONARIO (DNB e simili). Nell'archivio restano circa 10.900 voci del Dictionary of National Biography
   («Joyce, George (DNB00)»): la regola delle enciclopedie (storico/coautori.py, CONSULTAZIONE) non le prende.
   a) Che classe hanno su Wikidata (P31) e dove sono pubblicate (P1433)? Su un campione di 300 voci DNB.
   b) Le classi candidate («voce biografica», «voce di enciclopedia», «voce di dizionario», con le sottoclassi):
      quante opere dell'archivio prenderebbero in tutto, e quali NON sono voci DNB (per vedere se la regola
      toglierebbe anche opere vere: sono elencate tutte, con il titolo).
2. NOMI ITALIANI DEGLI AUTORI. In Già pubblici gli autori hanno solo il nome inglese («Leo Tolstoy», «Homer»):
   per tutti gli autori con codice Wikidata, quanti hanno un nome italiano diverso, con esempi.
Scrive docs/stima-sito/prova-dnb-nomi.json."""
import glob, json, os, re, sys, time
from collections import Counter
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storico")]
import coautori as C  # noqa: E402  (sparql con i tentativi)

inizio = time.time()
out = {}

# archivio: titoli e autori dai file della ricerca
opere, autori = {}, {}
for f in glob.glob("data/storico/ricerca/*.json"):
    d = json.load(open(f, encoding="utf8"))
    for r in d["opere"]:
        opere.setdefault(r[0], r)
    for r in d["autori"]:
        autori.setdefault(r[0], r)
DNB = re.compile(r"\((DNB\d\d|EB1911|[A-Z][A-Za-z]{1,8}\d{2,4})\)\s*$")
dnb = sorted(q for q, r in opere.items() if re.fullmatch(r"Q\d+", q) and DNB.search(r[1] or ""))
out["voci_con_sigla_nel_titolo"] = len(dnb)

# 1a. classi e «pubblicato in» di un campione
camp = dnb[::max(1, len(dnb) // 300)][:300]
cl, pub = Counter(), Counter()
v = " ".join("wd:" + q for q in camp)
r = C.sparql(f"SELECT ?o ?c ?cL WHERE {{ VALUES ?o {{ {v} }} ?o wdt:P31 ?c. ?c rdfs:label ?cL. FILTER(LANG(?cL)='en') }}") or []
for x in r:
    cl[(C.q_(C.v(x, "c")), C.v(x, "cL"))] += 1
r = C.sparql(f"SELECT ?o ?p ?pL WHERE {{ VALUES ?o {{ {v} }} ?o wdt:P1433 ?p. ?p rdfs:label ?pL. FILTER(LANG(?pL)='en') }}") or []
for x in r:
    pub[(C.q_(C.v(x, "p")), C.v(x, "pL"))] += 1
out["campione"] = len(camp)
out["classi_campione"] = [[q, l, n] for (q, l), n in cl.most_common(15)]
out["pubblicato_in_campione"] = [[q, l, n] for (q, l), n in pub.most_common(15)]

# 1b. classi candidate su tutto l'archivio
CAND = {"Q19389637": "voce biografica", "Q13433827": "voce di enciclopedia", "Q1580166": "voce di dizionario"}
for q, l in [(a, b) for (a, b), n in cl.most_common(5)]:
    CAND.setdefault(q, l)
qids = sorted(q for q in opere if re.fullmatch(r"Q\d+", q))
vals = " ".join("wd:" + c for c in CAND)
prese = {}
for i in range(0, len(qids), 300):
    v = " ".join("wd:" + q for q in qids[i:i + 300])
    r = C.sparql(f"SELECT ?o ?c WHERE {{ VALUES ?o {{ {v} }} VALUES ?c {{ {vals} }} ?o wdt:P31/wdt:P279* ?c. }}")
    for x in r or []:
        prese.setdefault(C.q_(C.v(x, "o")), set()).add(CAND[C.q_(C.v(x, "c"))])
    time.sleep(0.3)
dnbs = set(dnb)
out["classi_candidate"] = CAND
out["prese_in_tutto"] = len(prese)
out["prese_per_classe"] = Counter(c for s in prese.values() for c in s)
out["prese_con_sigla"] = len([q for q in prese if q in dnbs])
out["sigla_non_prese"] = [[q, opere[q][1]] for q in dnb if q not in prese][:60]
out["prese_senza_sigla"] = sorted([[q, opere[q][1], opere[q][2], opere[q][4], sorted(prese[q])] for q in prese if q not in dnbs], key=lambda x: -(x[3] or 0))

# 2. nomi italiani degli autori
aq = sorted(q for q in autori if re.fullmatch(r"Q\d+", q))
it = {}
for i in range(0, len(aq), 300):
    v = " ".join("wd:" + q for q in aq[i:i + 300])
    r = C.sparql(f"SELECT ?a ?l WHERE {{ VALUES ?a {{ {v} }} ?a rdfs:label ?l. FILTER(LANG(?l)='it') }}")
    for x in r or []:
        it[C.q_(C.v(x, "a"))] = C.v(x, "l")
    time.sleep(0.3)
diversi = [[q, autori[q][1], it[q], autori[q][3]] for q in aq if q in it and it[q].strip() != autori[q][1].strip()]
diversi.sort(key=lambda x: -x[3])
out["autori_con_codice"] = len(aq)
out["con_nome_italiano"] = len(it)
out["nome_italiano_diverso"] = len(diversi)
out["esempi_diversi_piu_presenti"] = diversi[:80]
out["minuti"] = round((time.time() - inizio) / 60, 1)
os.makedirs("docs/stima-sito", exist_ok=True)
json.dump(out, open("docs/stima-sito/prova-dnb-nomi.json", "w", encoding="utf8"), ensure_ascii=False, indent=1, default=list)
print(json.dumps({k: out[k] for k in ("voci_con_sigla_nel_titolo", "prese_in_tutto", "prese_con_sigla", "autori_con_codice", "nome_italiano_diverso", "minuti")}, ensure_ascii=False))
