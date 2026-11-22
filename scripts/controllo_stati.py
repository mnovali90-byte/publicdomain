"""CONTROLLO DEGLI STATI SCRITTI SULLE PAGINE (22/11/2026). Non cambia il sito; si ferma con errore se qualcosa non torna.

Perché: le regole stanno in scripts/regole.py, ma ogni pagina deve usarle. Il 22/11/2026 la vetrina della home dava
«L'opera da tre soldi» libera dal 2027 senza passare dalla regola dei coautori. Questo controllo legge le pagine GIÀ
GENERATE (quello che vede chi visita il sito) e rifà ogni conto da capo con regole.py e i registri, senza usare il codice
che ha scritto le pagine. Così una pagina che salta le regole non passa.

Cosa controlla, su ogni scheda autore in italiano e in inglese:
  1. la tabella «Quando è libero» paese per paese: anno di morte dal registro unico (data/registro/autori.json) e
     regole.anno_libero (Francia: «morti per la Francia» da data/registro/mpf.json);
  2. l'intestazione «… · libero dal 1° gennaio <anno>» e «Altri scrittori liberi dal 1° gennaio <anno>»;
  3. le note dei coautori e della musica: l'anno scritto deve essere quello della regola per l'anno di morte scritto;
  4. le opere principali che sono anche nei dati di Già pubblici (data/storico/ricerca): lo stato negli USA della
     tabella e, in Europa, l'eventuale coautore morto dopo l'autore (se la regola per opera dà una data più tarda,
     la scheda deve avere la nota con quella data) devono coincidere con regole.stato_opera.
Le opere che non sono nei dati di Già pubblici si contano come «non controllabili» (non è un errore).
Uso: python3 scripts/controllo_stati.py   (gira anche dentro scripts/prova_regole.py, parte 6)"""
import glob, html, json, re, sys
from datetime import date
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE / "scripts"))
import regole as R  # noqa: E402

OGGI = date.today().year
PAESI = {"Italia": "it", "Italy": "it", "Francia": "fr", "France": "fr", "Germania": "de", "Germany": "de",
         "Regno Unito": "uk", "United Kingdom": "uk", "Spagna": "es", "Spain": "es"}
MESI = {"gen": 1, "Jan": 1}


def _l(p, d=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return d


def pt(x):
    import unicodedata
    x = unicodedata.normalize("NFKD", html.unescape(str(x or ""))).encode("ascii", "ignore").decode().lower()
    return " ".join(re.findall(r"[a-z0-9]+", x))


def testo(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))


