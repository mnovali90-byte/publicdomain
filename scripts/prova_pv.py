import json, urllib.request, urllib.parse
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com)"}
PAG = [("it", "Pubblico_dominio"), ("en", "Public_domain"), ("en", "Public_Domain_Day"), ("it", "Diritto_d'autore")]
for lingua, titolo in PAG:
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{lingua}.wikipedia/all-access/user/{urllib.parse.quote(titolo, safe='')}/monthly/20200101/20261031"
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
        serie = {i["timestamp"][:6]: i["views"] for i in d["items"]}
    except Exception as e:
        print(lingua, titolo, "ERRORE", e); continue
    print(f"== {lingua} {titolo}")
    for anno in range(2020, 2027):
        print(anno, " ".join(f"{serie.get(f'{anno}{m:02d}', '-'):>6}" for m in range(1, 13)))
