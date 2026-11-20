"""Elenco delle cose da decidere con Marco: docs/da-decidere.md (deciso il 19/11/2026).

Il sistema gira da solo; questo file raccoglie SOLO le eccezioni, cioè i casi in cui i dati non bastano:
  1. fonti che non hanno risposto (il sistema non deve andare avanti in silenzio);
  2. libri USA che una fonte autorevole dà usciti prima dell'anno della lista;
  3. autori con l'anno di morte discorde tra le fonti;
  4. la lista Duke dell'anno non ancora letta (dopo il 1° gennaio);
  5. il calendario degli anniversari dell'anno prossimo non ancora approvato (da settembre);
  6. i nomi in apertura delle pagine del Public Domain Day, da guardare prima che escano.
Non scarica niente: legge solo i file già prodotti dagli altri script.
"""
import json
from datetime import date
from pathlib import Path

R = Path(__file__).resolve().parent.parent
D = R / "data"
OGGI = date.today()
Y = OGGI.year


def leggi(p, vuoto=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return vuoto


def main():
    righe = [f"# Da decidere — {OGGI.isoformat()}", "",
             "Scritto da `scripts/da_decidere.py`. Qui ci sono solo i casi in cui i dati non bastano. "
             "Il resto è già sul sito.", ""]
    n = 0
    anni = sorted(int(p.stem) for p in D.glob("[0-9][0-9][0-9][0-9].json") if int(p.stem) > Y)
    us = leggi(R / "docs" / "stima-sito" / "us-anni.json", {})

    # 0. aggiornamento non finito dopo 3 giri
    if (R / ".incompleto").exists():
        righe += ["## 0. Aggiornamento non finito",
                  "- **L'aggiornamento non ha finito in questo giro.** Non riparte da solo (decisione del 19/11/2026): "
                  "i dati mancanti arrivano al prossimo giro previsto, oppure si lancia a mano.", ""]
        n += 1

    if (R / ".salvataggio_rifiutato").exists():
        righe += ["## 0b. Dati degli autori non salvati",
                  "- **L'ultimo aggiornamento ha prodotto dati incompleti e non sono stati salvati:** "
                  + "; ".join((R / ".salvataggio_rifiutato").read_text(encoding="utf-8").split("\n")).strip("; "), ""]
        n += 1

    # 1. fonti
    ko = {k: v for k, v in (us.get("fonti_non_raggiunte") or {}).items() if v}
    righe.append("## 1. Fonti che non hanno risposto")
    if ko:
        for k, v in sorted(ko.items(), key=lambda x: -x[1]):
            righe.append(f"- **{k}**: {v} richieste fallite nell'ultima verifica dei libri USA.")
            n += 1
    else:
        righe.append("- Nessuna.")
    righe.append("")

    # 2. libri usciti prima
    righe.append("## 2. Libri USA che risultano usciti prima dell'anno della lista")
    trovati = False
    # dai dati veri (data/us-anni-verificati.json), non dal riepilogo dell'ultimo giro: così vale anche una
    # correzione fatta dopo il giro (20/11/2026)
    ver = leggi(D / "us-anni-verificati.json", {})
    def voci(a, esito):
        titoli = {o["qid"]: o.get("titolo") for o in leggi(D / f"us-{a}.json", {}).get("opere", [])}
        return [(titoli.get(q, q), v[1], v[2]) for q, v in (ver.get(str(a)) or {}).items() if v[0] == esito]
    for a in anni:
        for titolo, anno_f, fonte in voci(a, "prima"):
            righe.append(f"- Lista {a}: **{titolo}**: {fonte} dà il {anno_f}. Se è vero, il libro è già libero e va tolto dalla lista.")
            trovati = True
            n += 1
    if not trovati:
        righe.append("- Nessuno.")
    righe.append("")

    # 2b. libri usciti a puntate fino a un anno dopo
    righe.append("## 2b. Libri USA usciti a puntate fino a un anno dopo")
    trovati = False
    for a in anni:
        for titolo, ultima, fonte in voci(a, "parziale"):
            righe.append(f"- Lista {a}: **{titolo}**: a puntate fino al {ultima} ({fonte}). Per intero è libero solo dal {ultima + 96}.")
            trovati = True
            n += 1
    if not trovati:
        righe.append("- Nessuno.")
    righe.append("")

    # 3. anni di morte discordi
    righe.append("## 3. Autori con l'anno di morte discorde tra le fonti")
    trovati = False
    for a in anni:
        for pref in ("", "es-"):
            p = leggi(D / f"{pref}{a}.json", {})
            for x in p.get("autori", []):
                v = x.get("verifica") or {}
                if x.get("letterario") and v.get("esito") == "discorde":
                    el = ", ".join(f"{k} {y}" for k, y in (v.get("fonti") or {}).items())
                    righe.append(f"- {pref or 'ue-'}{a}: **{x['nome']}** ({el}).")
                    trovati = True
                    n += 1
    if not trovati:
        righe.append("- Nessuno (oppure la verifica delle date non ha ancora girato su questi anni).")
    righe.append("")
    corr = leggi(D / "morti_corrette.json", {}).get("autori", {})
    if corr:
        righe.append("### Corretti in automatico (due fonti autorevoli contro Wikidata): solo da sapere")
        for c in sorted(corr.values(), key=lambda c: c["nome"]):
            righe.append(f"- {c['nome']}: Wikidata {c['morte_wikidata']}, {', '.join(c['fonti'])} {c['morte']}.")
        righe.append("")

    # 4. Duke
    righe.append("## 4. Lista Duke dell'anno")
    dk = leggi(D / "storico" / "duke.json", {})
    if str(Y) in dk:
        righe.append(f"- Letta: {len(dk[str(Y)].get('libri', []))} libri nel {Y}.")
    else:
        righe.append(f"- **La lista Duke del {Y} non è ancora letta.** Esce intorno al 1° gennaio: senza, i libri del {Y - 96} "
                     "hanno solo le nostre conferme.")
        n += 1
    righe.append("")

    # 5. calendario
    righe.append("## 5. Calendario degli anniversari")
    cal = (leggi(D / "calendari_approvati.json", {}) or {}).get("anni", [])
    if OGGI.month >= 9 and (Y + 1) not in cal:
        righe.append(f"- **Il calendario {Y + 1} non è ancora approvato.** Va preparato e scelto con Marco prima di gennaio.")
        n += 1
    else:
        righe.append(f"- Approvati: {', '.join(map(str, cal)) or 'nessuno'}.")
    righe.append("")

    # 5b. calendario e registro unico: un anniversario di morte con un anno diverso da quello deciso nel registro
    reg = leggi(D / "registro" / "autori.json", {}).get("autori", {})
    diversi = []
    for f in sorted(D.glob("anniversari-[0-9][0-9][0-9][0-9].json")):
        for v in leggi(f, {}).get("voci", []):
            r = reg.get(v.get("qid"))
            if v.get("tipo") == "morte" and r and r.get("m") != v.get("anno"):
                diversi.append(f"- {f.stem}: **{v.get('nome')}**, nel calendario morto nel {v.get('anno')}, nel registro {r['m']} "
                               f"({r.get('e')}{': ' + ', '.join(r['a']) if r.get('a') else ''}).")
            elif v.get("tipo") == "morte" and r and r.get("e") == "discorde":
                diversi.append(f"- {f.stem}: **{v.get('nome')}**, anno di morte {v.get('anno')} con fonti discordi: da guardare.")
    righe.append("## 5b. Calendario: anniversari di morte da ricontrollare con il registro")
    righe += diversi or ["- Nessuno."]
    n += len(diversi)
    righe.append("")

    # 6. nomi in apertura
    righe.append("## 6. Nomi in apertura delle pagine del Public Domain Day (da guardare)")
    for a in anni:
        p = leggi(D / f"{a}.json", {})
        lett = {"scrittore", "scrittrice", "poeta", "poetessa", "romanziere", "romanziera", "drammaturgo", "drammaturga",
                "saggista", "novellista", "autore", "autrice"}
        v = lambda x: sum((x.get("visite_" + l) or 0) for l in ("it", "en", "fr", "de", "es"))
        top = sorted([x for x in p.get("autori", []) if x.get("letterario") and x.get("morte") and x.get("pagina")
                      and lett & set(x.get("professioni") or [])], key=lambda x: -v(x))[:8]
        righe.append(f"- {a}: " + ", ".join(x["nome"] for x in top))
    righe.append("")
    righe.insert(4, f"**Casi da decidere: {n}.**\n")
    (R / "docs" / "da-decidere.md").write_text("\n".join(righe) + "\n", encoding="utf-8")
    print(f"docs/da-decidere.md: {n} casi")


if __name__ == "__main__":
    main()
