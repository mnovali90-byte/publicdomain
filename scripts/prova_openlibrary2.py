"""Prova 2 (21/11/2026), non cambia il sito. Open Library, secondo giro con i filtri decisi dopo la prova 1.

Prova 1 (docs/registro-prove.md): 794.209 titoli «unici», ma con molto rumore: enti al posto di autori, antologie e
traduzioni uscite dopo la morte, attribuzioni sbagliate. Qui gli stessi dati con tre filtri, uno alla volta, per vedere
quanto pesa ciascuno:
  A. solo persone: l'autore su Wikidata è un essere umano (P31 = Q5);
  B. solo opere con l'anno di prima pubblicazione di Open Library non oltre l'anno di morte (uscite da vivo);
     quelle senza anno si contano a parte;
  C. sopra B, titoli unici per autore (stessa pulizia della prova 1).
Esempi per gli autori più noti, per vedere a occhio se restano opere vere.
Scrive docs/stima-sito/prova-openlibrary-2.json."""
import glob, gzip, io, json, os, re, sys, time, unicodedata, urllib.request
from collections import Counter, defaultdict
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storico")]
import coautori as C  # noqa: E402  (sparql con i tentativi)

inizio = time.time()
out = {}

# i nostri autori e quante opere hanno oggi
autori, nostre, viste = {}, Counter(), set()
for f in glob.glob("data/storico/ricerca/*.json"):
    d = json.load(open(f, encoding="utf8"))
    for r in d["autori"]:
        autori.setdefault(r[0], (r[1], r[2]))
    for r in d["opere"]:   # le opere stanno in più file (una per parola del titolo): si contano una volta sola
        if r[0] in viste:
            continue
        viste.add(r[0])
        for a in r[5] or []:
            nostre[a[0]] += 1
qids = sorted(q for q in autori if re.fullmatch(r"Q\d+", q))
out["nostri_autori"] = len(qids)
out["nostre_opere"] = len(viste)

# 1. codici Open Library
ol = {}
for i in range(0, len(qids), 400):
    v = " ".join("wd:" + q for q in qids[i:i + 400])
    for x in C.sparql(f"SELECT ?a ?ol WHERE {{ VALUES ?a {{ {v} }} ?a wdt:P648 ?ol. }}") or []:
        c = C.v(x, "ol")
        if c and c.endswith("A"):
            ol.setdefault(c, C.q_(C.v(x, "a")))
    time.sleep(0.2)
out["autori_con_codice_open_library"] = len(set(ol.values()))
umani = set()
qs = sorted(set(ol.values()))
for i in range(0, len(qs), 400):
    v = " ".join("wd:" + q for q in qs[i:i + 400])
    for x in C.sparql(f"SELECT ?a WHERE {{ VALUES ?a {{ {v} }} ?a wdt:P31 wd:Q5. }}") or []:
        umani.add(C.q_(C.v(x, "a")))
    time.sleep(0.2)
out["di_cui_persone"] = len(umani)
print("codici Open Library:", len(ol), "per", out["autori_con_codice_open_library"], "autori", flush=True)

# 2. il file delle opere, letto in streaming
URL = "https://openlibrary.org/data/ol_dump_works_latest.txt.gz"
req = urllib.request.Request(URL, headers=C.UA)
righe = tenute = 0
per_autore = defaultdict(list)   # qid -> [(titolo, anno)]
pat = re.compile(r'/authors/(OL\d+A)')
with urllib.request.urlopen(req, timeout=300) as r:
    for riga in io.TextIOWrapper(gzip.GzipFile(fileobj=r), encoding="utf8", errors="replace"):
        righe += 1
        if righe % 2_000_000 == 0:
            print(f"  {righe:,} righe, {tenute:,} tenute, {round((time.time()-inizio)/60,1)} min", flush=True)
        codici = set(pat.findall(riga))
        trovati = {ol[c] for c in codici if c in ol}
        if not trovati:
            continue
        try:
            w = json.loads(riga.rsplit("\t", 1)[1])
        except Exception:  # noqa: BLE001
            continue
        t = (w.get("title") or "").strip()
        if not t:
            continue
        tenute += 1
        anno = None
        m = re.search(r"(\d{4})", str(w.get("first_publish_date") or ""))
        if m:
            anno = int(m.group(1))
        for q in trovati:
            per_autore[q].append((t, anno))
out["righe_lette"] = righe
out["opere_open_library_dei_nostri_autori"] = tenute


# 3. filtri
def pulisci(t):
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = re.split(r"\s*[:;(\[]|(?<=\w{4})\.\s", t)[0]
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"^(the|a|an|il|lo|la|i|gli|le|l|un|una|der|die|das|ein|eine|les|une|el|los|las)\s+", "", t.strip())
    return re.sub(r"\s+", " ", t).strip()


def unici(sel):
    return {q: {pulisci(t) for t, _ in v if pulisci(t)} for q, v in sel.items()}


tutti = {q: v for q, v in per_autore.items()}
pers = {q: v for q, v in tutti.items() if q in umani}
vivo, senza_anno, dopo = {}, 0, 0
for q, v in pers.items():
    m = autori[q][1]
    tenere = []
    for t, a in v:
        if a is None:
            senza_anno += 1
        elif m and a <= m:
            tenere.append((t, a))
        else:
            dopo += 1
    if tenere:
        vivo[q] = tenere
u0, uA, uC = unici(tutti), unici(pers), unici(vivo)
out["passi"] = {
    "0_tutto": {"autori": len(u0), "titoli_unici": sum(map(len, u0.values()))},
    "A_solo_persone": {"autori": len(uA), "titoli_unici": sum(map(len, uA.values()))},
    "B_opere_da_vivo_righe": sum(len(v) for v in vivo.values()),
    "B_scartate_senza_anno": senza_anno, "B_scartate_uscite_dopo_la_morte": dopo,
    "C_titoli_unici_da_vivo": {"autori": len(uC), "titoli_unici": sum(map(len, uC.values()))},
}
out["confronto_oggi_stessi_autori"] = {"oggi": sum(nostre[q] for q in uC), "open_library_da_vivo": sum(map(len, uC.values()))}
fasce = Counter()
for s_ in uC.values():
    n = len(s_)
    fasce["1" if n == 1 else "2-10" if n <= 10 else "11-50" if n <= 50 else "51-200" if n <= 200 else "oltre 200"] += 1
out["autori_per_numero_di_opere_da_vivo"] = dict(fasce)
noti = sorted([q for q in uC if nostre[q] >= 15], key=lambda q: -nostre[q])[:12]
out["esempi_autori_noti"] = [{"qid": q, "nome": autori[q][0], "morte": autori[q][1], "oggi": nostre[q], "open_library_da_vivo": len(uC[q]),
                              "titoli": sorted(uC[q])[:30]} for q in noti]
top = sorted(uC, key=lambda q: -len(uC[q]))[:10]
out["esempi_piu_opere"] = [{"qid": q, "nome": autori[q][0], "oggi": nostre[q], "open_library_da_vivo": len(uC[q]), "titoli": sorted(uC[q])[:20]} for q in top]
out["minuti"] = round((time.time() - inizio) / 60, 1)
os.makedirs("docs/stima-sito", exist_ok=True)
json.dump(out, open("docs/stima-sito/prova-openlibrary-2.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if not isinstance(v, list)}, ensure_ascii=False, indent=1))
