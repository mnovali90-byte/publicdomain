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
- **18/11, Saldías:** Marco l'ha trovato su OPAC («Saldias, José Antonio»). Causa del mio «assente» sbagliato: in SBN gli accenti sono usati in modo incoerente dentro la stessa scheda («Saldias» senza, «José» con). Cercare togliendo tutti gli accenti o tenendoli tutti non basta: va cercata ogni parola in tutte e due le forme. Lo stesso problema tocca il sistema e va nella fase 4. Esiti: presenti 75, assenti 53, irrisolti 12.
