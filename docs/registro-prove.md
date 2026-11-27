# Registro delle prove sulla qualità dei dati

Una riga per ogni prova: data, cosa è cambiato, numeri prima e dopo, giudizio.
Piano di lavoro concordato il 17/11/2026 (dopo il report esterno e la revisione di ChatGPT):

| Fase | Cosa | Riuscita quando |
|---|---|---|
| 0 | Date in numero, blocco dei conteggi incoerenti, niente min() che nasconde errori | Nessun conteggio pubblicato con «dal 2000» > totale o con «dal 2000» > 0 e più recente < 2000 |
| 1 | Definizione del numero: «registrazioni bibliografiche in italiano collegate all'autore nel catalogo SBN» (per ora con altre collaborazioni) | Il sito dice esattamente cosa conta |
| 2 | Campione di sviluppo (60) + casi difficili (80), controllati a mano | Numeri di partenza per catalogo (autori sbagliati, non trovati) |
| 3 | Identità: P396 prima di VIAF; «riconosciuto con zero» separato da «non riconosciuto»; prove salvate | Ogni collegamento spiegabile |
| 4 | Nomi: particelle, doppi cognomi, alias, grafia italiana | Il campione migliora senza errori nuovi |
| 5 | Cosa si conta: solo autore e coautore; date incerte e intervalli | Conteggi riconducibili a elenchi verificabili |
| 6 | Dati nuovi in prova finché i controlli non passano | Dati sbagliati messi apposta non arrivano sul sito |
| 7 | Stesso metodo per BnF, BNE, British Library | Numeri separati per catalogo |

Il campione ridotto (fase 2) serve a sviluppare e a trovare problemi: non dimostra una qualità del 99%,
che resta un obiettivo da verificare dopo con un campione casuale più grande.

## Prove

### 17/11/2026 — Fase 0 e 1
- **Prima:** su 122 autori con dati SBN, 66 avevano numeri che si contraddicono (es. Corrado Alvaro: 105 registrazioni «dal 2000», più recente 1934). BnF, BNE, British Library: 0 incoerenze, ma lì un `min()` avrebbe nascosto un eventuale «dal 2000» superiore al totale.
- **Causa (diagnosi di ChatGPT, interrogazione diretta a SBN):** le date arrivano in formati diversi e il confronto come testo dà massimo e conteggi sbagliati. Su Alvaro, con gli anni trasformati in numero: più recente 2019, «dal 2000» 41 (valori diagnostici, non fissati nel codice).
- **Cambiato:**
  - `scripts/sbn.py`: anni di 4 cifre trasformati in numero; massimo e «dal 2000» calcolati dallo stesso insieme; cache SBN alla versione 6 (tutti gli autori si rifanno);
  - `scripts/bnf.py`, `scripts/alma.py`: tolto `min()`;
  - nuovo `scripts/controlli.py` (gira prima delle pagine): i conteggi incoerenti, nuovi o vecchi, restano nel file con `stato: da_verificare` e il sito non li mostra; riepilogo in `data/controlli.json`;
  - il sito ripete lo stesso controllo (`conteggioSospeso`), così un dato incoerente non si vede neanche se il controllo non gira;
  - etichette: «registrazioni bibliografiche in italiano collegate all'autore nel catalogo SBN», con la precisazione che per ora comprendono anche altre collaborazioni; «più recente con anno certo».
- **Dopo il controllo sui dati vecchi:** SBN 56 passano, 66 sospesi; BnF 106/0; BNE 141/0; British Library 174/0. Pagine statiche con «Dati in verifica»: 60.
- **Da fare:** confronto prima/dopo quando il nuovo giro SBN (versione 6) ha riscaricato gli autori.
- **Dopo il nuovo giro SBN (versione 6, 17/11/2026 sera):** 451 autori riscaricati, 0 errori. Controlli: SBN 122 passano, 0 sospesi; BnF 106/0; BNE 141/0; British Library 174/0.
  - I 66 incoerenti di prima ora sono tutti coerenti. Il totale non cambia (non dipende dalle date); cambiano «dal 2000» e «più recente». Esempi (prima → dopo, «dal 2000» / più recente): Alvaro 105/1934 → 41/2019; Churchill 41/1929 → 9/2012; Fraccaroli 60/1934 → 1/2010; Sayers 12/1948 → 6/2017; Bromfield 22/1955 → 0/1986; Foleÿ 42/1932 → 0/1955.
  - Anche 18 autori che prima sembravano coerenti avevano «dal 2000» gonfiato: Papini 181 → 26, Tomasi di Lampedusa 53 → 34, Brecht 101 → 68, Döblin 13 → 6.
  - Autori trovati in SBN: 122 su 459, invariato (si affronta nella fase 3).
  - **Limite noto:** «dal 2000» conta solo le registrazioni con un anno scritto in 4 cifre. Le date come «[2005]», «2005?» o «1998/2002» per ora restano fuori, quindi il numero può essere per difetto (fase 5).

### 17/11/2026 — Fase 2 (SBN): campione e numeri di partenza
- **Come è fatto il campione** (`scripts/campione_sbn.py`, seme fisso 20261117): 60 di sviluppo (20 trovati col VIAF, 15 per nome, 25 non trovati) + 80 difficili (pseudonimi 23, nomi da translitterare 19, particelle e cognomi composti 17, omonimi e iniziali 15, doppi cognomi 6). Le «date incomplete» non hanno dato abbastanza casi.
- **Risultato del sistema congelato** con le schede collegate: `docs/campione/sbn-base-2026-11-17.json`. Prove in più (nome intero, pseudonimi, alias): `docs/campione/sbn-prove-extra.json`.
- **Controllo a mano:** fatto da Claude sui dati del triplestore SBN e sul P396 di Wikidata, non sull'OPAC (non raggiungibile da qui). Esiti in `docs/campione/sbn-campione.csv`. Secondo verificatore: Marco sull'OPAC per 10 casi a caso + i 18 «probabili» (`docs/campione/da-controllare-marco.md`).
- **Esiti:** persona presente in SBN 71 (53 certi, 18 probabili), assente 52, irrisolti 17.
- **Numeri di partenza (campione scelto apposta, non stime sulla popolazione):**
  - persone presenti in SBN trovate dal sistema: 41 su 71 (58%); mancate 30;
  - collegamenti del sistema valutabili: 43; sicuramente sbagliati 2 (Richard Griffith: preso anche un musicista nato nel 1948; John Dyfnallt Owen: quattro «Owen, John»); con schede in più non dimostrate 5; incompleti 1;
  - autori assenti: il sistema non collega niente in 51 casi su 52.
- **Cause dei 30 mancati:** il codice SBN di Wikidata (P396) c'era in 20 casi; pseudonimi in SBN (Possendorf per Mahner-Mons, «Lujan, André : de» per García-Mansilla); cognomi composti e con particella (Le Gallienne, von Bodman, Saint-Paul, Kaye-Smith); «riconosciuto ma zero registrazioni in italiano» trattato come «non trovato» (Kreidolf, Coppard).
- **Errori del confronto per nome:** gli anni con qualifica («<1948-2007 ; musicista>») non vengono letti, quindi l'omonimo non si scarta; con le iniziali (L., S., F.) si collegano schede senza prove; nei nomi giapponesi in ordine originale si prende il nome come cognome.

### 18/11/2026 — Fase 2 (SBN): prova con i titoli e secondo verificatore
- **Titoli** (`scripts/campione_titoli.py`, risultato in `docs/campione/sbn-titoli.json`): per ogni scheda candidata si leggono i titoli collegati in SBN e si confrontano con le opere che Wikidata attribuisce all'autore. Il confronto automatico funziona poco, perché per gli autori minori Wikidata ha 1-2 opere; i titoli però, letti a mano, decidono molti casi.
- **Secondo verificatore:** Marco sull'OPAC: 28 risposte. Dieci a caso: 7 sì, 2 non so, 1 no (Alois Čáp, da chiarire). Probabili: 17 sì, 1 non so (Stewart White, poi deciso dai titoli). Sua proposta di regola: un nome molto simile (iniziali, ordine invertito) indica la stessa persona; tenuta solo con almeno una prova in più (anni, titolo o cognome unico in SBN).
- **Esiti aggiornati (`docs/campione/sbn-esiti.json`):** presenti 74, assenti 54, irrisolti 12. Nessun «probabile» resta senza secondo controllo o prova dai titoli.
- **Numeri di partenza aggiornati (campione scelto apposta, non stime sulla popolazione):**
  - presenti trovati dal sistema: 43 su 74 (58%), mancati 31;
  - collegamenti del sistema valutabili: 45, di cui 37 puliti, 7 che contengono anche schede di altre persone, 1 incompleto. Prima della prova con i titoli le schede in più sembravano solo «non dimostrate»: i titoli mostrano che sono altre persone (musica sacra per «Timmermans, F.», jazz per «Vieira, Afonso», un economista per «Adler, Hans A.», satelliti per «White, Stewart»);
  - assenti: il sistema collega comunque qualcosa in 1 caso su 54.
- **Scoperta:** in SBN una stessa scheda può mescolare due persone («Leclercq, Paul»: libri su Toulouse-Lautrec e un supplemento di diritto civile). Lì il conteggio è gonfiato anche con il collegamento giusto: è un limite del catalogo, da dichiarare.
- **Conseguenza per la fase 3/4:** la regola «nome compatibile» non può aggiungere schede con le sole iniziali o con il solo nome di battesimo; serve una prova (anni, titolo, codice).
- **18/11, Saldías:** Marco l'ha trovato su OPAC («Saldias, José Antonio»). Causa del mio «assente» sbagliato: in SBN gli accenti sono usati in modo incoerente dentro la stessa scheda («Saldias» senza, «José» con). Cercare togliendo tutti gli accenti o tenendoli tutti non basta: va cercata ogni parola in tutte e due le forme. Lo stesso problema tocca il sistema e va nella fase 4. Esiti: presenti 75, assenti 54, irrisolti 11 (Saldías era tra gli irrisolti, non tra gli assenti: correzione del 18/11).

### 18/11/2026 — Fase 3 (SBN): nuovo riconoscimento dell'autore
- **Come funziona** (`scripts/riconosci_sbn.py`, misura con `scripts/campione_valuta.py`, risultato in `docs/campione/sbn-fase3.json`). Per ogni autore, in ordine: 1) codice SBN di Wikidata (P396): se c'è si usa solo quello, anche con zero registrazioni; 2) VIAF; 3) ricerca per nome. Nella ricerca per nome i nomi vengono **normalizzati da tutte e due le parti** (senza accenti, minuscole, particelle «de/von/i» separate, iniziali, trattini, ordine orientale per Cina/Giappone/Corea) e ogni parola si cerca con e senza accenti e come prefisso fino al primo accento («Sald*»). Una scheda si accetta solo se il nome torna (cognome intero + primo nome, anche come iniziale) **e** c'è una prova: anni di nascita/morte entro ±1, oppure un titolo che coincide con le opere in Wikidata, oppure cognome raro in SBN (≤3 schede) con nome di battesimo per intero e nessun nome in più. Anni o secolo nella scheda che contraddicono escludono la scheda. Senza prova la scheda resta «ambigua» e non si collega.
- **Primo giro:** trovati 64 su 75 presenti; 3 errori nuovi: Jeanne collegato a «Laon, Jean : de <sec. 17.>» (via pseudonimo), Subbārāvu (assente) collegato a «Subbarao, Karumuri Venkata», F. W. Harvey a «Harvey, John Wilfred <1889-tr>».
- **Correzioni:** il primo nome deve tornare; se la scheda ha nomi che Wikidata non ha, il cognome raro non basta; il secolo nella scheda («sec. 17.») conta come contraddizione; per i cognomi troppo comuni (oltre 1000 schede) si cerca cognome + nome insieme.
- **Perché i presenti sono passati da 71 a 75 e gli assenti da 52 a 54** (classificazione a mano, non il sistema):
  - prima classificazione (17/11): presenti 71 (53 certi + 18 probabili), assenti 52, irrisolti 17;
  - prova con i titoli (18/11): 3 irrisolti diventano presenti (Abercrombie, Leclercq, Hardt: i titoli SBN sono loro); 3 irrisolti diventano assenti (Alan Sullivan, Ahmed Galal, Pedro Pérez Fernández: l'unica scheda con quel nome ha libri di un'altra persona); Saldías passa da assente a irrisolto (dubbio sugli accenti). Quindi presenti 71 + 3 = 74, assenti 52 + 3 − 1 = 54, irrisolti 17 − 6 + 1 = 12;
  - Marco su OPAC (18/11): Saldías da irrisolto a presente. Finale: presenti 75, assenti 54, irrisolti 11;
  - i 18 «probabili» sono stati tutti confermati (Marco sull'OPAC o titoli) e restano presenti.
- **Confronto prima/dopo con la stessa classificazione finale (75 / 54 / 11; rivista il 18/11 pomeriggio in 75 / 53 / 12, vedi «Revisioni dopo l'esplorazione»).** Anche il vecchio sistema è rimisurato su questi esiti, non su quelli del 17/11:
  - vecchio: presenti trovati 43 su 75 (37 puliti, 5 con anche schede di altre persone, 1 incompleto), mancati 32; assenti collegati per errore 1 su 54; irrisolti collegati 1 su 11 (Richard Griffith, con un omonimo musicista). Le 7 «schede di altre persone» del 18/11 sono quindi 5 + 1 + 1;
  - nuovo: vedi sotto.
- **Secondo giro (risultato attuale), prima → dopo:**
  - presenti trovati: 43 → 64 su 75 (58% → 85%); 53 col codice SBN, 11 col nome e una prova;
  - presenti collegati anche a schede di altre persone: 5 → 0; schede sbagliate o falsi positivi introdotti: 0;
  - assenti: collegamenti sbagliati 1 → 0 su 54;
  - irrisolti (11, non si contano): collegati 1 → 0;
  - tempo: circa 580 secondi per 140 autori.
- **Gli 11 mancati** hanno tutti la scheda giusta tra le «ambigue», ma senza anni né titolo che lo provino: Leclercq, Jeanne, Maurey, Shimoni, Bradby, von Bodman, Saint-Paul, Sainsbury, Broderzon, Stewart White, Haava. È una scelta voluta: meglio non collegare che collegare la persona sbagliata.
- **Limite:** misura sullo stesso campione usato per costruire le regole (rischio di regole «su misura»). Prima di passare in produzione serve un secondo campione nuovo.
- **Stato del campione dei 140:** è di sviluppo. Le regole sono state cambiate dopo averne visto gli errori, quindi i suoi numeri non valgono come verifica.

### 18/11/2026 — Fase 3 (SBN): verifica su un campione nuovo
- **Protocollo** (`scripts/verifica_sbn.py`, file in `docs/verifica-sbn/`):
  1. **regole congelate prima della prova**: impronta sha256 di `riconosci_sbn.py` e `sbn.py` in `regole-congelate.json`; la misura non parte se i file sono cambiati;
  2. **campione nuovo, a caso**: 100 autori estratti (seme 20261118) tra i 319 autori del sito interrogati in SBN che **non** sono nei 140 di sviluppo; nessun criterio di scelta, quindi ci sono anche gli autori che il sistema non trova (81 su 100 per il vecchio sistema, che è la proporzione reale del sito);
  3. **prove raccolte senza il nuovo sistema**: codice SBN e VIAF di Wikidata, schede con il cognome in tutte le forme (con e senza accenti, prefisso), schede con tutte le parole del nome e degli pseudonimi, titoli collegati a ogni scheda, opere in Wikidata; più il risultato del vecchio sistema;
  4. **decisione a mano prima della misura**: per ogni autore presente / assente / irrisolto e, per ogni scheda, giusta / altra persona / non dimostrabile (`esiti.json`), salvata prima di far girare il nuovo sistema;
  5. **misura**: tre conteggi separati: persone sbagliate, collegamenti senza prove sufficienti, autori mancati.
  6. Se dopo la misura si cambiano le regole, anche questo campione diventa di sviluppo e serve un'altra verifica nuova.
- **Limite del campione:** essendo casuale, ha pochi autori presenti in SBN (circa uno su cinque), quindi misura bene gli errori sugli assenti e meno bene quanti presenti si trovano.
- **Esiti decisi a mano** (`esiti.json`, salvato in un commit prima della misura): presenti 46, assenti 52, irrisolti 2 (Ray Cummings: il codice SBN di Wikidata porta a una scheda con un solo titolo, il film «Sabotatori», che non è suo; Margaret Cameron: una sola scheda con un titolo che non so attribuire).
- **Risultato (regole congelate, nessuna modifica dopo la misura), vecchio → nuovo:**
  - **persone sbagliate:** 5 → 0. Vecchio: Morley, Sheldon, Kenneth Roberts, May Sinclair collegati anche a omonimi; Winston Churchill (il romanziere americano, assente in SBN) collegato allo statista inglese;
  - **collegamenti senza prove sufficienti:** 1 → 1, lo stesso: Ray Cummings, collegato dal codice SBN di Wikidata a una scheda dubbia. Il codice va seguito (è la regola più sicura che abbiamo), ma il caso mostra che anche un codice può portare a una scheda sbagliata nel catalogo;
  - **autori mancati:** 29 → 7 su 46 presenti; trovati 17 (13 puliti) → 39, tutti puliti (85%). 29 col codice SBN, 10 col nome e una prova;
  - **assenti collegati per errore:** 1 → 0 su 52;
  - **incompleti:** 3 trovati a cui manca una scheda secondaria (Kazantzakis: «Kazantsakis, Nikos» nella discoteca; Larbaud: le lettere; Bouhélier: 2 schede scritte «Saint-Georges de Bouhelier» senza virgola). Il conteggio per loro è un po' più basso del vero.
- **I 7 mancati** e perché: Duncan Campbell Scott, Carl Rössler, Pierre Blanchon, Renée Erdős (scheda giusta trovata, ma senza anni e con titoli che non coincidono con quelli in Wikidata); Edward Sheldon e Channing Pollock (stesso motivo; il vecchio sistema li trovava, ma Sheldon insieme a due omonimi); Minnie Louise Haskins (SBN scrive «Harkins»: errore del catalogo, nessuna regola sul nome può trovarla senza rischi).
- **Rendiconto, tenuto distinto:** errori certi osservati: **0** (nessuna persona sbagliata, nessun assente collegato). Collegamenti non dimostrati: **1** (Ray Cummings, dal codice SBN di Wikidata). Non è contato tra gli errori perché non è dimostrato che sia sbagliato, né tra i giusti perché non è dimostrato che sia giusto. Dal 18/11 il suo conteggio è sospeso sul sito (`data/sospesi_manuali.json`) finché il collegamento non è chiarito.
- **Giudizio:** il risultato tiene sul campione nuovo: stessa precisione del campione di sviluppo (nessun errore certo; un collegamento non dimostrato) e stessa quota di presenti trovati (85%). Il prezzo è che due autori che il vecchio sistema trovava ora restano ambigui. Zero errori certi su 100 non vuol dire zero errori sul sito: con 0 errori certi su 100 casi si può dire, con il 95% di sicurezza, che gli errori sul sito sono sotto il 3% circa degli autori.
- **Conseguenza:** rilascio prudente autorizzato da Marco. `scripts/sbn.py` usa `riconosci_sbn.py` dalla versione 7 della cache; i casi senza prova restano ambigui e non si contano; la vecchia ricerca resta solo per `anniversari.py` (da passare al nuovo sistema). Il campione resta di verifica finché le regole non cambiano.

### 18/11/2026 — Correzioni dopo il rilascio
- **«Inedito» tolto:** un catalogo che riconosce l'autore dal codice ma non ha registrazioni nella lingua non basta per dire che l'autore sia inedito (un'edizione può essere collegata a un'altra scheda o mancare dal catalogo). Il sito ora scrive «Nessuna registrazione in {lingua} collegata all'autore», con questa spiegazione. Vale per SBN, BnF e BNE.
- **Sospensioni a mano:** nuovo file `data/sospesi_manuali.json`, letto da `controlli.py`. Un caso lì dentro non mostra numeri sul sito, anche se il catalogo dice zero, e la scheda spiega che il collegamento non è dimostrato. Primo caso: Ray Cummings.
- **Campi separati:** il risultato del riconoscimento si chiama «riconoscimento» (riconosciuto / ambiguo / non_trovato); «stato» resta solo per i controlli («da_verificare»).
- **Aggiornamento completo (18/11, tre giri):** 449 autori con dati nuovi (versione 7); 10 conservano i vecchi (versione 5), tutti «non trovato, 0 registrazioni»: non hanno opere in Wikidata e sbn.py non li interroga, quindi sul sito non mostrano numeri. Dei 449: riconosciuti 194 (121 con registrazioni in italiano: 108 dal codice SBN, 13 dal nome con una prova; 73 riconosciuti ma con zero registrazioni), ambigui 90, non trovati 165. Sospeso a mano: 1 (Ray Cummings). Controlli: Brecht 419, Milne 86, Ingalls Wilder 282, Papini 356, tutti sopra le soglie.
- **Confronto con i dati di prima:** 101 autori trovati prima e ora; 20 trovati solo ora; 21 collegamenti di prima tolti: Winston Churchill americano (133 registrazioni erano dello statista), 16 che il vecchio sistema collegava col solo nome (1-3 registrazioni ciascuno) e ora sono ambigui, 2 riconosciuti dal codice ma senza registrazioni in italiano, Michael Arlen (13 prima) ed Elizabeth Jordan (1 prima) ora non trovati: da controllare a mano.

### 18/11/2026 — Analisi esplorativa: 20 ambigui SBN (le regole in produzione non cambiano)
- **Come:** 20 autori estratti a caso (seme 20261118) tra i 90 ambigui in produzione (`scripts/esplora_ambigui.py`, file in `docs/esplora-ambigui/`). Per ogni scheda candidata: titoli, lingua, ruolo e anni in SBN. Titoli confrontati SOLO con fonti collegate all'autore da un codice di Wikidata: opere in Wikidata (P50), voci di Wikipedia collegate all'elemento, BnF (P268), BNE (P950), DNB tramite lobid (GND P227), Open Library (P648). Le pubblicazioni dopo la morte non si usano per escludere; quelle prima della nascita sono solo segnalate. Giudizio a mano in `esiti.json`.
- **Risultato:** identificati 3 su 20, irrisolti 17.
  - Duncan Campbell Scott: «The poems of Archibald Lampman» in BnF, DNB, Open Library e Wikipedia;
  - David Shimoni: «Idylls» in Open Library;
  - Yamandú Rodríguez: «El matrero» nella BNE e in Wikipedia.
- **Per fonte (autori risolti):** Open Library 2, BnF 1, DNB 1, BNE 1, Wikipedia 2 corretti **e 1 falso** (Karl M. Baer: la voce cita Karl Ernst von Baer, e il confronto automatico ci casca), opere in Wikidata 0. Senza Wikipedia si risolvono gli stessi 3 casi.
- **Cosa dicono i 17 irrisolti:** in quasi tutti i candidati sembrano altre persone (musicisti, scienziati, omonimi; SBN stesso segna «omonimi non identificati» per Oliver, J.). È probabile che molti di questi autori non siano in SBN, ma nessuna fonte lo dimostra, quindi restano irrisolti. Casi da guardare: Countee Cullen (nome rarissimo, titolo di un'antologia italiana che nessuna fonte riporta); Alan Sullivan (nel campione di sviluppo l'avevo segnato «altra persona» senza fonte: da rivedere).
- **Giudizio:** altre fonti per codice aiutano poco (3 su 20, 15%); Wikipedia letta in automatico è rischiosa. Se si estende, conviene usare solo cataloghi e Open Library, non Wikipedia.

### 18/11/2026 — Revisioni dopo l'esplorazione
- **Alan Sullivan (campione di sviluppo, n. 80): da assente a irrisolto.** La scheda «Sullivan, Alan» ha John Melly of Ethiopia (Londra, Faber & Faber 1937, «edited by Kathleen Nelson and Alan Sullivan»). Il 18/11 mattina l'avevo segnato «altra persona» senza una fonte. Ci sono indizi che sia lui (librerie antiquarie lo indicano come «E. Alan Sullivan», cioè Edward Alan come in Wikidata; una wiki di poesia lo elenca fra le sue opere), ma nessuna fonte collegata per codice. **Ricalcolo del campione di sviluppo:** presenti 75, assenti 53, irrisolti 12 (prima 75/54/11). Vecchio sistema: presenti trovati 43/75, assenti collegati per errore 1/53 (Owen), irrisolti collegati 1/12. Nuovo: presenti 64/75, assenti collegati per errore 0/53, irrisolti collegati 0/12. Il campione di verifica (100 autori) non cambia: Sullivan non ne fa parte.
- **Shimoni:** «Idylls» è un titolo generico, ma la notizia SBN e quella di Open Library coincidono anche in luogo (Gerusalemme), anno (1957) ed editore (Youth and Hechalutz Department of the Zionist Organization). Confermato.
- **Scott e Rodríguez:** altri elementi coerenti in SBN (Scott: Toronto, Morang 1900, «with a memoir by Duncan Campbell Scott»; Rodríguez: spartito di El matrero di Felipe Boero, Buenos Aires 1937, lui librettista).
- **Wikipedia esclusa dal confronto automatico:** i titoli solo menzionati in una voce possono essere di altre persone (Karl M. Baer). Resta come lettura a mano. In produzione Wikipedia non è mai stata usata: `riconosci_sbn.py` confronta solo le opere di Wikidata (P50). Conteggio per fonte senza Wikipedia: Open Library 2, BnF 1, DNB 1, BNE 1; autori identificati sempre 3 su 20.
- **Prudenza sui numeri:** 3 su 20 è il risultato di questo piccolo campione, non una stima affidabile per i 90. I 17 non risolti restano irrisolti, non assenti.

### 18/11/2026 — BnF, punto 1: risultato congelato e campione di sviluppo
- **Perché 236 autori e non 459 come SBN:** bnf.py lavora sugli elenchi UE (`2027.json`, `2028.json`) e salta di proposito gli elenchi della Spagna (`es-*.json`): la pagina Francia non li mostra. SBN invece li interroga tutti. Differenza: 213 autori presenti solo negli elenchi spagnoli. Tra i 236 candidati BnF **nessuno è rimasto non elaborato**: 106 trovati, 34 con codice e zero notizie in francese, 96 senza codice BnF in Wikidata (quindi nessun dato).
- **Risultato attuale congelato** prima di ogni modifica: `docs/campione-bnf/bnf-base-2026-11-18.json` (cache e codici BnF di Wikidata per i 236).
- **Campione di sviluppo** (`scripts/bnf_campione.py`, `bnf_campione2.py`, seme 20261118): 20 trovati, 20 con codice e zero, 20 senza codice. Prove: scheda d'autore BnF (nome, anni, varianti, fonti), notizie collegate in tutte le lingue e in francese, come è collegato l'autore (autore, collaboratore, soggetto), notizie in francese col suo nome ma non collegate, schede d'autore con lo stesso cognome. Esiti in `esiti.json`.
- **Esiti, categorie distinte:**
  - riconosciuto, con notizie in francese: 20 su 20 (identità verificata: nome e anni coincidono);
  - riconosciuto senza risultati in francese: 19 su 20 (identità verificata; nessuna notizia nemmeno cercando il nome);
  - riconosciuto ma con una notizia francese non collegata: 1 (Hans Mahner-Mons: il codice porta a «Possendorf Hans», suo pseudonimo; «Monsieur de Paris / H.-M. Mons», 1955, è collegato a un'altra forma del nome). Quindi «zero» non è sempre zero;
  - identità irrisolta: 20 su 20 senza codice. Per 12 la BnF non ha nessuna scheda d'autore con quel cognome e nome (elenco completo); per 8 il cognome ha troppe schede e la ricerca è incompleta;
  - errori tecnici: 0.
- **Codici:** 40 su 40 portano alla persona giusta. Roger Vercel ha due codici in Wikidata (anche «Crétin Roger», il vero nome): oggi se ne conta uno.
- **Cosa si conta:** nelle notizie lette (fino a 100 per autore) nessuna è collegata all'autore solo come soggetto (libri su di lui): sono tutte da autore o collaboratore, come deciso. Le collaborazioni pesano in modo diverso: Van Druten 11 su 12 (adattamenti), Ingalls Wilder 23 su 88.
- **Da verificare nel punto successivo:** per alcuni autori la ricerca per nome trova più notizie in francese di quelle collegate al codice (Arlen 41 contro 5, Cummings 31 contro 4, Lewis 53 contro 12, Leclercq 123 contro 15). Potrebbero essere omonimi (Michael J. Arlen, il figlio) o notizie non collegate: non si sa ancora.

### 18/11/2026 — BnF: verifica su autori nuovi (non superata)
- **Il conto 459 − 236 = 223:** 213 autori solo negli elenchi spagnoli (che bnf.py salta) + i 10 autori senza opere in Wikidata che anche sbn.py non interroga (sono negli elenchi spagnoli e hanno dati vecchi «non trovato»). Verificato uno per uno.
- **Regole provate** (`scripts/riconosci_bnf.py`, congelate prima della prova, `docs/verifica-bnf/regole-congelate.json`): tutti i codici BnF di Wikidata; senza codice, scheda d'autore BnF trovata per nome e accettata solo con anni che coincidono. Le notizie trovate per nome ma non collegate (Arlen, Cummings, Lewis) restano escluse.
- **Campione:** i 76 autori senza codice non usati nello sviluppo + 24 con codice estratti a caso (seme 20261119). Prove raccolte senza il nuovo sistema, esiti decisi a mano e salvati prima della misura: presenti 28, nessuna scheda 56, irrisolti 16.
- **Risultato:**
  - con codice: 24 su 24 giusti (6 senza notizie in francese); Döblin e Malaparte ora contano anche la scheda dello pseudonimo / del vero nome;
  - senza codice: 3 trovati per nome e giusti (Jirsík, Urbanová, Vurğun, tutti senza notizie in francese); 1 mancato (Judith Blunt-Lytton: la BnF scrive 1879 come anno di nascita, Wikidata 1873, quindi la regola la scarta come voluto);
  - **2 collegamenti sbagliati, con ogni probabilità**: Hans Müller-Schlösser collegato a due schede «Müller, Hans 1885-19..»; Kim Nae-sung collegato a «Kim, Seong-tae 1910-....». In tutti e due i casi la scheda ha un solo anno certo, che coincide per caso entro ±1. In più: per Müller-Schlösser basta una parte del cognome composto; per Kim il nome di battesimo non torna (regola dei nomi orientali troppo larga). Nelle prove non li avevo segnati come «altra persona», quindi il conteggio automatico li mette tra i «senza prove sufficienti»: sono comunque errori della regola;
  - assenti collegati: 0 oltre ai due casi sopra; errori tecnici: 0.
- **Giudizio:** la verifica non è superata, niente rilascio. Il codice funziona; la regola per nome è troppo larga quando la scheda ha un solo anno. Correzioni proposte: accettare per nome solo schede con **entrambi** gli anni e tutti e due coincidenti; nei cognomi composti devono tornare tutte le parti; nei nomi orientali deve tornare il nome intero. Questo campione diventa di sviluppo. Gli autori BnF senza codice sono finiti: per una verifica nuova servono altri autori (proposta: quelli degli elenchi spagnoli, mai usati per la BnF).
- **Nota per SBN:** anche `riconosci_sbn.py` accetta una scheda con un solo anno che coincide. Sul campione di verifica SBN non ha prodotto errori, ma il rischio è lo stesso.

### 18/11/2026 — Situazione del sito e misura della British Library e dei 9 autori BNE trovati per nome
- **Decisione:** la ricerca BnF per nome non vale la pena (3 autori trovati su 76, nessuno con notizie in francese, 2 errori): si ferma. Resta solo la correzione sicura: tutti i codici BnF dell'autore (`bnf.py`, versione 2). Controllo fatto: la ricerca con due codici funziona (Vercel 222 → 225 notizie).
- **Come è fatta la misura** (`scripts/bl_campione.py`, file in `docs/campione-bl/`, risultato di oggi congelato in `base-2026-11-18.json`): 40 autori con numeri BL e 20 senza, estratti a caso, più tutti i 9 autori BNE trovati per nome. Per ogni autore si scaricano le notizie trovate (fino a 50) e si guarda se cognome e anni stanno nella STESSA voce d'autore.
- **British Library, 40 con numeri:** 35 puliti, comprese le schede col vero nome o lo pseudonimo (Dion Fortune come Violet Firth, Karl M. Baer come N. O. Body, Rerich come Roerich). Errori: **F. W. Harvey 142 notizie, quasi tutte di altri** (5 sue su 50 lette, le altre soprattutto di Michael Sadleir, 1888-1957); Duncan Campbell Scott 1 notizia in più su 12 (un libro di J. B. Scott, 1792-1862, e di Ethel Mann, 1861-1947); Emanuel von Bodman 1 notizia dubbia (un volume di Lieder di Strauss); Falla e W. J. Turner qualche notizia senza la voce giusta, da guardare. Causa: la ricerca prende cognome e anni anche se stanno in voci d'autore diverse della stessa notizia.
- **British Library, 20 senza numeri:** almeno 5 ci sono ma sono schedati senza anni (Augustus Goetz 15 notizie, Arvid Mörne, Kaj Gynt, Guy de Téramond, Frona Eunice Wait come «Colburn»). Il sito dice già che qualche registrazione può sfuggire.
- **BNE, 9 autori trovati per nome:** 6 giusti (Hruška, Chiarelli, Foleÿ, Risso, Bizet, Heltai), **3 sbagliati** (J. O. Francis, Robert Mitchell, A. E. Thomas: notizie di altri, stessa causa).
- **Sospesi subito a mano** (`data/sospesi_manuali.json`): BNE di J. O. Francis, Robert Mitchell, A. E. Thomas; British Library di F. W. Harvey.
- **Correzione proposta:** contare una notizia solo se cognome e anni stanno nella stessa voce d'autore. Da provare su un campione nuovo prima del rilascio.

### 18/11/2026 — British Library e BNE per nome: conteggio verificato (rilasciato)
- **Regola** (`scripts/voce_alma.py`): si scaricano le notizie trovate dalla ricerca «Cognome nascita-morte» e se ne conta una solo se una stessa voce d'autore ha il cognome (anche di pseudonimo o vero nome da Wikidata) e tutti e due gli anni; oppure il cognome, nessun anno e la stessa iniziale del nome (la British Library scrive spesso «Cummings, Ray.» senza anni).
- **Versione 1, prima verifica** (40 autori nuovi, `docs/verifica-alma/`): 0 notizie di altri tenute, 5 tolte, ma **41 giuste perse** (Ray Cummings 22 → 0, Lilian Turner 18 → 0: voci senza anni). Non rilasciata; il campione è diventato di sviluppo.
- **Versione 2, verifica nuova** (40 autori nuovi, seme 20261121, `docs/verifica-alma2/`, regole congelate prima, esiti a mano prima della misura): 836 notizie lette; **818 giuste tenute, 14 di altre persone tolte, 0 di altre persone tenute, 4 giuste perse** (Wen Yiduo e Qi Baishi: nomi cinesi con il cognome prima; Godabarish Mishra scritto «Miśra»). Autori che prima avevano numeri di altre persone e ora hanno 0: John Dyfnallt Owen, Frederick Ferdinand Moore, Jindřich Bedřich Heller, Flora Thompson; con numeri corretti: Tristan Bernard 13 → 11, Lloyd Osbourne 70 → 65, Christofredo Jakob 3 → 2.
- **Sullo sviluppo** (i 49 della prima misura): F. W. Harvey 142 → 27, Duncan Campbell Scott 12 → 11, Walter J. Turner 54 → 52, i 3 autori BNE sbagliati → 0; pseudonimi e veri nomi tenuti (Dion Fortune, Karl M. Baer, Rerich).
- **Giudizio:** nessun errore certo osservato nella verifica; il costo è 4 notizie giuste perse su 822 (0,5%), tutte per nomi orientali o traslitterati. Rilascio: `alma.py` versione 2. Le sospensioni a mano di Harvey e dei 3 autori BNE restano finché i nuovi numeri non sono controllati.
- **Limite noto:** nomi cinesi e coreani con il cognome prima, e traslitterazioni (Mishra/Miśra).

### 18/11/2026 — USA: Library of Congress
- **Diagnosi:** il catalogo LC (SRU `lx2.loc.gov`) cerca per intestazione d'autore (`bath.personalName`) ma non filtra per lingua né per anno; con gli accenti nella ricerca non trova nulla, senza accenti sì; chiude le connessioni se si va troppo veloci. Il codice LC di Wikidata (P244) dà l'intestazione ufficiale da id.loc.gov: si cerca l'autore dal codice, come per la BnF. 386 autori su 449 hanno il codice.
- **Sviluppo** (`docs/campione-loc/`, 40 autori): identità giuste; problemi: accenti nella ricerca, notizie solo «su» l'autore (soggetto 600: Roerich 24 su 136), pagine dei risultati a volte incomplete.
- **Regola (loc.py):** intestazione ufficiale senza accenti; si scaricano le notizie; se ne conta una se l'intestazione è dell'autore come autore o collaboratore (100/700/800, non solo soggetto) e la lingua è l'inglese; pagine incomplete riprovate.
- **Prima verifica** (`docs/verifica-loc/`, 40 autori nuovi, regole congelate): 1131 notizie giuste contate, **54 giuste perse** (nelle notizie gli accenti sono scritti come codici, «Heltai, Jeno&#x30B;»: Noguchi 34, Martínez Sierra 13), **4 di altri contate** (intestazione senza anni che prendeva anche «Cummings, Ray, 1970-» e «Flament, Albert, 1877-»). Non superata; il campione diventa di sviluppo.
- **Versione 2:** caratteri decodificati e intestazione identica (non solo che comincia allo stesso modo). Sullo sviluppo: 1185 giuste contate, 0 di altri. Serve una verifica nuova (`docs/verifica-loc2/`).
- **Seconda verifica** (`docs/verifica-loc2/`, 40 autori nuovi, seme 20261123, regole versione 2 congelate prima, esiti a mano prima della misura guardando tutte le intestazioni col cognome): **1181 notizie giuste in inglese contate, 0 perse, 0 di altre persone contate**; 801 notizie non sue o non in inglese correttamente escluse; 0 errori tecnici. Due intestazioni sue con anni scritti in più (Suits, Villetard) non sono contate, ma nessuna era in inglese.
- **Limite:** 7 autori su 40 hanno il codice ma il catalogo non trova nulla con l'intestazione ufficiale (tra questi E. C. Vivian e Bob Olsen, che quasi certamente hanno libri in inglese): notizie vecchie schedate con un'altra forma del nome. Il sito dice «nessuna registrazione collegata», non «inedito».
- **Rilascio:** `loc.py` nel flusso di aggiornamento (30 minuti per giro, riparte da solo); sul sito, Paese «USA»: numeri della Library of Congress; senza codice LC: «Wikidata non indica il codice Library of Congress di questo autore».

### 18/11/2026 — Revisione di cosa dice il sito
- **Cosa si è controllato:** tutti i testi del sito, delle pagine autore e dei README, confrontati con quello che il sistema fa davvero oggi.
- **Corretto:**
  - l'esportazione per Excel (CSV) aveva ancora le colonne di Open Library e solo quelle di SBN: ora ha le colonne del catalogo del paese scelto (SBN, BnF, BNE, British Library, Library of Congress), con «dato non disponibile» e «in verifica» al posto dei vuoti;
  - testi di presentazione, fonti in fondo al sito e descrizioni per Google citavano solo SBN o Open Library: ora citano i cataloghi nazionali e il Regno Unito e gli USA;
  - tolte parti morte del codice (vecchio blocco SBN, testi di Open Library mai mostrati);
  - README italiano e inglese riscritti: metodi attuali di ogni catalogo, USA coperti, Germania non collegata, come si evitano gli errori.
- **Proroga italiana di 6 anni (D.Lgs.Lgt. 440/1945):** verificata sul testo della L. 52/1996 art. 17 riportato da WIPO Lex. Il comma 1 abroga la proroga dei termini; i commi 3 e 5 richiamano solo le procedure degli articoli 2-5 del decreto (accordi tra autori, eredi ed editori; compenso per il cinema). Quindi la frase del sito «abrogata dalla legge 52/1996, art. 17» è corretta e resta.

### 18/11/2026 — Controllo dei numeri nuovi e fine di 4 sospensioni a mano
- **F. W. Harvey, British Library:** con la regola nuova 142 → 27 notizie (115 scartate), come previsto dallo sviluppo. Controllo: rifatta la regola sulle 50 notizie lette a mano a novembre (`docs/campione-bl/prove.json`): tiene 5 notizie, tutte con la voce «Harvey, F. W. (Frederick William), 1888-1957» (Gloucestershire Lad, Collected poems, Comrades in captivity); le 45 di Michael Sadleir e altri sono scartate. Sospensione tolta.
- **J. O. Francis, Robert Mitchell, A. E. Thomas, BNE:** con la regola nuova nessuna notizia per nome è loro, quindi il sito non mostra più un numero ma «Wikidata non indica il codice BNE di questo autore». Sospensioni tolte perché non c'è più un numero da sospendere.
- **Ray Cummings, SBN:** resta sospeso (il codice porta al film «Sabotatori»).
- **Limite:** di Harvey sono controllate a mano 50 notizie su 142; le altre 92 sono state giudicate solo dalla regola.

### 18/11/2026 — Spiegato sul sito cosa vuol dire «registrazione»
- Sopra la nota di ogni catalogo (sito e pagine autore, italiano e inglese) c'è ora una riga: una registrazione è la scheda con cui la biblioteca descrive una pubblicazione; di solito una per ogni edizione o ristampa, quindi un libro uscito cinque volte conta cinque; non sono copie vendute né titoli diversi.
- Corrette anche le descrizioni per Google delle pagine autore: citavano 4 paesi (italiano) o 5 (inglese), ora tutti e 6.

### 18/11/2026 — Stima di accuratezza e copertura del sito (solo misura)
- **Come è fatta** (`scripts/stima_sito.py`, dati in `docs/stima-sito/`): sui dati di oggi (autori morti nel 1956 e nel 1957, opere USA del 1931), confronto con Wikidata completo, con due liste esterne (Wikipedia inglese «1956 in literature», sezione Deaths; Duke, Public Domain Day 2026, sezione Books) e con il testo della legge britannica (regola del 2039). Nessuna regola cambiata.
- **Anno di morte** (456 autori letterari del 2027): 297 confermati da almeno due fonti (65%), 56 documentati con una fonte citata, 3 da un catalogo nazionale, **94 con la sola Wikidata (21%), per cui il sito non mostra nessun avviso**, 6 discordi (segnalati in rosso). In Wikidata 20 persone del file 2027 hanno più anni di morte (per esempio Ricardo Baeza 1956 e 1959, Frances Mabel Robinson 1954 e 1956); 3 compaiono sia nel 2027 sia nel 2028.
- **Opere USA del 2027** (163): **9 hanno in Wikidata una data di pubblicazione precedente al 1931** (L'opera da tre soldi 1928, L'allegria 1916, Wise Parenthood 1918…): sono già libere, il sito dice che lo diventano nel 2027. Causa: si prende qualsiasi data uguale al 1931, non la prima.
- **USA contro la Duke** (libri del 1930, regola del sito applicata al 1930): 13 dei 19 libri citati dalla Duke ci sono; mancano Private Lives, The 42nd Parallel, Cimarron, Civilization and Its Discontents, The Conquest of Happiness, Elson Basic Readers.
- **Autori trovati in Wikidata:** persone morte nel 1956 con una professione che discende da «scrittore» (345 professioni) e almeno 3 pagine Wikimedia, assenti dal sito: 24, di cui solo 2 davvero letterari. La raccolta da Wikidata è quasi completa.
- **Lista principale («Autori con opere», 120 nel 2027):** dei 50 scrittori più noti del 2027 ne contiene 33; dei 100 più noti 49. Esclusi tra i più noti: Fadeev, Aino Kallas, Julien Benda, Evelyn Beatrice Hall (Wikidata dice solo «scrittore»), Jan Lechoń, Johannes Jørgensen (nessuna opera in Wikidata). Nel 2028: Joyce Cary (solo «scrittore»), Avetik Isahakyan, Leopold Staff, Mark Aldanov (nessuna opera). Dei 967 esclusi perché Wikidata dice solo «scrittore» o «traduttore», 418 sono descritti in Wikidata come scrittori, romanzieri o poeti.
- **Wikipedia «1956 in literature»** (22 nomi letti): 19 sul sito, 13 nella lista principale; mancano Wickham Steed, Otto Roth, Michael Ventris (giornalisti e studiosi).
- **Regole non segnalate sulla scheda:** la data italiana degli autori di paesi alleati è mostrata come certa (l'avviso è solo generico, in fondo); nel Regno Unito le opere inedite al 1989 di autori morti prima del 1969 restano protette fino al 31/12/2039 (gov.uk, Copyright Notice: Duration of copyright), e il sito non lo dice.

### 18/11/2026 — Correzioni dopo la stima
- **USA (grave):** `opere.py` ora tiene un'opera solo se NON ha in Wikidata una data di pubblicazione precedente all'anno della lista (conta la prima pubblicazione). Tolte subito a mano da `data/us-2027.json` le 9 opere già libere trovate dalla stima; `us-2028.json` si rifà al prossimo aggiornamento con la regola nuova. Sul sito l'avviso USA dice che l'anno è la prima pubblicazione registrata in Wikidata e che ci sono solo le opere con pagine Wikipedia.
- **Anno di morte con più valori in Wikidata:** `verifica.py` legge tutti gli anni di morte (P570); se Wikidata ne dà più d'uno l'esito è «discorde» e il sito mostra anche «Wikidata (altra data)».
- **Una sola fonte:** la scheda del sito ora lo dice («controllalo prima di pubblicare»); le pagine autore lo dicevano già.
- **Autori di paesi alleati (Italia):** avviso sulla scheda (Paese Italia) e sulle pagine autore quando la cittadinanza in Wikidata è di una delle Potenze alleate e associate del Trattato di pace del 1947 (preambolo; Albania per adesione). È un indizio, non cambia la data. Oggi riguarda 70 dei 120 autori principali del 2027 e 76 dei 117 del 2028.
- **Regno Unito:** aggiunta la regola del 2039 per le opere inedite al 1989 di autori morti prima del 1969 (CDPA, allegato 1, paragrafo 12; gov.uk, Copyright Notice: Duration of copyright).

### 18/11/2026 — Calendario anniversari 2027: due date corrette dopo una verifica esterna
- **Verifica fatta fuori da qui** (82 date controllate sul web, portata da Marco): 2 sbagliate, 4 incerte.
- **Gogol':** il calendario aveva il 21 febbraio, che è la data del calendario russo dell'epoca; la morte è il 4 marzo 1852 nel calendario gregoriano (Britannica). La data veniva dalla scheda di Wikipedia inglese, che riporta il calendario vecchio. Corretto in `anniversari_correzioni.json`.
- **Góngora:** 23 maggio 1627 (Britannica; prima biografia di Chacón, 1628), non il 24 di Wikipedia. Corretto.
- **I promessi sposi:** il 15 giugno non è confermato; la Ventisettana fu ultimata nel giugno 1827 (Martinelli) e un documento del 14 luglio parla di copie in vendita dal 5 luglio. Ora il calendario dice giugno 1827, senza giorno.
- **Restano come sono:** Aspettando Godot 17 ottobre 1952 (fonte già registrata; un libraio antiquario dice settembre), Gaston Leroux 15 aprile 1927 (Britannica dà 15 o 16).
- **Kleist (250 anni dalla nascita) mancava.** Oggi in Wikidata passa tutte le regole del calendario (una sola data, 18 ottobre 1777, nel calendario gregoriano; professioni letterarie; 86 pagine Wikimedia): la causa più probabile è che la ricerca del 12 novembre sui nati nel 1777 non sia andata a buon fine o che Wikidata fosse diverso quel giorno, ma non è dimostrato. Aggiunto a mano al calendario approvato (dati della voce presi da Wikidata con `scripts/voce_kleist.py`), con la nota che il Kleist-Museum indica il 10 o il 18 ottobre.
- **Calendario pubblico rigenerato** (pagine IT/EN, .ics e .csv) con le date corrette.
- **Tolta *La capanna dello zio Tom*** (prima edizione, 175 anni) dal calendario 2027, su richiesta di Marco; esclusa anche dai calendari futuri (`anniversari_esclusioni.json`).

### 18/11/2026 — Confronto con una lista di riferimento esterna (ChatGPT)
- **Lista:** 204 scrittori morti nel 1956, fatta da ChatGPT con una fonte per riga (`docs/stima-sito/riferimento-1956-chatgpt.csv`).
- **Controllo delle fonti** (`scripts/controlla_riferimento.py`, automatico): 197 pagine su 204 contengono il 1956; 7 non si sono aperte (non vuol dire che siano sbagliate). La lista segnala da sola 6 anni di morte controversi.
- **Confronto con il sito** (170 righe con codice Wikidata ricavato dalla pagina Wikipedia): 65 nella lista principale (38%), 28 tra i «senza opere», 65 solo in «Tutti», 12 assenti (studiosi e saggisti che Wikidata non chiama scrittori: Klages, Febvre, Calamandrei, Soddy, Griaule…; Dakshinaranjan Mitra Majumder ha l'anno conteso 1956/1957).
- **Al contrario:** dei 120 autori principali del sito, 77 sono nella lista di ChatGPT; tra i 30 più noti ne mancano solo 3 (Tartakower, Velimirović, John Emerson), che non sono soprattutto scrittori. La lista di riferimento prende bene i nomi importanti e meno bene i minori.
- **Giudizio:** il sito ha quasi tutti (93% delle righe con codice), ma ne mostra nella lista principale poco più di un terzo; e la lista principale contiene anche chi non è uno scrittore (Tartakower, scacchista; Marie Laurencin, pittrice).

### 18/11/2026 — Storico: logica dei dati allineata alle correzioni del sito
- **Prima pubblicazione:** nella ricerca per periodo un'opera si prende solo con la sua data di pubblicazione più vecchia (stesso errore trovato sulle opere USA). Nella ricerca per autore era già così (la più vecchia tra le date).
- **Più anni di morte:** si tiene il più tardo (prudente) e l'autore è segnato «morte incerta»; prima, nella ricerca per periodo, si teneva il primo trovato.
- **Paesi alleati:** per gli autori morti dal 1900 si legge la cittadinanza; chi è di un paese alleato del Trattato di pace del 1947 è segnato, perché in Italia la protezione può durare di più.
- **Effetto:** un'opera che con l'anno di morte più tardo non è libera da nessuna parte esce dallo Storico. I due segni nuovi entrano nei file della ricerca, per gli avvisi della pagina.
- **Regole che la pagina dovrà applicare** (dai dati: anno della prima pubblicazione, anni di morte, segni): Spagna 80 anni per i morti prima del 1987; Regno Unito, regola del 2039 per le opere pubblicate dopo il 1989 di autori morti prima del 1969; avviso per «morte incerta» e, con l'Italia, per gli autori di paesi alleati.

### 18/11/2026 — Lista principale: regola nuova su chi è uno scrittore (verificata, rilasciata)
- **Problema** (stima di stasera): la lista principale prendeva solo chi Wikidata chiama romanziere, poeta, drammaturgo o saggista E ha opere collegate. Restavano fuori Fadeev, Aino Kallas, Benda, Jan Lechoń, Joyce Cary; dentro c'erano anche uno scacchista (Tartakower) e una pittrice.
- **Regola nuova** (`scripts/regola_lista.py`, congelata con sha256 in `docs/regola-lista/regole-congelate.json` prima della verifica): è scrittore chi ha un mestiere letterario nella descrizione inglese di Wikidata (anche dopo un altro: «artist and poet»; ma «chemist and author» solo con una professione letteraria); se la descrizione non nomina mestieri, chi ha una professione letteraria; se nomina solo mestieri non letterari, chi ha una professione letteraria e almeno 5 opere (Ambedkar). Non serve più avere opere in Wikidata.
- **Sviluppo** (autori morti nel 1956, `docs/regola-lista/esiti-sviluppo.json`): 100 a caso + i 120 principali, giudicati a mano dalle descrizioni.
- **Verifica** (campione nuovo: 100 autori a caso morti nel 1957, seme 20261119, giudicati a mano PRIMA di applicare la regola; `esiti-verifica.json`, `misura.json`). Su 36 scrittori veri: **regola di oggi 2 presi, regola nuova 36**. Non scrittori dentro: oggi 1 su 23, nuova 1 su 23 (Miloš Klicman, grafico, che Wikidata segna anche saggista). Dentro entrano anche 17 dei 20 «soprattutto altro ma autori di libri» (giornalisti e scrittori, scultori e scrittori…) e 2 dei 21 non giudicabili.
- **Correzione di trascrizione:** nella lista dei giudizi a mano i valori dalla posizione 82 alla 100 erano spostati di un posto; ripristinati quelli annotati prima della misura, nessun giudizio cambiato.
- **Confronto esterno** (lista ChatGPT, 1956): presi 136 su 158, contro 65 su 170 di prima.
- **Limiti:** il giudizio a mano è di Claude, che ha scritto anche la regola, e si basa sulle stesse descrizioni di Wikidata che la regola legge: misura quanto la regola segue le descrizioni, non quanto le descrizioni siano giuste. Il confronto con la lista di ChatGPT è l'unico controllo indipendente. La lista cresce molto (circa 825 autori nel 2027 contro 120): gli aggiornamenti dei cataloghi saranno più lunghi e ripartono da soli.
- **Rilascio:** `aggiorna.py` legge la descrizione inglese; `arricchisci.py` arricchisce i candidati e poi decide con la regola; i cataloghi non chiedono più opere in Wikidata; sul sito il filtro si chiama «Scrittori» e «Senza opere in Wikidata» resta come filtro.

### 19/11/2026 — Storico contro la Duke (libri entrati nel pubblico dominio USA 2019-2026)
- **Come:** dalle pagine Public Domain Day della Duke 2019-2026 (`docs/stima-sito/duke/`) ho preso i 114 libri della sezione Books (opere del 1923-1930) e li ho cercati nei file di ricerca dello Storico, prima per titolo esatto poi a mano per parole del titolo (`docs/stima-sito/storico-vs-duke.json`).
- **Risultato:** 93 trovati con l'anno giusto (82%); 6 trovati con un anno diverso o mancante; 15 mancanti (13%).
- **Mancanti:** New Hampshire (Frost), The Prospects of Industrial Civilization e The Conquest of Happiness (Russell), Rootabaga Pigeons, The Writing of Fiction (Wharton), Enough Rope (Parker), Now We Are Six (Milne), Amerika (Kafka), Le Temps retrouvé (Proust), Peter Pan come testo teatrale del 1928, Rope, A Preface to Morals, Nancy Drew (serie), Elson Basic Readers, Private Lives. Causa probabile: in Wikidata manca la data di pubblicazione o il tipo di opera, e l'autore è morto dopo il 1955 (quindi non entra dalla strada per autore).
- **Anno mancante** (opera trovata ma senza anno: Desire Under the Elms, Old New York, On the Trail of Negro Folk-Songs): nello Storico non risulta libera negli USA anche se lo è.
- **Anno più vecchio della Duke** (Seven Pillars of Wisdom 1922 contro 1926, Bambi 1923 contro 1926, Red Harvest 1927 contro 1929): è la prima data che Wikidata registra (stampa privata, edizione straniera, puntate su rivista). Per la legge USA quella data non sempre conta (Bambi: causa Twin Books contro Disney, 1996). Oggi non cambia niente perché sono tutte libere, ma con la stessa logica un'opera può risultare libera troppo presto: va detto nella pagina («prima data registrata, da verificare»).
- **Errori gravi** (un'opera data per libera quando non lo è): nessuno in questo confronto, che però contiene solo opere già libere.

### 19/11/2026 — Storico: correzioni dopo il confronto con la Duke
- **Wikidata, più opere** (periodi v3, si riscaricano tutti): entra anche un'opera senza tipo ma con un autore (P50), come «Now We Are Six» (escluse le pubblicazioni scientifiche); l'anno di prima pubblicazione può venire anche da un'edizione dell'opera (P629), come «New Hampshire» di Frost, che in Wikidata ha la data solo sull'edizione.
- **Seconda fonte per gli USA** (`storico/duke.py`): i libri delle pagine Public Domain Day della Duke dal 2019 (CC BY 4.0), cercati in Wikidata per titolo e cognome dell'autore. Se lo Storico non ha l'anno lo prende dalla Duke; se ha un anno diverso lo annota («anno_duke», per mostrarlo come data da verificare); se l'opera non c'è la aggiunge, anche senza codice Wikidata. L'anno della Duke vale solo per gli USA.
- **Diagnosi** (`docs/stima-sito/diagnosi-duke.json`): Time Regained e The Secret of the Old Clock c'erano già (titolo diverso nel confronto); Now We Are Six non ha tipo in Wikidata; New Hampshire e Rootabaga Pigeons hanno la data solo sull'edizione; Private Lives, Desire Under the Elms e Old New York non hanno nessuna data; quattro libri (Russell, Lippmann, Wharton, Elson) non hanno un elemento con quel titolo.
- **Misura dopo:** il confronto con la Duke non è più indipendente (ora è una fonte). Per misurare servirà un altro riferimento, per esempio le liste «<anno> in literature» di Wikipedia.

### 19/11/2026 — Pagina «Già pubblici» pubblicata (/gia-pubblici/, /en/already-public/)
- **Cosa:** pagina costruita dal mockup approvato: ricerca per titolo o autore con lo stato in Italia, Francia, Germania, Spagna e USA; scaffali per il paese scelto (più letti della settimana, liberi dal 1° gennaio, classifica di 40 autori con ritratto, generi con simbolo, lingue a colore piatto). Link nel menu del sito e del calendario, sitemap.
- **Come è fatta:** `storico/pagina.py` (senza rete) prepara `data/storico/pagina.json` (le 3000 opere più note), `data/storico/per_autore/` (tutte le opere di ogni autore, 100 file) e scrive le due pagine da `storico/pagina.html`. `storico/ritratti.py` prende i ritratti da Wikimedia Commons con autore e licenza. Lavoro `gia-pubblici.yml`: parte dopo ogni aggiornamento dello Storico.
- **Regole nella pagina (una sola funzione per ricerca e scaffali):** UE 70 anni dalla morte; Spagna 80 per i morti prima del 1987; USA 95 anni dalla prima data registrata (nota «prima data registrata» per le opere vicine al limite; anno dalla Duke segnalato da verificare). Italia: autori di paesi alleati morti negli ultimi 79 anni, opere fino al 1947 → «da verificare» e fuori dagli scaffali italiani. Francia: avviso «morti per la Francia» per chi è morto nel 1939-1945. Anno di uscita più vecchio di 90 anni della morte di tutti gli autori → errore dei dati, non si usa (es. «La dottrina del fascismo» 1562). «Various authors», «anonymous» fuori dalla classifica autori.
- **Prova:** pagina aperta in Chrome sul computer di lavoro (desktop e telefono, italiano e inglese): ricerche «orwell», «brecht», «promessi sposi»; cambio paese; finestra di un'opera. Nessun errore di script.
- **Limiti:** non c'è il Regno Unito (regola 2039 non applicata); i ritratti arrivano con il primo lavoro su GitHub; gli scaffali usano le 3000 opere più note, la ricerca tutte.

### 19/11/2026 — Già pubblici: Regno Unito e scaffale delle differenze
- **Segnalazione di Marco:** cambiando paese le opere sembravano uguali. Verifica: gli scaffali cambiavano, ma i primi titoli dei «più letti» (Ramayana, Odissea, Dickens…) sono liberi ovunque, quindi in alto non si vedeva differenza.
- **Correzione:** primo scaffale nuovo «Liberi {paese}, non ancora altrove» (opere libere nel paese scelto e ancora protette in almeno un altro), poi «Liberi dal 1° gennaio», poi i più letti. Nell'introduzione: quante delle opere più lette sono libere nel paese. Nota onesta: Italia, Francia, Germania e Regno Unito hanno la stessa regola, quindi tra loro cambiano poco.
- **Regno Unito aggiunto:** 70 anni dalla morte; opera uscita per la prima volta dopo il 1988 di autore morto prima del 1969 → protetta fino al 31/12/2039 (CDPA 1988, allegato 1, par. 12, già citato nel sito); opera postuma uscita prima del 1989 da meno di 51 anni → «da verificare». Esempio: «Franz Kafka: The Office Writings» (2008) → dal 2040 nel Regno Unito.
- **Errore dei dati corretto:** un anno di uscita di oltre 150 anni dopo la morte di tutti gli autori è un'edizione moderna (la «Repubblica» di Platone risultava del 1963 e quindi non libera negli USA): non si usa.

### 19/11/2026 — Già pubblici: ordine per lingua del paese; aggiornamenti meno frequenti
- **Segnalazione di Marco:** nel resto del sito l'ordine segue le visite alla Wikipedia nella lingua del paese; nello Storico no (si sommavano inglese e italiano per tutti i paesi).
- **Correzione:** lo Storico misura le visite della settimana su cinque Wikipedia (italiano, inglese, francese, tedesco, spagnolo), con gli indirizzi delle pagine letti da Wikidata. La pagina ordina scaffali e classifica autori con la lingua del paese: Italia → italiano, Francia → francese, Germania → tedesco, Spagna → spagnolo, Regno Unito e USA → inglese. Finché francese, tedesco e spagnolo non sono misurati, per quei paesi si usa la somma inglese + italiano e il sottotitolo lo dice.
- **Effetto subito visibile (Italia):** i più letti diventano Canto di Natale, Jane Eyre, Odissea, Moby Dick, Madame Bovary, Divina Commedia, L'infinito, I promessi sposi (prima: Rāmāyaṇa, Odissea, Canto di Natale, Moby Dick, Hanuman Chalisa).
- **Aggiornamenti (decisione di Marco):** autori ogni tre mesi più dicembre; Storico una volta al mese; nessuno dei due riparte più da solo quando si cambia uno script. Titoli «I più letti» e «Classifica» senza «della settimana».

### 19/11/2026 — Anniversari 2027: perché mancano scrittori (diagnosi, il sito non cambia)
- **Prova** (`scripts/diagnosi_anniv_writer.py`, esito in `docs/stima-sito/anniv-writer.json`): stessa domanda a Wikidata di `anniversari.py` (nascite e morti per ogni età tonda, stesse esclusioni), ma con il mestiere «writer» (Q36180) e soglia di 15 pagine Wikipedia; poi si contano le varianti. Esempi estratti a caso con seme 20261119.
- **Oggi (mestieri attuali, soglia 30):** 160 nascite e morti. **Con «writer», soglia 30:** +41 (gen 2, feb 8, mar 2, apr 3, mag 7, giu 2, lug 2, ago 1, set 3, ott 2, nov 3, dic 2, senza giorno 4). **Con «writer», pagine 20-29:** +57 in più. **Mestieri attuali, pagine 20-29:** +126.
- **10 esempi a caso (writer, soglia 30):** buoni 4 (Isidora Sekulić, Güzäl Yäxinä, Ahad Ha'am, Tite Kubo da valutare), rumore 6 (Charles Taze Russell, Thomas S. Monson, Isadora Duncan, Ray Kroc, Juliette Récamier, Vilhelm Thomsen linguista). **10 a caso (writer, 20-29 pagine):** buoni 6 (Remizov, Matavulj, Nayantara Sahgal, Šatrijos Ragana, Shen Congwen, Giovanni Arpino), dubbi o rumore 4 (Locard, Ali Gomaa, Elena Milashina, Beryl Markham).
- **I nomi segnalati, tre cause diverse:** solo «writer» → Uderzo (56 pagine) e Carlo Levi (42); soglia 30 → Josephine Tey (28), W. S. Merwin (29), Oğuz Atay (18); esclusi perché hanno anche un mestiere non letterario (pittore, politico) e in Wikidata nessun loro libro collegato con almeno 10 pagine → Paul Éluard (79 pagine), Clarice Lispector (63). Hikmet, De Roberto e Drummond de Andrade non trovati per nome inglese nella prova (da rifare per codice).
- **Giudizio:** «writer» da solo porta circa metà rumore (capi religiosi, imprenditori, una danzatrice). Va filtrato con la regola già verificata per la lista principale (`scripts/regola_lista.py`, mestiere letterario nella descrizione) invece di inventarne una nuova.
- **Date:** Foscolo morto il 10 settembre 1827 (Britannica; ODNB tramite la Jackson Bibliography dell'Università di Toronto): il sito ha già il 10 settembre, la fonte salvata (Studenti.it) è debole. Góngora 23 maggio 1627 (Britannica; Wikipedia spagnola; Encyclopedia of the Renaissance; prima biografia, Chacón 1628): il sito ha già il 23.

### 19/11/2026 — Anniversari 2027: lista larga da scegliere a mano
- **Decisione di Marco:** non tutto può essere automatico; i calendari si rifiniscono a mano.
- **Prova** (`scripts/candidati_anniv.py`, esito `docs/stima-sito/anniv-candidati.json` e `.md`): nascite e morti con anniversario tondo nel 2027 di chi su Wikidata ha un mestiere letterario compreso «writer», almeno 15 pagine Wikipedia, senza l'esclusione per altri mestieri. Per ognuno il verdetto della regola della lista principale (`regola_lista.scrittore`), solo come aiuto.
- **Risultato:** 1.029 persone, 146 già nel calendario, **883 nuove**, di cui 416 scrittori secondo la regola. Per mese tra 52 e 77 nuove (dicembre 71, di cui 40 con la regola).
- **Nomi segnalati da Marco:** ora ci sono Tey, Uderzo, Éluard, Carlo Levi, Lispector, Atay, Drummond de Andrade, Merwin. Mancano ancora Nazım Hikmet e Federico De Roberto: da guardare a parte (probabile data di nascita doppia o meno di 15 pagine).
- **Uderzo:** la regola dice «no» (descrizione «fumettista»): esempio di dove serve la scelta a mano.
- Lista messa in un foglio con una casella «Entra?» per ogni nome.

### 19/11/2026 — Già pubblici: seconda fonte obbligatoria per le opere libere solo negli USA
- **Errore grave trovato:** «Poesie di Svendborg» (Brecht) risultava del 1926, quindi libera negli USA; è uscita nel 1939 (Malik-Verlag, Londra; fonte: Krabiel, Wallstein/De Gruyter 2017). Il 1926 c'era già prima delle correzioni di oggi: viene da Wikidata, e nessun aggiornamento lo avrebbe corretto.
- **Il buco:** la Duke riempiva o aggiungeva solo i suoi ~15 libri l'anno; Open Library e Library of Congress erano usate solo per gli autori (traduzioni, edizioni), mai per l'anno di ogni opera.
- **Regola (fissata prima dei risultati):** un'opera libera solo negli USA e solo per l'anno è «libero» solo se la Duke o Open Library (anno di prima pubblicazione, stesso titolo e stesso autore) confermano un'uscita entro il 1930; altrimenti «da verificare» nella ricerca e fuori dagli scaffali USA. Riguarda 3.458 opere.
- **Subito:** finché la verifica non le conferma, tutte e 3.458 sono «da verificare» (prudenza). `storico/verifica_anni.py` gira nel lavoro gia-pubblici.yml e scrive `data/storico/anni_verificati.json`.
- **Da misurare:** quante confermate, quante in disaccordo, quante non trovate; 10 esempi per tipo da controllare a mano prima di fidarsi di Open Library come seconda fonte.
- **Esito del primo giro (19/11, 14:07–14:50):** 3.458 opere controllate. Confermate 1.134 (33%: Open Library 1.087, Duke 47); Open Library dà un anno più tardo 350 (10%); non trovate 1.974 (57%). Svendborg: non trovata, resta «da verificare».
- **Giudizio:** Open Library serve a confermare, non a smentire. Nei 10 esempi «confermati» l'anno è giusto. Nei 10 «in disaccordo» l'anno di Wikidata è quasi sempre quello giusto (The Highwayman 1906, Jeeves and the Hard-boiled Egg 1917, Envy 1927, Zaynab 1913–14): Open Library mette come «prima pubblicazione» la più vecchia edizione che possiede, spesso una ristampa o una traduzione recente. Quindi la regola è prudente (nessun «libero» falso aggiunto) ma lascia «da verificare» 2.324 opere probabilmente libere.
- **Passo successivo proposto:** terza fonte per le 2.324 (catalogo della Library of Congress, prima edizione per titolo e autore).
- **Terza fonte, prova veloce (Library of Congress):** The Sun Also Rises confermato (1926); The Highwayman trovato solo in un'edizione del 1969 (la poesia uscì nel 1906 in una raccolta: un catalogo di libri non vede le prime uscite in rivista o dentro raccolte); Svendborg e Jeeves non trovati. Indice «bath.name» non accettato: si usano dc.title e dc.creator. Limite noto del metodo: racconti, poesie e opere uscite prima in rivista restano spesso «da verificare».

### 19/11/2026 — Schede autore: cosa è cambiato e cosa no (dal mockup)
- **Dati di partenza (Search Console, 6–17 nov):** 228 schede autore, 1.166 impressioni, 6 clic. Le schede avevano già la data in cima; il difetto era il testo identico ripetuto in tutte (sei paragrafi di regole) e i pochi dati propri.
- **Cambiato:** le date paese per paese diventano una griglia visibile di 6 riquadri con una riga di regola ciascuno (prima: paragrafi lunghi, uguali ovunque, chiusi in un riquadro a scomparsa) e un link alle regole; nuova sezione «Nei cataloghi nazionali» con le registrazioni nei cinque cataloghi a confronto (dato proprio del sito); la biografia di Wikipedia va dopo i dati.
- **Non fatto, di proposito:** la tabella «opera per opera» (gli anni delle opere non sono ancora verificati: vedi metodo-anni-opere.md); le domande frequenti (sarebbero frasi uguali in tutte le schede con solo nome e data diversi, cioè lo stesso difetto che togliamo).
- **Come si misura:** stesse esportazioni di Search Console tra 3–4 settimane, schede autore: impressioni, clic, posizione media.
- **Aggiunto su richiesta di Marco («fallo comunque»):** nelle schede, le opere principali con lo stato negli USA opera per opera, secondo il metodo degli anni (libero solo con anno confermato da una seconda fonte; altrimenti «da verificare»; le date future usano l'anno di Wikidata, detto nella nota). Primo giro: 97 «libero», 493 «da verificare» nelle schede italiane; diminuiranno man mano che la Library of Congress conferma. Domande con risposte fatte solo dei dati dell'autore (quando entra in pubblico dominio; quali opere sono già libere negli USA, solo se ce ne sono di confermate), con dati strutturati FAQPage. Le schede si rigenerano nel lavoro gia-pubblici.yml dopo ogni verifica.

### 19/11/2026 — Calendario: titoli per Google
- **Controllo di Marco:** il calendario italiano è indicizzato da Google (Controllo URL, 19/11). Le zero impressioni vengono quindi dalle ricerche, non da un blocco.
- **Cambiato:** titolo e descrizione (inglese: «Literary and book anniversaries 2027…», perché per «book anniversaries 2027» eravamo all'8° posto senza clic; italiano: «Anniversari letterari 2027: scrittori, libri e ricorrenze…»); ogni mese ha il titolo con l'anno («Gennaio 2027») e un'ancora (#mese-1, #month-1). «Literary anniversaries 2027» resta all'inizio del titolo inglese, che oggi è al 3°–4° posto.
- **Rischio:** cambiare il titolo della pagina che porta più clic può spostarla per qualche giorno. Da guardare nella prossima esportazione.

### 19/11/2026 — Calendario 2027: 39 scrittori aggiunti a mano
- **Scelta:** dalla lista larga (`anniv-candidati.json`), solo scrittori davvero importanti; esclusi di proposito (in `data/anniversari_aggiunte.json`): Maurras, Chateaubriant, Bonsels, Hugo Ball, Frank Norris (razzismo, antisemitismo, nazismo, collaborazionismo).
- **Controllo delle date** (`scripts/aggiungi_anniversari.py`): data di Wikidata (con conversione dal calendario giuliano) confermata nel testo o nel riquadro di almeno una Wikipedia (en, it, fr, de, es); in disaccordo la voce non entra. 39 aggiunte su 40, tutte con almeno due Wikipedia d'accordo tranne nessuna (vedi resoconto `docs/stima-sito/anniv-aggiunte.json`). Fuori: Bolesław Leśmian (Wikidata 3 febbraio, Wikipedia 22 gennaio: probabile errore di calendario su Wikidata).
- **Nota:** Nazım Hikmet entra il 15 gennaio (Wikidata, Wikipedia inglese e spagnola); la lista di Marco diceva 20 gennaio.
- **Calendario:** da 192 a 231 voci (dicembre da 8 a 15). Le voci aggiunte a mano restano anche se il calendario si rigenera.

### 19/11/2026 (sera) — Schede autore allineate al mockup; fine della verifica con la Library of Congress
- **Schede:** testata scura larga con nome grande e ritratto a destra, risposta in rosso, sei riquadri paese colorati come nel mockup (primo paese rosso, USA verde, già liberi verdi), sezioni con occhiello rosso e titolo grande. Errore trovato nella prova e corretto prima di pubblicare: i riquadri colorati risultavano «libero dal …» anche quando non lo erano («USA: libero dal None»). Nomi lunghi: carattere più piccolo perché la parola più lunga stia intera.
- **Library of Congress:** provate 2.311 opere. Confermate in tutto 1.340 su 3.493 (Open Library 1.099, Library of Congress 186, Duke 55); 294 con anno più tardo nelle altre fonti, 1.859 non trovate: restano «da verificare».
- **Errore mio:** 28 opere su cui il catalogo non rispondeva non venivano mai segnate come provate, e il lavoro è ripartito da solo circa 70 volte, ogni 2 minuti, dalle 17:00 alle 19:00 circa. Corretto: un'opera senza risposta conta come provata.

## 19/11/2026 — Verifica degli anni sulle liste USA 2027 e 2028
- **Perché:** le liste USA (data/us-2027.json, us-2028.json) prendevano l'anno solo da Wikidata.
- **Come:** script scripts/verifica_anni_usa.py, stesso metodo e stesse fonti dello Storico (Duke → Open Library → Library of Congress). Per ogni libro si cerca l'edizione più vecchia con lo stesso titolo e lo stesso autore. Esiti: «ok» se una fonte ha un'edizione dell'anno giusto; «prima» se ne ha una più vecchia; «nd» negli altri casi.
- **Risultati 2027 (libri del 1931, 154 in tutto):**
  - 54 confermati (47 da Open Library, 7 dalla Library of Congress);
  - 97 non confermati;
  - 3 «prima».
- **Risultati 2028 (libri del 1932, 159 in tutto):**
  - 56 confermati;
  - 96 non confermati;
  - 7 «prima».
- **Giudizio:**
  - La conferma funziona sui libri più cercati: La buona terra, Le onde, Santuario, La chiave di vetro, Il mondo nuovo.
  - I non confermati sono soprattutto opere tradotte, che nei cataloghi USA hanno l'anno della traduzione (Volo di notte, I sonnambuli, La marcia di Radetzky), e racconti usciti in rivista (The Whisperer in Darkness).
  - L'esito «prima» NON è affidabile come smentita: Open Library dà Death in the Afternoon al 1920, Peter Duck al 1800 e Light in August al 1931, tutti errori. Quindi non si toglie nessun libro dalla lista: i «prima» restano «da confermare».

## 19/11/2026 (sera) — Liste USA: registro del copyright, BnF, catalogo tedesco
- **Fonti aggiunte:**
  - registro del copyright USA (Catalog of Copyright Entries 1930-33, trascrizione NYPL, CC0);
  - BnF per le opere francesi;
  - per le opere tedesche, prima DNB e poi K10plus. La DNB risponde 403/429 a tutte le richieste da GitHub (prova con scripts/prova_cataloghi_de.py); K10plus risponde.
- **Errore corretto:** il titolo originale veniva preso da Wikidata anche in un'altra lingua (Musil cercato come «L'homme sans qualités»). Ora si usa solo il titolo nella lingua dell'opera (P407).
- **Risultati finali:**
  - 2027: 78 confermati su 154 (prima 54);
  - 2028: 76 confermati su 159 (prima 56).
  - Conferme per fonte nel 2027: registro del copyright 38, Open Library 15, BnF 15, K10plus 8, Library of Congress 2.
- **Usciti prima (da decidere a mano):**
  - 2027: Charlie Chan Carries On e Le Bal, 1930 per il registro del copyright: errori veri della lista.
  - 2028: Der Mann ohne Eigenschaften (K10plus 1930: il primo volume è uscito nel 1930, quindi probabilmente errore vero), Die Morgenlandfahrt (K10plus 1931), Die heilige Johanna der Schlachthöfe (K10plus 1930), Solitude de la pitié (BnF 1930). Gli ultimi tre sono da controllare: possono essere anticipazioni in rivista o schede sbagliate.
- **Non confermati che restano:**
  - opere in lingue senza catalogo nella catena (russo, ceco, giapponese…);
  - racconti usciti in rivista;
  - racconti postumi di Kafka, usciti dentro la raccolta del 1931 e non come libri a sé.

## 19/11/2026 (notte) — Perché Gravelli è in cima alla classifica italiana
- **Prova:** scripts/prova_visite.py. Per 6 autori della lista 2027 ha letto le visite mese per mese a it.wikipedia negli ultimi 12 mesi, separate per tipo di visitatore (persone, programmi, crawler), e poi il mese con più visite giorno per giorno.
- **Cosa ha trovato:**
  - Gravelli ha 19.430 visite da persone. Di queste 11.690 sono di febbraio 2026, e 9.380 arrivano da un solo giorno, il 9 febbraio; il 10 febbraio ne ha 1.718. Negli altri mesi le visite sono tra 560 e 1.020.
  - Senza il picco, Gravelli ha circa 8.000 visite l'anno.
  - Papini, Alvaro, Brecht, Walser e Milne hanno visite regolari, senza picchi di questo tipo.
- **Errori di metodo:**
  1. La somma dei 12 mesi conta per intero un picco di un giorno.
  2. Il voto da 0 a 100 dà 100 a tutti i primi, quindi tra loro decide il numero grezzo, che è quello falsato dal picco.
  3. L'aggiornamento riparte da solo quando non finisce (.incompleto): il 19/11 ha girato 8 volte, e la classifica cambia a ogni giro.
- **Nota:** anche senza il picco, Gravelli su it.wikipedia ha più visite di Milne (circa 530 al mese) e di Walser. La classifica «Italia» misura solo la Wikipedia italiana.

## 19/11/2026 (notte) — Perché lo scaffale «Italiano» di Già pubblici ha solo 37 titoli
- **Cosa ho guardato:** data/storico/opere.json, cioè le 3.000 opere degli scaffali, e data/storico/ricerca (l'archivio intero, 82.545 opere).
- **Come sono costruiti gli scaffali:**
  - chi entra: le 3.000 opere con più Wikipedia nel mondo, almeno 12 lingue (fama mondiale);
  - in che ordine: le visite nella lingua del paese scelto (locale).
  - La classifica degli autori invece usa la Wikipedia locale per tutti gli autori: è diverso.
- **Lingue nelle 3.000:** inglese 725, francese 327, tedesco 292, greco antico 219, russo 183, latino 167, italiano 40.
- **L'italiano spezzato:** dialetti toscani 5 (Divina Commedia), italiano medievale 6 (Decameron), napoletano 2.
- **Non libri dentro le 3.000:** Lo schiaccianoci, Torah, Editto di Milano, testi biblici.
- **Correzione proposta, da fare dopo il campione:**
  - per ogni lingua, le opere più lette nella Wikipedia di quella lingua, prese dall'archivio intero;
  - unire le varianti (italiano medievale e toscano → italiano; le varianti del latino → latino);
  - solo libri e testi letterari;
  - campione con i primi 30 per lingua, prima e dopo.

## 19/11/2026 (notte) — Prova alla cieca contro la Duke 2025 (libri del 1929)
- **Come:** scripts/prova_cieca_duke.py. Ha ricostruito la lista del 1929 con la stessa domanda a Wikidata delle liste USA, un tipo di opera alla volta; il primo tentativo era fallito per timeout di Wikidata e la lista era vuota. Poi ha verificato gli anni senza usare la Duke (registro del copyright, BnF, K10plus, Open Library, Library of Congress). Solo alla fine ha aperto la lista Duke 2025, che nei nostri dati ha 15 libri.
- **Risultati:** 163 opere nella nostra lista, di cui 80 con l'anno confermato. Conferme per fonte: registro del copyright 51, BnF 11, Open Library 11, Library of Congress 4, K10plus 3.
- **Confronto con la Duke:**
  - 9 libri su 15 sono nella nostra lista, e 8 di questi hanno l'anno confermato. Due li aveva persi il confronto automatico per il titolo diverso: «The Seven Dials Mystery» contro «Seven Dials Mystery», e «Laughing Boy» contro «Laughing Boy: A Navajo Love Story».
  - Cup of Gold è nella lista, ma non confermato.
  - 6 libri non risultano tra le nostre opere confermate: A Room of One's Own, Red Harvest, Rope, All Quiet on the Western Front, A Preface to Morals, The Roman Hat Mystery.
    - All Quiet on the Western Front: la Duke elenca la traduzione inglese del 1929, ma l'originale tedesco è del 1928.
    - Per gli altri 5 la prova non ha salvato la lista completa, quindi non si sa se sono assenti o non confermati. Da salvare la prossima volta.
- **In più rispetto alla Duke:** almeno 72 libri confermati che la Duke non elenca, tra cui Berlin Alexanderplatz, Les Enfants terribles, David Golder, Look Homeward Angel, Passing e The Dain Curse.
- **Problemi trovati:**
  - The Maltese Falcon risulta confermato 1929 da noi, mentre la Duke lo mette nel 2026 (1930). È uscito a puntate su rivista nel 1929-30. Serve un controllo: conflitto con la Duke di un altro anno = da decidere.
  - «Good-Bye to All That» compare due volte (due voci Wikidata).

## 19/11/2026 (notte) — Date delle puntate: Wikipedia inglese e ISFDB
- **Come:** scripts/prova_puntate.py. Per 40 opere (4 romanzi noti più i testi inglesi non confermati delle liste 2027 e 2028) ha letto il testo della Wikipedia inglese, cercando le frasi su rivista e puntate, e le voci di ISFDB con la data del numero della rivista.
- **Romanzi a puntate:**
  - Red Harvest: 4 puntate su Black Mask, da novembre 1927 a febbraio 1928 (Wikipedia).
  - The Dain Curse: da novembre 1928 a febbraio 1929.
  - Tarzan Triumphant: su Blue Book da ottobre 1931 a marzo 1932. **Nella lista 2027 è «1931 confermato», ma per intero è libero solo dal 2028.**
  - Tarzan and the City of Gold: su Argosy da marzo ad aprile 1932 (ISFDB, puntata per puntata).
  - Pirates of Venus: su Argosy nel 1932, libro nel 1934.
  - The Maltese Falcon: né Wikipedia né ISFDB (non è un genere che ISFDB copre).
- **Racconti in rivista:** ISFDB dà il mese e la rivista per circa 20 testi di Lovecraft, Howard, Clark Ashton Smith e Wells, per esempio The Whisperer in Darkness (Weird Tales, agosto 1931) e The Phoenix on the Sword (dicembre 1932). Con questo diventano confermabili.
- **Errori nella lista 2028:** The Lagoon (1897), The Idiots (1896) e The Return (1898) sono racconti di Conrad dell'Ottocento, non del 1932: sono già liberi. Wikipedia e ISFDB concordano.
- **Non coperti:** racconti di Faulkner e testi teatrali di Coward. Per Wodehouse e Woolf a volte risponde Wikipedia.
- **Giudizio:** ISFDB va bene per il genere (fantascienza, fantasy, horror, avventura), la Wikipedia inglese per i romanzi famosi. Vanno usate tutte e due.

## 19/11/2026 (notte) — Incidente: giro annullato che ha salvato dati a metà
- **Cosa è successo:** il lavoro «Aggiorna autori», ripartito da solo, è stato annullato a mano dopo il primo passo. I passi «Crea le pagine» e «Salva» avevano `if: always()`, quindi hanno girato lo stesso. Il commit eb6cc42a ha salvato autori senza biografie, visite e opere, e ha cancellato quasi tutte le schede autore.
- **Ripristino:** commit 742caae4 (revert di eb6cc42a): 410 schede in italiano e 397 in inglese, dati com'erano prima.
- **Blindatura:**
  - `if: ${{ !cancelled() }}` al posto di `if: always()` in aggiorna.yml e storico.yml;
  - pagine.py non cancella le schede se ci sono meno di 100 autori con biografia e opere;
  - tolte tutte le ripartenze automatiche (aggiorna, storico, gia-pubblici);
  - l'elenco «fuori classifica» si legge da data/fuori_classifica.json e non dipende più dai file dei dati.
- **Limite che resta:** se l'arricchimento fallisce senza annullamento, «Salva» salva comunque l'elenco grezzo. Da blindare: non salvare i file degli autori se mancano biografie e visite.

## 20/11/2026 — Prova alla cieca contro la Duke 2025, metodo corretto
- **Correzioni rispetto alla prova del 19/11:**
  - liste USA con saggi, opere drammatiche e «opere scritte» con autore;
  - tutte le date di Wikidata, non solo la preferita (Red Harvest);
  - per le opere a puntate conta la data più recente;
  - riviste e puntate da ISFDB e dal testo della Wikipedia inglese;
  - registro del copyright da data/cce_file.json;
  - domande a Wikidata con 5 tentativi, e prova non valida se una fallisce;
  - prova senza limite di tempo stretto.
- **Lista del 1929:** 187 opere, tutte controllate. Esiti: 115 confermate, 69 non confermate, 2 «uscito prima» (The Gunner 1928 dal registro del copyright, The Croxley Master 1899 da ISFDB), 1 a puntate fino all'anno dopo (Tintin nel paese dei Soviet, fino al 1930). Conferme per fonte: registro del copyright 60, Wikipedia 17, Open Library 13, BnF 11, ISFDB 8, K10plus 4, Library of Congress 2.
- **Confronto con la Duke (15 libri):**
  - 14 nella nostra lista. A Room of One's Own c'era, ma il confronto non la trovava per l'apostrofo tipografico «One’s»: corretto in parole().
  - 12 confermati.
  - Non confermati: Cup of Gold, e The Roman Hat Mystery (lo pseudonimo «Ellery Queen» non corrisponde ai nomi veri degli autori su Wikidata).
  - Mancante: A Preface to Morals (Lippmann), che su Wikidata non ha nessuna pagina Wikipedia e resta fuori dalla soglia.
- **Giudizio:** sui libri della Duke ora troviamo 14 su 15 e ne confermiamo 12; in più abbiamo circa 100 libri confermati che la Duke non elenca.
- **Limiti che restano:**
  - pseudonimi: usare P742 di Wikidata per confrontare con il registro del copyright;
  - opere senza Wikipedia: valutare il registro del copyright come porta d'ingresso.

## 20/11/2026 — Liste USA 2027 e 2028 ricostruite col metodo corretto
- **Come:** scripts/ricostruisci_liste_usa.py (opere.py, poi verifica_anni_usa.py da capo, poi le pagine del Public Domain Day e da_decidere). Wikidata ha dato molti errori 502/504, ma ogni domanda ha risposto entro i 5 tentativi: nessuna è fallita.
- **2027 (libri del 1931):** 169 libri (prima 154), 111 confermati (prima 78), 3 usciti prima, 1 a puntate fino al 1932 (Tarzan Triumphant). Conferme: registro del copyright 48, Wikipedia 18, BnF 15, ISFDB 12, Open Library 9, K10plus 8, Library of Congress 1.
- **2028 (libri del 1932):** 175 libri (prima 159), 110 confermati (prima 76), 5 usciti prima (Musil, Brecht, tre racconti di Conrad dell'Ottocento), 1 a puntate fino al 1933 (Cat Country di Lao She).
- **Errore trovato e corretto:** «Dwellers in the Mirage» risultava a puntate fino al 1941, perché ISFDB ha anche una ristampa a puntate del 1941. Ora contano solo le puntate entro 5 anni dalla prima uscita. Il libro è stato corretto a mano nei dati: confermato 1932 dal registro del copyright.

## 20/11/2026 — Caratteri serviti dal nostro dominio
- **Prima:** ogni pagina caricava Big Shoulders Display, Instrument Sans e DM Mono da Google Fonts, quindi l'indirizzo IP di chi visita arrivava a Google.
- **Come:** scripts/scarica_font.py ha scaricato i file .woff2 (solo alfabeti latino e latino esteso) in assets/fonts/ e ha scritto assets/fonts/fonts.css. Licenza dei tre caratteri: SIL Open Font License. In 821 pagine e nei modelli (scripts/pagine.py, storico/pagina.html, index.html) il collegamento a Google è stato sostituito con /assets/fonts/fonts.css. Le copie salvate delle pagine Duke in docs/ non sono state toccate.
- **Controllo:** home IT ed EN, Già pubblici, Public Domain Day 2027, calendario 2027 e una scheda autore aperti nel browser: tutti i caratteri caricati, zero richieste a Google, aspetto invariato.
- **Limite:** i nomi in alfabeti non latini (cirillico, greco) usano il carattere di sistema. Prima Google li serviva per Big Shoulders e Instrument Sans.

## 20/11/2026 — Credito delle foto: nome dell'autore ripetuto
- **Difetto:** Wikimedia Commons scrive il nome due volte (visibile e nascosto), e noi li incollavamo: «Unknown authorUnknown author».
- **Correzione:**
  - alla lettura da Commons, in arricchisci.py, opere.py e storico/ritratti.py: si toglie la ripetizione all'inizio e il modello «Unknown…» ripetuto;
  - nei dati: 4 file degli autori, 2 liste USA, cache_arricchimento (372 voci, altrimenti il giro successivo le rimetteva) e ritratti dello Storico;
  - schede e Già pubblici rifatte in locale.
- **Attenzione:** la prima regola, più larga, rovinava nomi veri («R. R. Bowker» diventava «R. Bowker», «The Theatre» diventava «Theatre»). È stata ristretta a ripetizioni di almeno 4 caratteri seguite da fine, spazio o punteggiatura. Controllato su questi casi.

## 20/11/2026 — Campione degli scaffali per lingua (Già pubblici)
- **Come:** scripts/prova_scaffali.py. Per ogni opera dell'archivio (82.545) legge da Wikidata la lingua (P407), il tipo (P31) e le pagine Wikipedia. Unisce le varianti storiche (italiano antico, toscano e medievale → italiano; francese antico e anglo-normanno → francese…). Tiene solo i tipi letterari. Per le 400 opere più diffuse di ogni lingua legge le visite degli ultimi 12 mesi alla Wikipedia di quella lingua, con la regola anti-picchi.
- **Opere per lingua (oggi → candidati):** italiano 51 → 946, francese 354 → 2.192, tedesco 303 → 1.402, spagnolo 50 → 673, inglese 839 → 6.309.
- **Italiano, primi 10 col metodo nuovo:** Divina Commedia, L'infinito, I promessi sposi, La pioggia nel pineto, Cantico delle creature, Il fu Mattia Pascal, Orlando furioso, Pinocchio, Uno nessuno e centomila, I Malavoglia. Oggi mancavano Il fu Mattia Pascal, La pioggia nel pineto e Uno nessuno e centomila.
- **Problemi trovati:**
  1. 24 blocchi di Wikidata su 207 falliti (circa 9.600 opere, il 12%): servono più tentativi.
  2. Entrano testi d'odio già esclusi dalle classifiche (Mein Kampf, Protocolli dei Savi di Sion): va applicato anche qui l'elenco degli esclusi (colonna escl dell'archivio).
  3. Entrano non-libri: Costituzione degli Stati Uniti, Siete Partidas, Diccionario geográfico, Manual de Carreño, inni nazionali. Il tipo «opera scritta» è troppo largo: serve un elenco di tipi da escludere (leggi, costituzioni, dizionari, manuali, inni, testi sacri).
  4. Opere in più lingue: Guerra e pace finisce nel francese perché Wikidata elenca anche il francese. Regola: si assegna una lingua solo se tutte le lingue dell'opera portano a quella.
  5. Alcuni autori anonimi compaiono come codice tecnico di Wikidata (Lazarillo de Tormes, Beowulf): vanno mostrati come «anonimo».

## 20/11/2026 — Scaffali per lingua in produzione (Già pubblici)
- **Come:** storico/scaffali_lingua.py nel lavoro gia-pubblici.yml, prima di storico/pagina.py. storico/pagina.py aggiunge le opere degli scaffali in coda (n_principali), e la pagina le usa solo per gli scaffali per lingua.
- **Primo giro (44712368946):** riuscito, tutte le opere con risposta da Wikidata, 0 letture fallite, 30 lingue. Opere: italiano 2.362, francese 3.036, tedesco 2.426, russo 1.744, latino 1.384, greco antico 1.107, spagnolo 936. Tolte: 39.318 per tipo non letterario, 4.882 non libri, 17 escluse (testi d'odio).
- **Errori trovati nei risultati:**
  1. Don Chisciotte assente: la sua lingua su Wikidata è «Early Modern Spanish», senza codice. Ora le varianti senza codice si riconoscono dall'ultima parola del nome.
  2. Nel latino entravano Lexicon Universale e Promptuarium iconum: aggiunti lessici e cataloghi tra i non-libri.
- **Secondo giro:** 44720257705.

## 20/11/2026 — Coautori: misura
- **Come:** controllo locale sull'archivio (82.545 opere), poi scripts/prova_coautori.py su Wikidata.
- **Regola di oggi (storico/pagina.html, liberaUe):** in Europa un'opera è libera se sono morti da più di 70 anni tutti gli autori segnati su Wikidata (P50).
- **A. Voci senza data di morte tra gli autori:** 294 opere oggi risultano non libere per questo. Che cosa sono quelle voci:
  - duo di fratelli (Fratelli Grimm): 83;
  - pseudonimi collettivi e duo di scrittori (Ilf e Petrov, Publius): 23;
  - organizzazioni (università, editori, società scientifiche): circa 15;
  - valore sconosciuto: 24;
  - persone senza data di morte su Wikidata: 78.
  Esempi di opere libere date per non libere: Hänsel e Gretel, Raperonzolo, I musicanti di Brema, Le dodici sedie, Federalist Papers.
- **B. Collaboratori in altri campi (opere degli scaffali, 5.896):** 411 opere ne hanno: illustratore 420, collaboratore 71, compositore 69, librettista 24. Le opere oggi libere con un collaboratore morto dopo la soglia sono 49, quasi tutte per illustratori di edizioni moderne (Robinson Crusoe illustrato nel 2014, La metamorfosi, Via col vento). Il testo resta libero: l'illustrazione di un'edizione ha diritti propri.
- **Giudizio:** il caso «L'opera da tre soldi» (Elisabeth Hauptmann) non risulta su Wikidata in nessun campo. I coautori non dichiarati non si trovano in automatico.

## 20/11/2026 — Coautori: regola applicata (prova in locale, non ancora pubblicata)
- **Regola approvata da Marco:** 1) gruppi, pseudonimi collettivi ed enti non contano se ci sono autori persone con la data di morte; un gruppo con i membri segnati (P527) vale per la morte più tardiva dei membri; 2) coautore senza data di morte, o «valore sconosciuto», accanto ad autori con la data: «da verificare», con il motivo; 3) compositore (P86) e librettista (P87): avviso, il testo resta libero; 4) illustratori: non contano; 5) elenco a mano data/coautori_manuali.json, per ora vuoto.
- **Come:** storico/coautori.py legge da Wikidata il tipo dei 829 autori senza data di morte (205 non sono persone), i membri dei gruppi, compositori e librettisti delle 82.518 opere dell'archivio (251 ne hanno) e i coautori delle opere dei 607 autori con una scheda (306 opere). Giro 44738559524, nessun pezzo mancante. Risultato in data/storico/coautori.json. La regola è nella pagina (storico/pagina.html, coautori()), nello Storico (storico/per_autore.py, autori_efficaci(): così entrano nell'archivio anche le fiabe con il solo «Fratelli Grimm») e nelle schede autore (scripts/pagine.py, note_coautori()).
- **Correzione di quanto scritto sopra:** Elisabeth Hauptmann È su Wikidata come autrice de «L'opera da tre soldi» (P50); lo Storico la dava già libera dal 2044. Il giudizio della misura era sbagliato.
- **Risultato (Italia, Già pubblici):** cambiano 174 opere, non 294. Le altre 120 erano già giuste per la regola «uscita più di 170 anni fa» (Hänsel e Gretel, 1812). Da «non lo sappiamo» a libera: 126 (Le dodici sedie, fiabe dei Grimm senza anno); a «libera dal…»: 11 (Ellery Queen dal 2053); a «da verificare»: 37. Opere libere che smettono di esserlo: 0.
- **Schede autore:** 75 con una nota nuova (Brecht: Hauptmann e Berlau; Nordhoff: Hall; Crofts: Agatha Christie).
- **Errori che restano:** gravi 0. Medi 2: 5 opere antiche «da verificare» per un coautore antico senza data (Kādambari, Pseudo-Demostene); persone messe come autori su Wikidata che hanno solo curato un'edizione (Stephen Fry per «La strada di Puh», Neil Gaiman, Vivian Gornick). Lievi: musica di film o adattamenti segnata sull'opera (Kazantzakis).
- **Da decidere (Marco):** 1) coautore senza data accanto ad autori morti da più di 170 anni: antico e libero? 2) elenco a mano dei «non coautori» con fonte.

## 20/11/2026 — Coautori: due aggiunte decise da Marco
- **1. Coautore senza data accanto ad autori tutti antichi o morti da più di 170 anni:** è antico anche lui, l'opera è libera (5 opere: Kādambari, Pseudo-Demostene, Alcione).
- **2. Chi è nato dopo la morte degli altri autori non è un coautore** (ha curato, letto o presentato un'edizione): si legge l'anno di nascita (P569). Spariscono Stephen Fry («La strada di Puh») e Neil Gaiman (Dunsany). Vivian Gornick è nata nel 1935, prima della morte di Willa Cather: resta «da verificare». Giro 44741780482, nessun pezzo mancante.
- **Risultato finale (Italia, Già pubblici):** cambiano 174 opere. Da «non lo sappiamo» a libere: 132; a «libera dal…»: 11; a «da verificare»: 31. Opere libere che smettono di esserlo: 0. Schede autore con una nota nuova: 72, di cui 7 note «da verificare».
- **Errori che restano:** gravi 0; medi 1 (persone segnate come autori su Wikidata ma nate prima della morte dell'autore, come Gornick: restano «da verificare», che è onesto); lievi: musica di film o adattamenti segnata sull'opera.

## 20/11/2026 — Anni di morte: regola delle due fonti autorevoli
- **Regola (Marco):** se due fonti autorevoli concordano contro Wikidata, valgono le fonti autorevoli.
- **Fonti autorevoli:** quelle che leggiamo noi (GND, Library of Congress) e, tra le fonti che Wikidata cita, le autorità delle biblioteche nazionali (BnF, Repubblica Ceca, IdRef, NUKAT, Biblioteca nazionale russa, BNE, Uruguay…) e i dizionari biografici (Diccionario Biográfico Español, Deutsche Biographie, Österreichisches Biographisches Lexikon, Britannica, Store norske leksikon…). La stessa biblioteca citata due volte conta una volta. Non contano: Wikidata stessa, VIAF, WorldCat, SNAC, IMDb, Project Gutenberg, Open Library.
- **Come si decide:** l'anno con almeno due fonti autorevoli diverse, e più di ogni altro anno. Se è quello di Wikidata: «maggioranza» (confermato). Se è un altro: «corretto», l'autore esce dall'elenco sbagliato ed entra in quello giusto se lo costruiamo (data/morti_corrette.json, così vale anche per gli anni dopo). Altrimenti resta «discorde».
- **Prova in locale** sui dati delle biblioteche già scaricati (stesso codice di scripts/verifica.py, senza rete): degli 83 casi discordi, 14 corretti, 19 confermati, 50 restano (47 persone).
  - Corretti, per esempio: Ioseb Mčedlišvili (Wikidata 1956; GND, LoC, Dizionario biografico georgiano 1950: era già libero dal 2021, esce dal 2027); Vladimír Sís e Hanns Gobsch (1958: escono dal 2028); Labiba Hashim e Zhaleh Qaem-Maqami (1946: passano da Spagna 2028 a Spagna 2027).
  - I 50 rimasti: una sola fonte autorevole contro Wikidata 21; Wikidata contro sé stessa o contro fonti deboli 12; fonti autorevoli divise 11; una fonte autorevole con Wikidata e solo fonti deboli contro 6.
- **Errori:** gravi 0 (nessun autore resta in un elenco con un anno smentito da due fonti autorevoli). Il rischio nuovo: due fonti che copiano la stessa voce sbagliata. Lo si limita contando una volta sola la stessa biblioteca ed escludendo gli aggregatori.

## 20/11/2026 — Registro unico, parte 1: primo giro degli autori (incompleto)
- **Come:** scripts/registro_autori.py (giro 44754404163) su 5.939 autori: quelli delle liste più quelli dello Storico morti tra il 1930 e il 1955. Fonti: Wikidata (tutti gli anni di morte, codici GND e LoC, fonti citate), GND e Library of Congress lette da noi. Decisione: scripts/regole.py, decidi_morte(). Come anno di Wikidata si prende il più tardo, come fa lo Storico.
- **Risultato:** 2.844 letture nuove dalle biblioteche; tempo finito (40 minuti); 1.038 autori «in attesa» di una biblioteca. Esiti: verificato 3.282, documentato 1.497, una sola fonte 1.032, maggioranza 37, corretto 11, discorde 76, controllo a mano 4. Anno diverso da Wikidata: 12 (per esempio Tomás Carrasquilla: Wikidata 1936, Britannica, GND e LoC 1940).
- **Giudizio:** nessun errore e nessun dato perso. La misura sullo Storico si fa solo a registro completo: serve un secondo giro (in attesa dell'ok di Marco).

## 20/11/2026 — Registro unico: secondo giro e misura sullo Storico
- **Giro 44762480014:** 1.940 letture nuove dalle biblioteche; in attesa resta 1 solo autore (una biblioteca che non risponde). Esiti su 5.939 autori: verificato 4.266, documentato 588, una sola fonte 945, maggioranza 44, corretto 14, discorde 78, controllo a mano 4.
- **Misura sullo Storico (in locale):** stato in Europa delle 82.545 opere con gli anni di morte del registro al posto di quelli di oggi, stesse regole dei coautori. **Opere che cambiano stato: 0.** Le 14 correzioni non attraversano mai il confine del 1955 (esempio: Carrasquilla 1936 → 1940, libero comunque).
- **Rischio che resta:** 2 opere libere in Europa hanno un autore con fonti discordi proprio sul confine: Otto Nückel, «Destiny» (Wikidata e GND 1955, Library of Congress 1956) e Alice Alison Lide, «Ood-le-uk the Wanderer» (Wikidata 1955, Library of Congress 1956). Con una sola fonte autorevole contro, la regola non le cambia: andrebbero mostrate «da verificare».
- **Giudizio:** gravi 0, medi 2. Lo Storico con solo Wikidata era già giusto per lo stato delle opere; il registro serve a non avere più date diverse da una pagina all'altra.

## 20/11/2026 — Registro unico, parte 3: le pagine leggono dal registro
- **Storico / Già pubblici:** storico/applica_registro.py porta nello Storico gli anni di morte del registro (anche dentro storico/storico.py, passo 1d, e come passo di gia-pubblici.yml). Regola: scripts/regole.py, morte_dal_registro(). Prova in locale: 37 autori cambiano (10 nell'anno, 27 solo come «fonti discordi»), nessuna opera cambia stato tranne 2 che passano a «da verificare» perché le fonti autorevoli discordano proprio sul confine del 1955 (Otto Nückel, Alice Alison Lide). Seconda passata: 0 cambi (il risultato non si sposta).
- **Liste degli autori (home, schede, Public Domain Day):** scripts/verifica.py prende la decisione dal registro; ricalcola solo per chi nel registro non c'è ancora. Prova in locale: elenchi e esiti identici a prima (0 differenze).
- **Calendario:** resta curato a mano. Il registro ora contiene anche le persone degli anniversari di morte; docs/da-decidere.md (sezione 5b) segnala un anniversario con un anno diverso da quello del registro.
- **Aggiornamento:** il registro gira il 1° di ogni mese, prima dello Storico (il 2).
- **Errori:** gravi 0; medi 0 (le 2 opere sul confine ora sono «da verificare»).

## 20/11/2026 — Giri più leggeri: scaffali e coautori una volta al mese
- **Problema:** il giro «Pagina Già pubblici» delle 16:10 ha impiegato 118 minuti negli scaffali (di solito 40-55) e 35 nei coautori (di solito 10). Nel dettaglio dei coautori: 17 risposte «troppe richieste» (429), 502 e tempo scaduto di Wikidata, dopo cinque giri in un giorno. Negli scaffali la causa non si poteva vedere: il programma riprovava senza scriverlo.
- **Correzione:** gli scaffali non si rifanno se il file è già del mese in corso (le visite sono mensili); i coautori si rileggono solo se il file è di un mese prima, se era incompleto o se sono cambiati gli autori delle schede o le opere dell'archivio. FORZA=1 rifà comunque. Ogni «aspetta» o risposta mancata viene contata e scritta alla fine del giro.
- **Prova in locale:** scaffali saltati («già aggiornati questo mese»). Il sito non cambia.

## 20/11/2026 — Registro unico, parte 2a: coautori in un posto solo
- **Prima:** la regola dei coautori era scritta tre volte: nella pagina Già pubblici (JavaScript), nello Storico (storico/per_autore.py) e nelle schede autore (scripts/pagine.py).
- **Ora:** una sola regola, scripts/regole.py autori_che_contano(). Lo Storico e le schede la chiamano; per Già pubblici storico/registro_opere.py scrive le decisioni in data/registro/opere.json (968 opere: 550 gruppi con membri, 72 autori che non contano, 50 coautori senza data, 49 antichi, 251 con musica) e la pagina le applica soltanto.
- **Prova:** stato in Europa di tutte le 82.545 opere con la regola vecchia e con la nuova: 0 differenze. Schede autore con note: 72 prima, 72 dopo; pagine delle schede rifatte identiche al bit. La funzione della pagina provata con node sui dati veri.

## 20/11/2026 — Registro unico, parte 2b: anni USA in un posto solo
- **Prima:** due file letti in modi diversi: data/us-anni-verificati.json (liste dei prossimi anni, scripts/verifica_anni_usa.py) e data/storico/anni_verificati.json (Storico, storico/verifica_anni.py). Avevo detto che non avevano opere in comune: sbagliato (avevo contato male). Ne hanno 3, e in due casi davano risposte diverse.
- **Ora:** una regola sola, scripts/regole.py anno_usa_confermato(): vale l'edizione confermata più vecchia (come per la Duke). Le pagine leggono da scripts/registro.py (anni_usa); Già pubblici legge data/registro/opere.json, parte "usa". I due raccoglitori restano (metodi diversi: quello delle liste usa anche il registro del copyright americano, BnF, K10plus, ISFDB).
- **Prova:** sulle 3.493 opere dello Storico controllate cambiano 2 stati, entrambi in meglio: «The Decision» (Q318208) diventa libera negli USA (K10plus: 1930); Q112276362 passa da «da verificare» a «libera dal 2027» (registro del copyright americano: 1931). L'opera da tre soldi resta libera (Duke 1928). Schede autore: identiche. Una prima versione cambiava per sbaglio la data «libero dal» di 19 schede (usava l'anno dell'edizione confermata invece di quello dell'opera): corretto prima di pubblicare.
- **Da fare:** dare allo Storico lo stesso metodo forte delle liste (oggi 1.859 opere dello Storico restano «da verificare» negli USA).

## 20/11/2026 — Anni USA delle liste: Wikipedia non vince più sulle fonti autorevoli
- **Errore trovato** unendo i due file degli anni USA: «L'opera da tre soldi» risultava «non confermato» nella lista 2027, anche se Duke e K10plus davano entrambi 1928. Colpa di una riga di Wikipedia sulle «puntate» (1929), che faceva fermare la decisione prima di guardare le fonti autorevoli.
- **Correzione** (scripts/verifica_anni_usa.py, decidi): quando Wikipedia da sola porterebbe a «non confermato», se una fonte autorevole (Duke, registro del copyright, BnF, K10plus, ISFDB) dà un'edizione uscita prima, l'esito è «uscito prima».
- **Prova:** decisione rifatta su tutte le opere delle liste 2027 e 2028 con i dati salvati: cambia 1 sola opera, L'opera da tre soldi (nd → uscito prima, Duke 1928). Le altre coincidono con il salvato. Va tra le decisioni di Marco (docs/da-decidere.md, sezione 2, che ora si calcola dai dati veri e non dal riepilogo dell'ultimo giro).

## 20/11/2026 — Prova: fonti forti sugli anni USA dello Storico
- **Come:** scripts/prova_storico_usa.py (giro 44806919624, 110 minuti, non cambia il sito). Opere dello Storico libere solo negli USA e non confermate (2.153: 1.859 «nessuna conferma», 294 «solo edizioni più tarde»), provate con le fonti delle liste: registro del copyright americano (volumi 1923-1930), BnF per le opere francesi, K10plus per le tedesche, ISFDB per riviste e racconti. Conferma = un'edizione uscita entro il 1930 con stesso titolo e stesso autore.
- **Risultato:** provate 1.257 su 2.153 (tempo finito). Confermate 114 (9%): ISFDB 62, K10plus 31, BnF 16, registro del copyright 5. Niente trovato 1.133; solo edizioni dopo il 1930: 10. Stima su tutte: circa 190-200 opere in più «libere negli USA».
- **Controllo a mano** di 40 conferme (titolo, autore, anno della fonte contro quello noto): nessun abbinamento sbagliato evidente (Essere e tempo 1927, Ich und Du 1923, Alexis 1929, Sotto la ruota 1906, Il caso dei cioccolatini avvelenati 1929...). Le fiabe dei Grimm confermate erano già libere in Europa con la regola dei coautori.
- **Giudizio:** guadagno vero ma modesto (circa il 9%); il resto sono opere poco note che nessun catalogo aperto ha. Rischio grave (falso abbinamento) basso nel campione, ma non zero: le conferme ISFDB valgono per riviste e racconti, dove i titoli brevi possono coincidere.

## 21/11/2026 — Prova di pulizia dello Storico (giro 44829240505, 115 minuti, non cambia il sito)
- **Enciclopedie e riviste:** 1.311 opere dell'archivio sono, su Wikidata, «opere di consultazione», dizionari, periodici, riviste, enciclopedie o giornali. La classe «opera di consultazione» è troppo larga: prende anche gli Elementi di Euclide, la Summa Theologiae, l'Anabasi, Il Federalista. Regola proposta: togliere solo enciclopedie, riviste (anche scientifiche e accademiche) e giornali = 356 opere. Tenere le 165 che sono solo «periodico» (spesso narrativa uscita a puntate: Varney il vampiro, gli almanacchi di fiabe di Hauff, Il Federalista). Zona grigia da chiedere a Marco: i dizionari biografici (per esempio le «Vite dei pittori» di Karel van Mander).
- **Testi senza autore:** 3.554. Di questi, 2.043 sono già liberi (usciti entro il 1855). 701 hanno un autore dichiarato anonimo o «valore sconosciuto»: per la legge europea un'opera anonima è libera 70 anni dopo la pubblicazione (Direttiva 2006/116/CE, art. 1, c. 3). Con questa regola diventano libere in Europa 210 opere (Beowulf, Dhammapada, Didaché, Testi delle piramidi, Edda...). La regola non si applica alle opere a cui Wikidata semplicemente non mette l'autore: lì serve la data di creazione prima del 1856 (13 opere) o il controllo a mano.
- **Titolo originale:** provate 515 opere su 1.878 (le più note per prime). Confermate 86 (17%; tra le prime 200, 44). Fonti: Open Library 52, ISFDB 15, K10plus 9, registro del copyright 4, BnF 4, Library of Congress 2. Controllo a mano di 45 conferme: tutte giuste (Sein und Zeit 1927, Narziß und Goldmund 1930, Platero y yo 1914, Veinte poemas de amor 1924, Doña Bárbara 1929, Ich und Du 1923...). Alcune fonti danno un anno più vecchio di quello vero (Unterm Rad: Open Library 1900, vero 1906): non cambia la conclusione (uscita entro il 1930), ma vuol dire che l'anno della fonte non va mostrato come anno dell'opera.

## 21/11/2026 — Storico: via enciclopedie e riviste, testi antichi e opere anonime, titolo originale nel controllo mensile
- **Decisioni di Marco:** togliere enciclopedie (anche i dizionari biografici), riviste e giornali; applicare la regola delle opere anonime e segnare come antichi i testi controllati a mano.
- **Enciclopedie e riviste:** 356 opere tolte dallo Storico (storico/applica_registro.py, togli_consultazione; elenco aggiornato ogni mese da storico/coautori.py; storico/storico.py non le fa più entrare). Restano i 165 «periodici» che sono narrativa a puntate.
- **Testi antichi e opere anonime** (scripts/regole.py, opera_antica; data/opere_antiche.json per quelli a mano, con la fonte): libera dappertutto se a mano (8 opere, 5 autori), o se Wikidata dà una data di creazione più vecchia di 171 anni e nessun autore ha una data; opera anonima dichiarata = libera in Europa 70 anni dopo la pubblicazione (Direttiva 2006/116/CE, art. 1, c. 3; in Spagna, per prudenza, 80), negli USA la solita regola. «Canto dell'India» è «Sare Jahan se Accha» di Muhammad Iqbal (1877-1938, fonte Wikipedia): aggiunto come autore in data/coautori_manuali.json.
- **Prova in locale:** in Italia 229 opere passano da «non lo sappiamo» a libere (Beowulf, Dhammapada, Al-Fātiḥa, Qoèlet, Didaché, Testi delle piramidi, Mabinogion, Tosefta...); negli USA 222 da «da verificare» a libere (solo testi antichi; le anonime seguono la regola dei 95 anni). Nessuna opera libera smette di esserlo.
- **Titolo originale:** entra nel controllo mensile degli anni USA dello Storico (storico/verifica_anni.py, quarta fase, prima le opere più note); le 86 conferme della prova portate nei dati. Le conferme di Duke, Library of Congress e fonti forti non vengono più cancellate da un ricontrollo di Open Library.

## 21/11/2026 — Le due opere della Duke che non confermavamo
- **Cup of Gold (Steinbeck, 1929):** Wikidata ha il titolo con il sottotitolo lungo («... A Life of Sir Henry Morgan, Buccaneer, with Occasional Reference to History»); i cataloghi hanno «Cup of Gold». Sul sito era libera negli USA solo grazie alla Duke. Correzione: si cerca il titolo senza sottotitolo (storico/verifica_anni.py, titolo_cercato; usato anche in scripts/verifica_anni_usa.py).
- **The Roman Hat Mystery (Ellery Queen, 1929):** su Wikidata gli autori sono Manfred B. Lee e Frederic Dannay; lo pseudonimo non è sugli autori ma è una voce a parte che li ha come membri (P527). La voce Duke non veniva collegata all'opera di Wikidata, e l'opera compariva due volte nello Storico. Correzione: pseudonimi letti da Wikidata (P742 e voci di cui l'autore è membro) e usati nelle ricerche e nel collegamento della Duke (storico/duke.py, risolvi; i libri non collegati si riprovano una volta).
- **Prova** (scripts/prova_due_duke.py, senza la Duke): Cup of Gold confermata da registro del copyright, Open Library e Library of Congress (1929); The Roman Hat Mystery da registro del copyright e Open Library (1929), e la voce Duke ora si collega a Q1147884. Il doppione sparisce al prossimo giro dello Storico (2 dicembre).
- **Classifica a prova di picchi:** tolta dalle cose da fare (decisione di Marco: inutile, i nomi in vetrina li sceglie lui).

## 21/11/2026 — Errore trovato: l'elenco delle enciclopedie si svuotava
- **Cosa:** nel giro 44879812411 il passo dei coautori ha letto «0 enciclopedie, riviste e giornali», perché le 356 opere erano già state tolte dall'archivio e Wikidata non le vedeva più; il programma ha sostituito l'elenco con quello vuoto. Il sito era giusto, ma al giro mensile dello Storico (2 dicembre) le opere sarebbero rientrate.
- **Correzione:** storico/coautori.py ora somma gli elenchi (enciclopedie e date di creazione) invece di sostituirli; elenco ripristinato (356) dai dati della prova.
- **Giro 44879812411 (titolo originale):** fase nuova partita; restano da provare 1.268 opere; confermate finora con il titolo originale: Open Library 52, Library of Congress 2, più K10plus 9, BnF 4, registro del copyright 4, ISFDB 17.

## 21/11/2026 — SEO: indirizzi con lettere speciali e date della sitemap
- **Da dove:** analisi SEO di Marco (Search Console, 6-19 novembre). Controllata sul sito: confermati i tre problemi; due più larghi del previsto.
- **Indirizzi:** il programma buttava le lettere che la normalizzazione non scompone (ø, ı, ł, ß, æ, đ, ð...): 74 autori nelle liste, 2 con una scheda già pubblicata (Valdemar Rørdam → «valdemar-rrdam», Cahit Sıtkı Tarancı → «cahit-stk-taranc»). Ora le lettere si convertono (scripts/pagine.py, LETTERE). Al vecchio indirizzo resta una pagina di rimando (noindex, canonical e rimando immediato al nuovo), ricordata in data/indirizzi_vecchi.json e riscritta a ogni giro. Prova: cambiano solo quelle 2 schede; nella sitemap ci sono i nuovi indirizzi e non i vecchi; nessun altro link del sito punta ai vecchi.
- **Sitemap:** tutte le 815 pagine avevano la data di ogni giro, perché il conto alla rovescia delle schede cambia ogni giorno. Ora la data è quella in cui il contenuto cambia davvero: impronta della pagina senza conto alla rovescia e senza date di aggiornamento (data/sitemap_date.json). Prova: due giri di fila → sitemap identica; pagina con solo il conto alla rovescia cambiato → stessa impronta; pagina con un dato cambiato → impronta diversa. Al primo giro le date partono tutte da oggi (non c'era una storia).

## 21/11/2026 — Collegamenti interni verso le schede (SEO punto 1, mockup approvato da Marco)
- Cosa: nelle schede, blocco «Altri scrittori liberi dal 1° gennaio AAAA» (6 scrittori dello stesso anno: prima lo stesso paese, poi i più letti su Wikipedia; per gli autori delle liste spagnole «liberi in Spagna», senza link all'elenco). Nella pagina dell'anno (2027, 2028, IT e EN), sezione «Tutti gli scrittori con una scheda» in ordine di cognome con le lettere A–Z (`id="autori"`).
- Come si misura: per ogni scheda italiana, quante pagine del sito la linkano (escluse sé stessa e le pagine di rimando).
- Prima: media 3,0 pagine, minimo 2. Dopo: media 9,6, minimo 3.
- Restano 82 schede con 3 link o meno: sono soprattutto autori delle liste spagnole (morti nel 1946–47), che non hanno una pagina dell'anno con l'elenco. Prova futura possibile: un elenco anche per loro.
- Controllo a vista: desktop e telefono (sul telefono l'elenco è a 2 colonne senza la professione, come nel mockup).

## 21/11/2026 — Controllo giri «Pagina Già pubblici»
- 44883389633: finito bene. Pseudonimi letti per 254 autori. Fase «titolo originale e fonti forti»: 1268 opere provate, confermate 53 con Open Library (titolo originale) e 4 con Library of Congress (titolo originale). Totale confermate 1405.
- Enciclopedie tolte: 0. Atteso: in quel giro l'elenco era stato svuotato (errore già corretto, elenco ripristinato con 356 voci). Le toglie il giro successivo.
- 44885040526 (avviato dalla correzione): in corso alle 09:29 UTC, fermo sulla fase degli anni USA (~40 minuti). Ricontrollo alle 09:55 UTC.

## 21/11/2026 — Frase di risposta in cima alle schede (SEO punto 3, mockup approvato)
- Cosa: sotto il nome, una frase con la risposta («Le opere di X diventano di pubblico dominio in … il 1° gennaio AAAA; in Spagna …; negli USA dipende…»), scritta dai dati della scheda. Varianti controllate: autore già libero, Spagna più tardi dell'UE, autore di paese alleato (Italia «va verificato»), inglese.
- Tolta la domanda «Quando X entra in pubblico dominio in Italia?» dalle «Risposte brevi», perché ripeteva la stessa frase. La sezione resta solo nelle 47 schede che hanno opere già libere negli USA. Restano il riquadro rosso e le date paese per paese (grafica e dettaglio).
- Controllo: 408 schede IT e 395 EN generate, nessuna senza frase; viste a schermo Brecht (IT/EN) e Döblin (alleato).
- 44885040526: finito bene. Elenco enciclopedie e riviste: 356 voci; tolte 0 perché erano già state tolte: nessuna delle 356 è ancora nell'archivio, nella ricerca o nelle pagine per autore (controllato a mano). Titolo originale: 1182 provate; confermate in totale 61 con Open Library e 5 con Library of Congress (+8 rispetto al giro prima). Pseudonimi: 254 autori. Opere confermate in totale 1417 (prima 1405). Schede autore dopo il Salva: blocco «Altri scrittori» e frase di risposta presenti.

## 21/11/2026 — Logo: RDR al posto di PDR
- Perché: «PDR» è anche la sigla di The Public Domain Review (publicdomainreview.org), nel nostro stesso campo. Nome del sito e dominio restano uguali.
- Scelto da Marco dopo i mockup: sigla RDR, taglio sull'ultima R come lancetta del radar, «solo taglio bianco» (senza punto e senza lancetta piena nel buco).
- Come è fatto: scripts/logo.py prende le lettere dal carattere già usato dal sito (Big Shoulders Display, peso 900), misura il centro del buco della R sul disegno della lettera e fa partire il taglio esattamente da lì, a 40 gradi, spessore 3,7. Scrive assets/logo-rdr.svg e assets/favicon.svg. La scritta «Public Domain Radar» sotto ora corre per tutta la larghezza della sigla.
- Controllo: tracciata sopra al logo la retta della lancetta: passa per il centro del buco e sta al centro del taglio. Viste a schermo testata della home, scheda autore (telefono), Già pubblici, calendario e icona.

## 21/11/2026 — Scheda autore col nuovo design (solo in locale, non pubblicata)
- Come: scheda rigenerata con scripts/pagine.py + scripts/stile_scheda.css; confronto automatico con la versione online (titolo, h1, descrizione, canonical, dati strutturati, link interni, frasi).
- Risultato: 803 pagine (408 IT, 395 EN). Titolo, h1, descrizione, canonical e dati strutturati identici; 0 link interni persi. Frasi segnalate: quasi tutte il vecchio piede di pagina (ora nel menu e nel nuovo piede) e «Su N opere registrate in Wikidata» diventata «Le più note delle N su Wikidata».
- Casi speciali visti: Döblin (paese alleato, avviso giallo), Mörne (già libero in UE, conto verso la Spagna), Brecht EN, telefono 390 px: nessuna pagina più larga dello schermo, nessun errore JavaScript.
- Giudizio: pronta per l'ok di Marco. Le foto in locale non si vedono perché qui non c'è rete (vengono da Wikimedia): online si vedono.

## 21/11/2026 — Indice degli autori col nuovo design (solo in locale, non pubblicato)
- Come: pagina_indice riscritta in scripts/pagine.py + scripts/stile_indice.css. L'elenco completo resta scritto nella pagina (Google lo legge); i due filtri (Paese, Libero dal) nascondono solo le voci, con la regola 70 anni (morte+71) e Spagna 80 anni (morte+81).
- Confronto con la pagina online (IT e EN): titolo, descrizione, canonical, h1 identici; 0 link persi; aggiunto il link alla versione in altra lingua.
- Prove filtri (telefono): tutti 408; Italia 2027 = 122; Spagna 2027 = 90; tutti 2028 = 196; Spagna tutti gli anni = 162; Regno Unito 2028 = 124. Coincidono con gli anni di morte nell'elenco (1946: 90, 1947: 72, 1956: 122, 1957: 124). Nessun errore JavaScript, nessuna pagina più larga dello schermo.
- Effetto collaterale: le 803 schede cambiano di una riga nel codice (piede: controllo che il nome esista, serviva per l'indice). Nessun cambiamento visibile.

## 21/11/2026 — Pagine Pubblico dominio 2027 e 2028 col nuovo design (solo in locale, non pubblicate)
- Come: pagina_landing in scripts/pagine.py riscritta con la struttura del mockup rdr-2027-indice.html + scripts/stile_anno.css. Tutti i testi restano scritti nella pagina (anche le risposte brevi e l'elenco A–Z); il contatore dei giorni è in alto.
- Confronto con la versione online (4 pagine, IT/EN, 2027/2028): titolo, descrizione, canonical, hreflang, h1, dati strutturati (FAQ) identici; 0 link persi; 0 titoli di sezione (h2) persi. Le frasi segnalate dal confronto sono solo testi spezzati in modo diverso (numeri, righe della tabella paesi).
- Telefono 390 px e computer: nessun errore, nessuna pagina più larga dello schermo. Corretti durante la prova: contatore in alto che andava a capo sul telefono (ora solo «tra N giorni»), etichetta «anno da confermare» spezzata su due righe.
- Effetto: anche le schede autore e l'indice vengono rigenerati, ma senza cambiamenti (solo i parametri della funzione comune).

## 21/11/2026 — Calendario 2027 col nuovo design (solo in locale, non pubblicato)
- Come: pagina() e scheda() in scripts/calendario.py riscritte sul mockup rdr-calendario-indice.html + scripts/stile_cal.css. Ogni voce è una riga (giorno, nome, tipo); i dettagli (paese, anni, descrizione, opere, Nobel, Wikipedia) restano scritti nella pagina e il pannello a destra (in basso sul telefono) li mostra. «Crea scheda →» diventa «Condividi →» (scripts/schede.py).
- Confronto con la versione online (IT ed EN): titolo, descrizione, canonical, hreflang, h1, dati strutturati identici; 0 link persi; 232 titoli delle voci (h3) tutti presenti; i 14 titoli dei mesi restano, con «·» in più tra anno e numero di voci.
- Prove: filtro Morti + 100 anni = 15 voci, uguale al conteggio nel file dei dati; «Condividi» dal pannello apre la scheda da condividere (computer e telefono); barra dei mesi e mese in alto seguono lo scorrimento; nessun errore, nessuna pagina più larga dello schermo (1280 e 390 px).
- I file .ics e .csv non cambiano.

## 21/11/2026 — Già pubblici col nuovo design (solo in locale, non pubblicato)
- Come: storico/pagina.html (stessa ricerca e stesse regole per paese di prima, codice JavaScript invariato nella logica) con nuova grafica: apertura «È già libero?» con ricerca grande ed esempi da provare, paesi, risultati con 6 caselle paese per paese, scaffali a schede con copertine che scorrono, classifica autori con ritratto, generi e lingue come indice. Stile in storico/stile_gia.css; testata, menu e piede comuni (scripts/pagine.py). Lo fa storico/pagina.py, come prima.
- Confronto con la versione online: titolo, descrizione, canonical, hreflang identici; il titolo principale (h1) prima era vuoto nel codice della pagina (lo scriveva il JavaScript) e ora è scritto: Google lo legge subito. Spariscono solo i link /#/2027 e /#/2028 della vecchia barra (il menu porta alle pagine 2027 e 2028 vere).
- Prove (computer e telefono): ricerca Kafka, Brecht (autore non ancora libero: compare il rimando alla scheda), Il grande Gatsby (finestra paese per paese), cambio paese Spagna, scaffali, classifica, generi. Nessun errore JavaScript, nessuna pagina più larga dello schermo.
- Errori trovati e corretti (c'erano già sul sito): 1) ritratti della classifica e avviso «non è ancora libero» non comparivano mai, perché l'istruzione che li carica era finita dentro un commento; 2) nella finestra di un'opera senza note compariva la scritta «null».

## 21/11/2026 — Home (radar) col nuovo design «Indice» (solo in locale, non pubblicata)
- Come: index.html rifatto nella grafica (stile, struttura, funzioni di disegno) sul mockup pdr-home-completa.html; dati, regole, filtri, anni, paesi, USA, preferiti, Excel e indirizzi (#/2027, #/autore/…, #/us/…, #/opera/…, #/genere/…) sono quelli di prima. en/index.html rigenerato da scripts/pagine.py come sempre.
- Decisioni di Marco: «I nomi più grandi» dal 13° al 19° (niente doppioni con l'indice dei primi 12); «Per paese» diventa «Paese d'origine».
- Correzioni rispetto al mockup: logo RDR; testata piena quando compare la barra fissa (prima si vedeva il testo sotto); scheda autore come la scheda del sito (conto alla rovescia in grande, date nella tabella, niente rosso scuro); «Ordine: interesse in Italia»; conteggio Excel = conteggio dell'elenco; fila dei nomi con margine sul telefono; titolo principale scritto nella pagina.
- Confronto con la versione online (IT ed EN): titolo, descrizione, canonical, hreflang, dati strutturati, blocco di testo per Google (12 nomi con link) identici; 0 link persi. Il titolo principale è lo stesso; tolto un secondo h1 vuoto che c'era prima.
- Prove automatiche (computer 1280 e telefono 390): scheda dalla riga dell'indice e dall'indirizzo #/autore/bertolt-brecht; USA (169 opere, ricerca, scaffali); Spagna (782 scrittori morti nel 1946); Da scoprire; cuore e «I miei»; Excel (825); filtro paese d'origine; scaffale → scheda dell'opera; anno 2028 (838 scrittori morti nel 1957). Nessun errore, nessuna pagina più larga dello schermo.
- Archivio: 40 nomi per volta invece di 120 (come nel mockup), poi «Mostra altri 120».

## 21/11/2026 sera — Ricerca di Già pubblici: tutte le parole del titolo, autori Duke uniti (solo in locale, non pubblicato)
- Come: storico/chiavi.py (nuova regola unica), usata da storico/storico.py e da storico/applica_registro.py (riordina i file della ricerca già pronti); la pagina (storico/pagina.html, funzione chiavi) cerca con le stesse parole da saltare (articoli, preposizioni). Dati rigenerati dopo l'aggiornamento automatico delle 17:04.
- Risultato: 82.189 opere, 575 file. Ogni opera è sotto ogni parola che conta del titolo. 16 autori «finti» della Duke uniti al loro autore vero (Virginia Woolf, Marcel Proust… non compaiono più due volte).
- Prove nella pagina: «Pinocchio» ora trova «Le avventure di Pinocchio» (prima niente); «Virginia Woolf» un solo autore (prima due); «promessi sposi», «guerra e pace», «the waves», «anna karenina» trovati. Nessun errore.
- Costo: i file della ricerca passano da 14 a 31 MB in tutto, ma ogni ricerca ne scarica solo 1–3 (per esempio «pi» da 54 a 136 KB). Il più grande resta «th» (1,1 MB, come prima); «dn» è 1,1 MB per le 10.879 voci del Dictionary of National Biography, da togliere con la prova DNB.

## 21/11/2026 sera — Telefono: più respiro su tutte le pagine (solo in locale, non pubblicato)
- Come: un blocco di regole per schermi fino a 860 px aggiunto in fondo a tutti i fogli di stile (scheda, anno, calendario, indice, Già pubblici, home): titoli grandi con interlinea .96 invece di .82 (le righe non si toccano più), voci del menu più piccole e distanziate, righe dell'indice più alte, ritratto che scorre più piccolo e più in basso, sezioni più distanziate. Barra fissa della home sul telefono: solo i valori («Italia · Interesse in Italia»), senza i due punti rimasti.
- Prova: schermate a 390 px di home (apertura, indice, menu), scheda Brecht, 2027, calendario, Già pubblici, indice autori. Nessuna pagina più larga dello schermo.

## 21/11/2026 sera — Già pubblici: via le voci di enciclopedia, nomi italiani degli autori (codice pronto, non ancora lanciato)
- Da dove: prova DNB e nomi (docs/stima-sito/prova-dnb-nomi.json, 18 minuti su GitHub). 25.673 opere dell'archivio sono voci di enciclopedia o dizionario (classi Wikidata «voce biografica» Q19389637, «voce di enciclopedia» Q13433827, «voce di dizionario» Q1580166), di cui 10.872 del Dictionary of National Biography; tutte con al massimo 2 pagine Wikipedia, nessun libro vero. 3.114 autori su 17.567 hanno un nome italiano diverso dall'inglese (Esopo, Lev Tolstoj, Platone…).
- Come: storico/coautori.py aggiunge le tre classi a CONSULTAZIONE (stessa regola già usata per enciclopedie, riviste e giornali) e rilegge se le classi cambiano; storico/nomi_it.py (nuovo) scrive data/storico/nomi_it.json con i soli nomi italiani diversi; storico/applica_registro.py li mette nei file della ricerca (la ricerca trova «Tolstoj» e «Tolstoy»); storico/pagina.html mostra il nome italiano sulla pagina italiana.
- Prova in locale con due nomi finti nel file (Q7243 Lev Tolstoj, Q43423 Esopo): «Tolstoj», «Tolstoy», «Esopo», «Aesop» trovano l'autore giusto col nome italiano; la classifica mostra «Lev Tolstoj». Dati di prova poi tolti: quelli veri li scrive il giro su GitHub.

## 21/11/2026 sera — «Morti per la Francia»: si riconoscono con dati aperti? (prova, non cambia il sito)
- **Come:** scripts/prova_mpf.py, lanciato con stima.yml (commit ee9975a0, 23 secondi). Cerca su Wikidata chi ha «premio ricevuto» (P166) = mort pour la France (Q3324507), lo incrocia con i nostri 21.002 autori (Già pubblici + 2027 + 2028) e confronta con gli autori marcati a mano su Wikisource francese (modello «Auteur Mort pour la France»). Risultati: docs/stima-sito/prova-mpf.json.
- **Numeri:** 2.300 persone col titolo su Wikidata (1.547 morte nel 1939-45, 635 nel 1914-18). Tra i nostri autori: 11, tutti in Già pubblici (nessuno in 2027/2028). 7 sono della Seconda guerra e quindi ancora protetti in Francia: Politzer, Némirovsky, Allatini, Saint-Exupéry, Bloch, Desnos, Messac. I nostri autori morti negli anni di guerra sono 1.736.
- **Completezza:** i 22 autori marcati su Wikisource hanno tutti il titolo su Wikidata, ma è un elenco piccolo. Wikidata ne perde almeno uno: Louis Pergaud (1915) è «mort pour la France» per il sito del Ministero (cheminsdememoire.gouv.fr) ma su Wikidata non ha il titolo. Nessun autore ha su Wikidata la data di libertà francese calcolata con questo criterio (0).
- **Giudizio:** Wikidata va bene per mettere la data francese esatta a chi ha il titolo (nessun falso trovato), non basta per dire che gli altri non lo sono: per i morti del 1939-45 senza titolo resta l'avviso generico. Per completare: incrocio con la base del Ministero (Mémoire des hommes, scaricabile in CSV) su nome + date esatte di nascita e morte.

## 21/11/2026 sera — Già pubblici: «morti per la Francia» riconosciuti con Wikidata (solo in locale, non pubblicato)
- **Cosa cambia:** nuovo storico/mpf.py (passo nel workflow gia-pubblici, prima del registro) scrive data/registro/mpf.json con i nostri autori che su Wikidata hanno P166 = Q3324507. La pagina lo legge: per questi autori la Francia non è più «libero» ma «da verificare», con la spiegazione (CPI art. L123-10; la data esatta dipende dall'anno di uscita di ogni opera, quindi non la scriviamo). Nella scheda autore la riga «Italia, Francia, Germania, Regno Unito» diventa «Italia, Germania, Regno Unito» più una riga sulla Francia. Per i morti del 1939-45 senza titolo resta l'avviso, riscritto: «su Wikidata non risulta, ma l'elenco può essere incompleto».
- **Regola usata:** non libero in Francia finché morte + 101 > anno in corso (lettura più prudente: 70 + 30 anni). Le date esatte variano: per Saint-Exupéry fonti diverse dicono 2032 o 2033.
- **Prove (pagina in locale, Chrome):** «Il piccolo principe» prima risultava LIBERO in Francia, ora DA VERIFICARE con la spiegazione; schede di Némirovsky, Desnos, Saint-Exupéry (anche in inglese) corrette; Joseph Odolant Desnos (morto nel 1849) invariato. Nessun errore nella pagina. Gli 11 autori di partenza vengono dalla prova precedente (stessi dati Wikidata); il workflow li riprende da Wikidata a ogni aggiornamento.
- **Errori gravi corretti:** 7 autori della Seconda guerra (e le loro opere) risultavano liberi in Francia senza esserlo. Errori nuovi introdotti: nessuno trovato. Resta un limite noto: chi è «morto per la Francia» ma non segnato su Wikidata (es. Pergaud, già libero) non viene riconosciuto.

## 21/11/2026 sera — Controllo dopo i giri di Già pubblici (74c69d44: voci di enciclopedia, nomi italiani)
- **Giri:** 44928297536 (18:07) e 44931457782 (74c69d44) finiti bene.
- **Numeri:** opere nell'archivio da 82.189 a 56.516 (−25.673, esattamente le voci di enciclopedia e dizionario previste dalla prova DNB); voci di consultazione segnate in coautori.json: 26.029; nomi italiani: 3.114.
- **Telefono:** le regole «più respiro» ci sono in Già pubblici (it/en) e in 409 schede autore su 411; le 2 senza sono vecchi rimandi a indirizzi nuovi (pagine vuote che reindirizzano), non schede.
- **Ricerche (Chrome, in locale):** Tolstoj, Esopo, Joyce: nessuna voce DNB, nessun errore. Trovato un difetto vecchio: Esopo appare «morto nel -563 · libero dal -492» (anni prima di Cristo scritti col meno); da correggere.

## 21/11/2026 sera — Open Library: quante opere in più per i nostri autori? (prova, non cambia il sito)
- **Come:** scripts/prova_openlibrary.py con stima.yml (commit 0054b0d7, 19 minuti). Codici Open Library (P648) dei nostri autori da Wikidata; lettura completa del file mensile delle opere di Open Library (41,7 milioni di righe) tenendo quelle dei nostri autori; titoli unici per autore dopo pulizia (minuscole, accenti, articolo, sottotitolo). Risultati: docs/stima-sito/prova-openlibrary.json.
- **Numeri:** 12.290 autori collegati su 17.567. 1.316.025 righe-opera; 794.209 titoli «unici» dopo la pulizia, contro 49.327 opere che gli stessi autori hanno oggi (circa 16 volte tanto).
- **Qualità (dai campioni):** molto rumore. 1) «Autori» che sono enti (Camera dei rappresentanti USA 36.203 titoli, Servizio geologico USA, Hôtel Drouot, Chiesa cattolica, Francia). 2) Antologie, raccolte e traduzioni con titoli diversi contate come opere («5 minutes stories aesop s fables», «40 fiabe di andersen», «12 plays and merchant of venice»). 3) Attribuzioni sbagliate (sotto Čechov «75 facts about apj abdul kalam»; sotto Dickinson un titolo osceno). Esempi buoni: Alfieri 202 titoli quasi tutti opere vere (Abele, Agamennone, Agide, Alceste, Antigone...).
- **Giudizio:** il numero vero di opere singole è molto più basso di 794.209 e oggi non si può stimare con onestà. Serve un secondo giro con tre filtri: solo persone (non enti), solo opere uscite entro la morte dell'autore (taglia antologie e traduzioni postume), unione delle traduzioni tramite gli identificativi di Wikidata quando ci sono.

## 21/11/2026 notte — Nuova home «frontespizio», radar spostato su /radar/ (solo in locale, non pubblicato)
- **Cosa cambia:** la home (index.html, en/index.html) è il frontespizio approvato (prova 1), scritto da scripts/home.py con i dati delle liste: opere scelte (Brecht ×2, Milne, Walser in Europa; Buck, Woolf, Saint-Exupéry negli USA, solo con l'anno 1931 confermato dal registro). Sotto, nello stile del resto del sito (solo il frontespizio è in Garamond, su richiesta di Marco): i numeri del 2027 (826 / 790 / 169, 111 confermati: gli stessi della pagina 2027) e le quattro sezioni; testata e piede sono quelli delle altre pagine. Il radar (l'app con i filtri) è passato da index.html a radar/index.html ed en/radar/index.html; canonical, hreflang e og:url aggiornati; il marchio nel radar porta alla home.
- **Programmi aggiornati:** scripts/pagine.py (lettura e scrittura del radar, menu «Il radar», link «/#regole-paesi» e «/#/autore/…», sitemap con /radar/ e /en/radar/, chiamata a home.py), scripts/calendario.py, scripts/etichette.py, storico/pagina.py, .github/workflows/aggiorna.yml (ripristino in caso di dati incompleti). Caratteri: EB Garamond (OFL) in assets/fonts, aggiunto a fonts.css.
- **Vecchi indirizzi:** la home manda al radar chi arriva con # (es. /#/autore/Q38757 → /radar/#/autore/Q38757; /en/#/2027 → /en/radar/#/2027) e chi arriva con ?lang=en va su /en/.
- **Prove (Chrome, server locale):** 13 indirizzi aperti (home it/en, radar it/en, rimandi con #, ?lang=en, pagine 2027 it/en, scheda Brecht, calendario, Già pubblici): nessun errore, nessuna pagina che esce dallo schermo. 899 link interni in 11 pagine controllati: nessuno rotto. pagine.py e storico/pagina.py rigirati per intero: nelle 805 schede autore cambiano solo i link al radar. Sitemap: 817 indirizzi, con /radar/ e /en/radar/.
- **Rischi noti:** su Google la home portava 9 clic in due settimane (Search Console, 5–21/11); il calendario inglese, che porta più della metà dei clic, non cambia.
- **Aggiunte dopo i commenti di Marco (21/11/2026 notte):** sotto il frontespizio numeri e sezioni centrati nella loro cella (griglia 2×2); «Il radar» diventa «Tutti gli autori» nella home e nei menu; la pagina dell'anno dopo (2028) sparisce dai menu e dalle schede del radar fino al 1° gennaio 2027 (resta online per Google e raggiungibile con /radar/#/2028). Riprova: 903 link in 11 pagine, nessuno rotto; 10 indirizzi nel browser senza errori.

## 21/11/2026 — Radar: ritratto in ritardo e copertine disallineate (telefono)
- **Problema 1:** sul telefono il ritratto stava più in basso della riga che decideva il nome acceso (metà schermo), quindi accanto al n. 09 c'era ancora la foto del n. 08. In più il cambio era una tendina lenta (460 ms + 900 ms di zoom).
- **Correzione:** la riga accesa ora è quella all'altezza del centro del ritratto; il cambio è una dissolvenza di 260 ms che parte nello stesso istante in cui cambia il nome.
- **Problema 2:** le copertine sono pulsanti e una regola le metteva in `display:block`: il browser centrava il contenuto in altezza, così le copertine con didascalia più corta scendevano di circa 9 px. Sul telefono, inoltre, la copertina toccata restava sollevata (effetto «hover»).
- **Correzione:** contenuto allineato in alto (flex in colonna); effetti al passaggio del mouse solo su dispositivi con mouse.
- **Prova (Playwright, 390 px telefono e 1440 px desktop):** 8 scaffali × tutte le copertine: stessa altezza e stesso bordo superiore (differenze di 1 px solo per arrotondamento). Elenco autori a 30 passi di scorrimento: il nome acceso è sempre accanto al ritratto (0 casi fuori). Nessun errore JavaScript.
- Errori gravi/medi rimasti noti su queste due parti: 0.

## 21/11/2026 — Classifica spiegata meglio; ritratti degli autori al posto delle copertine finte (libri USA)
- **Testo:** «più letti su Wikipedia» faceva pensare che la gente leggesse le opere su Wikipedia. Ora si dice qual è la misura: visite alla pagina Wikipedia dell'autore negli ultimi 12 mesi (5 lingue nella pagina dell'anno, la lingua del paese nel radar), che dice quanto un autore è conosciuto oggi, non quanto vende. Per i libri USA: visite alla pagina del libro su Wikipedia in inglese. Cambiato nella pagina dell'anno (it/en), nel radar («I più noti in…» + una frase di spiegazione; ordine USA «Più visitate su Wikipedia») e nelle 803 schede autore («poi quelli con la pagina Wikipedia più visitata»).
- **Libri USA:** accanto al titolo acceso c'era una copertina tipografica che ripeteva titolo e autore. Ora c'è il ritratto del primo autore che ne ha uno libero su Commons (Wikidata P18, stesso filtro di licenza delle copertine), con i crediti sotto la lista. Senza ritratto: riquadro con le iniziali (come per gli autori europei).
- **Come arrivano i ritratti:** `scripts/opere.py` li cerca da ora a ogni giro; `scripts/ritratti_usa.py` li aggiunge una volta ai file già raccolti (us-2027, us-2028) e ricrea le pagine, lanciato dal workflow «Stima» (non tocca il resto).
- **Pagina dell'anno:** stessa correzione del radar per il ritratto in ritardo (riga accesa = riga all'altezza del ritratto, dissolvenza 260 ms).
- **Prova (Playwright, 390 px, ritratto di Brecht simulato dai dati europei):** lista autori e lista libri, 25 passi ciascuna: nome acceso sempre accanto al ritratto; crediti corretti; nessun errore JavaScript. Le immagini vere non si caricano in questo ambiente (rete chiusa): da ricontrollare sul sito dopo il giro.

## 21/11/2026 — Autori di paesi alleati: niente data per l'Italia
- **Problema (segnalato da Marco su A. A. Milne):** l'avviso diceva «in Italia va verificato», ma nella tabella paese per paese e nel radar l'Italia mostrava comunque «1° gen 2027»; il frontespizio della home diceva «Libero in Europa».
- **Regola:** Trattato di pace 1947, allegato XV, parte A, punto 3 (testo UK: legislation.gov.uk/uksi/1948/117): per i diritti già in vigore in Italia allo scoppio della guerra, il periodo fino all'entrata in vigore del trattato (15/9/1947) non conta. Al massimo poco più di 7 anni: per prudenza 8.
- **Correzione:** per gli autori di paesi alleati, finché data normale + 8 anni non è passata, l'Italia mostra «da verificare» (schede autore it/en: 159+158; radar, riquadro grande e tabella). Avviso riscritto: «per questo in Italia non diamo una data, va verificata opera per opera». Home: per questi autori «Libero in Francia, Germania e Regno Unito dal 1° gennaio».
- **Prova (Playwright, 390 px):** scheda Milne, radar Milne, home pagina 2 di 7: nessuna data italiana, nessun errore JavaScript.

## 21/11/2026 — Niente più «Europa» nelle date; controllo automatico delle frasi sui paesi
- **Problema:** «Libero in Europa dal 1° gennaio» era impreciso per tutti: in Spagna gli autori morti prima del 1987 hanno 80 anni (Brecht, Walser: 2037), in Italia gli autori di paesi alleati vanno verificati.
- **Correzione:** home: la riga elenca solo i paesi dove l'autore è libero quel giorno, calcolati dai dati (Italia esclusa per i paesi alleati, Spagna solo se l'autore è nella lista spagnola dell'anno). Radar, scheda dell'opera: «Libera in Italia, Francia, Germania e nel Regno Unito dal…» (o senza Italia + «In Italia: da verificare» per i paesi alleati; «in Spagna» per la lista spagnola). Già pubblici, frase sulla musica: Francia, Germania, Regno Unito; Italia e Spagna «può essere più tarda».
- **Controllo nuovo:** `scripts/controllo_frasi.py` cerca in tutte le pagine «libero in Europa dal/free in Europe from» e date italiane per autori di paesi alleati. Sulla versione pubblicata oggi trova 4 frasi nella home, 2 nel radar e la data di Milne; sulla versione corretta 0.
- **Prova (Playwright, 390 px):** home 7 pagine it/en, scheda opera nel radar (Winnie Puh, L'opera da tre soldi): testi giusti, nessun errore JavaScript.

## 21/11/2026 — Già pubblici e radar: copertine, colori, esclusioni, classifica, ritratti
- **Copertina sollevata (Il piccolo principe):** sul telefono restava l'effetto «hover» dopo il tocco. Ora solo con il mouse.
- **Colori in fila:** prima il colore veniva solo dal titolo, quindi capitavano tre bianche di seguito. Ora: mai due dello stesso colore vicine, al massimo due chiare (beige, bianca) o due scure (rossa, nera) di seguito; vale per scaffali e griglie di Già pubblici e per gli scaffali del radar.
- **Titoli spezzati («L'ADOLESCENT-E», «COCCODRILL-O»):** le parole non si spezzano più; se una parola non ci sta, il carattere si rimpicciolisce finché ci sta (misurato nella pagina, anche quando cambia la larghezza).
- **Esclusioni:** aggiunti «La dottrina del fascismo» (Q212143) e Benito Mussolini (Q23559) a data/storico_esclusioni.json: restano nella ricerca, non negli scaffali e nelle classifiche. Cercati altri titoli e autori di propaganda nei dati dello Storico: nessun altro da aggiungere (Bernays «Propaganda» è un saggio sulla comunicazione, resta).
- **Testi:** «dal più letto sulla Wikipedia» → «in ordine di visite alle pagine Wikipedia in italiano delle loro opere libere nella settimana 11–17 novembre 2026», più «misura quanto sono cercate oggi, non quanto si vendono». «I più letti» → «I più visitati»; «più lette» → «con più visite» negli scaffali per lingua e nella descrizione per Google.
- **Ritratti tagliati (Omero, Dante):** riquadro verticale 4:5 e immagine intera (contenuta), mai ritagliata.
- **Prova (Playwright, 390 e 1440 px, 6 paesi × 3 scaffali, griglia di Dostoevskij, 8 scaffali del radar):** colori: 0 ripetizioni vicine, 0 file di tre chiare o tre scure; copertine tutte alla stessa altezza; 0 titoli che escono dalla copertina; nessun titolo sul fascismo; un errore JavaScript trovato e corretto (griglia). Le foto vere non si caricano in questo ambiente: i ritratti vanno ricontrollati sul sito.
- **Ancora aperto:** anni sbagliati di alcune opere nei dati (es. «Alla ricerca del tempo perduto» 2000, «La Repubblica» 1963: sono date di edizioni moderne in Wikidata).

## 22/11/2026 — Regole per paese in un posto solo (scripts/regole.py)
- **Prima:** le regole per paese (70 anni, Spagna 80, «morti per la Francia», USA 95, paesi alleati) erano copiate in schede, home, pagina dell'anno, calendario, radar e Già pubblici, con tre liste di paesi alleati diverse tra loro (es. Etiopia, Scozia, Armenia, Paesi Bassi mancavano in una o nell'altra) e un confine diverso di un anno nello Storico. Il 20/11 avevamo unificato solo anni di morte, coautori e anni USA.
- **Ora:** tutto in scripts/regole.py (anni_protezione, anno_libero, morti_liberi_nel, anno_libero_usa, pubblicate_libere_usa_nel, ALLEATI_1947 unica, italia_da_verificare, paesi_liberi_insieme). Il browser usa assets/regole.js (REGOLE_PAESI), scritto da regole.py a ogni giro delle pagine. Tolti tutti i +71/+81/+96 sparsi (pagine.py, home.py, calendario.py, verifica.py, opere.py, storico/*.py, radar, Già pubblici); cancellate due funzioni morte che avevano copie delle regole (paese_per_paese, scheda_statica).
- **Trattato di pace (riletto):** allegato XV, parte A, punto 3 (testo inglese ufficiale: The Treaty of Peace (Italy) Order 1948, SI 1948/117, legislation.gov.uk): escluso il periodo dallo scoppio della guerra al 15/9/1947 per i diritti in vigore allo scoppio della guerra o riconosciuti dall'allegato. Regola: opere uscite fino al 1947, proroga prudente 8 anni.
- **Regola nuova:** cittadinanza non nota = «da verificare» in Italia (non possiamo escludere che fosse di un paese alleato). Nuovo scripts/cittadinanza.py: chiede a Wikidata la cittadinanza di tutti gli autori delle liste (prima solo gli scrittori arricchiti), così «non nota» vuol dire davvero assente su Wikidata.
- **Prova di equivalenza (scripts/prova_regole.py --prima-dopo):**
  - gemelli Python/browser: 31.521 confronti, 0 differenze (la prima versione ne ha trovate 9: il radar traduceva i paesi nei nomi attuali e perdeva «Impero russo» per gli autori baltici; ora usa i nomi di Wikidata come il Python);
  - Italia «da verificare», prima → dopo, autori delle liste: +1.308 per cittadinanza non nota (di cui 252 scrittori, 15 con scheda: es. Rose Fyleman, F. W. Harvey, Dorothy Cottrell), +3 per paesi mancanti nella lista vecchia (Unione Sudafricana, Regno di Grecia, Uzbekistan), 0 senza motivo;
  - schede autore: cambiano solo le righe dell'Italia di quei 15 (+14 in inglese); tutte le altre date identiche;
  - Già pubblici: 15 opere di 12 autori alleati morti nel 1947 tornano libere in Italia (il vecchio confine era un anno troppo prudente: la proroga massima è finita nel 2025).
- **Controlli nuovi:** controllo_frasi.py confronta la tabella di tutte le 803 schede (4.015 righe) con regole.py (provato su Milne vecchio: lo trova); controllo_pagine.py apre radar e Già pubblici in un browser vero su un campione per caso (84 valori, 0 errori; la prima volta ha trovato un conflitto di nomi: il radar aveva già una costante REGOLE, il file nuovo si chiama REGOLE_PAESI). prova_regole.py e controllo_frasi.py diventano passi bloccanti negli aggiornamenti automatici (aggiorna.yml, gia-pubblici.yml).
- **Testi corretti insieme:** descrizioni «nell'UE» delle schede, calendario «in Europa», pagina dell'anno (descrizione per Google, esempio Winnie Puh → esempio senza paesi alleati, domande frequenti, numeri «in Italia N da verificare»), frasi di Già pubblici con l'Italia accanto a «da verificare».
- **Ancora aperto:** lo Storico usa ancora il vecchio significato di «alleato» (solo paesi alleati) finché non rifà le cittadinanze: al prossimo giro (o lanciandolo a mano) ricalcola gli autori morti negli ultimi 79 anni.

## 22/11/2026 notte — Prova 2 Open Library: interrotta per tempo (giro 44954885907)
- **Esito:** fermata dal limite di 130 minuti del workflow, senza risultati. Prima parte riuscita: 15.695 codici Open Library per 12.290 autori. Poi letti 12 milioni di righe su circa 41,7 (29%) del file delle opere, 377.936 righe tenute.
- **Perché:** il programma è lo stesso della prova 1, che aveva letto tutto il file in 19 minuti. Questa volta andava 20 volte più piano (circa 9,5 minuti per milione di righe): il collo di bottiglia è stato lo scaricamento dal server di Open Library, non i filtri.
- **Da fare:** rifarla scaricando prima il file per intero (con ripresa se si interrompe) e poi leggendolo dal disco, con un limite di tempo più alto; il conteggio dei titoli resta quello della prova 1 finché non si rifà.

## 22/11/2026 mattina — Cittadinanza di tutti gli autori (giro 44999207348, commit 812f2187)
- **Esito:** finito bene. Autori senza paese prima / trovati su Wikidata / davvero senza cittadinanza: 2027 678 / 367 / 311; 2028 633 / 323 / 310; Spagna 2027 785 / 487 / 298; Spagna 2028 924 / 621 / 303. Pagine rifatte.
- **Scrittori (quelli delle liste del sito):** senza cittadinanza su Wikidata 127 nel 2027 (10 con scheda) e 125 nel 2028 (5 con scheda): gli stessi di prima, perché per gli scrittori la cittadinanza era già stata chiesta. I trovati in più sono autori non scrittori.
- **Controlli in locale dopo il giro:** regole Python/browser 31.521 confronti, 0 differenze; 803 schede, 4.015 righe paese, 0 errori; frasi imprecise 0.
- **Da notare:** in Italia risultano «da verificare» 484 scrittori su 826 del 2027 e 510 su 849 del 2028 (paesi alleati più cittadinanza non nota). È la regola prudente del Trattato del 1947 applicata a tutti.

## 22/11/2026 — Trattato di pace 1947 e diritto d'autore: cosa dicono i giudici (ricerca, non cambia il sito)
- **Il Piccolo Principe** (Saint-Exupéry, francese, morto nel 1944): Tribunale di Milano n. 2826/2021 e Corte d'appello di Milano n. 2994/2022: caduto in pubblico dominio in Italia dal 1° gennaio 2015, cioè con i soli 70 anni. La proroga dell'allegato XV non è stata applicata: secondo il Tribunale riguarda le durate normali in vigore allo scoppio della guerra e non si somma alla proroga del 1945 (fonti: giurisprudenzadelleimprese.it; albertinilawfirm.eu, 7/10/2022).
- **Cassazione:** non si sommano la sospensione del Trattato e la proroga del D.Lgs.Lgt. 440/1945 (Sezioni Unite 29/12/2009 n. 49783; penale 38721/2007; civile 30036/2011 e 25574/2014, film). La legge 52/1996 (70 anni) richiama solo il decreto del 1945, non il Trattato (Cass. pen. 38721/2007).
- **Voce contraria:** le FAQ della Digital Library del Ministero della Cultura (2021) dicono che il Trattato allunga la durata di 7 anni e 8 mesi; il Centro studi SIAE (anni '90) riteneva corretta la proroga.
- **Giudizio:** le sentenze recenti, l'unica su un libro compresa, vanno nel senso di «70 anni e basta». Resta una voce ufficiale contraria (le FAQ del Ministero). Decisione da prendere con Marco su come mostrarlo.
- **Confronto con la ricerca di ChatGPT (22/11/2026, file di Marco):** stesse conclusioni (70 anni come criterio; Sezioni Unite 2009 contro il cumulo; Piccolo Principe libero dal 1/1/2015, Milano 2021 e 2022; FAQ del Ministero fonte informativa, non norma). In più: Cassazione civile 1993, 1994, 2004 a favore del cumulo (vecchio orientamento, superato nel 2009); la proroga di 6 anni del 1945 è abrogata dalla legge 52/1996 (verificato sul testo WIPO: «L'extension des délais de protection prévue par le décret législatif du Lieutenant n. 440 du 20 juillet 1945 est abrogée»); resta aperto solo un possibile effetto residuo del Trattato per opere i cui diritti esistevano già allo scoppio della guerra (prima del 10/6/1940). Non ancora verificata da me: Cass. civ. 33598/2021.

## 22/11/2026 — Decisione di Marco: in Italia la data dei 70 anni anche per i paesi alleati, con una nota
- **Regola (scripts/regole.py):** tolto «da verificare»; nuova nota_trattato: autore di un paese alleato, opera uscita entro il 1940 (diritti in vigore allo scoppio della guerra, 10/6/1940), finché la proroga massima prudente (8 anni) potrebbe essere in corso. La cittadinanza non nota non fa più differenza. Testo della nota: chi sostiene la proroga, e che i tribunali non l'hanno applicata (Piccolo Principe, Milano 2021 e 2022).
- **Dove cambia:** schede (riga Italia con la data e «paese alleato: vedi la nota»), radar (conto alla rovescia anche in Italia, nota sotto), home e pagina dell'anno (di nuovo «liberi in Italia, Francia, Germania e Regno Unito»), calendario, Già pubblici (le opere degli autori alleati tornano negli scaffali italiani, con la nota nella scheda dell'opera). Storico: il segno «alleato» torna a voler dire solo cittadinanza alleata (cache v3; il giro in corso lo calcola ancora alla v2).
- **Controlli dopo la modifica:** regole Python/browser 31.521 confronti, 0 differenze; 803 schede, 4.015 righe, 0 errori; frasi imprecise 0; pagine vere 84 valori, 0 errori; 15 pagine senza errori JavaScript; nessuna scheda con «da verificare» per l'Italia.

## 22/11/2026 — Altre copie delle regole trovate e tolte (locale, non pubblicato)
- Rispondendo a Marco su come nasce il radar del 2029 ho trovato che scripts/aggiorna.py (quello che scarica gli autori di ogni anno) usava ancora +71/+81 scritti a mano. Cercando con un controllo automatico nuovo (prova_regole.py, parte 2: numeri delle regole scritti fuori da regole.py) ne sono uscite altre in da_decidere.py, registro_autori.py, verifica_anni_usa.py, storico/duke.py, storico/verifica_anni.py. Tutte passate a scripts/regole.py; stessi valori di prima (provato: 1955, 1930, 1956/1957/1958, 1946/1947/1948).
- Limite del controllo: trova i numeri scritti nei calcoli (es. «anno - 96»), non quelli dentro tabelle come la vecchia PAESI di aggiorna.py.
- Trovato anche un buco nel cambio d'anno: il radar mostra il primo anno dell'elenco data/indice.json, che contiene tutti gli anni con un file; il 1° gennaio 2027 il file 2027.json resta e il radar continuerebbe a mostrare il 2027. Da progettare con Marco.

## 22/11/2026 — Audit delle regole per opera (solo lettura, niente cambiato)
- **Dove stanno oggi:** `storico/pagina.html` (funzioni stato e liberaUe, nel browser), `storico/per_autore.py` (libera_ue, libera_usa, ue_da_verificare: quali opere entrano in Già pubblici), `scripts/pagine.py` (stato_usa: le opere USA nelle schede), `scripts/regole.py` (opera_antica, autori_che_contano, decidi_morte).
- **Regole per opera trovate:** opere molto vecchie (uscite più di 170 anni fa), opere anonime (70 anni dall'uscita), coautori senza data, fonti in disaccordo sul confine dei 70 anni, Regno Unito (inediti e opere postume, 2039), USA (95 anni dall'uscita con seconda fonte per l'anno; senza anno), «morti per la Francia» (100 anni), nota sul Trattato, controllo degli anni assurdi (edizioni moderne).
- **Incoerenze trovate:**
  1. opere anonime: il browser usa 80 anni per la Spagna, il Python (opera_antica) 70 per tutti;
  2. USA: il browser vuole la conferma dell'anno da una seconda fonte («da verificare» senza), il Python di Già pubblici (libera_usa) no; le schede (stato_usa) sì, ma cercando l'opera per titolo;
  3. opere molto vecchie: il browser usa 180 anni per la Spagna, il Python 170 per tutti;
  4. il controllo automatico delle copie non vede soglie come «Y - 171» o «+ 150».

## 22/11/2026 — Primi casi di riferimento (docs/casi-di-riferimento.md, da approvare)
- **Come:** 8 casi reali con fonte (sentenze di Milano 2021-2022, BNE 2017, Duke 2021, IfZ/bpb 2016, GOV.UK e UCL per la regola del 2039, news.belgium.be 2015, fonti francesi su Saint-Exupéry). Stato calcolato dalla pagina Già pubblici vera (funzione stato, aperta in un browser) per ogni caso.
- **Risultati:** 6 su 7 confrontabili tornano. Mein Kampf: «non determinato» perché l'opera è collegata alla voce sbagliata di Wikidata (Q346521 «Hitler», senza data di morte, invece di Q352). Saint-Exupéry in Francia: il sito dice «da verificare» (giusto), ma la regola «morti per la Francia» (+30) darebbe il 2045 contro il 2032 della maggior parte delle fonti. Kitty-in-Boots non è nei dati.
- **Da fare:** trovare casi reali per opere anonime, coautori e il confine spagnolo del 1987; aggiunto in storico/pagina.html window.statoOpera (solo per le prove).

## 22/11/2026 — Passo 2: regole per opera in scripts/regole.py (in locale, non pubblicato)
- **Spostamento senza cambiare nulla.** Le funzioni stato() e liberaUe() di storico/pagina.html, più i controlli sugli anni impossibili (-90, +150), sono diventate stato_opera, libera_ue_opera e anno_opera_credibile in scripts/regole.py, con la copia per il browser in assets/regole.js. Prima di toccare la pagina ho salvato lo stato di tutte le 56.516 opere in 6 paesi; dopo la modifica: 0 differenze su 339.096 risultati. Python e browser: 0 differenze su 452.128 confronti (prova_regole parte 3, a ogni giro).
- **Casi di riferimento automatici** (prova_regole parte 4, data/casi_riferimento.json): 10 reali e 13 di confine. Tornano 21. Mein Kampf è un errore noto nei dati e non blocca. **Errore trovato dal caso di confine:** per gli autori morti tra il 1960 e il 1968 con opere inedite uscite dal 1989 in poi, il Regno Unito dice «dal 2039» invece di «dal 2040», perché la regola dei 70 anni viene prima di quella del 2039. Non corretto: è un cambio di risultato giuridico e va fatto a parte.
- **Rilevatore delle copie esteso alle soglie** (Y-171, +150, 2039...), ignorando i testi tra virgolette. Ha trovato una copia in storico/verifica_anni.py (Y - 171), corretta con regole.opera_vecchia, stesso risultato su tutti gli anni dal -500 al 2100. Anche storico/per_autore.py (ANNO_UE - 100) usa ora opera_vecchia, con lo stesso risultato.
- **Correzione 1 (cambia risultati): schede autore, colonna USA.** stato_usa in scripts/pagine.py usa ora stato_opera, la stessa regola di Già pubblici. Cambiano 500 opere principali su 2.192:
  - 474 passano da «da verificare» a «libero», perché l'autore è libero anche in Europa e la regola di Già pubblici in quel caso non chiede una seconda fonte;
  - 17 hanno un anno diverso tra scheda e Storico;
  - 9 erano «libero» per un errore: un titolo vuoto si collegava all'opera sbagliata dello stesso autore (Pío Baroja ×3, Benn ×2...). Ora sono «da verificare».
- **Già pubblici e Python per lo Storico (per_autore.py):** le tre differenze (anonime in Spagna, 180 anni in Spagna, seconda fonte USA) non cambiano niente di ciò che si vede. Il Python decide solo quali opere entrano nello Storico, con un filtro più largo della pagina, e poi decide la pagina. Gli scaffali «solo USA» e «solo UE» calcolati dal Python non sono usati dalla pagina.
- **Dato sbagliato trovato:** nei file di ricerca le date di morte avanti Cristo perdono il segno meno (Platone 348 invece di -348). Lo stato non cambia, perché sono comunque antichi, ma nella ricerca si legge «morto nel 348».
- **Aperto:** la regola «niente seconda fonte se l'autore è libero in Europa» vale oggi per 35.684 opere «libere negli USA» in Già pubblici. Da decidere con Marco.

## 22/11/2026 — Regola USA (b): impatto prima della decisione (niente pubblicato)
- **Domanda di Marco:** non dichiarare un'opera libera negli USA solo perché l'autore è libero in Europa. Quando serve davvero la seconda fonte?
- **Base giuridica (17 U.S.C. § 303; tabella Cornell «Copyright Term and the Public Domain»):** è libero ciò che è uscito entro il 1930. Gli inediti seguono la regola della vita dell'autore più 70 anni. Un'opera creata prima del 1978 e pubblicata per la prima volta tra il 1978 e il 2002 è protetta almeno fino al 31/12/2047. Quindi il rischio vero è una prima pubblicazione dal 1931 al 2002, cioè le opere postume o tardive, non l'anno esatto in sé.
- **Prova:** ho diviso le 35.684 opere «libere USA» senza seconda fonte usando la data di pubblicazione (P577) e quella di composizione (P571) dei blocchi dello Storico. Script in /home/claude/prove/impatto_b*.py, non nel repo.
  - Bastano i dati (18.827 + 4.816):
    - 149 testi antichi dell'elenco a mano;
    - 8.234 pubblicate più di 170 anni fa;
    - 10.444 pubblicate in vita da autori morti entro il 1930;
    - 4.816 composte da autori morti più di 170 anni fa.
  - Serve la seconda fonte:
    - 4.234 in cui l'anno decide perché l'autore è morto dopo il 1930 (Gatsby, Ulisse);
    - 1.290 postume (Il processo);
    - 6.518 con la sola data di composizione e autori più recenti.
  - **Risultato con la (b) così precisata:** in Già pubblici 23.671 opere restano libere negli USA e 12.013 diventano «da verificare». Nelle schede degli autori, rispetto al sito di oggi, cambiano 28 opere principali.
- **Errore trovato e corretto a parte:** le liste della Duke non contavano come seconda fonte. Corretto in scripts/registro.py: 32 conferme in più, tra cui Gatsby, e 0 risultati visibili cambiati oggi.
- **Altri errori corretti a parte, in locale, ognuno nel suo commit:**
  - regola britannica del 2039, che diceva 2040 invece di 2039: 0 opere del sito cambiano;
  - date di morte avanti Cristo nello Storico: vale dal prossimo giro.
- **Mein Kampf:** non corretto. L'autore Q346521 è nelle esclusioni dello Storico, e da qui non posso aprire Wikidata per controllare il collegamento giusto.

## 22/11/2026 — Regola USA selettiva ANNULLATA (decisione di Marco)
- **Perché:** con quella regola l'Iliade, la Bibbia, l'Odissea e Romeo e Giulietta sarebbero risultate «da verificare» negli USA. Il mio errore è stato non mostrare prima quali titoli conosciuti avrebbe toccato. La decisione di Marco: le opere antiche sono di pubblico dominio e non si toccano più.
- **Fatto:** annullato il commit 3e2042e92 con un revert. Già pubblici è di nuovo identico al sito di oggi: 0 differenze su 56.516 opere. L'Iliade, l'Odissea, la Bibbia, Romeo e Giulietta e la Divina Commedia risultano libere negli USA e in Italia.
- **Regola di lavoro da ora in poi:** prima di proporre qualsiasi cambio di regola, mostrare i titoli più letti che cambierebbero.

## 22/11/2026 — Passo 2 pubblicato (push 394266e7, approvato da Marco)
- **Pubblicato:** regole in un posto solo, regola britannica del 2039, date a.C., Duke come seconda fonte, e 3 schede rigenerate. Il cambio USA delle schede (le 474 opere) è rimasto fuori.
- **Giro «Pagina Già pubblici» 45009014354:** tutti i passi «success», controlli bloccanti compresi. Dopo il giro le 3 schede mostrano «libero dal 2024/2023/2022», come atteso.
- **Storico 44999863016:** fermato da Marco (cancelled). Il controllo programmato su quel giro non serve più.

## 22/11/2026 — Passo 3: fotografia dello stato giuridico (in locale, non pubblicato)
- **Cosa fa:** scripts/fotografia.py salva, per ognuna delle 56.516 opere di Già pubblici e dei 5.400 autori delle liste e per ogni paese, tre cose:
  - lo stato;
  - il perché, cioè la regola usata, che ora stato_opera restituisce in Python e nel browser (campo «r», per esempio «morte», «uk_2039», «usa_seconda_fonte_mancante»);
  - i dati usati: anno di uscita, anni di morte, conferma USA, «morto per la Francia», paesi.
  - In cima ci sono l'anno e l'impronta delle regole (assets/regole.js). Il file compresso pesa circa 1,7 MB e si crea in 2-3 secondi.
- **Confronto** (scripts/confronta_fotografia.py): ogni cambio è classificato come atteso (è cambiato solo l'anno), dati, regola o non spiegato. Se c'è un cambio non atteso esce con errore, e quindi il giro non pubblica.
- **Prove:**
  - **Due fotografie di fila sono identiche, byte per byte.**
  - **Simulazione del 1° gennaio 2027** (fotografia con l'anno 2027 contro quella del 2026):
    - 9.152 cambi, tutti «atteso», codice 0;
    - 6.991 riguardano autori, per esempio 1.423 morti nel 1956 che diventano liberi in Italia, Francia, Germania e Regno Unito;
    - 1.187 riguardano opere;
    - 974 cambiano solo il motivo, non lo stato.
  - **Regola cambiata apposta** (Spagna 80 anni fino al 1986 invece che al 1987): 8 cambi, tutti «regola», codice 1. Il giro si sarebbe fermato. Esempio: The Little Friend in Spagna, da «dal 2068» a «dal 2058».
  - prova_regole: 0 errori; Python e browser uguali, anche nel motivo.
- **Da fare al passo 4:** mettere la fotografia nei giri: si salva dopo ogni giro riuscito e si confronta prima di pubblicare.

## 22/11/2026 — Mein Kampf corretto (in locale)
- **Errore:** nei dati di Wikidata, Mein Kampf (Q48244) è collegato a Q346521 «Hitler», che non ha data di morte. Per questo risultava «non determinato» in tutti i paesi europei.
- **Correzione a mano, con fonte:** in data/coautori_manuali.json l'autore diventa Adolf Hitler (Q352, morto nel 1945). La fonte è l'Institut für Zeitgeschichte (ifz-muenchen.de/?id=550): i diritti sono scaduti il 31/12/2015, 70 anni dopo la morte. Per farlo ho aggiunto il campo «sostituisce» in storico/registro_opere.py, che toglie dall'opera l'autore sbagliato.
- **Verifica:**
  - **Fotografia prima e dopo:** 5 cambi, tutti per Mein Kampf, tutti classificati «dati» (corretto). In Italia, Francia, Germania, Regno Unito e Spagna passa da «non determinato» a «libero»; negli USA era già libero.
  - **Pagina vera nel browser:** autore Adolf Hitler, 1945; libero in Italia, Germania e USA.
  - **Casi di riferimento:** 24 su 24, il caso 6 ora blocca.
- L'opera resta fuori da classifiche e scaffali (data/storico_esclusioni.json); si trova solo con la ricerca.

## 22/11/2026 — Giri automatici: tre protezioni corrette (dall'audit esterno; in locale)
- **Giro trimestrale (aggiorna.yml):** «Salva» partiva anche con il controllo delle regole fallito, bastava che il giro non fosse annullato. Ora il controllo gira sempre e «Salva» parte solo se il controllo è riuscito.
- **Già pubblici (gia-pubblici.yml):** partiva anche dopo uno Storico fallito o annullato. Ora, quando parte dopo lo Storico, parte solo se lo Storico è finito bene. Il pulsante e i cambi di file restano come prima.
- **Già pubblici e stima:** se l'invio su GitHub falliva 5 volte, il giro restava verde. Ora finisce rosso, con il messaggio «niente pubblicato». La logica è provata in locale con un invio finto che fallisce (codice 1) e con uno che riesce (codice 0).
- **Non toccato:** i giri che scrivono nello stesso momento (punto 4 dell'audit), da risolvere nel passo 4 mettendo in fila tutti i giri che scrivono.

## 22/11/2026 — Passo 4, prima parte: salvataggio unico e fotografia nei giri (in locale)
- **scripts/salva.sh, usato da tutti i 15 giri che salvano** (il logo escluso): niente più «-X theirs». Se un altro giro ha cambiato gli stessi file, il giro finisce rosso e non pubblica; se l'invio fallisce 5 volte, finisce rosso. Provato su un deposito finto:
  - salvataggio normale: pubblicato, codice 0;
  - stesso file cambiato da due giri: «CONFLITTO», niente pubblicato, codice 1;
  - file diversi: pubblicato, codice 0;
  - niente da salvare: codice 0.
- **Fotografia nei giri che rifanno le pagine** (aggiorna, Già pubblici, anniversari, stima): confronto con data/fotografia.json.gz, che è la prima fotografia ed è salvata adesso. Provato:
  - nessun cambio: passa;
  - regola cambiata apposta: 8 cambi, codice 1, elenco con impronta in docs/cambi-da-approvare.md;
  - impronta scritta in data/cambi-approvati.txt: passa, e la fotografia si aggiorna.
- **Anniversari e stima** salvavano anche un giro annullato («always()»): ora salvano solo se il giro non è annullato.
- **Non ancora fatto:** cambiare le date dei giri secondo docs/giri-automatici.md (seconda parte del passo 4).
- Date cambiate (22/11/2026, ok di Marco): registro il 1° aprile, luglio, ottobre e novembre; anniversari il 1° ottobre e novembre.
- Fotografia: se spariscono in massa opere o autori (più di 50 e più dell'1%), anche le uscite vanno approvate. Provato: 2000 opere tolte apposta, il giro si ferma (codice 1). In locale, da pubblicare.

## 22/11/2026 — Passo 5: mockup della settimana del Public Domain Day, APPROVATO da Marco
- **Primo mockup** disegnato da zero: bocciato («spaziature, forma, tutto fatto a caso»). Conteneva anche un numero sbagliato, 1.423 autori invece degli 826 scrittori indicati dal sito.
- **Secondo mockup**, approvato («Perfetto mi piace»): costruito dalla home vera, con lo stesso codice, gli stessi spazi e i caratteri incorporati. Cambiano solo i testi e una sezione. Script fuori dal repository: /home/claude/prove/costruisci_mockup.py.
  - **31/12:** in alto «Domani»; nel testo un orologio fino a mezzanotte; bottone «Chi si libera a mezzanotte».
  - **1/1:** in alto, in rosso, «Public Domain Day»; le righe del frontespizio dicono «da oggi»; testo: «Da oggi, 1° gennaio 2027, sono liberi 826 scrittori in IT, FR, DE e UK, 790 in Spagna e 169 libri negli Stati Uniti»; numeri sotto il titolo «Da oggi, 1° gennaio 2027»; sezione nuova «Da oggi sono liberi», con 4 riquadri porta (paesi e Spagna dal 2037).
  - **2-6/1:** come il 1°, con «dal 1° gennaio».
  - **7/1:** la home dell'anno dopo (2028), più un riquadro d'archivio «Pubblico dominio 2027» a tutta larghezza.
- **Regola di lavoro imparata:** i mockup si costruiscono sulla pagina vera del sito, non disegnati da zero.

## 22/11/2026 — Pagina del Public Domain Day e comportamento del sito nella settimana (in locale, simulato)
- **Pagina dell'anno (pubblico-dominio-2027):** i testi cambiano tempo da soli nel browser, con fase_sito, e il codice è di scripts/pagine.py.
  - **Prima del 1° gennaio:** come oggi, «Cosa diventa libero nel 2027».
  - **1° gennaio:** «Public Domain Day · oggi», «Cosa è libero da oggi», «Oggi, 1° gennaio 2027, scadono…»; in alto, in rosso, «Public Domain Day».
  - **Dal 2 gennaio:** «Cosa è diventato libero nel 2027», «sono scaduti»; «I nomi più attesi» diventa «I nomi più letti»; nel paragrafo USA «sono diventati liberi».
  - **Dal 7 gennaio, archivio:** in alto «Liberi dal 1° gennaio 2027».
- **Già pubblici:** prima calcolava gli stati con l'anno dei dati (l'ultimo Storico), non con l'anno di oggi, quindi il 1° gennaio non cambiava niente fino allo Storico del 2 gennaio. Ora usa l'anno di oggi.
  - Gli autori appena liberati restano nell'elenco «in arrivo» per tutta la festa, con la scheda «Libero da poco» invece di «Non è ancora libero».
  - Corretto anche il testo di quella scheda, che diceva «in Italia anche salvo le eccezioni dei paesi alleati»: era rimasto da prima della decisione sul Trattato.
- **Simulazione:** il 20/12, il 1/1, il 4/1 e il 10/1 i testi tornano tutti; per Papini il 2/1 compare «Libero da poco».
- **Contraddizione trovata, non corretta:** *L'opera da tre soldi* è nella vetrina della home come «libera dal 1° gennaio 2027» in Italia, Francia, Germania e Regno Unito. Su Wikidata però ha come coautrice Elisabeth Hauptmann (morta nel 1973), quindi per Già pubblici, con la regola dei coautori, è libera dal 2044. La vetrina della home guarda solo l'autore, non l'opera. Da decidere con Marco.

## 22/11/2026 — Prova «anni mancanti»: risultati (giro 45042176593)
- **Cosa ha fatto:** opere delle schede senza anno su Wikidata: 375. Il tempo (50 minuti) è bastato per controllarne 270, cercandole in Library of Congress, Open Library, Wikipedia en/it, BnF e K10plus.
- **Risultati:**
  - con almeno un anno trovato: 137 su 270 (51%);
  - due o più fonti d'accordo: 73;
  - una fonte sola: 42;
  - fonti in disaccordo: 22;
  - nessuna fonte: 133.
- **Quante volte ogni fonte ha trovato un anno:** Open Library 104, LoC 94, Wikipedia en 23, BnF 17, K10plus 12, Wikipedia it 5.
- **Controllo a mano:**
  - Mencken, *In Defense of Women*: 1918, giusto, con Open Library e Wikipedia d'accordo.
  - *Toad of Toad Hall* 1929 e *Il tradimento dei chierici* 1928: giusti.
- **Problema 1:** anche quando le fonti sono d'accordo possono dare la data di una traduzione o di una ristampa, non della prima uscita.
  - Walser, *A Schoolboy's Diary*: 2013, cioè la traduzione inglese.
  - Gail, *The Shot into Infinity*: 1975, cioè la traduzione.
  - In 22 casi l'anno più vecchio trovato è dopo la morte dell'autore. Alcuni sono veri postumi (Alvaro, Gadenne), altri sono edizioni tarde.
- **Problema 2:** il gruppo di controllo (opere con l'anno su Wikidata, per misurare quanto sbaglia Wikidata) non è partito. Il tempo è finito sul primo gruppo. È un errore di come ho costruito la prova: i due gruppi andavano alternati.
- **Giudizio:** le fonti autorevoli completano circa metà delle opere senza anno, ma prendere «l'anno più vecchio» in automatico non basta.
- **Regole proposte prima di usarle sul sito:**
  - contare solo le edizioni con il titolo originale;
  - non basta Open Library da sola;
  - se l'anno è dopo la morte, l'opera va verificata.

## 22/11/2026 — Vetrina della home con la regola dei coautori
- **Problema:** la vetrina guardava solo l'anno di morte dell'autore. *L'opera da tre soldi* risultava libera dal 2027, ma ha come coautrice Elisabeth Hauptmann (morta nel 1973). Per la Kurt Weill Foundation, che ne detiene i diritti, l'opera è protetta fino al 2043.
- **Correzione:**
  - la vetrina usa la stessa regola delle schede: pagine.opera_libera_ue, ricavata da note_coautori, che ora la usa anch'essa;
  - le schede autore rigenerate sono identiche a prima.
- **Opere di Brecht in vetrina:**
  - *Madre Coraggio e i suoi figli* e *La resistibile ascesa di Arturo Ui*.
  - Non *Il cerchio di gesso del Caucaso*: l'edizione Suhrkamp porta «unter Mitarbeit von Ruth Berlau», morta nel 1974. Wikidata non la segna; inserirla fra i coautori manuali è da decidere con Marco.
- **Winnie Puh:** in vetrina compare la nota «Solo il testo: i disegni originali di E. H. Shepard restano protetti fino al 2046». La fonte è lo UK IPO: Shepard è morto nel 1976, quindi i disegni sono liberi dal 1° gennaio 2047. La nota sta fuori dal flusso della pagina, così il resto non si sposta.
- **Nuova prova automatica** (prova_regole parte 5): ogni opera della vetrina europea deve risultare libera anche per le regole per opera di Già pubblici.
  - Con la vecchia home dà 2 errori, *L'opera da tre soldi* in italiano e in inglese.
  - Con la nuova home dà 0 errori.
  - 4 pagine non sono controllabili: le due opere di Brecht non sono nei dati di Già pubblici, perché sono uscite dopo il 1930.
- **Pagine dell'anno 2027 e 2028 rigenerate:** ora contengono il codice della settimana del Public Domain Day.

## 22/11/2026 — Prova «anni mancanti», secondo giro (preparata)
- I due gruppi vanno a turno: 100 opere senza anno, scegliendo prima le 105 non ancora cercate, e 100 di controllo con l'anno su Wikidata.
- Il riepilogo conta anche gli anni trovati che cadono dopo la morte dell'autore.
- I risultati del primo giro restano in risultati-giro1.json e riepilogo-giro1.md.
- **Il cerchio di gesso del Caucaso:** aggiunta Ruth Berlau (morta nel 1974) ai coautori che Wikidata non segna. Le fonti sono l'edizione Suhrkamp («Unter Mitarbeit von Ruth Berlau») e la Brecht Guide dell'Università del Wisconsin («Collaborator: Ruth Berlau»). La scheda di Brecht ora la dà libera dal 1° gennaio 2045.
- **Nota di data/coautori_manuali.json corretta:** i coautori li decidono le fonti terze, non Marco e non Claude.

## 22/11/2026 — Prova «opere dalle fonti» (preparata, non ancora lanciata)
- **Perché:** opere, coautori e illustratori vengono ancora solo da Wikidata. Le altre fonti oggi confermano soltanto quello che Wikidata dice già.
- **Cosa fa:** per ogni opera interroga i cataloghi Library of Congress, K10plus (catalogo collettivo tedesco) e BnF (solo per gli autori francesi) e legge:
  - la dicitura del frontespizio, campo 245 $c («unter Mitarbeit von», «illustrated by»…);
  - le persone con le loro date e il loro ruolo, campi 700;
  - l'anno di ogni edizione.
- **Cosa non conta:** traduttori, curatori e prefatori.
- **Campione:** i 60 autori più letti della lista 2027, 4 opere ciascuno, più Brecht e Milne.
- **Cosa misura:**
  - le persone che Wikidata non segna, nelle edizioni uscite quando l'autore era vivo, e quante sono morte dopo l'autore (quelle cambiano la data);
  - quante volte l'anno della prima edizione coincide con Wikidata;
  - se ritrova i casi noti: Hauptmann, Berlau, Shepard.
- **Prova a secco, in locale con un record finto:** legge Berlau sia dal campo 700 sia dalla dicitura «Mitarbeiter: R. Berlau», e Shepard da «with decorations by E. H. Shepard». Il traduttore viene scartato.
- **Limite:** da qui non posso raggiungere i cataloghi, quindi la prova vera gira solo su GitHub.

## 22/11/2026 — Controllo degli stati scritti sulle schede (scripts/controllo_stati.py, prova_regole parte 6)
- **Come funziona:** legge le 803 schede autore già generate (italiano e inglese) e rifà ogni conto da capo con regole.py e i registri (autori, opere, USA), senza usare il codice di pagine.py. Controlla quattro cose:
  - la tabella paese per paese;
  - l'intestazione;
  - le note dei coautori e della musica;
  - lo stato USA e i coautori delle opere che sono anche in Già pubblici.
- **Numeri:** 4.015 date per paese, 1.284 intestazioni, 202 note, 906 stati USA, 22 opere con un coautore morto dopo. Le opere che non sono in Già pubblici sono 2.273 e non si possono controllare.
- **Differenze nelle schede italiane** (le inglesi sono uguali):
  - **149 opere, colonna USA:** la scheda dice «da verificare» e Già pubblici «libera». Le due pagine usano due regole diverse sulla seconda fonte. È la decisione aperta sulle 474 opere.
  - **20 opere, colonna USA:** la scheda usa l'anno grezzo di Wikidata, spesso quello di un'edizione moderna, mentre Già pubblici usa l'anno del registro. Esempi:
    - *Millions of Cats* (1928): la scheda dice «dal 2052», ma è libera;
    - *Weeds* (1923): la scheda dice «dal 2116»;
    - *Cirkus Humberto*: la scheda dice 2113, Già pubblici 2037.
  - **Henham:** la scheda usa l'anno di morte 1946 della lista, mentre il registro, con fonti discordi, ha deciso 1948.
  - ***The Skylark of Space* (Garby):** la regola per opera la dà libera dal 2036 per il coautore E. E. Smith, ma la scheda non lo dice.
  - ***Reigin pappi*:** la scheda dice «libero», Già pubblici «da verificare», perché usano due registri di verifica diversi.
- **Causa comune:** le schede (pagine.py) usano dati loro, cioè gli anni grezzi di Wikidata, una propria verifica USA e coautori.json, invece dei registri e di stato_opera.
- **Per ora la parte 6 non blocca i giri.** Diventa bloccante quando le schede useranno stato_opera.

## 22/11/2026 — Le schede usano gli stessi dati di Già pubblici (in locale, branch schede-registri, non pubblicato)
- **Cosa cambia in scripts/pagine.py:**
  - **anno di morte:** quello deciso nel registro unico (regole.morte_dal_registro). Chi per il registro è morto in un altro anno non compare più tra gli «altri scrittori» di quella lista.
  - **opere principali che sono anche in Già pubblici:** stessa riga, stesso anno, stessi coautori e stesso stato USA (regole.stato_opera, verifiche di data/registro/opere.json).
  - **opere che non sono in Già pubblici:** l'anno di Wikidata vale solo se è credibile (regole.anno_opera_credibile).
  - **decisione ancora aperta (le 474 opere):** nelle schede un'opera libera in Europa resta «da verificare» negli USA senza la seconda fonte.
  - **stesso titolo due volte:** la nota del coautore ha lo stesso numero su tutte e due le righe.
- **Controllo degli stati (parte 6):** 0 differenze (prima 351). Conta a parte 313 righe con la decisione USA aperta, cioè le stesse opere nelle schede in italiano e in inglese. Ora la parte 6 blocca i giri.
- **Cosa cambia sul sito:** 32 opere principali nelle schede italiane (le stesse nelle inglesi) e la scheda di Henham.
  - **Da protette a libere negli USA, con l'anno giusto:**
    - *Millions of Cats*: da «dal 2102» a «libero dal 2024», anno 1928;
    - *Weeds*: da «dal 2116» a «libero dal 2019»;
    - *Caliban by the Yellow Sands*.
  - **Da «anno non noto» a «libero»:** *Tarr*, *Trent's Last Case*, *The Green Hat*.
  - **Anni corretti:**
    - *The American Language*: 1919, non 1923;
    - *The Richest Man in Babylon*: 1926;
    - *Cirkus Humberto*: 1941, quindi dal 2037 e non dal 2113.
  - **Più prudenti:**
    - *Reigin pappi*: da «libero» a «da verificare», perché le fonti trovano solo edizioni dal 1962;
    - *Héro et Léandre*: da «libero» a «anno non noto», perché l'anno 1854 è precedente alla nascita dell'autore;
    - 11 opere passano a «da verificare», perché ora c'è l'anno ma non ancora la seconda fonte.
  - **Henham:** anno di morte 1948 secondo il registro (Library of Congress e Wikidata; GND e SNAC dicono 1946); tutte le date si spostano di due anni.
- **Ancora da fare:** le liste per anno (data/AAAA.json) non usano ancora il registro, quindi 11 autori con fonti discordi stanno nella lista di un anno diverso da quello deciso. Lo stesso problema riguarda radar e pagine dell'anno: è la prossima correzione.

## 22/11/2026 — Prova «anni mancanti», secondo giro: risultati (100 senza anno, 100 di controllo)
- **Opere senza anno:**
  - con almeno un anno trovato: 56 su 100;
  - due o più fonti d'accordo: 21;
  - una fonte sola: 24;
  - fonti in disaccordo: 11;
  - anno trovato dopo la morte dell'autore: 4.
  - Fonti che rispondono: LoC 47, Open Library 27, K10plus 11, Wikipedia 5, BnF 1.
- **Gruppo di controllo (opere con l'anno su Wikidata):** almeno una fonte per 58; l'anno più vecchio delle fonti coincide con Wikidata in 40 casi (69%) e differisce in 18.
- **Controllo a mano di 5 casi in disaccordo:**
  - *Weeds* (Kelley): Wikidata dice 2020, LoC 1923. Ha ragione LoC: il frontespizio dice «Copyright, 1923, by Harcourt, Brace» (archive.org).
  - *El árbol de la ciencia* (Baroja): Wikidata dice 1911, le fonti 1928, che è la traduzione inglese. Ha ragione Wikidata (1911, Wikipedia e Revista de Literatura CSIC).
  - *Les civilisés* (Farrère): Wikidata dice 1905, le fonti 1906 e 1900. Ha ragione Wikidata (Wikisource, Ollendorff 1905; Goncourt 1905).
  - *Once on a Time* (Milne): Wikidata dice 1917, le fonti 1922, che è l'edizione americana. Ha ragione Wikidata (Project Gutenberg, 1917).
  - *Zaynab* (Haykal): Wikidata dice 1913, le fonti 1963. Ha ragione Wikidata (Wikipedia; Cambridge University Press).
- **Giudizio:** cercare «l'edizione più vecchia con lo stesso titolo» nei cataloghi sbaglia spesso, perché trova traduzioni e edizioni più tarde, soprattutto quando cerca col titolo inglese. Wikidata sbaglia soprattutto quando dà l'anno di un'edizione moderna (Weeds 2020), e quel caso ora lo ferma anno_opera_credibile.
- **Proposta di regole per l'anno:**
  - si contano solo le edizioni nella lingua originale (campo 008/35-37 di MARC) o col titolo originale;
  - deve dirlo il catalogo nazionale del paese dell'autore, oppure due fonti d'accordo;
  - la data di copyright (260/264 $c «c1923») vale più dell'anno di stampa;
  - Open Library da sola non basta;
  - un anno dopo la morte dell'autore va verificato.

## 22/11/2026 — Prova «opere dalle fonti»: risultati (191 opere, 18 minuti, nessun errore di rete)
- **Trovate in almeno un catalogo:** 125. K10plus 105, LoC 100, BnF 1.
- **Persone che Wikidata non segna, in edizioni uscite quando l'autore era vivo:** 30. Di queste 7 sono morte dopo l'autore, quindi cambiano la data:
  - Shepard per 4 libri di Milne;
  - l'illustratrice Maginel Wright Barney per *Downright Dencey*;
  - l'illustratore Frank Schoonover per *The Man from Bar-20*;
  - il coautore H. Warner Allen per *Trent's Own Case* di Bentley.
- **Casi noti:**
  - Hauptmann trovata (K10plus);
  - Shepard trovato (K10plus e LoC);
  - Berlau non trovata: nei cataloghi c'erano solo traduzioni inglesi.
- **Anni:** coincidono con Wikidata 68 volte su 94. Le differenze sono quasi tutte traduzioni o edizioni più tarde, come nella prova sugli anni.
- **Giudizio:** i collaboratori e gli illustratori che contano escono davvero. Le edizioni in traduzione vanno però tolte dal voto, come per gli anni.

## 22/11/2026 — Attività «verifica delle opere» impostata (docs/verifica-opere.md)
- **Decisione di Marco:** si fa una volta per lista, non a pagamento. Claude prepara il rapporto e Marco controlla. Si parte dalle liste 2027 e 2028; la lista 2029 si fa a gennaio.
- **Raccolta completa:** scripts/prova_opere_fonti.py con LISTE, giro fonti-opere.yml. Le opere sono 2.126 (2027, 2028, es-2027, es-2028), circa 3,5 ore. Salva per ogni edizione lingua, data di copyright e lingua di traduzione. Se non finisce, riprende da dove si era fermato.
- **Prova a secco in locale, con una rete finta:** la ripresa funziona (119 opere fatte su 1.026, nessuna ripetuta).

## 22/11/2026 — Registro unico collegato alle liste per anno e al calendario (in locale)
- **Errore di Claude:** il registro unico (20/11) diceva «da qui leggono tutte le parti del sito», ma liste per anno, radar, pagine dell'anno e calendario leggevano ancora Wikidata, e le schede fino a stasera. Nessuna prova lo controllava.
- **Correzione:**
  - scripts/applica_registro_liste.py mette nelle liste l'anno di morte deciso nel registro. Se un autore appartiene a un altro anno lo sposta, se quella lista non esiste lo toglie, e scrive ogni spostamento in data/registro/liste_spostati.json. Rifatto due volte dà lo stesso risultato.
  - Gira nel giro aggiorna, dopo Wikidata, e nel giro registro. Il giro registro ora rifà anche le pagine, con i controlli bloccanti e la fotografia; se i controlli falliscono salva solo il registro.
- **Nuova prova bloccante (prova_regole parte 7):** ogni autore delle liste e del calendario deve avere l'anno del registro e stare nella lista del suo anno. Prima della correzione dava 11 differenze, dopo 0. Il calendario 2027 era già a posto.
- **Spostamenti:**
  - Jafar Kashif e Julián Cruz Balmaceda: morti nel 1947, non nel 1946, quindi liberi in Spagna dal 2028;
  - Nikos Karvounis: morto nel 1957, quindi entra nella lista europea 2028;
  - 8 autori escono dalle liste: Stott (1980), Henham (1948), Donaghy (1949), Horstmann (1954), Scheffler (1951), Vengerov (1962), Ohlson (1948), Mohor (1948).
  - Hanno tutti fonti in disaccordo; decide la regola del registro (due fonti autorevoli contro Wikidata).
- **Schede:** 407 invece di 408 (esce Henham). Prove 1-7 tutte a 0.
- **Fotografia:** 10 cambi di stato da approvare, tutti «dati»: Kashif e Cruz Balmaceda in Spagna passano dal 2027 al 2028. Marco li deve approvare prima della pubblicazione.
- **Correzione dopo la domanda di Marco «chi decide e controlla il registro?»** Gli 11 autori erano tutti «discorde»: il registro non aveva deciso e teneva l'anno di Wikidata. Non si spostano più.
  - **Regola:** applica_registro_liste e le schede usano l'anno del registro solo se le fonti hanno deciso (verificato, documentato, maggioranza, corretto, nazionale). Con fonti in disaccordo resta l'anno della lista e la scheda dice «Da verificare: le fonti non concordano…». Questa nota ora la decide il registro, non il vecchio scripts/verifica.py.
  - **Prova:** la parte 6 controlla che ogni scheda con fonti in disaccordo lo dica. Ha trovato 6 schede che non lo dicevano: Buck, Henham, Robinson, Scarborough, Garby, Sainsbury. Ora 0.
  - **Risultato:** nessun autore spostato, nessun cambio di stato (fotografia: 0 cambi). Sul sito cambiano solo le note di quelle 6 schede (e delle inglesi), più il «totale» delle liste, che ora è giusto: 2027 dice 1.423, non 1.427.
- **Registro, numeri:** verificato 4.333, documentato 588, una sola fonte 945, discorde 78, maggioranza 45, corretto 14, nazionale 4. I 78 «discorde» entrano nella verifica (docs/verifica-opere.md).

## 22/11/2026 sera — Prova 2 Open Library rifatta con il metodo fissato prima (preparata, non lanciata)
- **Cambi decisi con Marco prima del lancio:**
  - niente filtro «uscite mentre l'autore era vivo», perché taglierebbe le postume e si fiderebbe degli anni peggiori;
  - la misura è decisa prima: 50 candidate a caso (seme 20261122), controllate a mano, da cui una percentuale con il suo margine d'errore;
  - il file si scarica da Internet Archive, tutto su disco prima di leggerlo, e il server di Open Library resta come riserva.
- **Filtri tenuti:**
  - solo persone (P31 = Q5);
  - tolti i titoli che abbiamo già;
  - le probabili raccolte e antologie contate a parte.
- **Giro separato** (prova-openlibrary.yml, partenza da docs/stima-sito/passo-openlibrary.txt). Salva solo il rapporto (prova-openlibrary2.json, campione-openlibrary2.md), niente registro e niente pagine.
- **Il vecchio script prova 2** (con il filtro sull'anno) è sostituito ed è nella storia di git (b8ec64040).

## 23/11/2026 notte — Prova 2 Open Library, primo lancio annullato (giro 45070358753)
- **Esito:** codici Open Library letti: 15.641 per 12.247 persone. Poi lo scaricamento da archive.org (ol_dump_works_2026-10-31) è stato annullato dopo 8 minuti, senza messaggi d'errore: il passo risulta «cancelled». La causa non si vede nel log; un annullamento a mano non si può escludere.
- **Correzione (in locale, non lanciata):** lo script stampa ogni minuto quanto ha scaricato e lo spazio libero. Se la velocità resta sotto 1 MB/s per 2 minuti, curl riprova e riprende da dove era arrivato.
- **Raccolta «fonti delle opere 2027-2028»:** finita (giro del 22/11, 188 minuti), 2.003 opere su 2.003, 967 trovate in almeno un catalogo, nessun errore di rete. L'analisi è al controllo programmato delle 00:50 UTC.

## 23/11/2026 notte — Verifica delle opere 2027-2028: primo rapporto (docs/da-decidere-opere.md)
- **Incrocio:**
  - un'edizione con stesso titolo e stesso autore prova che l'opera era già uscita in quell'anno;
  - per gli USA contano solo le edizioni entro il 1930, quando Wikidata non dà l'anno o ne dà uno più tardo;
  - per l'Europa contano le persone con un ruolo scritto nel catalogo (autore, collaboratore, illustratore, musica), presenti nella prima edizione (anno di Wikidata o prima edizione del catalogo, ±1), non già su Wikidata, morte dopo l'autore e non ancora libere oggi.
- **Europa: 33 casi.**
  - Confermati con fonti web, 5:
    - Ferdinand: il testo è di Munro Leaf, morto nel 1976;
    - Trent's Own Case: coautore H. Warner Allen;
    - I Am a Camera: commedia tratta da Isherwood;
    - Four Saints: musica di Thomson;
    - Honk the Moose: illustrazioni di Wiese;
    - più Shepard, già confermato.
  - Illustratori della prima edizione con una sola fonte: 13.
  - Incerto: 1 (Tribulations, Farrère e Méré).
  - Scartati: 36 attori e produttori senza ruolo; 4 traduzioni o adattamenti presi per prima edizione.
- **USA: 130 opere** con un'edizione entro il 1930 nei cataloghi ma non su Wikidata. Due cataloghi indipendenti d'accordo per 62, uno solo per 68. Tra le 68 ci sono trappole: Gatsby e Gentlemen Prefer Blondes nelle schede dei riduttori teatrali.
- **Niente cambiato sul sito.**

## 23/11/2026 mattina — 62 opere USA dai cataloghi messe nei dati (in locale, da approvare)
- **Dati:** data/verifiche_opere.json, 62 voci (chiave autore|titolo). «entro» è il più tardo dei due cataloghi che hanno un'edizione entro il 1930; ogni voce ha le sue fonti.
- **Codice:**
  - **scripts/registro.py (voci_usa):** le voci con codice d'opera diventano seconda fonte nel registro USA;
  - **regole.stato_opera** (e la gemella JS): se Wikidata non dà l'anno, vale quello confermato dal registro USA;
  - **pagine.stato_usa:** per le opere che non sono in Già pubblici legge verifiche_opere.json e scrive «libero» senza anno, con «entro il 1922» nella colonna dell'anno.
- **Effetto sulle schede:** 55 righe in italiano, le stesse in inglese.
  - 49 passano da «anno non noto» a «libero».
  - 6 passano da «da verificare» a «libero dal…». Queste vengono dal registro delle opere rifatto, che ora conta anche le conferme della Duke aggiunte il 22/11 (Polti, T. Bernard ×3, Toman, May Sinclair in ceco).
- **Effetto su Già pubblici (fotografia):** 15 cambi negli USA da «non determinato» a «libero».
  - 14 vengono da questi dati.
  - 1 viene dalla regola: *Nymphée* di J.-H. Rosny, anno di Wikidata non credibile, ma Open Library conferma un'edizione del 1909.
- **Prove:** 1-7 tutte a 0 differenze.

## 23/11/2026 mattina — Coautori, opere derivate, musica e illustratori confermati messi nei dati (in locale)
- **data/coautori_manuali.json** ha una chiave nuova, «autore|titolo», per le opere senza codice, e quattro ruoli: autore, opera originale, compositore/librettista, illustratore. Ogni voce ha la sua fonte. Voci nuove:
  - Munro Leaf per Ferdinand;
  - H. Warner Allen per Trent's Own Case;
  - Isherwood per I Am a Camera (opera originale);
  - Virgil Thomson per Four Saints (compositore);
  - Shepard per 4 libri di Milne (illustratore);
  - Kurt Wiese per Honk, the Moose (illustratore).
- **Schede:** nuove note per i casi sopra:
  - coautore: «è scritta anche da»;
  - opera originale: «è tratta da un'opera di»;
  - illustratore: «i disegni originali di X hanno diritti propri… il testo segue la data dell'autore».
  - storico/registro_opere.py non conta come autori del testo illustratori, compositori e librettisti scritti a mano.
- **Errore trovato nel radar:** lo stesso della vetrina della home. Il dettaglio di un'opera diceva «Libera dal 1° gennaio» con la data dell'autore, senza la regola dei coautori: L'opera da tre soldi risultava libera nel 2027, Ferdinand nel 2028.
  - Correzione: pagine.py scrive data/vincoli-opere.json (117 opere) con vincoli_opera, cioè la stessa regola delle schede.
  - Il radar toglie dalle «opere che si liberano» quelle con un coautore più tardo o senza data, e mostra la nota (per esempio i disegni di Shepard).
  - Verificato nel browser: L'opera da tre soldi, Trent's Own Case e Ferdinand non ci sono più; Winnie Puh c'è, con la nota.
- **Prove:** 1-7 a 0. Fotografia: 0 cambi, perché le schede e il radar non entrano nella fotografia.

## 23/11/2026 — Disegni e musica allineati su tutto il sito (in locale)
- **Un dato solo, data/coautori_manuali.json:**
  - le schede lo leggono con vincoli_opera;
  - Già pubblici con registro_opere (illustratori, compositori e librettisti messi a mano entrano in «mu»), e la pagina ha la nota nuova sDisegni;
  - la home con nota_disegni, che sostituisce la nota scritta a mano NOTE_VETRINA;
  - il radar con vincoli-opere.json.
- **Milne:** le voci sono legate ai codici delle opere (Winnie-the-Pooh, The House at Pooh Corner con anche la voce della Duke, When We Were Very Young, Now We Are Six).
- **Verifica nel browser:** in Già pubblici, aprendo *Winnie Puh* compare «I disegni originali di E. H. Shepard hanno diritti propri… liberi dal 1° gennaio 2047». Prove 1-7 a 0, fotografia 0 cambi.
- **Errore di procedura di Claude:** il push delle 08:03 ha fatto partire il giro Già pubblici, perché era cambiato storico/registro_opere.py, e non era stato detto prima. Il giro è passato senza problemi.

## 23/11/2026 — Le 9 opere USA dubbie della lista 2027
- **Regola (Marco):** per ogni opera si decide con due fonti se è già libera; se lo è, esce dalla lista. È scritta in scripts/applica_registro_liste.py:
  - fonti: le verifiche delle liste (anno per fonte) e, quando i cataloghi ne danno una sola, le conferme web in data/verifiche_opere.json («usa_prima»);
  - ogni opera tolta è scritta in data/registro/liste_spostati.json («usa_gia_libere»).
- **Tolte da us-2027 (5):**
  - L'opera da tre soldi: 1928 (Duke, K10plus, Wikipedia);
  - Charlie Chan Carries On: 1930 (CCE, LoC, Open Library);
  - Il ballo di Némirovsky: 1930 (CCE, LoC, Open Library);
  - Die Maßnahme: 1930 (K10plus, Brecht Guide dell'Università del Wisconsin). La versione rivista del 1931 si libera nel 2027;
  - With Mystics and Magicians in Tibet: originale francese del 1929 (Plon; BnF/Défense, Wikipedia). La traduzione inglese del 1931 si libera nel 2027.
- **Restano (4):**
  - Tarzan the Invincible: a puntate 1930-31, libro 1931;
  - Tarzan Triumphant: a puntate 1931-32;
  - A Small Circus: originale tedesco del 1931 (K10plus); il 1942 di Wikidata è la traduzione;
  - The Course of Wisdom in Europe: più volumi dal 1931, nessuna fonte prima.
- **Effetto della stessa regola su us-2028:** tolte La laguna e Gli idioti di Conrad (1896: ISFDB, LoC, Open Library). Restano, con una fonte sola: Il ritorno di Conrad, L'uomo senza qualità, Santa Giovanna dei Macelli.
- **Liste:** us-2027 passa da 169 a 164 opere, us-2028 da 175 a 173. Prove 1-7 a 0.

## 23/11/2026 — Correzione di Marco sulle opere USA: esce solo ciò che è libero per intero
- **Regola (Marco):** esce dalla lista solo ciò che è già libero per intero. Se è libera solo una versione (prima versione, originale straniero, uscita a puntate), l'opera resta con una nota.
  - scritta in data/verifiche_opere.json («usa_lista», esito «resta» con nota e fonti), al posto di «usa_prima»;
  - letta da scripts/applica_registro_liste.py; la nota si vede sulla pagina 2027 (prime 12) e nella scheda dell'opera nel radar (tutte).
- **Tornano nella lista con la nota:**
  - Die Maßnahme: prima versione del 1930 già libera, versione rivista del 1931 libera nel 2027;
  - With Mystics and Magicians in Tibet: originale francese del 1929 già libero, traduzione inglese del 1931 libera nel 2027.
- **Vetrina 2027, titoli con «anno da confermare», controllati con due fonti:**
  - Tintin in Congo: a puntate dal 5/6/1930 all'11/6/1931, volume 1931 (BnF, notice de titre; Wikipedia, Tintinologist). Ora «1931 confermato» con la nota sulle tavole del 1930;
  - Why I Am an Atheist: pubblicato il 27/9/1931 su The People (Wikipedia; Marxists Internet Archive). Ora «1931 confermato»;
  - Gaban: Saraswati Press 1931 (Wikipedia; Oxford University Press). Ora «1931 confermato»;
  - nella vetrina 2027 non resta nessun «anno da confermare».
- **Stessa regola, applicata anche a due titoli già confermati della vetrina:** La chiave di vetro (Black Mask, marzo-giugno 1930; University at Buffalo) e La via del ritorno (Vossische Zeitung, dicembre 1930-gennaio 1931; Wikipedia). Restano con la nota sulle puntate.
- **Le opere tolte ora risultano libere negli USA in Già pubblici.** Prima Charlie Chan Carries On, Il ballo, La laguna e Gli idioti vi comparivano come «dal 2027/2028».
  - Ora vale anche lì la regola: se due fonti danno l'opera uscita per intero prima, conta quell'anno (scripts/registro.py, voce «libere»; scripts/regole.py, nei gemelli Python e browser).
  - Fotografia: 4 cambi, approvati (impronta e1275a5e5bcb). L'opera da tre soldi era già libera.
- **Liste:** us-2027 passa da 169 a 166, us-2028 da 175 a 173. Prove 1-7 a 0. Nel browser:
  - pagina 2027 e radar con le note, in italiano e in inglese;
  - Già pubblici con le 5 opere libere negli USA;
  - nessun errore JS.
- **Corretto anche:** liste_spostati.json ora toglie dalle «già libere» le opere che sono tornate nella lista.

## 23/11/2026 — Controllo di Marco: tre punti e i due errori medi
- **1. Note USA sempre con «negli USA»** (data/verifiche_opere.json, «usa_lista»), in italiano e in inglese.
  - Le note sulle opere a puntate dicono anche «in Europa è ancora protetto/a»: Tintin, La chiave di vetro, La via del ritorno.
  - Le note sono in un solo posto, scripts/registro.py (note_usa), e da lì arrivano a:
    - liste e radar (nota_usa);
    - Già pubblici (data/registro/opere.json, «usa_note», mostrata in storico/pagina.html);
    - schede autore (scripts/pagine.py, note_coautori).
- **2. La linea di condotta con due fonti nei dati:** in «usa_lista» c'è «versione_libera» (1930: K10plus e Brecht Guide dell'Università del Wisconsin). Il registro ora dice «due fonti: …» al posto del solo K10plus.
  - Con la stessa regola, quando «usa_lista» ha un anno confermato da due fonti (Tintin, Atheist, Gaban…), quell'anno entra nel registro.
- **3. Vetrina della home sotto controllo:**
  - Margarete Steffin è messa come coautrice, con due fonti ciascuna, in data/coautori_manuali.json:
    - Madre Coraggio: Wikipedia, German Literature;
    - Arturo Ui: DLA Marbach, Suhrkamp;
    - Steffin è morta il 4/6/1941 (Suhrkamp): la data europea non cambia (2027).
  - Le due opere sono nei casi di riferimento (data/casi_riferimento.json, casi 9 e 10). La prova 5 controlla anche le opere non ancora in Già pubblici, con gli stessi dati della home (scripts/pagine.py, opera_regole).
  - Risultato: non controllabili da 4 a 0.
  - Da sapere: Encyclopedia.com scrive che per Arturo Ui Brecht fu aiutato anche dal figlio Stefan (morto nel 2009). L'editore e il DLA indicano come collaboratrice solo Steffin: non l'ho messo coautore.
- **Errori medi corretti (Già pubblici):**
  - La linea di condotta mostra la nota sulla versione rivista del 1931;
  - le 5 opere tolte dicono quale edizione conta negli USA e con quali fonti. I codici delle fonti sono scritti per esteso (es. Catalog of Copyright Entries).
- **Esito:**
  - prove 1-7 a 0: casi di riferimento 26 su 26, vetrina 8 su 8 controllate;
  - fotografia 0 cambi;
  - nel browser, in italiano e in inglese, le note si vedono in Già pubblici e nel radar, senza errori JS.

## 23/11/2026 — Registro delle opere: un anno e una nota per opera, letti da tutte le pagine
- **Problema (Marco):** le regole erano uniche, i fatti no. Il ballo aveva 1930 nella lista USA e 1931 (Wikidata) in Già pubblici, perché Già pubblici prendeva dal registro solo lo stato.
- **Il registro** (data/registro/opere.json, parte nuova «opere», scritta da storico/registro_opere.py con scripts/registro.py, opere_decise).
  - Contiene 73 opere. Per ognuna:
    - anno deciso, di tipo «uscita» o «entro» (entro = un'edizione esiste entro quell'anno, dai cataloghi);
    - «anno_lista», se la versione in lista è un'altra;
    - tutte le fonti, ciascuna con il link;
    - nota in italiano e inglese;
    - da dove viene la decisione.
  - Le fonti web hanno il link alla pagina. Per i cataloghi (LoC, K10plus, BnF) il link è la ricerca nel catalogo per titolo e autore, perché non danno un link stabile alla scheda.
  - Le opere tolte dalle liste ora salvano anche il link a Wikipedia.
  - Non ho toccato il registro degli autori, né spostato o rinominato file.
- **Chi legge dal registro:**
  - **Già pubblici:**
    - i file della ricerca, per autore e scaffali, scritti da storico/applica_registro.py e anche dal giro mensile storico/storico.py;
    - la pagina stessa (regole.anno_deciso, gemello nel browser annoDeciso), così vale anche se i file sono vecchi;
    - la scheda dell'opera mostra la nota, o «un'edizione esiste entro il …»;
    - la frase «conta la data registrata su Wikidata» non compare più quando l'anno viene dal registro.
  - **Liste USA:** non hanno più copie di note e conferme (applica_registro_liste.py le toglie).
  - **Pagine dell'anno:** «confermato» e la nota vengono dal registro.
  - **Radar, IT e EN:** carica il registro solo quando si apre la scheda di un'opera USA.
  - **Schede autore:** anno, «entro il …» e note vengono dal registro. Ogni nota ha il suo numero, prima si vedeva solo la prima.
- **Anni che cambiano** (prima → ora, tutti in Già pubblici e nelle schede):
  - Il ballo 1931 → 1930;
  - Charlie Chan Carries On 1931 → 1930;
  - La laguna 1932 → 1896;
  - Gli idioti 1932 → 1896.
  - Fotografia: 0 cambi di stato.
- **Prova 8, bloccante** (scripts/prova_regole.py). Controlla:
  - il file del registro uguale al calcolo (nessuna copia rimasta indietro);
  - anno uguale al registro in ricerca, per autore, scaffali, liste USA, pagine dell'anno e schede;
  - nota presente nelle pagine dell'anno e nelle schede;
  - nessuna copia della nota nelle liste;
  - «libero/free» sempre con «negli USA / in the US»;
  - almeno due fonti per ogni anno deciso;
  - fonti senza link.
  - Esito: 73 opere, 55 trovate, 112 confronti, 0 diversi.
  - Non controllabili 18: opere del registro (dai cataloghi) che non compaiono in nessuna pagina o file.
  - Prova al contrario: rimesso a mano 1931 a Il ballo e una nota copiata nella lista, la prova li trova tutti e due.
- **Punti a-d:** ricontrollati, erano già a posto (commit 09cf19d); la prova 8 ora controlla il punto a. Errori medi:
  - Maßnahme senza nota in Già pubblici: sparito;
  - anno di Wikidata accanto a «USA libero»: sparito.
- **Esito:**
  - prove 1-8 a 0;
  - browser in italiano e inglese (Già pubblici, radar, pagina 2027, scheda di Brecht, home): nessun errore JS.

## 23/11/2026 — La laguna 1897 e la regola della prima pubblicazione documentata
- **Correzione (Marco, fonti verificate):** The Lagoon uscì su The Cornhill Magazine nel gennaio 1897 (Victorian Web, da F. R. Karl, A Reader's Guide to Joseph Conrad; Wikipedia).
  - Nel registro adesso c'è 1897.
  - Nei dati, per fonte, la Library of Congress dà il 1896, ISFDB il 1897. Il 1896 veniva dall'anno più vecchio fra i cataloghi.
- **Regola nuova** (scripts/regole.py, anno_prima_pubblicazione): quando c'è una prima pubblicazione documentata (rivista o editore, con la data e due fonti), vale quella. I cataloghi confermano ma non la battono.
  - I dati stanno in data/verifiche_opere.json, «prima_pubblicazione».
  - Valgono sia per il registro delle opere sia per l'anno USA del registro.
- **Gli idioti:** 1896 confermato con la prima pubblicazione su The Savoy, ottobre 1896 (Victorian Web, Wikipedia, Project MUSE).
- **Note:** dicono dove uscì l'opera. Per La laguna, la nota dice anche che la Library of Congress dà il 1896.
- **Prova 8:** ora controlla anche che l'anno del registro e l'anno USA siano quelli della prima pubblicazione documentata.
- **Punto c:** alle 9:17 la prova 5 sul sito pubblicato dava ancora «non controllabili», perché il commit 09cf19d è stato pubblicato alle 9:29. Sulla copia attuale dà 8 controllate, 0 non controllabili; i casi 9 e 10 sono in data/casi_riferimento.json.
- **Esito:** prove 1-8 a 0, fotografia 0 cambi di stato.

## 23/11/2026 — Vetrina USA della home nella prova 8
- **Cosa cambia:** le opere USA del frontespizio (La buona terra Q1218608, Le onde Q1217475, Volo di notte Q1070729) ora hanno nella pagina il codice Wikidata. Se il registro delle opere ha una nota, la home mostra quella (scripts/home.py).
- **Prova 8:** controlla anche la home, in italiano e in inglese. Ogni opera USA deve avere il codice e la stessa nota del registro.
- **Esito:**
  - prova 8: 120 confronti (prima 114), 0 diversi;
  - prove 1-8 a 0;
  - fotografia 0 cambi;
  - home IT/EN senza errori JS.

## 23/11/2026 — Ricerca sulle 52 opere USA 2027 «da confermare» (solo ricerca, niente applicato)
- **Metodo:** circa 50 ricerche web, dalle opere più viste, con le regole di Marco:
  - due fonti indipendenti, di cui almeno una primaria o specialistica;
  - vale la prima pubblicazione documentata;
  - una regola sola per originali e traduzioni;
  - le opere uscite dopo il 1931 si spostano.
- **Esito** (rapporto in docs/da-decidere-usa-2027.md, opera per opera con i link):
  - 28 confermate 1931;
  - 7 restano con la nota (una parte uscita prima);
  - 2 escono (Quicksand e Macchina, uscite per intero a puntate entro il 1930);
  - 3 da spostare (La madre e Vlak u snijegu al 2029, Il 35 maggio al 2028);
  - 3 da decidere (Noce i dnie, Kondujt i Švambranija, Los placeres prohibidos);
  - 6 incerte;
  - 3 già decise.
- **Fonti deboli segnalate:** San Manuel Bueno, Racconti di Odessa, Vlak u snijegu. Marco fa controllare a campione 10 opere prima di decidere.

## 23/11/2026 — Decisioni sulle 52 opere USA 2027 applicate (decise dall'altra chat, su delega di Marco)
- **Dati:** `data/verifiche_opere.json`, «usa_lista», 43 decisioni nuove, ognuna con due o più fonti e i link:
  - 27 confermate 1931 (resta);
  - 7 restano con la nota: Number 31328, Il baldacchino nuziale, The London Scene, L'ombra dell'uccello, I vagabondi, Siamese Musical Instruments, Altazor;
  - 3 tolte, già libere per intero: Quicksand (1930), Macchina (1930), Racconti di Odessa (1924, raccolta senza testi nuovi);
  - 6 spostate: Il 35 maggio e Noce i dnie (vol. I) al 2028; La madre, Vlak u snijegu e Švambranija al 2029; Los placeres prohibidos al 2032.
- **Fonti nuove verificate oggi:**
  - Altazor: nota della prima edizione 1931 (CIAP), Cyber Humanitatis e Revista Chilena de Literatura (Universidad de Chile): frammenti dal 1925;
  - San Manuel: Open Library, nota del prologo (La Novela de Hoy n. 461, 13 marzo 1931);
  - Noce i dnie: lubimyczytac (I e II 1932, III 1933, IV 1934) e Britannica (1932-34). Goodreads non conta: dà anni diversi da edizione a edizione.
- **Do swego Boga:** resta «da confermare». Per il 1894 c'è ancora una fonte sola (one.bid); il record BnF cb332271862 non dà la data.
- **Codice:**
  - `scripts/applica_registro_liste.py`: nuovo esito «sposta». L'opera esce dalla lista; se la lista del suo anno c'è, ci entra; altrimenti aspetta in liste_spostati.json, «usa_spostate»;
  - `scripts/registro.py`: «tolta» e «sposta» danno anno, fonti e nota nel registro delle opere.
- **Regola scritta** in docs/verifica-opere.md: raccolte (senza testi nuovi = esce; con almeno un testo nuovo = resta con nota) e opere in più volumi.
- **Esito:**
  - us-2027 passa da 166 a 157 opere; us-2028 passa da 173 a 175;
  - prove 1-8 a 0 (prova 8: 236 confronti, 0 diversi, 23 non mostrati);
  - fotografia: 2 cambi di stato, entrambi voluti (Racconti di Odessa e Macchina: da «dal 2027» a «libero» negli USA).
- **Limiti:**
  - Quicksand entra in Già pubblici solo al giro mensile dello Storico (2 dicembre): oggi non è nella ricerca, perché con il 1931 non era libero da nessuna parte;
  - per Noce i dnie i volumi II-IV non hanno un codice Wikidata proprio: i loro anni sono nella nota;
  - Švambranija, La madre, Vlak u snijegu e Los placeres prohibidos aspettano che si creino le liste 2029 e 2032.

## 23/11/2026 — Approvati i 2 cambi di stato delle opere USA tolte
- **Approvazione di Marco:** Racconti di Odessa e Macchina passano da «dal 2027» a «libero» negli USA. Impronta f1eaf52c4506, aggiunta a data/cambi-approvati.txt.
- **Fotografia:** aggiornata (data/fotografia.json.gz). Il confronto rifatto dà 0 cambi; docs/cambi-da-approvare.md dice «Nessun cambio di stato da approvare».
- **Il ballo:** non c'è nessun errore aperto. In Già pubblici ha il 1930 (Q3220209) da stamattina: era una mia segnalazione sbagliata.

## 23/11/2026 — Campione di 30 autori «una fonte» delle liste 2027 (solo rapporto)
- **Come:** 30 estratti a caso (seme 20261123) dai 395 autori «una_fonte» di 2027 ed es-2027. Per ognuno ho cercato due fonti indipendenti da Wikidata. Circa 45 ricerche web.
- **Esito** (docs/campione-una-fonte-2027.md):
  - 5 confermati;
  - 0 sbagliati con due fonti;
  - 1 in disaccordo: F. Hadland Davis, Gutenberg dà 1956, Wikidata 1946;
  - 8 con una fonte sola, tutte concordi con Wikidata;
  - 16 non trovati.
- **Giudizio:** per la regola decisa prima vale «0 sbagliati». Però con 16 non trovati il campione non può escludere errori, e il caso Davis tocca proprio il confine tra la lista spagnola e quella europea.
- **Nel sito:** niente cambiato.

## 23/11/2026 — Davis «discorde», autori senza nome fuori dalle liste pubbliche, controllo automatico preparato
- **Campione dei 30 autori:** l'esito è inconcludente (decisione di Marco), non «0 sbagliati»: 16 su 30 non sono verificabili. I 395 non si controllano a mano.
- **Davis (Q87470685):**
  - nuova parte «fonti_aggiunte» in data/verifiche_manuali.json, con Project Gutenberg 1882-1956 e il link. Queste fonti entrano nel confronto ma non decidono l'anno;
  - lo script scripts/registro_autori.py le legge (aggiungi_fonti); l'esito ora è «discorde»;
  - scripts/applica_registro_liste.py scrive nella lista la nota «da verificare» per gli autori «discorde» del registro, se la lista non l'ha già;
  - regole.morte_dal_registro: Gutenberg, che è una fonte debole, non conta per dire «sul confine», come già succedeva per le fonti citate.
- **Autori senza nome:**
  - regola in scripts/regole.py (autore_con_nome, lista_pubblica) con la gemella autoreConNome nel browser. Le usano il radar, le pagine dell'anno, le schede e la home; i file data/*.json restano completi;
  - quanti sono: 45 in tutto (2027: 2, 2028: 19, es-2027: 14, es-2028: 10). Di questi, 25 sono letterari con una data e quindi cambiano i conteggi (1, 11, 8, 5);
  - la prova 1 ora confronta anche la regola dei nomi (Python e browser).
- **Errore trovato e corretto durante la prova:** un primo tentativo toglieva gli autori senza nome anche dai file dei dati, perché scripts/pagine.py riscrive le liste. Ora la riscrittura legge il file completo.
- **Controllo automatico preparato, non lanciato:**
  - script scripts/confronta_una_fonte.py e giro .github/workflows/confronto-una-fonte.yml, che parte cambiando docs/registro/passo-confronto.txt;
  - confronta gli autori con Open Library e Project Gutenberg, abbinati con i codici Wikidata P648 e P1938.
- **Esito:**
  - prove 1-8 a 0 (prova 1: 36.937 confronti);
  - fotografia 0 cambi: la fotografia legge i file dei dati, che non cambiano.

## 23/11/2026 — Autori senza nome: prima si cerca il nome in qualsiasi lingua (correzione di Marco)
- **Regola corretta:** si nasconde solo chi non ha un nome in nessuna lingua su Wikidata. Gli altri compaiono con il nome originale, e con la traslitterazione se Wikidata ne ha una.
- **Perché succede:** scripts/aggiorna.py chiede il nome solo in 18 lingue. Chi ce l'ha solo in un'altra lingua (ucraino, georgiano, arabo...) resta con il codice.
- **Codice:**
  - scripts/nomi_originali.py cerca in Wikidata, in qualsiasi lingua, il nome nella lingua nativa (P1559), le etichette e gli altri nomi. Scrive data/registro/nomi_originali.json;
  - giro .github/workflows/nomi-originali.yml, e un passo nel giro mensile aggiorna.yml;
  - scripts/applica_registro_liste.py mette il nome nella lista, oppure «senza_nome» se un nome non c'è in nessuna lingua;
  - regole.autore_visibile, con la gemella autoreVisibile, nasconde solo chi ha «senza_nome».
- **Finché il giro dei nomi non è passato non si nasconde nessuno:** i numeri delle pagine restano 826 e 790.
- **Esito:** prove 1-8 a 0, fotografia 0 cambi.
- **Giro dei nomi (11:02):** tutti e 45 gli autori hanno un nome in qualche lingua, 0 non ne hanno nessuno. Quindi non si nasconde nessuno.
  - 1 ha anche una traslitterazione: Q6749996 «יהושכר כרכי (קרקובסקי) (Jehoŝua Kraki)»;
  - per esempio Q20483877 ora è «Өтеп Оңғарбаев» (kazako).
- **Applicato:**
  - le liste e le pagine mostrano i nomi originali;
  - i numeri restano 826 e 790 per il 2027;
  - nelle schede il «su N» delle classifiche torna a contare anche questi autori (per esempio da «6° su 825» a «6° su 826»).
- **Esito:** prove 1-8 a 0, fotografia 0 cambi di stato.

## 23/11/2026 — Confronto automatico dei 394 autori «una fonte» 2027 (giro delle 11:02, durato 7 minuti)
- **Esito:**
  - 370 senza codici: nessun codice Open Library né Gutenberg in Wikidata;
  - 11 d'accordo;
  - 2 in disaccordo;
  - 11 senza anno.
- **Disaccordi:** tutti e due sul confine europeo, Wikidata 1956 contro Open Library 1957. Con il 1957 entrerebbero nel 2028, non nel 2027.
  - Syed Emdad Ali (Q7660316, OL11762A);
  - Zebi Eliezer Kroy (Q113360712, OL146206A).
- **Problema:** Project Gutenberg non ha risposto a nessuna delle 8 pagine autore (su GitHub dava «non risponde»), quindi il confronto con Gutenberg non è stato fatto. Il confronto con Open Library sì.
- **Nel sito:** niente cambiato.

## 23/11/2026 — Due disaccordi risolti, Gutenberg dal catalogo, chiusura del lavoro sui «una fonte»
- **Syed Emdad Ali (Q7660316) e Zebi Eliezer Kroy (Q113360712): 1956**, per decisione di Marco con le fonti:
  - Banglapedia, «Ali, Syed Emdad (1875-1956)»;
  - Yiddish Leksikon, «December 25, 1900-December 29, 1956», che cita Kressel, Leksikon hasifrut haivrit, vol. 2 (1967).
- **Come sono registrati:**
  - in data/verifiche_manuali.json («autori», verifica a mano: esito «nazionale», cioè confermato);
  - Open Library (1957) è in «fonti_aggiunte»: è una fonte in disaccordo e non ha effetto;
  - scripts/applica_registro_liste.py ora scrive nella lista anche le verifiche a mano. Effetto sul sito: per questi due il radar non dice più «una sola fonte».
- **Gutenberg, una sola prova:** scripts/confronta_una_fonte.py legge ora il catalogo RDF in file unico (rdf-files.tar.bz2) invece delle pagine autore. Se non funziona, si lascia.
- **Chiuso il lavoro sui 395 «una fonte»** (Marco): basta la nota del sito «anno di morte da una sola fonte».
- **Esito:** prove 1-8 a 0, fotografia 0 cambi.

## 23/11/2026 — Gutenberg dal catalogo: non funziona, si lascia
- **Esito del giro delle 11:21:** il catalogo RDF di Gutenberg ha risposto «HTTP 503 Service Unavailable». Come deciso, Gutenberg si lascia.
- **Open Library su 392 autori:** 11 d'accordo, 0 disaccordi, 11 senza anno, 370 senza codici.

## 23/11/2026 — Incrocio delle fonti sulle opere in codice, collaudo alla cieca, giro 2028 (solo rapporti)
- **Regola:** regole.incrocio_opera (passo 2 di docs/verifica-opere.md).
  - Esiti: conferma, nota, esce, sposta, da decidere.
  - La prima pubblicazione documentata vale più dei cataloghi.
  - Le traduzioni non votano: un catalogo vota solo per le opere nella lingua delle sue edizioni (CCE, LoC, Open Library e ISFDB per l'inglese, K10plus per il tedesco, BnF per il francese).
  - Open Library conta insieme alla LoC, perché la ripete. Wikidata con più date non vota.
  - Raccolte, volumi e prima pubblicazione documentata entrano come «fatti» dalle verifiche.
  - Ogni decisione vuole due gruppi indipendenti; un solo indizio contrario dà «da decidere».
- **Collaudo alla cieca** (scripts/collaudo_incrocio.py, docs/collaudo-incrocio.md):
  - 55 opere: le 50 di «usa_lista» e le 5 tolte stamattina che non sono già fra quelle;
  - il sistema legge solo i dati raccolti in automatico e la lingua dalle liste com'erano prima delle decisioni (commit c50a23324); le decisioni si leggono dopo;
  - esito: giuste 2, sbagliate 0, da decidere 53. Le due giuste sono Gli idioti e Charlie Chan Carries On, entrambe «esce».
- **Prima versione corretta durante la prova:** bloccava ogni «esce» se c'era un'indicazione di uscita a puntate. Ora le puntate bloccano solo se iniziano prima dell'anno trovato o durano più anni. Con la prima versione: 1 giusta, 0 sbagliate.
- **Limite del collaudo:** le 55 opere sono i casi difficili, quelli che il sistema non sapeva già confermare. Il ramo «conferma» non è mai stato messo alla prova.
- **Giro sulla lista 2028** (scripts/incrocio_opere.py, docs/incrocio-us-2028.md): 175 opere, 78 conferma e 97 da decidere. Sono «conferma» non collaudate.
- **Preparato, non lanciato:**
  - giro annuale degli autori mancanti (scripts/autori_mancanti.py, .github/workflows/autori-mancanti.yml, che parte con docs/registro/passo-mancanti.txt);
  - fonti: categorie Wikipedia dei morti dell'anno in en, it, de, fr, es e pl (con una categoria da scrittore) e la GND; poi Wikidata dice perché l'autore manca.
- **Nel sito:** niente cambiato. Prove 1-8 a 0.

## 23/11/2026 — Campione di 15 «conferma» 2028: non passa; regola corretta; dati più ricchi preparati
- **Campione** (docs/campione-conferma-2028.md, seme 20261123, controllo a mano sul web): 14 giuste, 1 sbagliata o dubbia.
  - The Black Swan: il racconto da cui nasce il romanzo è uscito su Ladies' Home Journal a settembre 1931. Doveva essere almeno «nota».
  - Regola 0 sbagliate: **il ramo «conferma» non passa.**
- **Correzione di regole.incrocio_opera:** per confermare serve una prima pubblicazione documentata (Duke, ISFDB, rivista con data su Wikidata, ricerca sul web registrata). Wikidata e cataloghi da soli danno l'anno del libro, non della prima uscita.
  - Lista 2028: conferma da 78 a 12 (tutte con ISFDB); The Black Swan ora «da decidere». Le 12 non sono ricontrollate a mano.
  - Collaudo sulle 55: invariato, 2 giuste, 0 sbagliate, 53 da decidere.
- **Dati più ricchi, preparati e non lanciati:** scripts/fonti_prima_uscita.py con .github/workflows/fonti-prima-uscita.yml (parte con docs/registro/passo-fonti.txt).
  - Wikidata: data (P577), rivista di prima uscita (P1433) e date delle edizioni (P629) per 344 opere (liste 2027 e 2028 e le opere tolte o spostate).
  - Bibliografia nella lingua originale, col titolo originale: K10plus per il tedesco (la DNB blocca GitHub), BnF per il francese, BNE per lo spagnolo, SBN per l'italiano.
  - Nella regola: la bibliografia nella lingua originale vota; le date di riviste ed edizioni da Wikidata sono indizi.
- **Ricerca sul web come procedura fissa:** docs/ricerca-web.md (cosa cercare, fonti che valgono, formato fisso) e docs/ricerca-web/risultati.json. Decide regole.fatti_da_ricerca: due gruppi indipendenti per ogni fatto; una fonte sola resta indizio. Prima voce: The Black Swan (una fonte con link).
- **Nel sito:** niente cambiato. Prove 1-8 a 0, fotografia 0 cambi.

## 23/11/2026 — Riverifica dei confermati 2027, prime ricerche sul web, Dehkhoda, conteggio dei saggisti (preparato)
- **Riverifica** (scripts/riverifica_confermati.py, docs/riverifica-confermati-us-2027.md): le 111 opere segnate «ok» il 20/11 e ancora nella lista 2027, ripassate con la regola di oggi.
  - Senza ricerca sul web: 13 conferma, 98 da decidere.
  - Il motivo: il 20/11 85 delle 111 erano state confermate da una sola fonte (di solito il registro CCE) che aveva trovato un'edizione del 1931.
- **Ricerca sul web** (docs/ricerca-web.md), partendo dalle più viste: La buona terra, Le onde, The Whisperer in Darkness, The Sittaford Mystery, Sanctuary, The Joy of Cooking. Due fonti indipendenti per ciascuna, tutte danno il 1931; in docs/ricerca-web/risultati.json.
  - The Sittaford Mystery è uscito a puntate su Good Housekeeping da marzo ad agosto 1931, prima del libro: tutto nel 1931, quindi resta.
  - Dopo: 19 conferma, 92 da decidere.
- **Dehkhoda:** morto nel 1956 secondo l'Encyclopaedia Iranica e Rekhta (docs/verifica-autori-mancanti-2027.md). Wikidata (1959) sbaglia. Non inserito nella lista: serve l'ok di Marco.
- **Conteggio dei saggisti, preparato e non lanciato:** scripts/conta_saggisti.py con .github/workflows/conta-saggisti.yml (parte con docs/registro/passo-saggisti.txt).
- **Nel sito:** niente cambiato.

## 23/11/2026 — Incrocio sulle 111 confermate 2027 con i dati nuovi; Dehkhoda nella lista 2027 (preparato)
- **Giro fonti-prima-uscita** (fatto alle 12:58), 344 opere:
  - Wikidata: tutte hanno una data (P577); 26 hanno la rivista di prima uscita (P1433) e 79 hanno edizioni datate;
  - bibliografia nella lingua originale: 71 opere con un anno (BnF 35, K10plus 30, BNE 5, SBN 1).
- **Incrocio sulle 111:** 20 conferma, 91 da decidere (prima dei dati nuovi: 19 e 92). Collaudo sulle 55: invariato, 2 giuste e 0 sbagliate.
  - Giudizio: la bibliografia nazionale dà l'anno del libro, non della prima uscita, quindi da sola non conferma (è il caso Black Swan). Esempio: Der Weg zurück, K10plus 1931, ma secondo la verifica a mano (data/verifiche_opere.json) era uscito a puntate sulla Vossische Zeitung fra dicembre 1930 e gennaio 1931.
  - La rivista su Wikidata c'è per poche opere.
- **Dehkhoda:** Encyclopaedia Iranica letta su iranicaonline.org (26 febbraio 1956). Scheda da costruire con scripts/scheda_autore.py e .github/workflows/scheda-autore.yml (parte con docs/registro/passo-scheda.txt); non lanciato.

## 23/11/2026 — Ricerca sul web, lista USA 2027, blocco 1 (18 opere)
- **Esito** (docs/ricerca-web/blocco-01-2027.md): 12 conferma, 2 nota (Wyatt Earp, The Face in the Abyss), 4 da decidere. Fonti in disaccordo solo per Living My Life (volume 2: 1931 o 1934).
- **Regola rafforzata** (regole.incrocio_opera e fatti_da_ricerca): se anche una sola fonte indica un'uscita più vecchia, non si conferma («da decidere»). Caso: If It Had Happened Otherwise.
- **Lista 2027:** delle 111, conferma 32, nota 2, da decidere 77. Collaudo sulle 55 invariato (2 giuste, 0 sbagliate). Lista 2028: 14 conferma (prima 12; la differenza viene dai dati del giro fonti-prima-uscita, non ricontrollata a mano).
- **Proposta** in docs/giri-automatici.md: verifica delle opere USA per la lista 2029, da gennaio 2027.
- **Conteggio dei saggisti:** il giro è fallito alla richiesta del numero di Wikipedia (Wikidata non ha risposto a 200 autori per volta). Corretto: 50 per volta. Da rilanciare con l'ok di Marco.
- **Nel sito:** niente cambiato. Prove 1-8 a 0.

## 23/11/2026 — Dehkhoda nella lista 2027 (preparato, non pubblicato)
- **Scheda** (giro scheda-autore, data/registro/schede_proposte.json): professioni su Wikidata giornalista, lessicografo, letterato, linguista, politico, satirista, scrittore, traduttore; descrizione «Iranian linguist and lexicographer»; 2 opere su Wikidata. Per la regola della lista è solo in «Tutti».
- **Correzioni a mano** (data/verifiche_manuali.json):
  - fonti aggiunte: Encyclopaedia Iranica 1956 e Rekhta 1956;
  - professione «poeta» con la fonte Iranica («scholar, poet, and social critic»).
- **Regola:** Encyclopaedia Iranica e Rekhta entrano fra le fonti autorevoli (scripts/regole.py). Effetto sugli altri autori: nessuno; Iranica era citata solo per Balaghi e Christensen, già d'accordo.
- **Esito:** «corretto», 1956 (Wikidata 1959). Entra da data/morti_corrette.json, come gli altri corretti, quindi resta anche ai giri successivi.
- **Anche con «poeta» resta solo in «Tutti»:** la descrizione nomina solo mestieri non letterari, quindi la regola vuole almeno 5 opere su Wikidata, e ne ha 2.
- **Fotografia:** 1 cambio, l'autore nuovo Q470931. Prove 1-8 a 0. Non pubblicato: aspetta l'ok di Marco.

## 23/11/2026 — Regola della registrazione (CCE), volumi in anni diversi, blocco 2, Dehkhoda (verifica a mano)
- **Registrazione** (decisione di Marco; Circular 15A): conta la prima tra pubblicazione e registrazione da inedita, presa dal CCE; per le riviste vale la data © del numero.
  - Green Grow the Lilacs: CCE 1930, D unpub. 7017, 30 agosto 1930 → esce.
  - Dry September: CCE 1931 Periodicals, Scribner's v. 89 n. 1, © 18 dicembre 1930 → esce.
- **Volumi:** primo volume nell'anno della lista e altri dopo → nota; volume con fonti in disaccordo → nota «da verificare». Casi: The Sleepwalkers (vol. 3 1932), Living My Life (vol. 2 1931 o 1934).
- **Blocco 2** (docs/ricerca-web/blocco-02-2027.md): 11 conferma, 1 nota, 6 da decidere; fonti in disaccordo per Pietr-le-Letton e Proust.
- **Lista 2027:** conferma 41, nota 5, esce 2, da decidere 63. Collaudo sulle 55 invariato.
- **Dehkhoda rifatto:** Rekhta tolta dalle fonti autorevoli; verifica a mano (Iranica e Rekhta, con link) ed esito «nazionale»; segnalato come scrittore a mano (Iranica), quindi entra nella lista principale. Codice: verifica.py aggiunge chi manca quando la verifica a mano dà lo stesso anno; arricchisci.py legge professioni e scrittori aggiunti a mano. Fotografia: 1 cambio, l'autore nuovo. Non pubblicato.
- **Conteggio dei saggisti:** secondo giro fallito di nuovo al numero di Wikipedia. Ora, se Wikidata non risponde, si aspetta e si va avanti senza quel dato. Da rilanciare con l'ok di Marco.

## 23/11/2026 — Metodo prima del blocco 3: criteri in un posto, casi per ogni regola, citazioni, tre stati
- **docs/criteri.md:** criterio della verifica delle opere USA («una scheda CCE basta da sola; per tutto il resto servono due fonti») ed elenco delle regole con data, motivo e caso.
- **Regola più stretta:** Wikidata non fa da seconda fonte per confermare. Lista 2027: conferma 28, nota 5, da decidere 76 (prima 41 conferma). Lista 2028: conferma 1 (prima 14). Collaudo: 4 giuste, 0 sbagliate, 53 da decidere (le 2 giuste in più sono Green Grow the Lilacs e Dry September, che però non sono alla cieca: la decisione viene dalla stessa ricerca).
- **Casi di riferimento:** data/casi_riferimento.json, sezione «incrocio»: La laguna, Racconti di Odessa, Altazor, The Black Swan, I sonnambuli, Green Grow the Lilacs, Dry September. La prova 4 li rifà: 7 su 7.
- **Citazioni:** campo obbligatorio in docs/ricerca-web.md; riempito per le 91 voci già scritte, da frasi delle pagine lette; controllo automatico preparato (scripts/controlla_citazioni.py, .github/workflows/citazioni.yml, parte con docs/registro/passo-citazioni.txt), non lanciato. L'incrocio non usa le voci senza citazione o con la citazione non trovata.
- **Seconda lettura** di 3 voci a caso per blocco (seme 20261123 + numero del blocco): blocco 1 voci 13, 24, 56; blocco 2 voci 57, 77, 85. Lanciata in un'altra chat.
- **Tre stati della lista USA** (regole.stato_usa_lista, scripts/stati_usa.py → data/registro/stati_usa.json): 2027 su 155 opere: 56 prima uscita verificata, 91 anno dell'edizione confermato, 8 da confermare. Delle 41 decise a mano il 23/11, 18 hanno solo una fonte indipendente oltre a Wikipedia: per il criterio sono «anno dell'edizione confermato». Non pubblicato.
- **Fotografia:** ora controlla anche le liste USA per anno. Prima 79 delle 157 opere della lista 2027 non erano nella fotografia, quindi un'opera tolta dalla lista non si vedeva (Dry September).
- **Q1306780:** è la raccolta Beim Bau der chinesischen Mauer (Kiepenheuer 1931): lo dicono il titolo e la data su Wikidata e la pagina Wikipedia collegata. Il titolo italiano «Un messaggio dell'imperatore» viene dall'etichetta italiana di Wikidata ed è sbagliato per la raccolta.

## 23/11/2026 — Pubblicazione della fotografia 6fced287e3a0 e lancio del controllo delle citazioni (ok di Marco, 14:57)
- Impronta 6fced287e3a0 aggiunta a data/cambi-approvati.txt; la fotografia nuova prende il posto della vecchia. Sul sito: escono Green Grow the Lilacs e Dry September dalla lista USA 2027 (155 libri); frase delle verifiche a mano «controllato a mano su fonti terze».
- Lanciato citazioni.yml (docs/registro/passo-citazioni.txt): solo rapporto, non cambia il sito.

## 23/11/2026 — Controllo delle citazioni: primo giro e correzione del controllo
- **Primo giro** (citazioni.yml): 41 trovate, 32 non verificabili in automatico, 18 non trovate.
- **Ricontrollo a mano delle 18 non trovate** (lettura delle pagine):
  - 1 citazione sbagliata: The Face in the Abyss (voce 38). I fatti erano giusti ma la frase non era quella esatta dell'SFE. Ora è «stories first appeared 8 September 1923 Argosy».
  - 3 pagine anti-bot (Brown, Princeton, Marsh's Library): il controllo le contava come «non trovata».
  - 9 citazioni presenti nella pagina ma divise dai tag HTML o dagli a capo dei PDF: Sanctuary (Nobel), If It Had Happened Otherwise (SFE), The Floating Admiral (Fantlab), Back Street, Proust (Taylor & Francis), Fabian (DDB, 2 voci), Swallowdale (Loughborough), The Great Wall of China (dLib, PDF).
  - 1 link scritto con «\» invece di «/»: The Sittaford Mystery (deliciousdeath). Corretto; la citazione c'è.
  - 4 non controllabili da qui: Le Feu follet (Universalis, Wikisource), Night Flight (Lavoisier), Coup d'État (Universalis). Restano fuori dall'incrocio finché il controllo non le trova.
- **Correzione del controllo** (scripts/controlla_citazioni.py):
  - seconda prova con sole lettere e cifre, così spazi, punteggiatura e a capo non contano;
  - pagine anti-bot e pagine che non mostrano il testo della scheda → «non verificabile in automatico»;
  - «non trovata» resta solo quando le parole ci sono ma la frase esatta no;
  - controlla anche le fonti delle verifiche a mano degli autori e le opere principali degli autori aggiunti a mano (chiavi «a:»).
- **Effetto sui tre stati 2027:** con il primo giro le prime uscite verificate scendono da 54 a 44, perché le voci «non trovata» non contano più. Il numero si rifà dopo il secondo giro del controllo.

## 23/11/2026 — Etichette dei tre stati, Subbaravu, 8 saggisti a mano (ok di Marco, 14:57)
- **Etichette accanto ai libri:** «Verificato», «Edizione confermata», «Da confermare» (EN «Verified», «Edition confirmed», «To be confirmed»). L'introduzione è quella approvata, con i nomi corti delle etichette. Lo stato si calcola nelle pagine con regole.stato_usa_lista (scripts/stati_usa.py, stati_anno), così non resta un file vecchio. Vale per tutte le liste USA, quindi anche per la 2028: 1 verificata, 109 edizione, 65 da confermare. La prova 8 ora controlla che un anno deciso nel registro non compaia «da confermare». Non pubblicato.
- **Subbaravu (Q6963402):** ho cercato fonti terze per l'anno di morte.
  - Triveni Journal, numero di luglio 1957: necrologio («The death of their author, Mr. Nanduri Venkata Subba Rao»), https://www.wisdomlib.org/history/compilation/triveni-journal/d/doc69419.html. Dice che a luglio 1957 era già morto, ma non dà la data.
  - Seconda fonte terza non trovata. L'Encyclopaedia of Indian Literature (vol. 2, pp. 1173-1174) è citata da un blog, ma non l'ho letta.
  - Senza la verifica a mano non tornerebbe «da una sola fonte»: GND e Library of Congress danno il 1958 (registro autori). Con la regola delle due fonti autorevoli diventerebbe «corretto 1958» e uscirebbe dalla lista 2028. Ma il necrologio del luglio 1957 contraddice il 1958. Non applicato: decide Marco.
- **Altre verifiche a mano con Wikipedia** (del 09/11/2026): Răcăciuni (Wikipedia en e Ziarul de Bacău), Romanescu (il link è a Wikipedia), von den Steinen (Wikipedia de via BookBrainz). Segnalate, non toccate.
- **8 saggisti a mano** (docs/saggisti-a-mano.md): anno di morte da due fonti terze con citazione, opera principale con fonte, segnati come scrittori e saggisti; data/verifiche_manuali.json «aggiunti_a_mano». Entrano solo con «approvato»: true. La scheda viene da scheda-autore.yml, che ora legge i codici da docs/registro/passo-scheda.txt. scripts/verifica.py li mette nella lista (anche senza rete: --solo-aggiunti; --anteprima per la fotografia prima dell'ok). La prova 9 controlla fonti, citazioni, opera e lista. Le pagine delle verifiche a mano ora linkano anche la seconda fonte.

## 23/11/2026 — Blocco 3 (docs/ricerca-web/blocco-03-2027.md)
- 14 opere, 25 voci, tutte con citazione. Seconda lettura di 3 voci (seme 20261126) prima di applicarle: 1 confermata, 2 non verificabili (anti-bot, link che apre la home), nessuna smentita.
- Esito: 8 conferma, 1 nota (raccolta di Kafka), 5 da decidere.
- Lista 2027: prima uscita verificata 53, anno dell'edizione confermato 94, da confermare 8 (con le 18 voci «non trovata» del primo giro del controllo ancora escluse).
- Limite trovato: l'esito «nota» della ricerca non mette la nota in pagina (6 opere). Da sistemare con un'approvazione di Marco sui testi delle note.

## 23/11/2026 — Verifiche a mano rifatte, note delle opere «nota» (ok di Marco, 15:20)
- **Subbaravu:** verifica a mano «discorde» (Triveni Journal, luglio 1957, contro GND e LoC 1958). Resta nella lista 2028 con l'avviso «da verificare». La regola è ora in un posto solo, regole.voce_morte, usata dal registro degli autori (scripts/registro_autori.py, anche senza rete con --solo-manuali) e da verifica.py.
- **Răcăciuni, Romanescu, von den Steinen:** nessuna seconda fonte terza; verifiche a mano tolte (data/verifiche_manuali.json, «verifiche_tolte»).
  - Romanescu: torna «discorde» (Wikidata 1956, GND 1955, LoC 1954). Trovata una sola fonte terza: Muzeul Aman, «m. 1956».
  - Von den Steinen: l'Onassis Cavafy Archive dice 1956, la vecchia verifica diceva 1957.
  - Răcăciuni e von den Steinen non sono in nessuna lista e nel registro: tornano al primo giro automatico, con lo stato delle fonti automatiche.
- **Note delle opere con esito «nota»:** sono 4, non 6 (avevo contato male): I sonnambuli, Wyatt Earp: Frontier Marshal, la raccolta di Kafka, Tarzan the Invincible. I testi sono in data/verifiche_opere.json «usa_lista», con le fonti della ricerca. Regola nuova in docs/criteri.md.
- **Registro degli autori rifatto per le verifiche a mano:** 4 voci (Romanescu e Subbaravu discordi, Keynes nazionale, Dehkhoda con il secondo link).
- **scheda-autore.yml, primo giro per gli 8 saggisti:** fermato dopo 20 minuti (Gutenberg non rispondeva per Sarton) senza salvare nulla. Corretto: si salva dopo ogni autore, si riprende chi è già fatto, limite 90 minuti. Da rilanciare con l'ok di Marco.
- **Note approvate da Marco (15:48):** I sonnambuli, Wyatt Earp, Tarzan the Invincible. Per la raccolta di Kafka la frase su «Eine kaiserliche Botschaft» (1919) resta, perché c'è la seconda fonte: TextGrid, «Erstdruck in: Selbstwehr. (Prag), 13. Jg., Nr. 38/39, 1919.» (https://www.textgridrep.de/browse/qmwb.0?lang=en). franzkafka.de dà «24. September 1917», ma per l'annata (13. Jg.) è un refuso: non usata.
- **scheda-autore rilanciato** (ok di Marco, 15:48) per 10 autori: gli 8 saggisti, Răcăciuni e von den Steinen.
- **Schede dei 10 autori:** riuscite (data/registro/schede_proposte.json). Keynes non aveva l'etichetta italiana e la scheda aveva solo il codice: ora il nome viene dalla voce a mano, e scheda_autore.py usa l'etichetta di riserva.
- **Rientri:** chi ha avuto la verifica a mano tolta torna nella lista dell'anno di Wikidata (scripts/verifica.py, inserisci_rientri, anche nel giro). Răcăciuni (Wikidata 1956) e von den Steinen (Wikidata 1956) rientrano nella lista 2027 con «una sola fonte». Le biblioteche le legge il giro dopo.
- **Anteprima della pubblicazione unica** (verifica.py --solo-aggiunti --anteprima): fotografia con 0 cambi di stato e 10 autori nuovi; prove 1-9 a 0. Lista 2027: 62 / 85 / 8.

## 23/11/2026 — Pubblicazione unica (ok di Marco, 16:23)
- **Contenuto:**
  - etichette dei tre stati: 2027 62 / 85 / 8, 2028 1 / 109 / 65;
  - 4 note delle opere «nota»;
  - 8 saggisti approvati;
  - von den Steinen rientra;
  - Subbaravu e Romanescu «da verificare».
- **CASO APERTO — Isaiia Răcăciuni (Q12731091):** Wikidata dice 1956, Wikipedia (en) dice 17 giugno 1976. Sono 20 anni di differenza: se fosse il 1976, in Europa le opere sono protette fino al 2046. Decisione di Marco: resta fuori dalle liste finché una fonte terza non decide l'anno.
  - Il dato: data/verifiche_manuali.json, «verifiche_tolte», «caso_aperto».
  - scripts/verifica.py lo tiene fuori anche se il giro di Wikidata lo riporta. La prova 9 controlla che non sia in nessuna lista.
- **Von den Steinen (Q115085):** rientra nella lista 2027 con Wikidata 1956. L'Onassis Cavafy Archive concorda («died on Rhodes (Greece) in 1956», https://cavafy.onassis.org/creator/von-den-steinen-helmut/) e lo aggiungo come fonte trovata a mano («fonti_aggiunte»). In pagina e nel radar: «Anno di morte da Wikidata, che concorda con Onassis Cavafy Archive (fonte trovata a mano)».

## 2026-11-23 — Ritocchi vetrina 2027 e vetrina 2028 (locale, non pubblicato)
- Cosa: voci di ricerca nel blocco «vetrina-2027» (Why I am an Atheist, Gaban) e «vetrina-2028» (12 opere più viste); nota corretta per La via del ritorno (puntate 1930 già libere); bozze di nota per Il concetto di 'politico' (prima versione 1927) e The Thirteen Problems (primi sei racconti 1927-28).
- Regola (incrocio_opera): conferma Why I am an Atheist, Little House, Light in August, Cold Comfort Farm, Radetzky March; nota Concept of the Political, Thirteen Problems; da decidere Gaban (una fonte dice 1930), Céline (una sola fonte), Musil (volume 2: 1932 o 1933), Peril at End House (a puntate su Liberty nel 1931), German Ideology (prima parte 1926, una sola fonte), Death in the Afternoon (seconda fonte debole).
- Seconda lettura (altra sessione), seme 20261127, 3 voci: Morgan/Light in August trovata e confermata; PARI/Atheist e MUSE/Radetzky non verificabili (pagina caricata via script; blocco anti-robot). Nessuna smentita.
- Etichette: 2027 63/84/8 (prima 62/85/8); 2028 7/103/65 (prima 1/109/65).
- Prove 1-9: 0 errori; fotografia: 0 cambi da approvare.

## 2026-11-23 — Modifiche di Marco alla vetrina 2028 (ok alla pubblicazione)
- Carl Schmitt (Q77148) in data/fuori_classifica.json (iscritto al partito nazista nel 1933, Britannica https://www.britannica.com/print/article/2003862). Fuori dalle vetrine, resta in lista, conteggi e ricerca.
- Il filtro valeva solo per gli autori europei: aggiunta pagine.opera_in_vetrina, usata dalle pagine dell'anno (libri USA, anche titolo per Google) e dalla home (scelte e riserve, Europa e USA).
- Nuova prova 5b: nessun autore fuori classifica nelle vetrine. Sulla pagina 2028 di prima l'avrebbe trovato (Schmitt era all'11° posto); ora 0.
- In vetrina 2028 sale al 12° posto Come fu temprato l'acciaio (Ostrovskij, Q63707), «Da confermare».
- Nota Thirteen Problems riscritta con il testo di Marco; note di Schmitt e Christie approvate (la prima resta nel registro).
- Prove 1-9 e 5b: 0 errori; fotografia: 0 cambi. Etichette invariate: 2027 63/84/8, 2028 7/103/65.

## 2026-11-23 — Peril at End House: le puntate su Liberty (1931) erano il testo completo? (locale, non pubblicato)
- Fonti: The Online Books Page (UPenn), rinnovi CCE dei contributi a Liberty: 11 puntate dal 13/6 al 22/8/1931. Delicious Death: Liberty giugno-agosto 1931 e Woman's Pictorial ottobre-dicembre 1931.
- Testo completo? Solo Wikipedia (copiata da nocloo e dal wiki fandom) dice «slight abridgements», niente capitoli e una frase tolta nel cap. III. Non ho trovato una seconda fonte indipendente, né le puntate digitalizzate da confrontare.
- Regola (incrocio_opera) con le due voci nuove (blocco vetrina-2028-peril): «nota», uscita prima solo una parte. Resta nella lista 2028 con la nota, in attesa del testo approvato da Marco.

## 2026-11-23 — Nota Peril approvata; niente «Da confermare» in vetrina (ok di Marco)
- Peril at End House: nota approvata da Marco, senza l'inciso sui tagli (fonte unica).
- Come fu temprato l'acciaio (Q63707): non verificabile. Le fonti si contraddicono sull'inizio delle puntate su Molodaja gvardija: maggio 1932 (Rossijskaja Gazeta) o aprile/primavera 1934 (biblioteca NGOUNB, Radio Rossii con esperti IMLI). Inoltre seconda parte e libro intero sono del 1934. Resta «Da confermare» (blocco vetrina-2028-ostrovskij).
- Regola nuova (Marco): nessun «Da confermare» nella vetrina dei libri USA, né nelle pagine dell'anno né nella home (pagine.py, home.py); prova 5b lo controlla. Sulla pagina 2028 di prima ne avrebbe trovati 2 (Musil e Ostrovskij), sulla 2027 nessuno.
- Vetrina 2028: escono Musil (L'uomo senza qualità, volumi 1930/1932-33) e Ostrovskij; salgono Tobacco Road e Stamboul Train («Edizione confermata»). Solo 7 opere della lista 2028 sono «Verificato» (Schmitt escluso): una vetrina di soli «Verificato» non si riempie.
- Etichette 2028: 8/102/65 (Peril passa a Verificato con la nota). Prove 1-9 e 5b: 0 errori; fotografia: 0 cambi.

## 2026-11-23 — Prova a vuoto dei giri del 1° e del 7 gennaio (capodanno.yml), niente pubblicato
- Come: copia del repository in /tmp (senza collegamento a GitHub, cancellata alla fine). Orologio finto per Python (sitecustomize: date.today e datetime.now) e per node (Date finto via NODE_OPTIONS --require), così le prove 1, 3 e 3b confrontano Python e browser con la stessa data finta. Stessi passi del giro: storico/pagina.py, scripts/pagine.py, prova_regole.py, controllo_frasi.py, confronta_fotografia.py --giro; prima 1/1/2027 00:05, poi 7/1/2027 00:05 sopra il risultato del 1°.
- Orari: cron "5 23 31 12 *" = 1/1/2027 00:05 a Roma; "5 23 6 1 *" = 7/1/2027 00:05 (gennaio è sempre ora solare, UTC+1).
- Fase del sito, Python e browser uguali: 31/12 23:59 vigilia 2027; 1/1 00:05 festa 2027; 6/1 23:59 festa 2027; 7/1 00:05 conto 2028.
- 1° gennaio: prove 1-9 e 5b 0 errori, frasi imprecise 0; fotografia 9325 cambi, tutti attesi, 0 da approvare: il giro pubblicherebbe. 831 file (schede «1° gen 2027» → «libero dal 2027», conti dei giorni, sitemap, data degli .ics).
- 7 gennaio: 0 errori, fotografia 0 cambi; 840 file (menu «Pubblico dominio 2028», conto alla rovescia 2028, autori in arrivo da 251 a 125).
- Se il giro fallisce: niente ripartenza; il sito resta com'era, ma home e radar cambiano fase da soli nel browser. Avviso solo per email di GitHub a chi ha toccato per ultimo l'orario (se le notifiche sono accese); se GitHub salta il giro, nessun avviso. Rimedio a mano: pulsante «Run workflow».

## 2026-11-24 — Calo su Google: date della sitemap solo per cambi veri (locale, in attesa di ok)
- Search Console: impressioni da 275 (14/11) a 0 (21-22/11); calendario 2027 «scansionata, ma attualmente non indicizzata» (22/11); nessuna azione manuale; site: circa 10 risultati; home seconda per «public domain radar».
- Causa trovata nel codice: l'impronta che decide la data «modificata» contava il conto dei giorni (<span id="days">), le posizioni in classifica, i conteggi «Tutti i N scrittori» e l'elenco «Altri scrittori liberi». Ogni giro segnava tutte le pagine come nuove.
- Correzione (scripts/pagine.py, VOLATILE_2, versione 2 dell'impronta): queste parti non contano. Al passaggio si tiene la data già salvata.
- Prova: giro di oggi, 833 date invariate (831 al 23/11, 2 al 22/11). Giro simulato al 24/12 su una copia: schede con data nuova 0 su 418 (con la regola vecchia 416); cambiano solo le 4 pagine dell'anno (conto alla rovescia). Prove 1-9 e 5b: 0 errori.
- Le 47 pagine sparite: 4 sono rinominate e hanno già il rimando; 43 sono autori tolti dalle liste (non letterari): il 404 è la risposta giusta, nessun intervento.

## 2026-11-24 — Pagina che salta (CLS) e llms.txt (locale, in attesa di ok)
- PageSpeed (Marco, computer, calendario EN 2027): spostamento del layout 0.171, navigazione agentica 1/2 (telefono 98/2/2).
- Causa misurata (Chrome senza schermo, caratteri ritardati di 0,8 s): il titolo in Big Shoulders cambia righe quando arriva il carattere vero (il ripiego Impact/sans-serif è largo il doppio: Big Shoulders = 53% di Arial) e tutto sotto salta. Sul radar, in più, la riga sopra il titolo si riempie dopo i dati e su telefono va a capo.
- Tentativo scartato: ripiego Arial ridotto al 53-60% (size-adjust) per il titolo: cifre e lettere hanno proporzioni diverse, le righe cambiano comunque (0.07-0.35).
- Correzione: Big Shoulders con font-display optional + pre-caricamento del file 800 latino in ogni pagina; Instrument Sans con ripiego Arial al 101,6% (misurato); DM Mono non serve (99,7%). Radar: spazio fisso di due righe per la riga sopra il titolo sul telefono. Tutto in fonts.css (e nel suo generatore scarica_font.py), nelle due testate di pagine.py e nelle pagine radar.
- Misure dopo (pc / telefono, caratteri subito e in ritardo): calendario EN 0.047/0.002, calendario IT 0.001/0.001, pubblico dominio 2027 IT 0.025-0.034/0.051, EN 0.051/0.001, radar 0.002-0.025/0-0.005, home EN 0.017/0.010, scheda 0.001/0.026. Prima: fino a 0.45 (pd 2027 IT) e 0.35 (radar telefono).
- Confronto foto prima/dopo con caratteri caricati: calendario e scheda identici al pixel; radar e pagina 2027 differiscono solo per il punto dell'animazione del testo.
- Date della sitemap: impronta versione 4 (senza <style> e <link>), le 833 date restano quelle di prima.
- llms.txt nuovo alla radice: descrizione del sito, regole delle date (con le eccezioni di Spagna, Francia, Italia), pagine principali, dati scaricabili, metodo (docs/criteri.md su GitHub).
- Prove 1-9 e 5b: 0 errori.

## 2026-11-25 — Navigazione: controllo e menu del radar nell'HTML (locale, in attesa di ok)
- Controllo dei collegamenti (HTML senza programmi, come lo leggono Google e le AI): radar con menu vuoto (costruito dal programma) e 15 collegamenti; Già pubblici 12 collegamenti (contenuto dal programma); menu con «Tutti gli autori» e «Indice degli autori» simili; 334 schede su 825 raggiungibili solo dall'indice A–Z o da altre schede; «sei qui» solo sulle schede. Le pagine 2027/2028 collegano circa 135 autori ciascuna.
- Correzione dell'analisi: il calendario 2027 non ha schede da collegare (0 delle 189 voci con codice Wikidata ha una scheda: morti del 1927/1977 e nati del 1827/1877/1927).
- Fatto: il menu del radar (IT/EN) è scritto nell'HTML con le stesse voci che disegna il programma; il programma lo ridisegna uguale, quindi nessun cambio visibile. Spostamento del layout radar invariato.
- Scoperta: il riquadro delle regole con le fonti di legge (Italia, Francia, Germania, Regno Unito, Svezia, Spagna, UE) esiste solo dentro il programma del radar: Google e le AI non lo vedono. Base per le pagine paese.
- Mockup (in chat, fuori dal repository): menu per domande e pagina paese per i sei paesi, con dati delle liste (data/2027.json, 2028, es-, us-) e testi del riquadro regole.

## 25/11/2026 — Pagine paese e menu nuovo (solo in locale, non pubblicato)
- Cosa: nuovo `scripts/pagine_paese.py` (14 pagine: indice «Per paese» e 6 paesi, IT ed EN), costruite con i pezzi della pagina dell'anno; regole lette dal riquadro del radar (un posto solo); fuori classifica esclusi. Menu di tutte le pagine generate: «2027: chi diventa libero · Già pubblici · Per paese · Anniversari 2027»; radar e indice A–Z spostati nel piede.
- Prova: `pagine.py` completo, poi `prova_regole.py`: test 1–9 e 5b tutti a 0 errori. 834 file cambiati (quasi tutti per il menu).
- Ancora da fare: menu scritti a mano di radar e Già pubblici; pagine Come funziona e Shop (servono immagini e link Etsy); sitemap, CLS e foto controllati sul sito vero.

## 25/11/2026 — Come funziona, Shop, menu su radar e Già pubblici, porte in home (solo in locale)
- Cosa: pagine /come-funziona/ e /shop/ (IT/EN) in `scripts/pagine_paese.py`. Come funziona riporta solo cose scritte in docs/criteri.md e docs/giri-automatici.md. Lo Shop segue il mockup approvato in un'altra chat: due poster (Alice, Tale of Two Cities, 35 €), link Etsy nel formato publicdomainradar.etsy.com (in inglese senza «/it/»); il calendario non c'è perché manca l'inserzione.
- Menu: «2027: chi diventa libero · Già pubblici · Per paese · Anniversari 2027 · Come funziona · Shop». Nel radar la testata mostra solo 2027, Già pubblici, Per paese (con 6 voci andava a capo); tutte le voci nel menu.
- Home: 6 porte (2027, Per paese, Già pubblici, Calendario, Come funziona, Shop); la porta «Tutti gli autori» (radar) tolta, il radar resta nel piede e nei link della pagina 2027. Pagina 2027: «Chi entra, dove» porta alle pagine paese.
- Giro «stima» (.github/workflows/stima.yml): aggiunte le cartelle nuove a `git add`.
- Prova: catena completa (applica_registro_liste, applica_registro, registro_opere, pagina, pagine, stati_usa), prova_regole 1–9 e 5b a 0, confronta_fotografia: 0 cambi. Foto delle pagine a 1280 e 412 px.
- 25/11/2026, correzione chiesta da Marco: in «Come funziona» mancavano fonti. Ora l'elenco è completo come nei piedi delle pagine: Wikidata, Wikipedia (visite in 5 lingue), cataloghi nazionali (SBN, BnF, BNE, British Library, Library of Congress, GND, K10plus), Catalog of Copyright Entries (trascrizione NYPL, CC0), Duke University (CC BY 4.0), Open Library, Project Gutenberg, Wikimedia Commons, testi di legge. Il link delle fonti dice «Apri →» invece di «Leggi la norma →».

## 25/11/2026 — Controllo grafico prima di pubblicare (chiesto da Marco)
- Come è fatta la prova: pagine generate in locale e aperte in Chrome (Playwright) a 360, 412, 768, 1024, 1280 e 1600 px di larghezza, scorrendo tutta la pagina. Per ogni pagina un programma cerca: pagina che scorre di lato, elementi che escono dallo schermo, testi su più righe con interlinea più stretta di 0,84. Poi ho guardato a occhio le foto. Pagine: indice Per paese, i 6 paesi (IT ed EN), Come funziona, Shop (IT/EN), home (IT/EN), pagina 2027 (IT/EN), calendario, Già pubblici, radar, una scheda autore. Menu aperto a 360×640, 1280×720, 1600×900.
- Trovato e corretto:
  1. Pagina 2027 (già online): le note lunghe dei libri USA (es. Thirteen Problems, Peril at End House) stavano su una riga sola: la pagina scorreva di lato fino a 1.100 px sul telefono. Ora vanno a capo (classe `nota-us`, stile_anno.css).
  2. Menu a tutto schermo: con 6–7 voci su un computer con schermo basso l'ultima voce («Shop») usciva dallo schermo. Ora la grandezza tiene conto dell'altezza (stile_scheda.css e radar) e il menu scorre se serve.
  3. Come funziona: «Aprile, luglio, ottobre» e «Cataloghi delle biblioteche nazionali» venivano spezzati come «legge, articolo». Corretto.
  4. Shop: la griglia a 3 colonne lasciava un buco con 2 poster; ora si adatta al numero di poster.
  5. Indice Per paese: a 768 px andava in una colonna; ora va in una colonna solo sotto 760 px, come le porte della home.
  6. Piede di tutte le pagine e home: l'elenco delle fonti non citava Duke, Open Library, Project Gutenberg, il registro USA e i cataloghi tedeschi; ora sì, con il link a Come funziona. Il link «riquadro delle regole» del piede porta alle pagine dei paesi.
  7. Radar: voce «Anniversari 2027» come nel resto del sito.
- Controllato e lasciato com'è: interlinea dei titoli grandi uguale alla pagina 2027 già approvata (stesse misure); gli «elementi fuori schermo» rimasti sono gli scaffali che scorrono di lato apposta (Già pubblici, radar, schede, mesi del calendario).
- Dopo le correzioni: nessuna pagina scorre di lato a nessuna larghezza; prova_regole 1–9 e 5b a 0.

## 25/11/2026 — Pubblicazione della ristrutturazione e ricerca «Omero» in Già pubblici
- Pubblicati con l'ok di Marco (09:52) i 5 commit della ristrutturazione (df498c1f5 … 0213a2679); GitHub Pages: riuscito alle 09:53. Le pagine vere non si possono aprire da qui (sito non tra gli indirizzi permessi): controllo affidato a Marco.
- Segnalazione di Marco: cercando «Omero» uscivano Pseudo-Omero e titoli di altri autori (Andersen, Nietzsche, Miquel), e Omero risultava «morto nel -800, libero dal -729 / -719».
- Perché: (1) la ricerca trova anche le opere con «Omero» nel titolo, giusto, ma le opere di Omero stesso restavano chiuse dietro «Tutte le opere dell'autore» perché gli autori trovati erano due; (2) Omero ha un anno di morte su Wikidata (-800) e la pagina lo trattava come un autore qualsiasi.
- Corretto (storico/pagina.html): un autore morto prima dell'anno 1 si mostra come «autore antico, libero ovunque»; le opere del primo autore si aprono da sole se il nome è proprio quello cercato o se ha almeno 10 volte le opere del secondo (Dante Alighieri 149 contro 2), mostrando le prime 10 e un pulsante «Tutte le N opere». Provato: Omero, Dante, Homer (inglese, 390 px), Tolkien.
- 25/11/2026, decisione di Marco (screenshot Tintin in Congo): le note delle opere USA («uscito a puntate…», «a puntate fino al…») non vanno nelle classifiche delle pagine 2027 e 2028 ma solo nella scheda dell'opera del radar, che le legge già dal registro. Tolte dalle classifiche; prova 8 cambiata (ora controlla che la classifica NON ripeta la nota); regola aggiunta in docs/criteri.md. Provato: classifica 2027 con solo autore e stato; scheda radar di Tintin in Congo con la nota. prova_regole 1–9 e 5b a 0.
- 25/11/2026, decisione di Marco: nelle classifiche dei libri USA solo «Verificato». Prima: pagina 2027 11 Verificato + 1 Edizione confermata; 2028 7 + 5; pagina Stati Uniti tutti i 155 (63 + 84 + 8 Da confermare). Ora: 2027 12 Verificato; 2028 7 (sono tutti i verificati del 1932 fuori dai fuori classifica); Stati Uniti 63, con il link al radar per tutti i 155; home 3 su 3 Verificato (lo erano già). Prova 5b estesa: controlla anche «Edizione confermata» nelle righe delle classifiche e le pagine Stati Uniti. Regola in docs/criteri.md. prova_regole 1–9 e 5b a 0.

## 25/11/2026 — Regola di Marco sulle pubblicazioni
- Si pubblica a gruppi: le correzioni si fanno e si provano in locale, si annotano qui, e si pubblicano tutte insieme in un'unica volta (al massimo una al giorno), dopo aver detto a Marco cosa si carica e con il suo ok. Eccezione: errori gravi, segnalati prima a Marco. Motivo: il 25/11 il sito è stato pubblicato tre volte in un'ora.
- 25/11/2026, errore segnalato da Marco: le pagine paese (pubblicate alle 09:53) elencavano solo gli scrittori del paese (es. Italia: niente Brecht). Regola inventata da me, sbagliata: in ogni paese europeo la legge vale per autori di ogni nazionalità. Corretto in locale: prima lista «Chi diventa libero in <paese> nel 2027» con tutti gli scrittori, in ordine di visite sulla Wikipedia della lingua del paese (it, fr, de, en per il Regno Unito, es); poi «Gli scrittori <del paese>»; poi «E nel 2028» con tutti. In Francia esclusi i «morti per la Francia». Numeri in cima: prima il totale (831; Spagna 793), poi quanti sono del paese. Provato su tutte le 5 pagine europee in italiano e inglese; nessuna pagina scorre di lato; prova_regole 1–9 e 5b a 0.
- 25/11/2026, controllo chiesto da Marco: «regole inventate» nel lavoro di oggi. Ogni frase di legge delle pagine paese, Stati Uniti e Come funziona confrontata con il riquadro delle regole del radar (che ha le fonti): tutte presenti lì. Trovate e corrette 3 frasi mie senza base: (1) pagine paese, «Gli scrittori italiani — liberi ovunque in Europa dal 2027» (falso: in Spagna dal 2037) → «morti nel 1956»; (2) Come funziona: K10plus messo tra le fonti degli anni di morte (si usa solo per gli anni di uscita dei libri USA) → spostato; (3) Come funziona: «I nomi e i libri messi in evidenza hanno la data confermata» (vero solo per i libri USA, non per gli autori europei) → riscritto sui soli libri USA. Scelte mie da far approvare a Marco: radar tolto dal menu e dalle porte della home; ricerca di Già pubblici (autore «antico» se morto prima dell'anno 1; opere aperte da sole se il nome è quello cercato o se l'autore ha almeno 10 volte le opere del secondo); classifica 2028 con 7 libri invece di 12.
- 25/11/2026, decisioni di Marco: (1) niente 2028 nelle pagine che parlano del 2027: tolta la lista «E nel 2028» dalle pagine paese e il numero «libri del 1932» dalla pagina Stati Uniti (la pagina 2028 entra nei menu il 7 gennaio, come già deciso il 21/11); (2) «Home» come prima voce del menu in tutte le pagine (radar compreso). Voci del menu un po' più piccole: con 7–8 voci entrano a 360×640, 1280×720, 1600×900. prova_regole 1–9 e 5b a 0. Non pubblicato (si pubblica a gruppi).

## 25/11/2026 — Percorso semplice: «Dove pubblichi?» e un elenco solo per paese (in locale, non pubblicato)
- Perché: Marco, da visitatore, si perdeva (home → pagina 2027 → radar = tre classifiche diverse; uno spagnolo vedeva in cima autori liberi in Spagna solo nel 2037). Rapporto dell'agente UX in /tmp/ux (fuori dal repo); prova del percorso approvata da Marco («procedi»).
- Home: al posto del pulsante unico verso la pagina 2027, una tendina «Dove pubblichi?» con i 6 paesi (si chiude toccando fuori o con Esc).
- Pagine paese europee: al posto della classifica dei 12 e della lista degli scrittori del paese, un elenco solo con TUTTI gli scrittori che diventano liberi lì (Spagna 793, gli altri 831), in ordine di visite sulla Wikipedia della lingua del paese; ricerca per nome (senza accenti, a inizio parola), filtro «Solo <del paese>», «Scarica Excel» (CSV), primi 30 e «Mostra tutti». Frase della regola in cima (Spagna: solo per chi è morto prima del 7/12/1987; Francia: esclusi i «morti per la Francia»). Gli autori fuori classifica restano nell'elenco completo e nei conteggi, come nel radar (regola di opera_in_vetrina).
- Corretti anche: home «109 con l'anno confermato» → «63 verificati» (stesso numero delle pagine 2027 e Stati Uniti); filtro «Libero dal 1° gennaio 2028» tolto dall'indice degli autori; llms.txt senza le pagine 2028 e con Per paese e Come funziona.
- Prove: catena completa, prova_regole 1–9 e 5b a 0, controllo_pagine 0 errori, fotografia 0 cambi; tendina e elenchi provati a 360, 768 e 1440 px in IT ed EN (6 voci, nessuna pagina che scorre di lato, 793/831 righe, ricerca «Gerhart Hauptmann», «marquina», «leautaud», Excel scaricato con 794/832 righe).
- Non ancora fatto: pagina 2027 e radar restano come sono (da ridirigere in un secondo passo); pagina Stati Uniti invariata (63 verificati).
- 25/11/2026, richiesta di Marco («il breakdown deve essere uguale al radar quando si seleziona la nazione»): le 5 pagine paese europee (IT/EN) ora si costruiscono dal file del radar (scripts/pagine_paese.py, pagina_paese_radar) con il paese fisso (window.PAESE_FISSO): classifica con «paese / fama nel mondo / da scoprire» e spiegazione, nomi più grandi, scaffali delle opere per genere, paese d'origine e lingua, «I miei», elenco completo con tutti i filtri ed Excel; testata con il menu del sito e il link alla lingua gemella; sotto regola di legge, cosa significa, domande (aperte/chiuse senza programma), altri paesi. Per motori di ricerca e AI i primi 12 nomi sono già scritti nella pagina. Nel radar: guardie per PAESE_FISSO (lingua dall'indirizzo, paese che non si salva, menu del sito), fonti complete nel piede, «Tutti i {n}» → «Elenco completo: {n}». Prove: 10 pagine a 360 e 1440 px senza errori del programma né scorrimento laterale; paese giusto in ogni pagina; scheda autore che si apre dentro la pagina paese; prova_regole 1–9 e 5b a 0; controllo_pagine 0 errori. La pagina Stati Uniti resta quella dei 63 verificati.
- Da guardare (non toccato): nello scaffale «Le più note» della Spagna compare «Mein Kampf» con James Vincent Murphy (il traduttore, morto nel 1946) come autore.
- 25/11/2026, errore grave segnalato da Marco (12:08): nelle pagine paese pubblicate alle 11:55, sul computer, MENU non c'era. Causa: il radar nasconde MENU sopra i 860 px perché lì mostra la barra delle voci, che nelle pagine paese ho nascosto. Corretto (CSS_LEGGE: MENU sempre visibile). Provato a 1440, 1024, 768 e 390 px in IT ed EN: MENU visibile, si apre, 7 voci. Il mio controllo grafico di stamattina guardava le pagine solo sul telefono dopo la trasformazione: errore di metodo, da ora le prove delle pagine nuove includono sempre il computer e il menu aperto.

## 25/11/2026 — Secondo passo: radar e pagina 2027 portano alle pagine paese; ritratti; Shop (in locale)
- Radar: chi lo apre senza una scheda (/radar/, #/2027, #/regole-paesi) va a «Per paese»; #/us/… va alla pagina Stati Uniti; restano solo le schede (#/autore/, #/opera/, #/genere/), che si aprono come prima. Indirizzo canonico del radar → /pubblico-dominio/ (EN /en/public-domain/), «noindex,follow», tolto dalla mappa del sito. Le pagine paese, costruite dal radar, tolgono il rimando e il noindex.
- Pagina 2027: tendina «Dove pubblichi?» sotto la frase d'apertura (la stessa della home: pagine_paese.tendina_html, un posto solo); «Tutti gli 831 nel radar» → «Tutti gli 831, paese per paese» (/pubblico-dominio/); «Tutti i 155 libri» → pagina Stati Uniti; numeri in cima verso le pagine paese.
- Schede autore: «Apri nel radar» → «Tutti gli scrittori liberi in Italia/Spagna» e «Gli altri paesi» (per gli autori dell'anno in vetrina); «Le regole, paese per paese» → /pubblico-dominio/. Piede: tolta la voce «Tutti gli autori (radar)».
- Ritratti (segnalazione di Marco: Walter de la Mare tagliato al busto): il riquadro tagliava al centro della foto; ora dall'alto (object-position 50% 18%) in pagina dell'anno, schede, radar e pagine paese. Non verificabile qui con le foto vere (Wikimedia non raggiungibile da questa macchina): da controllare sul sito.
- Shop: errore del programma della pagina (mancava id="say") corretto.
- Prove: rimandi del radar (6 casi), schede che si aprono, link e tendina della pagina 2027, schede autore; 14 pagine a 390 e 1440 px: MENU visibile, nessun errore del programma, nessuno scorrimento laterale; prova_regole 1–9 e 5b a 0; controllo_pagine 0; fotografia 0 cambi.

## 25/11/2026 — Contenuti nazisti fuori da tutte le vetrine; pagina Stati Uniti «solo verificati, con possibilità di ampliare» (in locale)
- Segnalazione di Marco: nello scaffale «Le più note» della pagina Spagna c'era «Mein Kampf» (attribuito a James Vincent Murphy, traduttore, morto nel 1946). Perché era successo: l'elenco delle opere escluse (data/storico_esclusioni.json, con Mein Kampf e i Protocolli dal 20–21/11) valeva solo per Già pubblici; le liste degli autori, da cui leggono radar e pagine paese, non lo usavano, e lì le opere non hanno il codice Wikidata.
- Corretto in un posto solo: regole.opere_escluse / regole.opera_esclusa (per codice e per titolo esatto, anche tradotto; titoli aggiunti al file); applicata alle liste da scripts/applica_registro_liste.py (tolto «Mein Kampf» dalle opere di Murphy in es-2027) e alle vetrine USA (pagine.opera_in_vetrina). Murphy in data/fuori_classifica.json (fonte: Wikipedia inglese). La sua scheda autore non c'è più (senza opere non si crea). Nuova prova 5c: nessuna opera esclusa negli elenchi delle liste né nelle pagine con le vetrine (2221 opere controllate, 0). Regola scritta in docs/criteri.md.
- Pagina Stati Uniti (decisione di Marco): in classifica i 63 verificati; sotto, il pulsante «Mostra anche gli altri 92: 84 con l'edizione confermata, 8 da confermare», che apre l'elenco con lo stato di ognuno e una frase che spiega che non sono verificati. Provato: 63 visibili, 155 dopo il pulsante.
- Prove: catena completa, prova_regole 1–9, 5b e 5c a 0, controllo_pagine 0, fotografia 0 cambi; pagina Spagna senza Mein Kampf; scaffali di Già pubblici senza Mein Kampf e Protocolli.
- 25/11/2026, tre ritocchi per Google (controllo delle basi SEO sulle pagine principali): (1) titolo della pagina «Per paese» accorciato da 123 a 58 caratteri («Pubblico dominio per paese: le regole · Public Domain Radar»); (2) radar con un segnale solo: «noindex,follow» e indirizzo ufficiale di sé stesso (prima indicava anche «Per paese» come pagina giusta: segnali in conflitto); (3) scheda di James Vincent Murphy tolta: al vecchio indirizzo una pagina di rimando (noindex) verso la pagina Spagna, invece di «pagina non trovata» (data/schede_tolte.json, scritta da pagine.py a ogni giro). prova_regole 1–9, 5b, 5c a 0; controllo_pagine 0.
- 25/11/2026, segnalazione di Marco (pagina Stati Uniti, riquadro con «HL» al posto della foto di Lovecraft): la pagina cercava la foto dell'opera, che nei dati non c'è. Ora usa il ritratto del primo autore che ne ha uno, come la pagina dell'anno (138 righe su 155 con ritratto; le altre mostrano le iniziali perché l'autore non ha foto libera), con i crediti delle licenze di Wikimedia Commons sotto l'elenco. Provato a 390 e 1440 px: nessun errore, nessuno scorrimento laterale, 63 righe visibili. prova_regole a 0.
- 25/11/2026, tre ritocchi grafici chiesti da Marco: (1) crediti delle foto chiusi dietro «Crediti delle foto (N) +» (si aprono toccando) in pagina dell'anno, pagina Stati Uniti, pagine paese e radar (pagine.crediti_foto e radar: un disegno solo; allineati al titolo della sezione: 48 px sul computer, 20 sul telefono); (2) titolo della home (frontespizio) con interlinea 1,04 invece di 0,92: le lettere di righe vicine si toccavano («Courage and / Her Children»); (3) pulsante «Mostra anche gli altri 92» della pagina Stati Uniti con lo stesso carattere e la stessa misura dei link «→» del sito. prova_regole a 0.
- 25/11/2026, Shop: aggiunti i due poster della serie «Distant Reading» (Wuthering Heights «I am Heathcliff!», White Nights «A whole moment of happiness!») dai PDF di Marco, trasformati in immagini per il sito (900 px, webp; tolti i 3 mm di abbondanza dal PDF di Brontë) con i link Etsy che ha dato. Prezzo 35 € (confermato da Marco). Frase d'apertura e passo 01 aggiornati alla serie; griglia a 4 colonne sul computer, 2 sul tablet, 1 sul telefono; pulsanti «Acquista su Etsy» alla stessa altezza. Nessuno scorrimento laterale a 1440, 1024, 768, 390 px.
- 25/11/2026, errore grafico segnalato da Marco: nello Shop i numeri 01/02/03 di «Come si compra» toccavano la linea (0 px). C'era dalla prima versione dello Shop di stamattina: i miei controlli guardavano scorrimento laterale, menu ed errori, non la distanza tra la linea di sezione e il contenuto. Corretto (.how a 34 px dalla linea, come «Cosa significa davvero»). Nuovo controllo scripts/controllo_spazi.py: misura su 13 pagine, a 390 e 1440 px, la distanza linea–contenuto di ogni sezione; unica sotto i 12 px era questa. Le altre segnalate (12–16 px: «Le risposte brevi», «Chi entra, dove», scaffali di Già pubblici, classifica delle pagine paese) sono il disegno già approvato delle pagine 2027, Già pubblici e radar, lasciate come sono. Da ora il controllo fa parte delle prove grafiche prima di ogni pubblicazione.

## 25/11/2026 — Visite di Già pubblici corrette; «Poster disponibile» sulle opere dei poster (in locale)
- Errore trovato: 1.572 opere avevano lo stesso numero di visite in tutte e 5 le lingue (Faust I: 206.578). Causa: le opere aggiunte dagli scaffali per lingua (storico/scaffali_lingua.py) portano la visita MENSILE sulla Wikipedia della lingua originale; storico/pagina.py la copiava in tutte e 5 le lingue delle visite settimanali. Salivano in cima alle classifiche (in Italia: «Una notte sul treno della Via Lattea», «Dogra Magra»). Corretto in storico/pagina.py: per quelle opere niente visite per le classifiche; il loro scaffale di lingua le ordina comunque col suo numero. Dopo: 1 sola opera con valori uguali (vera); prime in Italia Jane Eyre, Odissea, Moby Dick, Divina Commedia.
- Poster: elenco unico in data/poster.json (codice dell'opera su Wikidata, inserzione Etsy, frase, serie). Lo legge lo Shop (scripts/pagine_paese.py) e Già pubblici: nella riga dell'opera «Poster disponibile», nella scheda dell'opera il link «Poster disponibile su Etsy ↗» con la frase e la serie. Codici: Alice Q92640, Tale of Two Cities Q308918, Wuthering Heights Q202975, White Nights Q600461.
- Prove: catena completa, prova_regole 1–9, 5b e 5c a 0, controllo_pagine 0, fotografia 0 cambi; Shop 4 poster; Cime tempestose a 1440 e 390 px: riga e scheda giuste, link Etsy /it/, nessuno scorrimento laterale, nessun errore. controllo_spazi: stessi avvisi (12–16 px) del sito pubblicato, nessuno nuovo.
- Lista candidati poster (idea 2): opere libere in UE, Spagna, Regno Unito e USA (uscite entro il 1930, autori morti entro il 1945), ordinate per visite settimanali nelle 5 Wikipedia; anni di uscita controllati su Wikipedia e altre fonti per le prime 15. File consegnato a Marco in chat, non nel sito.

## 25/11/2026 — Analisi SEO esterna: gruppo A (ritocchi invisibili) e gruppo B (elenco autori nelle pagine paese), in locale
- A1. Home: il titolo dell'opera che cambia non è più un h1 (resta identico a video, ora è un paragrafo); h1 vero nascosto «Public Domain Radar: chi diventa libero, e quando» (classe .vh, scripts/home.py).
- A2. Titoli su due righe (pagine 2027/2028, paesi, Come funziona, calendario, schede autore): spazio prima di <br>, Google leggeva «Cosa diventalibero».
- A3. 404.html del sito (stile RDR, porte principali, link all'inglese, noindex) e favicon.ico (16/32/48 px dal favicon.svg).
- A4. /calendario/ e /en/calendar/ portano al 2027; nel calendario il 1° gennaio punta alle pagine 2027 e Stati Uniti invece che al radar.
- A5. llms.txt: tolto il radar, aggiunto lo Shop. A6. Titoli oltre i 60 caratteri: tolto « · Public Domain Radar» in fondo (pagine.titolo_corto, una regola sola). A7. Dati per Google: Organization (con Marco e LinkedIn) in home; i 4 poster come Product/Offer (35 EUR, MadeToOrder) nello Shop.
- Non fatto, con motivo: link alle schede autore nel calendario (0 persone del calendario su 229 hanno una scheda); 2028 in home e menu (regola di Marco: il 2028 si fa nel 2027); Event con noi come organizzatori (falso).
- B. Pagine paese: l'elenco completo (831 autori; 793 in Spagna) scritto nella pagina, righe nascoste finché il programma non le sostituisce; il programma del radar ora tiene tutti i nomi nella pagina (oltre i primi 40 nascosti) e chi ha la scheda ha un vero link (126 in Italia). Senza JavaScript l'elenco si vede intero. Pagina Italia da 214 a 299 KB.
- Prove: catena completa, prova_regole 1–9, 5b, 5c a 0; controllo_pagine 0; fotografia 0 cambi; controllo_spazi: stessi avvisi di prima, nessuno nuovo. Italia, Spagna EN, Francia a 1440 e 390 px: 40 righe visibili come prima, «Mostra altri» 160, ricerca giusta, clic sul nome apre la scheda nella finestra, nessuno scorrimento laterale, nessun errore; senza JavaScript 831 righe visibili. Home con un solo h1; 404 su computer e telefono.
- 25/11/2026, correzione dopo Marco («Promessi sposi, Manzoni, Machiavelli»): avevo contato solo le schede /autore/ (che esistono solo per chi si libera nel 2027–2028) e scritto «niente da collegare». Sbagliato: quelle persone e opere sono in Già pubblici. Ora nel calendario 69 voci su 231 (IT e EN) hanno l'azione «Dove è già libero →», che apre Già pubblici con la ricerca già fatta (scripts/calendario.py, cerca_gia_pubblici; dati da data/storico/pagina.json). Prova: tutti i 69 link IT e 69 EN aprono Già pubblici con almeno un risultato (controllo: una ricerca senza senso dà 0); Machiavelli 11 risultati, I promessi sposi 2; pannello giusto su computer e telefono, nessun errore. Manzoni non è nel calendario 2027 come persona (c'è il suo romanzo, 200 anni dalla prima edizione).
- 25/11/2026, punto 1 (decisione di Marco): l'opera più cercata nel titolo della scheda autore, per 23 autori del 2027 (46 pagine IT ed EN): «A. A. Milne e «Winnie Puh»: quando entrano in pubblico dominio». Elenco scelto a mano in data/opera_nel_titolo.json tra le opere principali di ciascuno (la prima di Wikidata non sempre è la più nota: Calamandrei aveva una lapide, Seton un manuale di ornitologia); esclusi gli autori senza un'opera letteraria nota tra le principali e Thomas Dixon Jr. (prima opera: il romanzo del Ku Klux Klan). Cambia solo il titolo per Google e la scheda del browser; la pagina a video resta uguale. Prove: catena, prova_regole tutte a 0, controllo_pagine 0, fotografia 0 cambi; 46 titoli su 46 controllati.
- 26/11/2026: il ramo «cursor/hreflang-x-default-inglese» (x-default verso l'inglese + barra «This page is available in English») era stato rimesso sopra il sito e provato in locale (tutto a 0), ma Marco ha deciso di non pubblicarlo («che senso ha?»): gli stranieri arrivano già sulle pagine inglesi e il tasto EN c'è sempre. Modifiche tolte, sito locale riportato alla versione pubblicata (e203eb6c6). Il ramo resta su GitHub, non unito.

## 26/11/2026 — Riordino delle lingue, passo 1 (decisione di Marco: «in modo pianificato e sicuro»)
- Metodo: quello di gettext (lo standard dei siti multilingue). Nuovo scripts/lingue.py: ogni testo fisso è una coppia italiano/inglese con segnaposti tra graffe per le parti che cambiano; per italiano e inglese esce il testo scritto nel codice; per le altre lingue il testo inglese fa da chiave in testi/<lingua>.json (vuoto o assente = esce l'inglese e il testo finisce in testi/mancanti-<lingua>.json).
- Conversione automatica (script verificato, non a mano) di scripts/pagine.py e scripts/pagine_paese.py: 23 definizioni della funzione T → traduttore(lang); i testi con parti variabili (f-string) → modelli con segnaposti; 21 scelte «"testo" if it else "text"» → testo_l(...); 2 testi fatti di pezzi incollati sistemati a mano. Restano come sono, perché non sono testi ma indirizzi o dati: circa 57 scelte su URL (/autore/ ↔ /en/author/), campi (titolo ↔ titolo_en), nomi dei paesi da tabella. Per una lingua nuova questi scelgono l'inglese, cioè le pagine tedesche collegheranno le schede inglesi: da decidere nel passo 2.
- Già divisi per lingua nei loro file (una lingua nuova = un blocco in più): home (scripts/home.py), calendario (scripts/calendario.py), radar (radar/index.html, TESTI: 112 + 23 voci), Già pubblici (storico/pagina.html).
- scripts/testi_da_tradurre.py: 392 testi fissi nei programmi delle pagine; con radar, Già pubblici, home e calendario si arriva intorno ai 650 stimati.
- Garanzia: fotografia di tutte le 868 pagine generate prima del cambio, poi catena completa con il codice nuovo: 868 su 868 identiche carattere per carattere. prova_regole tutte a 0, controllo_pagine 0, fotografia dati 0 cambi. Prova del meccanismo con un testo tedesco di esempio: traduzione usata, testo mancante → inglese e segnalato. Non si ripubblicano pagine (sono identiche): cambia solo il codice.

## 26/11/2026 — Sito in tedesco, passo 2 (in locale, da mostrare a Marco prima di pubblicare)
- Dati: scripts/bio_lingue.py sul giro GitHub (run 45798553147, 22 minuti, riuscito) → data/lingue_extra.json per i 415 autori con scheda. Biografie da Wikipedia: tedesco 205, francese 227, spagnolo 179. Descrizioni brevi da Wikidata: 305 / 326 / 276. Titoli delle opere nella lingua (etichette Wikidata): 213 / 260 / 178.
- Pagine tedesche nuove: home /de/, pagina dell'anno /de/gemeinfrei-2027/, indice dei paesi /de/gemeinfrei/, Germania /de/gemeinfrei/deutschland/, 205 schede /de/autor/<nome>/ (solo chi ha la biografia sulla Wikipedia tedesca; gli altri restano in inglese). Già pubblici, calendario, Come funziona, Shop e gli altri paesi restano in inglese, con «auf Englisch» dove serve.
- La Germania in tedesco usa la versione della pagina paese senza radar (elenco completo con ricerca, «Nur deutsche», Excel, regola di legge, domande): il radar è scritto solo in italiano e inglese. Stesso contenuto, meno animazioni.
- Testi: testi/de.json, 434 traduzioni (le 392 frasi dei programmi + titoli, domande della pagina dell'anno, 32 note sulle opere USA, frasi della scheda). Testi senza traduzione alla fine: 0 (testi/mancanti-de.json vuoto). Forma di cortesia: «Sie» ovunque (la home diceva «deinen Kalender», corretto).
- Pagine italiane e inglesi: confronto con la fotografia di stamattina. Cambiano solo le pagine che esistono anche in tedesco (home, 2027, indice paesi, Germania, le 205 schede): in più il tasto IT · EN · DE e la riga hreflang «de». Tutto il resto identico, a parte il numero dei giorni.
- Prove: prova_regole tutte a 0; controllo_pagine 0 errori; fotografia 0 cambi; controllo_spazi stessi 10 avvisi di prima; link interni di 217 pagine (tutte le tedesche + le italiane e inglesi toccate): 0 rotti; ricerca di frasi inglesi rimaste nelle pagine tedesche: restano solo titoli originali inglesi (corretto).
- Grafica: home, 2027, indice, Germania, Brecht, Milne a 1440 e 390 px, tasto lingua aperto e menu aperto sul telefono. Errore trovato e corretto: sul telefono «DEUTSCHLAND» usciva dallo schermo; nelle pagine tedesche il titolone sul telefono è un po' più piccolo (scripts/lingue.py, CSS_LINGUA).

## 26/11/2026 — Tutto il sito in tedesco (decisione di Marco: «voglio questo sito in francese, tedesco e spagnolo»), in locale
- Pagine tedesche: home, pagine dell'anno 2027 e 2028, indice dei paesi e tutti e sei i paesi (con il radar tradotto, come in italiano), So funktioniert es, Shop, Schon gemeinfrei (Già pubblici), Kalender 2027 (con .ics e .csv), radar, indice degli autori, 205 schede. Tasto IT · EN · DE su tutte le pagine che hanno la versione tedesca.
- Radar e Già pubblici: il programma ora funziona in qualunque lingua; in italiano e inglese il testo mostrato è identico a prima (prova: testo delle pagine Italia, Francia EN, Regno Unito EN con scheda autore aperta, Stati Uniti, Già pubblici IT/EN con ricerca, prima e dopo: identico, tranne il tasto lingua).
- Dati nuovi (giri GitHub 45806410047 e 45807106803, con l'ok di Marco): data/lingue_etichette.json (titoli, descrizioni e pagine Wikipedia de/fr/es per 12.119 codici Wikidata: opere e autori di Già pubblici, autori delle liste, voci del calendario; paese, genere e lingua delle voci del calendario) e data/etichette_de/fr/es.json (nomi di paesi e lingue).
- Traduzioni tedesche in testi/de.json: 1.010. Testi senza traduzione: 0 (mancanti-de.json e mancanti-de-gia.json vuoti).
- Prove: prova_regole a 0, controllo_pagine 0, fotografia 0 cambi, 220 pagine tedesche senza collegamenti rotti, nessun testo italiano nelle pagine tedesche (ricerca sul testo mostrato), inglese solo nei titoli originali.
- Resta da decidere con Marco: 210 autori hanno la scheda in inglese ma non la biografia sulla Wikipedia tedesca; dalle pagine tedesche portano alla scheda inglese.

## 26/11/2026 — Francese e spagnolo (decisione di Marco), in locale
- Tutto il sito anche in francese (/fr/) e spagnolo (/es/), con lo stesso metodo del tedesco: stesse pagine (home, anni 2027 e 2028, sei paesi con il radar, Déjà libres / Ya libres, calendario con .ics e .csv, Comment ça marche / Cómo funciona, Boutique / Tienda, radar, indice degli autori, schede). Schede: 227 in francese, 179 in spagnolo (solo dove c'è la biografia sulla Wikipedia della lingua; per gli altri il collegamento resta alla scheda inglese, come deciso da Marco per il tedesco).
- Traduzioni: testi/fr.json e testi/es.json, 1.017 testi ciascuno, segnaposti controllati uno per uno (0 differenze). Date con il paese sempre indicato («en Italie, en France, en Allemagne et au Royaume-Uni», «en Italia, Francia, Alemania y el Reino Unido»); formati di data della lingua (1er janvier 2027, 1 de enero de 2027); spazi insecabili francesi prima di : ; ? ! e dentro « ».
- Regole uniche per lingua in scripts/lingue.py: date lunghe e brevi, mesi, elenchi di paesi, congiunzioni.
- Prove: testi senza traduzione 0 in tutte e tre le lingue; collegamenti rotti 0 (de 221, fr 243, es 195 pagine); prova_regole a 0; controllo_pagine 0; fotografia 0 cambi; controllo_spazi stessi 10 avvisi; pagine italiane e inglesi: testo identico, cambiano solo i tasti FR ed ES del selettore.
- Corretti durante le prove: «EST-CE DÉJÀ LIBRE / ?» (punto di domanda a capo, risolto con lo spazio insecabile); «Home» nel percorso in alto delle pagine paese ora tradotto (Start, Accueil, Inicio).

## 26/11/2026 — Testi scritti direttamente nella lingua e rilettura (idea di Marco), in locale
- Metodo: tre agenti separati, uno per lingua, con le istruzioni scritte nella lingua (tedesco, francese, spagnolo), senza vedere le mie traduzioni per la parte «vetrina». Compito 1: riscrivere da zero 125 testi di vetrina (titoli e descrizioni per Google, titoloni, frasi d'apertura, menu, home) con le parole che la gente cerca nel paese, stesso contenuto, segnaposti e HTML identici, data sempre col paese, titoli entro ~60 caratteri. Compito 2: rileggere le 1.014 traduzioni come un redattore del posto e segnalare solo errori o frasi che suonano tradotte, con gravità. File di lavoro conservati in docs/registro/rilettura-<lingua>-*.json.
- Segnalazioni: tedesco 136 (7 gravi, 48 medie, 81 lievi, di cui ~45 virgolette «» → „“), francese 103 (2 gravi, 54 medie, 47 lievi), spagnolo 34 (1 grave, 18 medie, 15 lievi). Tutte applicate dopo il controllo automatico dei segnaposti (0 scartate).
- Errori gravi trovati: titolone di Già pubblici composto male nelle tre lingue («¿Es ya libre libre?», «Est-ce libre déjà libre ?»); in tedesco numeri attaccati («Die 312 1956 gestorbenen Autoren») e frasi rotte (doppio «für»); in francese «1e» al posto di «1er» nelle classifiche.
- Effetto collaterale trovato e corretto: le nuove frasi d'apertura francese e spagnola non contenevano più il pezzo che la pagina Spagna completa con «per chi è morto prima del 7 dicembre 1987»; testi 304/305 aggiornati e aggiunto un controllo che ferma la generazione se in futuro non combaciano più.
- Prove: testi mancanti 0; link rotti 0 nelle tre lingue; prova_regole a 0; controllo_pagine 0; fotografia 0 cambi; pagine italiane e inglesi: testo identico a prima.

## 26/11/2026 — Home principale in inglese (decisione di Marco)
- publicdomainradar.com/ ora è la home inglese; l'italiana è su /it/; /en/ rimanda a / (con l'eventuale # dietro). Tutte le altre pagine tengono il loro indirizzo.
- Per Google la versione di partenza (x-default) è ora l'inglese su home, pagine paese e Già pubblici.
- Collegamenti alla home: una passata sola alla fine della generazione (scripts/lingue.py, sistema_home): nelle pagine italiane i collegamenti alla home vanno a /it/, ovunque /en/ diventa /. Le righe hreflang e canonical non si toccano. Chiamata da scripts/pagine.py e da storico/pagina.py (che gira anche da sola sul server).
- Niente avviso nella lingua del browser (Marco: non serve).
- prova_regole aggiornata ai nuovi percorsi delle due home (punti 5 e 8): 245 confronti come prima, tutto a 0. controllo_pagine 0, fotografia 0 cambi, link rotti in tutto il sito 0.

## 26/11/2026 — Già pubblici: titoli di altri autori separati (segnalazione di Marco)
- Problema: cercando Dostoevskij e aprendo le sue opere, sotto comparivano «Dostoevskij e il parricidio» (Freud) e «L. Tolstoj e Dostoevskij» (Merežkovskij), che sembravano sue. Non erano nei dati dell'autore: erano i titoli che contengono la parola cercata, messi subito dopo senza separazione.
- Correzione (storico/pagina.html): quando la ricerca trova un autore, i titoli di altri autori vanno in una parte a sé, «Altri titoli che contengono «…»» con la riga «Opere di altri autori: il nome compare solo nel titolo»; le opere dell'autore trovato non si ripetono lì. Testi in tutte e cinque le lingue.
- Prova: ricerca «Dostoevskij» in locale: le 40 opere dell'autore, poi la parte separata con il libro di Freud. prova_regole e controllo_pagine a 0.

## 26/11/2026 — Prova Thema, passo 1: raccolta dei testi con fonte (ok di Marco)
- Scopo: capire quanto bene l'AI assegna i codici Thema (EDItEUR, gratuito; scartato BISAC perché la lista completa richiede licenza per i database) leggendo solo testi con fonte. Regola di Marco: mai inventare; se l'AI non è sicura decide lui.
- Campione fisso: docs/stima-sito/prova-thema/campione.json, 200 opere su 54.509 (seme 20261126): 100 con voce Wikipedia in almeno 20 lingue, 100 meno note.
- Raccolta (scripts/prova_thema.py, giro .github/workflows/prova-thema.yml, parte da docs/registro/passo-thema.txt): descrizioni Wikidata it/en, genere/argomento/luogo/periodo/forma Wikidata, inizio voce Wikipedia it/en con indirizzo; lista Thema en/it da EDItEUR. Solo italiano e inglese, per decisione di Marco: prima si misura la bravura dell'AI; i nomi Thema nelle lingue del sito (de/fr/es) vengono dopo.
- Il giro scrive solo docs/stima-sito/prova-thema/: sito e pagine invariati. La correzione Dostoevskij resta fuori da questo invio.

## 26/11/2026 — Prova Thema, passo 2: classificazione delle 200 opere (AI) e pagina di controllo per Marco
- Raccolta (giro GitHub, 2 min): 138/200 con inizio voce Wikipedia it/en, 104 con genere Wikidata, 80 con argomento/luogo/periodo, 54 con sola descrizione breve Wikidata, 1 senza nulla. Lista Thema scaricata: v1.7 del 20/10/2026 (9.448 codici), en e it.
- Classificazione fatta da Claude in sessione (nessun credito a parte), file in docs/stima-sito/prova-thema/classificazione/ (lotto1-3.py). Regola: ogni codice ha una frase copiata dalla fonte; se la fonte non basta, l'opera va «da decidere» o «nessun testo».
- Controllo automatico (verifica.py): ogni codice deve esistere nella lista Thema e ogni frase deve comparire identica nella fonte. Al primo giro ha fermato 2 codici inesistenti (Calcutta, Amburgo: codici scritti a memoria e sbagliati) e 3 frasi non identiche. Rilettura mia: tolti o spostati tra le alternative 8 codici che erano mie deduzioni (es. periodo storico non scritto nella fonte, nazionalità dell'autore usata come luogo). Esito finale: 0 errori.
- Risultato: 155 sicure, 30 da decidere, 15 nessun testo. Famose: 89 sicure, 11 da decidere. Meno note: 66 sicure, 19 da decidere, 15 senza testo. In media 2,3 codici per opera sicura.
- Limite noto: il controllo automatico non vede una frase vera che però non giustifica il codice. Questo lo misura solo la revisione di Marco.
- Pagina di controllo (artifact privato «Prova Thema»): schede delle 200 opere con frasi evidenziate e fonti; le decisioni di Marco si salvano nel database dell'artifact (collezione «decisioni»). Niente sul sito, niente nel repository oltre a questi file di prova (ancora da inviare).
- Regola nuova di Marco (26/11/2026): codici per bambini (Y*) solo se la fonte dice chiaramente che è per bambini sotto i 12 anni; altrimenti codici per adulti. Scritta in docs/stima-sito/prova-thema/regole-classificazione.md. Applicata: Senza famiglia diventa sicura senza l'alternativa per ragazzi; tolte le alternative per bambini da L'acciarino magico e Jabberwocky; «A Visit from St. Nicholas» e «The Frost King» passano a «da decidere» (solo Wikidata le dice per l'infanzia). Restano Y*: Il piccolo Lord («children's novel» in Wikipedia) e l'alternativa per ragazzi di Tintin («supplemento per ragazzi»).
- Regola nuova di Marco (26/11/2026): si usano tutti i codici sostenuti dalle fonti, senza scegliere tra loro (Thema è additivo). Applicata: diventano sicure De ceremoniis, Skáldskaparmál (aggiunto DSC), Ad extirpanda, Běncǎo Gāngmù, Il giardino dei supplizi (aggiunto FP da «erotica» di Wikidata). Ora: 159 sicure, 26 da decidere, 15 nessun testo. Le decisioni già salvate da Marco non cambiano.

## 26/11/2026 sera — Prova Thema, passo 3: prime 42 decisioni di Marco
- Sicure controllate: 12, tutte confermate senza cambiare nulla (tutte tra le famose).
- Da decidere: 30 risolte. 22 con i codici proposti così com'erano, 8 scegliendo tra le alternative proposte, 2 lasciate senza codice. Nessun codice aggiunto da fuori.
- Su 4 opere (Winckelmann, Stopes, penny blood, Gartenlaube sul pubblico) Marco ha scelto alternative che si basavano solo sul titolo: decisione sua, l'AI da sola per regola non le avrebbe messe.
- Note di Marco diventate regole 6-8 in regole-classificazione.md. Da chiarire: su Re Giovanni ha confermato il periodo XII-XIII secolo, che era una deduzione mia, ma la nota dice «se non c'è il dato non mettiamo nulla».
- Ancora da controllare: 147 sicure (tutte le 66 meno note) e le 15 senza testo.

## 26/11/2026 sera — Prova Thema, passo 4: fonti in più per le opere difficili (ok di Marco)
- Perché: Marco ha notato che «Jules César» (traduzione francese del 1872) risultava «meno nota» e senza testo: su Wikidata le edizioni e le traduzioni hanno una scheda a parte, senza Wikipedia. Proposta di Marco: incrociare le opere difficili con altre fonti.
- Come (scripts/prova_thema2.py, giro .github/workflows/prova-thema2.yml): per 106 opere (da decidere, senza testo, sicure meno note) si seguono solo i collegamenti dichiarati da Wikidata, niente ricerca per titolo (lezione della prova autori del 18/11: per titolo si trovano libri sbagliati): «edizione di» verso l'opera originale; Gutenberg (argomenti Library of Congress); Open Library; biblioteca nazionale tedesca (GND, via lobid.org); Wikisource tedesca (categorie, per gli articoli della Gartenlaube).
- Poi riclassificazione con le stesse regole (regole-classificazione.md) e confronto con il giro 1. Sito invariato.
- **Esito raccolta (2 min):** su 106 opere, 35 con almeno una fonte nuova. Edizioni ricondotte all'originale 7 (4 con Wikipedia dell'originale), Open Library 12, Wikisource tedesca 13, GND 9, Gutenberg 0 (nessuna delle 106 aveva il numero Gutenberg su Wikidata, o il sito non ha risposto: da verificare prima del giro completo).
- **Qualità per fonte:** l'originale dell'edizione è la fonte migliore (Jules César, La Foire aux vanités, Les Natchez classificate per intero). Wikisource tedesca è utile per gli articoli della Gartenlaube (necrologio, racconto, poesia, biografia) e ha corretto un mio errore: «Des Agha's Erzählung» è un racconto, non un articolo. Open Library aiuta ma è sporca: mescola le edizioni (su Re Giovanni anche «Fiction, westerns» e «Montana»), quindi solo come conferma. GND: le categorie riguardano quasi sempre l'autore, non l'opera; utile solo il campo argomento (es. Immacolata Concezione).
- **Riclassificazione (lotto4.py, 16 opere):** da 159/26/15 a 168 sicure, 23 da decidere, 9 senza testo. Meno note: da 66 a 73 sicure, senza testo da 15 a 9. Re Giovanni: il periodo ora ha una fonte. Tre deduzioni mie (Stoccarda dal titolo, Parigi, mitologia celtica) spostate tra le alternative. Controllo automatico: 0 errori.

## 26/11/2026 sera — Già pubblici: tolte le pagine tecniche dei wiki (decisione di Marco)
- Nella prova Thema è uscita «Template:Brongniart, 1828»: su Wikidata alcune schede hanno come nome il modello di Wikispecies usato per citare un libro, e finivano nel catalogo come opere. Marco: «togli quella cosa».
- Regola in un posto solo (scripts/registro.py, non_e_un_opera): un titolo che inizia con un prefisso tecnico dei wiki (Template:, Vorlage:, Modèle:, Category:, Kategorie:, Portal: ecc.) non è un'opera. Usata dal giro mensile (storico/storico.py) e dal passo che ripulisce i file già pronti (storico/applica_registro.py, togli_consultazione).
- Effetto: 22 opere tolte (63 righe tra ricerca e pagine per autore). Rimaste 0. prova_regole e controllo_pagine a 0.

## 26/11/2026 notte — Thema, passo 1: dati strutturati per tutto il catalogo (ok di Marco)
- Metodo deciso: lo script assegna i codici con tabelle di corrispondenza fatte una volta e controllate da Marco riga per riga (valore Wikidata per codice Q... → codice Thema), non leggendo testi: genere/forma, luogo della storia (solo se nome e Paese coincidono esattamente con la lista Thema), periodo della storia (solo se dichiarato, mai l'anno di pubblicazione), formule fisse delle descrizioni brevi; più le regole di Marco (regole-classificazione.md). Valori rari o ambigui: all'AI.
- Raccolta (scripts/thema_raccolta.py, giro .github/workflows/thema-catalogo.yml): per le 54.489 opere della ricerca, proprietà Wikidata P136, P7937, P31, P921, P840, P2408, P629, P1433, descrizioni brevi it/en, presenza di Wikipedia it/en e Wikisource tedesca; conteggio di ogni valore. Wikipedia non scaricata (serve solo all'AI, dopo). Sito invariato.
- **Esito raccolta (27 min):** 54.472 opere. Forma su 23.698 (216 valori: i primi 20 coprono il 97%), genere su 15.707 (1.370 valori: i primi 200 coprono l'86%), tipo su 54.436, luogo della storia solo su 2.399, periodo su 334, «edizione di» su 4.001, «pubblicato in» su 13.962 (Die Gartenlaube 4.404). Descrizione breve it/en su 49.575, voce Wikipedia it/en su 19.870 (36%), Wikisource tedesca su 6.539.
- **Tabelle proposte (scripts/thema_tabelle.py):** 213 righe (forma 49, genere 136, tipo 28, formule delle descrizioni 16). Condizioni: generi teatrali solo per testi teatrali; generi per bambini mai in automatico; «articolo» solo come ripiego (una poesia uscita su rivista resta poesia); «romantic fiction» esclusa (su Wikidata indica spesso il Romanticismo).
- **Copertura dello script:** 37.724 opere su 54.472 (69%) con almeno un codice; 16.639 senza (all'AI); 109 solo con generi per bambini (da decidere).
- **Qualità contro le 168 sicure della prova a mano:** dei codici dello script 116 uguali ai miei, 35 della stessa famiglia ma più generici (es. «poesia di un autore» invece di «poesia classica», «filosofia» invece di «filosofia dell'Illuminismo»), 43 diversi. Tra i diversi: «narrativa classica» aggiunto a romanzi che hanno anche il genere (accettabile), ma anche errori presi da Wikidata così com'è (Commentarii de Bello Gallico come «autobiografia», I gauchos ebrei come «saggio»). Giudizio: lo script è affidabile ma grossolano; il dettaglio (argomento, luogo, epoca) lo può dare solo l'AI leggendo Wikipedia, che c'è per il 36% delle opere.
- Pagina di controllo delle righe per Marco: artifact privato «Tabelle Thema» (decisioni nella collezione «righe»).
