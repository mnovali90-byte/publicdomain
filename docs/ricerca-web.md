# Ricerca sul web per le opere: procedura fissa

Decisione di Marco, 23/11/2026. **Chi cerca scrive solo cosa dice ogni fonte. Decide la regola in codice**
(`regole.fatti_da_ricerca` e `regole.incrocio_opera`), non chi cerca. Niente di quello che si scrive qui cambia il sito
da solo: lo leggono i rapporti (scripts/collaudo_incrocio.py, scripts/incrocio_opere.py).

## Quando si cerca
Solo per le opere che l'incrocio lascia «da decidere», e per i campioni di collaudo.

## Cosa cercare, in quest'ordine
1. **Prima uscita in assoluto**, anche in rivista o a puntate: anno, rivista, editore.
2. **Parti uscite prima**: un racconto da cui nasce il romanzo, capitoli in rivista, una versione più breve.
3. **Raccolta**: se l'opera è una raccolta, se i testi erano già usciti prima (e quando) o sono nuovi.
4. **Volumi**: se è uscita in più volumi, l'anno di ciascuno.
5. **Lingua originale**: in che lingua è stata scritta e pubblicata la prima volta.

Ricerche tipo: «<titolo originale> <autore> first published», «<titolo> serialized», «<titolo> magazine <anno>»,
«<titolo> première édition», «<titolo> Erstausgabe», «<titolo> prima edizione», «<titolo> primera edición».

## Quali fonti valgono
- **Valgono:** bibliografie dell'autore curate (studiosi, società dell'autore, edizioni critiche), cataloghi delle
  biblioteche nazionali, indici delle riviste (FictionMags, ISFDB, Online Books Page), scansioni della rivista o del
  libro (archive.org, HathiTrust, Gallica, Trove), recensioni d'epoca con data, la pagina Wikipedia **solo se cita una
  fonte** (si scrive la fonte citata, non Wikipedia).
- **Non valgono:** librerie e venditori, siti di riassunti, blog senza fonti, risposte di AI, memoria di chi cerca.
- **Indipendenza («gruppo»):** due voci contano come due fonti solo se hanno gruppo diverso. Stesso gruppo se una copia
  l'altra (Wikipedia e la fonte che cita; Open Library e LoC; due edizioni dello stesso editore).

## Formato fisso del risultato
Una voce per fonte, in `docs/ricerca-web/risultati.json`, lista «voci»:

| campo | cosa | obbligatorio |
|---|---|---|
| qid | codice Wikidata dell'opera | sì |
| titolo | titolo come nella lista | sì |
| fonte | nome della fonte | sì |
| link | indirizzo della pagina letta | sì: senza link la voce non vale |
| citazione | frase esatta e breve copiata dalla pagina, che dice il fatto (anno, rivista, editore) | sì: senza citazione la voce non vale |
| tipo | prima_pubblicazione, parte_prima, raccolta, volume, edizione, registrazione | sì |
| anno | anno che la fonte dà (numero) | sì, se la fonte lo dà |
| gruppo | chi c'è dietro la fonte (per l'indipendenza) | sì |
| intera | per prima_pubblicazione: true se era l'opera intera, false se una parte | se si sa |
| testi_nuovi | per raccolta: true se i testi erano nuovi, false se già usciti | se si sa |
| volume | per volume: numero del volume | se tipo volume |
| inedita | per registrazione: true se registrata da inedita (classe D unpub., ecc.) | se tipo registrazione |
| lingua | lingua di quella uscita (en, fr, de, it, es...) | se si sa |
| nota | cosa dice la fonte, in parole proprie, una riga | no |
| data_ricerca, chi | quando e chi ha cercato | sì |

## Controlli contro l'invenzione (dal 23/11/2026)
- **Citazione controllata in automatico:** scripts/controlla_citazioni.py (giro `citazioni.yml`) apre ogni link e cerca la citazione. Esiti: «trovata», «non trovata», «non verificabile in automatico» (il sito blocca, non risponde, PDF illeggibile). Le voci «non trovata» e quelle senza citazione l'incrocio non le usa.
- **Seconda lettura:** in ogni blocco 3 voci estratte a caso (seme scritto nel rapporto del blocco) le ricontrolla un'altra chat, che apre il link e dice se la pagina dice davvero quello che è scritto. Le voci del blocco si applicano solo dopo.
- I criteri sono in docs/criteri.md: «una scheda CCE basta da sola; per tutto il resto servono due fonti».

## Registrazione (dal 23/11/2026)
Con la legge del 1909 il copyright nasce alla pubblicazione o, per le opere inedite, alla registrazione (Copyright Office, Circular 15A). Si cerca la scheda nel Catalog of Copyright Entries (CCE, scansioni su archive.org): per le opere inedite la data «©» della registrazione; per i numeri delle riviste la data «©» del numero, che è la data di pubblicazione (non quella in copertina). Gruppo «cce». Il CCE basta da solo: è il registro ufficiale.

## Come decide la regola (in codice, regole.fatti_da_ricerca)
- **Registrazione:** conta la prima tra pubblicazione e registrazione da inedita; se è prima dell'anno della lista → «esce».
- **Prima uscita:** serve lo stesso anno da due gruppi diversi e nessuna fonte con un anno più vecchio.
- **Parte uscita prima:** due gruppi; se l'anno è prima della lista → «nota» (resta, con l'avviso), mai «esce» da sola.
- **Raccolta:** due gruppi d'accordo sui testi già usciti → «esce»; testi nuovi → «nota».
- **Volumi:** il primo volume dopo l'anno della lista → «sposta»; prima → «esce». Primo volume nell'anno della lista e altri dopo → «nota» (ogni volume si libera nel suo anno); un volume con fonti in disaccordo → «nota» con quel volume «da verificare».
- Una sola fonte, o fonti in disaccordo: la voce resta scritta ma l'opera resta «da decidere».
