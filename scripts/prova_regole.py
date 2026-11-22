"""Prova delle regole per paese (21/11/2026). Si ferma con errore se qualcosa non torna.

1. GEMELLI: assets/regole.js (usato da radar e Già pubblici) deve dare gli stessi risultati di scripts/regole.py,
   su tutti gli anni di morte dal -500 al 2030, tutti i paesi, e su tutti gli autori veri delle liste (con i nomi dei paesi
   come li vede il radar, cioè dopo la sua traduzione nei nomi attuali).
2. PRIMA E DOPO: per ogni autore delle liste confronta la regola vecchia dell'Italia (quella delle schede prima del
   21/11/2026: solo paesi alleati, lista vecchia) con la nuova, e scrive le differenze con il motivo.
Uso: python3 scripts/prova_regole.py [--prima-dopo [--differenze file.json]]"""
import glob, json, re, subprocess, sys, tempfile
from datetime import date
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE / "scripts"))
import regole as R  # noqa: E402

OGGI = date.today().year
errori = []

# ---------------------------------------------------------------- 1. gemelli Python / browser
R.esporta_js(RADICE / "assets" / "regole.js")
radar = (RADICE / "radar" / "index.html").read_text(encoding="utf-8")
i, j = radar.index("const norm = "), radar.index("\n", radar.index("const norm = "))
norm_js = radar[i:j]
i = radar.index("const PAESI = {")
j = radar.index("\n", radar.index("const PAESE_MODERNO = "))
paesi_js = radar[i:j]

autori = []
for f in sorted(glob.glob(str(RADICE / "data" / "[0-9]*.json")) + glob.glob(str(RADICE / "data" / "es-[0-9]*.json"))):
    for a in json.load(open(f, encoding="utf-8")).get("autori", []):
        m = re.match(r"-?\d+", str(a.get("morte") or ""))
        if m:
            autori.append({"q": a["wikidata"], "n": a.get("nome"), "m": int(m.group(0)), "p": a.get("paesi") or [], "f": Path(f).name})

casi = {"morti": list(range(-500, 2031)), "anni": list(range(1900, 2101)), "autori": autori, "oggi": OGGI}
js = (RADICE / "assets" / "regole.js").read_text(encoding="utf-8")
CORPO = r"""
const REGOLE_PAESI = window.REGOLE_PAESI;
const paeseModerno = (nome) => PAESE_MODERNO.get(norm(nome)) || nome;
const C = JSON.parse(require("fs").readFileSync(process.argv[2], "utf8"));
const out = { al: [], mo: [], usa: [], ver: [] };
for (const m of C.morti) for (const p of ["it", "fr", "de", "uk", "es"]) for (const f of [false, true]) out.al.push(REGOLE_PAESI.annoLibero(m, p, f));
for (const y of C.anni) { for (const p of ["it", "es"]) out.mo.push(REGOLE_PAESI.mortiLiberiNel(y, p)); out.usa.push(REGOLE_PAESI.annoLiberoUsa(y), REGOLE_PAESI.pubblicateLibereUsaNel(y)); }
for (const a of C.autori) out.ver.push(REGOLE_PAESI.italiaDaVerificare(a.p, a.m, C.oggi));   // il radar usa a.paesiWd: i nomi di Wikidata
console.log(JSON.stringify(out));
"""
prog = "const window = {};\n" + js + "\n" + norm_js + "\n" + paesi_js + "\n" + CORPO
# senzaRussiaGenerica sta nel blocco copiato dal radar
with tempfile.TemporaryDirectory() as d:
    Path(d, "p.js").write_text(prog, encoding="utf-8")
    Path(d, "c.json").write_text(json.dumps(casi), encoding="utf-8")
    res = json.loads(subprocess.run(["node", str(Path(d, "p.js")), str(Path(d, "c.json"))], capture_output=True, text=True, check=True).stdout)

