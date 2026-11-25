"""Controllo grafico (25/11/2026): in ogni pagina misura la distanza tra la linea del titolo di sezione (.sh) e il primo contenuto sotto,
a 390 e 1440 px, e segnala quelle sotto i 18 px. Si lancia con il sito servito in locale su http://localhost:8765/ (python3 -m http.server 8765)."""
import asyncio,sys
from playwright.async_api import async_playwright
PAG=["","en/","pubblico-dominio-2027/","pubblico-dominio/","pubblico-dominio/italia/","pubblico-dominio/spagna/","pubblico-dominio/stati-uniti/","come-funziona/","shop/","en/shop/","gia-pubblici/","calendario/2027/","autore/bertolt-brecht/"]
JS="""()=>{const out=[];document.querySelectorAll('.sh').forEach(sh=>{const b=sh.getBoundingClientRect();if(!b.height)return;let n=sh.nextElementSibling;while(n&&(!n.getBoundingClientRect().height||getComputedStyle(n).display==='none'))n=n.nextElementSibling;if(!n)return;
 // primo elemento con testo o immagine dentro n
 const walker=[...n.querySelectorAll('*')].concat([n]).filter(e=>{const r=e.getBoundingClientRect();return r.height>0&&(e.childElementCount===0)&&(e.textContent.trim()||e.tagName==='IMG')});
 const top=Math.min(...walker.map(e=>e.getBoundingClientRect().top));
 const gap=Math.round(top-b.bottom); const t=(sh.querySelector('h2')||sh).innerText.slice(0,40);
 out.push([t,gap]);});return out}"""
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    for w in (390,1440):
      for u in PAG:
        pg=await b.new_page(viewport={"width":w,"height":900})
        await pg.goto("http://localhost:8765/"+u,wait_until="networkidle"); await pg.wait_for_timeout(1500)
        await pg.evaluate("(async()=>{for(let y=0;y<document.body.scrollHeight;y+=700){scrollTo(0,y);await new Promise(r=>setTimeout(r,40))}scrollTo(0,0)})()"); await pg.wait_for_timeout(800)
        r=await pg.evaluate(JS)
        bad=[x for x in r if x[1]<18]
        if bad: print(w,u or "home",bad)
        await pg.close()
    await b.close()
asyncio.run(m())
