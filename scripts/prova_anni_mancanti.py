"""PROVA – ANNI MANCANTI (22/11/2026, richiesta di Marco: «Wikidata è un layer fra tanti»). Non cambia il sito.

Domanda: per le opere principali delle schede che su Wikidata non hanno l'anno di uscita (375 su 1.260), quante si
completano con le fonti autorevoli? E per le opere che l'anno su Wikidata ce l'hanno, quante volte le fonti dicono un'altra
cosa (cioè: quanto possiamo fidarci di Wikidata)?

Fonti interrogate per ogni opera (titolo inglese e titolo della scheda, più il cognome dell'autore):
  - Library of Congress (catalogo SRU, l'edizione più vecchia con lo stesso titolo);
  - Open Library (first_publish_year; da sola non basta: prova del 19/11/2026);
  - Wikipedia in inglese e in italiano: la scheda della voce dell'opera (campi «published», «pub_date», «release_date»,
    «anno», «1ª ed. originale»), solo se la voce nomina l'autore;
  - BnF per gli autori francesi, K10plus (catalogo collettivo tedesco) per quelli di lingua tedesca.
Non ancora in questa prova: il registro del copyright americano (CCE) per le opere senza anno, perché va letto anno per anno
(si aggiunge se la prova mostra che serve), e SBN per gli autori italiani.

Scrive docs/prova-anni/risultati.json e docs/prova-anni/riepilogo.md. Gira con .github/workflows/prova-anni.yml.
"""
import glob, html, json, os, re, sys, time, urllib.parse, urllib.request
from collections import Counter
from pathlib import Path

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "storico"))
sys.path.insert(0, str(R / "scripts"))
import verifica_anni as va        # noqa: E402  Open Library e Library of Congress, come per lo Storico
import verifica_anni_usa as vu    # noqa: E402  BnF, K10plus

UA = va.UA
BUDGET = float(os.environ.get("BUDGET_MINUTI", "50")) * 60
CONTROLLO = int(os.environ.get("CONTROLLO", "120"))   # opere CON l'anno su Wikidata, per misurare quanto sbaglia
USCITA = R / "docs" / "prova-anni"
FR = {"Francia", "Terza Repubblica francese", "Quarta Repubblica francese", "Belgio"}
DE = {"Germania", "Reich tedesco", "Austria", "Svizzera", "Repubblica Democratica Tedesca", "Repubblica di Weimar",
      "Germania nazista", "Impero austro-ungarico", "Austria-Ungheria"}


def opere_schede():
    senza, con = [], []
    for f in sorted(glob.glob(str(R / "data" / "[0-9]*.json"))):
        for a in json.loads(Path(f).read_text(encoding="utf-8")).get("autori", []):
            for o in a.get("opere", [])[:10]:
                x = {"autore": a["nome"], "aq": a["wikidata"], "morte": str(a.get("morte") or "")[:4], "paesi": a.get("paesi") or [],
                     "titolo": o.get("titolo"), "titolo_en": o.get("titolo_en") or o.get("titolo"), "anno_wikidata": o.get("anno"),
                     "lista": Path(f).stem}
                (senza if o.get("anno") is None else con).append(x)
    return senza, con[::max(1, len(con) // CONTROLLO)][:CONTROLLO]


def riga(x, titolo):
    return [None, titolo, x["titolo"], None, 0, [[x["aq"], x["autore"], None, 0, 0, 0]], 0]


def wikipedia(x):
    """Anno dalla scheda della voce su Wikipedia (inglese, poi italiana), solo se la voce nomina il cognome dell'autore."""
    cognome = (va.parole(x["autore"]) or [""])[-1]
    for lingua, titolo, campi in (("en", x["titolo_en"], r"published|pub_date|release_date|publication_date|first_published"),
                                  ("it", x["titolo"], r"annoorig|anno|1ª ed\. originale|annoprimapubblicazione")):
        if not titolo:
            continue
        u = (f"https://{lingua}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
            {"action": "query", "titles": titolo, "prop": "revisions", "rvprop": "content", "rvslots": "main",
             "redirects": 1, "format": "json", "formatversion": 2}))
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30))
        except Exception:
            continue
        for p in d.get("query", {}).get("pages", []):
            testo = ((p.get("revisions") or [{}])[0].get("slots", {}).get("main", {}).get("content") or "")
            if not testo or cognome.lower() not in va.parole(testo[:6000]) and cognome.lower() not in testo[:6000].lower():
                continue
            m = re.search(r"\|\s*(?:" + campi + r")\s*=\s*([^\n|]*)", testo, re.I)
            if m:
                anni = [int(y) for y in re.findall(r"\b(1[5-9]\d\d|20[0-2]\d)\b", m.group(1))]
                if anni:
                    return min(anni), lingua
        time.sleep(0.3)
    return None, None


