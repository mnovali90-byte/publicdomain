"""Scarica i caratteri del sito da Google Fonts e li salva in assets/fonts/ (20/11/2026).
Motivo: servirli dal nostro dominio, così l'indirizzo IP di chi visita non arriva a Google (privacy) e la pagina non
dipende da un altro server. Licenza dei tre caratteri: SIL Open Font License (si possono ridistribuire).
Scrive i file .woff2 (solo alfabeti latini) e assets/fonts/fonts.css con le regole @font-face."""
import re, urllib.request
from pathlib import Path

R = Path(__file__).resolve().parent.parent
OUT = R / "assets" / "fonts"
CSS = ("https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700;800;900"
       "&family=Instrument+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
TENERE = ("latin", "latin-ext")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    css = urllib.request.urlopen(urllib.request.Request(CSS, headers=UA), timeout=60).read().decode()
    blocchi = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{.*?\})", css, re.S)
    out, n = [], 0
    for sottoinsieme, b in blocchi:
        if sottoinsieme not in TENERE:
            continue
        fam = re.search(r"font-family:\s*'([^']+)'", b).group(1)
        peso = re.search(r"font-weight:\s*(\d+)", b).group(1)
        url = re.search(r"url\((https://[^)]+\.woff2)\)", b).group(1)
        nome = f"{fam.lower().replace(' ', '-')}-{peso}-{sottoinsieme}.woff2"
        dati = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        (OUT / nome).write_bytes(dati)
        out.append(f"/* {fam} {peso} {sottoinsieme} — SIL Open Font License */\n" + b.replace(url, f"/assets/fonts/{nome}"))
        n += 1
    (OUT / "fonts.css").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("file scaricati:", n)


if __name__ == "__main__":
    main()
