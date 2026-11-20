"""Ricostruzione delle liste USA (20/11/2026, dopo la prova alla cieca contro la Duke).
1. scripts/opere.py: liste data/us-<anno>.json col metodo corretto (se Wikidata non risponde, il file resta com'è).
2. scripts/verifica_anni_usa.py: verifica da capo dell'anno di ogni libro (RIFAI_TUTTO).
3. scripts/pagine.py: pagine del Public Domain Day (pubblico-dominio-<anno>, en/public-domain-<anno>).
4. scripts/da_decidere.py: elenco delle cose da decidere."""
import os, subprocess, sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent
os.environ["RIFAI_TUTTO"] = "1"
os.environ.setdefault("BUDGET_MINUTI_USA", "95")
for passo in ("opere.py", "verifica_anni_usa.py"):
    print("==", passo, flush=True)
    subprocess.run([sys.executable, str(R / "scripts" / passo)], cwd=R, check=False)
sys.path.insert(0, str(R / "scripts"))
import pagine        # noqa: E402
print("== pagine del Public Domain Day:", pagine.crea_landing())
import da_decidere   # noqa: E402
da_decidere.main()
