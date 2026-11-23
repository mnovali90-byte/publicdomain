/* SCRITTO DA scripts/regole.py (esporta_js): non modificare a mano. Regole per paese del sito, in un posto solo. */
window.REGOLE_PAESI = (() => {
  const C = {"ANNI_DOPO_MORTE": 70, "SPAGNA_80_FINO_AL": 1987, "SPAGNA_ANNI_VECCHI": 80, "MPF_ANNI_IN_PIU": 30, "USA_ANNI": 95, "PROROGA_ALLEATI": 8, "ALLEATI_OPERE_FINO_AL": 1940, "PAESI_70": ["it", "fr", "de", "uk"], "ALLEATI_1947": ["Albania", "Armenia", "Armenian Soviet Socialist Republic", "Australia", "Azerbaigian", "Azerbaijan Soviet Socialist Republic", "Bangladesh", "Belgio", "Belgium", "Bielorussia", "Brasile", "Brazil", "British Raj", "Byelorussian Soviet Socialist Republic", "Canada", "Cecoslovacchia", "China", "Cina", "Czechoslovakia", "Dominion dell'India", "Dominion of India", "Ethiopia", "Ethiopian Empire", "Etiopia", "Federal People's Republic of Yugoslavia", "First Czechoslovak Republic", "France", "Francia", "French Third Republic", "Galles", "Georgia", "Georgian Soviet Socialist Republic", "Grecia", "Greece", "Impero anglo-indiano", "Impero d'Etiopia", "Impero russo", "India", "Jugoslavia", "Kazakistan", "Kingdom of England", "Kingdom of Greece", "Kingdom of Serbs, Croats and Slovenes", "Kingdom of Yugoslavia", "Kingdom of the Netherlands", "Netherlands", "New Zealand", "Nuova Zelanda", "Paesi Bassi", "Pakistan", "Poland", "Polish People's Republic", "Polonia", "Prima Repubblica cecoslovacca", "RSS Bielorussa", "RSS Ucraina", "Regno Unito", "Regno Unito di Gran Bretagna e Irlanda", "Regno d'Inghilterra", "Regno dei Paesi Bassi", "Regno dei Serbi, Croati e Sloveni", "Regno di Grecia", "Regno di Jugoslavia", "Repubblica Ceca", "Repubblica Popolare di Polonia", "Repubblica Socialista Cecoslovacca", "Repubblica Socialista Federale di Jugoslavia", "Repubblica Socialista Federativa Sovietica Russa", "Repubblica Socialista Sovietica Georgiana", "Repubblica di Cina", "Repubblica federale popolare di Jugoslavia", "Republic of China", "Republic of China (1912–1949)", "Russia", "Russia sovietica", "Russian Empire", "Russian Soviet Federative Socialist Republic", "Scotland", "Scozia", "Second Polish Republic", "Seconda Repubblica di Polonia", "Serbia", "Socialist Federal Republic of Yugoslavia", "South Africa", "Soviet Union", "Stati Uniti", "Sudafrica", "Ucraina", "Ukrainian Soviet Socialist Republic", "Union of South Africa", "Unione Sovietica", "Unione Sudafricana", "United Kingdom", "United Kingdom of Great Britain and Ireland", "United States", "United States of America", "Uzbekistan", "Wales", "Yugoslavia"], "OPERA_VECCHIA_ANNI": 170, "OPERA_VECCHIA_ANNI_ES": 180, "ANNO_DATI_PRIMA_MORTE": 90, "ANNO_DATI_DOPO_MORTE": 150, "USA_NOTA_RECENTE": 10, "UK_LEGGE_1988": 1989, "UK_MORTI_PRIMA_DEL": 1969, "UK_2039_LIBERO": 2040, "UK_POSTUME_ANNI": 50, "FR_GUERRA": [1939, 1945], "FESTA_FINO_AL": 6};
  const ALLEATI = new Set(C.ALLEATI_1947);
  const anniProtezione = (morte, paese) => (paese === "es" && morte <= C.SPAGNA_80_FINO_AL ? C.SPAGNA_ANNI_VECCHI : C.ANNI_DOPO_MORTE);
  const annoLibero = (morte, paese, mpf) => morte + anniProtezione(morte, paese) + (paese === "fr" && mpf ? C.MPF_ANNI_IN_PIU : 0) + 1;
  const mortiLiberiNel = (anno, paese) => (paese === "es" && anno - C.SPAGNA_ANNI_VECCHI - 1 <= C.SPAGNA_80_FINO_AL ? anno - C.SPAGNA_ANNI_VECCHI - 1 : anno - C.ANNI_DOPO_MORTE - 1);
  const annoLiberoUsa = (pub) => pub + C.USA_ANNI + 1;
  const pubblicateLibereUsaNel = (anno) => anno - C.USA_ANNI - 1;
  const paesiAlleati = (paesi) => (paesi || []).filter((p) => ALLEATI.has(p));
  const notaTrattatoFlag = (alleato, morte, oggiAnno, annoOpera) => {
    if (morte === null || morte === undefined || !alleato) return false;
    if (annoOpera !== null && annoOpera !== undefined && annoOpera > C.ALLEATI_OPERE_FINO_AL) return false;
    return annoLibero(morte, "it") + C.PROROGA_ALLEATI > oggiAnno;
  };
  const notaTrattato = (paesi, morte, oggiAnno, annoOpera) => notaTrattatoFlag(paesiAlleati(paesi).length > 0, morte, oggiAnno, annoOpera);
  // ---- regole per opera: gemelle di stato_opera, libera_ue_opera, anno_opera_credibile in scripts/regole.py ----
  const vecchio = (x, oggi, paese) => x <= oggi - (paese === "es" ? C.OPERA_VECCHIA_ANNI_ES : C.OPERA_VECCHIA_ANNI) - 1;
  const nn = (v) => v !== null && v !== undefined;
  const annoDeciso = (q, y, decise) => {
    const d = (decise || {})[q];
    return d && d.tipo === "uscita" && Number.isInteger(d.anno) ? d.anno : y;
  };
  const annoOperaCredibile = (y, au) => {
    if (!nn(y)) return null;
    const morti = au.filter((a) => !a.an && nn(a.m)).map((a) => a.m);
    if (morti.length && morti.length === au.length && y < Math.min(...morti) - C.ANNO_DATI_PRIMA_MORTE) return null;
    if (morti.length && au.every((a) => a.an || (nn(a.m) && y > a.m + C.ANNO_DATI_DOPO_MORTE))) return null;
    return y;
  };
  const liberaUeOpera = (o, oggi) => {
    if (o.antica) return true;
    if (nn(o.y) && vecchio(o.y, oggi)) return true;
    return o.au.length > 0 && o.au.every((a) => a.an || (!a.sc && a.inc !== 2 && nn(a.m) && annoLibero(a.m, "it") <= oggi));
  };
  // gemella di fase_sito: d è una Date del browser (ora locale)
  const faseSito = (d) => {
    const m = d.getMonth() + 1, g = d.getDate(), y = d.getFullYear();
    if (m === 12 && g === 31) return ["vigilia", y + 1];
    if (m === 1 && g <= C.FESTA_FINO_AL) return ["festa", y];
    return ["conto", y + 1];
  };
  const statoOpera = (o, c, oggi, mpf, verifiche) => {
    const Y = oggi, note = [], au = o.au || [];
    let y = nn(o.y) ? o.y : null;
    if (o.antica && o.antica !== "anonima") return { s: "si", note: ["sAntica_antica"], r: "antico" };
    if (o.antica === "anonima" && c !== "us" && y !== null) {
      const fine = y + (c === "es" ? C.SPAGNA_ANNI_VECCHI : C.ANNI_DOPO_MORTE) + 1;
      return fine <= Y ? { s: "si", note: ["sAntica_anonima"], r: "anonima" } : { s: "dal", y: fine, note: ["sAntica_anonima"], r: "anonima" };
    }
    if (au.some((a) => a.inc)) note.push("sInc");
    if (c === "us") {
      if (o.yd) note.push("sDuke");
      // 23/11/2026: senza anno su Wikidata, vale l'anno confermato dal registro USA (gemella di stato_opera)
      if (y === null && ((verifiche || {})[o.q] || [null])[0] != null) y = verifiche[o.q][0];
      { const _v = (verifiche || {})[o.q] || [null]; if (y !== null && _v[0] != null && _v[0] < y && _v.length > 4 && _v[4]) y = _v[0]; }
      if (y !== null) {
        if (annoLiberoUsa(y) <= Y && !liberaUeOpera(o, Y)) {
          const v = (verifiche || {})[o.q];
          if (v && v[0] !== null && v[0] > pubblicateLibereUsaNel(Y)) return { s: "dal", y: annoLiberoUsa(v[0]), note, r: "usa_edizione_confermata" };
          if (!v || v[0] === null) return { s: "ver", note: note.concat([v && v[2] ? "sUsNo" : "sUsNd"]), y2: v ? (nn(v[3]) ? v[3] : null) : null, r: "usa_seconda_fonte_mancante" };
        }
        if (annoLiberoUsa(y) <= Y) { if (annoLiberoUsa(y) >= Y - C.USA_NOTA_RECENTE) note.push("sUsPrima"); return { s: "si", note, r: "usa_95_anni" }; }
        return { s: "dal", y: annoLiberoUsa(y), note, r: "usa_95_anni" };
      }
      if (au.length && au.every((a) => a.an || (nn(a.m) && vecchio(a.m, Y)))) return { s: "si", senza: true, note, r: "usa_autori_antichi" };
      return { s: "nd", note, r: "usa_anno_mancante" };
    }
    if (y !== null && vecchio(y, Y, c)) return { s: "si", note, r: "uscita_oltre_170_anni" };
    if (!au.length) return { s: "nd", note, r: "autori_mancanti" };
    let fine = 0, dubbio = false;
    for (const a of au) {
      if (a.an) continue;
      if (a.sc) { dubbio = true; continue; }
      if (!nn(a.m)) return { s: "nd", note, r: "morte_mancante" };
      fine = Math.max(fine, annoLibero(a.m, c, false));
    }
    if (c === "uk" && y !== null && y >= C.UK_LEGGE_1988) {
      const morti = au.filter((a) => !a.an && !a.sc && nn(a.m)).map((a) => a.m);
      if (morti.length && y > Math.max(...morti) && Math.max(...morti) < C.UK_MORTI_PRIMA_DEL && fine < C.UK_2039_LIBERO) { fine = C.UK_2039_LIBERO; note.push("sUk2039"); }
    }
    if (fine > Y) return { s: "dal", y: fine, note, r: note.includes("sUk2039") ? "uk_2039" : "morte" };
    if (dubbio) return { s: "ver", note: note.concat(["sCoaut"]), r: "coautore_senza_data" };
    if (c !== "es" && au.some((a) => a.inc === 2)) return { s: "ver", note: note.filter((k) => k !== "sInc").concat(["sConfine"]), r: "morte_incerta_sul_confine" };
    if (c === "uk") {
      const morti = au.filter((a) => !a.an).map((a) => a.m);
      if (morti.length) {
        const ultima = Math.max(...morti);
        if (y !== null && y > ultima) {
          if (y < C.UK_LEGGE_1988 && y + C.UK_POSTUME_ANNI + 1 > Y) return { s: "ver", note: note.concat(["sUkPostumo"]), r: "uk_postuma" };
        }
        if (y === null && ultima < C.UK_MORTI_PRIMA_DEL) note.push("sUkNd");
      }
    }
    if (c === "it" && au.some((a) => !a.an && notaTrattatoFlag(a.al, a.m, Y, y))) note.push("sAlleato");
    const haMpf = (q) => (mpf && (mpf.has ? mpf.has(q) : mpf.includes(q)));
    if (c === "fr" && au.some((a) => !a.an && haMpf(a.q) && annoLibero(a.m, "fr", true) > Y)) return { s: "ver", note: note.concat(["sMpf"]), r: "fr_morto_per_la_francia" };
    if (c === "fr" && au.some((a) => !a.an && a.m >= C.FR_GUERRA[0] && a.m <= C.FR_GUERRA[1] && annoLibero(a.m, "fr", true) > Y)) note.push("sFr");
    return { s: "si", note, r: note.includes("sUk2039") ? "uk_2039" : "morte" };
  };
  const autoreConNome = (nome) => typeof nome === "string" && nome.trim() !== "" && !/^Q\d+$/.test(nome.trim());
  return Object.assign({}, C, { autoreConNome, anniProtezione, annoLibero, mortiLiberiNel, annoLiberoUsa, pubblicateLibereUsaNel, paesiAlleati,
    notaTrattatoFlag, notaTrattato, statoOpera, liberaUeOpera, annoOperaCredibile, annoDeciso, faseSito });
})();
