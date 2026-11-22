"""Dati per la pagina "Storico" di Public Domain Radar: opere già in pubblico dominio negli USA
(tutto ciò che è uscito fino al 1930, cioè 95 anni compiuti), con le playlist più lette della settimana.

Fonti aperte: Wikidata (opere, autori, anno di prima pubblicazione), Wikipedia (visite).

Due insiemi di dati con due scopi diversi, così il lavoro resta leggero:
  RICERCA   TUTTE le opere con anno certo e almeno una pagina Wikipedia, senza visite.
            Spezzata in un file per lettera (data/storico/ricerca/a.json ...): la pagina scarica
            solo la lettera che serve. Contiene anche gli autori (nome, anno di morte).
  PLAYLIST  solo le prime MAX_VISITE opere per fama (numero di lingue con pagina Wikipedia):
            per queste si contano le visite della settimana su Wikipedia in italiano, inglese, francese,
            tedesco e spagnolo (19/11/2026: la pagina ordina per la lingua del paese scelto, come il resto del sito).
            Scrive data/storico/opere.json (quelle misurate) e data/storico/playlist.json.

Regola per il file: prime due lettere (senza accenti) della prima parola e della prima parola
dopo un eventuale articolo (the, il, la, der, les...). Per gli autori: prima e ultima parola del nome.
La pagina deve usare la stessa regola (funzione chiavi_ricerca).

Limite noto: le opere molto antiche spesso non hanno un anno di prima pubblicazione su Wikidata e restano fuori.
Si lancia a mano o dalla GitHub Action .github/workflows/storico.yml (una volta al mese, il 2).
"""
import json, os, re, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from opere import CLASSI, GENERI, get, qid, sparql, val  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import applica_registro  # noqa: E402
from per_autore import semi, opere_per_autore, opere_anonime, libera_ue, libera_usa, libera, info_autori, sparql_o_errore  # noqa: E402
import duke  # noqa: E402  seconda fonte per gli USA (19/11/2026)
import regole as R  # noqa: E402  (regole per paese in un posto solo)

UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
ANNO_A = int(os.environ.get("STORICO_ANNO_A", R.pubblicate_libere_usa_nel(date.today().year)))   # 2026 -> 1930
ANNO_DA = int(os.environ.get("STORICO_ANNO_DA", 1800))
FASCE_ANTICHE = [(-3000, 1400), (1400, 1600), (1600, 1700), (1700, ANNO_DA)]   # prima di ANNO_DA, a fasce
MAX_VISITE = int(os.environ.get("STORICO_MAX_VISITE", 3000))
BUDGET_WIKIDATA = float(os.environ.get("BUDGET_MINUTI_WIKIDATA", 60))   # tempo massimo per scaricare periodi nuovi
BUDGET_VISITE = float(os.environ.get("BUDGET_MINUTI_VISITE", 35))       # tempo massimo per le visite della settimana
RINFRESCA_GIORNI = 30   # un periodo già scaricato si riscarica solo dopo 30 giorni
USCITA = "data/storico"
SOGLIA = 1000   # sotto questo numero di opere qualcosa è andato storto: non si sovrascrive nulla
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chiavi import ARTICOLI, chiavi_ricerca, norm as _norm, lettera as _lettera  # noqa: E402,F401  (regola di ricerca in storico/chiavi.py)


