"""Schede da condividere (immagini per storie e post), generate nel browser dal calendario.
Fornisce: dati_scheda(v, lang, ...) per ogni voce, CSS, HTML della finestra e JS."""
import html
import json
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent

TESTI = {
    "it": {"crea": "Crea scheda →", "titolo": "Scheda da condividere", "storia": "Storia 9:16", "post": "Post 4:5",
           "condividi": "Condividi", "scarica": "Scarica immagine", "chiudi": "Chiudi", "cal": "Calendario {a}",
           "url": "publicdomainradar.com/calendario", "suggerimento": "Da telefono: Condividi → Instagram → Storia."},
    "en": {"crea": "Create card →", "titolo": "Shareable card", "storia": "Story 9:16", "post": "Post 4:5",
           "condividi": "Share", "scarica": "Download image", "chiudi": "Close", "cal": "Calendar {a}",
           "url": "publicdomainradar.com/en/calendar", "suggerimento": "On your phone: Share → Instagram → Story."},
}


def cap(s):
    return s[:1].upper() + s[1:] if s else s


def dati_scheda(v, lang, t, mesi, nome, autore, sc):
    """Dizionario con il testo della scheda per questa voce (solo voci con data completa)."""
    if v["tipo"] == "prima edizione":
        gen = cap((sc.get("generi") or [""])[0])
        aut = autore
        if gen and aut:
            d = f'{gen}{t["di"]}{aut}'
        else:
            d = gen or (cap(t["di"].strip()) + " " + aut if aut else "")
        vita = str(v["anno"])
    else:
        d = cap(sc.get("desc") or "")
        if sc.get("nobel"):
            d += "\n" + t["nobel"].format(y=sc["nobel"])
        vita = f'{sc["nato"]} – {sc["morto"]}' if sc.get("nato") and sc.get("morto") else ""
    return {"t": t["tipi"][v["tipo"]], "n": t["anni"].format(n=v["anni"]), "g": str(v["giorno"]),
            "m": mesi[v["mese"] - 1], "nome": nome, "d": d, "v": vita, "id": f'{v["tipo"]}-{v["qid"]}'}


CSS = """
dialog#sd{border:0;padding:0;background:#F7F7F4;color:#0C0C10;width:min(440px,calc(100vw - 24px));max-height:calc(100vh - 24px);overflow:auto}
dialog#sd::backdrop{background:rgba(12,12,16,.72)}
#sd .dh{display:flex;justify-content:space-between;align-items:center;padding:14px 16px 8px}
#sd .dh b{font:500 12px var(--mono);letter-spacing:.12em;text-transform:uppercase}
#sd .dh button{font:500 12px var(--mono);letter-spacing:.08em;text-transform:uppercase;background:none;border:0;cursor:pointer;color:#0C0C10;padding:6px 0}
#sd .fm{display:flex;gap:8px;padding:0 16px 12px}
#sd .fm button{flex:1;font:500 12px var(--mono);letter-spacing:.08em;text-transform:uppercase;padding:10px;border:2px solid #0C0C10;background:none;color:#0C0C10;cursor:pointer}
#sd .fm button[aria-pressed=true]{background:#0C0C10;color:#F7F7F4}
#sd .cv{padding:0 16px;display:flex;justify-content:center}
#sd canvas{display:block;max-width:100%;max-height:56vh;width:auto;height:auto;box-shadow:0 0 0 1px rgba(12,12,16,.15)}
#sd .db{display:flex;gap:8px;padding:14px 16px 6px;flex-wrap:wrap}
#sd .db button{flex:1;min-width:140px;border-color:#0C0C10;color:#0C0C10;background:none}
#sd .db button.p{background:#FF4326;border-color:#FF4326;color:#0C0C10}
#sd .sg{padding:4px 16px 16px;font-size:13px;color:#5C5C66;margin:0}
.crea{font:500 12px var(--mono);letter-spacing:.06em;text-transform:uppercase;background:none;border:0;padding:4px 0;color:var(--vt);cursor:pointer;text-decoration:underline;text-underline-offset:3px;text-align:left}
"""


def finestra(lang):
    x = TESTI[lang]
    e = html.escape
    return (f'<dialog id="sd" aria-label="{e(x["titolo"])}"><div class="dh"><b>{e(x["titolo"])}</b>'
            f'<button type="button" id="sdx">{e(x["chiudi"])}</button></div>'
            f'<div class="fm"><button type="button" data-f="s" aria-pressed="true">{e(x["storia"])}</button>'
            f'<button type="button" data-f="p" aria-pressed="false">{e(x["post"])}</button></div>'
            f'<div class="cv"><canvas id="sdc"></canvas></div>'
            f'<div class="db"><button type="button" class="btn p" id="sds" hidden>{e(x["condividi"])}</button>'
            f'<button type="button" class="btn" id="sdd">{e(x["scarica"])}</button></div>'
            f'<p class="sg" id="sdg" hidden>{e(x["suggerimento"])}</p></dialog>')


