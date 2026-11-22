# I giri automatici del sito

Bozza del 22/11/2026, terza versione (con due revisioni di ChatGPT), **da approvare da Marco**. Finché non è approvata, i giri restano quelli di oggi (in fondo, «Com'è oggi»).
Se un giro cambia, si cambia anche questa pagina.

## L'idea

I dati del sito cambiano in tre modi diversi, e ogni giro esiste per uno solo di questi motivi:

1. **Fatti fissi** (anno di morte, anno di uscita, cittadinanza): non cambiano. Si controllano quando entrano nel sito e prima che contino.
2. **Chi è libero e chi no**: non si scarica, si calcola (fatti fissi + regole di `scripts/regole.py` + data di oggi). Cambia il 1° gennaio.
3. **Segnali vivi** (visite su Wikipedia, opere e correzioni nuove su Wikidata, edizioni nelle biblioteche): cambiano piano.

## La vita di un anno (esempio: il 2028, autori morti nel 1957)

| Quando | Cosa succede |
|---|---|
| 1° gennaio 2026 | nasce la lista 2028 (nascosta) |
| aprile, luglio, ottobre 2026 | la lista si aggiorna con i rinfreschi |
| 1° novembre 2026 | primo controllo serio delle date di morte; i dubbi vanno decisi entro dicembre |
| **7 gennaio 2027** | **la pagina 2028 diventa pubblica: parte il conto alla rovescia** |
| aprile, luglio, ottobre 2027 | rinfreschi |
| 1° novembre 2027 | ultimo controllo prima della liberazione |
| **1° gennaio 2028** | **Public Domain Day**: i dati cambiano (Già pubblici li conta da subito); per una settimana home e radar fanno festa: «Da oggi sono liberi» |
| **7 gennaio 2028** | fine della festa: parte il conto alla rovescia del 2029; la pagina 2028 resta al suo indirizzo come archivio («liberi dal 2028») |

Regola chiave: **il 1° gennaio cambiano lo stato giuridico e la presentazione (parte la festa del Public Domain Day); il 7 gennaio finisce la festa e diventa protagonista il nuovo conto alla rovescia.** Sono due passaggi distinti, ognuno con il suo giro.

Nel programma lo dice una funzione sola (in `scripts/regole.py`): dalla data di oggi ricava l'anno in vetrina e la fase («festa» dal 1° al 6 gennaio, «conto alla rovescia» il resto dell'anno). Tutte le pagine la usano; niente più `anno + 1` sparsi.

## I sei giri (cinque a calendario, uno a mano)

