#!/usr/bin/env python3
"""Riconoscimento degli autori nella BnF (piano qualità, 18/11/2026; prove in docs/registro-prove.md).

Ordine, dal più sicuro al meno sicuro, con le stesse regole di SBN (scripts/riconosci_sbn.py):
  1. CODICI BnF che Wikidata indica per l'autore (P268): TUTTI, non solo il primo (Roger Vercel ne ha due:
     il nome d'arte e il vero nome). Se la scheda esiste è lui; ci si ferma qui anche con zero notizie in francese.
  2. NOME, solo se Wikidata non ha codici: si cercano le schede d'autore BnF con il cognome (con e senza accenti,
     parti dei cognomi composti, pseudonimi e nomi alternativi di Wikidata); il nome si confronta normalizzato da
     tutte e due le parti (riconosci_sbn.compatibile). Una scheda si accetta SOLO se gli anni scritti nella scheda
     coincidono (±1) con Wikidata e nessuno li contraddice. Senza anni la scheda resta «ambigua» e non si conta.
Le notizie che hanno il nome dell'autore ma non sono collegate alla sua scheda NON si contano: possono essere di
omonimi (Arlen, Cummings, Lewis nel campione del 18/11).
Distingue sempre: riconosciuto (con o senza notizie in francese), ambiguo, non_trovato, errore tecnico.
"""
import re
import time
import urllib.parse
import urllib.request

import riconosci_sbn as rs

SRU = "https://catalogue.bnf.fr/api/SRU"
UA = "publicdomain-radar/1.0 (https://github.com/mnovali90-byte/publicdomain)"
MAX_SCHEDE = 200


class ErroreTecnico(Exception):
    """Il servizio BnF non risponde o risponde in modo inatteso: non è un risultato sull'autore."""


def sru(query, schema="unimarcXchange", n=0, pausa=1.0):
    url = SRU + "?" + urllib.parse.urlencode({"version": "1.2", "operation": "searchRetrieve", "query": query,
                                              "recordSchema": schema, "maximumRecords": str(n)})
    ultimo = None
    for t in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            testo = urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")
            time.sleep(pausa)
            m = re.search(r"numberOfRecords>(\d+)<", testo)
            if not m:
                raise ValueError("risposta senza numero di risultati: " + (re.findall(r"<sd:message>([^<]+)", testo) or [testo[:80]])[0])
            return int(m.group(1)), testo
        except Exception as e:
            ultimo = e
            time.sleep(4 * (t + 1))
    raise ErroreTecnico(str(ultimo)[:150])


def schede(testo):
    """Schede d'autore della risposta: ark, cognome, nome, anni, varianti."""
    out = []
    for r in re.findall(r"<srw:recordData>(.*?)</srw:recordData>", testo, re.S):
        ark = re.search(r"ark:/12148/cb(\d{8}\w)", r)
        f200 = re.search(r'tag="200"[^>]*>(.*?)</(?:\w+:)?datafield>', r, re.S)
        if not ark or not f200:
            continue
        sub = lambda c, s=f200.group(1): (re.findall(rf'code="{c}">([^<]*)<', s) or [""])[0]
        varianti = []
        for v in re.findall(r'tag="400"[^>]*>(.*?)</(?:\w+:)?datafield>', r, re.S):
            a = (re.findall(r'code="a">([^<]*)<', v) or [""])[0]
            b = (re.findall(r'code="b">([^<]*)<', v) or [""])[0]
            if a:
                varianti.append(f"{a}, {b}" if b else a)
        out.append({"ark": ark.group(1), "cognome": sub("a"), "nome": sub("b"), "anni": sub("f"), "varianti": varianti})
    return out


def anni(testo):
    """«1867-1957», «1867?-1957», « 19..» -> (nato, morto) con None dove manca un anno certo."""
    m = re.match(r"\s*(\d{4})?\D*?-\s*(\d{4})?", testo or "")
    if not m:
        m2 = re.match(r"\s*(\d{4})", testo or "")
        return (int(m2.group(1)) if m2 else None), None
    return (int(m.group(1)) if m.group(1) else None), (int(m.group(2)) if m.group(2) else None)


