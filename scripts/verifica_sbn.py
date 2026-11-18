#!/usr/bin/env python3
"""Verifica indipendente del riconoscimento autori SBN (fase 3), su un campione NUOVO.

Regole del protocollo (chieste da Marco, 18/11/2026):
- campione scelto a caso tra gli autori del sito che SBN ha interrogato, SENZA i 140 del campione di sviluppo,
  compresi gli autori che il sistema non trova;
- le regole del riconoscimento (scripts/riconosci_sbn.py e scripts/sbn.py) sono CONGELATE prima della prova:
  se ne salva l'impronta (sha256) e la misura si rifiuta di partire se i file sono cambiati;
- prima si raccolgono le prove e si decide a mano chi è chi, SENZA guardare il nuovo sistema;
  solo dopo si fa girare il nuovo riconoscimento e si confronta;
- se dopo aver visto gli errori si cambiano le regole, questo campione diventa di sviluppo e serve una
  verifica nuova.

Uso:
  python scripts/verifica_sbn.py congela     -> docs/verifica-sbn/regole-congelate.json
  python scripts/verifica_sbn.py prove       -> docs/verifica-sbn/campione.json e prove.json (non usa il nuovo sistema)
  python scripts/verifica_sbn.py misura      -> docs/verifica-sbn/misura.json (solo se esiti.json esiste e le regole non sono cambiate)
"""
import collections
import hashlib
import json
import pathlib
import random
import re
import subprocess
import sys
import time
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sbn  # noqa: E402
from arricchisci import sparql  # noqa: E402

RADICE = pathlib.Path(__file__).resolve().parent.parent
D = RADICE / "docs" / "verifica-sbn"
SEME = 20261118
QUANTI = 100
CONGELATI = ["scripts/riconosci_sbn.py", "scripts/sbn.py"]
URI = "http://triplestore.iccu.sbn.it/resource/Agent/"
PARTICELLE = {"de", "di", "da", "del", "della", "van", "von", "der", "den", "la", "le", "du", "des", "ten", "ter", "y", "i",
              "e", "dos", "das", "do", "zu", "af", "ibn", "bin", "al", "el", "mac", "st"}


def impronte():
    return {f: hashlib.sha256((RADICE / f).read_bytes()).hexdigest() for f in CONGELATI}


def congela():
    D.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=RADICE, capture_output=True, text=True).stdout.strip()
    (D / "regole-congelate.json").write_text(json.dumps({"commit": commit, "sha256": impronte(),
        "nota": "regole del riconoscimento congelate prima della verifica; non modificarle fino alla fine della misura"},
        indent=1), encoding="utf-8")
    print("congelate", impronte())


def senza_accenti(t):
    return "".join(c for c in unicodedata.normalize("NFKD", t or "") if not unicodedata.combining(c))


def autori_noti():
    out = {}
    for f in sorted((RADICE / "data").glob("*[0-9][0-9][0-9][0-9].json")):
        if not f.name.startswith(("us-", "anniversari-")):
            for a in json.loads(f.read_text(encoding="utf-8"))["autori"]:
                out.setdefault(a["wikidata"], a)
    return out


def scegli():
    cache = json.loads((RADICE / "data" / "cache_sbn.json").read_text(encoding="utf-8"))
    autori = autori_noti()
    vecchi = set(json.loads(sorted((RADICE / "docs" / "campione").glob("sbn-base-*.json"))[-1].read_text(encoding="utf-8"))["autori"])
    popolazione = sorted(q for q in cache if q in autori and q not in vecchi)
    scelti = random.Random(SEME).sample(popolazione, min(QUANTI, len(popolazione)))
    return [(q, autori[q]) for q in scelti], len(popolazione), cache


