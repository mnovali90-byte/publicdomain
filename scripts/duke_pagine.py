"""Scarica le pagine Public Domain Day della Duke (2019-2026) come riferimento esterno per lo Storico USA. Solo misura."""
import pathlib, time, urllib.request
UA = "PublicDomainTool/0.1 (https://github.com/mnovali90-byte/publicdomain)"
out = pathlib.Path("docs/stima-sito/duke"); out.mkdir(parents=True, exist_ok=True)
for anno in range(2019, 2027):
    for u in (f"https://web.law.duke.edu/cspd/publicdomainday/{anno}/", f"https://cspd.law.duke.edu/publicdomainday/{anno}/"):
        try:
            h = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=60).read().decode("utf-8", "replace")
            (out / f"{anno}.html").write_text(h, encoding="utf-8"); print(anno, len(h)); break
        except Exception as e:
            print(anno, u, e)
    time.sleep(2)
