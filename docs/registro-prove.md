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
