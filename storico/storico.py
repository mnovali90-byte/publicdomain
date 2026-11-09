"""Dati per la pagina "Storico" di Public Domain Radar: opere già in pubblico dominio negli USA
(tutto ciò che è uscito fino al 1930, cioè 95 anni compiuti), con le playlist più lette della settimana.

Fonti aperte: Wikidata (opere, autori, anno di prima pubblicazione), Wikipedia (visite).

Due insiemi di dati con due scopi diversi, così il lavoro resta leggero:
  RICERCA   TUTTE le opere con anno certo e almeno una pagina Wikipedia, senza visite.
            Spezzata in un file per lettera (data/storico/ricerca/a.json ...): la pagina scarica
            solo la lettera che serve. Contiene anche gli autori (nome, anno di morte).
  PLAYLIST  solo le prime MAX_VISITE opere per fama (numero di lingue con pagina Wikipedia):
            per queste si contano le visite della settimana (Wikipedia en + it).
            Scrive data/storico/opere.json (quelle misurate) e data/storico/playlist.json.

Regola per la lettera di un file: prima lettera (senza accenti) della prima parola e della prima parola
dopo un eventuale articolo (the, il, la, der, les...). Per gli autori: prima e ultima parola del nome.
La pagina deve usare la stessa regola (funzione chiavi_ricerca).

Limite noto: le opere molto antiche spesso non hanno un anno di prima pubblicazione su Wikidata e restano fuori.
Si lancia a mano o dalla GitHub Action .github/workflows/storico.yml (ogni lunedì).
"""
import json, os, re, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from opere import CLASSI, GENERI, get, qid, sparql, val  # noqa: E402

UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
ANNO_A = int(os.environ.get("STORICO_ANNO_A", date.today().year - 96))   # 2026 -> 1930
ANNO_DA = int(os.environ.get("STORICO_ANNO_DA", 1800))
FASCE_ANTICHE = [(-3000, 1400), (1400, 1600), (1600, 1700), (1700, ANNO_DA)]   # prima di ANNO_DA, a fasce
MAX_VISITE = int(os.environ.get("STORICO_MAX_VISITE", 3000))
BUDGET_WIKIDATA = float(os.environ.get("BUDGET_MINUTI_WIKIDATA", 60))   # tempo massimo per scaricare periodi nuovi
BUDGET_VISITE = float(os.environ.get("BUDGET_MINUTI_VISITE", 35))       # tempo massimo per le visite della settimana
RINFRESCA_GIORNI = 30   # un periodo già scaricato si riscarica solo dopo 30 giorni
USCITA = "data/storico"
SOGLIA = 1000   # sotto questo numero di opere qualcosa è andato storto: non si sovrascrive nulla
ARTICOLI = {"the", "a", "an", "il", "lo", "la", "l", "le", "i", "gli", "un", "una", "uno", "der", "die", "das", "den",
            "ein", "eine", "les", "el", "los", "las", "de", "het"}


# ------------------------------------------------------------------ regola di ricerca
def _norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.findall(r"[a-z0-9]+", t)


def _lettera(parola):
    return parola[0] if parola and parola[0].isalpha() else "_"


def chiavi_ricerca(testo, autore=False):
    """Lettere (file) sotto cui va cercato un titolo o un autore."""
    p = _norm(testo)
    if not p:
        return set()
    if autore:
        return {_lettera(p[0]), _lettera(p[-1])}
    ks = {_lettera(p[0])}
    for w in p:
        if w not in ARTICOLI:
            ks.add(_lettera(w)); break
    return ks


