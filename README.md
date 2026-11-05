# Public Domain Radar

Quali autori entrano in pubblico dominio il prossimo anno, con biografia, opere principali e tre misure di interesse online. Si aggiorna da solo ogni mese.

**Regola (Unione Europea):** le opere diventano libere il 1° gennaio dell'anno successivo ai 70 anni dalla morte dell'autore.
Autore morto nel 1956 → opere libere dal 1° gennaio 2027.

## Come funziona

1. `scripts/aggiorna.py` scarica da [Wikidata](https://www.wikidata.org) (dati aperti) gli scrittori, poeti e drammaturghi morti nell'anno giusto, mese per mese. Salva `data/<anno>.json`.
2. `scripts/arricchisci.py` aggiunge, per gli autori con una qualifica letteraria precisa (romanziere, poeta, drammaturgo, saggista):
   - **biografia**: prime frasi della pagina Wikipedia (italiano, altrimenti inglese), con link alla fonte;
   - **opere e generi**: da Wikidata. Chi non ha nessuna opera collegata finisce nella sezione "senza opere note";
   - **interesse online, in tre numeri separati (0-100 rispetto alla lista dell'anno)**: Italia (visite alla pagina Wikipedia italiana, 12 mesi), mondo anglofono (visite alla pagina inglese), internazionale (in quante lingue esiste una pagina). Nessuna media: le visite dipendono anche da quanti lettori ha una lingua, quindi vanno lette per mercato. Gutenberg è mostrato come dato a parte.
3. `index.html` mostra tutto: scelta dell'anno, filtri, ricerca, dettaglio per autore.
4. `.github/workflows/aggiorna.yml` esegue i passi 1 e 2 il primo di ogni mese e salva il risultato in `data/`.

Se Wikidata non risponde, l'aggiornamento si ferma con errore e i dati precedenti restano intatti.

## Metterlo online

Su GitHub: **Settings → Pages → Source: Deploy from a branch → `main` / `(root)`**. L'indirizzo sarà `https://<utente>.github.io/publicdomain/`.

## Lanciarlo a mano

Su GitHub: **Actions → Aggiorna autori in pubblico dominio → Run workflow**.
In locale: `python scripts/aggiorna.py` e poi `python scripts/arricchisci.py`.

## Limiti da conoscere

- Regola europea di base. Alcuni paesi hanno proroghe o eccezioni (per esempio proroghe di guerra): per questi casi serve una verifica nazionale.
- Per gli autori anonimi o con pseudonimo la durata si calcola dalla pubblicazione, non dalla morte.
- Il pubblico dominio riguarda l'opera dell'autore: una traduzione moderna o un'edizione critica può avere diritti propri.
- Wikidata a volte chiama "poeta" o "scrittore" anche chi è soprattutto altro (pittori, sportivi): per questo conta anche avere opere collegate.
- L'interesse online è un indizio, non una misura esatta (le visite risentono di anniversari, notizie e dimensione del pubblico). Le opere in Wikidata sono ben coperte per gli autori famosi e poco per gli altri.
- Le biografie sono testi di Wikipedia (CC BY-SA): vanno sempre mostrati con il link alla fonte.

Fonti dati: Wikidata (CC0), Wikipedia e API Wikimedia, Project Gutenberg (tramite Gutendex).
