"""Le liste per anno (data/AAAA.json, data/es-AAAA.json) con l'anno di morte DECISO nel registro unico (22/11/2026).

Perché: le liste nascono da Wikidata (scripts/aggiorna.py), cioè da una fonte sola. Il registro unico
(data/registro/autori.json, scripts/registro_autori.py) decide l'anno di morte incrociando le fonti, e tutte le parti del
sito devono usare quello: radar, pagine dell'anno, schede, home, calendario leggono le liste, quindi la correzione si fa
qui, sui file, una volta sola.

Cosa fa, per ogni autore di ogni lista: se il registro decide un altro anno (regole.morte_dal_registro), l'autore passa
nella lista di quell'anno, ma solo se le fonti hanno deciso davvero (non «discorde») (con l'anno di morte del registro e l'anno di Wikidata in «morte_wikidata»); se la lista di
quell'anno non c'è (anni già liberi o non ancora creati), esce dalle liste. Ogni spostamento è scritto in
data/registro/liste_spostati.json. Si può rifare quante volte si vuole: dà sempre lo stesso risultato.
Gira dopo scripts/aggiorna.py e dopo scripts/registro_autori.py (giri aggiorna.yml e registro.yml)."""
import glob, json, re, sys
from datetime import date
from pathlib import Path

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "scripts"))
import regole as RG  # noqa: E402

DATA = R / "data"