def wikidata(qids):
    out = {q: {"p396": [], "viaf": [], "pseudonimi": [], "alias": [], "opere": []} for q in qids}
    for i in range(0, len(qids), 50):
        v = " ".join("wd:" + q for q in qids[i:i + 50])
        for b in sparql(f"""SELECT ?a ?p396 ?viaf ?ps ?al WHERE {{ VALUES ?a {{ {v} }}
              OPTIONAL {{ ?a wdt:P396 ?p396 }} OPTIONAL {{ ?a wdt:P214 ?viaf }} OPTIONAL {{ ?a wdt:P742 ?ps }}
              OPTIONAL {{ ?a skos:altLabel ?al FILTER(LANG(?al) IN ("it", "en")) }} }}"""):
            k = b["a"]["value"].rsplit("/", 1)[-1]
            for campo, chiave in (("p396", "p396"), ("viaf", "viaf"), ("ps", "pseudonimi"), ("al", "alias")):
                if campo in b and b[campo]["value"] not in out[k][chiave]:
                    out[k][chiave].append(b[campo]["value"])
        time.sleep(2)
    for q in qids:   # opere: stessa fonte che usa la misura (titoli Wikidata con P50)
        try:
            r = sparql(f"""SELECT DISTINCT ?l WHERE {{ ?w wdt:P50 wd:{q} . ?w rdfs:label ?l .
              FILTER(LANG(?l) IN ("it","en","fr","de","es","cs","ca","pl","pt","mul")) }} LIMIT 300""")
            out[q]["opere"] = sorted({x["l"]["value"] for x in r})
        except Exception:
            pass
        time.sleep(1)
    return out


def q_sbn(query):
    try:
        r = sbn.interroga(query)
    except Exception as e:
        return [{"errore": str(e)[:80]}]
    time.sleep(sbn.PAUSA)
    return r


def etichette(uris):
    if not uris:
        return {}
    out = {}
    for x in q_sbn("SELECT ?a ?l WHERE { VALUES ?a { " + " ".join(f"<{u}>" for u in uris) + f" }} ?a <{sbn.LAB}> ?l }}"):
        if "a" in x:
            out.setdefault(x["a"]["value"], x["l"]["value"])
    return out


def titoli(uri):
    r = q_sbn(f"SELECT DISTINCT ?t ?d WHERE {{ ?w <{sbn.BF}contribution> ?c . ?c <{sbn.BF}agent> <{uri}> . "
              f"?w <{sbn.BF}title> ?tt . ?tt <{sbn.BF}mainTitle> ?t . OPTIONAL {{ ?w <{sbn.BF}provisionActivity> ?pa . ?pa <{sbn.BF}date> ?d }} }} LIMIT 25")
    return sorted({(x["t"]["value"][:110] + (f" ({x['d']['value']})" if "d" in x else "")) for x in r if "t" in x})[:15]


def forme_cognome(nome):
    """Forme del cognome per pescare i candidati (prove per chi controlla, indipendenti dalle regole del sistema)."""
    p = nome.replace(",", " ").split()
    pezzi = [p[-1]] if p else []
    for i, w in enumerate(p[:-1]):
        if w.lower() in PARTICELLE and i + 1 < len(p):
            pezzi += p[i + 1:]
    pezzi += pezzi[0].split("-") if pezzi else []
    if len(p) >= 2:
        pezzi.append(p[0])     # ordine orientale o nome di battesimo usato come cognome
    out = []
    for w in pezzi:
        w = re.sub(r"[^\w]", "", w)
        for f in (w, senza_accenti(w)):
            if len(f) >= 3 and f not in out:
                out.append(f)
        m = re.match(r"([A-Za-z]{4,})[^A-Za-z]", w)
        if m and m.group(1) + "*" not in out:
            out.append(m.group(1) + "*")
    return out


def candidati(nome, alias):
    """Schede con il cognome (tutte le forme) + schede con tutte le parole del nome e degli alias."""
    out = {}
    for f in forme_cognome(nome):
        termine = f"\"{f}\"" if f.endswith("*") else f"'{f}'"
        r = q_sbn(f'SELECT DISTINCT ?a ?l WHERE {{ ?a <{sbn.LAB}> ?l . ?l bif:contains "{termine}" . '
                  f'FILTER(CONTAINS(STR(?a), "/resource/Agent/")) }} LIMIT 400')
        for x in r:
            if "a" in x:
                out.setdefault(x["a"]["value"], x["l"]["value"])
    for n in [nome] + list(alias)[:6]:
        p = [w for w in re.findall(r"[A-Za-z]{3,}", senza_accenti(n))][:4]
        if len(p) < 2:
            continue
        cond = " and ".join(f"'{w}'" for w in p)
        for x in q_sbn(f'SELECT DISTINCT ?a ?l WHERE {{ ?a <{sbn.LAB}> ?l . ?l bif:contains "{cond}" . '
                       f'FILTER(CONTAINS(STR(?a), "/resource/Agent/")) }} LIMIT 50'):
            if "a" in x:
                out.setdefault(x["a"]["value"], x["l"]["value"])
    return out