def k10plus_senza_anno(titolo, cognome):
    q = f'pica.tit="{titolo}" and pica.per="{cognome}"'
    u = "https://sru.k10plus.de/opac-de-627?" + urllib.parse.urlencode(
        {"version": "1.1", "operation": "searchRetrieve", "query": q, "recordSchema": "marcxml", "maximumRecords": "100"})
    x = vu.scarica(u, timeout=90)
    if not x:
        return None
    anni = []
    for rec in vu.record(x.decode("utf-8", "replace")):
        t = " ".join(f.get("a", "") + " " + f.get("b", "") for f in vu.campi(rec, "245"))
        if vu.stesso_titolo(html.unescape(t), titolo):
            a = vu.controllo(rec, "008")[7:11]
            if a.isdigit():
                anni.append(int(a))
    time.sleep(1)
    return min(anni) if anni else None


def interroga(x):
    trovati = {}
    titoli = list(dict.fromkeys(t for t in (x["titolo_en"], x["titolo"]) if t))
    cognome = (va.parole(x["autore"]) or [""])[-1]
    for t in titoli:
        r = riga(x, t)
        for nome, f in (("loc", va.library_of_congress), ("openlibrary", va.open_library)):
            if nome in trovati:
                continue
            try:
                _, a = f(r)
            except Exception:
                a = None
            if a:
                trovati[nome] = a
    a, lingua = wikipedia(x)
    if a:
        trovati[f"wikipedia_{lingua}"] = a
    paesi = set(x["paesi"])
    for t in titoli:
        if paesi & FR and "bnf" not in trovati:
            a, _ = vu.bnf(t, cognome)
            if a:
                trovati["bnf"] = a
        if paesi & DE and "k10plus" not in trovati:
            a = k10plus_senza_anno(t, cognome)
            if a:
                trovati["k10plus"] = a
    return trovati


def esito(trovati):
    """Come leggere le fonti (da decidere con Marco dopo la prova): qui solo la fotografia di cosa dicono."""
    if not trovati:
        return "nessuna fonte"
    anni = Counter(trovati.values())
    a, n = anni.most_common(1)[0]
    if n >= 2:
        return "due o più fonti d'accordo"
    return "una fonte sola" if len(trovati) == 1 else "fonti in disaccordo"


def main():
    inizio = time.time()
    senza, con = opere_schede()
    USCITA.mkdir(parents=True, exist_ok=True)
    out = {"senza_anno": [], "controllo": []}
    for gruppo, elenco in (("senza_anno", senza), ("controllo", con)):
        for x in elenco:
            if time.time() - inizio > BUDGET:
                break
            t = interroga(x)
            out[gruppo].append({**x, "fonti": t, "esito": esito(t)})
    (USCITA / "risultati.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    # riepilogo
    righe = ["# Prova – anni mancanti", "", f"Opere senza anno su Wikidata nelle schede: {len(senza)}; controllate: {len(out['senza_anno'])}.", ""]
    c = Counter(o["esito"] for o in out["senza_anno"])
    righe += [f"- {k}: {v}" for k, v in c.most_common()]
    f = Counter(k for o in out["senza_anno"] for k in o["fonti"])
    righe += ["", "Quante volte ogni fonte ha trovato un anno: " + ", ".join(f"{k} {v}" for k, v in f.most_common()), ""]
    dis = [o for o in out["controllo"] if o["fonti"]]
    uguali = [o for o in dis if o["anno_wikidata"] in o["fonti"].values() or min(o["fonti"].values()) == o["anno_wikidata"]]
    righe += [f"Controllo: {len(out['controllo'])} opere CON l'anno su Wikidata; con almeno una fonte: {len(dis)}; "
              f"la fonte più vecchia coincide con Wikidata: {len(uguali)}; diverso: {len(dis) - len(uguali)}.", "",
              "Esempi (senza anno):", ""]
    righe += [f"- {o['autore']}, {o['titolo']}: {o['fonti'] or '—'}" for o in out["senza_anno"][:40]]
    righe += ["", "Esempi di controllo dove Wikidata e le fonti non coincidono:", ""]
    righe += [f"- {o['autore']}, {o['titolo']}: Wikidata {o['anno_wikidata']}, fonti {o['fonti']}" for o in dis if o not in uguali][:30]
    (USCITA / "riepilogo.md").write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe[:12]))


if __name__ == "__main__":
    main()
