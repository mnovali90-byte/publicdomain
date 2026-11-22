#!/usr/bin/env bash
# SALVATAGGIO UNICO DI TUTTI I GIRI (22/11/2026, passo 4 di docs/giri-automatici.md; audit esterno, punti P1).
# Uso, dopo «git add» dei file da salvare:   bash scripts/salva.sh "messaggio del salvataggio"
# - Niente «-X theirs»: prima, se un altro giro aveva cambiato gli stessi file nel frattempo, vincevano a occhi chiusi i dati
#   di chi salvava per ultimo. Ora il giro si ferma ROSSO e non pubblica niente: meglio fermi che dati mescolati.
# - Se GitHub rifiuta l'invio si riprova fino a 5 volte; se fallisce sempre, il giro finisce ROSSO (prima restava verde).
set -u
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
if git diff --cached --quiet; then
  echo "Nessun cambiamento da salvare"
  exit 0
fi
git commit -q -m "$1"
for i in 1 2 3 4 5; do
  if ! git pull --rebase --autostash origin main; then
    git rebase --abort 2>/dev/null || true
    echo "CONFLITTO: un altro giro ha cambiato gli stessi file nel frattempo. Niente pubblicato."
    exit 1
  fi
  if git push; then
    echo "Pubblicato"
    exit 0
  fi
  echo "Invio rifiutato da GitHub (tentativo $i), riprovo tra $((i * 20)) secondi"
  sleep $((i * 20))
done
echo "Invio fallito 5 volte: niente pubblicato"
exit 1
