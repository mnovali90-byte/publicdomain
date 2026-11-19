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