# ------------------------------------------------------------------ Wikidata
def opere_periodo(da, a):
    """Opere con anno di prima pubblicazione tra da e a (inclusi), almeno una pagina Wikipedia.
    v3 (19/11/2026, dopo il confronto con la Duke), in tre interrogazioni leggere (una sola andava in timeout):
    1. opere di un tipo letterario con la loro data di pubblicazione più vecchia (come prima);
    2. opere SENZA tipo ma con un autore (P50), come «Now We Are Six»;
    3. opere SENZA data propria che hanno la data su un'edizione (P629), come «New Hampshire» di Frost.
    Se una delle tre non risponde il periodo resta da rifare (None)."""
    classi = " ".join("wd:" + c for c in CLASSI)
    coda = """?w wikibase:sitelinks ?sl. FILTER(?sl>=1)
      OPTIONAL {{ ?w wdt:P50 ?a. OPTIONAL {{ ?a wdt:P570 ?morte }} }}
      OPTIONAL {{ ?w rdfs:label ?wit FILTER(LANG(?wit)="it") }}
      OPTIONAL {{ ?en schema:about ?w; schema:isPartOf <https://en.wikipedia.org/> }}
      OPTIONAL {{ ?itw schema:about ?w; schema:isPartOf <https://it.wikipedia.org/> }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,it,mul". }} }}"""
    testa = "SELECT ?w ?wLabel ?wit ?a ?aLabel ?morte ?sl ?en ?itw (YEAR(?d) AS ?anno) WHERE {{"
    domande = [
        testa + f"""
      VALUES ?c {{ {classi} }}
      {{ ?w wdt:P31 ?c }} UNION {{ ?w wdt:P31 wd:Q47461344; wdt:P7937 ?c }}
      ?w wdt:P577 ?d. FILTER(YEAR(?d)>={da} && YEAR(?d)<={a})
      FILTER NOT EXISTS {{ ?w wdt:P577 ?d0 FILTER(?d0 < ?d) }}   # conta la PRIMA pubblicazione (18/11/2026)
      """ + coda.format(),
        testa + f"""
      ?w wdt:P577 ?d. FILTER(YEAR(?d)>={da} && YEAR(?d)<={a})
      ?w wdt:P50 [] . FILTER NOT EXISTS {{ ?w wdt:P31 [] }}
      FILTER NOT EXISTS {{ ?w wdt:P577 ?d0 FILTER(?d0 < ?d) }}
      """ + coda.format(),
        testa + f"""
      ?ed wdt:P629 ?w; wdt:P577 ?d. FILTER(YEAR(?d)>={da} && YEAR(?d)<={a})
      FILTER NOT EXISTS {{ ?w wdt:P577 [] }}
      FILTER NOT EXISTS {{ ?ed0 wdt:P629 ?w; wdt:P577 ?d1 FILTER(?d1 < ?d) }}
      {{ VALUES ?c {{ {classi} }} ?w wdt:P31 ?c }} UNION {{ ?w wdt:P50 [] }}
      """ + coda.format(),
    ]
    righe = []
    for q in domande:
        r = sparql_o_errore(q)
        if r is None:
            return None
        righe += r
    out = {}
    for r in righe:
        k = qid(val(r, "w"))
        o = out.setdefault(k, {"qid": k, "titolo": val(r, "wLabel"), "titolo_it": val(r, "wit"),
                               "anno": int(val(r, "anno") or 0), "autori": {}, "pagine": int(val(r, "sl")),
                               "wiki_en": None, "wiki_it": None})
        if val(r, "anno") and (not o["anno"] or int(val(r, "anno")) < o["anno"]):
            o["anno"] = int(val(r, "anno"))
        if val(r, "a"):
            x = o["autori"].setdefault(qid(val(r, "a")), {"nome": val(r, "aLabel"), "morte": None})
            if val(r, "morte"):
                m = re.match(r"(-?\d+)", val(r, "morte"))   # 22/11/2026: prima perdeva il segno meno (Platone 348 invece di -348)
                if m and (x["morte"] is None or int(m.group(1)) > x["morte"]):
                    x["morte"] = int(m.group(1))   # più anni di morte: si tiene il più tardo (prudente)
        if val(r, "en") and not o["wiki_en"]: o["wiki_en"] = val(r, "en")
        if val(r, "itw") and not o["wiki_it"]: o["wiki_it"] = val(r, "itw")
    res = []
    for o in out.values():
        if re.fullmatch(r"Q\d+", o["titolo"] or ""):
            continue  # senza etichetta leggibile
        o["autori"] = [{"qid": k, "nome": d["nome"], "morte": d["morte"]} for k, d in o["autori"].items()
                       if not re.fullmatch(r"Q\d+", d["nome"] or "")]
        res.append(o)
    return res


