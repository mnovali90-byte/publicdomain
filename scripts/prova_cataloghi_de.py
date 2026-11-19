"""Prova (19/11/2026): quale catalogo tedesco risponde da GitHub. Risultato in docs/stima-sito/prova-cataloghi-de.txt."""
import urllib.request, urllib.parse
UA = {"User-Agent": "PublicDomainRadar/1.0 (https://publicdomainradar.com; open data project)"}
P = {"version": "1.1", "operation": "searchRetrieve", "maximumRecords": "5"}
prove = {
 "dnb": "https://services.dnb.de/sru/dnb?" + urllib.parse.urlencode({**P, "query": 'tit="Die Schlafwandler" and per="Broch"', "recordSchema": "MARC21-xml"}),
 "dnb_token_free_cql": "https://services.dnb.de/sru/dnb?" + urllib.parse.urlencode({**P, "query": "Schlafwandler Broch", "recordSchema": "MARC21-xml"}),
 "k10plus": "https://sru.k10plus.de/opac-de-627?" + urllib.parse.urlencode({**P, "query": 'pica.tit="Die Schlafwandler" and pica.per="Broch"', "recordSchema": "marcxml"}),
 "obvsg_at": "https://services.obvsg.at/sru/OBV-LIT?" + urllib.parse.urlencode({**P, "query": 'alma.title="Die Schlafwandler" and alma.creator="Broch"', "recordSchema": "marcxml"}),
}
out = []
for k, u in prove.items():
    try:
        x = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read().decode("utf-8", "replace")
        import re
        out.append(f"{k}: OK {len(x)} byte, record={re.findall(r'numberOfRecords>(\d+)<', x)[:1]}, 008={re.findall(r'tag=.008.>([^<]*)<', x)[:3]}")
    except Exception as e:
        out.append(f"{k}: ERRORE {e} {getattr(e, 'read', lambda: b'')()[:300]!r}")
open("docs/stima-sito/prova-cataloghi-de.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
