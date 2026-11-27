"""Thema: tabelle di corrispondenza valore Wikidata -> codici Thema (proposta di Claude, 26/11/2026, da far
controllare a Marco riga per riga) e loro applicazione al catalogo raccolto da scripts/thema_raccolta.py.

Regole (docs/stima-sito/prova-thema/regole-classificazione.md):
- si confronta il codice Wikidata del valore (Q...), mai la parola;
- i generi teatrali (commedia, tragedia, farsa...) danno il codice teatrale solo se l'opera è un testo teatrale;
- i generi per bambini NON danno codici in automatico (regola di Marco: kids solo se certo) -> «da decidere»;
- un'edizione o traduzione prende i codici dell'opera originale, se l'originale è nel catalogo;
- le formule fisse delle descrizioni brevi valgono solo se la descrizione comincia così.
Scrive docs/stima-sito/prova-thema/catalogo/tabelle.json (le righe da controllare) e script.json (esito sul catalogo).
"""
import gzip, json, re
from collections import Counter
from pathlib import Path

CART = Path("docs/stima-sito/prova-thema/catalogo")
TEATRO = "teatro"      # condizione: solo se l'opera è un testo teatrale
NARR = "narrativa"     # condizione: solo se l'opera è narrativa (romanzo, racconto...)
BAMBINI = "bambini"    # mai in automatico
RISERVA = "riserva"    # solo se dagli altri valori non è venuto nessun codice (es. «articolo»: una poesia uscita su rivista resta poesia)

