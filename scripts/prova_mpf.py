"""Prova (21/11/2026), non cambia il sito. «Morti per la Francia»: si possono riconoscere con dati aperti?

In Francia gli autori dichiarati «mort pour la France» hanno 30 anni di protezione in più (CPI L123-10).
Oggi il sito mette solo un avviso generico a chi è morto nel 1939-1945. Su Wikidata il titolo è registrato
come «premio ricevuto» (P166) = mort pour la France (Q3324507): per esempio Saint-Exupéry (Q2908).

Misure:
1. Quante persone su Wikidata hanno P166 = Q3324507, divise per anno di morte (1914-18, 1939-45, altri anni).
2. Quanti dei NOSTRI autori lo hanno: Già pubblici (archivio) + liste 2027 e 2028. Elenco completo con nome e anno.
3. Controllo di completezza: gli autori che Wikisource francese marca col modello «Auteur Mort pour la France»
   (lista fatta a mano dai volontari, presa dalla API di Wikisource). Quanti hanno il titolo su Wikidata e
   quali no: se mancano in tanti, Wikidata da solo non basta.
4. Quanti autori di Wikidata hanno già la data di libertà in Francia calcolata con questo criterio
   (P6216 stato del diritto d'autore, qualificatore P1013 = mort pour la France).
Scrive docs/stima-sito/prova-mpf.json."""
import glob, json, os, sys, time, urllib.parse, urllib.request
from collections import Counter
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storico")]
import coautori as C  # noqa: E402  (sparql con i tentativi)

MPF = "Q3324507"
inizio = time.time()
out = {"titolo_wikidata": MPF}

# 1. tutte le persone con il titolo
r = C.sparql(f"""SELECT ?p ?pL (YEAR(MIN(?m)) AS ?anno) WHERE {{ ?p wdt:P166 wd:{MPF}. OPTIONAL {{ ?p wdt:P570 ?m. }}
  OPTIONAL {{ ?p rdfs:label ?pL. FILTER(LANG(?pL)='fr') }} }} GROUP BY ?p ?pL""") or []
tutti = {C.q_(C.v(x, "p")): (C.v(x, "pL"), int(C.v(x, "anno")) if C.v(x, "anno") else None) for x in r}
fasce = Counter("1914-1918" if a and 1914 <= a <= 1919 else "1939-1945" if a and 1939 <= a <= 1946 else
                "senza anno" if not a else "altri anni" for _, a in tutti.values())
out["persone_con_titolo"] = len(tutti)
out["per_periodo"] = dict(fasce)

# 2. i nostri autori
nostri = {}
for f in glob.glob("data/storico/ricerca/*.json"):
    for row in json.load(open(f, encoding="utf8"))["autori"]:
        nostri.setdefault(row[0], (row[1], row[2], "già pubblici"))
for f in ("data/2027.json", "data/2028.json"):
    if os.path.exists(f):
        d = json.load(open(f, encoding="utf8"))
        for a in d["autori"]:
            nostri.setdefault(a["wikidata"], (a["nome"], int(a["morte"][:4]), os.path.basename(f)[:4]))
presi = sorted(((q,) + nostri[q] for q in nostri if q in tutti), key=lambda x: (x[2] or 0, x[1]))
out["nostri_autori"] = len(nostri)
out["nostri_con_titolo"] = len(presi)
out["nostri_con_titolo_per_lista"] = dict(Counter(x[3] for x in presi))
out["elenco_nostri"] = [{"qid": q, "nome": n, "morte": m, "lista": l} for q, n, m, l in presi]
morti_guerra = [q for q, (n, m, l) in nostri.items() if m and (1914 <= m <= 1919 or 1939 <= m <= 1946)]
out["nostri_morti_in_guerra"] = len(morti_guerra)


# 3. confronto con Wikisource francese
def get(url):
    req = urllib.request.Request(url, headers=C.UA)
    for i in range(4):
        try:
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as e:  # noqa: BLE001
            print("riprovo", e)
            time.sleep(5 * (i + 1))
    return {}


ws, cont = [], {}
while True:
    p = {"action": "query", "list": "embeddedin", "eititle": "Modèle:Auteur Mort pour la France", "eilimit": "500",
         "format": "json", **cont}
    d = get("https://fr.wikisource.org/w/api.php?" + urllib.parse.urlencode(p))
    ws += [x["title"] for x in d.get("query", {}).get("embeddedin", []) if x.get("ns") == 102]
    if "continue" not in d:
        break
    cont = d["continue"]
ws_q = {}
for i in range(0, len(ws), 50):
    p = {"action": "query", "prop": "pageprops", "ppprop": "wikibase_item", "titles": "|".join(ws[i:i + 50]), "format": "json"}
    d = get("https://fr.wikisource.org/w/api.php?" + urllib.parse.urlencode(p))
    for pg in d.get("query", {}).get("pages", {}).values():
        ws_q[pg["title"]] = pg.get("pageprops", {}).get("wikibase_item")
out["wikisource_autori_marcati"] = len(ws)
out["wikisource_con_wikidata"] = sum(1 for q in ws_q.values() if q)
out["wikisource_con_titolo_su_wikidata"] = sum(1 for q in ws_q.values() if q in tutti)
out["wikisource_senza_titolo_su_wikidata"] = sorted(t for t, q in ws_q.items() if q and q not in tutti)
out["wikisource_tra_i_nostri"] = sorted(f"{t} ({q})" for t, q in ws_q.items() if q in nostri)
out["wikisource_tra_i_nostri_senza_titolo"] = sorted(f"{t} ({q})" for t, q in ws_q.items() if q in nostri and q not in tutti)

# 4. date di libertà francesi già calcolate su Wikidata con questo criterio
r = C.sparql(f"""SELECT (COUNT(DISTINCT ?p) AS ?n) WHERE {{ ?p p:P6216 ?s. ?s pq:P1013 wd:{MPF}. }}""") or []
out["con_stato_diritti_criterio_mpf"] = int(C.v(r[0], "n")) if r else None

out["minuti"] = round((time.time() - inizio) / 60, 1)
os.makedirs("docs/stima-sito", exist_ok=True)
json.dump(out, open("docs/stima-sito/prova-mpf.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if not isinstance(v, list)}, ensure_ascii=False, indent=1))
