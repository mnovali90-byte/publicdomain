#!/usr/bin/env python3
"""Riconoscimento degli autori in SBN, fase 3 del piano qualità (docs/registro-prove.md).

Ordine, dal più sicuro al meno sicuro (authority control, poi record linkage):
  1. CODICE SBN che Wikidata indica per l'autore (P396): se la scheda esiste nel triplestore, è lui.
     Ci si ferma qui anche se ha zero registrazioni in italiano («riconosciuto, zero»).
  2. VIAF (P214): le schede SBN collegate a quel VIAF.
  3. NOME, solo se mancano i codici:
     - si pesca largo: il cognome in tutte le forme (con e senza accenti, con il trattino e senza,
       la parte iniziale della parola fino al primo accento, es. «Sald*» per Saldías), più gli pseudonimi
       e i nomi alternativi di Wikidata;
     - si confronta normalizzato da tutte e due le parti (minuscole, senza accenti né punteggiatura,
       particelle come «de», «von», «van» trattate a parte, ordine delle parole libero);
     - una scheda con nome compatibile si accetta SOLO con una prova in più:
         a) anni scritti nella scheda che coincidono (±1) con Wikidata, anche con una qualifica
            («<1880-1957>», «<1948-2007 ; musicista>» si legge);
         b) almeno un titolo collegato alla scheda che torna con le opere di Wikidata;
         c) cognome raro (in SBN al massimo 3 schede con quel cognome) e nome di battesimo per intero,
            non solo l'iniziale;
       anni che contraddicono Wikidata escludono la scheda; senza prove la scheda resta «ambigua» e
       non si conta.
Restituisce stato (riconosciuto / non_trovato / ambiguo), metodo, schede e prove per ogni scheda.
"""
import re
import time
import unicodedata

import sbn

PARTICELLE = {"de", "di", "da", "del", "della", "dei", "degli", "van", "von", "der", "den", "le", "la", "les", "du",
              "des", "ten", "ter", "y", "i", "e", "dos", "das", "do", "zu", "af", "al", "el", "ibn", "bin", "mac", "st"}
STOP_TIT = set("the a an of and il lo la i gli le di del della e ed un una de des du les et der die das und von ein eine "
               "el los las y en per con su al dal nel".split())
URI = "http://triplestore.iccu.sbn.it/resource/Agent/"
SOGLIA_RARO = 3
LIMITE = 1000


def senza_accenti(t):
    t = unicodedata.normalize("NFKD", t or "")
    return "".join(c for c in t if not unicodedata.combining(c))


def parole(t):
    """Parole normalizzate: minuscole, senza accenti, la punteggiatura e i trattini dividono."""
    return re.findall(r"[a-z0-9]+", senza_accenti(t).lower().replace("ʼ", "").replace("'", " "))


def anni_scheda(etichetta):
    """Anni scritti tra < > nell'etichetta SBN, anche con qualifica: «<1948-2007 ; musicista>» -> (1948, 2007)."""
    m = re.search(r"<([^>]*)>", etichetta or "")
    if not m:
        return None, None
    a = re.findall(r"(\d{3,4})", m.group(1))
    if not a:
        return None, None
    nato = int(a[0]) if re.match(r"\s*\d", m.group(1)) else None
    morto = int(a[1]) if len(a) > 1 else (int(a[0]) if re.match(r"\s*(m\.|morto|d\.)", m.group(1)) else None)
    return nato, morto


def scomponi(etichetta):
    """«Falla, Manuel : de <1876-1946>» -> cognome {falla}, particelle {de}, nome [manuel]."""
    e = re.sub(r"<[^>]*>", " ", etichetta or "")
    part = set()
    if " : " in e:
        e, p = e.split(" : ", 1)
        part |= set(parole(p))
    if "," in e:
        cog, nom = e.split(",", 1)
    else:
        cog, nom = e, ""
    cog_p = [w for w in parole(cog) if w not in PARTICELLE]
    part |= {w for w in parole(cog) if w in PARTICELLE}
    return set(cog_p), part, [w for w in parole(nom) if w not in PARTICELLE]


