# Metodo: la classifica degli autori per paese (Public Domain Radar)

Deciso il 19/11/2026 dopo un errore: Asvero Gravelli era tra i primi in Italia per un picco di un giorno
(9.380 visite il 9 febbraio 2026, contro 560-1.020 al mese negli altri mesi). Prova e numeri in `docs/registro-prove.md`.

## Il principio

La classifica di un paese misura **quanto si legge di un autore, in modo regolare, sulla Wikipedia della lingua
di quel paese**. Un picco di pochi giorni non deve contare quanto un anno intero.

## Che cosa si misura

- **Visite da persone** alla pagina dell'autore, mese per mese, negli **ultimi 12 mesi chiusi**. Fonte: Wikimedia
  Pageviews, tipo di visitatore «user», quindi senza i programmi automatici riconosciuti.
- **Una lingua per paese:**
  - Italia: Wikipedia in italiano;
  - Francia: in francese;
  - Germania: in tedesco;
  - Spagna: in spagnolo;
  - Regno Unito e USA: in inglese.
- **Il titolo della pagina** si prende da Wikidata (collegamento tra le Wikipedia).

## Come si calcola

1. **Mese tipico** = la mediana dei 12 mesi dell'autore.
2. **Ogni mese conta al massimo 3 volte il mese tipico.** Il resto è considerato picco e non conta.
3. **Visite tipiche dell'anno** = la somma dei 12 mesi dopo il passo 2.
4. **Ordine:** si ordina per visite tipiche, dalla più alta. A parità di visite conta il numero di Wikipedia in cui
   esiste la pagina, poi il nome. Nessun voto da 0 a 100 per ordinare: il voto resta solo come informazione.

## Picchi

Un autore ha un **picco** quando, in un mese, ha più di 3 volte il suo mese tipico e almeno 1.000 visite in più.
I picchi si salvano e finiscono in `docs/da-decidere.md`: il nome resta in classifica, con le visite tipiche.

## Quando cambia la classifica sul sito

Solo quando la misura di **tutto l'elenco** è finita. Le misure parziali non si pubblicano.

## Vetrina

I «nomi più attesi» delle pagine del Public Domain Day sono una **scelta editoriale di Marco**, anno per anno. Il
sistema propone i primi 30 per visite tipiche, sommando le 5 lingue, e segnala i picchi. Le classifiche complete
restano calcolate dai dati.

## Come si controlla

Prima di cambiare il sito si fa un campione: i primi 30 di ogni paese, nell'ordine vecchio e in quello nuovo
(`scripts/prova_classifica.py`), da approvare.
