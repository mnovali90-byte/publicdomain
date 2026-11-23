"""Seconda fonte per l'anno di morte degli autori, e illustratori delle loro opere.

Per ogni autore «letterario» dei file data/<anno>.json:
1. da Wikidata prende i codici dell'autore in due biblioteche nazionali:
   GND (Deutsche Nationalbibliothek, P227) e Library of Congress (P244);
2. legge l'anno di morte scritto nei loro cataloghi (lobid.org per GND, id.loc.gov per LoC);
3. confronta con l'anno di Wikidata e scrive nell'autore:
   "verifica": {"esito": "verificato" | "discorde" | "una_fonte", "fonti": {"wikidata": 1956, "gnd": 1956, "loc": 1956}}
   - verificato: almeno un'altra fonte e tutte uguali a Wikidata
   - discorde: almeno una fonte dà un anno diverso -> il sito lo segnala "da verificare"
   - documentato: le biblioteche non hanno l'autore, ma in Wikidata l'anno di morte è accompagnato da una o più
     fonti citate (per esempio l'autorità nazionale ceca, BnF, Oxford Dictionary of National Biography), tutte con lo stesso anno.
     Più debole di "verificato": la fonte non la leggiamo noi, la riporta Wikidata. Le citazioni sono in "citate".
     Se una fonte citata dà un anno diverso, l'esito è "discorde" anche quando GND e LoC concordano.
   - una_fonte: nessuna biblioteca e nessuna fonte citata
   VIAF provato il 17/11/2026 come terza fonte: dai server di GitHub risponde solo "troppe richieste" (Cloudflare)
   e la nuova interfaccia chiede un accesso da browser. Non usabile in automatico.
4. da Wikidata prende anche gli illustratori (P110) delle opere dell'autore, con il loro anno di morte:
   "illustratori": [{"opera": "...", "nome": "...", "morte": 1976}]  (le illustrazioni hanno diritti propri).

5. REGOLA DELLE DUE FONTI AUTOREVOLI (decisa da Marco il 20/11/2026): se almeno due fonti autorevoli diverse danno lo
   stesso anno di morte, e nessun altro anno ne ha altrettante, vale quell'anno, anche contro Wikidata.
   Autorevoli: le biblioteche che leggiamo noi (GND, Library of Congress) e, tra le fonti citate da Wikidata, le
   autorità delle biblioteche nazionali (BnF, Repubblica Ceca, IdRef, NUKAT, Biblioteca nazionale russa) e i grandi
   dizionari biografici (Diccionario Biográfico Español, Deutsche Biographie, Britannica, Store norske leksikon...).
   La stessa biblioteca citata due volte (GND letta da noi e GND citata da Wikidata) conta una volta sola.
   Non sono autorevoli: Wikidata stessa (anche la sua «altra data»), IMDb, Project Gutenberg, Open Library, siti di fan.
   - le fonti autorevoli danno ragione a Wikidata: esito «maggioranza» (confermato, con la fonte che dissente);
   - danno un altro anno: esito «corretto». L'autore esce dall'elenco sbagliato ed entra in quello giusto, se c'è
     (UE: morti nell'anno N-71; Spagna: N-81). Le correzioni restano in data/morti_corrette.json, così valgono anche per
     gli elenchi degli anni dopo.
   Se le fonti autorevoli non arrivano a due d'accordo, resta «discorde» (da verificare).

Le risposte delle biblioteche restano in data/cache_verifica.json e si richiedono di nuovo solo dopo 180 giorni.
Se una fonte non risponde, l'autore resta con le fonti che ci sono: niente si blocca.
"""
import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
DATA = RADICE / "data"
CACHE = DATA / "cache_verifica.json"
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
RINFRESCA = 180
BUDGET_MINUTI = 40


