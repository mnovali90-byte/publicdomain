#!/usr/bin/env python3
"""Verifica del nuovo riconoscimento BnF (riconosci_bnf.py) su autori NUOVI, prima del rilascio. Stesso protocollo di SBN:
  congela -> regole congelate (sha256), la misura non parte se cambiano;
  prove   -> autori non usati nel campione di sviluppo: tutti quelli senza codice + 24 con codice estratti a caso;
             prove raccolte SENZA il nuovo sistema (schede d'autore con lo stesso cognome, anni, varianti, titoli francesi);
  (a mano: docs/verifica-bnf/esiti.json, salvato in un commit prima della misura)
  misura  -> nuovo sistema contro gli esiti a mano: persone sbagliate, collegamenti senza prove, mancati, errori tecnici.
Se dopo la misura si cambiano le regole, questo campione diventa di sviluppo e serve una verifica nuova."""
import collections, hashlib, json, pathlib, random, re, subprocess, sys, time, datetime as dt
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import bnf  # noqa: E402
from arricchisci import sparql  # noqa: E402
from bnf_campione import sru, record, scheda_autore, notizie_collegate, senza_accenti, ErroreTecnico  # noqa: E402

RADICE = pathlib.Path(__file__).resolve().parent.parent
D = RADICE / "docs" / "verifica-bnf"
CONGELATI = ["scripts/riconosci_bnf.py", "scripts/riconosci_sbn.py"]
SEME = 20261119


def impronte():
    return {f: hashlib.sha256((RADICE / f).read_bytes()).hexdigest() for f in CONGELATI}


def congela():
    D.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=RADICE, capture_output=True, text=True).stdout.strip()
    (D / "regole-congelate.json").write_text(json.dumps({"commit": commit, "sha256": impronte()}, indent=1), encoding="utf-8")


def autori_e_codici():
    autori = {}
    for f in sorted((RADICE / "data").glob("*[0-9][0-9][0-9][0-9].json")):
        if not f.name.startswith(("us-", "anniversari-", "es-")):
            for a in bnf.candidati(json.loads(f.read_text(encoding="utf-8"))):
                autori.setdefault(a["wikidata"], a)
    qs = sorted(autori)
    wd = {q: {"p268": [], "alias": []} for q in qs}
    for i in range(0, len(qs), 50):
        v = " ".join("wd:" + q for q in qs[i:i + 50])
        for b in sparql(f"""SELECT ?a ?bnf ?ps ?al WHERE {{ VALUES ?a {{ {v} }} OPTIONAL {{ ?a wdt:P268 ?bnf }} OPTIONAL {{ ?a wdt:P742 ?ps }}
              OPTIONAL {{ ?a skos:altLabel ?al FILTER(LANG(?al) IN ("it","en","fr")) }} }}"""):
            k = b["a"]["value"].rsplit("/", 1)[-1]
            for c, ch in (("bnf", "p268"), ("ps", "alias"), ("al", "alias")):
                if c in b and b[c]["value"] not in wd[k][ch]:
                    wd[k][ch].append(b[c]["value"])
        time.sleep(2)
    return autori, wd


