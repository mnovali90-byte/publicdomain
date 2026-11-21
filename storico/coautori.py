"""Coautori (regola approvata il 20/11/2026, docs/registro-prove.md). Scrive data/storico/coautori.json.

Perché: tra gli «autori» di un'opera Wikidata mette a volte voci che non sono persone (i «Fratelli Grimm» accanto a
Jacob e Wilhelm, pseudonimi collettivi, università, editori) o persone senza data di morte. Prima un'opera così
risultava «non libera» in Europa anche quando tutte le persone vere erano morte da secoli (294 opere, prova del 20/11).

Che cosa raccoglie (solo Wikidata, CC0):
1. autori: per ogni autore senza data di morte dell'archivio dello Storico e delle schede autore, che cos'è
   (persona Q5 oppure no: gruppo, pseudonimo, organizzazione) e, se è un gruppo con i membri segnati (P527),
   l'anno di morte più tardo dei membri. Regole che ne usano le pagine:
     - gruppo/organizzazione senza membri noti: non conta, se ci sono autori persone con la data di morte;
     - gruppo con membri tutti morti: conta l'anno di morte più tardo dei membri (Ilf e Petrov: 1942);
     - gruppo con membri senza data, persona senza data o «valore sconosciuto» accanto ad autori con la data:
       l'opera è «da verificare», con il motivo.
2. musica: compositore (P86) e librettista (P87) delle opere dell'archivio e delle schede. Il testo resta libero;
   la pagina avvisa che la musica o il libretto hanno diritti propri e quando scadono.
3. per_autore: per gli autori delle schede (data/AAAA.json, es-AAAA.json), le loro opere che hanno altri autori (P50)
   o musica, con titolo italiano e inglese, per legarle alle «Opere principali» della scheda.
Nato dopo la morte degli altri autori (anno di nascita P569): non è un coautore, è chi ha curato, letto o presentato
un'edizione (Stephen Fry per «La strada di Puh», Neil Gaiman per Dunsany). Deciso da Marco il 20/11/2026.
Gli illustratori (P110) non si leggono: è libero il testo, non l'edizione (avviso generale del sito).
Se Wikidata non risponde a un pezzo, per quel pezzo resta il dato di prima."""
import glob, json, os, re, sys, time, urllib.parse, urllib.request
from datetime import date

UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
CARTELLA = "data/storico"
USCITA = f"{CARTELLA}/coautori.json"
RUOLI = {"P86": "compositore", "P87": "librettista"}


def sparql(q):
    """Risposta di Wikidata, oppure None se non risponde dopo 5 tentativi (diverso da «nessun risultato»)."""
    for t in range(5):
        try:
            u = "https://query.wikidata.org/sparql"
            dati = urllib.parse.urlencode({"query": q, "format": "json"}).encode()
            r = urllib.request.Request(u, data=dati, headers={**UA, "Content-Type": "application/x-www-form-urlencoded"})
            return json.load(urllib.request.urlopen(r, timeout=120))["results"]["bindings"]
        except Exception as e:
            ATTESE[str(e)[:40]] += 1
            print("  Wikidata non risponde:", str(e)[:80], flush=True)
            time.sleep(15 * (t + 1))
    return None


from collections import Counter
ATTESE = Counter()


def v(x, k):
    return x.get(k, {}).get("value")


def q_(u):
    return u.rsplit("/", 1)[-1] if u else None


def anno(s):
    m = re.match(r"^(-?\d{1,4})-", s or "")
    return int(m.group(1)) if m else None


def archivio():
    arch = {}
    for f in sorted(glob.glob(f"{CARTELLA}/ricerca/*.json")):
        for r in json.load(open(f, encoding="utf8"))["opere"]:
            arch.setdefault(r[0], r)
    return arch


def autori_schede():
    out = set()
    for f in glob.glob("data/[0-9][0-9][0-9][0-9].json") + glob.glob("data/es-[0-9][0-9][0-9][0-9].json"):
        for a in json.load(open(f, encoding="utf8")).get("autori", []):
            if a.get("letterario") and a.get("opere") and re.fullmatch(r"Q\d+", a.get("wikidata") or ""):
                out.add(a["wikidata"])
    return sorted(out)


