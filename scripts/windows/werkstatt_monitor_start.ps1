# ============================================================================
# WERKSTATT MONITOR - 3-Split Kiosk Mode (PowerShell)
# ============================================================================
# Startet 3 Chrome-Fenster nebeneinander und positioniert sie korrekt
# ============================================================================

# --- KONFIGURATION ---
$SCREEN_WIDTH = 1920
$SCREEN_HEIGHT = 1080

# Fensterbreite (gleichmäßig 1/3)
$WINDOW_WIDTH = [math]::Floor($SCREEN_WIDTH / 3)

# URLs
$URL1 = "https://werkstattplanung.net/greiner/deggendorf/kic/da/#/views/40"
$URL2 = "https://werkstattplanung.net/greiner/deggendorf/kic/da/#/views/41"
$URL3 = "http://10.80.80.20/monitor/stempeluhr?token=Greiner2024Werkstatt!&subsidiary=1"

# Chrome Pfad
$CHROME = "C:\Program Files\Google\Chrome\Application\chrome.exe"

# Fensterbreite berechnen
$WINDOW_WIDTH = [math]::Floor($SCREEN_WIDTH / 3)

# --- Windows API fuer Fensterpositionierung ---
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")]
    public static extern bool MoveWindow(IntPtr hWnd, int X, int Y, int nWidth, int nHeight, bool bRepaint);
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
}
"@

Write-Host "============================================"
Write-Host " Werkstatt-Monitor wird gestartet..."
Write-Host "============================================"

# Alte Chrome-Instanzen beenden
Write-Host "Beende alte Chrome-Instanzen..."
Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Drei separate Chrome-Profile verwenden damit 3 unabhaengige Fenster entstehen
$PROFILE1 = "$env:TEMP\ChromeMonitor1"
$PROFILE2 = "$env:TEMP\ChromeMonitor2"
$PROFILE3 = "$env:TEMP\ChromeMonitor3"

# Fenster 1 starten (Links) - App-Mode ohne Adressleiste
Write-Host "Starte Fenster 1 (Links)..."
Start-Process -FilePath $CHROME -ArgumentList "--user-data-dir=$PROFILE1", "--app=$URL1", "--window-position=0,0", "--window-size=$WINDOW_WIDTH,$SCREEN_HEIGHT"
Start-Sleep -Seconds 4

# Fenster 2 starten (Mitte)
Write-Host "Starte Fenster 2 (Mitte)..."
Start-Process -FilePath $CHROME -ArgumentList "--user-data-dir=$PROFILE2", "--app=$URL2", "--window-position=$WINDOW_WIDTH,0", "--window-size=$WINDOW_WIDTH,$SCREEN_HEIGHT"
Start-Sleep -Seconds 4

# Fenster 3 starten (Rechts) - unsere Stempeluhr
Write-Host "Starte Fenster 3 (Rechts)..."
$POS_RIGHT = $WINDOW_WIDTH * 2
Start-Process -FilePath $CHROME -ArgumentList "--user-data-dir=$PROFILE3", "--app=$URL3", "--window-position=$POS_RIGHT,0", "--window-size=$WINDOW_WIDTH,$SCREEN_HEIGHT"
Start-Sleep -Seconds 4

# Fenster nochmal positionieren (zur Sicherheit)
Write-Host "Korrigiere Fensterpositionen..."
Start-Sleep -Seconds 2

$chromeWindows = Get-Process chrome -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 }

$positions = @(
    @{X = 0; Y = 0},
    @{X = $WINDOW_WIDTH; Y = 0},
    @{X = $WINDOW_WIDTH * 2; Y = 0}
)

$i = 0
foreach ($window in $chromeWindows) {
    if ($i -lt 3) {
        $handle = $window.MainWindowHandle
        $pos = $positions[$i]
        [Win32]::MoveWindow($handle, $pos.X, $pos.Y, $WINDOW_WIDTH, $SCREEN_HEIGHT, $true) | Out-Null
        Write-Host "  Fenster $($i+1) -> X=$($pos.X)"
        $i++
    }
}

Write-Host ""
Write-Host "============================================"
Write-Host " Werkstatt-Monitor gestartet!"
Write-Host " 3 Fenster nebeneinander (ohne Adressleiste)"
Write-Host "============================================"
Write-Host ""
Write-Host "Fenster schliesst in 5 Sekunden..."
Start-Sleep -Seconds 5
