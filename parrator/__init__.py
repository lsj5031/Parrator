"""Parrator package exports core components lazily."""

from typing import Any

__all__ = ["ParratorTrayApp", "HotkeyManager"]


def __getattr__(name: str) -> Any:
    if name == "ParratorTrayApp":
        from .tray_app import ParratorTrayApp

        return ParratorTrayApp

    if name == "HotkeyManager":
        from .hotkey_manager import HotkeyManager

        return HotkeyManager

    raise AttributeError(f"module 'parrator' has no attribute {name!r}")
