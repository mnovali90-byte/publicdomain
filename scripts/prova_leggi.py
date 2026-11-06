import urllib.request,re,html
def get(u):
    r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 PublicDomainRadar research"})
    try: t=urllib.request.urlopen(r,timeout=60).read().decode("utf8","ignore")
    except Exception as e: return "ERR "+str(e)
    t=re.sub(r"(?s)<(script|style).*?</\1>","",t); t=re.sub(r"<[^>]+>"," ",t); t=html.unescape(re.sub(r"\s+"," ",t)); return t
for sez,ini,lung in (("304","(a) Copyrights in Their First",9000),("303","(a) Copyright in a work created",2500),("104A","(a) Automatic Protection",6500)):
    u=f"https://www.law.cornell.edu/uscode/text/17/{sez}"
    t=get(u); i=t.find(ini) if not t.startswith("ERR") else 0
    print("=====",sez,u); print(t[max(i,0):max(i,0)+lung]); print()