py = {"al": [R.anno_libero(m, p, f) for m in casi["morti"] for p in ("it", "fr", "de", "uk", "es") for f in (False, True)],
      "mo": [R.morti_liberi_nel(y, p) for y in casi["anni"] for p in ("it", "es")],
      "usa": [x for y in casi["anni"] for x in (R.anno_libero_usa(y), R.pubblicate_libere_usa_nel(y))],
      "ver": [R.italia_da_verificare(a["p"], a["m"], OGGI) for a in autori]}
for k in py:
    diff = [i for i, (x, y) in enumerate(zip(py[k], res[k])) if x != y]
    if len(py[k]) != len(res[k]) or diff:
        errori.append(f"gemelli diversi su «{k}»: {len(diff)} casi")
        if k == "ver":
            for i in diff[:20]:
                a = autori[i]
                errori.append(f"   {a['n']} ({a['f']}): Python {py[k][i]}, browser {res[k][i]}; paesi {a['p']}")
print(f"1. Gemelli Python/browser: {sum(len(v) for v in py.values())} confronti, differenze: {sum(1 for e in errori if e.startswith('gemelli'))} gruppi")

# ---------------------------------------------------------------- 2. prima e dopo (Italia)
if "--prima-dopo" in sys.argv:   # confronto con la regola di prima del 21/11/2026 (solo per il registro delle prove)
    VECCHI = {"Regno Unito", "Regno Unito di Gran Bretagna e Irlanda", "Regno d'Inghilterra", "Galles", "Stati Uniti",
              "Unione Sovietica", "Impero russo", "Repubblica Socialista Federativa Sovietica Russa", "Russia sovietica", "RSS Ucraina",
              "RSS Bielorussa", "Repubblica Socialista Sovietica Georgiana", "Kazakistan", "Cina", "Repubblica di Cina", "Francia",
              "Australia", "Belgio", "Brasile", "Canada", "Cecoslovacchia", "Prima Repubblica cecoslovacca", "Repubblica Socialista Cecoslovacca",
              "Grecia", "India", "Impero anglo-indiano", "Dominion dell'India", "Pakistan", "Regno dei Paesi Bassi", "Nuova Zelanda",
              "Polonia", "Seconda Repubblica di Polonia", "Repubblica Popolare di Polonia", "Sudafrica", "Jugoslavia", "Regno di Jugoslavia",
              "Repubblica federale popolare di Jugoslavia", "Repubblica Socialista Federale di Jugoslavia", "Regno dei Serbi, Croati e Sloveni",
              "Serbia", "Albania"}
    diff = {"paese non noto": [], "paese aggiunto alla lista": [], "altro": []}
    visti = set()
    for a in autori:
        if a["q"] in visti or a["f"].startswith("es-"):
            continue
        visti.add(a["q"])
        vecchio = bool(set(a["p"]) & VECCHI) and a["m"] + 71 + 8 > OGGI
        nuovo = R.italia_da_verificare(a["p"], a["m"], OGGI)
        if vecchio != nuovo:
            k = "paese non noto" if not a["p"] else ("paese aggiunto alla lista" if nuovo and R.paesi_alleati(a["p"]) else "altro")
            diff[k].append({"nome": a["n"], "qid": a["q"], "morte": a["m"], "paesi": a["p"], "prima": vecchio, "dopo": nuovo})
    print("2. Italia «da verificare», prima → dopo, autori delle liste:", {k: len(v) for k, v in diff.items()})
    for k, v in diff.items():
        for x in v[:8]:
            print(f"   [{k}] {x['nome']} (morto {x['morte']}, paesi {x['paesi'] or '—'}): {x['prima']} → {x['dopo']}")
    if "--differenze" in sys.argv:
        Path(sys.argv[sys.argv.index("--differenze") + 1]).write_text(json.dumps(diff, ensure_ascii=False, indent=1), encoding="utf-8")
    if diff["altro"]:
        errori.append(f"differenze senza motivo noto: {len(diff['altro'])}")


for e in errori:
    print("ERRORE:", e)
sys.exit(1 if errori else 0)