def rid(ark):
    return re.sub(r"\D", "", ark or "")[:8]


def filtro(arks):
    return " or ".join(f'bib.author2bib all "{rid(a)}"' for a in arks)


def conta(arks, anno_oggi):
    """Notizie in francese collegate alle schede (tutti i ruoli: autore e collaborazioni) e quante dal 2000."""
    base = f"({filtro(arks)}) and bib.language any \"fre\""
    n, _ = sru(base)
    d = 0
    if n:
        d, _ = sru(f'{base} and bib.date any "{" ".join(str(y) for y in range(2000, anno_oggi + 1))}"')
    return n, d


def riconosci(autore):
    """autore: nome, nascita, morte, p268 (lista), alias, paesi. Solleva ErroreTecnico se la BnF non risponde."""
    codici = [c for c in (autore.get("p268") or []) if len(rid(c)) == 8]
    if codici:
        trovate = []
        for c in codici:
            n, testo = sru(f'aut.persistentid all "ark:/12148/cb{c}"', n=1)
            for s in schede(testo):
                trovate.append(s)
        if trovate:
            return {"stato": "riconosciuto", "metodo": "codice_bnf", "schede": [s["ark"] for s in trovate],
                    "prove": {s["ark"]: f"codice BnF di Wikidata (P268): {s['cognome']}, {s['nome']} {s['anni']}".strip() for s in trovate}}
    nome = autore["nome"]
    nomi = [nome] + list(autore.get("alias") or [])
    orientale = bool(set(autore.get("paesi") or ()) & rs.ORDINE_ORIENTALE)
    nato = int(str(autore["nascita"])[:4]) if str(autore.get("nascita") or "")[:4].isdigit() else None
    morto = int(str(autore["morte"])[:4]) if str(autore.get("morte") or "")[:4].isdigit() else None
    forme = [f for tipo, f in rs.forme_ricerca(nome, autore.get("alias") or [], autore.get("paesi") or []) if tipo == "parola"]
    battesimo = [re.sub(r"[^\w]", "", p) for p in nome.split()[:-1] if len(re.sub(r"[^\w]", "", p)) >= 3]
    cand = {}
    for f in forme:
        n, testo = sru(f'aut.accesspoint all "{f}"', n=MAX_SCHEDE)
        if n > MAX_SCHEDE:                       # cognome comune: si chiede cognome e nome insieme
            for b in battesimo[:2]:
                n2, testo2 = sru(f'aut.accesspoint all "{f} {b}"', n=MAX_SCHEDE)
                for s in schede(testo2):
                    cand.setdefault(s["ark"], s)
        for s in schede(testo):
            cand.setdefault(s["ark"], s)
    accettate, ambigue = {}, {}
    for a, s in cand.items():
        etichette = [f"{s['cognome']}, {s['nome']}"] + s["varianti"]
        if not any(rs.compatibile(n, e, orientale)[0] for n in nomi for e in etichette if "," in e):
            continue
        na, mo = anni(s["anni"])
        if (na and nato and abs(na - nato) > 1) or (mo and morto and abs(mo - morto) > 1):
            continue                             # anni che contraddicono: omonimo
        if (na and nato) or (mo and morto):
            accettate[a] = f"nome compatibile e anni che coincidono: {s['cognome']}, {s['nome']} {s['anni']}"
        else:
            ambigue[a] = f"{s['cognome']}, {s['nome']} {s['anni']}".strip()
    if accettate:
        return {"stato": "riconosciuto", "metodo": "nome_anni_bnf", "schede": sorted(accettate), "prove": accettate, "ambigue": ambigue}
    if ambigue:
        return {"stato": "ambiguo", "metodo": None, "schede": [], "prove": {}, "ambigue": ambigue}
    return {"stato": "non_trovato", "metodo": None, "schede": [], "prove": {}}
