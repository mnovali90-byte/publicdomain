"""Prova 2 Open Library (22/11/2026), non cambia il sito. Quante opere VERE in più per i nostri autori?

La prova 1 (21/11) ha trovato 794.209 «titoli» contro 49.327 opere nostre, ma con molto rumore (enti come autori,
antologie e traduzioni contate come opere, attribuzioni sbagliate) e non si poteva stimare il numero vero.
Questa volta il metodo e la misura sono fissati PRIMA del lancio (decisioni di Marco, 22/11/2026):
1. Solo persone: autori con «istanza di: essere umano» (Wikidata P31 = Q5) e codice Open Library (P648).
2. Niente filtro sull'anno: Open Library spesso dà l'anno di un'edizione tarda o nessun anno, e le opere postume contano
   (Kafka). L'anno si deciderà dopo, con l'incrocio delle fonti (docs/verifica-opere.md).
3. Tolti i titoli che abbiamo già (stessa pulizia del titolo) e segnate a parte le probabili raccolte e antologie
   (parole come «selected», «collected», «works», «opere», «racconti scelti», numeri all'inizio): si contano, non si buttano.
4. La misura: 50 opere candidate estratte a caso (seme fisso), da controllare A MANO dopo il giro: opera vera, dell'autore
   giusto, non un doppione di una che abbiamo. Ne esce una percentuale con il suo margine d'errore, e da lì «X opere vere in
   più». Nessun numero «N volte tanto» senza questa misura.
5. Il file viene da Internet Archive (copia delle esportazioni di Open Library, di solito più veloce del loro server):
   prima si scarica tutto su disco (con ripresa se si interrompe), poi si legge. Se archive.org non risponde, il server di
   Open Library.
Scrive solo docs/stima-sito/prova-openlibrary2.json e docs/stima-sito/campione-openlibrary2.md (rapporto, non registro)."""
import glob, gzip, json, os, random, re, subprocess, sys, time, unicodedata, urllib.request
from collections import Counter, defaultdict
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storico")]
import coautori as C  # noqa: E402  (sparql con i tentativi)

inizio = time.time()
out = {"metodo": "persone (P31=Q5), nessun filtro sull'anno, titoli già nostri tolti, raccolte contate a parte, campione di 50 da controllare a mano"}
FILE = "/tmp/ol_works.txt.gz"


def min_():
    return round((time.time() - inizio) / 60, 1)


# i nostri autori, le opere che hanno oggi e i loro titoli
autori, nostre, viste, titoli_nostri = {}, Counter(), set(), defaultdict(set)


def pulisci(t):
    t = unicodedata.normalize("NFKD", (t or "").lower())
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = re.split(r"\s*[:;(\[]|(?<=\w{4})\.\s", t)[0]
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"^(the|a|an|il|lo|la|i|gli|le|l|un|una|der|die|das|ein|eine|les|une|el|los|las)\s+", "", t.strip())
    return re.sub(r"\s+", " ", t).strip()


for f in glob.glob("data/storico/ricerca/*.json"):
    d = json.load(open(f, encoding="utf8"))
    for r in d["autori"]:
        autori.setdefault(r[0], (r[1], r[2]))
    for r in d["opere"]:
        for a in r[5] or []:
            for t in (r[1], r[2]):
                if t:
                    titoli_nostri[a[0]].add(pulisci(t))
        if r[0] in viste:
            continue
        viste.add(r[0])
        for a in r[5] or []:
            nostre[a[0]] += 1
qids = sorted(q for q in autori if re.fullmatch(r"Q\d+", q))

# 1. codici Open Library, solo per le persone
ol = {}
for i in range(0, len(qids), 400):
    v = " ".join("wd:" + q for q in qids[i:i + 400])
    for x in C.sparql(f"SELECT ?a ?ol WHERE {{ VALUES ?a {{ {v} }} ?a wdt:P31 wd:Q5; wdt:P648 ?ol. }}") or []:
        c = C.v(x, "ol")
        if c and c.endswith("A"):
            ol.setdefault(c, C.q_(C.v(x, "a")))
    time.sleep(0.2)
out["autori_persone_con_codice"] = len(set(ol.values()))
print("codici Open Library (solo persone):", len(ol), "per", out["autori_persone_con_codice"], "autori", min_(), "min", flush=True)

# 2. il file: prima scaricato tutto su disco, da Internet Archive se possibile
def url_archive():
    try:
        u = ("https://archive.org/advancedsearch.php?q=identifier%3Aol_dump_2*&fl%5B%5D=identifier&sort%5B%5D=publicdate+desc"
             "&rows=5&output=json")
        d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=C.UA), timeout=60))
        for doc in d["response"]["docs"]:
            ident = doc["identifier"]
            data = ident.replace("ol_dump_", "")
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", data):
                return f"https://archive.org/download/{ident}/ol_dump_works_{data}.txt.gz"
    except Exception as e:  # noqa: BLE001
        print("archive.org non risponde:", e, flush=True)
    return None


