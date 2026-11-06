import urllib.request,re,html
r=urllib.request.Request("https://www.law.cornell.edu/uscode/text/17/104A",headers={"User-Agent":"Mozilla/5.0 PublicDomainRadar research"})
t=urllib.request.urlopen(r,timeout=60).read().decode("utf8","ignore")
t=re.sub(r"(?s)<(script|style).*?</\1>","",t); t=re.sub(r"<[^>]+>"," ",t); t=html.unescape(re.sub(r"\s+"," ",t))
print("LUNGHEZZA",len(t))
i=t.find("(h) Definitions")
print(t[i:i+5200] if i>=0 else "NO (h)")