def prove():
    D.mkdir(parents=True, exist_ok=True)
    autori, wd = autori_e_codici()
    usati = {x["qid"] for x in json.loads((RADICE / "docs" / "campione-bnf" / "prove.json").read_text(encoding="utf-8"))["autori"]}
    resto = [q for q in sorted(autori) if q not in usati]
    senza = [q for q in resto if not wd[q]["p268"]]
    con = random.Random(SEME).sample([q for q in resto if wd[q]["p268"]], 24)
    out = []
    for n, q in enumerate(senza + con, 1):
        a, w = autori[q], wd[q]
        r = {"n": n, "qid": q, "nome": a["nome"], "nascita": a.get("nascita"), "morte": a.get("morte"), "paesi": a.get("paesi") or [],
             "p268": w["p268"], "alias": w["alias"][:8]}
        try:
            if w["p268"]:
                r["schede_codice"] = []
                for c in w["p268"]:
                    tot, testo = sru(f'aut.persistentid all "ark:/12148/cb{c}"', n=1)
                    s = scheda_autore(record(testo)[0]) if tot else {"ark": None, "nome": "(nessuna scheda)"}
                    s["codice"] = c
                    r["schede_codice"].append(s)
            else:
                p = [re.sub(r"[^\w\-]", "", x) for x in a["nome"].split() if len(x.strip(".")) > 1]
                forme = list(dict.fromkeys([p[-1], senza_accenti(p[-1])] + [x for x in p[-1].split("-") if len(x) > 2] +
                                           [al.split()[-1] for al in w["alias"][:4] if al.split()]))
                cand, quante = {}, {}
                for f in forme:
                    tot, testo = sru(f'aut.accesspoint all "{f}"', n=300)
                    quante[f] = tot
                    if tot > 300 and len(p) > 1:
                        tot2, testo2 = sru(f'aut.accesspoint all "{f} {p[0]}"', n=300)
                        quante[f + " " + p[0]] = tot2
                        testo += testo2
                    for rec in record(testo):
                        s = scheda_autore(rec)
                        if s["ark"] and senza_accenti(f).lower() in senza_accenti(s["nome"] + " " + " ".join(s["varianti"])).lower():
                            cand.setdefault(s["ark"], s)
                iniz = senza_accenti(p[0])[:1].lower()
                for s in list(cand.values()):
                    parole = senza_accenti(s["nome"]).lower().split()
                    if len(cand) <= 40 or any(w.startswith(iniz) for w in parole[1:]):
                        try:
                            s["notizie_fr"], es = notizie_collegate(re.sub(r"\D", "", s["ark"])[:8], n=5)
                            s["titoli_fr"] = [f'{e["titolo"]} ({e["anno"]})' for e in es]
                        except ErroreTecnico as e:
                            s["errore_tecnico"] = str(e)
                r["schede_cognome"], r["quante"] = list(cand.values()), quante
        except ErroreTecnico as e:
            r["errore_tecnico"] = str(e)
        out.append(r)
        print(n, a["nome"], len(r.get("schede_cognome", [])), r.get("errore_tecnico", ""), flush=True)
    (D / "campione.json").write_text(json.dumps({"seme": SEME, "senza_codice": len(senza), "con_codice": len(con), "autori": out},
                                                ensure_ascii=False, indent=1), encoding="utf-8")


def misura():
    import riconosci_bnf
    fermo = json.loads((D / "regole-congelate.json").read_text(encoding="utf-8"))
    if fermo["sha256"] != impronte():
        sys.exit("le regole sono cambiate dopo il congelamento: questo campione non vale più come verifica")
    camp = json.loads((D / "campione.json").read_text(encoding="utf-8"))["autori"]
    esiti = json.loads((D / "esiti.json").read_text(encoding="utf-8"))
    righe, conta = [], collections.Counter()
    for a in camp:
        e = esiti[a["qid"]]
        try:
            r = riconosci_bnf.riconosci({k: a[k] for k in ("nome", "nascita", "morte", "p268", "alias", "paesi")})
            n_fr = riconosci_bnf.conta(r["schede"], dt.date.today().year)[0] if r["schede"] else 0
        except riconosci_bnf.ErroreTecnico as ex:
            r, n_fr = {"stato": "errore tecnico", "schede": [], "errore": str(ex)}, None
        sch, coll = e["schede"], r["schede"]
        sbagliate = [s for s in coll if sch.get(s) == "X"]
        dubbie = [s for s in coll if sch.get(s, "?") == "?"]
        giuste = [s for s in coll if sch.get(s) == "G"]
        if r["stato"] == "errore tecnico":
            esito = "errore tecnico"
        elif sbagliate:
            esito = "persona sbagliata"
        elif dubbie:
            esito = "senza prove sufficienti"
        elif e["esito"] == "C":
            esito = ("trovato" + (" senza notizie in francese" if n_fr == 0 else "")) if giuste else "mancato"
        elif e["esito"] == "A":
            esito = "giusto (nessuna scheda)"
        else:
            esito = "irrisolto, non collegato"
        conta[esito] += 1
        righe.append({"n": a["n"], "qid": a["qid"], "nome": a["nome"], "manuale": e["esito"], "dopo": esito, "stato": r["stato"],
                      "metodo": r.get("metodo"), "schede": coll, "notizie_fr": n_fr, "prove": r.get("prove"), "ambigue": r.get("ambigue")})
        print(a["n"], a["nome"], e["esito"], esito, coll, n_fr, flush=True)
    (D / "misura.json").write_text(json.dumps({"regole": fermo, "conteggi": conta, "autori": righe}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("CONTEGGI", dict(conta))


if __name__ == "__main__":
    {"congela": congela, "prove": prove, "misura": misura}[sys.argv[1]]()
