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


def secolo_scheda(etichetta):
    """«<sec. 17.>» -> (1601, 1700); None se la scheda non indica un secolo."""
    m = re.search(r"<[^>]*sec\.?\s*(\d{1,2})", etichetta or "")
    if not m:
        return None
    n = int(m.group(1))
    return (n - 1) * 100 + 1, n * 100


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


def compatibile(nome_wd, etichetta, orientale=False):
    """Il nome di Wikidata e la scheda SBN possono essere la stessa persona? Restituisce (sì/no, nome intero?, nomi in più?).
    - Tutte le parole del cognome SBN devono stare nel nome Wikidata.
    - Il PRIMO nome di battesimo SBN deve tornare con il primo di Wikidata, per intero o come iniziale in tutte e due
      le direzioni («A. E.» / «Alfred Edgar»). Per i nomi in ordine orientale basta che torni uno dei nomi.
    - Gli altri nomi SBN possono mancare in Wikidata (secondi nomi: «White, Stewart Edward»); un'iniziale che non c'è
      esclude la scheda. «nomi in più» = la scheda ha nomi che Wikidata non ha: allora il cognome raro non basta,
      serve una prova di anni o di titolo."""
    wd = parole(nome_wd)
    cog, _part, nom = scomponi(etichetta)
    if not cog or not cog <= set(wd) or not nom:
        return False, False, False
    resto = [w for w in wd if w not in cog and (len(w) == 1 or w not in PARTICELLE)]   # «E.» è un'iniziale, non «e»
    if not resto:
        return False, False, False
    torna = lambda a, b: a == b or (len(a) == 1 and b.startswith(a)) or (len(b) == 1 and a.startswith(b))
    if not orientale and not torna(nom[0], resto[0]):
        return False, False, False
    tornano, intero, in_piu = 0, False, False
    for w in nom:
        if w in resto:
            tornano += 1
            intero = intero or len(w) > 1
        elif any(torna(w, r) for r in resto):
            tornano += 1
        elif len(w) == 1:
            return False, False, False
        else:
            in_piu = True
    return tornano > 0, intero, in_piu


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


def pesca(forme, interroga_fn, nomi_battesimo=()):
    """Schede SBN (uri -> etichetta) che contengono una delle forme. Se una forma dà troppe schede (cognomi
    comuni: White, Thomas) si ripete chiedendo cognome E nome di battesimo, con e senza accenti."""
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
            for nb in nomi_battesimo:
                try:
                    r2 = interroga_fn(f'SELECT DISTINCT ?a ?l WHERE {{ ?a <{sbn.LAB}> ?l . ?l bif:contains "{cond} and \'{nb}\'" . '
                                      f'FILTER(CONTAINS(STR(?a), "/resource/Agent/")) }} LIMIT {LIMITE}')
                except Exception:
                    continue
                time.sleep(sbn.PAUSA)
                for x in r2:
                    out.setdefault(x["a"]["value"], x["l"]["value"])
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
    orientale = bool(set(autore.get("paesi") or ()) & ORDINE_ORIENTALE)
    battesimo = sorted({f for n in nomi for p in n.split()[:-1] if len(senza_accenti(p).strip(".")) >= 3
                        for f in (re.sub(r"[^\w]", "", p), re.sub(r"[^\w]", "", senza_accenti(p)))})[:6]
    cand, troppe = pesca(forme_ricerca(nome, autore.get("alias") or [], autore.get("paesi") or []), interroga_fn, battesimo)
    nato_wd = int(str(autore["nascita"])[:4]) if autore.get("nascita") and str(autore["nascita"])[:4].isdigit() else None
    morto_wd = int(str(autore["morte"])[:4]) if autore.get("morte") and str(autore["morte"])[:4].isdigit() else None
    per_cognome = {}
    for u, l in cand.items():
        c, _, _ = scomponi(l)
        per_cognome.setdefault(" ".join(sorted(c)), set()).add(u)
    accettate, ambigue = {}, {}
    for u, l in cand.items():
        ok, intero, in_piu = False, False, True
        for n in nomi:
            o, i, p = compatibile(n, l, orientale)
            if o:
                ok, intero, in_piu = True, intero or i, in_piu and p
        if not ok:
            continue
        na, mo = anni_scheda(l)
        if (na and nato_wd and abs(na - nato_wd) > 1) or (mo and morto_wd and abs(mo - morto_wd) > 1):
            continue                                     # anni che contraddicono: omonimo
        sec = secolo_scheda(l)
        if sec and ((nato_wd and not sec[0] - 30 <= nato_wd <= sec[1]) or (morto_wd and not sec[0] <= morto_wd <= sec[1] + 30)):
            continue                                     # «<sec. 17.>» per un autore del Novecento: omonimo
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
        if raro and intero and not in_piu:
            accettate[u] = f"nome intero e cognome raro in SBN ({quanti} schede): {l}"
        else:
            ambigue[u] = l
    if accettate:
        return {"stato": "riconosciuto", "metodo": "nome_con_prova", "schede": sorted(accettate), "prove": accettate,
                "ambigue": ambigue}
    if ambigue:
        return {"stato": "ambiguo", "metodo": None, "schede": [], "prove": {}, "ambigue": ambigue}
    return {"stato": "non_trovato", "metodo": None, "schede": [], "prove": {}}