# ------------------------------------------------------------------ Wikidata
def opere_periodo(da, a):
    """Opere con anno di prima pubblicazione tra da e a (inclusi), almeno una pagina Wikipedia."""
    classi = " ".join("wd:" + c for c in CLASSI)
    q = f'''SELECT ?w ?wLabel ?wit ?a ?aLabel ?morte ?sl ?en ?itw (YEAR(?d) AS ?anno) WHERE {{
      VALUES ?c {{ {classi} }}
      ?w wdt:P31 ?c; wdt:P577 ?d. FILTER(YEAR(?d)>={da} && YEAR(?d)<={a})
      ?w wikibase:sitelinks ?sl. FILTER(?sl>=1)
      OPTIONAL {{ ?w wdt:P50 ?a. OPTIONAL {{ ?a wdt:P570 ?morte }} }}
      OPTIONAL {{ ?w rdfs:label ?wit FILTER(LANG(?wit)="it") }}
      OPTIONAL {{ ?en schema:about ?w; schema:isPartOf <https://en.wikipedia.org/> }}
      OPTIONAL {{ ?itw schema:about ?w; schema:isPartOf <https://it.wikipedia.org/> }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,it,mul". }} }}'''
    out = {}
    for r in sparql(q):
        k = qid(val(r, "w"))
        o = out.setdefault(k, {"qid": k, "titolo": val(r, "wLabel"), "titolo_it": val(r, "wit"),
                               "anno": int(val(r, "anno") or 0), "autori": {}, "pagine": int(val(r, "sl")),
                               "wiki_en": None, "wiki_it": None})
        if val(r, "a"):
            x = o["autori"].setdefault(qid(val(r, "a")), {"nome": val(r, "aLabel"), "morte": None})
            if val(r, "morte") and not x["morte"]:
                m = re.match(r"-?(\d{4})", val(r, "morte"))
                x["morte"] = int(m.group(1)) if m else None
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
        decenni.setdefault(str(o["anno"] // 10 * 10) if o["anno"] >= 1800 else "prima del 1800", []).append(o)

    def gruppi(d, minimo, n=30):
        r = [{"chiave": k, "n": len(v), "opere": top(v, n)} for k, v in d.items() if len(v) >= minimo]
        return sorted(r, key=lambda g: -g["n"])
    return {"piu_letti": top(ops, 50), "autori": autori[:40],
            "generi": gruppi(generi, 5), "lingue": gruppi(lingue, 5), "decenni": gruppi(decenni, 1, 20)}


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
                [[a["qid"], a["nome"], a["morte"]] for a in o["autori"]]]
        for k in chiavi_ricerca(o["titolo"]) | chiavi_ricerca(o["titolo_it"] or ""):
            lettere.setdefault(k, {"opere": [], "autori": []})["opere"].append(riga)
        for a in o["autori"]:
            x = autori.setdefault(a["qid"], {"qid": a["qid"], "nome": a["nome"], "morte": a["morte"], "n": 0})
            x["n"] += 1
    for a in autori.values():
        for k in chiavi_ricerca(a["nome"], autore=True):
            lettere.setdefault(k, {"opere": [], "autori": []})["autori"].append([a["qid"], a["nome"], a["morte"], a["n"]])
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
        fresco = vecchio and (oggi - date.fromisoformat(vecchio["scaricato"])).days < RINFRESCA_GIORNI
        if not fresco and time.time() - inizio_wd < BUDGET_WIKIDATA * 60:
            lista = []
            for tentativo in range(3):          # Wikidata ogni tanto va in timeout: si riprova
                lista = opere_periodo(da, a)
                if lista:
                    break
                time.sleep(20 * (tentativo + 1))
            print(nome, "opere:", len(lista), flush=True)
            if lista:
                json.dump({"scaricato": oggi.isoformat(), "opere": lista}, open(f, "w", encoding="utf8"),
                          ensure_ascii=False, separators=(",", ":"))
                vecchio = {"opere": lista}
            else:
                saltati.append(nome)
        if vecchio:
            for o in vecchio["opere"]:
                tutte[o["qid"]] = o
        else:
            mancanti.append(nome)
    incompleto = bool(mancanti)
    if saltati:
        print("PERIODI SENZA RISPOSTA da Wikidata:", ", ".join(saltati))
    if mancanti:
        print(f"periodi ancora da scaricare ({len(mancanti)}): il prossimo giro riparte da qui")
        open(".storico_incompleto", "w").write(" ".join(mancanti))
    ops = sorted(tutte.values(), key=lambda o: (-o["pagine"], o["qid"]))
    if len(ops) < SOGLIA:
        print("ancora poche opere (%d): salvo i periodi scaricati, non scrivo la pagina" % len(ops)); return

    # 2) lingua e genere solo per le opere che vanno nelle playlist (cache in dettagli.json)
    f_det = f"{USCITA}/dettagli.json"
    try:
        det = json.load(open(f_det, encoding="utf8"))
    except Exception:
        det = {}
    da_chiedere = [o["qid"] for o in ops[:MAX_VISITE] if o["qid"] not in det]
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
    inizio_vis = time.time()
    for o in misurate:
        if time.time() - inizio_vis > BUDGET_VISITE * 60:
            esaurito = True
        vecchio = precedenti.get(o["qid"], {})
        if not esaurito:
            try:
                o["visite_en"] = visite_settimana("en", o["wiki_en"], ini, fine)
                o["visite_it"] = visite_settimana("it", o["wiki_it"], ini, fine)
                time.sleep(0.05)
            except Exception as e:           # qualunque guaio: si smette di misurare, ma si salva quello che c'è
                print("misura interrotta:", e); esaurito = True
        if esaurito:
            o["visite_en"], o["visite_it"] = vecchio.get("visite_en"), vecchio.get("visite_it")
        o["visite_sett"] = (o["visite_en"] or 0) + (o["visite_it"] or 0)
    misurate.sort(key=lambda o: (-o["visite_sett"], -o["pagine"]))

    meta = {"aggiornato": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "settimana": [ini.isoformat(), fine.isoformat()], "interrotto_per_tempo": esaurito, "periodi_mancanti": mancanti,
            "regola": f"USA: opere pubblicate fino al {ANNO_A} (95 anni compiuti), compreso tutto ciò che è più antico",
            "fonte": "Wikidata (CC0), Wikipedia (visite)",
            "copertura": f"ricerca: tutte le opere con anno di prima pubblicazione su Wikidata e una pagina Wikipedia; "
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
