"""REGISTRO UNICO, parte 1: gli autori (schema approvato da Marco il 20/11/2026, docs/registro-prove.md).
Scrive data/registro/autori.json: per ogni autore l'anno di morte DECISO, con le fonti e l'esito. Da qui leggono tutte
le parti del sito (liste, Storico, schede, Già pubblici, calendario), che non decidono più niente da sole.

Quali autori: quelli delle liste (data/AAAA.json, data/es-AAAA.json), quelli dello Storico morti tra il 1930 e l'anno
in cui scade la regola europea (oggi 1955) e le persone degli anniversari di morte del calendario (data/anniversari-AAAA.json). Per chi è morto prima del 1930 un anno sbagliato non cambia niente: le opere
sono libere comunque da decenni.

Fonti, per ogni autore:
- Wikidata: tutti gli anni di morte (P570), i codici della Biblioteca nazionale tedesca (P227) e della Library of
  Congress (P244), le fonti che Wikidata cita per l'anno di morte (P248);
- GND (lobid.org) e Library of Congress (id.loc.gov): l'anno di morte nei loro cataloghi. Cache condivisa con
  scripts/verifica.py in data/cache_verifica.json (rifatta dopo 180 giorni).
Decisione: scripts/regole.py, decidi_morte() (regola delle due fonti autorevoli). Le verifiche a mano di
data/verifiche_manuali.json vincono su tutto.

Se il tempo finisce o una fonte non risponde, gli autori non ancora letti restano con il dato di prima e il file lo dice
("in_attesa"): niente si perde, il giro dopo riparte da lì."""
import glob, json, os, re, sys, time
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verifica as V                       # noqa: E402  (lettura delle fonti: stesse funzioni di verifica.py)
from regole import decidi_morte, morti_liberi_nel   # noqa: E402

R = Path(__file__).resolve().parent.parent
USCITA = R / "data" / "registro" / "autori.json"
ANNO_UE = morti_liberi_nel(date.today().year, "it")
DA = 1930
BUDGET = float(os.environ.get("BUDGET_MINUTI", "40"))


def autori_da_fare():
    nomi = {}
    for f in sorted(glob.glob(str(R / "data" / "[0-9][0-9][0-9][0-9].json")) + glob.glob(str(R / "data" / "es-[0-9][0-9][0-9][0-9].json"))):
        for a in json.load(open(f, encoding="utf-8")).get("autori", []):
            if a.get("letterario") and re.fullmatch(r"Q\d+", a.get("wikidata") or ""):
                nomi[a["wikidata"]] = a["nome"]
    for f in glob.glob(str(R / "data" / "storico" / "ricerca" / "*.json")):
        for r in json.load(open(f, encoding="utf-8"))["opere"]:
            for a in r[5]:
                if a[2] is not None and DA <= a[2] <= ANNO_UE and re.fullmatch(r"Q\d+", a[0] or ""):
                    nomi.setdefault(a[0], a[1])
    # le persone del calendario degli anniversari (morte): il calendario è curato a mano, ma le date vengono da qui
    for f in glob.glob(str(R / "data" / "anniversari-[0-9][0-9][0-9][0-9].json")):
        for v in json.load(open(f, encoding="utf-8")).get("voci", []):
            if v.get("tipo") == "morte" and re.fullmatch(r"Q\d+", v.get("qid") or ""):
                nomi.setdefault(v["qid"], v.get("nome"))
    return nomi


def codici(qids):
    out, ok = {}, True
    for i in range(0, len(qids), 150):
        v = " ".join("wd:" + q for q in qids[i:i + 150])
        try:
            r = V.sparql(f"SELECT ?a ?gnd ?loc WHERE {{ VALUES ?a {{ {v} }} OPTIONAL {{ ?a wdt:P227 ?gnd }} OPTIONAL {{ ?a wdt:P244 ?loc }} }}")
        except Exception as e:
            print("codici non letti:", e); ok = False; continue
        for x in r:
            q = V.val(x, "a").rsplit("/", 1)[-1]
            c = out.setdefault(q, {})
            if V.val(x, "gnd"): c.setdefault("gnd", V.val(x, "gnd"))
            if V.val(x, "loc"): c.setdefault("loc", V.val(x, "loc"))
        time.sleep(1)
    return out, ok


def a_pezzi(funzione, qids, passo):
    """Chiama funzione su pezzi di qids; se un pezzo non risponde lo segna e va avanti."""
    out, ok = {}, True
    for i in range(0, len(qids), passo):
        try:
            out.update(funzione(qids[i:i + passo]))
        except Exception as e:
            print("pezzo non letto:", str(e)[:80]); ok = False
    return out, ok


def aggiungi_fonti(fv, aggiunte):
    """Fonti trovate a mano (data/verifiche_manuali.json, «fonti_aggiunte», 23/11/2026): entrano nel confronto accanto a
    Wikidata, GND e LoC, ma non decidono da sole. Un anno diverso rende l'esito «discorde» (scheda «da verificare»)."""
    for x in aggiunte or []:
        if isinstance(x.get("morte"), int):
            fv[x.get("chiave") or "a_mano"] = x["morte"]
    return fv


