import json, urllib.request, urllib.parse, time, sys
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com)"}
d = json.load(open("data/anniversari-2027.json"))
voci = [v for v in d["voci"] if v["tipo"] == "prima edizione" and not v["giorno"]]
def get(u):
    for t in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40) as f:
                return json.load(f)
        except Exception as e:
            err = str(e)[:80]; time.sleep(3)
    print("   ERR", u[:70], err); return None
for v in voci:
    t, a, y = v["nome"], (v.get("autore") or "").split()[-1] if v.get("autore") else "", v["anno"]
    print("==", t, "|", v.get("autore"), "|", y, "| mese:", v["mese"], flush=True)
    r = get("https://openlibrary.org/search.json?" + urllib.parse.urlencode({"title": t, "author": v.get("autore") or "", "limit": 3, "fields": "key,title,first_publish_year,edition_key"}))
    for dd in (r or {}).get("docs", [])[:2]:
        k = dd["key"]
        e = get(f"https://openlibrary.org{k}/editions.json?limit=200")
        ds = sorted({x.get("publish_date") for x in (e or {}).get("entries", []) if str(y) in str(x.get("publish_date", ""))})
        print("  OL", k, dd.get("title"), dd.get("first_publish_year"), ds[:12], flush=True)
    g = get("https://www.googleapis.com/books/v1/volumes?" + urllib.parse.urlencode({"q": f'intitle:"{t}"+inauthor:"{a}"', "maxResults": 20, "printType": "books"}))
    ds = sorted({it["volumeInfo"].get("publishedDate") for it in (g or {}).get("items", []) if str(it["volumeInfo"].get("publishedDate", "")).startswith(str(y))})
    print("  GB", ds[:12], flush=True)
    time.sleep(1)