fonti = [u for u in (url_archive(), "https://openlibrary.org/data/ol_dump_works_latest.txt.gz") if u]
scaricato = None
for u in fonti:
    for t in range(4):
        print("scarico", u, "tentativo", t + 1, min_(), "min", flush=True)
        r = subprocess.run(["curl", "-L", "-C", "-", "--fail", "--retry", "5", "--retry-delay", "10", "-sS", "-o", FILE, u])
        if r.returncode == 0:
            scaricato = u
            break
        time.sleep(15)
    if scaricato:
        break
    if os.path.exists(FILE):
        os.remove(FILE)
if not scaricato:
    raise SystemExit("file delle opere non scaricato")
out["file"] = scaricato
out["mb_file"] = round(os.path.getsize(FILE) / 1e6)
out["minuti_scaricamento"] = min_()
print("scaricato:", out["mb_file"], "MB in", min_(), "min", flush=True)

# 3. lettura dal disco
righe = tenute = 0
per_autore = defaultdict(dict)   # qid -> {titolo pulito: (titolo, chiave OL, anno, n autori)}
pat = re.compile(r'/authors/(OL\d+A)')
RACCOLTA = re.compile(r"^\d|\b(selected|collected|complete|works|poems of|stories of|tales of|anthology|omnibus|reader|"
                      r"opere|racconti scelti|poesie scelte|antologia|werke|ausgew[aä]hlte|gesammelte|oeuvres|choix de|obras)\b", re.I)
with gzip.open(FILE, "rt", encoding="utf8", errors="replace") as fh:
    for riga in fh:
        righe += 1
        if righe % 5_000_000 == 0:
            print(f"  {righe:,} righe, {tenute:,} tenute, {min_()} min", flush=True)
        codici = set(pat.findall(riga))
        trovati = {ol[c] for c in codici if c in ol}
        if not trovati:
            continue
        try:
            parti = riga.split("\t")
            w = json.loads(parti[-1])
        except Exception:  # noqa: BLE001
            continue
        t = (w.get("title") or "").strip()
        p = pulisci(t)
        if not p:
            continue
        tenute += 1
        m = re.search(r"(\d{4})", str(w.get("first_publish_date") or ""))
        n_aut = len(w.get("authors") or [])
        for q in trovati:
            if p in titoli_nostri.get(q, set()):
                continue
            per_autore[q].setdefault(p, (t, w.get("key"), int(m.group(1)) if m else None, n_aut))
out["righe_lette"] = righe
out["opere_dei_nostri_autori_in_open_library"] = tenute

# 4. conti
candidate = [(q, p, v) for q, d in per_autore.items() for p, v in d.items()]
raccolte = [c for c in candidate if RACCOLTA.search(c[2][0])]
singole = [c for c in candidate if not RACCOLTA.search(c[2][0])]
out["candidate_titoli_nuovi"] = len(candidate)
out["di_cui_probabili_raccolte"] = len(raccolte)
out["di_cui_singole"] = len(singole)
out["con_piu_autori"] = sum(1 for c in candidate if c[2][3] > 1)
out["senza_anno_in_open_library"] = sum(1 for c in candidate if c[2][2] is None)
out["autori_con_candidate"] = len(per_autore)
out["stessi_autori_opere_oggi"] = sum(nostre[q] for q in per_autore)
out["minuti"] = min_()

# 5. campione di 50 da controllare a mano (seme fisso), dalle «singole»
random.seed(20261122)
camp = random.sample(singole, min(50, len(singole)))
out["campione"] = [{"autore": autori.get(q, ("?",))[0], "qid": q, "titolo": v[0], "open_library": f"https://openlibrary.org{v[1]}",
                    "anno_open_library": v[2], "autori_dell_opera": v[3], "esito": None} for q, p, v in camp]
os.makedirs("docs/stima-sito", exist_ok=True)
json.dump(out, open("docs/stima-sito/prova-openlibrary2.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
righe_md = ["# Prova 2 Open Library: campione da controllare a mano", "",
            f"{out['candidate_titoli_nuovi']:,} titoli nuovi per {out['autori_con_candidate']:,} autori "
            f"({out['di_cui_singole']:,} singoli, {out['di_cui_probabili_raccolte']:,} probabili raccolte). "
            "Per ognuna delle 50: opera vera? dell'autore giusto? non un doppione di un'opera che abbiamo (traduzione)?", "",
            "| # | Autore | Titolo | Anno OL | Esito |", "|---|---|---|---|---|"]
righe_md += [f"| {i} | {c['autore']} | [{c['titolo']}]({c['open_library']}) | {c['anno_open_library'] or ''} | |" for i, c in enumerate(out["campione"], 1)]
open("docs/stima-sito/campione-openlibrary2.md", "w", encoding="utf8").write("\n".join(righe_md) + "\n")
print(json.dumps({k: v for k, v in out.items() if not isinstance(v, list)}, ensure_ascii=False, indent=1))
