# Campione di 30 autori «una fonte» delle liste 2027 (23/11/2026)

**Solo rapporto: nel sito non cambia niente.**

## Come è costruito (deciso prima di guardare i risultati)
- **Insieme:** autori della lista europea 2027 (`data/2027.json`) e spagnola 2027 (`data/es-2027.json`) con esito «una_fonte» nel registro (`data/registro/autori.json`): 395. Per tutti e 30 quella fonte è solo Wikidata.
- **Estrazione:** 30 a caso, `random.Random(20261123).sample(sorted(qid), 30)` (Python). Rifacendo il comando esce lo stesso elenco.
- **Verifica:** anno di morte da due fonti indipendenti da Wikidata (biblioteca nazionale, dizionario biografico, studio accademico, necrologio dell'epoca). Wikipedia conta solo se cita una fonte, e allora conta come una fonte sola.
- **Esiti:** confermato (2 fonti viste) / sbagliato (anno giusto con 2 fonti) / non trovato. Ho aggiunto «una fonte» e «in disaccordo» per non perdere informazione: per la regola contano come «non trovato».
- **Regola decisa prima:** 0 sbagliati → si controllano solo i più noti e quelli vicini al confine; 1 o più → si controllano tutti i 395 prima del 1° gennaio.
- **Ricerche:** circa 45 ricerche web, 1-3 per autore.

## Risultato: 5 confermati, 0 sbagliati, 1 in disaccordo, 8 con una fonte, 16 non trovati

| # | Autore (Wikidata) | Lista | Wikidata | Esito | Fonti |
|---|---|---|---|---|---|
| 1 | Witold Makowiecki (Q947959) | es-2027 | 1946 | confermato | [Univ. di Varsavia, Our Mythical Childhood](https://omc.obta.al.uw.edu.pl/myth-survey/item-export/137) («dies at the beginning of 1946»); [Bibliografia letteraria polacca](https://literarybibliography.eu/en/search/record/b1000002832161.html) (1902-1946) |
| 2 | C. Bernard Rutley (Q17624734) | 2027 | 1956 | confermato | [Encyclopedia of Science Fiction](https://www.sf-encyclopedia.com/entry/rutley_c_bernard) (20/9/1956); [Wikipedia](https://en.wikipedia.org/wiki/Cecil_Bernard_Rutley) (cita Kirkpatrick) |
| 3 | Annie Pike Greenwood (Q66817922) | 2027 | 1956 | confermato | [Necrologio Daily Herald 24/2/1956 (trascritto su Find a Grave)](https://www.findagrave.com/memorial/86333550/annie-amelia-greenwood); [SNAC, Church History Library](https://snaccooperative.org/view/31671799) (1880-1956) |
| 4 | John McClure (Q15998843) | 2027 | 1956 | confermato | [Encyclopedia of Oklahoma History](https://www.okhistory.org/publications/enc/entry?entry=MC012) (1893–1956); [Wikipedia](https://wiki.riteme.site/wiki/John_McClure_(poet)) (cita il Times-Picayune del 9/2/1956) |
| 5 | Ayako Eguchi (Q26776573) | es-2027 | 1946 | confermato | [Biblioteca nazionale della Dieta (NDL), voce d'autorità 1887-1946](https://ndlsearch.ndl.go.jp/en/books/R100000002-I000000617217); [scheda biografica](https://www.asahi-net.or.jp/~PB5H-OOTK/pages/SAKKA/e/eguchiayako.html) (29/12/1946) |
| 6 | Frederick Hadland Davis (Q87470685) | es-2027 | 1946 | **in disaccordo** | [Project Gutenberg, scheda autore «1882-1956»](https://www.gutenberg.org/etext/16043) contro Wikidata 1946. Nessuna seconda fonte trovata |
| 7 | Dagmar Klami (Q5490074) | 2027 | 1956 | una fonte | [Biblioteca nazionale finlandese](https://data.nationallibrary.fi/au/pn/000080420) (1899-1956) |
| 8 | Keith Bullen (Q6384140) | es-2027 | 1946 | una fonte | [Wikipedia](https://en.wikipedia.org/wiki/Keith_Bullen_(poet)) (30/7/1946, senza fonte per la data) |
| 9 | Edward Sperling (Q5345388) | es-2027 | 1946 | una fonte | [Wikipedia](https://en.wikipedia.org/wiki/Edward_Sperling) (22/7/1946, attentato al King David Hotel) |
| 10 | Agnes Grainger Stewart (Q4693046) | 2027 | 1956 | una fonte | [Wikipedia](https://en.wikipedia.org/wiki/Agnes_Grainger_Stewart) (25/9/1956, cita il registro civile scozzese) |
| 11 | José Pérez Hervás (Q106327389) | es-2027 | 1946 | una fonte | [Wikipedia](https://en.wikipedia.org/wiki/Jos%C3%A9_P%C3%A9rez_Herv%C3%A1s) (21/7/1946, cita studi Silva-Villar) |
| 12 | Alice B. Curtis (Q116486322) | 2027 | 1956 | una fonte | [Wikipedia](https://en.wikipedia.org/wiki/Alice_B._Curtis) (19/4/1956, cita The Alumnus, settembre 1956) |
| 13 | Cyril Clague (Q63089389) | es-2027 | 1946 | una fonte | [Wikipedia](https://en.wikipedia.org/wiki/Cyril_Clague) (28/7/1946, cita due necrologi del 1946, che non ho visto) |
| 14 | Joseph Ruscoll (Q139266904) | 2027 | 1956 | una fonte | [Wikipedia](https://en.wikipedia.org/wiki/Joseph_Ruscoll) (19/11/1956, cita il necrologio di Variety) |
| 15-30 | Miklós Vitéz (Q31190440), Roman Mohytych (Q12124024), Juan Abando Urrejola (Q12260932), Minnie E. Bond (Q115015736), Matti Lilja (Q17382212), Ana Maria (Q123857200), Mukhtar Shavlokhov (Q112085467), Q20483877 (senza nome in Wikidata), Ibrantina Cardona (Q136736462), Géza Buday (Q851311), Béla Arató (Q117252748), Lajos Jámbor poeta (Q1102368), T. E. Grattan-Smith (Q64685269), Bronius Stosiūnas (Q16446222), Muḥammad ʻAlī Unsī (Q108616921), Sabri Andrea (Q111098197) | — | — | non trovato | nessuna fonte con l'anno di morte. Per Jámbor esce solo un omonimo (pittore, 1884-1954) |

## Cosa significa
- **Decisione di Marco (23/11/2026):** il campione è inconcludente, non «0 sbagliati». I 395 non si controllano a mano: si fa un confronto automatico con Open Library e Project Gutenberg (scripts/confronta_una_fonte.py).
- **Per la regola decisa prima:** 0 sbagliati, quindi si controllano solo i più noti e quelli vicini al confine.
- **Il campione però dice poco:** 16 autori su 30 non si trovano nemmeno, e 8 hanno una fonte sola. Lo «0 sbagliati» viene quasi tutto da opere che non si possono verificare, non da conferme.
- **Davis è proprio un caso di confine:** se è morto nel 1956 e non nel 1946, non è libero in Spagna nel 2027 (lista es-2027 sbagliata) ma lo è in Europa nel 2027. Serve una seconda fonte (Library of Congress n91100021, VIAF 63191932).
- **Q20483877 non ha nome in Wikidata:** è in lista solo con il codice. Un'«opera» o un autore senza nome non dovrebbe stare in una lista pubblica.
