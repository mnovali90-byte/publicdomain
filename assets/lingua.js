/* Barra sulle pagine italiane: «This page is available in English».
   Solo se la prima lingua del browser non è l'italiano e la pagina ha l'alternativa EN
   (link rel=alternate hreflang=en). Nessun rimando automatico. La chiusura resta in localStorage.
   Incluso solo dalle pagine italiane: la copia inglese (crea_home_inglese) toglie questo file. */
(function () {
  if (document.documentElement.lang === "en") return;
  var path = location.pathname;
  if (path === "/en" || path.indexOf("/en/") === 0) return;

  var link = document.querySelector('link[rel="alternate"][hreflang="en"]');
  var href = link && link.getAttribute("href");
  if (!href) return;

  /* Sulle pagine copiate dal radar c'è già un invito in fondo (#invito-en). Lo tiene chiuso questa barra. */
  var vecchio = document.getElementById("invito-en");
  if (vecchio) {
    vecchio.hidden = true;
    new MutationObserver(function () {
      if (!vecchio.hidden) vecchio.hidden = true;
    }).observe(vecchio, { attributes: true, attributeFilter: ["hidden"] });
  }

  var KEY = "pdr-avviso-en";
  try {
    if (localStorage.getItem(KEY) === "1") return;
  } catch (e) { /* localStorage bloccato: la barra si può mostrare lo stesso */ }

  var lingue = (navigator.languages && navigator.languages.length) ? navigator.languages : [navigator.language || ""];
  var prima = String(lingue[0] || "").toLowerCase();
  if (prima === "it" || prima.indexOf("it-") === 0) return;

  var css = document.createElement("style");
  css.textContent = "#pdr-lingua{position:fixed;top:var(--top,64px);left:0;right:0;z-index:35;display:flex;align-items:center;justify-content:center;gap:18px;min-height:32px;padding:8px var(--pad,48px);background:var(--ink);color:var(--paper);font-family:var(--mono),'DM Mono',ui-monospace,monospace;font-size:12px;letter-spacing:.12em;text-transform:uppercase;line-height:1.35}"
    + "#pdr-lingua a{color:inherit;text-decoration:none;border-bottom:2px solid var(--red);padding-bottom:1px}"
    + "#pdr-lingua a:hover,#pdr-lingua button:hover{color:var(--red)}"
    + "#pdr-lingua button{flex:none;font-family:var(--mono),'DM Mono',ui-monospace,monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--paper);background:transparent;border:0;padding:4px 0;cursor:pointer}"
    + "@media (max-width:860px){#pdr-lingua{font-size:11px;letter-spacing:.06em;padding:8px 16px;gap:12px}}";
  document.head.appendChild(css);

  var bar = document.createElement("div");
  bar.id = "pdr-lingua";
  bar.setAttribute("role", "region");
  bar.setAttribute("aria-label", "English version");
  var a = document.createElement("a");
  a.href = href;
  a.hreflang = "en";
  a.lang = "en";
  a.textContent = "This page is available in English";
  var btn = document.createElement("button");
  btn.type = "button";
  btn.setAttribute("aria-label", "Dismiss");
  btn.textContent = "Close";
  btn.addEventListener("click", function () {
    try { localStorage.setItem(KEY, "1"); } catch (e) {}
    bar.remove();
  });
  bar.appendChild(a);
  bar.appendChild(btn);
  document.body.appendChild(bar);
})();
