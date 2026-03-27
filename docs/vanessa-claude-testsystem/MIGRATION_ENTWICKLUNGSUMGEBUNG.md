# DRIVE Migration: Neue Entwicklungsumgebung

```mermaid
flowchart TB
    %% =========================
    %% IST -> SOLL
    %% =========================
    A[Vorher: /test Prefix fragil<br/>Redirects teils in Prod] --> B[Ziel: Stabile Develop-Umgebung]
    B --> C[Develop URL: http://drive:5002]
    B --> D[Prod URL: http://drive]
    B --> E[Klare Rollen + Tooling + Git-Flow]

    %% =========================
    %% UMGEBUNGEN
    %% =========================
    subgraph ENV[Umgebungen]
      P1[Produktion<br/>Code: /opt/greiner-portal<br/>Service: greiner-portal<br/>URL: drive]
      D1[Develop/Test<br/>Code: /data/greiner-test<br/>Service: greiner-test<br/>URL: drive:5002]
    end

    %% =========================
    %% PERSONEN
    %% =========================
    subgraph ROLES[Rollen]
      F[Florian<br/>arbeitet in Prod + Develop]
      V[Vanessa<br/>arbeitet nur in Develop]
    end

    F --> P1
    F --> D1
    V --> D1

    %% =========================
    %% ZUGRIFF / SICHERHEIT
    %% =========================
    subgraph ACCESS[Zugriff & Sicherheit]
      U1[Linux User: vanessa-dev]
      U2[SSH Key Login only]
      U3[Workspace fix: /data/greiner-test]
      U4[TESTSYSTEM Badge sichtbar]
    end

    V --> U1 --> U2 --> U3
    U3 --> D1
    D1 --> U4

    %% =========================
    %% TOOLS
    %% =========================
    subgraph TOOLS[Tooling]
      T1[Cursor: primär entwickeln]
      T2[Claude Code Desktop: punktuell]
      T3[Context7: externe Tech-Doku]
      T4[Interne SSOT: docs/workstreams/*/CONTEXT.md]
      T5[Prompts/Runbooks: docs/vanessa-claude-testsystem]
    end

    V --> T1
    V --> T2
    F --> T1
    F --> T2
    T3 --> T4
    T5 --> T4

    %% =========================
    %% GIT / GITHUB
    %% =========================
    subgraph GIT[Git / GitHub Flow]
      G1[feature/*]
      G2[develop]
      G3[main]
      G4[PR + Review + Testplan]
    end

    G1 --> G2 --> G3
    G4 --> G2
    G4 --> G3

    D1 --> G1
    F --> G4

    %% =========================
    %% RISIKEN / GATES
    %% =========================
    subgraph QUALITY[Qualitäts-Gates]
      Q1[Session-End:<br/>CONTEXT.md aktualisieren]
      Q2[Hilfe-Registry Check]
      Q3[Service-Restart bei Backend-Changes]
      Q4[Keine direkten Prod-Änderungen durch Vanessa]
    end

    D1 --> Q1 --> Q2 --> Q3 --> G4
    V --> Q4
```

## Kurzfassung fuer Besprechung mit Vanessa

- Wir entwickeln stabil auf `http://drive:5002` statt mit `/test`-Prefix.
- Vanessa arbeitet nur in `/data/greiner-test` mit `vanessa-dev`.
- Cursor ist das Haupttool, Claude nur ergänzend.
- Fachliche Wahrheit bleibt in `docs/workstreams/*/CONTEXT.md`.
- Git-Fluss: `feature/* -> develop -> main` mit Review-Gate.

