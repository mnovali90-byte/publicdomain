#!/usr/bin/env python3
"""Fase 2 del piano qualità: campione di riferimento per SBN (vedi docs/registro-prove.md).

Cosa fa, senza cambiare nulla del sito né del modo di cercare gli autori:
1. SCEGLIE il campione, sempre uguale (seme fisso), tra i 460 autori che sbn.py ha interrogato:
   - 60 di sviluppo: 20 trovati col codice VIAF, 15 trovati per nome, 25 non trovati;
   - 80 casi difficili: cognomi con particelle, doppi cognomi, pseudonimi, nomi da translitterare,
     cognomi condivisi da più autori (omonimi possibili), date incomplete.
2. CONGELA il risultato attuale del sistema per ogni autore del campione, rifacendo esattamente la
   stessa ricerca di sbn.py ma salvando anche QUALI schede SBN ha collegato (la cache non lo dice).
3. RACCOGLIE LE PROVE per il controllo a mano:
   - il codice SBN che Wikidata indica per l'autore (P396) e la scheda corrispondente nel triplestore
     (forma del nome e anni), con il link all'OPAC;
   - le schede SBN con lo stesso cognome (fino a 15), con forma del nome e anni;
   - nome, varianti e pseudonimi da Wikidata.
Scrive docs/campione/sbn-campione.csv (da compilare a mano: colonne «manuale_*») e
docs/campione/sbn-base-AAAA-MM-GG.json (risultato del sistema congelato, con le prove).
I casi dubbi si segnano «irrisolto»: non contano né come assenze né come collegamenti giusti.
"""
import csv
import datetime as dt
import json
import pathlib
import random
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sbn  # noqa: E402
from arricchisci import sparql  # noqa: E402

RADICE = pathlib.Path(__file__).resolve().parent.parent
USCITA = RADICE / "docs" / "campione"
SEME = 20261117
PARTICELLE = {"de", "da", "di", "del", "della", "van", "von", "der", "den", "la", "le", "du", "des", "ten", "ter", "y", "e", "dos", "das", "zu", "af", "ibn", "bin", "al", "el"}
PAESI_TRASLIT = {"Russia", "Unione Sovietica", "Impero russo", "Ucraina", "Bielorussia", "Georgia", "Armenia", "Azerbaigian",
                 "Turchia", "Impero ottomano", "Grecia", "Bulgaria", "Serbia", "Israele", "Egitto", "Libano", "Siria", "Iraq", "Iran",
                 "Cina", "Giappone", "Corea", "India", "Pakistan", "Bangladesh", "Kazakistan", "Uzbekistan", "Tagikistan"}
OPAC = "https://opac.sbn.it/risultati-autori/-/opac-autori/detail/{}?core=autoriall"


def autori_noti():
    """Autori dei file dati (per nome, date, paesi), indicizzati per QID."""
    out = {}
    for f in sorted((RADICE / "data").glob("*[0-9][0-9][0-9][0-9].json")):
        if f.name.startswith(("us-", "anniversari-")):
            continue
        for a in json.loads(f.read_text(encoding="utf-8"))["autori"]:
            out.setdefault(a["wikidata"], a)
    return out


def dati_wikidata(qids):
    """P396 (codice SBN), P214 (VIAF), pseudonimi (P742), alias in italiano e inglese."""
    out = {q: {"p396": [], "viaf": [], "pseudonimi": [], "alias": []} for q in qids}
    for i in range(0, len(qids), 60):
        v = " ".join("wd:" + q for q in qids[i:i + 60])
        q = f"""SELECT ?a ?p396 ?viaf ?ps ?al WHERE {{ VALUES ?a {{ {v} }}
          OPTIONAL {{ ?a wdt:P396 ?p396 }} OPTIONAL {{ ?a wdt:P214 ?viaf }} OPTIONAL {{ ?a wdt:P742 ?ps }}
          OPTIONAL {{ ?a skos:altLabel ?al FILTER(LANG(?al) IN ("it", "en")) }} }}"""
        for b in sparql(q):
            k = b["a"]["value"].rsplit("/", 1)[-1]
            for campo, chiave in (("p396", "p396"), ("viaf", "viaf"), ("ps", "pseudonimi"), ("al", "alias")):
                if campo in b and b[campo]["value"] not in out[k][chiave]:
                    out[k][chiave].append(b[campo]["value"])
        time.sleep(2)
    return out


