# Casi di riferimento

Approvati da Marco il 22/11/2026 come prima base. I casi stanno anche in `data/casi_riferimento.json` e `scripts/prova_regole.py` li controlla a ogni giro.

Ogni caso è un'opera o un autore reale con il risultato atteso e una fonte, che sia una legge, una sentenza o un'istituzione. Servono a controllare che le regole di `scripts/regole.py` diano il risultato giusto, e non solo lo stesso risultato in Python e nel browser. Senza fonte, un caso non entra. Quando le fonti non sono d'accordo, il caso lo dice e l'atteso è solo ciò su cui concordano.

L'ultima colonna dice cosa risponde oggi il sito (Già pubblici, regole attuali, prova del 22/11/2026).

| # | Caso | Paese | Atteso | Fonte | Oggi il sito dice |
|---|---|---|---|---|---|
| 1 | Il piccolo principe (Saint-Exupéry, morto nel 1944) | Italia | libero dal 1° gennaio 2015 | Tribunale di Milano n. 2826/2021; Corte d'appello di Milano n. 2994/2022 | libero ✓ |
| 2 | Il piccolo principe | Belgio e resto d'Europa (noi: Germania, Regno Unito) | libero dal 1° gennaio 2015 | Bibliothèque royale de Belgique e altri, comunicato news.belgium.be del 5/2/2015 | libero ✓ |
| 3 | Il piccolo principe («mort pour la France») | Francia | **non libero nel 2026**; data esatta da verificare. Fonti autorevoli indicano il 1° gennaio 2033: il Syndicat national de l'édition dice «protetto fino al 31/12/2032», indicazione di Marco, non ancora riletta da me alla fonte. «2032» in Livres Hebdo e Guichet du savoir è probabilmente l'ultimo anno protetto. Gli eredi nel 2013 dicevano 2035 (La Libre). Il 2045 non si adotta | SNE; Livres Hebdo; Guichet du savoir; La Libre 15/4/2013 | «da verificare» ✓ |
| 4 | Opere di Federico García Lorca (morto nel 1936) | Spagna | libere dal 1° gennaio 2017 (80 anni: morto prima del 1987) | Biblioteca Nacional de España, comunicato del 2/1/2017 (EFE, The Objective) | libere ✓ |
| 5 | The Great Gatsby (pubblicato nel 1925) | USA | libero dal 1° gennaio 2021 (95 anni) | Duke University, Center for the Study of the Public Domain, «Public Domain Day 2021» | libero ✓ |
| 6 | Mein Kampf (Hitler, morto nel 1945) | Germania | libero dal 1° gennaio 2016 | Institut für Zeitgeschichte di Monaco; Bundeszentrale für politische Bildung | **«non determinato» ✗** (vedi sotto) |
| 7 | Beatrix Potter (morta nel 1943), opere pubblicate in vita | Regno Unito | libere dal 1° gennaio 2014 | UCL Copyright, 2016 | libere ✓ (La storia di Peter Coniglio) |
| 8 | Beatrix Potter, Kitty-in-Boots (inedito, pubblicato nel 2016) | Regno Unito | probabilmente protetto fino al 31 dicembre 2039. **Non ancora validato:** vanno distinti il testo originale, la nuova edizione del 2016 e le illustrazioni | GOV.UK, Copyright Notice: Duration of copyright; UCL Copyright, 2016 | caso costruito con i dati veri: «dal 2040». Non blocca la prova |

## Casi di confine (costruiti sulla norma)

Sono separati dai casi reali e non li sostituiscono. Ognuno mette un'opera inventata proprio sul confine di una regola, e la fonte è la norma stessa. Sono 13, in `data/casi_riferimento.json`: 70 anni (morto nel 1955 o nel 1956), coautori, Spagna (morto nel 1986, nel 1987 o nel 1988), USA (uscito nel 1930 o nel 1931, con e senza seconda fonte), opere anonime (uscite nel 1955 o nel 1956) e regola britannica del 2039.

**Spagna, 6 o 7 dicembre 1987.** La norma (BOE, LPI, disposizione transitoria quarta) divide chi è morto prima del 7/12/1987 da chi è morto dopo. Noi però abbiamo solo l'anno di morte, non il giorno, quindi i due casi non si possono distinguere. Per tutti i morti del 1987 usiamo, per prudenza, 80 anni. Per chi è morto tra il 7 e il 31 dicembre 1987 diciamo 2068 invece di 2058: un errore dalla parte sicura. Il caso di confine lo dice esplicitamente.

## Regole senza ancora un caso reale

Per queste c'è la legge, ma manca un'opera reale con una fonte che ne confermi la data. Le cerco prima di spostarle in `regole.py`:
- opere anonime: 70 anni dalla pubblicazione (Direttiva 2006/116/CE, art. 1, par. 3), e in Spagna quanti anni;
- coautori: 70 anni dalla morte dell'ultimo coautore (Direttiva 2006/116/CE, art. 1, par. 2);
- confine dei 70 anni per gli autori morti nel 1987 in Spagna (prima o dopo il 7 dicembre).

## Cosa hanno già trovato i casi

1. **Mein Kampf (caso 6):** nei nostri dati l'opera è collegata a una voce di Wikidata sbagliata («Hitler», Q346521, senza data di morte) invece che ad Adolf Hitler (Q352). Per questo il sito non sa calcolarne lo stato. È un errore dei dati, non delle regole. L'opera è comunque esclusa dagli scaffali, ma la ricerca la trova.
2. **«Morti per la Francia» (caso 3):** la nostra regola, 70 più 30 anni, darebbe il 2045 per Saint-Exupéry. Le fonti dicono quasi tutte 2032, perché le proroghe di guerra si contano in un altro modo. Oggi il sito non mostra quella data, scrive «da verificare», quindi non sbaglia. Però se un giorno la mostrassimo, sarebbe sbagliata. Va sistemata la regola, o tenuto «da verificare» con il motivo.