def get(url, accept="application/json", tentativi=3):
    for t in range(tentativi):
        try:
            req = urllib.request.Request(url, headers={**UA, "Accept": accept})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return None
        except Exception:
            pass
        time.sleep(3 * (t + 1))
    raise RuntimeError("non risponde: " + url)


def sparql(q):
    u = "https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(q)
    return json.loads(get(u, "application/sparql-results+json"))["results"]["bindings"]


def val(r, k):
    return r[k]["value"] if k in r else None


def anno(s):
    m = re.search(r"-?\d{4}", s or "")
    return int(m.group(0)) if m else None


def codici_e_illustratori(qids):
    cod, ill = {}, {}
    for i in range(0, len(qids), 80):
        valori = " ".join("wd:" + q for q in qids[i:i + 80])
        for r in sparql(f"""SELECT ?a ?gnd ?loc WHERE {{ VALUES ?a {{ {valori} }}
            OPTIONAL {{ ?a wdt:P227 ?gnd }} OPTIONAL {{ ?a wdt:P244 ?loc }} }}"""):
            q = val(r, "a").rsplit("/", 1)[-1]
            c = cod.setdefault(q, {})
            if val(r, "gnd"): c.setdefault("gnd", val(r, "gnd"))
            if val(r, "loc"): c.setdefault("loc", val(r, "loc"))
        time.sleep(1)
        for r in sparql(f"""SELECT ?a ?wLabel ?iLabel ?morte ?sl WHERE {{ VALUES ?a {{ {valori} }}
            ?w wdt:P50 ?a; wdt:P110 ?i; wikibase:sitelinks ?sl. FILTER(?i != ?a)
            OPTIONAL {{ ?i wdt:P570 ?morte }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "it,en,mul". }} }}"""):
            q = val(r, "a").rsplit("/", 1)[-1]
            nome, opera = val(r, "iLabel"), val(r, "wLabel")
            if re.fullmatch(r"Q\d+", nome or "") or re.fullmatch(r"Q\d+", opera or ""):
                continue
            ill.setdefault(q, []).append({"opera": opera, "nome": nome, "morte": anno(val(r, "morte")), "sl": int(val(r, "sl"))})
        time.sleep(1)
    for q, lista in ill.items():
        visti, pulita = set(), []
        for x in sorted(lista, key=lambda x: -x["sl"]):
            k = (x["opera"], x["nome"])
            if k in visti:
                continue
            visti.add(k)
            pulita.append({"opera": x["opera"], "nome": x["nome"], "morte": x["morte"]})
        ill[q] = pulita[:6]
    return cod, ill


def citazioni(qids):
    """Per ogni autore: {nome fonte: anno di morte} dalle fonti citate in Wikidata (P248 «affermato in»).
    Le importazioni da Wikipedia (P143) non contano: non sono una fonte esterna."""
    out = {}
    for i in range(0, len(qids), 50):
        valori = " ".join("wd:" + q for q in qids[i:i + 50])
        for r in sparql(f"""SELECT ?a ?anno ?fonteLabel WHERE {{ VALUES ?a {{ {valori} }}
            ?a p:P570 ?s . ?s psv:P570/wikibase:timeValue ?t . BIND(YEAR(?t) AS ?anno)
            ?s prov:wasDerivedFrom/pr:P248 ?fonte .
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,mul". }} }}"""):
            nome = val(r, "fonteLabel")
            if not nome or re.fullmatch(r"Q\d+", nome):
                continue
            out.setdefault(val(r, "a").rsplit("/", 1)[-1], {}).setdefault(nome, int(val(r, "anno")))
        time.sleep(1)
    return out


def anni_wikidata(qids):
    """Tutti gli anni di morte (P570) che Wikidata dà per ogni autore: se sono più d'uno l'anno è incerto."""
    out = {}
    for i in range(0, len(qids), 100):
        valori = " ".join("wd:" + q for q in qids[i:i + 100])
        for r in sparql(f"SELECT ?a (YEAR(?m) AS ?anno) WHERE {{ VALUES ?a {{ {valori} }} ?a wdt:P570 ?m }}"):
            if val(r, "anno"):
                out.setdefault(val(r, "a").rsplit("/", 1)[-1], set()).add(int(val(r, "anno")))
        time.sleep(1)
    return out


