# Verifica delle opere: anni e collaboratori (attività decisa da Marco il 22/11/2026)

**Perché:** Wikidata da sola non basta, e neppure i cataloghi da soli: le fonti si incrociano e si tiene il dato su cui concordano.
Quando le fonti non sono d'accordo, Claude cerca sul web. Se anche lì non c'è certezza, il caso va a Marco con le fonti trovate.
I fatti li decidono le fonti terze, non Marco e non Claude.

**Quando:** una volta per lista.
- 2027 e 2028: dal 22/11/2026.
- 2029: a gennaio 2027, dopo il giro del 7 gennaio che crea la lista. È programmato.
- Poi ogni anno a gennaio, per la lista nuova.

**Anche gli autori:** quelli con fonti in disaccordo sull'anno di morte (esito «discorde» nel registro, 78 al 22/11/2026) seguono gli stessi passi 4-6. La decisione va in `data/verifiche_manuali.json`, con la fonte. Per quelli con una fonte sola (945) prima si contano quelli vicini al confine, cioè quelli per cui un anno sbagliato cambierebbe la data.

## Passi

1. **Raccolta (GitHub, giro «Fonti delle opere»).** Lo script è `scripts/prova_opere_fonti.py`, con `LISTE=...`. Per ogni opera principale (le prime 10 della scheda di ogni autore letterario) interroga Library of Congress, K10plus e BnF (solo per gli autori francesi). Di ogni edizione salva:
   - anno;
   - lingua (MARC 008/35-37, UNIMARC 101);
   - data di copyright (260/264 $c);
   - lingua da cui è tradotta (041 $h);
   - persone con date e ruolo (100/700, 700-702);
   - dicitura di responsabilità (245 $c, 200 $f/$g).

   Scrive `docs/fonti-opere/risultati.json`. Se il tempo finisce, il giro dopo riprende da dove si era fermato: basta cambiare `docs/fonti-opere/passo.txt`.

2. **Incrocio (regola scritta in codice il 23/11/2026: `regole.incrocio_opera`, script `scripts/incrocio_opere.py`, collaudo `scripts/collaudo_incrocio.py` → docs/collaudo-incrocio.md).** Esiti: conferma, nota, esce, sposta, da decidere. Regole del 23/11: prima pubblicazione documentata > cataloghi; le traduzioni non votano (un catalogo vota solo per le opere nella lingua delle sue edizioni); raccolta senza testi nuovi = esce, con testi nuovi = resta con nota; volumi uno per uno; uscita dopo = sposta; un solo indizio contrario basta per «da decidere».
   - **Anni.**
     - Votano Wikidata e i cataloghi, ma solo con le edizioni nella lingua originale e non tradotte.
     - Le fonti che si copiano contano una volta (Open Library ripete spesso la Library of Congress).
     - La data di copyright vale più dell'anno di stampa.
     - Gli anni impossibili non votano: un'edizione moderna, o un anno precedente alla nascita dell'autore.
     - Con due fonti indipendenti d'accordo, il dato si tiene. Altrimenti il caso è aperto.
   - **Collaboratori e illustratori.** Una persona che i cataloghi segnano come coautore, collaboratore («unter Mitarbeit von») o illustratore, in edizioni uscite quando l'autore era vivo e nella lingua originale, è un caso da verificare. Lo è anche se Wikidata non la segna.

3. **Solo i casi che contano.** Un disaccordo va nel rapporto solo se cambia lo stato dell'opera in almeno un paese:
   - **USA:** gli anni possibili stanno ai due lati del limite (oggi il 1930), oppure l'opera può essere postuma;
   - **Europa:** il collaboratore è morto dopo l'autore;
   - **illustrazioni:** l'illustratore è morto dopo l'autore, e allora serve la nota «solo il testo».

   Il calcolo si fa con `scripts/regole.py`, non a mano.

4. **Ricerca sul web (Claude, nella chat).** Per ogni caso aperto Claude cerca almeno due fonti autorevoli e indipendenti: editore, biblioteca nazionale, archivio, studi, chi detiene i diritti. Le pagine che ripetono Wikipedia non contano.

5. **Rapporto a Marco.** `docs/da-decidere-opere.md` e un messaggio in chat. Contiene:
   - i casi risolti, con le fonti;
   - i casi rimasti incerti, con le fonti trovate.

   Marco decide solo i casi incerti.

6. **Decisioni nei dati.** Ogni decisione va in `data/coautori_manuali.json` (collaboratori) o in `data/verifiche_opere.json` (anni, illustratori), con la fonte. Le pagine le leggono da lì. Il controllo degli stati (`scripts/controllo_stati.py`) verifica che le schede le rispettino.

## Liste USA: esiti delle decisioni (23/11/2026)

Le decisioni sulle opere delle liste USA stanno in `data/verifiche_opere.json`, parte «usa_lista», sempre con almeno due fonti indipendenti (almeno una primaria o specialistica) e con il link. Gli esiti sono tre:

- **resta:** l'opera resta nella lista del suo anno. Se una parte è uscita prima (puntate, frammenti, racconti già in rivista, originale in un'altra lingua), c'è una nota che lo dice.
- **tolta:** l'opera è già uscita per intero prima ed è già libera negli USA. Esce dalla lista e va in Già pubblici con l'anno della prima uscita.
- **sposta:** l'opera è uscita dopo l'anno della lista. Va nella lista del suo anno. Se quella lista non c'è ancora (si crea a gennaio), l'opera aspetta in `data/registro/liste_spostati.json`, parte «usa_spostate».

**Regola delle raccolte:** una raccolta senza testi nuovi esce (i testi erano già liberi); una raccolta con almeno un testo nuovo resta, con la nota.

**Opere in più volumi:** ogni volume conta con il suo anno, confermato da due fonti. La nota dell'opera dice l'anno di ogni volume.

Le applica `scripts/applica_registro_liste.py`; anno, fonti e note vanno nel registro delle opere (`scripts/registro.py`, `opere_decise`).