def lingua_genere_qid(qids):
    """Lingua originale (P407) e genere (P136) per un elenco di opere, a blocchi di 150 (query leggere)."""
    out = {}
    qids = list(qids)
    for i in range(0, len(qids), 150):
        valori = " ".join("wd:" + k for k in qids[i:i + 150])
        q = f'''SELECT ?w ?len ?lit ?gen WHERE {{ VALUES ?w {{ {valori} }}
          OPTIONAL {{ ?w wdt:P407 ?l. ?l rdfs:label ?len FILTER(LANG(?len)="en"). OPTIONAL {{ ?l rdfs:label ?lit FILTER(LANG(?lit)="it") }} }}
          OPTIONAL {{ ?w wdt:P136 ?g. ?g rdfs:label ?gen FILTER(LANG(?gen)="en") }} }}'''
        for r in sparql(q):
            k = qid(val(r, "w"))
            o = out.setdefault(k, {"lingua": None, "generi": set()})
            if val(r, "len") and not o["lingua"]:
                en = re.sub(r"^(American|British|Australian|Canadian) ", "", val(r, "len"))
                o["lingua"] = {"en": en, "it": val(r, "lit") or en}
            if val(r, "gen"):
                g = val(r, "gen").lower()
                for parola, chiave in GENERI:
                    if parola in g:
                        o["generi"].add(chiave); break
        time.sleep(1)
    for o in out.values():
        o["generi"] = sorted(o["generi"])
    return out


# ------------------------------------------------------------------ Wikipedia
def finestra():
    """Gli ultimi 7 giorni per cui Wikimedia ha già i dati (di solito si fermano a ieri)."""
    fine = date.today() - timedelta(days=2)
    return fine - timedelta(days=6), fine


def visite_settimana(wiki, url, ini, fine):
    """Visite (persone, non robot) in 7 giorni. 0 se la pagina non ha visite; None se manca la pagina o c'è un errore."""
    if not url:
        return None
    t = urllib.parse.unquote(url.rsplit("/", 1)[-1])
    u = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{wiki}.wikipedia/all-access/user/"
         + urllib.parse.quote(t, safe="") + "/daily/" + ini.strftime("%Y%m%d") + "/" + fine.strftime("%Y%m%d"))
    for tentativo in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30) as r:
                return sum(i["views"] for i in json.load(r).get("items", []))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 0
        except Exception:
            pass
        time.sleep(3 * (tentativo + 1))
    return None


LINGUE_VISITE = ("it", "en", "fr", "de", "es")   # Italia, Regno Unito e USA, Francia, Germania, Spagna


def pagine_wiki(qids):
    """Indirizzo della pagina Wikipedia di ogni opera nelle cinque lingue, a blocchi di 200 (query leggere).
    Se Wikidata non risponde il blocco resta vuoto e si tengono gli indirizzi già noti."""
    out, qids = {}, list(qids)
    siti = " ".join(f"<https://{l}.wikipedia.org/>" for l in LINGUE_VISITE)
    for i in range(0, len(qids), 200):
        valori = " ".join("wd:" + k for k in qids[i:i + 200])
        r = sparql_o_errore(f"SELECT ?w ?art ?sito WHERE {{ VALUES ?w {{ {valori} }} VALUES ?sito {{ {siti} }} "
                            f"?art schema:about ?w; schema:isPartOf ?sito }}")
        for x in r or []:
            l = val(x, "sito").split("//")[1].split(".")[0]
            out.setdefault(qid(val(x, "w")), {})[l] = val(x, "art")
        time.sleep(1)
    return out