def norm(t):
    return set(re.findall(r"[a-z]+", senza_accenti(t).lower()))


def vicini(nome, alias, cand, quanti=12):
    """I candidati più vicini al nome: cognome in comune e poi iniziale del nome."""
    nomi = [nome] + list(alias)
    def punti(l):
        pl = norm(l.split("<")[0])
        best = 0
        for n in nomi:
            pn = norm(n)
            comuni = len(pl & pn)
            iniz = len({w[0] for w in pl} & {w[0] for w in pn})
            best = max(best, comuni * 10 + iniz)
        return best
    ordinati = sorted(cand.items(), key=lambda kv: (-punti(kv[1]), kv[1]))
    return [(u, l) for u, l in ordinati if punti(l) >= 10][:quanti]


def sistema_vecchio(a, viaf):
    nome, nascita, morte = a["nome"], a.get("nascita"), a.get("morte")
    if viaf:
        f = f'?a <{sbn.SAME}> <http://viaf.org/viaf/{viaf}> . FILTER(CONTAINS(STR(?a), "/resource/Agent/"))'
        n, _, _ = sbn.conta(f, sbn.interroga)
        if n:
            r = q_sbn(f'SELECT DISTINCT ?a WHERE {{ {f} }}')
            return {"metodo": "viaf", "registrazioni": n, "schede": sorted(x["a"]["value"] for x in r if "a" in x)}
    u, verificato = sbn.agenti_per_nome(nome, sbn.interroga, nascita, morte)
    if u:
        n, _, _ = sbn.conta("VALUES ?a { " + " ".join(f"<{x}>" for x in u) + " }", sbn.interroga)
        if n:
            return {"metodo": "nome_anni" if verificato else "nome", "registrazioni": n, "schede": sorted(u)}
    return {"metodo": None, "registrazioni": 0, "schede": []}


def prove():
    D.mkdir(parents=True, exist_ok=True)
    scelti, pop, cache = scegli()
    print(f"popolazione senza i 140: {pop}; scelti: {len(scelti)}", flush=True)
    wd = wikidata([q for q, _ in scelti])
    camp, prov = [], {}
    for i, (q, a) in enumerate(scelti, 1):
        w = wd[q]
        alias = w["pseudonimi"] + w["alias"]
        p396 = [u for u in (URI + "IT-ICCU-{}-{}".format(*m.groups()) for m in
                            (re.fullmatch(r"(?:IT\\ICCU\\)?([A-Z0-9]{4})\\?(\d{6})", c.strip()) for c in w["p396"]) if m)]
        viaf_sc = []
        for v in w["viaf"][:2]:
            viaf_sc += [x["a"]["value"] for x in q_sbn(f'SELECT DISTINCT ?a WHERE {{ ?a <{sbn.SAME}> <http://viaf.org/viaf/{v}> . '
                                                         f'FILTER(CONTAINS(STR(?a), "/resource/Agent/")) }}') if "a" in x]
        try:
            vecchio = sistema_vecchio(a, (w["viaf"] or [None])[0])
        except Exception as e:
            vecchio = {"errore": str(e)[:80], "schede": []}
        cand = candidati(a["nome"], alias)
        vic = vicini(a["nome"], alias, cand)
        da_vedere = list(dict.fromkeys(p396 + viaf_sc + vecchio.get("schede", []) + [u for u, _ in vic]))[:16]
        lab = etichette(da_vedere)
        prov[q] = {"nome": a["nome"], "nascita": a.get("nascita"), "morte": a.get("morte"), "paesi": a.get("paesi") or [],
                   "alias": alias, "opere_wikidata": w["opere"][:30], "n_opere": len(w["opere"]),
                   "p396": w["p396"], "p396_schede": p396, "viaf": w["viaf"], "viaf_schede": viaf_sc,
                   "candidati_totali": len(cand),
                   "schede": {u: {"etichetta": lab.get(u, "(non nel triplestore)"), "titoli": titoli(u),
                                  "da": [k for k, s in (("p396", p396), ("viaf", viaf_sc), ("vecchio", vecchio.get("schede", [])),
                                                        ("nome", [x for x, _ in vic])) if u in s]} for u in da_vedere}}
        camp.append({"n": i, "qid": q, "nome": a["nome"], "nascita": a.get("nascita"), "morte": a.get("morte"),
                     "paesi": a.get("paesi") or [], "p396": w["p396"], "viaf": w["viaf"], "alias": alias,
                     "opere": w["opere"], "vecchio": vecchio, "cache": cache.get(q)})
        print(f"{i:3} {a['nome'][:36]:36} candidati={len(cand):4} schede viste={len(da_vedere)} vecchio={vecchio.get('metodo')}", flush=True)
    (D / "campione.json").write_text(json.dumps({"seme": SEME, "popolazione": pop, "autori": camp}, ensure_ascii=False, indent=1), encoding="utf-8")
    (D / "prove.json").write_text(json.dumps(prov, ensure_ascii=False, indent=1), encoding="utf-8")


