# Public Domain Radar

[🇮🇹 Italiano](README.md) · 🇬🇧 English · Site: **[publicdomainradar.com](https://publicdomainradar.com)**

Which authors enter the public domain on the next 1 January, **country by country** (Italy, France, Germany, Spain), with biography, works, existing Italian editions and online interest by language. Built for people who decide what to republish or retranslate: publishers, translators, agents, librarians.

It runs by itself: open data, automatic monthly updates, zero running cost (GitHub Pages + GitHub Actions).

## What it does

- **List by year and country.** A Country menu changes the term rule, and the ranking switches to interest in that country's language (Wikipedia in Italian, French, German, Spanish). "English-speaking world" and "International" (in how many languages a page exists) are always available.
- **Dates country by country** on every author card, with the legal sources in the box at the bottom of the site.
- **Italian editions** from the national SBN catalogue: how many records exist, the latest, how many since 2000.
- **One page per author** (`/autore/author-name/`) with a biography and at least one work, generated monthly; index and sitemap included. Authors with no biography or no works get no page, to avoid empty pages. These pages are in Italian.
- **Italian and English**, search, filters, "My list" (favourites saved in the browser), CSV export.

## How it works

Every month `.github/workflows/aggiorna.yml` runs, in order:

| Step | Script | What it does |
|---|---|---|
| 1 | `scripts/aggiorna.py` | Downloads from [Wikidata](https://www.wikidata.org) the writers, poets and playwrights who died in the right year. One file per year and rule (`data/2027.json`, `data/es-2027.json`). |
| 2 | `scripts/arricchisci.py` | Biography (Wikipedia), works and genres (Wikidata), Wikipedia page views over 12 months in 5 languages, 0-100 indices relative to the year's list, portrait from Wikimedia Commons with its licence. |
| 3 | `scripts/traduzioni.py` | Checks in which languages the works already exist ([Open Library](https://openlibrary.org)). |
| 4 | `scripts/sbn.py` | Counts Italian editions in [SBN](https://opac.sbn.it) (ICCU SPARQL). |
| 5 | `scripts/pagine.py` | Generates the author pages, the index and `sitemap.xml`. |

`index.html` is the site (a single file, no framework). The workflow saves data to the repository, retries the push if GitHub rejects it and, if it does not finish within the time limit, **saves what it already has and restarts by itself** from where it stopped. Downloaded data stays cached (`data/cache_*.json`).

### Open sources only, nothing from memory

Wikidata (CC0), Wikipedia and Wikimedia APIs (text CC BY-SA, always linked to the original page), Wikimedia Commons (portraits, each with its own licence), Open Library, Project Gutenberg, the SBN catalogue. Legal rules are read from official texts and cited on the site with the article. If a source does not answer, the update stops with an error and the previous data stays intact. A quality check blocks saving when too much data is missing.

### SBN matching, and how mistakes are prevented

An author is looked up in SBN first by VIAF identifier (Wikidata P214), then by name: surname, all given names compared in order, confirmed with birth and death years. If the candidate list is truncated or ambiguous, **it does not guess**: the author stays without a count. Two safeguards against silent errors:

- `CONTROLLI` in `scripts/sbn.py`: well-known authors with an expected minimum number of editions (Brecht, Milne, Wilder, Papini). If the count is lower, the workflow prints a warning.
- `data/sospetti_sbn.json`: very well-known authors with very few editions are flagged on the card ("to verify").

These checks came from a real bug: Milne showed a single edition because the agent list had been truncated and the name filter compared only the first initial.

## Term rules: what is verified and what is not

EU base: death + 70 years, from 1 January of the following year (Directive 2006/116/EC, Arts. 1 and 10). The site shows the national rules read from official texts:

- **Germany**: UrhG §64 and §69, no extension.
- **France**: CPI L123-1, L123-8/9 (wartime extension, 8 years and 120 days for works published before 3 September 1939), L123-10 (+30 years for those who died for France).
- **Italy**: Law 633/1941 Arts. 25 and 32-ter, D.Lgs.Lgt. 440/1945 Art. 1 (6-year extension for works published and not yet free in 1945).
- **Spain**: TRLPI Arts. 26 and 30, fourth transitional provision; for authors who died before 7 December 1987 the law of 10 January 1879 applies (80 years).

**Not yet verified** (and declared as such on the site): how Spain counts the expiry year (the date shown is cautious); whether Italy's 6-year extension adds on top of the 70 years; the exact length of the 1947 peace treaty extension for each Allied country; the United States (term tied to publication, not death, so it would need per-work data). Other EU countries are not covered: each needs its national law read.

## Limits to know

- Indicative calculation, **not legal advice**: check the law of the country before publishing.
- For anonymous or pseudonymous authors the term runs from publication.
- Public domain concerns the author's work: a modern translation or a critical edition may carry its own rights.
- Wikidata sometimes calls someone a "writer" who is mostly something else: that is why having linked works also counts.
- Online interest is a hint, not an exact measure. Wikipedia in Spanish or French is also read outside the country (Latin America, the French-speaking world).
- The SBN count covers catalogue records, not books on sale. Lesser-known authors may not have one.

## Running it

On GitHub: **Actions → Aggiorna autori in pubblico dominio → Run workflow**. Locally, from the project folder: `python scripts/aggiorna.py`, then `arricchisci.py`, `traduzioni.py`, `sbn.py`, `pagine.py`. To publish: **Settings → Pages → Deploy from a branch → `main` / root**.
