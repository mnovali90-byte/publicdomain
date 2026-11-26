"""Le lingue del sito, in un posto solo (26/11/2026).

Come funziona (lo stesso metodo di gettext, lo standard dei siti multilingue):
- nel codice ogni testo fisso è scritto come coppia italiano / inglese: T("Chi diventa libero nel {anno}", "Who becomes free in {anno}", anno=anno).
  Le parti che cambiano (numeri, nomi, date) sono segnaposti tra graffe, riempiti dopo.
- per l'italiano e l'inglese il risultato è esattamente il testo scritto nel codice.
- per le altre lingue il testo inglese fa da chiave: la traduzione sta in testi/<lingua>.json, { "testo inglese": "traduzione" },
  con gli stessi segnaposti. Se manca, esce l'inglese e il testo finisce nell'elenco dei mancanti (testi/mancanti-<lingua>.json).

Per aggiungere una lingua: un file testi/<lingua>.json con le traduzioni. Le pagine non si toccano.
"""
import json
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
CARTELLA = RADICE / "testi"
LINGUE_SITO = ("it", "en")          # le lingue con tutte le pagine; le altre arrivano un file alla volta

_cataloghi = {}
_mancanti = {}


def catalogo(lang):
    if lang not in _cataloghi:
        f = CARTELLA / f"{lang}.json"
        _cataloghi[lang] = json.loads(f.read_text(encoding="utf-8")).get("testi", {}) if f.exists() else {}
    return _cataloghi[lang]


def testo(lang, it_txt, en_txt, /, **valori):
    """Il testo nella lingua `lang` («it», «en», …; vero/falso valgono italiano/inglese, per le funzioni che ricevono ancora «it»).
    Senza segnaposti il testo esce com'è scritto (anche con graffe dentro, es. CSS)."""
    if lang is True:
        lang = "it"
    elif lang is False:
        lang = "en"
    if lang == "it":
        modello = it_txt
    elif lang == "en":
        modello = en_txt
    else:
        modello = catalogo(lang).get(en_txt) or None   # vuoto = non ancora tradotto
        if modello is None:
            _mancanti.setdefault(lang, set()).add(en_txt)
            modello = en_txt
    return modello.format(**valori) if valori else modello


def traduttore(lang):
    """La funzione T di una pagina: T(italiano, inglese, **valori)."""
    if lang is True:          # alcune funzioni ricevono ancora «it» (vero/falso) invece della lingua
        lang = "it"
    elif lang is False:
        lang = "en"

    def T(it_txt, en_txt, /, **valori):
        return testo(lang, it_txt, en_txt, **valori)
    return T


def salva_mancanti():
    """Scrive l'elenco dei testi senza traduzione, una lista per lingua (da chiamare a fine generazione)."""
    for lang, insieme in _mancanti.items():
        CARTELLA.mkdir(exist_ok=True)
        (CARTELLA / f"mancanti-{lang}.json").write_text(json.dumps(sorted(insieme), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