def breve(u):
    return u.rsplit("/", 1)[-1].replace("IT-ICCU-", "").replace("-", "")


def misura():
    import riconosci_sbn
    fermo = json.loads((D / "regole-congelate.json").read_text(encoding="utf-8"))
    if fermo["sha256"] != impronte():
        sys.exit("le regole sono cambiate dopo il congelamento: questo campione non vale più come verifica")
    camp = json.loads((D / "campione.json").read_text(encoding="utf-8"))["autori"]
    esiti = json.loads((D / "esiti.json").read_text(encoding="utf-8"))
    righe, conta, conta_v = [], collections.Counter(), collections.Counter()

    def giudica(e, sch, collegate):
        """e: C presente / A assente / I irrisolto; sch: {scheda: G giusta / X altra persona / ? non dimostrabile}."""
        sbagliate = [s for s in collegate if sch.get(s) == "X"]
        dubbie = [s for s in collegate if sch.get(s, "?") == "?"]
        giuste = [s for s in collegate if sch.get(s) == "G"]
        if e == "A":
            return ("persona sbagliata" if sbagliate else "senza prove sufficienti" if dubbie else "giusto (assente)")
        if e == "I":
            return ("persona sbagliata" if sbagliate else "senza prove sufficienti" if collegate else "irrisolto, non collegato")
        if sbagliate:
            return "persona sbagliata" + (" (con anche la giusta)" if giuste else "")
        if not giuste:
            return "senza prove sufficienti" if dubbie else "mancato"
        return "trovato" + (" con schede non dimostrabili" if dubbie else "")

    for a in camp:
        e = esiti[a["qid"]]
        autore = {k: a[k] for k in ("nome", "nascita", "morte", "p396", "viaf", "alias", "opere", "paesi")}
        t0 = time.time()
        try:
            r = riconosci_sbn.riconosci(autore)
        except Exception as ex:
            r = {"stato": "errore", "errore": str(ex)[:120], "schede": [], "prove": {}}
        nuove = sorted(breve(u) for u in r["schede"])
        vecchie = sorted(breve(u) for u in a["vecchio"].get("schede", []))
        dopo, prima = giudica(e["esito"], e["schede"], nuove), giudica(e["esito"], e["schede"], vecchie)
        conta[dopo] += 1
        conta_v[prima] += 1
        righe.append({"n": a["n"], "qid": a["qid"], "nome": a["nome"], "manuale": e["esito"], "prima": prima, "dopo": dopo,
                      "schede_nuove": nuove, "schede_vecchie": vecchie, "metodo": r.get("metodo"), "stato": r["stato"],
                      "prove": r.get("prove", {}), "ambigue": r.get("ambigue", {}), "secondi": round(time.time() - t0, 1)})
        print(f"{a['n']:3} {a['nome'][:34]:34} {e['esito']} prima={prima} | dopo={dopo} [{r.get('metodo')}]", flush=True)
    (D / "misura.json").write_text(json.dumps({"regole": fermo, "conteggi_dopo": conta, "conteggi_prima": conta_v,
                                                "autori": righe}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("PRIMA", dict(conta_v))
    print("DOPO", dict(conta))


if __name__ == "__main__":
    {"congela": congela, "prove": prove, "misura": misura}[sys.argv[1]]()