def compatibile(nome_wd, etichetta):
    """Il nome di Wikidata e la scheda SBN possono essere la stessa persona? Restituisce (sì/no, nome intero?).
    Tutte le parole del cognome SBN devono stare nel nome Wikidata. Almeno una parola del nome di battesimo SBN
    deve tornare, per intero o come iniziale (in tutte e due le direzioni: «A. E.» e «Alfred Edgar»); le altre
    parole del nome SBN possono mancare in Wikidata (secondi nomi: «White, Stewart Edward»), ma non possono
    contraddirlo: un'iniziale diversa da tutte quelle di Wikidata esclude la scheda."""
    wd = parole(nome_wd)
    wds = set(wd)
    cog, _part, nom = scomponi(etichetta)
    if not cog or not cog <= wds or not nom:
        return False, False
    resto = [w for w in wd if w not in cog and w not in PARTICELLE]
    if not resto:
        return False, False
    tornano, intero = 0, False
    for w in nom:
        if w in resto:
            tornano += 1
            intero = intero or len(w) > 1
        elif any((len(w) == 1 and r.startswith(w)) or (len(r) == 1 and w.startswith(r)) for r in resto):
            tornano += 1
        elif len(w) == 1:
            return False, False                   # iniziale che non c'è: altra persona
    return tornano > 0, intero


ORDINE_ORIENTALE = {"Giappone", "Cina", "Corea", "Corea del Sud", "Corea del Nord", "Ungheria", "Vietnam", "Taiwan"}


def forme_ricerca(nome, alias=(), paesi=()):
    """Parole da chiedere a SBN: il cognome (ultima parola o parole dopo la particella), le parti dei cognomi
    con il trattino, la prima parola per i nomi in ordine orientale, con e senza accenti, e il prefisso fino
    al primo accento (es. «Sald*»). Lo stesso per pseudonimi e alias."""
    forme = set()
    for n in [nome] + list(alias)[:6]:
        pezzi = [p for p in re.split(r"[\s]+", (n or "").strip()) if p]
        if not pezzi:
            continue
        candidati = {pezzi[-1]}
        if len(pezzi) > 1 and set(paesi or ()) & ORDINE_ORIENTALE:
            candidati.add(pezzi[0])                    # nomi giapponesi, cinesi, ungheresi: il cognome viene prima
        for i, p in enumerate(pezzi[:-1]):             # «Le Gallienne», «van Druten», «Kaye-Smith»: le parti del cognome composto
            if p.lower() in PARTICELLE and i + 1 < len(pezzi):
                candidati.add(pezzi[i + 1])
        for p in list(candidati):
            candidati |= set(p.split("-"))
        for p in candidati:
            p = re.sub(r"[^\w]", "", p.replace("-", ""))
            if len(p) < 3 or p.lower() in PARTICELLE:
                continue
            forme.add(("parola", p))
            s = senza_accenti(p)
            if s != p:
                forme.add(("parola", s))
                m = re.match(r"[A-Za-z]+", p)
                if m and len(m.group(0)) >= 4:
                    forme.add(("prefisso", m.group(0)))
    return sorted(forme)


def pesca(forme, interroga_fn):
    """Schede SBN (uri -> etichetta) che contengono una delle forme. Se una forma dà troppe schede si segnala."""
    out, troppe = {}, []
    for tipo, f in forme:
        cond = f"'{f}*'" if tipo == "prefisso" else f"'{f}'"
        try:
            r = interroga_fn(f'SELECT DISTINCT ?a ?l WHERE {{ ?a <{sbn.LAB}> ?l . ?l bif:contains "{cond}" . '
                             f'FILTER(CONTAINS(STR(?a), "/resource/Agent/")) }} LIMIT {LIMITE}')
        except Exception:
            continue
        time.sleep(sbn.PAUSA)
        if len(r) >= LIMITE:
            troppe.append(f)
        for x in r:
            out.setdefault(x["a"]["value"], x["l"]["value"])
    return out, troppe


def titoli_scheda(uri, interroga_fn):
    try:
        r = interroga_fn(f"SELECT DISTINCT ?t WHERE {{ ?w <{sbn.BF}contribution> ?c . ?c <{sbn.BF}agent> <{uri}> . "
                         f"?w <{sbn.BF}title> ?tt . ?tt <{sbn.BF}mainTitle> ?t }} LIMIT 60")
    except Exception:
        return []
    time.sleep(sbn.PAUSA)
    return [x["t"]["value"] for x in r]


def titolo_torna(titoli_sbn, opere_wd):
    """Un titolo SBN torna con un'opera di Wikidata: stesso titolo, o almeno 2 parole importanti in comune
    (1 se il titolo di Wikidata ne ha una sola, lunga almeno 5 lettere)."""
    pw = [set(w for w in parole(t) if w not in STOP_TIT and len(w) > 2) for t in opere_wd]
    for t in titoli_sbn:
        ps = set(w for w in parole(re.sub(r"<<[^>]*>>", " ", t) + " " + t) if w not in STOP_TIT and len(w) > 2)
        for p in pw:
            if not p:
                continue
            comuni = ps & p
            if len(comuni) >= 2 or (len(p) == 1 and comuni and len(next(iter(comuni))) >= 5):
                return t
    return None


