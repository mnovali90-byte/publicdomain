"""REGISTRO UNICO, parte 2: le opere (20/11/2026). Scrive data/registro/opere.json.

Per ogni opera dello Storico in cui la regola dei coautori cambia qualcosa, il registro scrive gli autori che contano,
già decisi con scripts/regole.py (autori_che_contano). La pagina Già pubblici legge e applica, non decide più:
  "x":  autori che non contano (gruppi o enti senza membri, nati dopo la morte degli altri autori)
  "m":  {autore: anno di morte} per i gruppi con membri (vale la morte più tarda dei membri)
  "sc": coautori senza data di morte accanto ad autori con la data (opera da verificare)
  "an": coautori senza data trattati come antichi (accanto ad autori morti da più di 170 anni)
  "add": coautori aggiunti a mano (data/coautori_manuali.json) [qid, nome, morte, fonte, nome della fonte]
  "mu": compositore e librettista [ruolo, nome, anno di morte] (avviso: il testo resta libero)
e, nella parte "usa", l'anno USA verificato di ogni opera (scripts/registro.py, anni_usa: liste e Storico insieme).
Dati: data/storico/coautori.json (tipi degli autori, da Wikidata) e le righe dell'archivio (data/storico/ricerca)."""
import glob, json, os, sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from regole import autori_che_contano, opera_antica  # noqa: E402
from registro import anni_usa, opere_decise, dati_eta, consultazione  # noqa: E402

Y = date.today().year


def leggi(p, vuoto):
    try:
        return json.load(open(p, encoding="utf8"))
    except Exception:
        return vuoto


def decidi(riga, tipi, manuali, eta=({}, {})):
    """Voce del registro per una riga dell'archivio, o None se la regola non cambia niente."""
    au = [{"qid": a[0], "nome": a[1], "morte": a[2], "antico": bool(a[3])} for a in riga[5]]
    antica = opera_antica(riga[0], au, riga[3], eta[0].get(riga[0]), eta[1], Y)
    add = []
    via = [x["sostituisce"] for x in manuali.get(riga[0], []) if x.get("sostituisce")]   # autore sbagliato, tolto a mano
    au = [a for a in au if a["qid"] not in via]
    for x in manuali.get(riga[0], []):
        # illustratori, compositori e librettisti hanno diritti propri ma non sono autori del testo (23/11/2026)
        if (x.get("ruolo") or "autore") not in ("autore", "opera originale"):
            continue
        if not any(a["qid"] == x.get("qid") for a in au):
            q = x.get("qid") or "man:" + x["nome"]
            au.append({"qid": q, "nome": x["nome"], "morte": x.get("morte"), "antico": False})
            add.append([q, x["nome"], x.get("morte"), x.get("fonte"), x.get("fonte_nome")])
    fuori = autori_che_contano(au, tipi, Y)
    tenuti = {a["qid"] for a in fuori}
    voce = {}
    x = via + [a["qid"] for a in au if a["qid"] not in tenuti]
    if x:
        voce["x"] = x
    m = {a["qid"]: a["morte"] for a in fuori if a.get("gruppo")}
    if m:
        voce["m"] = m
    sc = [a["qid"] for a in fuori if a.get("senza_data")]
    if sc:
        voce["sc"] = sc
    an = [a["qid"] for a in fuori if a.get("antico") and not next(b for b in au if b["qid"] == a["qid"])["antico"]]
    if an:
        voce["an"] = an
    if add:
        voce["add"] = add
    if antica:
        voce["antica"] = antica   # libera dappertutto per età (scripts/regole.py, opera_antica)
    return voce or None


def main():
    co = leggi("data/storico/coautori.json", {})
    tipi = co.get("autori", {})
    manuali = leggi("data/coautori_manuali.json", {}).get("opere", {})
    musica = co.get("musica", {})
    arch = {}
    for f in sorted(glob.glob("data/storico/ricerca/*.json")):
        for r in json.load(open(f, encoding="utf8"))["opere"]:
            arch.setdefault(r[0], r)
    opere = {}
    eta = dati_eta()
    for q, r in arch.items():
        v = decidi(r, tipi, manuali, eta)
        if musica.get(q):
            v = v or {}
            v["mu"] = musica[q]
        # musica e disegni scritti a mano con la loro fonte (data/coautori_manuali.json): stessa nota delle schede (23/11/2026)
        extra = [[x["ruolo"], x["nome"], x.get("morte")] for x in manuali.get(q, [])
                 if x.get("ruolo") in ("compositore", "librettista", "illustratore")]
        if extra:
            v = v or {}
            v["mu"] = list(v.get("mu", [])) + [e for e in extra if e not in v.get("mu", [])]
        if v:
            opere[q] = v
    os.makedirs("data/registro", exist_ok=True)
    json.dump({"aggiornato": date.today().isoformat(),
               "regola": "coautori decisi con scripts/regole.py, autori_che_contano(); vedi l'inizio di storico/registro_opere.py",
               "coautori": opere,
               "via": consultazione(),
               "usa": anni_usa(),
               # 23/11/2026: REGISTRO DELLE OPERE, un posto solo per anno deciso, fonti e note (scripts/registro.py, opere_decise)
               "opere": opere_decise()}, open("data/registro/opere.json", "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    from collections import Counter
    c = Counter(k for v in opere.values() for k in v)
    print("registro delle opere:", len(opere), "opere con una decisione sui coautori o con musica |", dict(c))


if __name__ == "__main__":
    main()
