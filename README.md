# Public Domain Radar

🇮🇹 Italiano · [🇬🇧 English](README.en.md) · Sito: **[publicdomainradar.com](https://publicdomainradar.com)**

Quali autori e quali opere entrano in pubblico dominio il prossimo 1° gennaio, **paese per paese**: Italia, Francia, Germania, Spagna, Regno Unito e USA. Ogni autore ha biografia, opere, interesse online per lingua e il numero di registrazioni che ha già nel catalogo della biblioteca nazionale del paese scelto. È pensato per chi deve decidere cosa ripubblicare o ritradurre: editori, traduttori, agenti, bibliotecari.

Il sito funziona da solo, con dati aperti e un aggiornamento mensile automatico. Il costo di gestione è zero (GitHub Pages + GitHub Actions).

## Cosa fa

- **Elenco per anno e per paese.** Il menu Paese cambia la regola di durata e la classifica dell'interesse, che passa alle visite su Wikipedia nella lingua di quel paese. Restano sempre disponibili il «mondo anglofono» e l'«internazionale» (in quante lingue esiste una pagina sull'autore).
- **Date paese per paese** su ogni scheda, con le norme di riferimento nel riquadro in fondo al sito.
- **USA:** qui si contano le opere, non gli autori. Vale la regola dei 95 anni dalla pubblicazione.
- **Registrazioni nei cataloghi nazionali**: quante registrazioni collegate all'autore ci sono nella lingua del paese scelto, quante dal 2000 e la più recente.

  | Paese | Catalogo | Come si riconosce l'autore |
  |---|---|---|
  | Italia | SBN | codice SBN di Wikidata, poi VIAF, poi nome con una prova |
  | Francia | BnF | codici BnF di Wikidata |
  | Spagna | BNE | codice BNE di Wikidata, poi nome e anni verificati |
  | Regno Unito | British Library | nome e anni verificati |
  | USA | Library of Congress | codice LC di Wikidata |
  | Germania | — | non ancora collegato |

  Si contano tutte le pubblicazioni collegate alla persona, comprese quelle in cui ha collaborato (traduzioni, curatele, prefazioni): è una misura di quanto l'autore è presente nel catalogo. Non indica se un libro è in commercio, né basta per dire che un autore sia inedito.
- **Una pagina per ogni autore** (`/autore/nome-autore/`) con biografia e almeno un'opera, generata ogni mese, con indici e sitemap. Esiste anche la versione inglese (`/en/author/…`).
- **Italiano (`/`) e inglese (`/en/`)**, più ricerca, filtri, «I miei» (preferiti salvati nel browser) ed esportazione per Excel (CSV) con le colonne del catalogo del paese scelto.

## Come funziona

Ogni mese `.github/workflows/aggiorna.yml` esegue questi passi, in ordine:

| Script | Cosa fa |
|---|---|
| `aggiorna.py` | Scarica da Wikidata scrittori, poeti e drammaturghi morti nell'anno giusto: un file per anno e per regola (`data/2027.json`, `data/es-2027.json`). |
| `arricchisci.py` | Aggiunge biografia (Wikipedia), opere e generi (Wikidata), visite a Wikipedia degli ultimi 12 mesi in 5 lingue, indici 0-100 e ritratto da Wikimedia Commons con la sua licenza. |
| `sbn.py` · `riconosci_sbn.py` | Registrazioni in italiano nel catalogo SBN (SPARQL dell'ICCU). |
| `bnf.py` | Registrazioni in francese nella BnF (SRU). |
| `alma.py` · `voce_alma.py` | Registrazioni in spagnolo nella BNE e in inglese nella British Library (SRU Alma). |
| `loc.py` | Registrazioni in inglese nella Library of Congress (SRU e id.loc.gov). |
| `opere.py` | Opere che diventano libere negli USA. |
| `verifica.py` | Seconda fonte per l'anno di morte (GND, Library of Congress, fonti citate in Wikidata). |
| `controlli.py` | Sospende i conteggi che si contraddicono e quelli segnati a mano in `data/sospesi_manuali.json`. |
| `pagine.py` | Genera le pagine autore, gli indici e `sitemap.xml`. |

`index.html` è il sito: un solo file, senza framework. Se il workflow non finisce nel tempo massimo, salva quello che ha fatto e riparte da solo da dove era rimasto. I dati scaricati restano in cache (`data/cache_*.json`).

### Tutto da fonti aperte, niente a memoria

Le fonti sono Wikidata (CC0), Wikipedia e le API Wikimedia (testi CC BY-SA, sempre con il link alla pagina d'origine), Wikimedia Commons, Project Gutenberg e i cataloghi SBN, BnF, BNE, British Library e Library of Congress. Le regole di legge sono lette sui testi ufficiali e citate nel sito con l'articolo.

## Come si evitano gli errori

Collegare un autore alla scheda di un omonimo è l'errore più grave, perché produce numeri falsi. Il metodo usato, documentato con tutte le prove in [`docs/registro-prove.md`](docs/registro-prove.md), è questo:

1. **Prima il codice, poi il nome.** Se Wikidata dà il codice dell'autore nel catalogo, si usa solo quello.
2. **Il nome solo con una prova.** Il nome viene normalizzato da tutte e due le parti (accenti, particelle, iniziali, ordine orientale) e la scheda si accetta solo se coincidono anche gli anni di nascita e morte, oppure un titolo. Senza prova l'autore resta «ambiguo» e non si conta nulla.
3. **Si conta solo ciò che è della persona.** Nella British Library e nella BNE una notizia conta solo se cognome e anni stanno nella stessa voce d'autore. Nella Library of Congress solo se l'intestazione è identica a quella ufficiale e l'autore compare come autore o collaboratore, non come soggetto.
4. **Ogni regola è misurata prima del rilascio:** un campione di sviluppo, poi regole congelate, poi un campione nuovo di autori mai visti, deciso a mano prima della misura. Se dopo la misura si cambia una regola, serve un'altra verifica. Zero errori in un campione non vuol dire zero errori sul sito.
5. **Controlli continui:** i conteggi incoerenti (per esempio più registrazioni recenti che totali) vengono sospesi e il sito mostra «Dati in verifica». Gli autori noti hanno soglie minime attese, e i collegamenti dubbi si possono sospendere a mano.

## Regole sulla durata

La base UE è morte + 70 anni, dal 1° gennaio dell'anno successivo (direttiva 2006/116/CE, art. 1 e 10). Le regole nazionali sono lette sui testi ufficiali:

- **Germania**: UrhG §64 e §69, nessuna proroga.
- **Francia**: CPI L123-1. Per la Cassazione (2007) le proroghe di guerra L123-8/9 sono comprese nei 70 anni; i «morti per la Francia» hanno 30 anni in più (L123-10).
- **Italia**: L. 633/1941 art. 25 e 32-ter. La proroga di 6 anni del D.Lgs.Lgt. 440/1945 è stata abrogata dalla L. 52/1996, art. 17. Per gli autori dei paesi alleati vale il Trattato di pace del 1947, allegato XV, da verificare caso per caso.
- **Spagna**: TRLPI art. 26 e 30, disposizione transitoria quarta. Per i morti prima del 7 dicembre 1987 vale la legge del 1879 (80 anni).
- **Regno Unito**: CDPA 1988, sezione 12.
- **USA**: 17 U.S.C. § 304, 95 anni dalla pubblicazione per le opere pubblicate prima del 1978, con le eccezioni del mancato rinnovo e del § 104A.

**Non ancora verificato**, e dichiarato come tale nel sito:
- come la Spagna conta l'anno di scadenza (la data mostrata è prudente);
- se ai 70 anni si sommino i 30 anni dei «morti per la Francia»;
- la durata esatta della proroga del Trattato di pace per ciascun paese alleato.

Gli altri paesi UE non sono coperti.

## Limiti da conoscere

- Il calcolo è indicativo e **non è consulenza legale**: prima di pubblicare va verificato nella legge del paese.
- Il pubblico dominio riguarda l'opera originale. Una traduzione moderna o un'edizione critica può avere diritti propri.
- I cataloghi riflettono come le biblioteche hanno schedato i libri. Un autore schedato con un'altra forma del nome può sfuggire, quindi «nessuna registrazione collegata» non vuol dire «inedito».
- L'interesse online è un indizio, non una misura delle vendite.

## Lanciarlo a mano

Su GitHub: **Actions → Aggiorna autori in pubblico dominio → Run workflow**. Per metterlo online: **Settings → Pages → Deploy from a branch → `main` / root**.