def morte_gnd(codice):
    t = get("https://lobid.org/gnd/" + urllib.parse.quote(codice) + ".json")
    if t is None:
        return None
    d = json.loads(t).get("dateOfDeath") or []
    return anno(d[0]) if d else None


def morte_loc(codice):
    t = get("https://id.loc.gov/authorities/names/" + urllib.parse.quote(codice) + ".json")
    if t is None:
        return None
    etichette = []
    io = "http://id.loc.gov/authorities/names/" + codice
    for nodo in json.loads(t):
        if nodo.get("@id") != io:          # il file contiene anche altre schede collegate: solo quella dell'autore
            continue
        for v in nodo.get("http://www.loc.gov/mads/rdf/v1#authoritativeLabel", []):
            etichette.append(v.get("@value", "") if isinstance(v, dict) else str(v))
    for e in etichette:
        m = re.search(r"(\d{4})\??-(\d{4})", e)   # «Brecht, Bertolt, 1898-1956»
        if m:
            return int(m.group(2))
    return None


from arricchisci import TIPO_CATALOGO, percentile  # noqa: E402  (stesse misure delle liste)
from regole import voce_morte  # noqa: E402
from regole import AUTOREVOLI, AUTOREVOLI_RE, NON_AUTOREVOLI_RE, maggioranza, decidi_morte, morti_liberi_nel  # noqa: E402,F401  (regole in un posto solo)
CORRETTE = DATA / "morti_corrette.json"
try:
    REGISTRO = json.load(open(DATA / "registro" / "autori.json", encoding="utf-8")).get("autori", {})
except Exception:
    REGISTRO = {}


def anno_atteso(f):
    """Anno di morte degli autori di un elenco (regola in scripts/regole.py, morti_liberi_nel)."""
    n = int(re.search(r"(\d{4})\.json$", f.name).group(1))
    return morti_liberi_nel(n, "es" if f.name.startswith("es-") else "it")


def verifica_a_mano(a, m):
    """Esito di una verifica a mano (data/verifiche_manuali.json, «autori»), con la regola del registro (regole.voce_morte):
    di norma «nazionale»; con «discorde» le fonti non concordano e l'autore resta nella lista con l'avviso «da verificare»."""
    if m.get("discorde"):
        v = voce_morte({"wikidata": anno(a.get("morte"))}, {}, m)
        return {"esito": "discorde", "fonti": v["f"], "citate": v["c"]}
    return {"esito": "nazionale", "fonti": {"wikidata": anno(a.get("morte"))},
            "nazionale": {"fonte": m["fonte"], "url": m["url"], "url_2": m.get("url_2"), "morte": m["morte"]}}


def _leggi_tolte():
    try:
        return json.load(open(DATA / "verifiche_manuali.json", encoding="utf-8")).get("verifiche_tolte", {})
    except Exception:
        return {}


def carica_aggiunti():
    """Correzioni a mano (data/verifiche_manuali.json) e schede proposte (data/registro/schede_proposte.json)."""
    try:
        _vm = json.load(open(DATA / "verifiche_manuali.json", encoding="utf-8"))
    except Exception:
        _vm = {}
    try:
        schede = json.load(open(DATA / "registro" / "schede_proposte.json", encoding="utf-8")).get("autori", {})
    except Exception:
        schede = {}
    return _vm.get("autori", {}), _vm.get("aggiunti_a_mano", {}), _vm.get("professioni_aggiunte", {}), schede


