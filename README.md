# Public Domain Radar

🇮🇹 Italiano · [🇬🇧 English](README.en.md) · Sito: **[publicdomainradar.com](https://publicdomainradar.com)**

Quali autori entrano in pubblico dominio il prossimo 1° gennaio, **paese per paese** (Italia, Francia, Germania, Spagna), con biografia, opere, edizioni italiane già esistenti e interesse online per lingua. Pensato per chi deve decidere cosa ripubblicare o ritradurre: editori, traduttori, agenti, bibliotecari.

Funziona da solo: dati aperti, aggiornamento mensile automatico, costo di gestione zero (GitHub Pages + GitHub Actions).

## Cosa fa

- **Elenco per anno e per nazione.** Menù Paese: cambia la regola di durata e la classifica passa subito all'interesse nella lingua di quella nazione (Wikipedia in italiano, francese, tedesco, spagnolo). Restano sempre disponibili "mondo anglofono" e "internazionale" (in quante lingue esiste una pagina).
- **Date paese per paese** su ogni scheda, con le norme di riferimento nel riquadro in fondo al sito.
- **Edizioni italiane** dal catalogo nazionale SBN: quante registrazioni esistono già, l'ultima, quante dal 2000.
- **Una pagina per ogni autore** (`/autore/nome-autore/`, 316) con biografia e almeno un'opera, generata ogni mese; indici e sitemap inclusi. Gli autori senza biografia o senza opere non hanno pagina, per non produrre pagine vuote. **Versione inglese** (`/en/author/nome-autore/`, 310) solo per chi ha la biografia inglese, collegata alla italiana con `hreflang`: senza opere, paesi e professioni, perché in Wikidata hanno etichette italiane e non si mescolano due lingue nella stessa pagina.
- **Italiano e inglese**, ricerca, filtri, "I miei" (preferiti salvati nel browser), esportazione CSV.

## Come funziona

Ogni mese `.github/workflows/aggiorna.yml` esegue in ordine:

| Passo | Script | Cosa fa |
|---|---|---|
| 1 | `scripts/aggiorna.py` | Scarica da [Wikidata](https://www.wikidata.org) scrittori, poeti e drammaturghi morti nell'anno giusto. Un file per anno e per regola (`data/2027.json`, `data/es-2027.json`). |
| 2 | `scripts/arricchisci.py` | Biografia (Wikipedia), opere e generi (Wikidata), visite a Wikipedia degli ultimi 12 mesi in 5 lingue, indici 0-100 rispetto alla lista dell'anno, ritratto da Wikimedia Commons con la sua licenza. |
| 3 | `scripts/traduzioni.py` | Controlla in quali lingue esistono già le opere ([Open Library](https://openlibrary.org)). |
| 4 | `scripts/sbn.py` | Conta le edizioni italiane in [SBN](https://opac.sbn.it) (SPARQL ICCU). |
| 5 | `scripts/pagine.py` | Genera le pagine autore in italiano e inglese, i due indici e `sitemap.xml`. |

`index.html` è il sito (un solo file, nessun framework). Il workflow salva i dati nel repository, ritenta il push se GitHub lo rifiuta e, se non finisce nel tempo massimo, **salva quello che ha già e riparte da solo** dal punto in cui era. I dati scaricati restano in cache (`data/cache_*.json`).

### Tutto da fonti aperte, niente a memoria

Wikidata (CC0), Wikipedia e API Wikimedia (testi CC BY-SA, sempre con link alla pagina d'origine), Wikimedia Commons (ritratti, ciascuno con la sua licenza), Open Library, Project Gutenberg, catalogo SBN. Le regole di legge sono lette sui testi ufficiali e citate nel sito con l'articolo. Se una fonte non risponde, l'aggiornamento si ferma con errore e i dati precedenti restano intatti. Un controllo di qualità blocca il salvataggio se mancano troppi dati.

### Il match con SBN, e come si evitano gli errori

Un autore si cerca in SBN prima per identificativo VIAF (Wikidata P214), poi per nome: cognome, tutti i nomi di battesimo confrontati in ordine, e conferma con gli anni di nascita e di morte. Se l'elenco di candidati è troncato o ambiguo, **non si indovina**: l'autore resta senza conteggio. Due protezioni contro gli errori silenziosi:

- `CONTROLLI` in `scripts/sbn.py`: autori noti con un minimo atteso di edizioni (Brecht, Milne, Wilder, Papini). Se il conteggio è più basso, il workflow stampa un avviso.
- `data/sospetti_sbn.json`: autori molto noti con pochissime edizioni vengono segnalati sulla scheda ("da verificare").

Questi controlli sono nati da un errore reale: Milne risultava con una sola edizione perché l'elenco degli agenti era stato troncato e il filtro sul nome confrontava solo la prima iniziale.

## Regole sulla durata: cosa è verificato e cosa no

Base UE: morte + 70 anni, dal 1° gennaio dell'anno successivo (direttiva 2006/116/CE, art. 1 e 10). Il sito mostra le regole nazionali lette sui testi ufficiali:

- **Germania**: UrhG §64 e §69, nessuna proroga.
- **Francia**: CPI L123-1, L123-8/9 (proroga di guerra, 8 anni e 120 giorni per le opere pubblicate prima del 3 settembre 1939), L123-10 (+30 anni per i morti per la Francia).
- **Italia**: L. 633/1941 art. 25 e 32-ter, D.Lgs.Lgt. 440/1945 art. 1 (proroga di 6 anni per le opere pubblicate e non ancora libere nel 1945).
- **Spagna**: TRLPI art. 26 e 30, disposizione transitoria quarta; per i morti prima del 7 dicembre 1987 vale la legge del 10 gennaio 1879 (80 anni).

**Non ancora verificato** (e dichiarato come tale nel sito): come la Spagna conta l'anno di scadenza (la data mostrata è prudente); se in Italia la proroga di 6 anni si somma ai 70 anni; la durata esatta della proroga del trattato di pace 1947 per ciascun paese alleato; gli Stati Uniti (durata legata alla pubblicazione, non alla morte, quindi servirebbe un dato per opera). Gli altri paesi UE non sono coperti: per ognuno serve leggere la legge nazionale.

## Limiti da conoscere

- Calcolo indicativo, **non consulenza legale**: prima di pubblicare va verificato nella legge del paese.
- Per gli autori anonimi o con pseudonimo la durata si calcola dalla pubblicazione.
- Il pubblico dominio riguarda l'opera dell'autore: una traduzione moderna o un'edizione critica può avere diritti propri.
- Wikidata chiama a volte "scrittore" chi è soprattutto altro: per questo conta anche avere opere collegate.
- L'interesse online è un indizio, non una misura esatta. Wikipedia in spagnolo o francese è letta anche fuori dal paese (America Latina, francofonia).
- Il conteggio SBN riguarda le registrazioni del catalogo, non i libri in commercio. Gli autori meno noti possono non averlo.

## Lanciarlo a mano

Su GitHub: **Actions → Aggiorna autori in pubblico dominio → Run workflow**. In locale, dalla cartella del progetto: `python scripts/aggiorna.py`, poi `arricchisci.py`, `traduzioni.py`, `sbn.py`, `pagine.py`. Per metterlo online: **Settings → Pages → Deploy from a branch → `main` / root**.
