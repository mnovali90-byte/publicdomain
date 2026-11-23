"""Lo Storico usa gli anni di morte del REGISTRO UNICO (data/registro/autori.json, scripts/registro_autori.py),
non più quelli presi da Wikidata da solo (20/11/2026). La regola sta in scripts/regole.py, morte_dal_registro().

Due usi:
- storico/storico.py chiama applica() su ogni autore prima di scrivere i file;
- lanciato da solo (passo di .github/workflows/gia-pubblici.yml), riscrive i file già pronti dello Storico
  (opere.json, ricerca/, per_autore/) senza rifare tutto il giro mensile.
«morte_incerta» diventa 2 quando le fonti discordano proprio sul confine europeo: la pagina mostra «da verificare»."""
import glob, json, os, sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regole import morte_dal_registro, morti_liberi_nel  # noqa: E402

CARTELLA = "data/storico"
ANNO_UE = morti_liberi_nel(date.today().year, "it")
_REG = None


def registro():
    global _REG
    if _REG is None:
        try:
            _REG = json.load(open("data/registro/autori.json", encoding="utf8")).get("autori", {})
        except Exception:
            _REG = {}
    return _REG


def applica(a):
    """a: autore come dizionario dello Storico ({"qid", "morte", "morte_incerta", ...}). Cambia a sul posto."""
    m, inc = morte_dal_registro(a.get("qid"), a.get("morte"), registro(), ANNO_UE)
    if inc is None:
        return False
    cambiato = m != a.get("morte") or (inc == 2) != (a.get("morte_incerta") == 2)
    a["morte"] = m
    a["morte_incerta"] = 2 if inc == 2 else max(a.get("morte_incerta") or 0, inc)
    return cambiato


_DECISE = None


def decise():
    """Il registro delle opere (scripts/registro.py, opere_decise): anni decisi con le fonti (23/11/2026)."""
    global _DECISE
    if _DECISE is None:
        from registro import opere_decise
        _DECISE = opere_decise()
    return _DECISE


def anno_opera(q, y):
    """L'anno di uscita dell'opera nei file dello Storico: quello deciso nel registro, se c'è (regole.anno_deciso)."""
    from regole import anno_deciso
    return anno_deciso(q, y, decise())


def _riga(r, i_morte, i_inc):
    """Riga di un file (autore come lista). Restituisce True se cambiata."""
    m, inc = morte_dal_registro(r[0], r[i_morte], registro(), ANNO_UE)
    if inc is None:
        return False
    nuovo_inc = 2 if inc == 2 else max(r[i_inc] or 0, inc)
    if r[i_morte] == m and r[i_inc] == nuovo_inc:
        return False
    r[i_morte], r[i_inc] = m, nuovo_inc
    return True


