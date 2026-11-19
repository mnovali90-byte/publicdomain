# Metodo: l'anno di uscita delle opere (Public Domain Radar)

Deciso il 19/11/2026 dopo un errore grave: le «Poesie di Svendborg» di Brecht risultavano del 1926, quindi libere
negli USA, ma sono uscite nel 1939. L'anno veniva solo da Wikidata e nessuno lo controllava.

## Il principio

Un'opera si dice **libera** solo quando l'anno da cui dipende è confermato da **almeno una fonte indipendente da
Wikidata**. Senza conferma si dice **«da verificare»**, mai «libera».

## Quando serve

Ogni volta che la libertà di un'opera dipende dal suo anno di uscita e non dalla morte dell'autore. Oggi: le opere
libere negli USA (95 anni dall'uscita) il cui autore non è morto da più di 70 anni. Vale anche per ogni pagina
futura che mostri lo stato opera per opera (per esempio la tabella «opera per opera» della scheda autore).

## Le fonti, in ordine

1. **Duke University, Public Domain Day** (CC BY 4.0): anno di pubblicazione dei libri delle sue liste.
2. **Open Library**: anno di prima pubblicazione, stesso titolo e stesso autore.
3. **Library of Congress**, catalogo (servizio SRU): anno di ogni edizione (campo 008), stesso titolo (campo 245)
   e cognome dell'autore.

## Come si leggono

- Una fonte **conferma** se ha un'edizione con lo stesso titolo e lo stesso autore uscita entro il limite.
- Una fonte **non smentisce**: un anno più tardo vuol dire solo che quella fonte non ha l'edizione più vecchia
  (Open Library e la Library of Congress danno l'edizione più vecchia che possiedono, spesso una ristampa).
- Nessuna conferma: «da verificare».

## Come si controlla il metodo

Dopo ogni giro: conteggio per esito e per fonte, e 10 esempi a caso per esito controllati a mano, scritti in
`docs/registro-prove.md`. Una fonte nuova entra solo dopo la stessa prova.

## Dove sta

`storico/verifica_anni.py` (gira nel lavoro `gia-pubblici.yml`, riparte da solo finché non ha finito),
risultati in `data/storico/anni_verificati.json`, letti dalla pagina «Già pubblici».
