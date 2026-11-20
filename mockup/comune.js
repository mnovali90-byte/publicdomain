/* Dati condivisi dei tre mockup: stessi file e stessa classifica del sito. */
const PAESI = [
  { id: "it", nome: "Italia", file: "2027.json", idx: "indice_it", vis: "visite_it", lingua: "italiano", regola: "In Italia le opere diventano libere 70 anni dopo la morte dell'autore." },
  { id: "fr", nome: "Francia", file: "2027.json", idx: "indice_fr", vis: "visite_fr", lingua: "francese", regola: "In Francia 70 anni dopo la morte, con 30 anni in più per i «morti per la Francia»." },
  { id: "de", nome: "Germania", file: "2027.json", idx: "indice_de", vis: "visite_de", lingua: "tedesco", regola: "In Germania le opere diventano libere 70 anni dopo la morte dell'autore." },
  { id: "es", nome: "Spagna", file: "es-2027.json", idx: "indice_es", vis: "visite_es", lingua: "spagnolo", regola: "In Spagna 80 anni dopo la morte per chi è morto prima del 1987: nel 2027 si liberano i morti del 1946." },
  { id: "uk", nome: "Regno Unito", file: "2027.json", idx: "indice_en", vis: "visite_en", lingua: "inglese", regola: "Nel Regno Unito le opere diventano libere 70 anni dopo la morte dell'autore." }
];
const MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"];
const cache = {};
let fuori = null;

async function json(url) { const r = await fetch(url, { cache: "no-cache" }); return r.json(); }

async function carica(id) {
  const p = PAESI.find((x) => x.id === id) || PAESI[0];
  if (!fuori) {
    try { fuori = new Set((await json("../data/fuori_classifica.json")).autori.map((a) => a.wikidata)); }
    catch (e) { fuori = new Set(); }
  }
  if (!cache[p.file]) cache[p.file] = await json("../data/" + p.file);
  const d = cache[p.file];
  const autori = d.autori
    .filter((a) => a.letterario === true && !/^Q\d+$/.test(a.nome) && !fuori.has(a.wikidata) && !a.fuori_classifica)
    .slice()
    .sort((x, y) => ((y[p.idx] || 0) - (x[p.idx] || 0)) || ((+y[p.vis] || 0) - (+x[p.vis] || 0)) || ((+y.pagine_wikipedia || 0) - (+x.pagine_wikipedia || 0)));
  return { paese: p, liberoDal: d.libero_dal, anno: +String(d.libero_dal).slice(0, 4), autori };
}

const fotoUrl = (a, w) => (a.foto && a.foto.url ? a.foto.url.replace(/width=\d+/, "width=" + w) : "");
const credito = (a) => (a.foto ? [a.foto.autore, a.foto.licenza].filter(Boolean).join(", ") : "");
const iniziali = (nome) => nome.split(/\s+/).filter((w) => /^\p{Lu}/u.test(w)).map((w) => w[0]).slice(0, 2).join("");
const anno = (s) => String(s || "").slice(0, 4);
function dataLunga(s) {
  const [y, m, g] = String(s).split("-");
  if (!m || (m === "01" && g === "01")) return y;   // date note solo per anno
  return +g + " " + MESI[+m - 1] + " " + y;
}
function giorniA(liberoDal) {
  const ms = new Date(liberoDal + "T00:00:00") - new Date();
  return Math.max(0, Math.ceil(ms / 86400000));
}
const num = (n) => Number(n || 0).toLocaleString("it-IT");
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const lista = (v) => (Array.isArray(v) ? v : []);
