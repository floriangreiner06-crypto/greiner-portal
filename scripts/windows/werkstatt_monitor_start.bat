@echo off
REM ============================================================================
REM WERKSTATT MONITOR - 3-Split Kiosk Mode
REM ============================================================================
REM Startet 3 Chrome-Fenster nebeneinander:
REM   Links:  Werkstattplanung View 40
REM   Mitte:  Werkstattplanung View 41
REM   Rechts: Stempeluhr LIVE
REM
REM ANPASSUNG: Bildschirmaufloesung unten einstellen!
REM ============================================================================

REM --- KONFIGURATION ---
SET SCREEN_WIDTH=1920
SET SCREEN_HEIGHT=1080

REM URLs
SET URL1=https://werkstattplanung.net/greiner/deggendorf/kic/da/#/views/40
SET URL2=https://werkstattplanung.net/greiner/deggendorf/kic/da/#/views/41
SET URL3=http://10.80.80.20/monitor/stempeluhr?token=Greiner2024Werkstatt!

REM Chrome Pfad (Standard)
SET CHROME="C:\Program Files\Google\Chrome\Application\chrome.exe"

REM Berechne Fensterbreite (1/3 des Bildschirms)
SET /A WINDOW_WIDTH=%SCREEN_WIDTH% / 3
SET /A POS_LEFT=0
SET /A POS_MIDDLE=%WINDOW_WIDTH%
SET /A POS_RIGHT=%WINDOW_WIDTH% * 2

REM --- ALTE CHROME INSTANZEN BEENDEN ---
echo Beende alte Chrome-Instanzen...
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 2 >nul

REM --- CHROME FENSTER STARTEN ---
echo Starte Werkstatt-Monitor...

REM Fenster 1 - Links (Werkstattplanung View 40)
start "" %CHROME% --new-window --window-position=%POS_LEFT%,0 --window-size=%WINDOW_WIDTH%,%SCREEN_HEIGHT% --app="%URL1%"
timeout /t 1 >nul

REM Fenster 2 - Mitte (Werkstattplanung View 41)
start "" %CHROME% --new-window --window-position=%POS_MIDDLE%,0 --window-size=%WINDOW_WIDTH%,%SCREEN_HEIGHT% --app="%URL2%"
timeout /t 1 >nul

REM Fenster 3 - Rechts (Stempeluhr LIVE)
start "" %CHROME% --new-window --window-position=%POS_RIGHT%,0 --window-size=%WINDOW_WIDTH%,%SCREEN_HEIGHT% --app="%URL3%"

echo.
echo ============================================
echo  Werkstatt-Monitor gestartet!
echo  3 Fenster sollten jetzt sichtbar sein.
echo ============================================
echo.
echo Druecke eine Taste zum Beenden dieses Fensters...
pause >nul
