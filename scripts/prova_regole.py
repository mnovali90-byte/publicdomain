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

VISIBILI_PROVA = [{}, {"senza_nome": True}, {"senza_nome": False}, {"nome": "Q1"}, {"senza_nome": None}]
casi = {"visibili": VISIBILI_PROVA, "morti": list(range(-500, 2031)), "anni": list(range(1900, 2101)), "autori": autori, "oggi": OGGI}
js = (RADICE / "assets" / "regole.js").read_text(encoding="utf-8")
CORPO = r"""
const REGOLE_PAESI = window.REGOLE_PAESI;
const paeseModerno = (nome) => PAESE_MODERNO.get(norm(nome)) || nome;
const C = JSON.parse(require("fs").readFileSync(process.argv[2], "utf8"));
const out = { al: [], mo: [], usa: [], ver: [], nome: [] };
for (const a of C.visibili) out.nome.push(REGOLE_PAESI.autoreVisibile(a));
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
      "ver": [R.nota_trattato(a["p"], a["m"], OGGI) for a in autori],
      "nome": [R.autore_visibile(a) for a in VISIBILI_PROVA]}
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
_norm = [R.opera_da_riga(r, _reg.get("coautori", {}), _reg.get("opere", {})) for r in _righe]
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
# 23/11/2026: un caso per ogni regola dell'incrocio delle fonti sulle opere USA (docs/criteri.md)
for c in CASI.get("incrocio", []):
    r = R.incrocio_opera(c["pub"], c.get("lingua"), c.get("per_fonte") or {}, None, c.get("date_wikidata"),
                         fatti=R.fatti_da_ricerca(c.get("voci") or [], c["pub"]))
    att = c["atteso"]
    if r["esito"] != att["esito"] or ("anno" in att and r.get("anno") != att["anno"]):
        no4.append(f"caso dell'incrocio «{c['caso']}»: atteso {att}, risulta {r['esito']} {r.get('anno')} ({r.get('motivo')})")
    else:
        ok4 += 1
print(f"4. Casi di riferimento: {len(CASI['reali'])} reali, {len(CASI['confine'])} di confine e {len(CASI.get('incrocio', []))} dell'incrocio USA; tornano {ok4}, sbagliati {len(no4)}, noti da sistemare {len(avvisi4)}")
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

# 5b. (23/11/2026, Carl Schmitt) nessun autore di data/fuori_classifica.json nelle vetrine: libri USA delle pagine dell'anno e home
_fuori = json.load(open(RADICE / "data" / "fuori_classifica.json", encoding="utf-8"))["autori"]
no5b, viste5b = [], 0
for f in sorted(list(RADICE.glob("pubblico-dominio-*/index.html")) + list((RADICE / "en").glob("public-domain-*/index.html")) + [RADICE / "index.html", RADICE / "en" / "index.html"]):
    h = f.read_text(encoding="utf-8")
    m = re.search(r'id="ix2".*?</ol>', h, re.S)
    pezzi = [m.group(0)] if m else []
    m2 = re.search(r"const P=(\[.*?\]), DIRITTI=", h)
    if m2:
        pezzi.append(json.dumps([p_.get("a") for p_ in json.loads(m2.group(1))], ensure_ascii=False))
    for pz in pezzi:
        viste5b += 1
        for x in _fuori:
            if x["nome"] in pz:
                no5b.append(f"{f.relative_to(RADICE)}: {x['nome']} è in vetrina ma è in data/fuori_classifica.json")
print(f"5b. Fuori classifica nelle vetrine: {viste5b} vetrine controllate, {len(_fuori)} autori esclusi, presenti: {len(no5b)}")
for x in no5b:
    print("   ", x)
errori += no5b

# ---------------------------------------------------------------- 6. stati scritti sulle schede autore (22/11/2026)
# scripts/controllo_stati.py rifà da capo, con regole.py e i registri, ogni stato scritto sulle schede generate.
# Bloccante dal 22/11/2026, da quando le schede usano gli stessi dati e la stessa regola di Già pubblici.
import controllo_stati  # noqa: E402
errori += [f"scheda contro le regole: {x}" for x in controllo_stati.main(stampa=True)]
# ---------------------------------------------------------------- 7. liste e calendario contro il registro unico (22/11/2026)
errori += [f"dati contro il registro: {x}" for x in controllo_stati.controlla_liste(stampa=True)]

# ---------------------------------------------------------------- 8. registro delle opere: un anno e una nota, uguali ovunque (23/11/2026)
# Per ogni opera del registro delle opere (data/registro/opere.json, «opere»; scripts/registro.py, opere_decise):
#   - l'anno mostrato in Già pubblici (file della ricerca, file per autore, scaffali), nelle liste USA, nella pagina dell'anno
#     e nelle schede autore è quello del registro;
#   - la nota del registro compare dove si mostra l'opera (pagina dell'anno, schede autore) e le liste non ne hanno copie;
#   - ogni nota che dice «libero/libera» dice dove («negli USA» / «in the US»);
#   - il registro scritto nel file è uguale a quello che calcola scripts/registro.py (niente copie rimaste indietro).
import html as _html  # noqa: E402
import registro as _registro  # noqa: E402
_dec = _registro.opere_decise()
no8, nc8, conti8 = [], [], {"opere": 0, "confronti": 0}
if json.loads(json.dumps(_dec)) != _reg.get("opere"):
    no8.append("data/registro/opere.json («opere») è diverso da quello che calcola scripts/registro.py: rilanciare storico/registro_opere.py")
_uscita = {q: x["anno"] for q, x in _dec.items() if x.get("tipo") == "uscita" and isinstance(x.get("anno"), int)}
# la prima pubblicazione documentata batte i cataloghi (regole.anno_prima_pubblicazione; caso The Lagoon, Cornhill 1897)
for q, p8 in (json.load(open(RADICE / "data" / "verifiche_opere.json", encoding="utf-8")).get("prima_pubblicazione") or {}).items():
    conti8["confronti"] += 1
    if _uscita.get(q) != p8.get("anno"):
        no8.append(f"{q}: prima pubblicazione documentata {p8.get('anno')}, ma il registro dice {_uscita.get(q)}")
    v8 = (_reg.get("usa") or {}).get(q) or [None]
    if v8[0] is not None and v8[0] != p8.get("anno"):
        no8.append(f"{q}: prima pubblicazione documentata {p8.get('anno')}, ma l'anno USA del registro è {v8[0]}")
for q, x in _dec.items():
    n = x.get("nota") or {}
    if n:
        if re.search(r"\blibe(r[oaie]|ra)\b|si liber", n.get("it", "")) and "USA" not in n.get("it", ""):
            no8.append(f"{q}: la nota italiana dice «libero» ma non dice dove («negli USA»)")
        if re.search(r"\bfree\b", n.get("en", "")) and " US" not in n.get("en", ""):
            no8.append(f"{q}: la nota inglese dice «free» ma non dice dove («in the US»)")
        if not n.get("it") or not n.get("en"):
            no8.append(f"{q}: nota senza italiano o senza inglese")
    if x.get("tipo") == "uscita" and len(x.get("fonti", [])) < 2:
        no8.append(f"{q}: anno deciso con meno di due fonti")
    senza = [f["nome"] for f in x.get("fonti", []) if not f.get("link")]
    if senza:
        nc8.append(f"{q}: fonti senza link: {'; '.join(senza)}")
# Già pubblici: file della ricerca, file per autore, scaffali
_visti8 = set()
for f in sorted(glob.glob(str(RADICE / "data" / "storico" / "ricerca" / "*.json"))) + sorted(glob.glob(str(RADICE / "data" / "storico" / "per_autore" / "*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    righe = d["opere"] if "opere" in d and isinstance(d["opere"], list) and (not d["opere"] or isinstance(d["opere"][0], list)) else [r for v in d.values() for r in v]
    for r in righe:
        if r[0] in _dec and r[0] not in _uscita:
            _visti8.add(r[0])   # «entro»: la scheda dell'opera in Già pubblici lo dice quando manca l'anno di uscita
        if r[0] in _uscita:
            conti8["confronti"] += 1
            _visti8.add(r[0])
            if r[3] != _uscita[r[0]]:
                no8.append(f"{r[0]} «{r[1]}»: {Path(f).relative_to(RADICE)} dice {r[3]}, il registro {_uscita[r[0]]}")
_pj = json.load(open(RADICE / "data" / "storico" / "pagina.json", encoding="utf-8"))
for r in _pj.get("opere", []):
    if r[0] in _uscita:
        conti8["confronti"] += 1
        if r[3] != _uscita[r[0]]:
            no8.append(f"{r[0]} «{r[1]}»: scaffali di Già pubblici dicono {r[3]}, il registro {_uscita[r[0]]}")
# liste USA e pagine dell'anno
for f in sorted((RADICE / "data").glob("us-[0-9][0-9][0-9][0-9].json")):
    d = json.load(open(f, encoding="utf-8"))
    pub, an = d.get("anno_pubblicazione"), f.stem[3:]
    pag = {lang: (RADICE / (f"pubblico-dominio-{an}" if lang == "it" else f"en/public-domain-{an}") / "index.html") for lang in ("it", "en")}
    pag = {k: _html.unescape(v.read_text(encoding="utf-8")) if v.exists() else "" for k, v in pag.items()}
    for o in d.get("opere", []):
        if "nota_usa" in o or "conferma_usa" in o:
            no8.append(f"{f.name}: {o['qid']} ha ancora una copia della nota o della conferma (devono stare solo nel registro)")
        x = _dec.get(o["qid"])
        if not x:
            continue
        _visti8.add(o["qid"])
        conti8["confronti"] += 1
        anno_l = x.get("anno_lista") or (x.get("anno") if x.get("tipo") == "uscita" else None)
        if anno_l is not None and anno_l != pub:
            no8.append(f"{f.name}: {o['qid']} è nella lista dei libri del {pub}, ma il registro dice {anno_l} (manca «anno_lista» o l'opera non va qui)")
        for lang, h8 in pag.items():
            m8 = re.search(r'<li class="row"[^>]*>(?:(?!</li>).)*?#/opera/' + o["qid"] + r'".*?</li>', h8, re.S)
            if not m8:
                continue
            conti8["confronti"] += 1
            riga = m8.group(0)
            nota = (x.get("nota") or {}).get(lang)
            if nota and nota not in riga:
                no8.append(f"pagina {an} ({lang}): {o['qid']} senza la nota del registro")
            # dal 23/11/2026 l'etichetta non ripete l'anno (tre stati, docs/criteri.md): un anno deciso nel registro
            # non può comparire come «Da confermare»
            if anno_l is not None and not re.search(r"Verificato|Verified|Edizione confermata|Edition confirmed", riga):
                no8.append(f"pagina {an} ({lang}): {o['qid']} ha l'anno deciso nel registro ({anno_l}) ma compare «da confermare»")
# schede autore: anno nella tabella delle opere e nota
import pagine as _pg  # noqa: E402
for f in sorted((RADICE / "data").glob("[0-9][0-9][0-9][0-9].json")):
    for a in json.load(open(f, encoding="utf-8")).get("autori", []):
        for o in a.get("opere", [])[:10]:
            og = _pg.opera_gp(a, o)
            ks = f"{a.get('wikidata')}|{o.get('titolo')}"
            if og and og["q"] in _dec:
                k8 = og["q"]
            elif ks in _dec or any(x.get("scheda") == ks for x in _dec.values()):
                k8 = ks if ks in _dec else next(q for q, x in _dec.items() if x.get("scheda") == ks)
                og = {"q": k8}
            else:
                continue
            x = _dec[k8]
            for lang, cart in (("it", "autore"), ("en", "en/author")):
                pg8 = a.get("pagina") if lang == "it" else a.get("pagina_en")
                if not pg8:
                    continue   # autore senza scheda
                fs = RADICE / cart / pg8 / "index.html"
                if not fs.exists():
                    nc8.append(f"{og['q']}: scheda di {a.get('nome')} ({lang}) non trovata")
                    continue
                h8 = _html.unescape(fs.read_text(encoding="utf-8"))
                _visti8.add(og["q"])
                t = o.get("titolo") if lang == "it" else o.get("titolo_en") or o.get("titolo")
                conti8["confronti"] += 1
                m8 = re.search(r'<li><span class="t">' + re.escape(t) + r'(?:<sup[^>]*>\d+</sup>)*</span><span class="y">([^<]*)</span>', h8)
                if m8 and x.get("tipo") == "uscita" and m8.group(1).strip() != str(x["anno"]):
                    no8.append(f"scheda {a.get('nome')} ({lang}): «{t}» mostra {m8.group(1)}, il registro {x['anno']}")
                if m8 and x.get("tipo") == "entro" and not m8.group(1).strip():
                    pass   # c'è un anno di uscita credibile: «entro» serve solo quando manca
                elif m8 and x.get("tipo") == "entro" and str(x["anno"]) not in m8.group(1) and not m8.group(1).strip().isdigit():
                    no8.append(f"scheda {a.get('nome')} ({lang}): «{t}» mostra «{m8.group(1)}», il registro «entro il {x['anno']}»")
                if not m8:
                    nc8.append(f"scheda {a.get('nome')} ({lang}): «{t}» non trovata nella tabella delle opere")
                nota = (x.get("nota") or {}).get(lang)
                if nota and nota[0].lower() + nota[1:] not in h8:
                    no8.append(f"scheda {a.get('nome')} ({lang}): «{t}» senza la nota del registro")
# vetrina della home: le opere USA hanno il codice Wikidata (23/11/2026); se il registro ha una nota, la home la mostra uguale
for lang, f8 in (("it", RADICE / "index.html"), ("en", RADICE / "en" / "index.html")):
    m8 = re.search(r"const P=(\[.*?\]), DIRITTI=", f8.read_text(encoding="utf-8"))
    for p8 in json.loads(m8.group(1)) if m8 else []:
        if ("Stati Uniti" in p8["r"]) or ("United States" in p8["r"]):
            if not p8.get("q"):
                no8.append(f"home ({lang}): «{p8['t']}» negli USA senza codice Wikidata: non si può confrontare con il registro")
                continue
            conti8["confronti"] += 1
            x = _dec.get(p8["q"])
            nota = ((x or {}).get("nota") or {}).get(lang) or ""
            if x:
                _visti8.add(p8["q"])
            if _html.unescape(p8.get("n") or "") != nota:
                no8.append(f"home ({lang}): «{p8['t']}» ha la nota «{p8.get('n')}», il registro «{nota}»")
conti8["opere"] = len(_visti8)
_mai = [q for q in _dec if q not in _visti8]
print(f"8. Registro delle opere: {len(_dec)} opere nel registro, {conti8['opere']} trovate nelle pagine e nei file, {conti8['confronti']} confronti; "
      f"diversi dal registro: {len(no8)}; non controllabili: {len(nc8) + len(_mai)}")
for x in no8 + nc8:
    print("   ", x)
if _mai:
    print("    non mostrate:", "; ".join(_mai))
if _mai:
    print(f"    non mostrate in nessuna pagina o file controllato (opere senza codice nelle schede o fuori da Già pubblici): {len(_mai)}")
errori += no8

# ---------------------------------------------------------------- 9. autori aggiunti e verifiche a mano (23/11/2026)
# Ogni autore scelto a mano (data/verifiche_manuali.json, «aggiunti_a_mano») ha: la lista giusta per il suo anno di morte,
# due fonti terze con citazione (non Wikipedia), un'opera principale con fonte e citazione, il segno di scrittore; se ha la
# scheda è nella sua lista una volta sola, con l'esito «nazionale». Nessuna verifica a mano nuova usa Wikipedia come fonte.
# Caso che l'ha fatta nascere: gli 8 saggisti scelti da Marco (Febvre, Sarton, Calamandrei, Keynes, Oman, Groos, Salvemini,
# Tokutomi); Klages resta fuori finché non è valutato con la regola sugli autori razzisti.
_vm9 = json.load(open(RADICE / "data" / "verifiche_manuali.json", encoding="utf-8"))
try:
    _sch9 = json.load(open(RADICE / "data" / "registro" / "schede_proposte.json", encoding="utf-8")).get("autori", {})
except Exception:
    _sch9 = {}
no9, in_lista9 = [], 0
_wiki9 = re.compile(r"wikipedia", re.I)
for q9, ag9 in _vm9.get("aggiunti_a_mano", {}).items():
    m9 = _vm9["autori"].get(q9) or {}
    lista9 = ag9.get("lista", "")
    f9 = RADICE / "data" / f"{lista9}.json"
    atteso9 = R.morti_liberi_nel(int(lista9[-4:]), "es" if lista9.startswith("es-") else "it") if re.search(r"\d{4}$", lista9) else None
    if m9.get("morte") != atteso9:
        no9.append(f"{ag9.get('nome')}: anno di morte {m9.get('morte')} non è quello della lista {lista9} ({atteso9})")
    fonti9 = m9.get("fonti") or []
    if len(fonti9) < 2 or any(not x.get("citazione") or _wiki9.search(x.get("nome", "") + x.get("url", "")) for x in fonti9):
        no9.append(f"{ag9.get('nome')}: servono due fonti terze (non Wikipedia) con citazione")
    op9 = ag9.get("opera") or {}
    if not (op9.get("titolo") and op9.get("fonte") and op9.get("url") and op9.get("citazione")):
        no9.append(f"{ag9.get('nome')}: manca l'opera principale con fonte e citazione")
    if q9 not in _vm9.get("scrittori_a_mano", {}):
        no9.append(f"{ag9.get('nome')}: non è segnato come scrittore")
    if ag9.get("approvato") and q9 in _sch9 and f9.exists():
        trovati9 = [a for a in json.load(open(f9, encoding="utf-8"))["autori"] if a.get("wikidata") == q9]
        if len(trovati9) != 1 or (trovati9[0].get("verifica") or {}).get("esito") != "nazionale" or not trovati9[0].get("letterario"):
            no9.append(f"{ag9.get('nome')}: ha la scheda ma nella lista {lista9} compare {len(trovati9)} volte o senza esito «nazionale»")
        else:
            in_lista9 += 1
for q9, m9 in _vm9.get("autori", {}).items():
    if (m9.get("controllato") or "") >= "2026-11-23" and _wiki9.search((m9.get("fonte") or "") + (m9.get("url") or "")):
        no9.append(f"verifica a mano di {m9.get('nome')} (dal 23/11/2026) con Wikipedia come fonte")
for q9, t9 in _vm9.get("verifiche_tolte", {}).items():   # caso aperto: in nessuna lista (Răcăciuni, 23/11/2026)
    if t9.get("caso_aperto"):
        for f9 in sorted((RADICE / "data").glob("*.json")):
            if re.fullmatch(r"(es-)?\d{4}\.json", f9.name) and any(a.get("wikidata") == q9 for a in json.load(open(f9, encoding="utf-8")).get("autori", [])):
                no9.append(f"{t9.get('nome')}: caso aperto, ma è nella lista {f9.stem}")
print(f"9. Autori aggiunti a mano: {len(_vm9.get('aggiunti_a_mano', {}))} (approvati: {sum(1 for x in _vm9.get('aggiunti_a_mano', {}).values() if x.get('approvato'))}), già nella loro lista: {in_lista9}, problemi: {len(no9)}")
for x in no9:
    print("   ", x)
errori += no9

for e in errori:
    print("ERRORE:", e)
sys.exit(1 if errori else 0)
