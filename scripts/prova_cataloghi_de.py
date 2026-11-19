"""Prova (19/11/2026): quale catalogo tedesco risponde da GitHub. Risultato in docs/stima-sito/prova-cataloghi-de.txt."""
import urllib.request, urllib.parse
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
P = {"version": "1.1", "operation": "searchRetrieve", "maximumRecords": "5"}
prove = {
 "k10_jhr_or": "https://sru.k10plus.de/opac-de-627?" + urllib.parse.urlencode({**P, "maximumRecords": "50", "query": 'pica.tit="Die Schlafwandler" and pica.per="Broch" and (pica.jhr=1930 or pica.jhr=1931 or pica.jhr=1932)', "recordSchema": "marcxml"}),
 "k10_jhr_1931": "https://sru.k10plus.de/opac-de-627?" + urllib.parse.urlencode({**P, "maximumRecords": "50", "query": 'pica.tit="Die Schlafwandler" and pica.per="Broch" and pica.jhr=1931', "recordSchema": "marcxml"}),
 "k10_kafka": "https://sru.k10plus.de/opac-de-627?" + urllib.parse.urlencode({**P, "maximumRecords": "50", "query": 'pica.tit="Beim Bau der chinesischen Mauer" and pica.per="Kafka" and (pica.jhr=1929 or pica.jhr=1930 or pica.jhr=1931)', "recordSchema": "marcxml"}),
}
out = []
for k, u in prove.items():
    try:
        x = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read().decode("utf-8", "replace")
        import re
        out.append(f"{k}: OK {len(x)} byte, record={re.findall(r'numberOfRecords>(\d+)<', x)[:1]}, 008={re.findall(r'tag=.008.>([^<]*)<', x)[:6]} 245={re.findall(r'tag=.245.[^>]*>\\s*<subfield code=.a.>([^<]*)<', x)[:4]}")
    except Exception as e:
        out.append(f"{k}: ERRORE {e} {getattr(e, 'read', lambda: b'')()[:300]!r}")
open("docs/stima-sito/prova-cataloghi-de.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
