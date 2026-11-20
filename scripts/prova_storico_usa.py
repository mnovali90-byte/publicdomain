"""Prova (20/11/2026), non cambia il sito: le opere dello Storico libere solo negli USA e ancora «da verificare»
(data/storico/anni_verificati.json, esito nd o no) provate con le fonti forti delle liste (scripts/verifica_anni_usa.py):
registro del copyright americano (CCE, volumi 1923-1930), BnF per le opere francesi, K10plus per le tedesche,
ISFDB per riviste e racconti. Conferma = una fonte dà un'edizione uscita entro il 1930, stesso titolo e stesso autore
(lo stesso criterio dello Storico). Scrive docs/stima-sito/prova-storico-usa.json."""
import glob, json, os, sys, time
from collections import Counter
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storico")]
import verifica_anni_usa as V  # noqa: E402

LIMITE = 2026 - 96
BUDGET = 110 * 60
inizio = time.time()
ver = json.load(open("data/storico/anni_verificati.json", encoding="utf8"))
arch = {}
for f in glob.glob("data/storico/ricerca/*.json"):
    for r in json.load(open(f, encoding="utf8"))["opere"]:
        arch.setdefault(r[0], r)
da_fare = [q for q, v in ver.items() if v[0] in ("nd", "no") and q in arch]
print("opere da verificare:", len(da_fare), flush=True)
idx = V.indice_cce(list(range(1923, LIMITE + 1)))
print("indice CCE: parole", len(idx), flush=True)
orig = V.originali(da_fare)
print("con titolo originale fr/de:", sum(1 for q in da_fare if q in orig and orig[q][0] in ("fr", "de")), flush=True)
conta, esempi, fatte = Counter(), [], 0
for q in da_fare:
    if time.time() - inizio > BUDGET:
        break
    r = arch[q]
    o = {"qid": q, "titolo": r[1], "autori": [{"nome": a[1]} for a in r[5]]}
    cognomi = [V.parole(a[1])[-1] for a in r[5] if V.parole(a[1] or "")]
    trovati = {}
    c = V.cce(idx, o, cognomi)
    if c:
        trovati["cce"] = c
    if q in orig and cognomi:
        lg, t = orig[q]
        try:
            if lg == "fr":
                trovati["bnf"] = V.bnf(t, cognomi[0])[0]
            elif lg == "de":
                trovati["k10plus"] = V.k10plus(t, cognomi[0], min(r[3] + 3, LIMITE))[0]
        except Exception as e:
            conta["errore biblioteca"] += 1
    try:
        i_ = V.puntate_isfdb(o, cognomi, LIMITE)
        if i_:
            trovati["isfdb"] = i_[0]
    except Exception:
        conta["errore isfdb"] += 1
    buone = {f: a for f, a in trovati.items() if a and a <= LIMITE}
    fatte += 1
    if buone:
        f, a = min(buone.items(), key=lambda x: x[1])
        conta["confermate"] += 1
        conta["per fonte: " + f] += 1
        if len(esempi) < 40:
            esempi.append([q, r[2] or r[1], [a_[1] for a_ in r[5]][:2], r[3], f, a])
    elif any(trovati.values()):
        conta["solo edizioni dopo il 1930"] += 1
    else:
        conta["niente"] += 1
    if fatte % 200 == 0:
        print(fatte, dict(conta), flush=True)
out = {"fatte": fatte, "su": len(da_fare), "esiti": dict(conta), "esempi": esempi,
       "minuti": int((time.time() - inizio) / 60)}
json.dump(out, open("docs/stima-sito/prova-storico-usa.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(out["esiti"], "| fatte", fatte, "su", len(da_fare))
