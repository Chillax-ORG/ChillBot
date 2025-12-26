import time
import requests


class ClassUpdater:
    def __init__(self, mapping_url_override: str | None = None) -> None:
        self._mapping_url = mapping_url_override or 'https://raw.githubusercontent.com/fedeericodl/discord-update-classnames/refs/heads/data/classNamesMap.json'
        self._class_mappings: dict[str, str] = {}
        self._last_map_refresh = 0
        self._map_cache_ttl = 15 * 60  # Cache the file for 15 minutes to avoid unnecessary requests
    
    def _refresh_mappings_file(self) -> None:
        if time.time() < self._last_map_refresh + self._map_cache_ttl:
            return
        response = requests.get(self._mapping_url)
        self._class_mappings = response.json()
        self._last_map_refresh = time.time()
    
    def _apply_mapping(self, text: str) -> tuple[str, bool]:
        was_updated = False
        for old_class, new_class in self._class_mappings.items():
            new_text = text.replace(old_class, new_class)
            if new_text != text:
                text = new_text
                was_updated = True
        return text, was_updated
    
    def replace(self, text: str, max_depth: int = 10) -> str:
        self._refresh_mappings_file()
        
        # Repeat the process, because file can contain mappings like a -> b; b -> c
        was_updated = True
        for _ in range(max_depth):
            if not was_updated:
                break
            text, was_updated = self._apply_mapping(text)
        
        return text