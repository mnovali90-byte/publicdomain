"""Controllo della lista di riferimento (ChatGPT, 18/11/2026): per ogni riga apre la fonte della morte e guarda se
la pagina contiene il 1956; per le pagine Wikipedia ricava il codice Wikidata. Solo misura."""
import csv, json, pathlib, re, sys, time, urllib.parse, urllib.request
UA = "PublicDomainTool/0.1 (https://github.com/mnovali90-byte/publicdomain)"
def get(u):
    try:
        r = urllib.request.Request(u, headers={"User-Agent": UA})
        return urllib.request.urlopen(r, timeout=40).read().decode("utf-8", "replace")
    except Exception as e:
        return "ERRORE " + str(e)[:80]
righe = list(csv.DictReader(open("docs/stima-sito/riferimento-1956-chatgpt.csv", encoding="utf-8"), delimiter=";"))
out = []
for r in righe:
    if not r.get("nome"): continue
    u = r["fonte_morte_url"]; t = get(u)
    x = {"nome": r["nome"], "url": u, "errore": t.startswith("ERRORE"), "c_1956": "1956" in t, "qid": None}
    m = re.match(r"https?://(\w+)\.wikipedia\.org/wiki/(.+)", u)
    if m:
        j = get(f"https://{m.group(1)}.wikipedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "prop": "pageprops", "ppprop": "wikibase_item", "redirects": 1, "titles": urllib.parse.unquote(m.group(2)), "format": "json"}))
        try: x["qid"] = next(iter(json.loads(j)["query"]["pages"].values())).get("pageprops", {}).get("wikibase_item")
        except Exception: pass
    m = re.match(r"https?://www\.wikidata\.org/wiki/(Q\d+)", u)
    if m: x["qid"] = m.group(1)
    out.append(x); time.sleep(0.3)
pathlib.Path("docs/stima-sito/riferimento-controllo.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(out), sum(x["c_1956"] for x in out), sum(x["errore"] for x in out), sum(bool(x["qid"]) for x in out))
