# Mockup di redesign della home (novembre 2026)

Cartella temporanea: tre proposte per la home di Public Domain Radar. Non è collegata dal menu né dalla sitemap e le pagine hanno `noindex`. Si cancella quando si sceglie la proposta.

Tutte e tre leggono i dati veri (`data/2027.json`, `data/es-2027.json`, `data/fuori_classifica.json`) con la stessa classifica del sito (indice per lingua del paese, poi visite). Le foto vengono da Wikimedia Commons con autore e licenza, come sul sito. Restano invariati colori, caratteri e logo.

## Diagnosi del sito attuale

- Cosa funziona: i ritratti, i nomi giganti in Big Shoulders, le copertine tipografiche, la classifica che cambia col paese.
- Cosa lo rende «già visto»: fondo quasi nero con un solo accento vermiglio; etichette in maiuscolo spaziato e monospazio sopra ogni titolo; una parola del titolo colorata («libero»); la foto, che è la cosa più bella, sta in un riquadro laterale piccolo; tutte le sezioni hanno lo stesso schema (etichetta, titolo, griglia).

## Le tre direzioni (un solo elemento forte per pagina)

- **A · Il salone** (`a.html`): la home è una parete di ritratti appesi come in un salone museale. La dimensione del quadro è il dato: più l'autore è letto nel paese scelto, più è grande. Il titolo è il cartellino della parete. Riferimento: le gallerie a quadreria e le pagine dei musei con collezioni aperte.
- **B · Il passaggio** (`b.html`): racconto a scorrimento con grafico fisso, il metodo delle storie di dati di The Pudding. Il ritratto del primo autore è coperto da un nastro «©» che si toglie scorrendo. Poi tutti gli scrittori dell'anno diventano un quadratino ciascuno, in colonna per mese di morte, e si possono filtrare.
- **C · Lo schedario** (`c.html`): la scheda di catalogo di biblioteca (SBN, BnF, BNE sono cataloghi), con la riga rossa in testa delle schede vere e il timbro «pubblico dominio» in vermiglio. Il cassetto si sfoglia di lato; i paesi sono le linguette del cassetto.

## Tratti evitati (lista della skill di design)

Niente parola singola colorata nel titolo, niente etichette in maiuscolo spaziato sopra ogni titolo, niente frecce in coda ai link, niente schede tutte uguali con ombra, niente animazioni d'ingresso su ogni sezione. Il monospazio resta solo dove ha un senso (la macchina da scrivere della scheda di catalogo in C).