def inserisci_aggiunti(f, p, atteso, manuali, aggiunti, prof_mano, schede, anteprima=False):
    # 23/11/2026 (Marco): autori scelti a mano (data/verifiche_manuali.json «aggiunti_a_mano»: saggisti noti
    # soprattutto come autori di libri). Entrano solo nella loro lista, con la scheda di scripts/scheda_autore.py e
    # l'anno di morte controllato a mano su due fonti terze (esito «nazionale»); sono scrittori segnati a mano.
    presenti = {a["wikidata"] for a in p["autori"]}
    for q, ag in aggiunti.items():
        if ag.get("lista") != f.stem or q in presenti:
            continue
        if not ag.get("approvato") and not anteprima:   # entra solo dopo l'ok di Marco sulla fotografia
            continue
        sch, m = (schede.get(q) or {}).get("scheda"), manuali.get(q)
        if not sch or not m or m.get("morte") != atteso or anno(sch.get("morte")) not in (None, m["morte"]):
            print(f"  NON AGGIUNTO a {f.name}: {ag.get('nome')} (manca la scheda o l'anno di morte non torna)")
            continue
        nuovo = {k: x for k, x in sch.items() if k not in ("candidato",)}
        if re.fullmatch(r"Q\d+", nuovo.get("nome") or "Q0"):   # Wikidata senza etichetta: il nome scritto a mano
            nuovo["nome"] = ag.get("nome") or nuovo.get("nome")
        nuovo["morte"] = sch.get("morte") or str(m["morte"])
        nuovo["letterario"] = True
        for pr in (prof_mano.get(q) or {}).get("professioni", []):
            if pr not in nuovo.setdefault("professioni", []):
                nuovo["professioni"].append(pr)
        nuovo["tipo_catalogo"] = [TIPO_CATALOGO[x] for x in nuovo["professioni"] if x in TIPO_CATALOGO]
        nuovo["verifica"] = {"esito": "nazionale", "fonti": {"wikidata": anno(sch.get("morte"))},
                             "nazionale": {"fonte": m["fonte"], "url": m["url"], "url_2": m.get("url_2"), "morte": m["morte"]}}
        # indici come per gli altri della lista (0-100 sullo stesso dato), senza toccare quelli già calcolati
        lett = [a for a in p["autori"] if a.get("letterario") and "n_opere" in a]
        for campo, chiave in (("visite_it", "indice_it"), ("visite_en", "indice_en"), ("visite_es", "indice_es"),
                              ("visite_de", "indice_de"), ("visite_fr", "indice_fr"), ("pagine_wikipedia", "indice_int")):
            val = [a[campo] for a in lett if a.get(campo) is not None]
            if nuovo.get(campo) is not None and val:
                nuovo[chiave] = 0 if nuovo[campo] == 0 else round(100 * percentile(nuovo[campo], val))
        p["autori"].append(nuovo)
        print(f"  AGGIUNTO a {f.name}: {ag.get('nome')} (scelto a mano; morto nel {m['morte']} secondo {m['fonte']})")

def inserisci_rientri(f, p, atteso, tolte, schede):
    """23/11/2026 (Marco): un autore la cui verifica a mano è stata tolta (data/verifiche_manuali.json, «verifiche_tolte»)
    torna allo stato delle fonti automatiche: se l'anno di morte di Wikidata (scheda di scripts/scheda_autore.py) è
    quello della lista e l'autore non c'è, rientra; le biblioteche (GND, Library of Congress) le legge il giro dopo."""
    presenti = {a["wikidata"] for a in p["autori"]}
    for q in tolte:
        sch = (schede.get(q) or {}).get("scheda")
        if not sch or q in presenti or anno(sch.get("morte")) != atteso or not sch.get("letterario"):
            continue
        nuovo = {k: x for k, x in sch.items() if k not in ("candidato",)}
        esito, deciso, fonti_d = decidi_morte({"wikidata": anno(sch["morte"])}, {})
        nuovo["verifica"] = {"esito": esito, "fonti": {"wikidata": anno(sch["morte"])}}
        lett = [a for a in p["autori"] if a.get("letterario") and "n_opere" in a]
        for campo, chiave in (("visite_it", "indice_it"), ("visite_en", "indice_en"), ("visite_es", "indice_es"),
                              ("visite_de", "indice_de"), ("visite_fr", "indice_fr"), ("pagine_wikipedia", "indice_int")):
            val = [a[campo] for a in lett if a.get(campo) is not None]
            if nuovo.get(campo) is not None and val:
                nuovo[chiave] = 0 if nuovo[campo] == 0 else round(100 * percentile(nuovo[campo], val))
        p["autori"].append(nuovo)
        print(f"  RIENTRA in {f.name}: {nuovo.get('nome')} (verifica a mano tolta; Wikidata {anno(sch['morte'])})")


