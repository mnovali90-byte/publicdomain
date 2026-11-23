"""Prova delle regole per paese (21/11/2026). Si ferma con errore se qualcosa non torna.

1. GEMELLI: assets/regole.js (usato da radar e Già pubblici) deve dare gli stessi risultati di scripts/regole.py,
   su tutti gli anni di morte dal -500 al 2030, tutti i paesi, e su tutti gli autori veri delle liste (con i nomi dei paesi
   come li vede il radar, cioè dopo la sua traduzione nei nomi attuali).
Uso: python3 scripts/prova_regole.py"""
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
for (const a of C.autori) out.ver.push(REGOLE_PAESI.notaTrattato(a.p, a.m, C.oggi));   // il radar usa a.paesiWd: i nomi di Wikidata
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
      "ver": [R.nota_trattato(a["p"], a["m"], OGGI) for a in autori]}
for k in py:
    diff = [i for i, (x, y) in enumerate(zip(py[k], res[k])) if x != y]
    if len(py[k]) != len(res[k]) or diff:
        errori.append(f"gemelli diversi su «{k}»: {len(diff)} casi")
        if k == "ver":
            for i in diff[:20]:
                a = autori[i]
                errori.append(f"   {a['n']} ({a['f']}): Python {py[k][i]}, browser {res[k][i]}; paesi {a['p']}")
print(f"1. Gemelli Python/browser: {sum(len(v) for v in py.values())} confronti, differenze: {sum(1 for e in errori if e.startswith('gemelli'))} gruppi")

# ---------------------------------------------------------------- 2. copie delle regole fuori da regole.py
# (22/11/2026: aggiorna.py e altri 4 script avevano ancora +71/+81/-96 scritti a mano e la prima unificazione non li aveva visti)
import re as _re  # noqa: E402
NUMERI = _re.compile(r"(?<![\w.])(?:[+-]\s?(?:51|70|71|80|81|90|95|96|101|106|150|170|171|180|181)|(?:70|71|80|81|95|96|101|171|181)\s?[+-](?!\d))(?![\w.])(?!\s*(?:anni|years|ans|Jahre))")   # 22/11/2026: anche le soglie delle regole per opera (Y - 171, + 150...)
SOGLIE = _re.compile(r"(?<![\w.])(?:1969|1989|2039|2040)(?![\w.])")   # regola britannica del 2039   # «morte + 70 anni» nei testi non conta
copie = []
for f in sorted(glob.glob(str(RADICE / "scripts" / "*.py")) + glob.glob(str(RADICE / "storico" / "*.py"))
                + [str(RADICE / "radar" / "index.html"), str(RADICE / "storico" / "pagina.html"), str(RADICE / "scripts" / "pagine.py")]):
    nome = Path(f).name
    if nome in ("regole.py", "prova_regole.py") or nome.startswith(("prova_", "campione", "esplora", "stima")):
        continue
    for i, riga in enumerate(Path(f).read_text(encoding="utf-8").splitlines(), 1):
        codice = riga.split("#", 1)[0] if f.endswith(".py") else riga.split("//", 1)[0]
        codice = _re.sub(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'', '""', codice)   # i testi tra virgolette non sono regole
        if (NUMERI.search(codice) or SOGLIE.search(codice)) and _re.search(r"\b(anno|morte|morti|pub|y|m|D|Y|ultima|oggi)\b", codice):
            copie.append(f"{Path(f).relative_to(RADICE)}:{i}: {riga.strip()[:110]}")
print(f"2. Copie delle regole fuori da regole.py: {len(copie)}")
for c in copie[:30]:
    print("   ", c)
if copie:
    errori.append(f"{len(copie)} righe con numeri delle regole scritti a mano (usare scripts/regole.py)")