FORMA = {
    "Q5185279": ["DCF"], "Q8261": ["FBC"], "Q49084": ["FYB"], "Q25379": ["DDA"], "Q80056": ["DCF", "DCRS"],
    "Q1279564": ["FYB"], "Q12106333": ["DCF"], "Q149537": ["FYC"], "Q693": ["FNF"], "Q7366": ["AVQ"],
    "Q5292": ["GBC"], "Q472808": ["FYC"], "Q27036528": ["FYB"], "Q25372": ["DDA"], "Q1344": ["AVLF", "AVQ"],
    "Q27560760": ["FNF"], "Q16324495": ["DNL"], "Q23622": ["CBD"], "Q1091366": ["DCF"], "Q72406516": ["DCF"],
    "Q182659": ["DCF"], "Q1194583": ["DDA"], "Q873000": ["DCF"], "Q17991521": ["FYB"], "Q17370328": ["DCF"],
    "Q86730311": ["DCF"], "Q254554": [BAMBINI], "Q216860": ["DCF"], "Q12799318": ["FYC"], "Q9378549": ["DCF"],
    "Q5707594": ["DNP"], "Q1161145": ["DCF"], "Q17367286": ["DCF"], "Q1497584": ["DCF"], "Q656042": ["DCF"],
    "Q338699": ["DCF"], "Q861911": ["DNS"], "Q72408184": ["DDA"], "Q482": ["DCF"], "Q19357149": ["DCQ"],
    "Q10916116": ["NH"], "Q10882175": ["DCF"], "Q36279": ["DNB"], "Q59126": ["FBC"], "Q1782649": ["DCF"],
    "Q65085460": ["DND"], "Q191067": ["DNP"], "Q465821": ["FBC"], "Q133492": ["DND"], "Q80930": ["DDA", "DDT"],
}
GENERE = {
    "Q482": ["DCF"], "Q35760": ["DNL"], "Q693": ["FNF"], "Q40831": [TEATRO, "DDA", "DDL"], "Q699": ["FNF"],
    "Q16575965": ["FK"], "Q24925": ["FL"], "Q132311": ["FM"], "Q80930": [TEATRO, "DDA", "DDT"], "Q36279": ["DNB"],
    "Q1196408": ["FV"], "Q182357": ["DCF"], "Q21802675": ["FJ"], "Q4184": ["DNC"], "Q1164267": ["WTL"],
    "Q6585139": ["FF"], "Q193121": ["DCF"], "Q5937792": ["FF"], "Q24723": ["FNF"], "Q37484": ["DCF"],
    "Q186424": ["FFD"], "Q185363": ["NH"], "Q1072723": ["WTL"], "Q56451354": [BAMBINI], "Q128758": [NARR, "FUP"],
    "Q116953130": ["AVLK", "QRVJ"], "Q25372": ["DDA"], "Q34620": ["DBSG", "DDT"], "Q474090": ["DCF"], "Q112983": ["DNC"],
    "Q19765983": [],  # «romantic fiction»: su Wikidata indica spesso il Romanticismo, non il romanzo rosa -> all'AI
     "Q131539": [BAMBINI], "Q182015": ["FH"], "Q3236984": ["DCF"], "Q5151421": [TEATRO, "DDA", "DDL"],
    "Q136472": ["FV"], "Q20669641": ["FYL"], "Q5292": ["GBC"], "Q465821": ["FBC"], "Q5891": ["QD"],
    "Q208628": ["DNBX"], "Q732782": ["FK"], "Q223945": ["FXB"], "Q185598": ["DND"], "Q12799318": ["FYC"],
    "Q182659": ["DCF"], "Q1161145": ["DCF"], "Q192881": [TEATRO, "DDA"], "Q20664530": ["FF"], "Q21803247": ["FJM"],
    "Q2254211": ["FXP"], "Q30277550": ["NH"], "Q3056541": ["FC"], "Q178985": ["DCF"], "Q110540276": ["FUP"],
    "Q104100753": ["FXS"], "Q10916116": ["NH"], "Q650175": [TEATRO, "DBSG", "DDL"], "Q367591": ["FJW"],
    "Q181001": ["FP"], "Q747483": ["FP"], "Q17991521": ["FYB"], "Q20737414": ["FDV"], "Q861911": ["DNS"],
    "Q101240581": ["FXM"], "Q7440128": ["FJN"], "Q740919": ["FXS"], "Q2561390": ["FU"], "Q58854": ["DS"],
    "Q1469987": [TEATRO, "DBSG", "DDL"], "Q5774663": ["DDA"], "Q2250271": ["FBC"], "Q1619411": ["NHF"],
    "Q21590660": ["FJW"], "Q23622": ["CBD"], "Q193979": [TEATRO, "DDA", "DDL"], "Q1050848": [TEATRO, "DBSG"],
    "Q1248788": ["FBC"], "Q8275050": [BAMBINI], "Q1787111": ["GBCB"], "Q111984153": [BAMBINI], "Q174864": ["DCF"],
    "Q50637": ["AGA"], "Q192782": ["FYL"], "Q191489": [TEATRO, "DDA"], "Q192239": ["FV"], "Q111143082": ["FJN"],
    "Q961849": [TEATRO, "DDA", "DDT"], "Q133492": ["DND"], "Q856713": ["AVLK", "QRVJ"], "Q44342": ["FNM"],
    "Q1312571": ["FXB"], "Q3026054": ["QDHA"], "Q64448878": ["FL"], "Q1784733": ["DND"], "Q20665028": ["FF"],
    "Q11635": ["DDA"], "Q15062348": ["FDB"], "Q512207": ["FBC"], "Q1562657": [TEATRO, "DDA", "DDL"],
    "Q339380": ["QRRB"], "Q20664331": ["FHD"], "Q1221280": ["FNF"], "Q1519335": ["FK"], "Q777828": ["DCF"],
    "Q908667": ["FJM"], "Q605076": ["WB"], "Q60548032": ["WH"], "Q951215": ["DCF"], "Q1080374": ["FL"],
    "Q67467614": ["FL"], "Q13408937": ["QD"], "Q7168625": ["DDA"], "Q156035": ["DNP"], "Q309": ["NH"],
    "Q19715429": ["FYL"], "Q12042160": [], "Q2084705": ["QRJ"], "Q3985225": ["QRJ"],
}
TIPO = {
    "Q191067": [RISERVA, "DNP"], "Q5707594": [RISERVA, "DNP"], "Q699": ["FNF"], "Q693": ["FNF"], "Q24723": ["FNF"],
    "Q116476516": ["DDA"], "Q861911": ["DNS"], "Q133492": ["DND"], "Q189867": ["QRMB1"], "Q221409": ["QRMB1"],
    "Q856713": ["AVLK", "QRVJ"], "Q602446": ["AVQ"], "Q131084": ["AVQ"], "Q43303440": ["FYB"], "Q474090": ["DCF"],
    "Q37484": ["DCF"], "Q47485959": ["DDA"], "Q204698": ["DCF", "WH"], "Q185598": ["DND"], "Q858157": ["FNF"],
    "Q47114558": ["AGC"], "Q23622": ["CBD"], "Q3374808": ["FBC"], "Q1347298": ["FBC"], "Q185363": ["NH"],
    "Q1497584": ["DCF"], "Q7366": ["AVQ"], "Q1517777": ["NH"],
}
# formule fisse all'inizio della descrizione breve (inglese e italiano): solo se la descrizione comincia così
FORMULE = [
    (r"^(\d{4} )?(poem|sonnet|epigram|ballad|ode)\b", ["DCF"]), (r"^(poesia|sonetto|epigramma|ballata|ode)\b", ["DCF"]),
    (r"^(\d{4} )?(play|tragedy|comedy) (by|written by)\b", ["DDA"]), (r"^(opera teatrale|tragedia|commedia) di\b", ["DDA"]),
    (r"^(\d{4} )?novel (by|written by)\b", ["FBC"]), (r"^romanzo (di|scritto da)\b", ["FBC"]),
    (r"^(\d{4} )?short story (by|written by)\b", ["FYB"]), (r"^racconto di\b", ["FYB"]),
    (r"^(\d{4} )?novella (by|written by)\b", ["FYC"]),
    (r"^(\d{4} )?(fable|fairy tale|folk tale)\b", ["FNF"]), (r"^(favola|fiaba)\b", ["FNF"]),
    (r"^(aesop's fable|fable attributed to aesop)", ["FNF"]),
    (r"^(\d{4} )?essay (by|written by)\b", ["DNL"]), (r"^saggio di\b", ["DNL"]),
    (r"^german article in die gartenlaube", ["DNP"]),
    (r"^(\d{4} )?(hymn|christian hymn)\b", ["AVLK", "QRVJ"]),
]
TEATRALI = {"Q25379", "Q25372", "Q1194583", "Q72408184", "Q80930"}            # forme
NARRATIVE = {"Q8261", "Q49084", "Q1279564", "Q149537", "Q472808", "Q27036528", "Q17991521", "Q12799318", "Q465821", "Q59126"}


