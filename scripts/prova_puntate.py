"""Prova (19/11/2026): date delle puntate (prima e ultima) per romanzi e racconti usciti su rivista.
Fonti: testo della Wikipedia inglese (servizio ufficiale, estratto in testo semplice) e ISFDB (CC BY: pagine delle voci
SERIAL e SHORTFICTION con la data del numero della rivista). Non cambia il sito.
Scrive docs/stima-sito/prova-puntate.json."""
import html, json, re, time, urllib.parse, urllib.request
from pathlib import Path

R = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
NOTI = [("Red Harvest", "Hammett"), ("The Maltese Falcon", "Hammett"), ("The Dain Curse", "Hammett"),
        ("Tarzan Triumphant", "Burroughs")]
MESI = "January|February|March|April|May|June|July|August|September|October|November|December"


def get(u, json_=True):
    for t in range(4):
        try:
            x = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
            return json.loads(x) if json_ else x.decode("utf-8", "replace")
        except Exception as e:
            err = str(e)
            time.sleep(5 * (t + 1))
    return {"errore": err} if json_ else ""


def wikipedia(titolo):
    d = get("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "query", "prop": "extracts", "explaintext": 1, "redirects": 1, "titles": titolo, "format": "json"}))
    pag = next(iter((d.get("query") or {}).get("pages", {}).values()), {})
    testo = pag.get("extract") or ""
    frasi = [f.strip() for f in re.split(r"(?<=[.!?])\s+", testo)
             if re.search(r"serial|install|Black Mask|Weird Tales|Amazing|Argosy|Blue Book|magazine", f, re.I)
             and re.search(rf"(?:{MESI})?\s*\d{{4}}", f)][:4]
    return {"pagina": pag.get("title"), "frasi": frasi}


def isfdb(titolo, autore):
    u = "https://www.isfdb.org/cgi-bin/se.cgi?" + urllib.parse.urlencode({"arg": titolo, "type": "All Titles"})
    h = get(u, json_=False)
    # righe dei risultati: anno, tipo, titolo, autore
    righe = re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S)
    out = []
    for r in righe:
        celle = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", c))).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
        if len(celle) >= 4 and autore.lower() in " ".join(celle).lower():
            out.append(celle[:5])
    return {"url": u, "righe": out[:12], "pagina_ok": bool(h)}


def main():
    casi = list(NOTI)
    for f, l in (("us-2027.json", "2027"), ("us-2028.json", "2028")):
        d = json.loads((R / "data" / f).read_text(encoding="utf-8"))
        ver = json.loads((R / "data" / "us-anni-verificati.json").read_text(encoding="utf-8")).get(l, {})
        for o in d["opere"]:
            if (o.get("lingua") or {}).get("it") in ("inglese", "inglese americano") and (ver.get(o["qid"]) or ["nd"])[0] != "ok" and o.get("autori"):
                casi.append((o["titolo"], o["autori"][0]["nome"].split()[-1]))
    out = {}
    for t, a in casi[:40]:
        out[t] = {"autore": a, "wikipedia": wikipedia(t), "isfdb": isfdb(t, a)}
        print(t, "|", out[t]["wikipedia"]["frasi"][:1], "|", out[t]["isfdb"]["righe"][:3])
        time.sleep(1.5)
    pag = get("https://www.isfdb.org/wiki/index.php/ISFDB_Downloads", json_=False)
    out["_scaricamento_isfdb"] = re.findall(r'href="([^"]+\.(?:zip|gz|sql)[^"]*)"[^>]*>([^<]*)</a>[^<]{0,120}', pag)[:10]
    (R / "docs" / "stima-sito" / "prova-puntate.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
