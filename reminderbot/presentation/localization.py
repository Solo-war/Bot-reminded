from __future__ import annotations

import yaml
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict


class Localizer:
    """Простая локализация на основе YAML-файлов."""

    def __init__(self, locales_dir: Path, default_locale: str = "ru") -> None:
        self.locales_dir = locales_dir
        self.default_locale = default_locale

    def translate(self, key: str, locale: str | None = None, **params: Any) -> str:
        catalogue = self._load_locale(locale or self.default_locale)
        value = self._resolve_key(catalogue, key.split("."))
        if params:
            return value.format(**params)
        return value

    @lru_cache(maxsize=32)
    def _load_locale(self, locale: str) -> Dict[str, Any]:
        file_path = self.locales_dir / f"{locale}.yml"
        if not file_path.exists():
            file_path = self.locales_dir / f"{self.default_locale}.yml"
        with file_path.open("r", encoding="utf-8") as fp:
            return yaml.safe_load(fp) or {}

    def _resolve_key(self, catalogue: Dict[str, Any], keys: list[str]) -> str:
        current: Any = catalogue
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                raise KeyError(f"Локализационный ключ отсутствует: {'.'.join(keys)}")
        if not isinstance(current, str):
            raise ValueError("Локализационное значение должно быть строкой")
        return current