def main(stampa=True):
    reg_aut = (_l(RADICE / "data" / "registro" / "autori.json", {}) or {}).get("autori", {})
    mpf = set((_l(RADICE / "data" / "registro" / "mpf.json", {}) or {}).get("autori", {}))
    reg_op = _l(RADICE / "data" / "registro" / "opere.json", {}) or {}
    # opere di Già pubblici per autore (stessi dati e stessa regola del browser)
    per_aut = {}
    for f in sorted(glob.glob(str(RADICE / "data" / "storico" / "ricerca" / "*.json"))):
        for r in (_l(f, {}) or {}).get("opere", []):
            o = R.opera_da_riga(r, reg_op.get("coautori", {}))
            for au in r[5]:
                for t in (r[1], r[2]):
                    if t:
                        per_aut.setdefault(au[0], {}).setdefault(pt(t), o)
    errori, non_contr, conti = [], 0, {"pagine": 0, "paesi": 0, "intestazioni": 0, "note": 0, "usa": 0, "coautori": 0}

    for f in sorted(glob.glob(str(RADICE / "autore" / "*" / "index.html")) + glob.glob(str(RADICE / "en" / "author" / "*" / "index.html"))):
        h = Path(f).read_text(encoding="utf-8")
        nome_p = "/".join(Path(f).parts[-3:-1])
        m = re.search(r"wikidata\.org/wiki/(Q\d+)", h)
        if not m:
            continue
        q = m.group(1)
        conti["pagine"] += 1
        v = reg_aut.get(q) or {}
        D = v.get("m")
        if not isinstance(D, int):
            non_contr += 1
            continue
        en = "/en/" in f
        if v.get("e") == "discorde":
            # fonti in disaccordo: la scheda usa l'anno della lista e deve dire «da verificare»
            conti["incerti"] = conti.get("incerti", 0) + 1
            hu = html.unescape(h)
            if "le fonti non concordano sull'anno di morte" not in hu and "the sources disagree on the year of death" not in hu:
                errori.append(f"{nome_p}: fonti in disaccordo sull'anno di morte, ma la scheda non dice «da verificare»")
            md = re.search(r"(?:Anno di morte|Year of death) <b>(\d{4})</b>", h)
            if not md:
                continue
            D = int(md.group(1))

        # 1. tabella paese per paese
        ul = re.search(r'<ul class="ps">(.*?)</ul>', h, re.S)
        for li in re.findall(r"<li[^>]*>(.*?)</li>", ul.group(1) if ul else "", re.S):
            mc = re.match(r'<span class="c">([^<]+)<small>', li)
            mv = re.search(r'<span class="v">[^<]*?(\d{4})</span>', li)
            if not (mc and mv):
                continue
            c, anno = mc.group(1), mv.group(1)
            p = PAESI.get(c.strip())
            if not p:
                continue
            conti["paesi"] += 1
            atteso = R.anno_libero(D, p, p == "fr" and q in mpf)
            if int(anno) != atteso:
                errori.append(f"{nome_p}: {c} {anno}, la regola dice {atteso} (morte {D})")

        # 2. intestazione e «altri scrittori»
        for anno in re.findall(r'<div class="cnt">[^<]*· (?:libero dal 1° gennaio|free from 1 January) (\d{4})</div>', h) + \
                re.findall(r"<b>(?:Altri scrittori liberi dal 1° gennaio|Other writers free from 1 January) (\d{4})</b>", h):
            conti["intestazioni"] += 1
            if int(anno) != R.anno_libero(D, "it"):
                errori.append(f"{nome_p}: in alto dice {anno}, la regola dice {R.anno_libero(D, 'it')} (morte {D})")

        # 3. note dei coautori e della musica: l'aritmetica della regola
        note = re.findall(r'<li id="nt\d+"><b>\d+</b>(.*?)</li>', h, re.S)
        for n in note:
            t = testo(n)
            conti["note"] += 1
            m1 = re.search(r"(?:\(morte: |, who died in )(\d{4})\)?: .*?(?:è libera dal 1° gennaio|it is free from 1 January) (\d{4}), (?:in Spagna dal|in Spain from) (\d{4})", t)
            if m1:
                M, ue, es = (int(x) for x in m1.groups())
                if (ue, es) != (R.anno_libero(M, "it"), R.anno_libero(M, "es")):
                    errori.append(f"{nome_p}: nota «{t[:80]}…» dice {ue}/{es}, la regola per la morte {M} dice {R.anno_libero(M, 'it')}/{R.anno_libero(M, 'es')}")
            m2 = re.search(r"\((?:morte: |died )(\d{4})\) .*?(?:fino al 31 dicembre|until 31 December) (\d{4}), (?:in Spagna fino al 31 dicembre|in Spain until 31 December) (\d{4})", t)
            if m2:
                M, ue, es = (int(x) for x in m2.groups())
                if (ue, es) != (R.anno_libero(M, "it") - 1, R.anno_libero(M, "es") - 1):
                    errori.append(f"{nome_p}: nota «{t[:80]}…» dice fino al {ue}/{es}, la regola per la morte {M} dice {R.anno_libero(M, 'it') - 1}/{R.anno_libero(M, 'es') - 1}")

        # 4. opere principali anche in Già pubblici: USA e coautori come regole.stato_opera
        mie = per_aut.get(q, {})
        righe = re.findall(r'<li><span class="t">(.*?)</span><span class="y">(\d*)</span><span class="u[^"]*">([^<]*)</span></li>', h)
        for tit_h, anno_h, stato_h in righe:
            n_nota = re.findall(r'data-n="(\d+)"', tit_h)
            tit = testo(re.sub(r"<sup.*?</sup>", "", tit_h)).strip()
            o = mie.get(pt(tit))
            if not o:
                non_contr += 1
                continue
            # USA
            conti["usa"] += 1
            su = R.stato_opera(o, "us", OGGI, mpf, reg_op.get("usa", {}))
            mm = re.match(r"(libero dal|free since|dal|from) (\d{4})", stato_h.strip())
            if mm and mm.group(1) in ("libero dal", "free since"):
                pagina = ("si", int(mm.group(2)))
            elif mm:
                pagina = ("dal", int(mm.group(2)))
            else:
                pagina = ("ver", None)
            regola = ("si", None) if su["s"] == "si" else ("dal", su.get("y")) if su["s"] == "dal" else ("ver", None)
            # decisione ancora aperta (le «474 opere», docs/registro-prove.md): Già pubblici non chiede la seconda fonte se
            # l'opera è libera in Europa, le schede sì. Si conta a parte, non è un errore.
            vv = (reg_op.get("usa", {}) or {}).get(o.get("q"))
            if pagina[0] == "ver" and su["s"] == "si" and o.get("y") is not None and not o.get("antica") \
                    and R.libera_ue_opera(o, OGGI) and not (vv and vv[0] is not None):
                conti["aperta"] = conti.get("aperta", 0) + 1
                continue
            if pagina[0] != regola[0] or (pagina[0] == "dal" and pagina[1] != regola[1]):
                errori.append(f"{nome_p}: «{tit}» negli USA la scheda dice «{stato_h}», Già pubblici (stato_opera) dice {su['s']} {su.get('y') or ''} ({su['r']})")
            # Europa: coautore morto dopo l'autore → la scheda deve dirlo, con la stessa data
            se = R.stato_opera(o, "it", OGGI, mpf, reg_op.get("usa", {}))
            if se["s"] == "dal" and se.get("y", 0) > R.anno_libero(D, "it"):
                conti["coautori"] += 1
                testi_note = [testo(note[int(k) - 1]) for k in n_nota if 0 < int(k) <= len(note)]
                if not any(str(se["y"]) in t for t in testi_note):
                    errori.append(f"{nome_p}: «{tit}» per la regola per opera è libera in Italia dal {se['y']} (coautori), la scheda non lo dice")

    if stampa:
        print(f"6. Stati scritti sulle pagine: {conti['pagine']} schede; controllati {conti['paesi']} paesi, {conti['intestazioni']} intestazioni, "
              f"{conti['note']} note, {conti['usa']} opere negli USA ({conti.get('aperta', 0)} con la decisione USA ancora aperta), {conti['coautori']} opere con coautori più tardi; "
              f"autori con l'anno di morte da verificare: {conti.get('incerti', 0)}; contro le regole: {len(errori)}; non controllabili: {non_contr}")
        for e in errori[:40]:
            print("   ", e)
    return errori


