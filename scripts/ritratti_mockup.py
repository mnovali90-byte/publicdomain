"""Ritratti degli autori della classifica nel mockup dello Storico: immagine Wikidata (P18) da Wikimedia Commons,
miniatura 240 px, con autore e licenza della foto (solo licenze libere). Solo per il mockup."""
import json, pathlib, re, time, urllib.parse, urllib.request
UA = {"User-Agent": "PublicDomainTool/0.1 (https://github.com/mnovali90-byte/publicdomain)"}
OUT = pathlib.Path("docs/mockup-ritratti"); OUT.mkdir(parents=True, exist_ok=True)
NOMI = ["William Shakespeare", "Valmiki", "Charles Dickens", "Fyodor Dostoyevsky", "Jane Austen", "George Orwell",
        "Herman Melville", "Brothers Grimm", "Edgar Allan Poe", "Vyasa", "James Joyce"]
def j(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60))
out = {}
for n in NOMI:
    q = """SELECT ?p ?img WHERE { ?p rdfs:label "%s"@en ; wdt:P18 ?img ; wikibase:sitelinks ?sl } ORDER BY DESC(?sl) LIMIT 1""" % n
    r = j("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"}))["results"]["bindings"]
    if not r:
        out[n] = None; continue
    file = urllib.parse.unquote(r[0]["img"]["value"].rsplit("/", 1)[-1])
    meta = j("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "titles": "File:" + file,
             "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 240, "format": "json"}))
    ii = next(iter(meta["query"]["pages"].values()))["imageinfo"][0]
    em = ii.get("extmetadata", {})
    lic = em.get("LicenseShortName", {}).get("value", "")
    aut = re.sub("<[^>]+>", "", em.get("Artist", {}).get("value", "")).strip()
    nome_f = re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-") + ".jpg"
    (OUT / nome_f).write_bytes(urllib.request.urlopen(urllib.request.Request(ii["thumburl"], headers=UA), timeout=60).read())
    out[n] = {"qid": r[0]["p"]["value"].rsplit("/", 1)[-1], "file": file, "miniatura": nome_f, "licenza": lic, "autore_foto": aut[:120],
              "pagina": ii.get("descriptionurl")}
    time.sleep(1)
(OUT / "ritratti.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1))
