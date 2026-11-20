"""Prova (20/11/2026): fa girare storico/coautori.py e copia il risultato in docs/stima-sito/coautori.json,
per rifare le pagine in locale e mostrare il prima/dopo. Non cambia il sito."""
import os, shutil, subprocess, sys
r = subprocess.run([sys.executable, "storico/coautori.py"])
if os.path.exists("data/storico/coautori.json"):
    shutil.copy("data/storico/coautori.json", "docs/stima-sito/coautori.json")
sys.exit(r.returncode)
