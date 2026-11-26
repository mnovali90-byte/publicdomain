import json, verifica
L=verifica.tutti(); D=verifica.D
import lotto4; L4=set(lotto4.L)
camp=json.load(open(verifica.P+'campione.json'))
EN=json.load(open('/tmp/thema_en.json')); IT=json.load(open('/tmp/thema_it.json'))
NOMI={"WPen":"Wikipedia inglese","WPit":"Wikipedia italiana","enwd":"Wikidata (descrizione inglese)","itwd":"Wikidata (descrizione italiana)","g":"Wikidata: genere","f":"Wikidata: forma","a":"Wikidata: argomento","l":"Wikidata: luogo della storia","p":"Wikidata: periodo","t":"Wikidata: tipo di opera"}
NOMI.update({"O:WPen":"Opera originale: Wikipedia inglese","O:WPit":"Opera originale: Wikipedia italiana","O:enwd":"Opera originale: Wikidata","O:itwd":"Opera originale: Wikidata","O:g":"Opera originale: Wikidata, genere","O:a":"Opera originale: Wikidata, argomento",
 "OL:a":"Open Library: argomenti","OL:l":"Open Library: luoghi","OL:p":"Open Library: periodi","OL:d":"Open Library: descrizione","WS":"Wikisource tedesca: categorie","GND:c":"Biblioteca nazionale tedesca","GND:f":"Biblioteca nazionale tedesca","GND:t":"Biblioteca nazionale tedesca","PI":"Wikidata: pubblicato in"})
out=[]
for i,c in enumerate(camp):
    q=c['q']; d=D[q]; st,cod,alt,nota=L[q]; wd=f"https://www.wikidata.org/wiki/{q}"; fonti=[]
    for l in ("it","en"):
        w=d.get("wikipedia_"+l)
        if w: fonti.append({"k":"WP"+l,"nome":NOMI["WP"+l],"testo":w["testo"].strip(),"url":w["fonte"]})
    for l in ("it","en"):
        x=d.get("descrizione_wikidata_"+l)
        if x: fonti.append({"k":l+"wd","nome":NOMI[l+"wd"],"testo":x,"url":wd})
    r2=verifica.D2.get(q,{}); o=r2.get("originale")
    if o:
        for l in ("it","en"):
            w=o.get("wikipedia_"+l)
            if w: fonti.append({"k":"O:WP"+l,"nome":NOMI["O:WP"+l],"testo":w["testo"].strip(),"url":w["fonte"]})
        for l in ("it","en"):
            x=o.get("descrizione_wikidata_"+l)
            if x: fonti.append({"k":"O:"+l+"wd","nome":NOMI["O:"+l+"wd"]+" ("+o["titolo"]+")","testo":x,"url":o["fonte"]})
    if r2.get("openlibrary"):
        ol=r2["openlibrary"]; t="Argomenti: "+"; ".join(ol["argomenti"])+(" — Luoghi: "+"; ".join(ol["luoghi"]) if ol["luoghi"] else "")+(" — Periodi: "+"; ".join(ol["periodi"]) if ol["periodi"] else "")+(" — "+ol["descrizione"] if ol.get("descrizione") else "")
        for k in ("OL:a","OL:l","OL:p","OL:d"): fonti.append({"k":k,"nome":"Open Library","testo":t,"url":ol["fonte"]}) if k=="OL:a" else None
    if r2.get("wikisource"): fonti.append({"k":"WS","nome":"Wikisource tedesca: categorie","testo":"; ".join(r2["wikisource"]["categorie"]),"url":r2["wikisource"]["fonte"]})
    if r2.get("gnd"):
        g=r2["gnd"]; fonti.append({"k":"GND","nome":"Biblioteca nazionale tedesca (GND)","testo":"; ".join(g["categorie"]+g["forma"]+g["argomenti"]),"url":g["fonte"]})
    dati=[{"nome":n,"valori":d[k]} for k,n in (("tipo","tipo"),("generi","genere"),("forma","forma"),("argomenti","argomento"),("luogo_narrazione","luogo della storia"),("periodo","periodo")) if d.get(k)]
    def url_of(f):
        k={"OL:l":"OL:a","OL:p":"OL:a","OL:d":"OL:a","GND:c":"GND","GND:f":"GND","GND:t":"GND"}.get(f,f)
        if k=="PI" or k.startswith("O:") and k[2:] in ("g","a","f","l","p","t"): return (o or {}).get("fonte",wd) if k.startswith("O:") else wd
        return next((x["url"] for x in fonti if x["k"]==k), wd)
    out.append({"q":q,"n":i,"gruppo":"famose" if i<100 else "meno note","titolo":c["titolo_it"] or c["titolo_en"],
      "titolo_en":c["titolo_en"] if c["titolo_it"] and c["titolo_it"]!=c["titolo_en"] else "",
      "autori":", ".join(a[1] for a in c["autori"] if not a[1].startswith("http")),"anno":c["anno"],
      "stato":{"S":"sicuro","I":"da decidere","N":"nessun testo"}[st],
      "codici":[{"c":k,"it":IT.get(k,""),"en":EN[k],"fonte":NOMI[f],"frase":fr,"url":url_of(f)} for k,f,fr in cod],
      "alternative":[{"c":k,"it":IT.get(k,""),"en":EN[k]} for k in alt],"nota":nota,"aggiornata":q in L4,"fonti":fonti,"wikidata":dati,"wikidata_url":wd})
json.dump(out,open('opere.json','w'),ensure_ascii=False)
print(len(out))