def codici(d, tutti, visti=None):
    """Codici Thema per un'opera, con la provenienza di ciascuno. Restituisce (codici, provenienze, bambini)."""
    out, da, bambini = [], {}, False
    teatro = bool(TEATRALI & set(d.get("forma", []))) or "Q116476516" in d.get("tipo", []) \
        or bool({"Q25372", "Q11635"} & set(d.get("genere", [])))
    narr = bool(NARRATIVE & set(d.get("forma", [])))

    def aggiungi(lista, origine):
        nonlocal bambini
        if not lista:
            return
        if lista[0] == BAMBINI:
            bambini = True
            return
        if lista[0] == RISERVA:
            if out:
                return
            lista = lista[1:]
        if lista[0] == TEATRO:
            if not teatro:
                return
            lista = lista[1:]
        if lista[0] == NARR:
            if not narr:
                return
            lista = lista[1:]
        for c in lista:
            if c not in out:
                out.append(c)
                da[c] = origine

    for k, tab in (("forma", FORMA), ("genere", GENERE), ("tipo", TIPO)):
        for v in d.get(k, []):
            if tab.get(v) and tab[v][0] != RISERVA:
                aggiungi(tab.get(v), f"{k}:{v}")
    for k, tab in (("forma", FORMA), ("genere", GENERE), ("tipo", TIPO)):
        for v in d.get(k, []):
            if tab.get(v) and tab[v][0] == RISERVA:
                aggiungi(tab.get(v), f"{k}:{v}")
    if not out:
        for l in ("en", "it"):
            t = (d.get("descr_" + l) or "").strip().lower()
            for rx, cc in FORMULE:
                if re.match(rx, t):
                    aggiungi(cc, f"descrizione_{l}")
                    break
            if out:
                break
    if not out and d.get("edizione_di"):
        visti = (visti or set()) | {d["q"]}
        for o in d["edizione_di"]:
            if o in tutti and o not in visti:
                c, _, b = codici(tutti[o], tutti, visti)
                for x in c:
                    if x not in out:
                        out.append(x)
                        da[x] = f"edizione_di:{o}"
                bambini = bambini or b
    return out, da, bambini