# ---------------------------------------------------------------- 3. regole per opera: gemelli su tutte le opere di Già pubblici
# (22/11/2026) stato_opera in Python e statoOpera in assets/regole.js, su ogni opera dei file di ricerca e 6 paesi
_reg = json.load(open(RADICE / "data" / "registro" / "opere.json", encoding="utf-8"))
_mpf = sorted(json.load(open(RADICE / "data" / "registro" / "mpf.json", encoding="utf-8")).get("autori", {}))
_viste = {}
for f in sorted(glob.glob(str(RADICE / "data" / "storico" / "ricerca" / "*.json"))):
    for r in json.load(open(f, encoding="utf-8"))["opere"]:
        _viste.setdefault(r[0], r)
_righe = list(_viste.values())
PAESI6 = ["it", "fr", "de", "uk", "es", "us"]
CORPO3 = r"""
const R = window.REGOLE_PAESI, C = JSON.parse(require("fs").readFileSync(process.argv[2], "utf8"));
const mpf = new Set(C.mpf), out = [];
for (const o of C.opere) { for (const c of C.paesi) out.push(R.statoOpera(o, c, C.oggi, mpf, C.ver)); out.push(R.liberaUeOpera(o, C.oggi)); }
console.log(JSON.stringify(out));
"""
_norm = [R.opera_da_riga(r, _reg.get("coautori", {})) for r in _righe]
# anno_opera_credibile: confronto anche sugli anni grezzi
CORPO3b = r"""
const R = window.REGOLE_PAESI, C = JSON.parse(require("fs").readFileSync(process.argv[2], "utf8"));
console.log(JSON.stringify(C.righe.map((x) => R.annoOperaCredibile(x[0], x[1]))));
"""
with tempfile.TemporaryDirectory() as d:
    Path(d, "p.js").write_text("const window = {};\n" + js + CORPO3, encoding="utf-8")
    Path(d, "c.json").write_text(json.dumps({"opere": _norm, "paesi": PAESI6, "oggi": OGGI, "mpf": _mpf, "ver": _reg.get("usa", {})}), encoding="utf-8")
    res3 = json.loads(subprocess.run(["node", str(Path(d, "p.js")), str(Path(d, "c.json"))], capture_output=True, text=True, check=True).stdout)
    grezzi = [[r[3], R.opera_da_riga([r[0], "", "", None, 0, r[5], 0], _reg.get("coautori", {}))["au"]] for r in _righe]
    Path(d, "q.js").write_text("const window = {};\n" + js + CORPO3b, encoding="utf-8")
    Path(d, "d.json").write_text(json.dumps({"righe": grezzi}), encoding="utf-8")
    res3b = json.loads(subprocess.run(["node", str(Path(d, "q.js")), str(Path(d, "d.json"))], capture_output=True, text=True, check=True).stdout)
py3 = []
for o in _norm:
    py3 += [R.stato_opera(o, c, OGGI, set(_mpf), _reg.get("usa", {})) for c in PAESI6] + [R.libera_ue_opera(o, OGGI)]
diversi3 = [i for i, (x, y) in enumerate(zip(py3, res3)) if json.dumps(x, sort_keys=True) != json.dumps(y, sort_keys=True)]
diversi3 += [i for i, (g, y) in enumerate(zip(grezzi, res3b)) if R.anno_opera_credibile(g[0], g[1]) != y]
print(f"3. Regole per opera, Python/browser: {len(_norm)} opere, {len(py3) + len(grezzi)} confronti, differenze: {len(diversi3)}")
if len(py3) != len(res3) or diversi3:
    errori.append(f"regole per opera diverse tra Python e browser: {len(diversi3)} casi")