def main():
    inizio = time.time()
    oggi = date.today()
    try:
        vecchio = json.load(open(USCITA, encoding="utf-8")).get("autori", {})
    except Exception:
        vecchio = {}
    nomi = autori_da_fare()
    qids = sorted(nomi)
    print("autori nel registro:", len(qids), flush=True)
    cod, ok_cod = codici(qids)
    cit, ok_cit = a_pezzi(V.citazioni, qids, 500)
    anni, ok_anni = a_pezzi(V.anni_wikidata, qids, 500)
    print(f"codici: {sum(1 for c in cod.values() if c)} autori con GND o LoC | citazioni: {len(cit)} | anni Wikidata: {len(anni)}", flush=True)

    try:
        cache = json.load(open(V.CACHE, encoding="utf-8"))
    except Exception:
        cache = {"gnd": {}, "loc": {}}
    cache.setdefault("gnd", {}); cache.setdefault("loc", {})
    fonti = {"gnd": V.morte_gnd, "loc": V.morte_loc}
    letti, esaurito = 0, False
    for q in qids:
        for nf, leggi in fonti.items():
            c = (cod.get(q) or {}).get(nf)
            if not c:
                continue
            v = cache[nf].get(c)
            if v and (oggi - date.fromisoformat(v["controllato"])).days < V.RINFRESCA:
                continue
            if time.time() - inizio > BUDGET * 60:
                esaurito = True
                continue
            try:
                cache[nf][c] = {"morte": leggi(c), "controllato": oggi.isoformat()}
                letti += 1
            except Exception as e:
                print(nf, c, "non letto:", e)
            time.sleep(0.2)
        if letti and letti % 200 == 0:
            json.dump(cache, open(V.CACHE, "w", encoding="utf-8"), separators=(",", ":"))
    json.dump(cache, open(V.CACHE, "w", encoding="utf-8"), separators=(",", ":"))
    print("letture nuove dalle biblioteche:", letti, "| tempo finito:" if esaurito else "", flush=True)

    try:
        vm = json.load(open(R / "data" / "verifiche_manuali.json", encoding="utf-8"))
        manuali, aggiunte = vm["autori"], vm.get("fonti_aggiunte", {})
    except Exception:
        manuali, aggiunte = {}, {}
    out, attesa = {}, 0
    for q in qids:
        wd_anni = sorted(anni.get(q, set()))
        if not wd_anni and q in vecchio:          # Wikidata non ha risposto per questo pezzo: resta il dato di prima
            out[q] = vecchio[q]; continue
        if not wd_anni:
            continue
        # anno principale di Wikidata: quello già usato dal sito (il più tardo, per prudenza, come nello Storico)
        wd = max(wd_anni)
        fv = {"wikidata": wd}
        altra = next(iter(sorted(set(wd_anni) - {wd})), None)
        if altra:
            fv["wikidata_altra"] = altra
        manca = False
        for nf in fonti:
            c = (cod.get(q) or {}).get(nf)
            if not c:
                continue
            v = cache[nf].get(c)
            if v is None:
                manca = True
            elif v.get("morte"):
                fv[nf] = v["morte"]
        aggiungi_fonti(fv, aggiunte.get(q))
        citate = cit.get(q, {})
        m = manuali.get(q)
        if m:
            voce = {"n": nomi[q], "m": m["morte"], "e": "nazionale", "f": fv, "manuale": {"fonte": m["fonte"], "url": m["url"]}}
        else:
            esito, deciso, autorevoli = decidi_morte(fv, citate)
            voce = {"n": nomi[q], "m": deciso, "e": esito, "f": fv}
            if autorevoli:
                voce["a"] = autorevoli
        if citate:
            voce["c"] = citate
        if manca:
            voce["in_attesa"] = True          # una biblioteca non ancora letta: l'esito può cambiare al giro dopo
            attesa += 1
        voce["d"] = oggi.isoformat()
        out[q] = voce
    from collections import Counter
    conta = Counter(v["e"] for v in out.values())
    cambiati = [q for q, v in out.items() if v["m"] != v["f"]["wikidata"]]
    incompleto = esaurito or not (ok_cod and ok_cit and ok_anni) or attesa > 0
    USCITA.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"aggiornato": oggi.isoformat(),
               "regola": "anno di morte deciso con scripts/regole.py, decidi_morte(): due fonti autorevoli contro Wikidata vincono; "
                         "verifiche a mano (data/verifiche_manuali.json) sopra a tutto",
               "chiavi": {"n": "nome", "m": "anno di morte deciso", "e": "esito", "f": "anni per fonte letta", "c": "fonti citate da Wikidata",
                          "a": "fonti autorevoli d'accordo", "d": "giorno del controllo", "in_attesa": "una biblioteca non ancora letta"},
               "incompleto": incompleto, "in_attesa": attesa, "esiti": dict(conta), "autori": out},
              open(USCITA, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("esiti:", dict(conta), "| anno diverso da Wikidata:", len(cambiati), "| in attesa di una biblioteca:", attesa,
          "| incompleto:" if incompleto else "")
    for q in cambiati[:40]:
        v = out[q]
        print(f"  CORRETTO {v['n']}: Wikidata {v['f']['wikidata']} -> {v['m']} ({', '.join(v.get('a', [])) or v['e']})")


if __name__ == "__main__":
    main()