def main():
    tema = json.load(open("docs/stima-sito/prova-thema/thema_en.json"))["CodeList"]["ThemaCodes"]["Code"]
    EN = {c["CodeValue"]: c["CodeDescription"] for c in tema}
    IT = {c["CodeValue"]: c["CodeDescription"] for c in json.load(open("docs/stima-sito/prova-thema/thema_it.json"))["CodeList"]["ThemaCodes"]["Code"]}
    for tab in (FORMA, GENERE, TIPO):
        for v, cc in tab.items():
            for c in cc:
                assert c in (TEATRO, NARR, BAMBINI, RISERVA) or c in EN, (v, c)
    tutti = {}
    with gzip.open(CART / "opere.jsonl.gz", "rt", encoding="utf8") as f:
        for r in f:
            d = json.loads(r)
            tutti[d["q"]] = d
    V = json.load(open(CART / "valori.json"))
    nomi = {x["q"]: (x["en"], x["it"], x["opere"]) for k in V for x in V[k]}
    righe = []
    for k, tab in (("forma", FORMA), ("genere", GENERE), ("tipo", TIPO)):
        for x in V.get(k, []):
            if x["q"] in tab:
                cc = tab[x["q"]]
                cond = cc[0] if cc and cc[0] in (TEATRO, NARR, BAMBINI, RISERVA) else ("niente" if not cc else "")
                cod = [c for c in cc if c not in (TEATRO, NARR, BAMBINI, RISERVA)]
                righe.append({"id": f"{k}-{x['q']}", "campo": k, "q": x["q"], "en": x["en"], "it": x["it"], "opere": x["opere"],
                              "codici": [{"c": c, "it": IT.get(c, ""), "en": EN[c]} for c in cod], "condizione": cond})
    for rx, cc in FORMULE:
        righe.append({"id": "formula-" + re.sub(r"\W+", "_", rx)[:40], "campo": "descrizione", "q": "", "en": rx, "it": "", "opere": 0,
                      "codici": [{"c": c, "it": IT.get(c, ""), "en": EN[c]} for c in cc], "condizione": ""})
    esito, prov, uso_riga = Counter(), Counter(), Counter()
    for d in tutti.values():
        c, da, b = codici(d, tutti)
        if c:
            esito["con codici"] += 1
            for o in set(x.split(":")[0] for x in da.values()):
                prov[o] += 1
        elif b:
            esito["solo bambini (da decidere)"] += 1
        else:
            esito["senza codici dallo script"] += 1
    (CART / "tabelle.json").write_text(json.dumps(righe, ensure_ascii=False, indent=0))
    (CART / "script.json").write_text(json.dumps({"esito": esito, "da_dove": prov, "opere": len(tutti)}, ensure_ascii=False, indent=1))
    print(len(righe), "righe di tabella;", dict(esito), "| da dove:", dict(prov))


if __name__ == "__main__":
    main()
