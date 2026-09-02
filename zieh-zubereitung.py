#!/usr/bin/env python3
"""Zieht die Zubereitungsdaten aus dem Rechentrainer in diese App.

Warum es dieses Skript gibt
---------------------------
Der Wirkstoff-Trainer fuehrt Wirkung, Indikation, Dosis und Cave -- aber keine
Zubereitung und keine Konzentration. Genau die braucht das Spritzenetikett.
Die Zahlen stehen im Rechentrainer (~/rettsan-rechentrainer) und in QRH Med.

Sie hier **abzutippen** waere die dritte Kopie derselben Tabelle. Als am
01.09.2026 eine einzige Ampullenstaerke wechselte (Esketamin 50 mg / 5 ml),
mussten schon zwei Apps und zwei Generatorskripte nachgezogen werden. Deshalb:
erzeugen statt tippen.

Aufruf
------
    python3 zieh-zubereitung.py            # schreibt index.html neu
    python3 zieh-zubereitung.py --probe    # zeigt nur, was sich aendern wuerde

Was passiert
------------
1. `const DRUGS = [...]` wird aus dem index.html des Rechentrainers geschnitten
   (Klammern werden gezaehlt, nicht per Regex geraten).
2. node wandelt das JS-Literal in JSON -- es ist kein JSON: unquotierte
   Schluessel, einfache Anfuehrungszeichen, Kommentare.
3. Aus jedem Eintrag wird genommen, was das Etikett braucht. Nichts wird
   umgerechnet und nichts ergaenzt; was der Rechentrainer nicht weiss,
   weiss diese App auch nicht.
4. Der Block zwischen den beiden Markierungen in index.html wird ersetzt.

Der Zuordnungsschluessel ist die M-Nummer. Wirkstoffe ohne M-Nummer (die
Vollelektrolytloesung) haben keine Entsprechung und bekommen kein Etikett.

Nach jedem Lauf: die Selbstpruefung im Reiter Rahmen zeigt, wie viele
Wirkstoffe eine Zubereitung haben. Faellt die Zahl, hat der Rechentrainer
etwas umbenannt.
"""

import json
import os
import subprocess
import sys
import tempfile

QUELLE = os.path.expanduser('~/rettsan-rechentrainer/index.html')
ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
ANFANG = '/* === ZUBEREITUNG:ANFANG — erzeugt von zieh-zubereitung.py, nicht von Hand pflegen === */'
ENDE = '/* === ZUBEREITUNG:ENDE === */'

# Was das Etikett braucht. Alles andere aus dem Rechentrainer bleibt dort.
FELDER = ['name', 'form', 'prep', 'conc', 'concText', 'kind', 'anchor', 'stock',
          'infusion', 'orders', 'wholeAmp']


def schneide_literal(text, name):
    """Gibt das Array-Literal hinter `const <name> = ` zurueck, per Klammerzaehlung."""
    start = text.find('const %s = [' % name)
    if start < 0:
        raise SystemExit('Im Rechentrainer steht kein `const %s = [`. '
                         'Wurde es umbenannt?' % name)
    i = text.index('[', start)
    tiefe, j, in_str, quote, esc = 0, i, False, '', False
    while j < len(text):
        c = text[j]
        if in_str:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == quote:
                in_str = False
        elif c in '"\'':
            in_str, quote = True, c
        elif c == '[':
            tiefe += 1
        elif c == ']':
            tiefe -= 1
            if tiefe == 0:
                return text[i:j + 1]
        j += 1
    raise SystemExit('Das Literal %s hoert nicht auf -- Datei unvollstaendig?' % name)


def js_zu_json(literal):
    """node wandelt das JS-Literal in JSON. Reines Auswerten eines Literals,
    kein Code aus der Quelldatei wird ausgefuehrt."""
    with tempfile.NamedTemporaryFile('w', suffix='.mjs', delete=False,
                                     encoding='utf-8') as f:
        f.write('const A = %s;\nprocess.stdout.write(JSON.stringify(A));\n' % literal)
        pfad = f.name
    try:
        r = subprocess.run(['node', pfad], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit('node konnte das Literal nicht lesen:\n' + r.stderr.strip())
        return json.loads(r.stdout)
    except FileNotFoundError:
        raise SystemExit('node ist nicht installiert -- das Skript braucht es, '
                         'um das JS-Literal zu lesen.')
    finally:
        os.unlink(pfad)


def ampulle(d):
    """Was auf der Ampulle steht, als Zahl und als Text -- fuer den Vergleich
    mit der Konzentration in der Spritze."""
    if d.get('amp'):
        a = d['amp']
        return a['mg'] / a['ml'], a
    if d.get('ts'):
        t = d['ts']
        return None, t          # Trockensubstanz: die Flasche nennt keine Konzentration
    return None, None


def bauen():
    quelle = open(QUELLE, encoding='utf-8').read()
    drugs = js_zu_json(schneide_literal(quelle, 'DRUGS'))

    raus = {}
    for d in drugs:
        m = d.get('m')
        if not m or m == '—':
            continue
        e = {k: d[k] for k in FELDER if d.get(k) is not None}
        ampConc, amp = ampulle(d)
        if amp is not None:
            e['amp'] = amp
            if ampConc is not None:
                e['ampConc'] = ampConc
        if d.get('ts'):
            e['ts'] = True
        if d.get('forms'):
            e['forms'] = d['forms']
        raus[m] = e
    return raus, len(drugs)


def schreiben(daten, probe=False):
    ziel = open(ZIEL, encoding='utf-8').read()
    if ANFANG not in ziel or ENDE not in ziel:
        raise SystemExit('Die Markierungen fehlen in index.html -- '
                         'ZUBEREITUNG:ANFANG und ZUBEREITUNG:ENDE muessen drinstehen.')
    a = ziel.index(ANFANG)
    b = ziel.index(ENDE) + len(ENDE)
    neu = (ANFANG + '\n/* Quelle: ~/rettsan-rechentrainer/index.html · '
           'neu ziehen mit `python3 zieh-zubereitung.py` */\n'
           'const ZUB = ' + json.dumps(daten, ensure_ascii=False, sort_keys=False) + ';\n'
           + ENDE)
    if probe:
        alt = ziel[a:b]
        print('unveraendert' if alt == neu else
              'wuerde sich aendern: %d Zeichen alt, %d neu' % (len(alt), len(neu)))
        return
    open(ZIEL, 'w', encoding='utf-8').write(ziel[:a] + neu + ziel[b:])


if __name__ == '__main__':
    daten, gesamt = bauen()
    ohne = [m for m, e in daten.items() if not e.get('concText')]
    print('%d Wirkstoffe aus dem Rechentrainer gelesen, %d mit M-Nummer uebernommen.'
          % (gesamt, len(daten)))
    if ohne:
        print('ohne Konzentrationsangabe (bekommen ein offenes Feld): '
              + ', '.join(ohne))
    schreiben(daten, probe='--probe' in sys.argv)