def uri_da_p396(codice):
    """CFIV001172 -> http://triplestore.iccu.sbn.it/resource/Agent/IT-ICCU-CFIV-001172 (forma vista per Brecht)."""
    m = re.fullmatch(r"(?:IT\\ICCU\\)?([A-Z0-9]{4})\\?(\d{6})", codice.strip())
    return f"http://triplestore.iccu.sbn.it/resource/Agent/IT-ICCU-{m.group(1)}-{m.group(2)}" if m else None


def etichette(uris):
    if not uris:
        return {}
    r = sbn.interroga("SELECT ?a ?l WHERE { VALUES ?a { " + " ".join(f"<{u}>" for u in uris) + f" }} ?a <{sbn.LAB}> ?l }}")
    time.sleep(sbn.PAUSA)
    out = {}
    for x in r:
        out.setdefault(x["a"]["value"], []).append(x["l"]["value"])
    return out


def agenti_viaf(viaf):
    r = sbn.interroga(f'SELECT DISTINCT ?a WHERE {{ ?a <{sbn.SAME}> <http://viaf.org/viaf/{viaf}> . '
                      f'FILTER(CONTAINS(STR(?a), "/resource/Agent/")) }}')
    time.sleep(sbn.PAUSA)
    return [x["a"]["value"] for x in r]


def candidati_cognome(nome, quanti=15):
    """Schede SBN con il cognome (ultima parola) nel nome: prove per chi controlla a mano, non per il sistema."""
    cognome = re.sub(r"[^\w]", "", nome.split()[-1])
    if len(cognome) < 3:
        return []
    r = sbn.interroga(f'SELECT DISTINCT ?a ?l WHERE {{ ?a <{sbn.LAB}> ?l . ?l bif:contains "\'{cognome}\'" . '
                      f'FILTER(CONTAINS(STR(?a), "/resource/Agent/")) }} LIMIT 200')
    time.sleep(sbn.PAUSA)
    return [(x["a"]["value"], x["l"]["value"]) for x in r][:quanti]


def risultato_sistema(a, viaf):
    """Stessa logica di sbn.edizioni_italiane, ma dice anche quali schede ha collegato."""
    nome, nascita, morte = a["nome"], a.get("nascita"), a.get("morte")
    uris, metodo, n = [], None, 0
    if viaf:
        f = f'?a <{sbn.SAME}> <http://viaf.org/viaf/{viaf}> . FILTER(CONTAINS(STR(?a), "/resource/Agent/"))'
        n, _, _ = sbn.conta(f, sbn.interroga)
        if n:
            uris, metodo = agenti_viaf(viaf), "viaf"
    if not n:
        u, verificato = sbn.agenti_per_nome(nome, sbn.interroga, nascita, morte)
        if u:
            n, _, _ = sbn.conta("VALUES ?a { " + " ".join(f"<{x}>" for x in u) + " }", sbn.interroga)
            if n:
                uris, metodo = u, ("nome_anni" if verificato else "nome")
    return {"trovato": n > 0, "registrazioni": n, "metodo": metodo, "schede": uris}


def scegli(cache, autori, wd):
    rnd = random.Random(SEME)
    qs = sorted(q for q in cache if q in autori)
    viaf = [q for q in qs if cache[q].get("metodo") == "viaf"]
    nome = [q for q in qs if cache[q].get("metodo") in ("nome", "nome_anni")]
    no = [q for q in qs if not cache[q].get("trovato")]
    sviluppo = [(q, "sviluppo", "trovato col VIAF") for q in rnd.sample(viaf, min(20, len(viaf)))]
    sviluppo += [(q, "sviluppo", "trovato per nome") for q in rnd.sample(nome, min(15, len(nome)))]
    sviluppo += [(q, "sviluppo", "non trovato") for q in rnd.sample(no, min(25, len(no)))]
    presi = {q for q, _, _ in sviluppo}
    cognomi = {}
    for q in qs:
        cognomi.setdefault(autori[q]["nome"].split()[-1].lower(), []).append(q)

    def criterio(q):
        a, parole = autori[q], autori[q]["nome"].split()
        paesi = set(a.get("paesi") or [])
        if any(p.lower() in PARTICELLE for p in parole[1:-1]) or "-" in parole[-1]:
            return "cognome con particella o composto"
        if wd.get(q, {}).get("pseudonimi"):
            return "pseudonimo"
        if paesi & PAESI_TRASLIT:
            return "nome da translitterare"
        if len(cognomi.get(parole[-1].lower(), [])) > 1 or any(len(p.rstrip(".")) == 1 for p in parole):
            return "omonimi possibili o iniziali"
        if not a.get("nascita") or not a.get("morte"):
            return "date incomplete"
        if len(parole) >= 3 and paesi & {"Spagna", "Portogallo", "Messico", "Argentina", "Cile", "Brasile", "Cuba", "Colombia", "Perù"}:
            return "doppio cognome"
        return None

    quote = {"cognome con particella o composto": 16, "pseudonimo": 16, "nome da translitterare": 18,
             "omonimi possibili o iniziali": 12, "date incomplete": 8, "doppio cognome": 10}
    gruppi = {}
    for q in qs:
        if q not in presi:
            c = criterio(q)
            if c:
                gruppi.setdefault(c, []).append(q)
    difficili = []
    for c, n in quote.items():
        lista = gruppi.get(c, [])
        difficili += [(q, "difficile", c) for q in rnd.sample(lista, min(n, len(lista)))]
    # se un gruppo ne ha meno della quota, si completa con gli altri gruppi difficili fino a 80
    resto = [q for c, lista in sorted(gruppi.items()) for q in lista if q not in {x for x, _, _ in difficili}]
    rnd.shuffle(resto)
    for q in resto:
        if len(difficili) >= 80:
            break
        difficili.append((q, "difficile", criterio(q)))
    return sviluppo + difficili[:80]


