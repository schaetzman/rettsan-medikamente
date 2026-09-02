# Wirkstoff-Trainer (rettsan-medikamente)

Single-File-PWA zum Üben der Notfallmedikamente der hessischen Algorithmen
(V 4.2, Stand 04.12.2025) — Teil 2: M 1–M 26 plus die Analgetika-Übersichtsblätter
M 27 (Risikoprofile) und M 28 (Dosierung/Applikation).

- Live: https://medikamententrainer.netlify.app
- Deploy: Push auf `main` → Netlify baut automatisch (kein Build-Schritt, statisch).
- Struktur flach: `index.html`, `manifest.webmanifest`, `service-worker.js`, `netlify.toml`, `icons/`.
- Lokal ansehen: `python3 serve.py` (schickt `no-store`) — startet im aktuellen Verzeichnis,
  also vorher hierher wechseln.

## Spritzenetiketten: Daten kommen aus dem Rechentrainer

Die Zubereitungs- und Konzentrationsangaben stehen **nicht** in dieser App, sondern in
`~/rettsan-rechentrainer`. Der Block `ZUB` in `index.html` ist erzeugt:

```bash
python3 zieh-zubereitung.py          # schreibt den Block neu
python3 zieh-zubereitung.py --probe  # zeigt nur, ob sich etwas aendern wuerde
```

Wenn sich im Rechentrainer eine Ampullenstaerke aendert, hier einmal das Skript laufen lassen —
nichts abtippen. Der Reiter Rahmen zeigt, wie viele Wirkstoffe eine Zubereitung haben; faellt die
Zahl nach einem Lauf, hat der Rechentrainer etwas umbenannt.

Lernhilfe, keine Handlungsanweisung — verbindlich ist die SAA des ÄLRD.
