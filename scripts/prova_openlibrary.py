"""Prova (21/11/2026), non cambia il sito. Quante opere in più avrebbero i nostri autori con Open Library?

Già pubblici ha 56.516 opere: solo quelle con una scheda su Wikidata. In Europa conta la morte dell'autore,
quindi per i nostri autori (data di morte già verificata) ogni loro opera è libera: Open Library (CC0) ne elenca molte di più.
Come:
1. Da Wikidata il codice Open Library (P648, solo quelli che finiscono in «A» = autore) dei nostri autori.
2. Si legge per intero il file mensile delle opere di Open Library (ol_dump_works_latest.txt.gz, circa 2,5 GB
   compressi), in streaming senza salvarlo, e si tengono le opere di quegli autori.
3. Doppioni: Open Library ha già una riga per «opera» (non per edizione), ma la stessa opera compare spesso più volte.
   Si contano i titoli unici per autore dopo una pulizia (minuscole, niente accenti e punteggiatura, niente articolo
   iniziale, niente sottotitolo dopo «:» o «.»). È una stima: traduzioni con titolo diverso restano separate.
4. Confronto con le opere che abbiamo oggi per gli stessi autori, ed esempi per gli autori con più opere.
Scrive docs/stima-sito/prova-openlibrary.json."""
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


# 3. titoli unici
def pulisci(t):
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = re.split(r"\s*[:;(\[]|(?<=\w{4})\.\s", t)[0]
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"^(the|a|an|il|lo|la|i|gli|le|l|un|una|der|die|das|ein|eine|le|les|la|un|une|el|los|las)\s+", "", t.strip())
    return re.sub(r"\s+", " ", t).strip()


unici = {q: {pulisci(t) for t, _ in v if pulisci(t)} for q, v in per_autore.items()}
tot_unici = sum(len(s) for s in unici.values())
out["titoli_unici_stimati"] = tot_unici
out["autori_con_opere_in_open_library"] = len(unici)
# fasce: quante opere per autore
fasce = Counter()
for s in unici.values():
    n = len(s)
    fasce["1" if n == 1 else "2-10" if n <= 10 else "11-50" if n <= 50 else "51-200" if n <= 200 else "oltre 200"] += 1
out["autori_per_numero_di_opere"] = dict(fasce)
# confronto con oggi, sugli stessi autori
stessi = list(unici)
out["confronto_stessi_autori"] = {"oggi": sum(nostre[q] for q in stessi), "open_library_unici": tot_unici}
# 4. esempi
top = sorted(unici, key=lambda q: -len(unici[q]))[:15]
noti = [q for q in unici if nostre[q] >= 15]
camp = sorted(noti, key=lambda q: -nostre[q])[:10]
out["esempi_piu_opere"] = [{"qid": q, "nome": autori[q][0], "oggi": nostre[q], "open_library": len(unici[q]),
                            "titoli": sorted(unici[q])[:25]} for q in top]
out["esempi_autori_noti"] = [{"qid": q, "nome": autori[q][0], "oggi": nostre[q], "open_library": len(unici[q]),
                              "titoli": sorted(unici[q])[:25]} for q in camp]
out["minuti"] = round((time.time() - inizio) / 60, 1)
os.makedirs("docs/stima-sito", exist_ok=True)
json.dump(out, open("docs/stima-sito/prova-openlibrary.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if not isinstance(v, list)}, ensure_ascii=False, indent=1))