### 1. Classifiche: il 1° di ogni mese (leggero)
**Perché:** l'ordine per visite usa il mese appena finito, che cambia ogni mese.
**Cosa fa:**
1. legge le visite su Wikipedia del mese scorso: autori delle liste (radar, schede, pagine dell'anno) e opere di Già pubblici;
2. rifà classifiche e pagine;
3. controlli (regole, frasi, schede).

**Non tocca:** autori, opere, date. Se le visite non arrivano, restano quelle del mese prima e la pagina dice di quale mese sono («visite di ottobre 2026»).

### 2. Rinfresco: 1° aprile, 1° luglio, 1° ottobre
**Perché:** opere e correzioni nuove su Wikidata, edizioni nelle biblioteche: cambiano piano.
**Cosa fa, in ordine:**
1. liste dei due anni dopo (autori nuovi o corretti) e i loro dati (biografie, opere, cittadinanza, lingue);
2. **edizioni nelle biblioteche (SBN, BnF, BNE, British Library, Library of Congress): si ricontano per tutti**, anche per autori e opere che non sono cambiati, perché le edizioni crescono senza che Wikidata cambi;
3. date di morte **solo per gli autori nuovi**; per le liste già pubbliche, confronto veloce con Wikidata: se una data di morte è cambiata, va subito nelle cose da decidere (non si aspetta novembre);
4. libri USA e i loro anni;
5. Già pubblici: opere nuove su Wikidata, ritratti, coautori, nomi italiani, «morti per la Francia», anni delle opere USA;
6. pagine, controlli, elenco delle cose da decidere;
7. **a ottobre in più:** il calendario anniversari dell'anno dopo, con l'avviso a Marco per approvarlo.

### 3. Controllo date: 1° novembre
**Perché:** prima che un anno diventi pubblico e prima che si liberi, un anno di morte sbagliato pesa davvero; servono due mesi per decidere i dubbi.
**Cosa fa:**
1. ricontrolla con tutte le fonti le date di morte delle due liste in arrivo (quella che si libera il 1° gennaio e quella che diventerà il conto alla rovescia);
2. ricontrolla il calendario anniversari dell'anno dopo;
3. scrive i dubbi nell'elenco delle cose da decidere.

**Non pubblica** cambiamenti di date da solo: i dubbi li decide Marco.

### 4. Public Domain Day: 1° gennaio, di notte
**Cosa fa:**
1. Già pubblici aggiunge gli autori e le opere appena liberati, presi dalla lista che c'è già (non riscarica tutto). **Solo quelli con lo stato verificato:** se un autore ha ancora una data dubbia non decisa, non viene dato per libero (resta «da verificare», con il motivo) e va nelle cose da decidere; il resto del Public Domain Day va avanti normalmente. Tre autori dubbi non fermano la festa: fermano solo sé stessi;
2. USA: la lista dei libri appena liberati, più la lista della Duke University appena esce;
3. home e radar passano alla festa;
4. nasce la lista di due anni dopo (nascosta);
5. controlli.

### 5. Fine festa: 7 gennaio
**Cosa fa:**
1. home e radar passano al conto alla rovescia del nuovo anno;
2. la pagina del nuovo anno appare nei menu;
3. la pagina dell'anno appena liberato diventa archivio;
4. controlli.

**Non scarica niente.**

### 6. Correzione straordinaria: solo a mano, quando serve
**Perché:** se a maggio si scopre una data di morte sbagliata o una regola da correggere, non si aspetta il giro dopo.
**Cosa fa:**
1. applica la correzione decisa da Marco (file delle verifiche a mano, o `scripts/regole.py`);
2. rifà solo le pagine coinvolte, senza riscaricare niente;
3. passa per gli stessi controlli, compreso il confronto dello stato giuridico (sotto);
4. scrive la correzione nel registro delle prove.

## Due controlli diversi

- **Bibliografico:** autore, data di morte, opere, anno di uscita, cittadinanza, fonti. Lo fanno i giri 2 e 3.
- **Giuridico:** quale regola si applica, in quale paese, con quali eccezioni. Il sito tiene una **fotografia dello stato** di ogni autore e di ogni opera, paese per paese. Per ognuno non solo il risultato (libero / dal / con nota / da verificare) ma anche **il perché**: la regola applicata e la sua versione, i dati usati (anno di morte, anno di uscita, cittadinanza…), la fonte dell'eventuale eccezione, la data dell'ultima verifica. Così, se uno stato cambia, si vede subito se dipende da una data corretta, da una regola diversa o da un'informazione nuova sull'opera. A ogni giro la fotografia nuova si confronta con la vecchia:
  - i cambiamenti attesi (il 1° gennaio: gli autori di quell'anno diventano liberi) passano;
  - ogni altro cambiamento di stato **ferma la pubblicazione** e va nelle cose da decidere, con l'elenco di chi cambia e perché. Si pubblica solo dopo l'ok di Marco.

  Vale soprattutto quando cambia una regola: si vede subito chi cambia stato, prima che lo veda il pubblico.

## Casi di riferimento

La prova «Python e browser uguali» dice che i due programmi danno lo stesso risultato, non che il risultato sia giusto: due copie possono sbagliare insieme. Per questo serve anche un elenco di **casi di riferimento verificati**, ognuno con il risultato atteso e la fonte (legge o sentenza): per esempio «Il piccolo principe» libero in Italia dal 1° gennaio 2015 (Tribunale di Milano n. 2826/2021). Ogni regola, e ogni eccezione (Spagna, Francia, Regno Unito, USA, Trattato di pace), ha almeno un caso. Se un caso non torna, il giro si ferma. Senza fonte, un caso non entra.

## Regole per tutti i giri

- **Ogni giro fa i suoi passi in ordine, in un solo programma:** niente giri che si aspettano a vicenda per data.
- **Due tipi di problema, due reazioni:**
  - una fonte non risponde (Wikipedia, una biblioteca): quel pezzo resta con il dato di prima, la pagina dice di quando è, il resto si pubblica;
  - una contraddizione nelle regole o un cambiamento di stato non atteso: **non si pubblica niente**.
- **Tutto o niente:** ogni giro salva tutto in un colpo solo alla fine, e il sito si aggiorna da quel salvataggio. Se un passo si rompe a metà, il pubblico continua a vedere la versione di prima, intera.
- **Aggiornare solo ciò che serve:** una data sul calendario non è un motivo per rifare tutto. Le classifiche non rifanno le schede; il rinfresco rilegge da Wikidata solo autori e opere nuovi o cambiati (i conteggi delle biblioteche invece si rifanno per tutti, vedi sopra); il 1° gennaio cambia solo lo stato di ciò che è già verificato. Così il sito può crescere a molti più autori e opere senza che i giri diventino lenti.
- **Ogni giro finisce con i controlli bloccanti:**
  - `prova_regole.py`;
  - `controllo_frasi.py`;
  - in locale anche `controllo_pagine.py`.

  Se qualcosa non torna, non pubblica e lo scrive in `docs/da-decidere.md`.
- **Le prove** (stime, campioni, verifiche di fonti) stanno a parte: nome che comincia con «Prova –», partono solo con l'ok di Marco e non cambiano il sito.
- **Il cambio d'anno si prova prima di Natale**, simulando il 1° e il 7 gennaio su una copia.

## Per quest'anno (primo Public Domain Day: 1° gennaio 2027)

- Il controllo del 1° novembre 2026 non c'è stato: lo facciamo appena approvato questo schema, sulle liste 2027 e 2028.
- La pagina 2028 diventa pubblica il 7 gennaio 2027 (prima avevamo detto il 1° gennaio: con la festa slitta al 7).
- Prima di Natale servono, in quest'ordine:
  - l'audit delle regole per opera (sotto);
  - la fotografia dello stato e il suo confronto;
  - il mockup della settimana del Public Domain Day;
  - la prova del cambio d'anno.

## Da fare: le regole per opera in un posto solo

Oggi `scripts/regole.py` ha le regole per autore (durate per paese, Spagna, Francia, USA, Trattato di pace, decisione sulle date di morte). Le regole per singola opera di Già pubblici (coautori, opere anonime, inediti nel Regno Unito, libri USA con anno confermato o no) stanno ancora in parte nella pagina stessa (`storico/pagina.html`) e in `storico/per_autore.py`. Usano le durate di `regole.py`, ma la logica è scritta lì: va spostata in `regole.py` come per gli autori, con la stessa prova «Python e browser uguali».

## Protezioni già attive in tutti i giri (22/11/2026)

- **Salvataggio unico** (`scripts/salva.sh`), uguale per tutti i giri. Se nel frattempo un altro giro ha cambiato gli stessi file, il giro si ferma rosso e non pubblica niente. Prima vincevano a occhi chiusi i dati di chi salvava per ultimo. Se GitHub rifiuta l'invio 5 volte, il giro finisce rosso.
- **Fotografia dello stato** (`scripts/confronta_fotografia.py --giro`) nei giri che rifanno le pagine: aggiorna, Già pubblici, anniversari, stima. Se un'opera o un autore che c'era già cambia stato senza un motivo atteso, il giro non pubblica. Salva solo `docs/cambi-da-approvare.md`, con l'elenco e l'impronta dei cambi. Per approvare, l'impronta si scrive in `data/cambi-approvati.txt`. L'ultima fotografia pubblicata sta in `data/fotografia.json.gz`.
- **I controlli bloccano davvero:** nel giro aggiorna il salvataggio parte solo se i controlli sono passati. Già pubblici riparte solo dopo uno Storico finito bene.

## Com'è oggi (fino all'approvazione)

| Giro | Quando |
|---|---|
| Registro unico (date di morte) | 1° aprile, luglio, ottobre, novembre (dal 22/11/2026) |
| Calendario anniversari | 1° ottobre e 1° novembre (dal 22/11/2026) |
| Aggiorna autori | 1° gennaio, aprile, luglio, ottobre, dicembre |
| Storico | 2 di ogni mese |
| Già pubblici | dopo ogni Storico e quando cambia il suo codice |
| Public Domain Day e fine festa (rifà le pagine) | 1° gennaio e 7 gennaio, 00:05 ora italiana (dal 22/11/2026) |
| Prove (Stima, Campione SBN, BnF, British Library, Library of Congress, verifiche, Logo) | solo a mano |

## Dopo il 7 gennaio 2027 (deciso da Marco il 22/11/2026)

- Estendere il sito ai 27 paesi UE seguendo `docs/specifica-ue27.md`: prima un rapporto, senza pubblicare niente.
- Da studiare: l'articolo 7 della direttiva 2006/116/CE, la regola del termine più breve per le opere di autori di paesi fuori dall'UE (per esempio gli americani). Oggi il sito non ne tiene conto.
- Da decidere a parte: in Spagna, per i morti nel 1987 di cui si conosce solo l'anno, la specifica dice «da verificare». Oggi il sito applica gli 80 anni per prudenza.
