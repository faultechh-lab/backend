# Çeviri durumu için basit in-memory cache
# Thread-safe değil ama tek worker için yeterli
_translation_status_cache = {}


def set_translation_complete(key: str, data: dict):
    """Çeviri tamamlandığında durumu cache'e kaydet"""
    _translation_status_cache[key] = data


def get_translation_status(key: str) -> dict | None:
    """Çeviri durumunu al ve cache'den sil (bir kez okunur)"""
    return _translation_status_cache.pop(key, None)


def get_all_completed_translations() -> list:
    """Tamamlanan tüm çevirileri al ve temizle"""
    if not _translation_status_cache:
        return []
    
    results = list(_translation_status_cache.values())
    _translation_status_cache.clear()
    return results
