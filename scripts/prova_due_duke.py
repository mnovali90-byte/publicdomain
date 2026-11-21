"""Prova (21/11/2026), non cambia il sito: Cup of Gold (Steinbeck) e The Roman Hat Mystery (Ellery Queen) con la
ricerca nuova (titolo senza sottotitolo, pseudonimi degli autori), SENZA usare la Duke: registro del copyright americano
(1929), Open Library, Library of Congress, ISFDB. E il riconoscimento della voce Duke «The Roman Hat Mystery»."""
import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storico")]
import verifica_anni as va      # noqa: E402
import verifica_anni_usa as V   # noqa: E402
import duke                     # noqa: E402

righe = {
    "Q3207868": ["Q3207868", "Cup of Gold: A Life of Sir Henry Morgan, Buccaneer, with Occasional Reference to History", "", 1929, 10,
                 [["Q39212", "John Steinbeck", 1968, False, 0, False]]],
    "Q1147884": ["Q1147884", "The Roman Hat Mystery", "", 1929, 10,
                 [["Q10323597", "Manfred B. Lee", 1971, False, 0, False], ["Q10285740", "Frederic Dannay", 1982, False, 0, False]]],
}
va.pseudonimi([a[0] for r in righe.values() for a in r[5]])
out = {"pseudonimi": {a[1]: va._PSEUDO.get(a[0]) for r in righe.values() for a in r[5]}}
idx = V.indice_cce([1929])
for q, r in righe.items():
    o = {"qid": q, "titolo": r[1], "autori": [{"qid": a[0], "nome": a[1]} for a in r[5]]}
    cognomi = va.cognomi_riga(r)
    out[r[1][:40]] = {"titolo cercato": va.titolo_cercato(r[1]), "cognomi": cognomi,
                      "registro del copyright": V.cce(idx, o, cognomi),
                      "open library": va.open_library(r), "library of congress": va.library_of_congress(r)}
out["duke: The Roman Hat Mystery ora riconosciuta come"] = (duke.risolvi("Ellery Queen", "The Roman Hat Mystery") or {}).get("qid")
json.dump(out, open("docs/stima-sito/prova-due-duke.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
