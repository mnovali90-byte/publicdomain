#!/usr/bin/env python3
"""Conteggio verificato nei cataloghi Alma (British Library e BNE senza codice), 18/11/2026.

Problema trovato (docs/registro-prove.md): la ricerca «Cognome nascita-morte» nel campo autore prende anche notizie
in cui il cognome è di una persona e gli anni di un'altra (F. W. Harvey: 142 notizie, quasi tutte di Michael Sadleir,
1888-1957). Correzione: si scaricano le notizie trovate e se ne conta una SOLO se una stessa voce d'autore (campi
100, 700, 110, 710) contiene il cognome e tutti e due gli anni. Il cognome può essere anche quello di uno pseudonimo o
del vero nome indicato in Wikidata (Dion Fortune schedata come «Firth, Violet M., 1890-1946»).
Le notizie «dal 2000» si contano dall'anno di pubblicazione scritto nella notizia (campo 008, o 264/260).
"""
import re
import time
import unicodedata
import urllib.parse
import urllib.request

UA = "publicdomain-radar/1.0 (https://github.com/mnovali90-byte/publicdomain)"
PAGINA = 50
MASSIMO = 3000
PARTICELLE = {"de", "di", "da", "del", "della", "van", "von", "der", "den", "le", "la", "du", "des", "y", "i", "e", "dos", "das", "do"}


class ErroreTecnico(Exception):
    pass


def sa(t):
    return "".join(c for c in unicodedata.normalize("NFKD", t or "") if not unicodedata.combining(c)).lower()


def cognomi(nome, alias=()):
    """Cognomi possibili, normalizzati: ultima parola, parti dei cognomi composti, parole dopo una particella;
    lo stesso per pseudonimi e nomi alternativi."""
    out = set()
    for n in [nome] + list(alias or []):
        p = [re.sub(r"[^\w\-']", "", x) for x in (n or "").split()]
        p = [x for x in p if x]
        if not p:
            continue
        c = {p[-1]}
        for i, x in enumerate(p[:-1]):
            if x.lower() in PARTICELLE and i + 1 < len(p):
                c.add(p[i + 1])
        for x in list(c):
            c |= set(x.split("-"))
        out |= {sa(x) for x in c if len(x) >= 3 and x.lower() not in PARTICELLE}
    return out


def scarica(url):
    ultimo = None
    for t in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            x = urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")
            time.sleep(0.6)
            return x
        except Exception as e:
            ultimo = e
            time.sleep(4 * (t + 1))
    raise ErroreTecnico(str(ultimo)[:150])


def notizie(base, query):
    """Tutte le notizie della ricerca (fino a MASSIMO): per ognuna le voci d'autore e l'anno."""
    out, tot, start = [], None, 1
    while True:
        t = scarica(base + "?" + urllib.parse.urlencode({"version": "1.2", "operation": "searchRetrieve", "query": query,
                                                        "recordSchema": "marcxml", "maximumRecords": str(PAGINA), "startRecord": str(start)}))
        m = re.search(r"numberOfRecords>(\d+)<", t)
        if not m:
            raise ErroreTecnico("risposta senza numero di risultati")
        tot = int(m.group(1))
        for r in re.findall(r"<record xmlns[^>]*>(.*?)</record>", t, re.S) or re.findall(r"<recordData>(.*?)</recordData>", t, re.S):
            voci = []
            for corpo in re.findall(r'tag="(?:100|700|110|710)"[^>]*>(.*?)</datafield>', r, re.S):
                voci.append(" ".join(v for c, v in re.findall(r'code="(\w)">([^<]*)<', corpo) if c in "abcdq"))
            f008 = (re.findall(r'tag="008">([^<]*)<', r) or [""])[0]
            anno = f008[7:11] if f008[7:11].isdigit() else (re.findall(r'tag="26[04]".*?code="c">[^<]*?(\d{4})', r, re.S) or [""])[0]
            out.append({"voci": voci, "anno": anno})
        start += PAGINA
        if start > tot or start > MASSIMO or not tot:
            break
    return tot, out


def iniziali(nome, alias=()):
    """Iniziali dei nomi di battesimo (tutte le parole tranne il cognome), anche da pseudonimi e nomi alternativi."""
    out = set()
    for n in [nome] + list(alias or []):
        for w in (n or "").split()[:-1]:
            w = sa(re.sub(r"[^\w]", "", w))
            if w and w not in PARTICELLE:
                out.add(w[0])
    return out


def sua(voci, cogn, nato, morto, iniz=None):
    """La notizia è dell'autore se una stessa voce d'autore:
    - ha il cognome nella parte prima della virgola (dove i cataloghi scrivono il cognome) o, per i nomi senza
      virgola, in una parola che comincia con il cognome (Wīra Siṅgha per Singh);
    - e ha tutti e due gli anni, OPPURE non ha nessun anno e il nome di battesimo comincia con la stessa iniziale
      (la British Library scrive spesso «Cummings, Ray.» senza anni: versione 2, 18/11/2026).
    Una voce con anni diversi è di un'altra persona."""
    for v in voci:
        w = sa(v)
        cogn_parte, _, resto = w.partition(",")
        parole = re.findall(r"\w+", cogn_parte)
        if not any(c in parole or any(p.startswith(c) and len(c) >= 4 for p in parole) for c in cogn):
            continue
        anni = re.findall(r"\d{4}", w)
        if nato in anni and morto in anni:
            return True
        if not anni and iniz:
            nomi = re.findall(r"[a-z]\w*", resto)
            if nomi and nomi[0][0] in iniz:
                return True
    return False


def conta_verificato(base, query, nome, alias, nascita, morte, anno_oggi):
    nato, morto = str(nascita or "")[:4], str(morte or "")[:4]
    if not (nato.isdigit() and morto.isdigit()):
        return {"trovato": False, "edizioni": 0, "dal_2000": 0}
    cogn, iniz = cognomi(nome, alias), iniziali(nome, alias)
    tot, recs = notizie(base, query)
    sue = [r for r in recs if sua(r["voci"], cogn, nato, morto, iniz)]
    d = sum(1 for r in sue if r["anno"].isdigit() and 2000 <= int(r["anno"]) <= anno_oggi)
    out = {"trovato": len(sue) > 0, "edizioni": len(sue), "dal_2000": d, "trovate_dalla_ricerca": tot, "scartate": len(recs) - len(sue)}
    if tot > MASSIMO:
        out["parziale"] = True          # lette solo le prime MASSIMO notizie
    return out