JS = r"""
(function(){
var LOGO=__LOGO__, X=__X__;
var INK="#0C0C10",CARTA="#F7F7F4",VERM="#FF4326",MUTO="#5C5C66";
var DISP='"Big Shoulders Display",Impact,"Arial Narrow",sans-serif',MONO='"DM Mono",ui-monospace,Menlo,monospace',TXT='"Instrument Sans",system-ui,sans-serif';
var dlg=document.getElementById("sd"),cv=document.getElementById("sdc"),cur=null,fmt="s",logoImg=null;
if(!dlg||!dlg.showModal)return;
function carica(){return new Promise(function(ok){
  if(logoImg)return ok();
  var i=new Image();i.onload=function(){logoImg=i;ok()};i.onerror=ok;
  i.src="data:image/svg+xml;charset=utf-8,"+encodeURIComponent(LOGO);
})}
function fonts(){
  if(!document.fonts||!document.fonts.load)return Promise.resolve();
  return Promise.all(['900 100px "Big Shoulders Display"','500 20px "DM Mono"','400 20px "Instrument Sans"'].map(function(f){return document.fonts.load(f,"Aa0").catch(function(){})}));
}
function spaced(c,s,x,y,ls,right){
  var cw=[],w=0,i;for(i=0;i<s.length;i++){cw[i]=c.measureText(s[i]).width;w+=cw[i]+(i<s.length-1?ls:0)}
  if(right)x-=w;for(i=0;i<s.length;i++){c.fillText(s[i],x,y);x+=cw[i]+ls}return w;
}
function justify(c,s,x,y,width){
  var cw=[],sum=0,i;for(i=0;i<s.length;i++){cw[i]=c.measureText(s[i]).width;sum+=cw[i]}
  var ls=s.length>1?(width-sum)/(s.length-1):0;for(i=0;i<s.length;i++){c.fillText(s[i],x,y);x+=cw[i]+ls}
}
function wrap(c,text,maxW){
  var ws=text.split(/\s+/),lines=[],l="";
  ws.forEach(function(w){var t=l?l+" "+w:w;if(l&&c.measureText(t).width>maxW){lines.push(l);l=w}else l=t});
  if(l)lines.push(l);return lines;
}
function balanced(c,text,maxW){
  var n=wrap(c,text,maxW).length,lo=0,hi=maxW,k;
  for(k=0;k<14;k++){var m=(lo+hi)/2;if(wrap(c,text,m).length>n)lo=m;else hi=m}
  return wrap(c,text,hi+1);
}
function disegna(d,f){
  var W=1080,H=f==="s"?1920:1350,sc=f==="s"?1:.8,M=80,c=cv.getContext("2d");
  cv.width=W;cv.height=H;
  c.fillStyle=CARTA;c.fillRect(0,0,W,H);c.textBaseline="alphabetic";
  /* logo */
  var lw=240,lh=lw*120/215.67;
  if(logoImg)c.drawImage(logoImg,M,M,lw,lh);
  c.fillStyle=MUTO;c.font='500 17px '+MONO;
  var k=lw/215.67,sy=M+lh+30,p=[[0,61.42,"PUBLIC"],[74.58,137.65,"DOMAIN"],[152.82,215.67,"RADAR"]];
  p.forEach(function(q){justify(c,q[2],M+q[0]*k,sy,(q[1]-q[0])*k)});
  c.font='500 28px '+MONO;spaced(c,X.cal.toUpperCase(),W-M,M+34,4,true);
  /* piede */
  var fy=H-M-62;c.fillStyle=INK;c.fillRect(M,fy,W-2*M,6);
  c.fillStyle=MUTO;c.font='500 30px '+MONO;spaced(c,X.url.toUpperCase(),M,H-M+4,3,false);
  /* misure */
  var maxW=W-2*M,top=M+lh+110,bot=fy-50;
  var nf=400*sc,mf=100*sc,tf=36*sc,df=48*sc,vf=36*sc;
  c.font='900 '+nf+'px '+DISP;var nm=c.measureText(d.g),asc=nm.actualBoundingBoxAscent||nf*.72;
  var ns=153*sc,nl;
  for(;;){c.font='900 '+ns+'px '+DISP;nl=balanced(c,d.nome.toUpperCase(),maxW);
    if(nl.length<=2||(ns<=100*sc&&nl.length<=3)||ns<=56*sc)break;ns-=6}
  c.font='400 '+df+'px '+TXT;
  var dl=[];(d.d||"").split("\n").forEach(function(s){dl=dl.concat(wrap(c,s,maxW))});dl=dl.slice(0,4);
  var g1=44*sc,th=60*sc,g2=70*sc,g3=34*sc,g4=22*sc;
  var total=asc+g1+th+g2+nl.length*ns*.94+(dl.length?g3+dl.length*df*1.38:0)+(d.v?g4+vf:0);
  var y=top+Math.max(0,(bot-top-total)/2);
  /* cerchio */
  c.fillStyle=VERM;c.beginPath();c.arc(W+20,y+asc*.42,250*sc,0,Math.PI*2);c.fill();
  /* data */
  c.fillStyle=INK;c.font='900 '+nf+'px '+DISP;c.fillText(d.g,M,y+asc);
  var gw=c.measureText(d.g).width;c.font='900 '+mf+'px '+DISP;c.fillText(d.m.toUpperCase(),M+gw+30*sc,y+asc);
  y+=asc+g1;
  /* tipo */
  c.font='500 '+tf+'px '+MONO;var tt=d.t.toUpperCase(),tw=spaced({measureText:function(s){return c.measureText(s)},fillText:function(){}},tt,0,0,5,false);
  c.fillStyle=INK;c.fillRect(M,y,tw+44*sc,th);c.fillStyle=CARTA;spaced(c,tt,M+22*sc,y+th*.7,5,false);
  c.fillStyle=INK;spaced(c,d.n.toUpperCase(),M+tw+44*sc+28*sc,y+th*.7,5,false);
  y+=th+g2;
  /* nome */
  c.font='900 '+ns+'px '+DISP;c.fillStyle=INK;
  nl.forEach(function(s,i){c.fillText(s,M,y+ns*.8+i*ns*.94)});y+=nl.length*ns*.94;
  /* descrizione */
  if(dl.length){y+=g3;c.font='400 '+df+'px '+TXT;c.fillStyle=INK;dl.forEach(function(s,i){c.fillText(s,M,y+df*.95+i*df*1.38)});y+=dl.length*df*1.38}
  if(d.v){y+=g4;c.font='500 '+vf+'px '+MONO;c.fillStyle=MUTO;spaced(c,d.v,M,y+vf*.85,4,false)}
}
function ridisegna(){Promise.all([carica(),fonts()]).then(function(){disegna(cur,fmt)})}
function blob(){return new Promise(function(ok){cv.toBlob(ok,"image/png")})}
function nomeFile(){return "pdr-"+cur.id+"-"+(fmt==="s"?"storia":"post")+".png"}
[].slice.call(document.querySelectorAll(".crea")).forEach(function(b){
  b.addEventListener("click",function(){
    cur=JSON.parse(b.closest(".ev").dataset.sc);fmt="s";
    [].slice.call(dlg.querySelectorAll(".fm button")).forEach(function(x){x.setAttribute("aria-pressed",x.dataset.f==="s"?"true":"false")});
    var can=false;try{can=!!(navigator.canShare&&navigator.canShare({files:[new File([""],"a.png",{type:"image/png"})]}))}catch(e){}
    document.getElementById("sds").hidden=!can;document.getElementById("sdg").hidden=!can;
    dlg.showModal();ridisegna();
  });
});
[].slice.call(dlg.querySelectorAll(".fm button")).forEach(function(b){
  b.addEventListener("click",function(){fmt=b.dataset.f;
    [].slice.call(dlg.querySelectorAll(".fm button")).forEach(function(x){x.setAttribute("aria-pressed",x===b?"true":"false")});ridisegna()});
});
document.getElementById("sdx").addEventListener("click",function(){dlg.close()});
dlg.addEventListener("click",function(e){if(e.target===dlg)dlg.close()});
document.getElementById("sdd").addEventListener("click",function(){
  blob().then(function(bl){var a=document.createElement("a");a.href=URL.createObjectURL(bl);a.download=nomeFile();document.body.appendChild(a);a.click();a.remove();setTimeout(function(){URL.revokeObjectURL(a.href)},4000)});
});
document.getElementById("sds").addEventListener("click",function(){
  blob().then(function(bl){var f=new File([bl],nomeFile(),{type:"image/png"});return navigator.share({files:[f]})}).catch(function(){});
});
})();
"""


def js(lang, anno):
    svg = (RADICE / "assets" / "logo-pdr.svg").read_text(encoding="utf-8").replace("currentColor", "#0C0C10")
    x = TESTI[lang]
    dati = {"cal": x["cal"].format(a=anno), "url": x["url"]}
    return "<script>" + JS.replace("__LOGO__", json.dumps(svg)).replace("__X__", json.dumps(dati)) + "</script>"
