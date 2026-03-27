# Prompts fuer Claude (Vanessa)

## 1) Session-Start (sicher)

```text
Arbeite nur im Testsystem.
Pfad: /data/greiner-test
Browser-URL: http://drive/test
Wenn TESTSYSTEM-Badge fehlt, sofort stoppen und mich informieren.
Fasse diese Regeln zuerst kurz zusammen und starte dann mit dem ersten kleinen Schritt.
```

## 2) Kleine UI-Aenderung

```text
Ich moechte nur eine kleine UI-Aenderung.
Bitte aendere nur templates/, static/css/ oder static/js/.
Zeige mir vor der Aenderung in 3 Punkten:
1) was du aenderst
2) welche Dateien
3) wie ich es in http://drive/test pruefe
```

## 3) Redesign aus Mockup

```text
Ich gebe dir gleich ein Mockup-Ziel.
Bitte setze es in kleinen Schritten um und halte bestehende Rechte-/Feature-Logik unveraendert.
Keine Produktivpfade, keine Deploys.
Nach jedem Schritt: kurze Testanleitung fuer drive/test.
```

## 4) Nur Analyse, kein Edit

```text
Bitte nur analysieren, nichts aendern.
Nenne mir:
1) welche Dateien betroffen waeren
2) Risiken fuer Rechte/Navigation
3) kleinstmoeglichen sicheren Umsetzungsplan im Testsystem
```

## 5) Abgabe-Format

```text
Gib das Ergebnis bitte in diesem Format:
- Geaenderte Dateien
- Was wurde verbessert
- Wie getestet (drive/test)
- Offene Punkte
```