# ---------------------------------------------------------------- 3b. calendario del sito: fase_sito e faseSito, tutti i giorni 2025-2029
import datetime as _dt  # noqa: E402
_giorni = [(_dt.date(2025, 1, 1) + _dt.timedelta(days=k)) for k in range(365 * 5 + 1)]
with tempfile.TemporaryDirectory() as d:
    Path(d, "g.js").write_text("const window = {};\n" + js + """
const G = JSON.parse(require("fs").readFileSync(process.argv[2], "utf8"));
console.log(JSON.stringify(G.map(([y, m, g]) => window.REGOLE_PAESI.faseSito(new Date(y, m - 1, g, 12)))));""", encoding="utf-8")
    Path(d, "g.json").write_text(json.dumps([[x.year, x.month, x.day] for x in _giorni]), encoding="utf-8")
    _resg = json.loads(subprocess.run(["node", str(Path(d, "g.js")), str(Path(d, "g.json"))], capture_output=True, text=True, check=True).stdout)
_dg = [x for x, r in zip(_giorni, _resg) if list(R.fase_sito(x)) != r]
_attesi = {(_dt.date(2026, 12, 31)): ("vigilia", 2027), _dt.date(2027, 1, 1): ("festa", 2027), _dt.date(2027, 1, 6): ("festa", 2027),
           _dt.date(2027, 1, 7): ("conto", 2028), _dt.date(2026, 11, 22): ("conto", 2027)}
_da = [k for k, v in _attesi.items() if R.fase_sito(k) != v]
print(f"3b. Calendario del sito: {len(_giorni)} giorni, Python/browser diversi: {len(_dg)}, date chiave sbagliate: {len(_da)}")
if _dg or _da:
    errori.append(f"calendario del sito: {len(_dg)} giorni diversi tra Python e browser, {len(_da)} date chiave sbagliate")

# ---------------------------------------------------------------- 4. casi di riferimento (data/casi_riferimento.json)
CASI = json.load(open(RADICE / "data" / "casi_riferimento.json", encoding="utf-8"))
_pern = {o["q"]: o for o in _norm}
ok4, no4, avvisi4 = 0, [], []
def _controlla(c, o):
    global ok4
    if o is None:
        return f"opera {c.get('q')} non trovata nei dati"
    st = R.stato_opera(o, c["paese"], c["anno"], set(_mpf), _reg.get("usa", {}))
    if st["s"] not in c["atteso"] or ("y_att" in c and st.get("y") != c["y_att"]):
        return f"atteso {c['atteso']} {c.get('y_att', '')}, risulta {st['s']} {st.get('y', '')}"
    return None
def _opera_home(chiave):
    """«autore|titolo della scheda»: l'opera come la vede la home (scripts/pagine.py, opera_regole), cercata nelle liste."""
    import glob as _g
    import pagine as _pg
    aq, t = chiave.split("|", 1)
    for f in sorted(_g.glob(str(RADICE / "data" / "[0-9][0-9][0-9][0-9].json"))):
        for a in json.load(open(f, encoding="utf-8")).get("autori", []):
            if a.get("wikidata") == aq:
                for o in a.get("opere", []):
                    if o.get("titolo") == t or o.get("titolo_en") == t:
                        return _pg.opera_regole(a, o)
    return None
for c in CASI["reali"]:
    e = _controlla(c, c.get("o") or (_opera_home(c["home"]) if c.get("home") else _pern.get(c.get("q"))))
    if e is None:
        ok4 += 1
    elif c.get("blocca", True):
        no4.append(f"caso reale {c['n']}, {c['caso']}: {e}")
    else:
        avvisi4.append(f"caso reale {c['n']}, {c['caso']}: {e} ({c.get('perche', '')})")
for c in CASI["confine"]:
    o = {"q": "confine", "y": c.get("y"), "yd": 0, "antica": c.get("antica"),
         "au": [{"q": f"x{i}", "m": m, "an": False, "inc": 0, "sc": False, "al": False} for i, m in enumerate(c["au"])]}
    e = _controlla(c, o)
    if e is None:
        ok4 += 1
    else:
        no4.append(f"caso di confine «{c['caso']}»: {e}")