def controlla_liste(stampa=True):
    """Liste per anno e calendario contro il registro unico: l'anno di morte deve essere quello deciso
    (regole.morte_dal_registro), e ogni autore deve stare nella lista del suo anno. Radar, pagine dell'anno, home e schede
    leggono le liste: se le liste tornano, tornano anche loro (22/11/2026)."""
    reg = (_l(RADICE / "data" / "registro" / "autori.json", {}) or {}).get("autori", {})
    anno_ue = R.morti_liberi_nel(OGGI, "it")
    errori, n = [], 0
    for f in sorted(glob.glob(str(RADICE / "data" / "[0-9][0-9][0-9][0-9].json")) + glob.glob(str(RADICE / "data" / "es-[0-9][0-9][0-9][0-9].json"))):
        nome = Path(f).stem
        tipo, anno_l = ("es" if nome.startswith("es-") else "it"), int(nome[-4:])
        for a in (_l(f, {}) or {}).get("autori", []):
            m_l = re.match(r"-?\d+", str(a.get("morte") or ""))
            if not m_l:
                continue
            n += 1
            m_l = int(m_l.group())
            m, inc = R.morte_dal_registro(a.get("wikidata"), m_l, reg, anno_ue)
            if inc:   # fonti in disaccordo: resta l'anno della lista finché non è verificato
                continue
            if m != m_l:
                errori.append(f"lista {nome}: {a.get('nome')} morto nel {m_l}, il registro dice {m}")
            elif R.anno_libero(m, tipo) != anno_l:
                errori.append(f"lista {nome}: {a.get('nome')} (morte {m}) dovrebbe stare nella lista {R.anno_libero(m, tipo)}")
    for f in sorted(glob.glob(str(RADICE / "data" / "anniversari-[0-9][0-9][0-9][0-9].json"))):
        for v in (_l(f, {}) or {}).get("voci", []):
            if v.get("tipo") == "morte" and v.get("qid") in reg:
                n += 1
                m, inc = R.morte_dal_registro(v["qid"], v.get("anno"), reg, anno_ue)
                if not inc and m != v.get("anno"):
                    errori.append(f"calendario {Path(f).stem}: {v.get('nome')} morto nel {v.get('anno')}, il registro dice {m}")
    if stampa:
        print(f"7. Liste e calendario contro il registro unico: {n} autori; diversi: {len(errori)}")
        for e in errori[:20]:
            print("   ", e)
    return errori


if __name__ == "__main__":
    sys.exit(1 if (main() + controlla_liste()) else 0)