def main():
    inizio = time.time()
    oggi = dt.date.today()
    try:
        cache = json.load(open(CACHE, encoding="utf-8"))
    except Exception:
        cache = {"gnd": {}, "loc": {}}
    if cache.get("versione_loc") != 2:   # la prima lettura LoC prendeva anche schede collegate: si rilegge
        cache["loc"], cache["versione_loc"] = {}, 2
    file = [f for f in sorted(DATA.glob("*[0-9][0-9][0-9][0-9].json")) if not f.name.startswith(("us-", "anniversari-"))]
    pacchetti = {f: json.load(open(f, encoding="utf-8")) for f in file}
    qids = sorted({a["wikidata"] for p in pacchetti.values() for a in p["autori"] if a.get("letterario")})
    print("autori da verificare:", len(qids))
    cod, ill = codici_e_illustratori(qids)
    try:
        cit = citazioni(qids)
    except Exception as e:      # se Wikidata non risponde si va avanti senza: restano GND e LoC
        print("fonti citate non lette:", e)
        cit = None
    try:
        anni_wd = anni_wikidata(qids)
    except Exception as e:      # come per le citazioni: senza risposta si va avanti
        print("anni di morte multipli non letti:", e)
        anni_wd = None

    fonti = {"gnd": morte_gnd, "loc": morte_loc}
    esauriti = False
    for q in qids:
        for nome_f, leggi in fonti.items():
            c = cod.get(q, {}).get(nome_f)
            if not c:
                continue
            vecchio = cache[nome_f].get(c)
            if vecchio and (oggi - dt.date.fromisoformat(vecchio["controllato"])).days < RINFRESCA:
                continue
            if time.time() - inizio > BUDGET_MINUTI * 60:
                esauriti = True
                continue
            try:
                cache[nome_f][c] = {"morte": leggi(c), "controllato": oggi.isoformat()}
            except Exception as e:
                print(nome_f, c, "non letto:", e)
            time.sleep(0.2)

    manuali, aggiunti, prof_mano, schede = carica_aggiunti()
    _tolte = _leggi_tolte()
    conta = {"verificato": 0, "maggioranza": 0, "corretto": 0, "documentato": 0, "discorde": 0, "una_fonte": 0, "nazionale": 0, "tolti": 0}
    corr = {}
    for f, p in pacchetti.items():
        anno_file = int(re.search(r"(\d{4})\.json$", f.name).group(1))
        tenuti = []
        for a in p["autori"]:
            m = manuali.get(a["wikidata"])
            if m and anno(a.get("morte")) != m["morte"]:
                # la fonte nazionale dà un altro anno di morte: l'autore non appartiene a questo elenco
                print(f"  TOLTO da {f.name}: {a['nome']} (Wikidata {anno(a.get('morte'))}, {m['fonte']} {m['morte']})")
                conta["tolti"] += 1
                continue
            tenuti.append(a)
        p["autori"] = tenuti
        for a in p["autori"]:
            m = manuali.get(a["wikidata"])
            if m:
                a["verifica"] = verifica_a_mano(a, m)
                conta[a["verifica"]["esito"]] += 1
                if ill.get(a["wikidata"]):
                    a["illustratori"] = ill[a["wikidata"]]
                continue
            if not a.get("letterario"):
                continue
            q = a["wikidata"]
            fv = {"wikidata": a.get("morte_wikidata") or anno(a.get("morte"))}
            for nome_f in fonti:
                c = cod.get(q, {}).get(nome_f)
                y = (cache[nome_f].get(c) or {}).get("morte") if c else None
                if y:
                    fv[nome_f] = y
            if anni_wd is None:     # giro senza risposta: si tiene l'altra data trovata il giro prima
                altra = ((a.get("verifica") or {}).get("fonti") or {}).get("wikidata_altra")
            else:
                altra = next(iter(sorted(anni_wd.get(q, set()) - {fv["wikidata"]})), None)
            if altra:
                fv["wikidata_altra"] = altra     # Wikidata stessa dà un altro anno di morte
            altre = [y for k, y in fv.items() if k != "wikidata"]
            if cit is None:     # giro senza citazioni: si tengono quelle del giro prima
                citate = (a.get("verifica") or {}).get("citate") or {}
            else:
                citate = cit.get(q, {})
            r = REGISTRO.get(q)
            if r and r.get("e") != "nazionale":
                # REGISTRO UNICO (20/11/2026): la decisione è quella di data/registro/autori.json, presa con la stessa
                # regola (scripts/regole.py). Qui si ricalcola solo per chi nel registro non c'è ancora.
                fv, citate = dict(r["f"]), dict(r.get("c") or {})
                esito, deciso, fonti_d = r["e"], r["m"], r.get("a")
                lista = a.get("morte_wikidata") or anno(a.get("morte"))
                if esito == "corretto" and deciso == lista:   # Wikidata ha più anni: le fonti confermano quello della lista
                    esito = "maggioranza"
                    fv["wikidata"] = lista
            else:
                esito, deciso, fonti_d = decidi_morte(fv, citate)
            magg = (deciso, fonti_d) if fonti_d else None
            a["verifica"] = {"esito": esito, "fonti": fv}
            if magg:
                a["verifica"]["autorevoli"] = {"morte": magg[0], "fonti": magg[1]}
            if esito == "corretto":
                corr[q] = {"nome": a["nome"], "morte_wikidata": fv["wikidata"], "morte": magg[0], "fonti": magg[1],
                           "scheda": {k: v for k, v in a.items() if k not in ("verifica",)}}
            if citate:
                a["verifica"]["citate"] = citate
            conta[esito] += 1
            if ill.get(q):
                a["illustratori"] = ill[q]
            else:
                a.pop("illustratori", None)
    # regola delle due fonti autorevoli: l'autore va nell'elenco dell'anno giusto (vedi il punto 5 in cima)
    try:
        vecchie = json.load(open(CORRETTE, encoding="utf-8")).get("autori", {})
    except Exception:
        vecchie = {}
    tutte = {**vecchie, **corr}
    for q in list(tutte):
        if q in manuali and manuali[q].get("morte") != tutte[q].get("morte"):   # il controllo a mano vince
            tutte.pop(q)
        # 23/11/2026 (Dehkhoda): se il controllo a mano dà lo stesso anno, l'autore che manca va aggiunto (scheda qui)
    for f, p in pacchetti.items():
        atteso = anno_atteso(f)
        tenuti = []
        for a in p["autori"]:
            c = tutte.get(a["wikidata"])
            if c and c["morte"] != atteso:
                print(f"  TOLTO da {f.name}: {a['nome']} (Wikidata {c['morte_wikidata']}, {', '.join(c['fonti'])} {c['morte']})")
                conta["tolti"] += 1
                continue
            tenuti.append(a)
        p["autori"] = tenuti
        presenti = {a["wikidata"] for a in p["autori"]}
        for q, c in tutte.items():
            if c["morte"] == atteso and q not in presenti:
                nuovo = dict(c["scheda"])
                nuovo["morte_wikidata"] = c["morte_wikidata"]
                nuovo["morte"] = str(c["morte"])
                nuovo["verifica"] = {"esito": "corretto", "fonti": {"wikidata": c["morte_wikidata"]},
                                     "autorevoli": {"morte": c["morte"], "fonti": c["fonti"]}}
                m = manuali.get(q)
                if m:                  # verifica a mano: esito «nazionale», come per chi è già nell'elenco
                    nuovo["verifica"] = {"esito": "nazionale", "fonti": {"wikidata": c["morte_wikidata"]},
                                         "nazionale": {"fonte": m["fonte"], "url": m["url"], "url_2": m.get("url_2"), "morte": m["morte"]}}
                p["autori"].append(nuovo)
                print(f"  AGGIUNTO a {f.name}: {c['nome']} (morto nel {c['morte']} secondo {', '.join(c['fonti'])})")
        inserisci_aggiunti(f, p, atteso, manuali, aggiunti, prof_mano, schede)
        inserisci_rientri(f, p, atteso, _tolte, schede)
        for a in p["autori"]:          # chi è già nell'elenco giusto prende l'anno delle fonti autorevoli
            c = tutte.get(a["wikidata"])
            if c and c["morte"] == atteso and anno(a.get("morte")) != c["morte"]:
                a["morte_wikidata"] = c["morte_wikidata"]
                a["morte"] = str(c["morte"])
        f.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
    CORRETTE.write_text(json.dumps({"nota": "Anni di morte corretti con la regola delle due fonti autorevoli (scripts/verifica.py, punto 5).",
                                    "autori": tutte}, ensure_ascii=False, indent=1), encoding="utf-8")
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    n_ill = len({a["wikidata"] for p in pacchetti.values() for a in p["autori"] if a.get("illustratori")})
    print("autori con illustratori noti:", n_ill)
    print("esiti (per file, un autore può contare più volte):", conta, "| tempo finito prima del termine:" if esauriti else "")
    discordi = sorted({(a["nome"], json.dumps(a["verifica"]["fonti"])) for p in pacchetti.values() for a in p["autori"]
                       if (a.get("verifica") or {}).get("esito") == "discorde"})
    discordi = sorted({(a["nome"], json.dumps({**a["verifica"]["fonti"], **a["verifica"].get("citate", {})}, ensure_ascii=False))
                       for p in pacchetti.values() for a in p["autori"] if (a.get("verifica") or {}).get("esito") == "discorde"})
    for n, fv in discordi[:40]:
        print("  DISCORDE:", n, fv)


