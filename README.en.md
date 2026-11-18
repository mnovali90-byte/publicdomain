# Public Domain Radar

[🇮🇹 Italiano](README.md) · 🇬🇧 English · Site: **[publicdomainradar.com](https://publicdomainradar.com)**

Which authors and works enter the public domain next 1 January, **country by country**: Italy, France, Germany, Spain, the UK and the USA. Each author comes with a biography, works, online interest by language, and the number of records they already have in the national library catalogue of the chosen country. It is meant for people who decide what to republish or retranslate: publishers, translators, agents, librarians.

The site runs by itself on open data, with an automatic monthly update. Running cost is zero (GitHub Pages + GitHub Actions).

## What it does

- **List by year and country.** The Country menu switches the term rule and the interest ranking, which moves to Wikipedia views in that country's language. The «English-speaking world» and «international» views (in how many languages a page about the author exists) are always available.
- **Dates country by country** on every card, with the legal sources in the box at the bottom of the site.
- **USA:** this list counts works, not authors, under the rule of 95 years from publication.
- **Records in national catalogues**: how many records linked to the author exist in the chosen country's language, how many date from 2000 onwards, and the latest one.

  | Country | Catalogue | How the author is identified |
  |---|---|---|
  | Italy | SBN | SBN identifier from Wikidata, then VIAF, then name with evidence |
  | France | BnF | BnF identifiers from Wikidata |
  | Spain | BNE | BNE identifier from Wikidata, then verified name and years |
  | UK | British Library | verified name and years |
  | USA | Library of Congress | LC identifier from Wikidata |
  | Germany | — | not connected yet |

  Every publication linked to the person counts, including those they contributed to (translations, editing, prefaces): it measures how present the author is in the catalogue. It does not tell whether a book is in print, and it is not enough to say an author is unpublished.
- **One page per author** (`/autore/author-name/`) with a biography and at least one work, generated every month, with indexes and a sitemap. An English version also exists (`/en/author/…`).
- **Italian (`/`) and English (`/en/`)**, plus search, filters, «My list» (favourites saved in the browser) and an Excel export (CSV) with the columns of the chosen country's catalogue.

## How it works

Every month `.github/workflows/aggiorna.yml` runs these steps, in order:

| Script | What it does |
|---|---|
| `aggiorna.py` | Downloads from Wikidata the writers, poets and playwrights who died in the right year: one file per year and rule (`data/2027.json`, `data/es-2027.json`). |
| `arricchisci.py` | Adds the biography (Wikipedia), works and genres (Wikidata), Wikipedia views for the last 12 months in 5 languages, 0-100 indexes, and a Wikimedia Commons portrait with its licence. |
| `sbn.py` · `riconosci_sbn.py` | Records in Italian in the SBN catalogue (ICCU SPARQL). |
| `bnf.py` | Records in French in the BnF (SRU). |
| `alma.py` · `voce_alma.py` | Records in Spanish in the BNE and in English in the British Library (Alma SRU). |
| `loc.py` | Records in English in the Library of Congress (SRU and id.loc.gov). |
| `opere.py` | Works that become free in the USA. |
| `verifica.py` | Second source for the year of death (GND, Library of Congress, sources cited in Wikidata). |
| `controlli.py` | Suspends contradictory counts and those flagged by hand in `data/sospesi_manuali.json`. |
| `pagine.py` | Generates the author pages, the indexes and `sitemap.xml`. |

`index.html` is the site: one file, no framework. If the workflow runs out of time, it saves what it has done and restarts by itself from where it stopped. Downloaded data stays in cache (`data/cache_*.json`).

### Everything from open sources, nothing from memory

The sources are Wikidata (CC0), Wikipedia and the Wikimedia APIs (text CC BY-SA, always linked to the original page), Wikimedia Commons, Project Gutenberg, and the SBN, BnF, BNE, British Library and Library of Congress catalogues. Legal rules are read from the official texts and cited on the site with the article number.

## How errors are avoided

Linking an author to a namesake's record is the most serious error, because it produces false figures. The method used, documented with all the tests in [`docs/registro-prove.md`](docs/registro-prove.md), is this:

1. **Identifier first, name second.** If Wikidata gives the author's identifier in the catalogue, only that is used.
2. **A name only with evidence.** The name is normalised on both sides (accents, particles, initials, East Asian order), and a record is accepted only if the years of birth and death also match, or a title. Without evidence the author stays «ambiguous» and nothing is counted.
3. **Only what belongs to the person counts.** In the British Library and the BNE a record counts only if surname and years are in the same author heading. In the Library of Congress it counts only if the heading is identical to the official one and the author appears as author or contributor, not as subject.
4. **Every rule is measured before release:** a development sample, then frozen rules, then a new sample of authors never seen before, judged by hand before the measurement. If a rule changes after the measurement, a new check is needed. Zero errors in a sample does not mean zero errors on the site.
5. **Ongoing checks:** inconsistent counts (for example more recent records than total records) are suspended and the site shows «Data under review». Well-known authors have expected minimum counts, and doubtful links can be suspended by hand.

## Term rules

The EU baseline is death + 70 years, from 1 January of the following year (Directive 2006/116/EC, Arts. 1 and 10). National rules are read from the official texts:

- **Germany**: UrhG §64 and §69, no extension.
- **France**: CPI L123-1. According to the Court of Cassation (2007), the wartime extensions L123-8/9 are included in the 70 years; authors who «died for France» get 30 more years (L123-10).
- **Italy**: Law 633/1941, Arts. 25 and 32-ter. The 6-year extension of Legislative Decree 440/1945 was repealed by Law 52/1996, Art. 17. For authors from Allied countries the 1947 Peace Treaty, Annex XV, applies, to be checked case by case.
- **Spain**: TRLPI Arts. 26 and 30, fourth transitional provision. For authors who died before 7 December 1987 the 1879 law applies (80 years).
- **UK**: CDPA 1988, section 12.
- **USA**: 17 U.S.C. § 304, 95 years from publication for works published before 1978, with the exceptions of non-renewal and § 104A.

**Not yet verified**, and stated as such on the site:
- how Spain counts the expiry year (the date shown is cautious);
- whether the 30 years for those who «died for France» are added to the 70;
- the exact length of the Peace Treaty extension for each Allied country.

Other EU countries are not covered.

## Limits to know

- The calculation is indicative and **not legal advice**: check the law of your country before publishing.
- The public domain concerns the original work. A modern translation or a critical edition may have rights of its own.
- Catalogues reflect how libraries recorded the books. An author recorded under another form of the name may be missed, so «no linked record» does not mean «unpublished».
- Online interest is a hint, not a measure of sales.

## Running it by hand

On GitHub: **Actions → Aggiorna autori in pubblico dominio → Run workflow**. To put it online: **Settings → Pages → Deploy from a branch → `main` / root**.
