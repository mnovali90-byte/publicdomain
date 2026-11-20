"""Lo Storico usa gli anni di morte del REGISTRO UNICO (data/registro/autori.json, scripts/registro_autori.py),
non più quelli presi da Wikidata da solo (20/11/2026). La regola sta in scripts/regole.py, morte_dal_registro().

Due usi:
- storico/storico.py chiama applica() su ogni autore prima di scrivere i file;
- lanciato da solo (passo di .github/workflows/gia-pubblici.yml), riscrive i file già pronti dello Storico
  (opere.json, ricerca/, per_autore/) senza rifare tutto il giro mensile.
«morte_incerta» diventa 2 quando le fonti discordano proprio sul confine europeo: la pagina mostra «da verificare»."""
import glob, json, os, sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from regole import morte_dal_registro  # noqa: E402

CARTELLA = "data/storico"
ANNO_UE = date.today().year - 71
_REG = None


def registro():
    global _REG
    if _REG is None:
        try:
            _REG = json.load(open("data/registro/autori.json", encoding="utf8")).get("autori", {})
        except Exception:
            _REG = {}
    return _REG


def applica(a):
    """a: autore come dizionario dello Storico ({"qid", "morte", "morte_incerta", ...}). Cambia a sul posto."""
    m, inc = morte_dal_registro(a.get("qid"), a.get("morte"), registro(), ANNO_UE)
    if inc is None:
        return False
    cambiato = m != a.get("morte") or (inc == 2) != (a.get("morte_incerta") == 2)
    a["morte"] = m
    a["morte_incerta"] = 2 if inc == 2 else max(a.get("morte_incerta") or 0, inc)
    return cambiato


def _riga(r, i_morte, i_inc):
    """Riga di un file (autore come lista). Restituisce True se cambiata."""
    m, inc = morte_dal_registro(r[0], r[i_morte], registro(), ANNO_UE)
    if inc is None:
        return False
    nuovo_inc = 2 if inc == 2 else max(r[i_inc] or 0, inc)
    if r[i_morte] == m and r[i_inc] == nuovo_inc:
        return False
    r[i_morte], r[i_inc] = m, nuovo_inc
    return True


def main():
    if not registro():
        print("registro non trovato: lo Storico resta com'è"); return
    cambi = 0
    f = f"{CARTELLA}/opere.json"
    d = json.load(open(f, encoding="utf8"))
    for o in d["opere"]:
        for a in o.get("autori", []):
            cambi += applica(a)
    json.dump(d, open(f, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    for f in sorted(glob.glob(f"{CARTELLA}/ricerca/*.json")):
        d = json.load(open(f, encoding="utf8"))
        c = sum(_riga(a, 2, 4) for r in d["opere"] for a in r[5]) + sum(_riga(r, 2, 5) for r in d["autori"])
        if c:
            json.dump(d, open(f, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
            cambi += c
    for f in sorted(glob.glob(f"{CARTELLA}/per_autore/*.json")):
        d = json.load(open(f, encoding="utf8"))
        c = sum(_riga(a, 2, 4) for righe in d.values() for r in righe for a in r[5])
        if c:
            json.dump(d, open(f, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
            cambi += c
    print("Storico allineato al registro: voci cambiate", cambi)


if __name__ == "__main__":
    main()