# ------------------------------------------------------------------ playlist
def escluse():
    """QID di opere e autori che non entrano mai in classifiche e playlist (data/storico_esclusioni.json)."""
    try:
        e = json.load(open("data/storico_esclusioni.json", encoding="utf8"))
        return set(e.get("qid", {})), set(e.get("autori_qid", {}))
    except Exception:
        return set(), set()


def costruisci_playlist(ops):
    no_opere, no_autori = escluse()
    ops = [o for o in ops if o["qid"] not in no_opere and not any(a["qid"] in no_autori for a in o["autori"])]
    def top(lista, n):
        return [o["qid"] for o in sorted(lista, key=lambda o: (-o["visite_sett"], -o["pagine"]))[:n]]

    per_autore = {}
    for o in ops:
        for a in o["autori"]:
            per_autore.setdefault(a["qid"], {"nome": a["nome"], "opere": []})["opere"].append(o)
    autori = [{"qid": k, "nome": a["nome"], "visite_sett": sum(o["visite_sett"] for o in a["opere"]),
               "opere": top(a["opere"], 30)} for k, a in per_autore.items() if len(a["opere"]) >= 3]
    autori.sort(key=lambda a: -a["visite_sett"])
    # un autore con quasi le stesse opere di uno già in lista (Jacob e Wilhelm dopo "Fratelli Grimm") si salta
    unici, visti = [], []
    for a in autori:
        s = set(a["opere"])
        if any(len(s & v) >= 0.6 * len(s) for v in visti):
            continue
        visti.append(s); unici.append(a)
    autori = unici

    generi, lingue, decenni = {}, {}, {}
    for o in ops:
        for g in o.get("generi") or []:
            generi.setdefault(g, []).append(o)
        if o.get("lingua"):
            lingue.setdefault(o["lingua"]["en"], []).append(o)
        y = o.get("anno")
        decenni.setdefault("data non nota" if y is None else str(y // 10 * 10) if y >= 1800 else "prima del 1800", []).append(o)

    # tre scaffali sulle differenze tra paesi: utili a chi pubblica (un libro libero negli USA non lo è per forza in Italia)
    anno_ue = R.morti_liberi_nel(date.today().year, "it")
    ue, usa = libera_ue, libera_usa
    def ultimo_morto(o):
        m = [a.get("morte") for a in o.get("autori") or [] if a.get("morte") is not None]
        return max(m) if m else None
    confronto = {
        "solo_usa": top([o for o in ops if usa(o) and not ue(o)], 30),
        "solo_ue": top([o for o in ops if ue(o) and not usa(o)], 30),
        "nuovi": top([o for o in ops if o.get("anno") == ANNO_A or (ue(o) and ultimo_morto(o) == anno_ue)], 30),
    }

    def gruppi(d, minimo, n=30):
        r = [{"chiave": k, "n": len(v), "opere": top(v, n)} for k, v in d.items() if len(v) >= minimo]
        return sorted(r, key=lambda g: -g["n"])
    return {"piu_letti": top(ops, 50), "autori": autori[:40],
            "generi": gruppi(generi, 5), "lingue": gruppi(lingue, 5), "decenni": gruppi(decenni, 1, 20), **confronto}


# ------------------------------------------------------------------ ricerca (un file per lettera)
def scrivi_ricerca(ops):
    cartella = f"{USCITA}/ricerca"
    os.makedirs(cartella, exist_ok=True)
    for f in os.listdir(cartella):
        if f.endswith(".json"):
            os.remove(os.path.join(cartella, f))
    lettere = {}
    autori = {}
    for o in ops:
        riga = [o["qid"], o["titolo"], o["titolo_it"] or "", o["anno"], o["pagine"],
                [[a["qid"], a["nome"], a["morte"], 1 if a.get("antico") else 0, a.get("morte_incerta", 0), a.get("alleato", 0)]
                 for a in o["autori"]], o.get("anno_duke") or 0]   # anno della Duke se diverso dalla prima data di Wikidata
        for k in chiavi_ricerca(o["titolo"]) | chiavi_ricerca(o["titolo_it"] or ""):
            lettere.setdefault(k, {"opere": [], "autori": []})["opere"].append(riga)
        for a in o["autori"]:
            x = autori.setdefault(a["qid"], {"qid": a["qid"], "nome": a["nome"], "morte": a["morte"], "n": 0,
                                             "antico": 1 if a.get("antico") else 0,
                                             "incerta": a.get("morte_incerta", 0), "alleato": a.get("alleato", 0)})
            x["n"] += 1
    for a in autori.values():
        for k in chiavi_ricerca(a["nome"], autore=True):
            lettere.setdefault(k, {"opere": [], "autori": []})["autori"].append([a["qid"], a["nome"], a["morte"], a["n"], a["antico"], a["incerta"], a["alleato"]])
    peso = 0
    for k, d in lettere.items():
        d["opere"].sort(key=lambda r: -r[4])
        d["autori"].sort(key=lambda r: -r[3])
        s = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
        peso += len(s)
        open(f"{cartella}/{k}.json", "w", encoding="utf8").write(s)
    return len(autori), len(lettere), peso


def main():
    inizio = time.time()
    os.makedirs(USCITA, exist_ok=True)
    precedenti = {}
    try:
        precedenti = {o["qid"]: o for o in json.load(open(f"{USCITA}/opere.json", encoding="utf8"))["opere"]}
    except Exception:
        pass
    ini, fine = finestra()

    # 1) OPERE: ogni periodo si salva in data/storico/periodi/ appena scaricato.
    #    Se il tempo finisce, il giro dopo riparte dai periodi mancanti (niente lavoro perso).
    cartella_p = f"{USCITA}/periodi"
    os.makedirs(cartella_p, exist_ok=True)
    oggi = date.today()
    periodi = [(da, a - 1) for da, a in FASCE_ANTICHE] + [(y, y) for y in range(ANNO_DA, ANNO_A + 1)]
    tutte, mancanti, saltati = {}, [], []
    inizio_wd = time.time()
    for da, a in periodi:
        nome = f"{da}-{a}"
        f = f"{cartella_p}/{nome}.json"
        vecchio = None
        try:
            vecchio = json.load(open(f, encoding="utf8"))
        except Exception:
            pass
        # v2 (18/11/2026): l'anno è la PRIMA pubblicazione; v3 (19/11/2026): edizioni e opere senza tipo. Si riscarica
        fresco = vecchio and vecchio.get("v") == 3 and (oggi - date.fromisoformat(vecchio["scaricato"])).days < RINFRESCA_GIORNI
        if not fresco and time.time() - inizio_wd < BUDGET_WIKIDATA * 60:
            lista = []
            for tentativo in range(3):          # Wikidata ogni tanto va in timeout: si riprova
                lista = opere_periodo(da, a)
                if lista:
                    break
                lista = lista or []
                time.sleep(20 * (tentativo + 1))
            print(nome, "opere:", len(lista), flush=True)
            if lista:
                json.dump({"v": 3, "scaricato": oggi.isoformat(), "opere": lista}, open(f, "w", encoding="utf8"),
                          ensure_ascii=False, separators=(",", ":"))
                vecchio = {"opere": lista}
            else:
                saltati.append(nome)
        if vecchio:
            for o in vecchio["opere"]:
                tutte[o["qid"]] = o
        else:
            mancanti.append(nome)
    # 1b) SECONDA STRADA: tutte le opere scritte degli autori (vedi storico/per_autore.py)
    fine_budget = inizio_wd + BUDGET_WIKIDATA * 60
    autori_date = {a["qid"] for o in tutte.values() for a in o["autori"]}
    semi_q, fasce_mancanti = semi(autori_date, fine_budget)
    per_aut, cassetti_mancanti = opere_per_autore(semi_q, fine_budget)
    prima = len(tutte)
    for o in per_aut:
        tutte[o["qid"]] = o
    anonime = opere_anonime() if time.time() < fine_budget else None
    for o in anonime or []:
        tutte.setdefault(o["qid"], o)
    print("opere famose senza autore:", "non lette" if anonime is None else len(anonime))
    print(f"autori-seme: {len(semi_q)} | opere dalla ricerca per data: {prima} | dopo la ricerca per autore: {len(tutte)}"
          f" | fasce di autori mancanti: {len(fasce_mancanti)} | cassetti da riscaricare: {cassetti_mancanti}", flush=True)
    if fasce_mancanti or cassetti_mancanti:
        mancanti = mancanti + [f"semi:{k}" for k in fasce_mancanti] + ([f"cassetti:{cassetti_mancanti}"] if cassetti_mancanti else [])
    if saltati:
        print("PERIODI SENZA RISPOSTA da Wikidata:", ", ".join(saltati))
    incompleto = bool(mancanti)
    if mancanti:
        print(f"periodi ancora da scaricare ({len(mancanti)}): il prossimo giro riparte da qui")
        open(".storico_incompleto", "w").write(" ".join(mancanti))
    # 1b-bis) SECONDA FONTE PER GLI USA (19/11/2026): i libri delle pagine Public Domain Day della Duke (storico/duke.py)
    try:
        duke.integra(tutte, duke.carica(R.anno_libero_usa(ANNO_A)))
    except Exception as e:      # se la Duke non risponde lo Storico si fa lo stesso
        print("Duke non letta:", e)
    # 1c) CONTROLLO SUGLI AUTORI (18/11/2026): tutti gli anni di morte e la cittadinanza, per gli autori morti dal 1900.
    #     Più anni di morte: vale il più tardo e l'autore è segnato «morte_incerta»; cittadinanza di un paese alleato
    #     (Trattato di pace con l'Italia, 1947): segnato «alleato», perché in Italia la protezione può durare di più.
    #     Un'opera che con l'anno di morte più tardo non è più libera da nessuna parte esce dallo Storico.
    da_controllare = sorted({a["qid"] for o in tutte.values() for a in o["autori"]
                             if (a.get("morte") or 0) >= 1900 and re.fullmatch(r"Q\d+", a["qid"] or "")})
    info = info_autori(da_controllare, fine_budget + 15 * 60)
    for o in tutte.values():
        for a in o["autori"]:
            x = info.get(a["qid"])
            if not x:
                continue
            if x["morti"]:
                a["morte"] = max(x["morti"])
            a["morte_incerta"] = 1 if len(set(x["morti"])) > 1 else 0
            a["alleato"] = x["alleato"]
    # 1d) REGISTRO UNICO (20/11/2026): l'anno di morte è quello deciso in data/registro/autori.json (due fonti
    #     autorevoli contro Wikidata vincono). Vedi storico/applica_registro.py.
    for o in tutte.values():
        for a in o["autori"]:
            applica_registro.applica(a)
    prima_controllo = len(tutte)
    from registro import consultazione   # enciclopedie, riviste e giornali: fuori (Marco, 21/11/2026)
    via = set(consultazione())
    tutte = {k: o for k, o in tutte.items() if libera(o) and k not in via}
    print(f"controllo autori: {len(info)} letti su {len(da_controllare)}; opere uscite perché non più libere: {prima_controllo - len(tutte)}")
    ops = sorted(tutte.values(), key=lambda o: (-o["pagine"], o["qid"]))
    if len(ops) < SOGLIA:
        print("ancora poche opere (%d): salvo i periodi scaricati, non scrivo la pagina" % len(ops)); return

    # 2) lingua e genere solo per le opere che vanno nelle playlist (cache in dettagli.json)
    f_det = f"{USCITA}/dettagli.json"
    try:
        det = json.load(open(f_det, encoding="utf8"))
    except Exception:
        det = {}
    da_chiedere = [o["qid"] for o in ops[:MAX_VISITE] if o["qid"] not in det and re.fullmatch(r"Q\d+", o["qid"])]
    if da_chiedere:
        try:
            for k, v in lingua_genere_qid(da_chiedere).items():
                det[k] = v
            json.dump(det, open(f_det, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
        except Exception as e:
            print("lingua/genere non aggiornati:", e)
    for o in ops[:MAX_VISITE]:
        x = det.get(o["qid"], {})
        if x.get("lingua"): o["lingua"] = x["lingua"]
        o["generi"] = x.get("generi", [])

    # PLAYLIST: visite solo per le più note
    misurate, esaurito = ops[:MAX_VISITE], False
    try:
        wiki = pagine_wiki(o["qid"] for o in misurate)
    except Exception as e:
        print("pagine Wikipedia non lette:", e); wiki = {}
    for o in misurate:
        w = wiki.get(o["qid"], {})
        w.setdefault("en", o.get("wiki_en")); w.setdefault("it", o.get("wiki_it"))
        o["_wiki"] = w
    from concurrent.futures import ThreadPoolExecutor
    inizio_vis = time.time()

    def misura(o):
        return {l: visite_settimana(l, o["_wiki"].get(l), ini, fine) for l in LINGUE_VISITE}
    with ThreadPoolExecutor(max_workers=6) as pool:   # sei pagine alla volta: l'API di Wikimedia lo regge
        for i in range(0, len(misurate), 60):
            blocco = misurate[i:i + 60]
            if not esaurito and time.time() - inizio_vis > BUDGET_VISITE * 60:
                esaurito = True
            if not esaurito:
                try:
                    for o, v in zip(blocco, pool.map(misura, blocco)):
                        for l in LINGUE_VISITE:
                            o["visite_" + l] = v[l]
                except Exception as e:           # qualunque guaio: si smette di misurare, ma si salva quello che c'è
                    print("misura interrotta:", e); esaurito = True
            if esaurito:
                for o in blocco:
                    vecchio = precedenti.get(o["qid"], {})
                    for l in LINGUE_VISITE:
                        o["visite_" + l] = vecchio.get("visite_" + l)
    for o in misurate:
        o.pop("_wiki", None)
        o["visite_sett"] = sum(o.get("visite_" + l) or 0 for l in LINGUE_VISITE)
    misurate.sort(key=lambda o: (-o["visite_sett"], -o["pagine"]))

    meta = {"aggiornato": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "settimana": [ini.isoformat(), fine.isoformat()], "interrotto_per_tempo": esaurito, "periodi_mancanti": mancanti,
            "regola": f"USA: opere pubblicate fino al {ANNO_A} (95 anni compiuti), compreso tutto ciò che è più antico",
            "fonte": "Wikidata (CC0), Wikipedia (visite)",
            "copertura": f"ricerca: le opere con anno su Wikidata e una pagina Wikipedia, più tutte le opere scritte degli scrittori morti "
                         f"entro il {R.morti_liberi_nel(date.today().year, 'it')} e degli autori delle opere più note, se libere in almeno un paese; "
                         f"playlist e visite: le {MAX_VISITE} più note"}
    json.dump({**meta, "opere": [{k: v for k, v in o.items() if k not in ("wiki_en", "wiki_it")} for o in misurate]},
              open(f"{USCITA}/opere.json", "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    json.dump({**meta, **costruisci_playlist(misurate)}, open(f"{USCITA}/playlist.json", "w", encoding="utf8"),
              ensure_ascii=False, separators=(",", ":"))
    n_aut, n_file, peso = scrivi_ricerca(ops)
    print(f"ricerca: {len(ops)} opere, {n_aut} autori, {n_file} file, {peso/1e6:.1f} MB in tutto "
          f"(la pagina ne scarica uno alla volta); visite aggiornate: {not esaurito}")


if __name__ == "__main__":
    main()
