# 🔄 CACHING-STRATEGIE - GREINER PORTAL

**Status:** ✅ IMPLEMENTIERT (TAG 23)

## Problem
Browser cachen JavaScript/CSS → alte Versionen werden angezeigt

## Lösung
Cache-Busting mit STATIC_VERSION in app.py (bereits implementiert)

## Bei Updates
1. JavaScript/CSS ändern
2. Flask neu starten → Neue Version
3. Browser lädt automatisch neue Datei

## Troubleshooting
Browser zeigt alte Version? → Hard-Refresh (Ctrl+Shift+R)
