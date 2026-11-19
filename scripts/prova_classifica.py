"""Campione della nuova classifica (docs/metodo-classifica.md), prima di cambiare il sito. 19/11/2026.

Per gli scrittori delle liste 2027 (data/2027.json per Italia, Francia, Germania, Regno Unito; data/es-2027.json per
la Spagna) legge le visite mese per mese degli ultimi 12 mesi chiusi sulla Wikipedia della lingua del paese e calcola
le visite tipiche (ogni mese al massimo 3 volte la mediana). Confronta i primi 30 nell'ordine di oggi (come il sito:
voto 0-100, poi visite grezze) e in quello nuovo.
Scrive docs/stima-sito/prova-classifica.json e docs/stima-sito/prova-classifica.md. Non cambia il sito.
"""
import json, statistics, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

R = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
PAESI = [("it", "Italia", "", "it"), ("fr", "Francia", "", "fr"), ("de", "Germania", "", "de"),
         ("uk", "Regno Unito", "", "en"), ("es", "Spagna", "es-", "es")]
OGGI = date.today()
FINE = OGGI.replace(day=1)
INIZIO = date(FINE.year - 1, FINE.month, 1)
LETT = {"scrittore", "scrittrice", "poeta", "poetessa", "romanziere", "romanziera", "drammaturgo", "drammaturga",
        "saggista", "novellista", "autore", "autrice"}


def get(u, prove=6):
    for t in range(prove):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"items": []}
            time.sleep(10 * (t + 1) if e.code == 429 else 3 * (t + 1))   # 429: troppe richieste, si aspetta di più
        except Exception:
            time.sleep(3 * (t + 1))
    return None


def titoli(qids):
    out = {}
    for i in range(0, len(qids), 50):
        d = get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
            {"action": "wbgetentities", "ids": "|".join(qids[i:i + 50]), "props": "sitelinks", "format": "json"}))
        for q, e in (d or {}).get("entities", {}).items():
            out[q] = {k[:-4]: v["title"] for k, v in (e.get("sitelinks") or {}).items() if k.endswith("wiki")}
        time.sleep(0.5)
    return out


def mesi(lingua, titolo):
    t = urllib.parse.quote(titolo.replace(" ", "_"), safe="")
    d = get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{lingua}.wikipedia/all-access/user/{t}/monthly/"
            f"{INIZIO:%Y%m%d}00/{FINE - timedelta(days=1):%Y%m%d}00")
    if d is None:
        return None
    m = {i["timestamp"][:6]: i["views"] for i in d.get("items", [])}
    chiavi = []
    y, mm = INIZIO.year, INIZIO.month
    for _ in range(12):
        chiavi.append(f"{y}{mm:02d}")
        mm += 1
        if mm == 13:
            y, mm = y + 1, 1
    return [m.get(k, 0) for k in chiavi]


def tipiche(serie):
    med = statistics.median(serie)
    tetto = 3 * med
    picco = max(serie) > tetto and max(serie) - tetto >= 1000
    return int(sum(min(x, tetto) for x in serie)), picco, int(med)


def main():
    out, md = {}, [f"# Campione della nuova classifica — {OGGI.isoformat()}", "",
                   f"Visite da persone, {INIZIO:%m/%Y}–{FINE - timedelta(days=1):%m/%Y} (12 mesi chiusi). "
                   "**Prima** = ordine del sito oggi (voto 0-100, poi visite grezze). **Dopo** = visite tipiche "
                   "(ogni mese al massimo 3 volte il mese tipico). ⚡ = picco.", ""]
    dati = {pref: json.loads((R / "data" / f"{pref}2027.json").read_text(encoding="utf-8")) for pref in ("", "es-")}
    tutti = {a["wikidata"]: a for d in dati.values() for a in d["autori"] if a.get("letterario") and a.get("morte")}
    tit = titoli(sorted(tutti))
    lavori = [(q, l) for q in tutti for _, _, _, l in PAESI if tit.get(q, {}).get(l)]
    lavori = sorted(set(lavori))
    print("pagine da leggere:", len(lavori))
    serie = {}

    def uno(x):
        q, l = x
        time.sleep(0.05)
        return x, mesi(l, tit[q][l])
    with ThreadPoolExecutor(max_workers=3) as pool:   # con 8 lavori in parallelo 152 letture su 1.521 erano fallite (19/11/2026)
        for (q, l), s in pool.map(uno, lavori):
            serie[(q, l)] = s
    # seconda passata, una alla volta, per quelle fallite
    for k in [k for k, s in serie.items() if s is None]:
        time.sleep(1)
        serie[k] = mesi(k[1], tit[k[0]][k[1]])
    falliti = sum(1 for s in serie.values() if s is None)
    print("letture fallite dopo la seconda passata:", falliti)
    for cod, nome, pref, l in PAESI:
        aut = [a for a in dati[pref]["autori"] if a.get("letterario") and a.get("morte")]
        prima = sorted(aut, key=lambda a: (-(a.get("indice_" + (l if cod != "uk" else "en")) if a.get("indice_" + (l if cod != "uk" else "en")) is not None else -1),
                                            -(a.get("visite_" + l) or 0), -(a.get("pagine_wikipedia") or 0), a["nome"]))
        righe = []
        for a in aut:
            s = serie.get((a["wikidata"], l))
            v, p, med = tipiche(s) if s else (0, False, 0)
            righe.append((a, v, p, sum(s) if s else 0, med, s))
        dopo = sorted(righe, key=lambda r: (-r[1], -(r[0].get("pagine_wikipedia") or 0), r[0]["nome"]))
        pos_prima = {a["wikidata"]: i + 1 for i, a in enumerate(prima)}
        out[cod] = {
            "prima": [[a["nome"], a.get("visite_" + l)] for a in prima[:30]],
            "dopo": [[r[0]["nome"], r[1], r[3], r[4], r[2], pos_prima[r[0]["wikidata"]], r[5]] for r in dopo[:30]],
            "picchi": [[r[0]["nome"], r[3], r[1], r[5]] for r in righe if r[2]],
        }
        md += [f"## {nome} (Wikipedia in {l})", "", "| # | Prima | Dopo | visite tipiche (grezze) | prima era |", "|---|---|---|---|---|"]
        for i in range(30):
            pa = prima[i]["nome"] if i < len(prima) else ""
            if i < len(dopo):
                r = dopo[i]
                md.append(f"| {i + 1} | {pa} | {r[0]['nome']}{' ⚡' if r[2] else ''} | {r[1]:,} ({r[3]:,}) | {pos_prima[r[0]['wikidata']]} |")
        md += ["", f"Picchi in questa lingua: {len(out[cod]['picchi'])}: " +
               ", ".join(f"{n} ({g:,} → {t:,})" for n, g, t, _ in sorted(out[cod]["picchi"], key=lambda x: -x[1])[:15]), ""]
    out["letture_fallite"] = falliti
    md.insert(2, f"**Letture fallite: {falliti}** (se non è 0, il campione non è completo e non vale).\n")
    (R / "docs" / "stima-sito" / "prova-classifica.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (R / "docs" / "stima-sito" / "prova-classifica.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
