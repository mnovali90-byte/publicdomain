#!/usr/bin/env python3
"""BnF, punto 1, seconda raccolta di prove (solo lettura) sugli stessi 60 autori di docs/campione-bnf/prove.json:
  - tutti: notizie in francese che hanno il NOME dell'autore ma non sono collegate alla sua scheda (bib.author),
    per vedere se il collegamento per codice ne perde; con titoli d'esempio;
  - trovati: come sono collegate TUTTE le notizie in francese (autore, collaboratore, soggetto), fino a 500;
  - senza codice: schede d'autore BnF con lo stesso cognome (ricerca larga, anche senza accenti), con anni.
Scrive docs/campione-bnf/prove2.json."""
import json, pathlib, re, sys, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bnf_campione import sru, record, primo, scheda_autore, senza_accenti, ErroreTecnico, D  # noqa: E402

def nome_query(nome):
    p = [re.sub(r"[^\w\-]", "", x) for x in nome.split() if len(x.strip(".")) > 1]
    return p

def collegamenti(rid, tot):
    c = collections.Counter(); visti = 0
    for start in range(1, min(tot, 500) + 1, 100):
        import urllib.parse
        n, testo = sru(f'bib.author2bib all "{rid}" and bib.language any "fre"', n=100) if start == 1 else (None, None)
        if testo is None:
            break
        for rec in record(testo):
            visti += 1
            come = set()
            for tag in ("700", "701", "702"):
                for f in rec.get(tag, []):
                    if any(rid in x for x in f.get("3", [])):
                        come.add("autore" if tag in ("700", "701") and (f.get("4") or ["070"])[0] == "070" else "collaboratore")
            for tag in ("600",):
                for f in rec.get(tag, []):
                    if any(rid in x for x in f.get("3", [])):
                        come.add("soggetto")
            c["solo soggetto" if come == {"soggetto"} else ("autore" if "autore" in come else "collaboratore" if "collaboratore" in come else "non letto")] += 1
    return visti, dict(c)

def main():
    prove = json.loads((D / "prove.json").read_text(encoding="utf-8"))["autori"]
    out = []
    for r in prove:
        x = {"n": r["n"], "nome": r["nome"], "gruppo": r["gruppo"]}
        p = nome_query(r["nome"])
        try:
            if p:
                cogn = p[-1]
                forme = list(dict.fromkeys([cogn, senza_accenti(cogn)]))
                nb = {}
                for f in forme:
                    q = f'bib.author all "{f}" and bib.author all "{p[0]}" and bib.language any "fre"' if len(p) > 1 else f'bib.author all "{f}" and bib.language any "fre"'
                    n, testo = sru(q, schema="dublincore", n=15)
                    nb[f] = {"quante": n, "esempi": [(re.findall(r"<dc:title>([^<]{0,110})", t) or [""])[0] + " | " + "; ".join(re.findall(r"<dc:creator>([^<]{0,60})", t)[:3]) + " | " + "".join(re.findall(r"<dc:date>([^<]+)", t)[:1])
                                                       for t in re.findall(r"<srw:recordData>(.*?)</srw:recordData>", testo, re.S)]}
                x["notizie_fr_col_nome"] = nb
            if r.get("schede_codice"):
                x["collegamenti"] = {}
                for s in r["schede_codice"]:
                    rid = re.sub(r"\D", "", s["codice"])[:8]
                    if s["notizie_fr"]:
                        x["collegamenti"][s["codice"]] = collegamenti(rid, s["notizie_fr"])
            elif p:
                cand = {}
                for f in list(dict.fromkeys([p[-1], senza_accenti(p[-1])])):
                    n, testo = sru(f'aut.accesspoint all "{f}"', n=50)
                    for rec in record(testo):
                        s = scheda_autore(rec)
                        if s["ark"] and senza_accenti(p[-1]).lower() in senza_accenti(s["nome"]).lower():
                            cand.setdefault(s["ark"], {k: s[k] for k in ("nome", "anni", "varianti")})
                    x.setdefault("quante_schede_cognome", {})[f] = n
                x["schede_cognome"] = cand
        except ErroreTecnico as e:
            x["errore_tecnico"] = str(e)
        out.append(x)
        print(r["n"], r["nome"], x.get("errore_tecnico", ""), flush=True)
    (D / "prove2.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

if __name__ == "__main__":
    main()
