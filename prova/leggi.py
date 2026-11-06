import urllib.request,re,html
r=urllib.request.Request("https://www.law.cornell.edu/uscode/text/17/104A",headers={"User-Agent":"Mozilla/5.0 PublicDomainRadar research"})
t=urllib.request.urlopen(r,timeout=60).read().decode("utf8","ignore")
t=re.sub(r"(?s)<(script|style).*?</\1>","",t); t=re.sub(r"<[^>]+>"," ",t); t=html.unescape(re.sub(r"\s+"," ",t))
for ini,l in (("(6) Restored work",1800),("(8) Eligible country",900),("(9) Reliance party",300),("(4) Date of restoration",900),("(3) Date of adherence",700)):
    i=t.find(ini); print("=====",ini); print(t[i:i+l] if i>=0 else "NON TROVATO"); print()
