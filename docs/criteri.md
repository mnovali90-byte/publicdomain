# Criteri del sito (un posto solo)

Questo documento è la fonte dei criteri. **Un criterio o una regola non cambia senza aggiornare qui** (data, motivo,
caso che l'ha fatta nascere) e senza un caso in `data/casi_riferimento.json`, che la prova 4
(`scripts/prova_regole.py`) ricontrolla a ogni giro. Il codice è in `scripts/regole.py`.

## Opere USA: quando un'opera è «verificata»

Un'opera USA è **verificata** quando la sua **prima uscita** (libro, rivista o registrazione) è documentata da
**due fonti indipendenti** oppure da **una scheda del Catalog of Copyright Entries (CCE)**, e **nessuna fonte indica
un'uscita precedente**.

- **Una scheda CCE basta da sola; per tutto il resto servono due fonti** (decisione di Marco, 23/11/2026): il CCE è il
  registro ufficiale del Copyright Office.
- **Indipendenti** vuol dire che una non copia l'altra. Wikidata non conta come fonte indipendente; Wikipedia vale solo
  per la fonte che cita; Open Library conta insieme alla Library of Congress; venditori, librerie e siti di riassunti
  non valgono (docs/ricerca-web.md).
- **Ogni fonte scritta a mano ha una citazione** (frase esatta e breve della pagina), controllata in automatico.

Sulla pagina della lista USA un'opera ha uno di tre stati:

| Stato | Quando |
|---|---|
| prima uscita verificata | il criterio qui sopra |
| anno dell'edizione confermato | una fonte diversa da Wikidata conferma l'anno dell'edizione, ma la prima uscita non è ancora verificata |
| da confermare | nessuna fonte oltre a Wikidata |

## Regole per le opere USA (in ordine di data)

| Data | Regola | Motivo | Caso che l'ha fatta nascere |
|---|---|---|---|
| 23/11/2026 | La prima pubblicazione documentata (rivista o editore, con data e due fonti) vale più dei cataloghi: i cataloghi confermano ma non la battono | la Library of Congress dava 1896, la prima uscita documentata era il 1897 | La laguna (Conrad), Q7745219 |
| 23/11/2026 | Una raccolta senza testi nuovi esce nell'anno dell'ultimo testo già uscito; con almeno un testo nuovo resta con nota | i quattro racconti erano già usciti in rivista nel 1921-1924 | Racconti di Odessa (Babel'), Q1775716 |
| 23/11/2026 | Se prima è uscita solo una parte (frammenti, racconto, puntate) l'opera resta con nota; se è uscita prima per intero, esce | frammenti in giornali e riviste dal 1925, libro completo nel 1931 | Altazor (Huidobro), Q5670870 |
| 23/11/2026 | L'anno del libro (Wikidata, cataloghi, bibliografie nazionali) non basta per confermare: serve la prima uscita documentata; se anche una sola fonte indica un'uscita più vecchia, si resta «da decidere» | il racconto da cui nasce il romanzo era uscito in rivista nel 1931 | The Black Swan (Sabatini), Q85806586 |
| 23/11/2026 | Wikidata non fa da seconda fonte per confermare | Wikidata spesso ripete le altre fonti: non è indipendente | (criterio della verifica) |
| 23/11/2026 | Volumi in anni diversi: primo volume nell'anno della lista e altri dopo → resta con nota, ogni volume si libera nel suo anno; volume con fonti in disaccordo → nota «da verificare» | trilogia uscita nel 1931 e nel 1932 | I sonnambuli (Broch), Q1216006 |
| 23/11/2026 | Registrazione: con la legge del 1909 conta la prima tra pubblicazione e registrazione da inedita (Copyright Office, Circular 15A), presa dal CCE | opera teatrale registrata da inedita nel 1930, pubblicata nel 1931 | Green Grow the Lilacs (Riggs), Q4190252 |
| 23/11/2026 | Per un numero di rivista conta la data © del CCE (data di pubblicazione), non la data in copertina | numero di gennaio 1931 pubblicato il 18 dicembre 1930 | Dry September (Faulkner), Q5309555 |

## Anni di morte degli autori

| Data | Regola | Motivo | Caso |
|---|---|---|---|
| 20/11/2026 | Registro unico: l'anno di morte si decide in un posto solo (scripts/regole.py, decidi_morte) e tutte le pagine lo leggono | anni diversi fra pagine | (registro unico) |
| 20/11/2026 | Due fonti autorevoli d'accordo contro Wikidata: vale il loro anno («corretto») | Wikidata sbagliava l'anno | vedi data/morti_corrette.json |
| 23/11/2026 | La verifica a mano su fonti terze vince su tutto; in pagina: «Anno di morte controllato a mano su fonti terze:» seguito dalle fonti | la frase «fonte del paese dell'autore» non era vera per tutte | Ali-Akbar Dehkhoda, Q470931 |
| 23/11/2026 | Un autore che la regola della lista lascerebbe solo in «Tutti» entra nella lista principale se una fonte lo descrive come scrittore o poeta (data/verifiche_manuali.json, «scrittori_a_mano») | lessicografo e poeta | Ali-Akbar Dehkhoda, Q470931 |