def solo_aggiunti():
    """Senza rete: rifà le verifiche a mano e mette nelle liste gli autori scelti a mano che hanno già la scheda (stesso codice del giro)."""
    manuali, aggiunti, prof_mano, schede = carica_aggiunti()
    _tolte = _leggi_tolte()
    for f in sorted(DATA.glob("*.json")):
        if not re.fullmatch(r"(es-)?\d{4}\.json", f.name):
            continue
        p = json.load(open(f, encoding="utf-8"))
        n, prima = len(p["autori"]), json.dumps(p["autori"], ensure_ascii=False)
        for a in p["autori"]:       # verifiche a mano cambiate (stesso codice del giro)
            if a["wikidata"] in manuali and anno(a.get("morte")) == manuali[a["wikidata"]]["morte"]:
                a["verifica"] = verifica_a_mano(a, manuali[a["wikidata"]])
        inserisci_aggiunti(f, p, anno_atteso(f), manuali, aggiunti, prof_mano, schede, anteprima="--anteprima" in sys.argv)
        inserisci_rientri(f, p, anno_atteso(f), _tolte, schede)
        if len(p["autori"]) != n or json.dumps(p["autori"], ensure_ascii=False) != prima:
            f.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    if "--solo-aggiunti" in sys.argv:
        sys.exit(solo_aggiunti())
    sys.exit(main())
