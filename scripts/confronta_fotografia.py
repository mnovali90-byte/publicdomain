"""CONFRONTO TRA DUE FOTOGRAFIE DELLO STATO GIURIDICO (passo 3 di docs/giri-automatici.md, 22/11/2026).

Per ogni opera e ogni autore che cambia stato in un paese dice PERCHÉ:
  - «atteso»: stessi dati e stesse regole, è cambiato solo l'anno (il 1° gennaio: «dal 2027» diventa libero, una nota
    che scade sparisce);
  - «dati»: è cambiato un dato usato (anno di uscita, anni di morte, conferma USA, «morto per la Francia», paesi);
  - «regola»: dati uguali ma regole diverse (impronta di assets/regole.js cambiata);
  - «non spiegato»: niente di tutto questo. Non dovrebbe succedere mai.
Entrano ed escono anche le opere e gli autori nuovi o tolti.

Si ferma con errore (codice 1) se c'è un cambio che non è «atteso»: il giro allora non pubblica e l'elenco va a Marco.
Uso: python3 scripts/confronta_fotografia.py vecchia.json nuova.json [--elenco 30]
"""
import gzip, json, sys
from collections import Counter


def carica(p):
    return json.load(gzip.open(p, "rt", encoding="utf-8") if str(p).endswith(".gz") else open(p, encoding="utf-8"))


def confronta(a, b):
    out = []
    for tipo in ("opere", "autori"):
        A, B = a[tipo], b[tipo]
        for q in sorted(set(A) | set(B)):
            if q not in A or q not in B:
                out.append({"tipo": tipo, "q": q, "t": (B.get(q) or A.get(q))["t"], "paese": "-",
                            "prima": "assente" if q not in A else "c'era", "dopo": "assente" if q not in B else "c'è",
                            "perche": "nuova" if q not in A else "tolta"})
                continue
            x, y = A[q], B[q]
            for c in y["stato"]:
                s1, s2 = x["stato"].get(c), y["stato"][c]
                if s1 == s2:
                    continue
                if x["dati"] != y["dati"]:
                    perche = "dati"
                elif a["regole"] == b["regole"] and a["anno"] != b["anno"]:
                    perche = "atteso"   # stessi dati e stesse regole: è cambiato solo l'anno (1° gennaio, note che scadono)
                elif a["regole"] != b["regole"]:
                    perche = "regola"
                else:
                    perche = "non spiegato"
                out.append({"tipo": tipo, "q": q, "t": y["t"], "paese": c, "prima": s1, "dopo": s2, "perche": perche,
                            "dati_prima": x["dati"] if perche == "dati" else None, "dati_dopo": y["dati"] if perche == "dati" else None})
    return out


def fmt(s):
    if not isinstance(s, list):
        return s
    return (f"dal {s[1]}" if s[0] == "dal" else {"si": "libero", "ver": "da verificare", "nd": "non determinato"}[s[0]]) + f" ({s[2]})"


if __name__ == "__main__":
    args = sys.argv[1:]
    n = 30
    if "--elenco" in args:
        i = args.index("--elenco")
        n = int(args[i + 1])
        del args[i:i + 2]
    a, b = carica(args[0]), carica(args[1])
    cambi = confronta(a, b)
    print(f"Fotografia {a['anno']} (regole {a['regole']}) -> {b['anno']} (regole {b['regole']}): {len(cambi)} cambi")
    c = Counter((x["perche"], x["tipo"], isinstance(x["prima"], list) and isinstance(x["dopo"], list)
                 and x["prima"][:2] == x["dopo"][:2]) for x in cambi)
    for (p, t, m), k in sorted(c.items()):
        print(f"  {p:13} {t:7} {k}" + ("  (cambia solo il motivo, non lo stato)" if m else ""))
    c2 = Counter((x["perche"], x["paese"], fmt(x["prima"]).split(" (")[0].split(" ")[0], fmt(x["dopo"]).split(" (")[0]) for x in cambi if x["perche"] != "atteso")
    if c2:
        print("Cambi da guardare (perché, paese, prima -> dopo):")
        for (p, pa, s1, s2), k in c2.most_common(20):
            print(f"  {k:6} {p} {pa}: {s1} -> {s2}")
        print(f"Primi {n}:")
        for x in [x for x in cambi if x["perche"] != "atteso"][:n]:
            print(f"  {x['tipo']} {x['q']} {x['t']!r} {x['paese']}: {fmt(x['prima'])} -> {fmt(x['dopo'])} [{x['perche']}]")
    sys.exit(1 if any(x["perche"] != "atteso" for x in cambi) else 0)
