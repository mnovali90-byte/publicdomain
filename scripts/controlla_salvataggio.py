"""Controllo prima di salvare (19/11/2026, dopo l'incidente del giro annullato).
Confronta i file degli autori appena prodotti (data/<anno>.json, data/es-<anno>.json) con quelli già salvati nel
repository: se gli autori con biografia o con le visite calano di più del 20%, il giro non è andato a buon fine e quei
file NON si salvano (si rimettono quelli di prima, e anche le pagine che ne dipendono). Scrive il motivo in
.salvataggio_rifiutato, letto da docs/da-decidere.md."""
import glob, json, subprocess, sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent
SOGLIA = 0.8


def conta(d):
    a = d.get("autori", [])
    return {"bio": sum(1 for x in a if x.get("bio")), "visite": sum(1 for x in a if x.get("visite_12m") is not None)}


def main():
    rifiuti = []
    for f in sorted(glob.glob(str(R / "data" / "[0-9][0-9][0-9][0-9].json")) + glob.glob(str(R / "data" / "es-[0-9][0-9][0-9][0-9].json"))):
        rel = str(Path(f).relative_to(R))
        try:
            vecchio = json.loads(subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=R, capture_output=True, text=True, check=True).stdout)
        except Exception:
            continue   # file nuovo: niente da confrontare
        nuovo = json.loads(Path(f).read_text(encoding="utf-8"))
        cv, cn = conta(vecchio), conta(nuovo)
        for k in cv:
            if cv[k] and cn[k] < SOGLIA * cv[k]:
                rifiuti.append(f"{rel}: {k} da {cv[k]} a {cn[k]}")
    if rifiuti:
        Path(R / ".salvataggio_rifiutato").write_text("\n".join(rifiuti) + "\n", encoding="utf-8")
        print("Dati incompleti, non si salvano:\n" + "\n".join(rifiuti))
        return 1
    print("Dati completi: si salvano.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
