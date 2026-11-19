"""Prova (19/11/2026): da dove vengono le 19.430 visite di Asvero Gravelli su Wikipedia in italiano?
Per alcuni autori della lista 2027: titolo della pagina usato (da Wikidata), visite mese per mese degli ultimi 12 mesi
su it.wikipedia, separate per tipo di visitatore (persone «user», programmi «automated», «spider»).
Risultato in docs/stima-sito/prova-visite.json. Non cambia il sito."""
import json, time, urllib.parse, urllib.request
from datetime import date

UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
AUTORI = {"Q3634560": "Asvero Gravelli", "Q352200": "Giovanni Papini", "Q1135452": "Corrado Alvaro", "Q38757": "Bertolt Brecht",
          "Q217566": "Robert Walser", "Q215913": "A. A. Milne"}


def get(u):
    for t in range(3):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60))
        except Exception as e:
            err = str(e)
            time.sleep(3)
    return {"errore": err}


def main():
    d = json.load(open("data/2027.json"))["autori"]
    per_nome = {a["nome"]: a for a in d}
    qids = {per_nome[n]["wikidata"]: n for n in AUTORI.values() if n in per_nome}
    e = get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "wbgetentities", "ids": "|".join(qids), "props": "sitelinks", "format": "json"}))
    out = {}
    fine = date.today().replace(day=1)
    inizio = date(fine.year - 1, fine.month, 1)
    for q, nome in qids.items():
        sl = (e.get("entities", {}).get(q, {}).get("sitelinks", {}) or {})
        titolo = (sl.get("itwiki") or {}).get("title")
        r = {"qid": q, "titolo_itwiki": titolo, "nel_file": {k: per_nome[nome].get(k) for k in ("visite_it", "visite_12m", "indice_it")}}
        if titolo:
            t = urllib.parse.quote(titolo.replace(" ", "_"), safe="")
            for agente in ("user", "automated", "spider"):
                u = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/it.wikipedia/all-access/{agente}/{t}/monthly/"
                     f"{inizio:%Y%m%d}00/{fine:%Y%m%d}00")
                x = get(u)
                r[agente] = {i["timestamp"][:6]: i["views"] for i in x.get("items", [])} if "items" in x else x
                time.sleep(0.5)
            # visite giorno per giorno del mese con più visite (per vedere un picco)
            mesi = r.get("user") or {}
            if isinstance(mesi, dict) and mesi and "errore" not in mesi:
                m = max(mesi, key=mesi.get)
                a, mm = int(m[:4]), int(m[4:])
                fm = date(a + (mm == 12), mm % 12 + 1, 1)
                u = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/it.wikipedia/all-access/user/{t}/daily/"
                     f"{a}{mm:02d}0100/{fm:%Y%m%d}00")
                x = get(u)
                r["giorni_del_mese_max"] = {i["timestamp"][:8]: i["views"] for i in x.get("items", [])} if "items" in x else x
        out[nome] = r
        print(nome, titolo, {k: (sum(v.values()) if isinstance(v, dict) and "errore" not in v else v) for k, v in r.items() if k in ("user", "automated", "spider")})
    open("docs/stima-sito/prova-visite.json", "w").write(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