def per_autore(autori):
    """{autore: {opera: {t, ti, co: {qid: [nome, morte]}, mu: [[ruolo, nome, morte]]}}} oppure None se manca un pezzo."""
    out, ok = {}, True
    for i in range(0, len(autori), 40):
        vals = " ".join("wd:" + a for a in autori[i:i + 40])
        r = sparql(f"""SELECT ?a ?o ?oLabel ?oit ?p ?c ?cLabel ?m ?n WHERE {{ VALUES ?a {{ {vals} }}
          ?o wdt:P50 ?a. VALUES ?p {{ wdt:P50 wdt:P86 wdt:P87 }} ?o ?p ?c. FILTER(?c != ?a)
          OPTIONAL {{ ?c wdt:P570 ?m }} OPTIONAL {{ ?c wdt:P569 ?n }} OPTIONAL {{ ?o rdfs:label ?oit FILTER(LANG(?oit)="it") }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,mul". }} }}""")
        if r is None:
            ok = False
            continue
        for x in r:
            a, o, p, c = q_(v(x, "a")), q_(v(x, "o")), q_(v(x, "p")), v(x, "c")
            w = out.setdefault(a, {}).setdefault(o, {"t": v(x, "oLabel"), "ti": v(x, "oit"), "co": {}, "mu": {}})
            nome = v(x, "cLabel")
            if not nome or re.fullmatch(r"Q\d+", nome):
                nome = None
            cq = q_(c) if c and "wikidata.org/entity/" in c else "?"   # «valore sconosciuto»
            m = anno(v(x, "m"))
            dove = w["co"] if p == "P50" else w["mu"]
            k = cq if p == "P50" else (RUOLI[p], cq)
            vecchio = dove.get(k)
            n = anno(v(x, "n"))
            dove[k] = [nome, max([y for y in (m, vecchio and vecchio[1]) if y is not None], default=None),
                       min([y for y in (n, vecchio and vecchio[2]) if y is not None], default=None)]
        time.sleep(1)
    finale = {}
    for a, opere in out.items():
        for o, w in opere.items():
            finale.setdefault(a, {})[o] = {"t": w["t"], "ti": w["ti"],
                                           "co": [[k, n, m, nasc] for k, (n, m, nasc) in w["co"].items()],
                                           "mu": [[r, n, m] for (r, _), (n, m, _n) in w["mu"].items()]}
    return finale, ok


def tipi(qids):
    """{autore: {"t": "p"|"g", "m": anno di morte più tardo dei membri o None, "nd": membri senza data}} oppure None."""
    out, ok = {}, True
    for i in range(0, len(qids), 150):
        vals = " ".join("wd:" + a for a in qids[i:i + 150])
        r = sparql(f"""SELECT ?a ?t ?mem ?mm ?n WHERE {{ VALUES ?a {{ {vals} }} OPTIONAL {{ ?a wdt:P31 ?t }} OPTIONAL {{ ?a wdt:P569 ?n }}
          OPTIONAL {{ ?a wdt:P527 ?mem. OPTIONAL {{ ?mem wdt:P570 ?mm }} }} }}""")
        if r is None:
            ok = False
            continue
        grezzo = {}
        for x in r:
            a = q_(v(x, "a"))
            g = grezzo.setdefault(a, {"tipi": set(), "membri": {}, "n": None})
            nn = anno(v(x, "n"))
            if nn is not None and (g["n"] is None or nn < g["n"]):
                g["n"] = nn
            if v(x, "t"):
                g["tipi"].add(q_(v(x, "t")))
            if v(x, "mem"):
                mq = q_(v(x, "mem"))
                y = anno(v(x, "mm"))
                prima = g["membri"].get(mq)
                g["membri"][mq] = max([z for z in (y, prima) if z is not None], default=None)
        for a, g in grezzo.items():
            persona = "Q5" in g["tipi"]
            morti = list(g["membri"].values())
            out[a] = {"t": "p" if persona else "g",
                      "m": max(morti) if morti and all(y is not None for y in morti) and not persona else None,
                      "nd": bool(morti) and any(y is None for y in morti) and not persona,
                      "n": g["n"]}   # anno di nascita: chi è nato dopo la morte degli altri autori non è un coautore
        time.sleep(1)
    return out, ok


