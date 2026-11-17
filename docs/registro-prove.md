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
