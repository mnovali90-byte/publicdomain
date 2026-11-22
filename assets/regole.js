/* SCRITTO DA scripts/regole.py (esporta_js): non modificare a mano. Regole per paese del sito, in un posto solo. */
window.REGOLE_PAESI = (() => {
  const C = {"ANNI_DOPO_MORTE": 70, "SPAGNA_80_FINO_AL": 1987, "SPAGNA_ANNI_VECCHI": 80, "MPF_ANNI_IN_PIU": 30, "USA_ANNI": 95, "PROROGA_ALLEATI": 8, "ALLEATI_OPERE_FINO_AL": 1947, "PAESI_70": ["it", "fr", "de", "uk"], "ALLEATI_1947": ["Albania", "Armenia", "Armenian Soviet Socialist Republic", "Australia", "Azerbaigian", "Azerbaijan Soviet Socialist Republic", "Bangladesh", "Belgio", "Belgium", "Bielorussia", "Brasile", "Brazil", "British Raj", "Byelorussian Soviet Socialist Republic", "Canada", "Cecoslovacchia", "China", "Cina", "Czechoslovakia", "Dominion dell'India", "Dominion of India", "Ethiopia", "Ethiopian Empire", "Etiopia", "Federal People's Republic of Yugoslavia", "First Czechoslovak Republic", "France", "Francia", "French Third Republic", "Galles", "Georgia", "Georgian Soviet Socialist Republic", "Grecia", "Greece", "Impero anglo-indiano", "Impero d'Etiopia", "Impero russo", "India", "Jugoslavia", "Kazakistan", "Kingdom of England", "Kingdom of Greece", "Kingdom of Serbs, Croats and Slovenes", "Kingdom of Yugoslavia", "Kingdom of the Netherlands", "Netherlands", "New Zealand", "Nuova Zelanda", "Paesi Bassi", "Pakistan", "Poland", "Polish People's Republic", "Polonia", "Prima Repubblica cecoslovacca", "RSS Bielorussa", "RSS Ucraina", "Regno Unito", "Regno Unito di Gran Bretagna e Irlanda", "Regno d'Inghilterra", "Regno dei Paesi Bassi", "Regno dei Serbi, Croati e Sloveni", "Regno di Grecia", "Regno di Jugoslavia", "Repubblica Ceca", "Repubblica Popolare di Polonia", "Repubblica Socialista Cecoslovacca", "Repubblica Socialista Federale di Jugoslavia", "Repubblica Socialista Federativa Sovietica Russa", "Repubblica Socialista Sovietica Georgiana", "Repubblica di Cina", "Repubblica federale popolare di Jugoslavia", "Republic of China", "Republic of China (1912–1949)", "Russia", "Russia sovietica", "Russian Empire", "Russian Soviet Federative Socialist Republic", "Scotland", "Scozia", "Second Polish Republic", "Seconda Repubblica di Polonia", "Serbia", "Socialist Federal Republic of Yugoslavia", "South Africa", "Soviet Union", "Stati Uniti", "Sudafrica", "Ucraina", "Ukrainian Soviet Socialist Republic", "Union of South Africa", "Unione Sovietica", "Unione Sudafricana", "United Kingdom", "United Kingdom of Great Britain and Ireland", "United States", "United States of America", "Uzbekistan", "Wales", "Yugoslavia"]};
  const ALLEATI = new Set(C.ALLEATI_1947);
  const anniProtezione = (morte, paese) => (paese === "es" && morte <= C.SPAGNA_80_FINO_AL ? C.SPAGNA_ANNI_VECCHI : C.ANNI_DOPO_MORTE);
  const annoLibero = (morte, paese, mpf) => morte + anniProtezione(morte, paese) + (paese === "fr" && mpf ? C.MPF_ANNI_IN_PIU : 0) + 1;
  const mortiLiberiNel = (anno, paese) => (paese === "es" && anno - C.SPAGNA_ANNI_VECCHI - 1 <= C.SPAGNA_80_FINO_AL ? anno - C.SPAGNA_ANNI_VECCHI - 1 : anno - C.ANNI_DOPO_MORTE - 1);
  const annoLiberoUsa = (pub) => pub + C.USA_ANNI + 1;
  const pubblicateLibereUsaNel = (anno) => anno - C.USA_ANNI - 1;
  const paesiAlleati = (paesi) => (paesi || []).filter((p) => ALLEATI.has(p));
  const alleatoOIgnoto = (paesi) => !paesi || !paesi.length || paesiAlleati(paesi).length > 0;
  const italiaDaVerificareFlag = (flag, morte, oggiAnno, annoOpera) => {
    if (morte === null || morte === undefined || !flag) return false;
    if (annoOpera !== null && annoOpera !== undefined && annoOpera > C.ALLEATI_OPERE_FINO_AL) return false;
    return annoLibero(morte, "it") + C.PROROGA_ALLEATI > oggiAnno;
  };
  const italiaDaVerificare = (paesi, morte, oggiAnno, annoOpera) => italiaDaVerificareFlag(alleatoOIgnoto(paesi), morte, oggiAnno, annoOpera);
  return Object.assign({}, C, { anniProtezione, annoLibero, mortiLiberiNel, annoLiberoUsa, pubblicateLibereUsaNel, paesiAlleati,
    alleatoOIgnoto, italiaDaVerificareFlag, italiaDaVerificare });
})();
