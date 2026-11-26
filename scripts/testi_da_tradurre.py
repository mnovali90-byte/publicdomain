"""Elenco dei testi fissi del sito da tradurre in una lingua nuova (26/11/2026).
Legge i programmi delle pagine e raccoglie ogni testo scritto come T("italiano", "inglese") o testo_l(lang, "italiano", "inglese"):
la chiave è il testo inglese, come in scripts/lingue.py.

Uso:  python3 scripts/testi_da_tradurre.py            → conta i testi
      python3 scripts/testi_da_tradurre.py de         → crea o completa testi/de.json con i testi ancora senza traduzione (valore vuoto)

Restano fuori, perché sono già divisi per lingua nei loro file: i testi della home (scripts/home.py), del calendario (scripts/calendario.py),
del radar (radar/index.html, oggetto TESTI) e di Già pubblici (storico/pagina.html): per una lingua nuova si aggiunge lì un blocco."""
import ast, json, sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
FILE = ["scripts/pagine.py", "scripts/pagine_paese.py"]


def raccogli():
    testi = {}
    for f in FILE:
        albero = ast.parse((RADICE / f).read_text(encoding="utf-8"))
        for n in ast.walk(albero):
            if not isinstance(n, ast.Call) or not isinstance(n.func, ast.Name):
                continue
            if n.func.id == "T" and len(n.args) == 2:
                a, b = n.args
            elif n.func.id == "testo_l" and len(n.args) == 3:
                a, b = n.args[1:]
            else:
                continue
            if isinstance(a, ast.Constant) and isinstance(b, ast.Constant) and isinstance(b.value, str) and b.value.strip():
                testi.setdefault(b.value, a.value)
    return testi


if __name__ == "__main__":
    testi = raccogli()
    print(f"testi fissi da tradurre: {len(testi)}")
    if len(sys.argv) > 1:
        lang = sys.argv[1]
        f = RADICE / "testi" / f"{lang}.json"
        dati = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"nota": f"Traduzioni {lang}: chiave = testo inglese, valore = traduzione con gli stessi segnaposti tra graffe.", "testi": {}}
        for en, it in testi.items():
            dati["testi"].setdefault(en, "")
        f.parent.mkdir(exist_ok=True)
        f.write_text(json.dumps(dati, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        vuoti = sum(1 for v in dati["testi"].values() if not v)
        print(f"{f.relative_to(RADICE)}: {len(dati['testi'])} testi, {vuoti} ancora da tradurre")