def _l(p, d=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return d


def anno_di(x):
    m = re.match(r"-?\d+", str(x or ""))
    return int(m.group()) if m else None


def main():
    reg = (json.loads((DATA / "registro" / "autori.json").read_text(encoding="utf-8")) or {}).get("autori", {})
    anno_ue = RG.morti_liberi_nel(date.today().year, "it")
    file = sorted(glob.glob(str(DATA / "[0-9][0-9][0-9][0-9].json")) + glob.glob(str(DATA / "es-[0-9][0-9][0-9][0-9].json")))
    liste = {Path(f).stem: json.loads(Path(f).read_text(encoding="utf-8")) for f in file}
    spostati, arrivi = [], {}
    for nome, d in liste.items():
        tipo = "es" if nome.startswith("es-") else "it"
        anno_l = int(nome[-4:])
        tenuti = []
        for a in d.get("autori", []):
            m_l = anno_di(a.get("morte"))
            m, inc = RG.morte_dal_registro(a.get("wikidata"), m_l, reg, anno_ue)
            # fonti in disaccordo («discorde»): il registro non ha deciso, l'autore resta dov'è (la scheda dice «da verificare»)
            # finché la verifica (docs/verifica-opere.md) non mette l'anno giusto in data/verifiche_manuali.json
            if inc or m is None or m_l is None or m == m_l or RG.anno_libero(m, tipo) == anno_l:
                tenuti.append(a)
                continue
            # le liste dove l'autore deve stare con l'anno del registro: quella europea e quella spagnola di quell'anno
            dest = [x for x in (str(RG.anno_libero(m, "it")), "es-" + str(RG.anno_libero(m, "es"))) if x in liste]
            b = dict(a, morte=str(m), morte_wikidata=a.get("morte_wikidata") or a.get("morte"), morte_registro=True)
            spostati.append({"autore": a.get("nome"), "wikidata": a.get("wikidata"), "da": nome, "a": dest or None,
                             "morte_wikidata": m_l, "morte_registro": m, "fonti_discordi": bool(inc)})
            for x in dest:
                arrivi.setdefault(x, []).append(b)
        d["autori"] = tenuti
    for dest, nuovi in arrivi.items():
        q_gia = {a.get("wikidata") for a in liste[dest].get("autori", [])}
        liste[dest]["autori"] += [b for b in nuovi if b.get("wikidata") not in q_gia]
    for nome, d in liste.items():
        d["totale"] = len(d.get("autori", []))
        nuovo = json.dumps(d, ensure_ascii=False, indent=1)
        p = DATA / f"{nome}.json"
        if p.read_text(encoding="utf-8") != nuovo:
            p.write_text(nuovo, encoding="utf-8")
    # USA (23/11/2026, Marco: «per ognuno si decide con due fonti se è già libero, e se lo è si toglie dalla lista»):
    # un'opera della lista USA che due fonti indipendenti danno uscita PRIMA dell'anno della lista è già libera: esce
    # dalla lista. Fonti: le verifiche delle liste (data/us-anni-verificati.json, quarto campo: anno per fonte) e le
    # conferme scritte a mano con le loro fonti (data/verifiche_opere.json, «usa_prima»).
    ver = _l(DATA / "us-anni-verificati.json", {})
    man = (_l(DATA / "verifiche_opere.json", {}) or {}).get("usa_lista", {})
    usa_tolte = []
    for f in sorted(glob.glob(str(DATA / "us-[0-9][0-9][0-9][0-9].json"))):
        lista = Path(f).stem[3:]
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        pub = d.get("anno_pubblicazione")
        tenute = []
        for o in d.get("opere", []):
            v = (ver.get(lista) or {}).get(o.get("qid")) or []
            per_fonte = v[5] if len(v) > 5 and isinstance(v[5], dict) else {}
            prima = sorted({f_ for f_, y in per_fonte.items() if isinstance(y, int) and pub and y < pub})
            m = man.get(o.get("qid"))
            if m and m.get("esito") == "resta":
                # resta nella lista (non è libera per intero). Anno, fonti e nota NON si scrivono qui: stanno nel
                # registro delle opere (scripts/registro.py, opere_decise) e le pagine li leggono da lì (23/11/2026)
                o = {k: v for k, v in o.items() if k not in ("nota_usa", "conferma_usa")}
                tenute.append(o)
                continue
            if m and m.get("esito") == "tolta" and isinstance(m.get("prima"), int) and m["prima"] < pub:
                prima = ["a mano: " + "; ".join(f["nome"] if isinstance(f, dict) else f for f in m.get("fonti", []))]
                prima_anno = m["prima"]
            else:
                prima_anno = min((per_fonte[f_] for f_ in prima), default=None)
            if (m and m.get("esito") == "tolta") or len(prima) >= 2:
                usa_tolte.append({"lista": f"us-{lista}", "qid": o.get("qid"), "titolo": o.get("titolo_it") or o.get("titolo"),
                                  "uscita": prima_anno, "fonti": prima, "nota": (m or {}).get("nota"), "wiki_en": o.get("wiki_en")})
                continue
            tenute.append(o)
        if tenute != d.get("opere", []):
            d["opere"] = tenute
            Path(f).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    # l'elenco degli spostamenti si tiene: al giro dopo gli autori già spostati non risultano più diversi
    fs = DATA / "registro" / "liste_spostati.json"
    try:
        vecchi = json.loads(fs.read_text(encoding="utf-8")).get("spostati", [])
    except Exception:
        vecchi = []
    nuovi_q = {(s["wikidata"], s["da"]) for s in spostati}
    tutti = [s for s in vecchi if (s["wikidata"], s["da"]) not in nuovi_q] + spostati
    try:
        usa_vecchie = json.loads(fs.read_text(encoding="utf-8")).get("usa_gia_libere", [])
    except Exception:
        usa_vecchie = []
    nuove_q = {(x["lista"], x["qid"]) for x in usa_tolte}
    # un'opera che ora resta nella lista (es. decisione «resta» in verifiche_opere.json) non è più fra le tolte
    in_lista = {(Path(f).stem, o.get("qid")) for f in glob.glob(str(DATA / "us-[0-9][0-9][0-9][0-9].json"))
                for o in json.loads(Path(f).read_text(encoding="utf-8")).get("opere", [])}
    usa_tutte = [x for x in usa_vecchie if (x["lista"], x["qid"]) not in nuove_q and (x["lista"], x["qid"]) not in in_lista] + usa_tolte
    fs.write_text(json.dumps({"aggiornato": date.today().isoformat(), "regola": "anno di morte del registro unico (regole.morte_dal_registro)",
                              "spostati": tutti, "usa_gia_libere": usa_tutte}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Liste USA: {len(usa_tolte)} opere già libere tolte (due fonti le danno uscite prima dell'anno della lista)")
    for x in usa_tolte:
        print(f"   {x['lista']}: {x['titolo']} (uscita {x['uscita']}; {', '.join(x['fonti'])})")
    print(f"Liste e registro: {len(spostati)} autori con un anno di morte diverso da Wikidata; "
          f"{sum(1 for s in spostati if s['a'])} spostati in un'altra lista, {sum(1 for s in spostati if not s['a'])} usciti dalle liste")
    for s in spostati:
        print(f"   {s['autore']}: Wikidata {s['morte_wikidata']}, registro {s['morte_registro']} → {', '.join(s['a']) if s['a'] else 'fuori dalle liste'} (da {s['da']})")


if __name__ == "__main__":
    main()
