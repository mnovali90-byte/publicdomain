# Public Domain Radar

Quali autori entrano in pubblico dominio il prossimo anno, aggiornato in automatico.

**Regola (Unione Europea):** le opere diventano libere il 1° gennaio dell'anno successivo ai 70 anni dalla morte dell'autore.
Autore morto nel 1956 → opere libere dal 1° gennaio 2027.

## Come funziona

- `scripts/aggiorna.py` scarica da [Wikidata](https://www.wikidata.org) (dati aperti) gli scrittori, poeti e drammaturghi morti nell'anno giusto, mese per mese, e li ordina per notorietà (numero di versioni Wikipedia).
- `.github/workflows/aggiorna.yml` lo fa girare da solo il primo di ogni mese e salva il risultato in `data/`.
- Se Wikidata non risponde, l'aggiornamento si ferma con errore e i dati precedenti restano intatti.

## Lanciarlo a mano

Su GitHub: **Actions → Aggiorna autori in pubblico dominio → Run workflow**.
In locale: `python scripts/aggiorna.py --anno 2027`

## Limiti da conoscere

- La regola è quella europea base. Alcuni paesi hanno proroghe o eccezioni (per esempio proroghe di guerra): per questi casi serve una verifica nazionale.
- Per gli autori anonimi o con pseudonimo la durata si calcola dalla pubblicazione, non dalla morte.
- Il pubblico dominio riguarda l'opera dell'autore: una traduzione moderna o un'edizione critica può avere diritti propri.
- I dati sono quelli di Wikidata: qualche data può mancare o essere approssimata.

Fonte dati: Wikidata, licenza CC0.