def togli_consultazione():
    """Enciclopedie, riviste e giornali fuori da Già pubblici (deciso da Marco il 21/11/2026; elenco da
    storico/coautori.py, classi in CONSULTAZIONE). Tolte dai file dello Storico: ricerca, opere, pagine per autore."""
    from registro import consultazione
    via = set(consultazione())
    if not via:
        return 0
    tolte = 0
    f = f"{CARTELLA}/opere.json"
    d = json.load(open(f, encoding="utf8"))
    prima = len(d["opere"])
    d["opere"] = [o for o in d["opere"] if o.get("qid") not in via]
    tolte += prima - len(d["opere"])
    json.dump(d, open(f, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    for f in sorted(glob.glob(f"{CARTELLA}/ricerca/*.json")):
        d = json.load(open(f, encoding="utf8"))
        prima = len(d["opere"])
        d["opere"] = [r for r in d["opere"] if r[0] not in via]
        if len(d["opere"]) != prima:
            tolte += prima - len(d["opere"])
            json.dump(d, open(f, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    for f in sorted(glob.glob(f"{CARTELLA}/per_autore/*.json")):
        d = json.load(open(f, encoding="utf8"))
        c = 0
        for k in d:
            n = len(d[k])
            d[k] = [r for r in d[k] if r[0] not in via]
            c += n - len(d[k])
        if c:
            json.dump(d, open(f, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    return tolte


def riordina_ricerca():
    """Riscrive i file della ricerca (data/storico/ricerca/) con la regola di storico/chiavi.py (21/11/2026):
    1. ogni opera va sotto ogni parola che conta del titolo, non solo sotto la prima («Pinocchio» trova
       «Le avventure di Pinocchio»);
    2. i libri della Duke rimasti senza codice Wikidata hanno un autore fittizio («duke-a-virginia-woolf»):
       se il nome è identico a quello di un solo autore vero dell'archivio, il libro passa a quell'autore
       (prima Virginia Woolf e Marcel Proust comparivano due volte). Se i nomi uguali sono più d'uno, non si tocca.
    Restituisce (opere, autori uniti, file)."""
    from chiavi import chiavi_ricerca
    try:   # nomi italiani degli autori (storico/nomi_it.py): la ricerca trova anche «Tolstoj» ed «Esopo»
        nomi_it = json.load(open(f"{CARTELLA}/nomi_it.json", encoding="utf8"))
    except Exception:
        nomi_it = {}
    opere, autori = {}, {}
    for f in sorted(glob.glob(f"{CARTELLA}/ricerca/*.json")):
        d = json.load(open(f, encoding="utf8"))
        for r in d["opere"]:
            opere.setdefault(r[0], r)
        for r in d["autori"]:
            autori.setdefault(r[0], r)
    if len(opere) < 1000:
        return len(opere), 0, 0
    veri = {}
    for q, r in autori.items():
        if q.startswith("Q"):
            veri.setdefault(r[1].strip().lower(), []).append(r)
    unisci = {}
    for q, r in autori.items():
        if q.startswith("duke-a-"):
            c = veri.get(r[1].strip().lower(), [])
            if len(c) == 1:
                unisci[q] = c[0]
    for r in opere.values():
        for i, a in enumerate(r[5]):
            v = unisci.get(a[0])
            if v:   # autore dell'opera: [qid, nome, morte, antico, morte_incerta, alleato]
                r[5][i] = [v[0], v[1], v[2], v[4], v[5], v[6]]
    for q, v in unisci.items():
        v[3] += autori[q][3]
        del autori[q]
    lettere = {}
    for r in opere.values():
        for k in chiavi_ricerca(r[1]) | chiavi_ricerca(r[2] or ""):
            lettere.setdefault(k, {"opere": [], "autori": []})["opere"].append(r)
    for r in autori.values():
        it = nomi_it.get(r[0])
        del r[7:]
        if it:   # riga autore: [qid, nome, morte, n_opere, antico, morte_incerta, alleato, nome italiano]
            r.extend([None] * (7 - len(r)) + [it])
        for k in chiavi_ricerca(r[1], autore=True) | (chiavi_ricerca(it, autore=True) if it else set()):
            lettere.setdefault(k, {"opere": [], "autori": []})["autori"].append(r)
    for f in glob.glob(f"{CARTELLA}/ricerca/*.json"):
        os.remove(f)
    for k, d in lettere.items():
        d["opere"].sort(key=lambda r: -(r[4] or 0))
        d["autori"].sort(key=lambda r: -r[3])
        json.dump(d, open(f"{CARTELLA}/ricerca/{k}.json", "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    return len(opere), len(unisci), len(lettere)


def main():
    if not registro():
        print("registro non trovato: lo Storico resta com'è"); return
    print("enciclopedie, riviste e giornali tolti dallo Storico:", togli_consultazione())
    cambi = 0
    f = f"{CARTELLA}/opere.json"
    d = json.load(open(f, encoding="utf8"))
    anni = 0
    for o in d["opere"]:
        for a in o.get("autori", []):
            cambi += applica(a)
        y = anno_opera(o["qid"], o.get("anno"))
        if y != o.get("anno"):
            o["anno"], anni = y, anni + 1
    json.dump(d, open(f, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    for f in sorted(glob.glob(f"{CARTELLA}/ricerca/*.json")):
        d = json.load(open(f, encoding="utf8"))
        c = sum(_riga(a, 2, 4) for r in d["opere"] for a in r[5]) + sum(_riga(r, 2, 5) for r in d["autori"])
        for r in d["opere"]:
            y = anno_opera(r[0], r[3])
            if y != r[3]:
                r[3], c, anni = y, c + 1, anni + 1
        if c:
            json.dump(d, open(f, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
            cambi += c
    for f in sorted(glob.glob(f"{CARTELLA}/per_autore/*.json")):
        d = json.load(open(f, encoding="utf8"))
        c = sum(_riga(a, 2, 4) for righe in d.values() for r in righe for a in r[5])
        for righe in d.values():
            for r in righe:
                y = anno_opera(r[0], r[3])
                if y != r[3]:
                    r[3], c, anni = y, c + 1, anni + 1
        if c:
            json.dump(d, open(f, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
            cambi += c
    print("Storico allineato al registro: voci cambiate", cambi, "| anni di uscita dal registro delle opere:", anni)
    n, u, k = riordina_ricerca()
    print(f"ricerca riordinata: {n} opere, {u} autori della Duke uniti al loro autore vero, {k} file")


if __name__ == "__main__":
    main()
