"""Controllo contro l'invenzione (decisione di Marco, 23/11/2026). NON CAMBIA IL SITO.

Per ogni voce di docs/ricerca-web/risultati.json apre il «link» e cerca la «citazione» (frase esatta e breve).
Esiti: «trovata», «non trovata», «non verificabile in automatico» (il sito blocca, non risponde, o è un PDF/scansione
che non si legge). Il confronto ignora maiuscole, spazi e a capo, tipi di virgolette, apostrofi e trattini.
Scrive data/registro/controllo_citazioni.json {indice: {"qid", "link", "esito", "motivo"}} e
docs/ricerca-web/controllo-citazioni.md. L'incrocio (regole.fatti_da_ricerca, via extra_da_file) non usa le voci
«non trovata» né quelle senza citazione."""
import json, re, subprocess, sys, tempfile, time, unicodedata, urllib.request, html
from pathlib import Path

R = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "PublicDomainRadar/1.0 (controllo citazioni; https://github.com/mnovali90-byte/publicdomain)"}


def norm(t):
    t = unicodedata.normalize("NFKC", html.unescape(t or "")).lower()
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("«", '"'), ("»", '"'), ("–", "-"), ("—", "-"), ("­", ""), (" ", " ")):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).strip()


def testo(url):
    req = urllib.request.Request(url.replace("\\", "/"), headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        dati, tipo = r.read(), (r.headers.get("Content-Type") or "").lower()
    if "pdf" in tipo or dati[:5] == b"%PDF-":
        with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
            f.write(dati); f.flush()
            try:
                return subprocess.run(["pdftotext", "-q", f.name, "-"], capture_output=True, timeout=120).stdout.decode("utf-8", "replace"), "pdf"
            except Exception:
                return None, "pdf non leggibile"
    t = dati.decode("utf-8", "replace")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", " ", t), "html"


def main():
    voci = json.load(open(R / "docs" / "ricerca-web" / "risultati.json", encoding="utf-8"))["voci"]
    out, cache = {}, {}
    for i, v in enumerate(voci):
        c, link = v.get("citazione"), v.get("link")
        if not c:
            out[str(i)] = {"qid": v.get("qid"), "link": link, "esito": "senza citazione", "motivo": "campo obbligatorio mancante"}
            continue
        if link not in cache:
            try:
                cache[link] = testo(link)
            except Exception as e:
                cache[link] = (None, str(e)[:120])
            time.sleep(1)
        t, info = cache[link]
        if t is None or len(t.strip()) < 200:
            esito, motivo = "non verificabile in automatico", info if t is None else "pagina quasi vuota (il sito blocca o carica il testo dopo)"
        elif norm(c) in norm(t):
            esito, motivo = "trovata", info
        else:
            esito, motivo = "non trovata", info
        out[str(i)] = {"qid": v.get("qid"), "titolo": v.get("titolo"), "link": link, "esito": esito, "motivo": motivo}
    json.dump({"fatto": time.strftime("%Y-%m-%d"), "voci": out},
              open(R / "data" / "registro" / "controllo_citazioni.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from collections import Counter
    n = Counter(x["esito"] for x in out.values())
    md = ["# Controllo delle citazioni (" + time.strftime("%Y-%m-%d") + ")", "",
          "Script `scripts/controlla_citazioni.py`: apre ogni link di docs/ricerca-web/risultati.json e cerca la citazione.", ""]
    md += [f"- {k}: {v}" for k, v in sorted(n.items())] + ["", "| # | Opera | Esito | Motivo | Link |", "|---|---|---|---|---|"]
    for k, x in out.items():
        if x["esito"] != "trovata":
            md.append(f"| {k} | {x.get('titolo')} ({x['qid']}) | {x['esito']} | {x['motivo']} | {x['link']} |")
    (R / "docs" / "ricerca-web" / "controllo-citazioni.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(dict(n))


if __name__ == "__main__":
    main()
