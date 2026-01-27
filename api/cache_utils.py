"""
Cache Utilities - TAG 213
==========================
Redis-basiertes Caching für Performance-Optimierung
"""
import json
import logging
from functools import wraps
from datetime import datetime
from typing import Optional, Any, Callable

logger = logging.getLogger(__name__)

# Redis-Client (lazy loading)
_redis_client = None


def get_redis_client():
    """Holt oder erstellt Redis-Client (lazy loading)"""
    global _redis_client
    
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test-Verbindung
            _redis_client.ping()
            logger.info("✅ Redis-Client initialisiert")
        except ImportError:
            logger.warning("⚠️ Redis-Package nicht installiert. Caching deaktiviert.")
            _redis_client = False  # Marker: Redis nicht verfügbar
        except Exception as e:
            logger.warning(f"⚠️ Redis-Verbindung fehlgeschlagen: {e}. Caching deaktiviert.")
            _redis_client = False  # Marker: Redis nicht verfügbar
    
    return _redis_client if _redis_client is not False else None


def cache_stempeluhr(ttl: int = 10):
    """
    Decorator für Stempeluhr-Caching.
    
    Args:
        ttl: Cache-TTL in Sekunden (default: 10)
    
    Beispiel:
        @werkstatt_live_bp.route('/stempeluhr')
        @cache_stempeluhr(ttl=10)
        def get_stempeluhr_live():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            redis_client = get_redis_client()
            
            # Wenn Redis nicht verfügbar, Funktion normal ausführen
            if redis_client is None:
                return func(*args, **kwargs)
            
            # Cache-Key bauen aus Funktionsname + Parametern
            from flask import request
            
            # Parameter sammeln
            subsidiary = request.args.get('subsidiary', '')
            datum = datetime.now().date().isoformat()  # Heute
            
            cache_key = f"stempeluhr:{datum}:{subsidiary}"
            
            try:
                # Cache prüfen
                cached = redis_client.get(cache_key)
                if cached:
                    logger.info(f"✅ Cache-Hit: {cache_key}")
                    # JSON-Response zurückgeben
                    from flask import jsonify
                    cached_data = json.loads(cached)
                    # Timestamp aktualisieren
                    cached_data['timestamp'] = datetime.now().isoformat()
                    cached_data['cached'] = True
                    return jsonify(cached_data)
                
                # Cache-Miss: Funktion ausführen
                logger.debug(f"❌ Cache-Miss: {cache_key}")
                result = func(*args, **kwargs)
                
                # Nur cachen wenn erfolgreich (200 Status)
                if hasattr(result, 'status_code') and result.status_code == 200:
                    # JSON-Response in Dict konvertieren
                    result_dict = result.get_json()
                    if result_dict and result_dict.get('success'):
                        # Cache setzen
                        redis_client.setex(cache_key, ttl, json.dumps(result_dict))
                        logger.debug(f"💾 Cache gespeichert: {cache_key} (TTL: {ttl}s)")
                
                return result
                
            except Exception as e:
                logger.warning(f"⚠️ Cache-Fehler: {e}. Funktion normal ausführen.")
                # Bei Cache-Fehler: Funktion normal ausführen
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def invalidate_stempeluhr_cache(subsidiary: Optional[str] = None):
    """
    Invalidiert Stempeluhr-Cache.
    
    Args:
        subsidiary: Optional - nur für bestimmten Betrieb invalidieren
    """
    redis_client = get_redis_client()
    if redis_client is None:
        return
    
    try:
        if subsidiary:
            pattern = f"stempeluhr:*:{subsidiary}"
        else:
            pattern = "stempeluhr:*"
        
        # Finde alle Keys
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            logger.info(f"✅ Cache invalidiert: {len(keys)} Keys gelöscht")
    except Exception as e:
        logger.warning(f"⚠️ Cache-Invalidierung fehlgeschlagen: {e}")