def uri_da_p396(codice):
    m = re.fullmatch(r"(?:IT\\ICCU\\)?([A-Z0-9]{4})\\?(\d{6})", (codice or "").strip())
    return f"{URI}IT-ICCU-{m.group(1)}-{m.group(2)}" if m else None


def esistono(uris, interroga_fn):
    if not uris:
        return {}
    r = interroga_fn("SELECT ?a ?l WHERE { VALUES ?a { " + " ".join(f"<{u}>" for u in uris) + f" }} ?a <{sbn.LAB}> ?l }}")
    time.sleep(sbn.PAUSA)
    return {x["a"]["value"]: x["l"]["value"] for x in r}


def riconosci(autore, interroga_fn=sbn.interroga):
    """autore: dict con nome, nascita, morte, p396 (lista), viaf (lista), alias (lista), opere (titoli Wikidata)."""
    nome = autore["nome"]
    # 1. codice SBN
    p396 = [u for u in (uri_da_p396(c) for c in autore.get("p396") or []) if u]
    trovate = esistono(p396, interroga_fn)
    if trovate:
        return {"stato": "riconosciuto", "metodo": "codice_sbn", "schede": sorted(trovate),
                "prove": {u: f"codice SBN di Wikidata (P396): {l}" for u, l in trovate.items()}}
    # 2. VIAF
    for v in autore.get("viaf") or []:
        r = interroga_fn(f'SELECT DISTINCT ?a ?l WHERE {{ ?a <{sbn.SAME}> <http://viaf.org/viaf/{v}> . ?a <{sbn.LAB}> ?l . '
                         f'FILTER(CONTAINS(STR(?a), "/resource/Agent/")) }}')
        time.sleep(sbn.PAUSA)
        if r:
            return {"stato": "riconosciuto", "metodo": "viaf", "schede": sorted({x["a"]["value"] for x in r}),
                    "prove": {x["a"]["value"]: f"collegata al VIAF {v}: {x['l']['value']}" for x in r}}
    # 3. nome
    nomi = [nome] + list(autore.get("alias") or [])
    cand, troppe = pesca(forme_ricerca(nome, autore.get("alias") or [], autore.get("paesi") or []), interroga_fn)
    nato_wd = int(str(autore["nascita"])[:4]) if autore.get("nascita") and str(autore["nascita"])[:4].isdigit() else None
    morto_wd = int(str(autore["morte"])[:4]) if autore.get("morte") and str(autore["morte"])[:4].isdigit() else None
    per_cognome = {}
    for u, l in cand.items():
        c, _, _ = scomponi(l)
        per_cognome.setdefault(" ".join(sorted(c)), set()).add(u)
    accettate, ambigue = {}, {}
    for u, l in cand.items():
        ok, intero = False, False
        for n in nomi:
            o, i = compatibile(n, l)
            if o:
                ok, intero = True, intero or i
        if not ok:
            continue
        na, mo = anni_scheda(l)
        if (na and nato_wd and abs(na - nato_wd) > 1) or (mo and morto_wd and abs(mo - morto_wd) > 1):
            continue                                     # anni che contraddicono: omonimo
        if (na and nato_wd) or (mo and morto_wd):
            accettate[u] = f"nome compatibile e anni che coincidono: {l}"
            continue
        t = titolo_torna(titoli_scheda(u, interroga_fn), autore.get("opere") or [])
        if t:
            accettate[u] = f"nome compatibile e titolo che torna («{t[:80]}»): {l}"
            continue
        c, _, _ = scomponi(l)
        quanti = len(per_cognome.get(" ".join(sorted(c)), ()))
        raro = quanti <= SOGLIA_RARO and not any(f.lower() in " ".join(sorted(c)) for f in troppe)
        if raro and intero:
            accettate[u] = f"nome intero e cognome raro in SBN ({quanti} schede): {l}"
        else:
            ambigue[u] = l
    if accettate:
        return {"stato": "riconosciuto", "metodo": "nome_con_prova", "schede": sorted(accettate), "prove": accettate,
                "ambigue": ambigue}
    if ambigue:
        return {"stato": "ambiguo", "metodo": None, "schede": [], "prove": {}, "ambigue": ambigue}
    return {"stato": "non_trovato", "metodo": None, "schede": [], "prove": {}}