def musica(qids):
    """{opera: [[ruolo, nome, morte]]} per le opere dell'archivio, oppure None se manca un pezzo."""
    out, ok = {}, True
    for i in range(0, len(qids), 400):
        vals = " ".join("wd:" + o for o in qids[i:i + 400])
        r = sparql(f"""SELECT ?o ?p ?c ?cLabel ?m WHERE {{ VALUES ?o {{ {vals} }} VALUES ?p {{ wdt:P86 wdt:P87 }} ?o ?p ?c.
          OPTIONAL {{ ?c wdt:P570 ?m }} SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,mul". }} }}""")
        if r is None:
            ok = False
            continue
        for x in r:
            o, p = q_(v(x, "o")), q_(v(x, "p"))
            nome = v(x, "cLabel")
            if not nome or re.fullmatch(r"Q\d+", nome) or nome.startswith("http"):
                nome = None
            m = anno(v(x, "m"))
            lista = out.setdefault(o, [])
            gia = next((e for e in lista if e[0] == RUOLI[p] and e[1] == nome), None)
            if gia:
                gia[2] = max([y for y in (gia[2], m) if y is not None], default=None)
            else:
                lista.append([RUOLI[p], nome, m])
        if (i // 400) % 25 == 0:
            print(f"  musica: {i + 400}/{len(qids)} opere", flush=True)
        time.sleep(1)
    return out, ok


# opere di consultazione da togliere da Già pubblici (deciso da Marco il 21/11/2026): enciclopedie (anche i dizionari
# biografici, che su Wikidata ne sono una sottoclasse), riviste anche scientifiche e accademiche, giornali.
# NON la classe larga «opera di consultazione»: comprende anche gli Elementi di Euclide e la Summa Theologiae.
# NON i «periodici» e basta: spesso è narrativa uscita a puntate (Varney il vampiro, Il Federalista).
CONSULTAZIONE = {"Q5292": "enciclopedia", "Q1371849": "dizionario biografico", "Q41298": "rivista", "Q11032": "giornale",
                 "Q5633421": "rivista scientifica", "Q737498": "rivista accademica"}


def consultazione(qids):
    out, ok = {}, True
    vals_c = " ".join("wd:" + c for c in CONSULTAZIONE)
    for i in range(0, len(qids), 300):
        v_ = " ".join("wd:" + q for q in qids[i:i + 300])
        r = sparql(f"SELECT ?o ?c WHERE {{ VALUES ?o {{ {v_} }} VALUES ?c {{ {vals_c} }} ?o wdt:P31/wdt:P279* ?c. }}")
        if r is None:
            ok = False; continue
        for x in r:
            out.setdefault(q_(v(x, "o")), set()).add(CONSULTAZIONE[q_(v(x, "c"))])
        time.sleep(0.5)
    return {q: sorted(t) for q, t in out.items()}, ok


def creazione(qids):
    """Anno di creazione (P571, il più vecchio) delle opere senza autori con la data: per i testi antichi."""
    out, ok = {}, True
    for i in range(0, len(qids), 300):
        v_ = " ".join("wd:" + q for q in qids[i:i + 300])
        r = sparql(f"SELECT ?o (MIN(?c) AS ?creato) WHERE {{ VALUES ?o {{ {v_} }} ?o wdt:P571 ?c. }} GROUP BY ?o")
        if r is None:
            ok = False; continue
        for x in r:
            a = anno(v(x, "creato"))
            if a is not None:
                out[q_(v(x, "o"))] = a
        time.sleep(0.5)
    return out, ok


def main():
    try:
        vecchio = json.load(open(USCITA, encoding="utf8"))
    except Exception:
        vecchio = {}
    arch = archivio()
    print("opere nell'archivio:", len(arch), flush=True)
    schede = autori_schede()
    # una volta al mese basta (20/11/2026): si rilegge solo se il file è di un mese prima, se era incompleto, o se
    # sono cambiati gli autori delle schede o le opere dell'archivio. FORZA=1 per rileggere comunque.
    if (vecchio.get("aggiornato") or "")[:7] == date.today().isoformat()[:7] and not vecchio.get("incompleto") \
            and vecchio.get("schede") == schede and vecchio.get("n_archivio") == len(arch) and not os.environ.get("FORZA"):
        print(f"coautori già letti questo mese ({vecchio['aggiornato']}), stessi autori e stesse opere: non rileggo")
        return
    print("autori delle schede:", len(schede), flush=True)
    pa, ok_pa = per_autore(schede)
    print("schede: opere con coautori o musica:", sum(len(x) for x in pa.values()), "" if ok_pa else "(INCOMPLETO)", flush=True)
    # autori senza data di morte: dall'archivio (non antichi) e coautori delle schede
    senza = {a[0] for r in arch.values() for a in r[5] if a[2] is None and not a[3] and re.fullmatch(r"Q\d+", a[0] or "")}
    senza |= {c[0] for w in pa.values() for o in w.values() for c in o["co"] if c[2] is None and re.fullmatch(r"Q\d+", c[0])}
    ti, ok_ti = tipi(sorted(senza))
    print("autori senza data di morte:", len(senza), "| letti:", len(ti), "| non persone:",
          sum(1 for x in ti.values() if x["t"] == "g"), "" if ok_ti else "(INCOMPLETO)", flush=True)
    tutte_q = sorted(q for q in arch if re.fullmatch(r"Q\d+", q))
    mu, ok_mu = musica(tutte_q)
    cons, ok_cons = consultazione(tutte_q)
    print("enciclopedie, riviste e giornali:", len(cons), "" if ok_cons else "(INCOMPLETO)", flush=True)
    senza = [q for q in tutte_q if all(a[2] is None and not a[3] for a in arch[q][5])]
    cre, ok_cre = creazione(senza)
    print("opere senza autori con data: con anno di creazione", len(cre), "su", len(senza), "" if ok_cre else "(INCOMPLETO)", flush=True)
    print("opere dell'archivio con compositore o librettista:", len(mu), "" if ok_mu else "(INCOMPLETO)", flush=True)
    out = {"aggiornato": date.today().isoformat(),
           "regola": "docs/registro-prove.md, 20/11/2026: gruppi e organizzazioni senza membri noti non contano se ci sono "
                     "autori persone con la data di morte; gruppi con membri: conta la morte più tardiva dei membri; "
                     "coautori senza data di morte: «da verificare»; compositore e librettista: avviso, il testo resta libero",
           "autori": ti if ok_ti else {**vecchio.get("autori", {}), **ti},
           "musica": mu if ok_mu else vecchio.get("musica", {}),
           "consultazione": cons if ok_cons else {**vecchio.get("consultazione", {}), **cons},
           "creazione": cre if ok_cre else {**vecchio.get("creazione", {}), **cre},
           "per_autore": pa if ok_pa else {**vecchio.get("per_autore", {}), **pa},
           "schede": schede, "n_archivio": len(arch),
           "incompleto": [n for n, ok in (("autori", ok_ti), ("musica", ok_mu), ("per_autore", ok_pa),
                                                         ("consultazione", ok_cons), ("creazione", ok_cre)) if not ok]}
    json.dump(out, open(USCITA, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    print("scritto", USCITA, "| pezzi incompleti:", out["incompleto"] or "nessuno",
          "| risposte «aspetta» o mancate:", dict(ATTESE) or "nessuna")


if __name__ == "__main__":
    main()