def main():
    USCITA.mkdir(parents=True, exist_ok=True)
    oggi = dt.date.today().isoformat()
    cache = json.loads((RADICE / "data" / "cache_sbn.json").read_text(encoding="utf-8"))
    autori = autori_noti()
    qs_cache = sorted(q for q in cache if q in autori)
    wd = dati_wikidata(qs_cache)
    campione = scegli(cache, autori, wd)
    print(f"campione: {len(campione)} autori", flush=True)
    righe, base = [], {"congelato": oggi, "nota": "risultato del sistema prima di cambiare il riconoscimento degli autori", "autori": {}}
    for i, (q, gruppo, crit) in enumerate(campione, 1):
        a, w = autori[q], wd.get(q, {})
        try:
            sis = risultato_sistema(a, (w.get("viaf") or [None])[0])
            p396 = [(c, uri_da_p396(c)) for c in w.get("p396", [])]
            lab = etichette([u for u in sis["schede"]] + [u for _, u in p396 if u])
            cand = candidati_cognome(a["nome"])
        except Exception as e:
            print(f"  {a['nome']}: {e}", flush=True)
            sis, p396, lab, cand = {"errore": str(e)[:120]}, [], {}, []
        base["autori"][q] = {"nome": a["nome"], "nascita": a.get("nascita"), "morte": a.get("morte"), "gruppo": gruppo,
                             "criterio": crit, "sistema": sis, "cache": cache.get(q), "wikidata": w,
                             "p396": [{"codice": c, "uri": u, "nel_triplestore": bool(u and lab.get(u)), "etichette": lab.get(u, [])} for c, u in p396],
                             "etichette_schede_sistema": {u: lab.get(u, []) for u in sis.get("schede", [])},
                             "candidati_cognome": cand}
        sist_ok = set(sis.get("schede", []))
        p396_uri = {u for _, u in p396 if u}
        righe.append({
            "qid": q, "nome": a["nome"], "nascita": (a.get("nascita") or "")[:4], "morte": (a.get("morte") or "")[:4],
            "gruppo": gruppo, "criterio": crit,
            "sistema_trovato": sis.get("trovato"), "sistema_metodo": sis.get("metodo") or "", "sistema_registrazioni": sis.get("registrazioni", ""),
            "sistema_schede": " ".join(u.rsplit("/", 1)[-1] for u in sis.get("schede", [])),
            "p396": " ".join(c for c, _ in p396), "p396_nel_triplestore": " ".join("sì" if (u and lab.get(u)) else "no" for _, u in p396),
            "sistema_concorda_con_p396": ("" if not p396_uri else "sistema non ha trovato" if not sist_ok
                                          else ("sì" + (" (più altre schede)" if sist_ok - p396_uri else "")) if sist_ok & p396_uri else "no"),
            "link_opac": " ".join(OPAC.format(c) for c, _ in p396),
            "manuale_esito": "", "manuale_schede_corrette": "", "manuale_prove": "", "manuale_note": "", "verificato_da": "", "verificato_il": "",
        })
        if i % 10 == 0:
            print(f"  {i}/{len(campione)}", flush=True)
    (USCITA / f"sbn-base-{oggi}.json").write_text(json.dumps(base, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(USCITA / "sbn-campione.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(righe[0].keys()))
        w.writeheader()
        w.writerows(righe)
    print("scritti:", USCITA / "sbn-campione.csv", USCITA / f"sbn-base-{oggi}.json")


if __name__ == "__main__":
    main()
