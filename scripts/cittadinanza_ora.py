"""Una tantum (22/11/2026): cittadinanza di tutti gli autori delle liste (scripts/cittadinanza.py) e pagine rifatte, senza
aspettare l'aggiornamento del 1° dicembre. Lanciato dal workflow «Stima» (docs/stima-sito/passo.txt)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cittadinanza  # noqa: E402

cittadinanza.main()
import pagine  # noqa: E402
pagine.main()