print(f"4. Casi di riferimento: {len(CASI['reali'])} reali e {len(CASI['confine'])} di confine; tornano {ok4}, sbagliati {len(no4)}, noti da sistemare {len(avvisi4)}")
for x in no4 + avvisi4:
    print("   ", x)
errori += no4

# ---------------------------------------------------------------- 5. vetrina della home contro le regole per opera (22/11/2026)
# Ogni opera che la home dà «libera dal 1° gennaio» in Europa deve esserlo anche per stato_opera (le regole di Già pubblici,
# con i coautori del registro). Caso che l'ha fatta nascere: «L'opera da tre soldi» (coautrice Elisabeth Hauptmann, morta nel 1973).
def _pt(x):
    import unicodedata
    x = unicodedata.normalize("NFKD", str(x or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(re.findall(r"[a-z0-9]+", x))
_anno_v = R.fase_sito(date.today())[1]
_pert = {}
for r, o in zip(_righe, _norm):
    for t in (r[1], r[2]):
        for au in r[5]:
            _pert.setdefault((_pt(au[1]), _pt(t)), o)
no5, nontrovate5, viste5 = [], [], 0
for f in (RADICE / "index.html", RADICE / "en" / "index.html"):
    h = f.read_text(encoding="utf-8")
    m = re.search(r"const P=(\[.*?\]), DIRITTI=", h)
    if not m:
        no5.append(f"{f.name}: vetrina non trovata")
        continue
    for p in json.loads(m.group(1)):
        if ("Stati Uniti" in p["r"]) or ("United States" in p["r"]):
            continue
        viste5 += 1
        o = next((_pert.get((_pt(n), _pt(p["t"]))) for n in re.split(r" e | and ", p["a"]) if _pert.get((_pt(n), _pt(p["t"])))), None)
        if not o:   # 23/11/2026: non ancora in Già pubblici, si controlla con gli stessi dati della home
            for n_ in re.split(r" e | and ", p["a"]):
                for f_ in sorted((RADICE / "data").glob("[0-9][0-9][0-9][0-9].json")):
                    for a_ in json.load(open(f_, encoding="utf-8")).get("autori", []):
                        if _pt(a_.get("nome")) == _pt(n_):
                            for o_ in a_.get("opere", []):
                                if _pt(p["t"]) in (_pt(o_.get("titolo")), _pt(o_.get("titolo_en"))):
                                    import pagine as _pg
                                    o = _pg.opera_regole(a_, o_)
        if not o:
            nontrovate5.append(f"{p['a']}, «{p['t']}» non è nei dati di Già pubblici: non controllabile")
            continue
        st = R.stato_opera(o, "it", _anno_v, set(_mpf), _reg.get("usa", {}))
        if st["s"] != "si":
            no5.append(f"home: «{p['t']}» di {p['a']} è in vetrina come libera dal {_anno_v}, ma per le regole per opera è «{st['s']}» {st.get('y') or ''} ({st['r']})")
print(f"5. Vetrina della home: {viste5} pagine europee, contro le regole: {len(no5)}, non controllabili: {len(nontrovate5)}")
for x in no5 + nontrovate5:
    print("   ", x)
errori += no5

# ---------------------------------------------------------------- 6. stati scritti sulle schede autore (22/11/2026)
# scripts/controllo_stati.py rifà da capo, con regole.py e i registri, ogni stato scritto sulle schede generate.
# Bloccante dal 22/11/2026, da quando le schede usano gli stessi dati e la stessa regola di Già pubblici.
import controllo_stati  # noqa: E402
errori += [f"scheda contro le regole: {x}" for x in controllo_stati.main(stampa=True)]
# ---------------------------------------------------------------- 7. liste e calendario contro il registro unico (22/11/2026)
errori += [f"dati contro il registro: {x}" for x in controllo_stati.controlla_liste(stampa=True)]

for e in errori:
    print("ERRORE:", e)
sys.exit(1 if errori else 0)
