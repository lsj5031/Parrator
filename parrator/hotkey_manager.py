"""
Global hotkey management using pynput.
"""

from typing import Callable, Optional
from pynput import keyboard


class HotkeyManager:
    """Manages global hotkeys using pynput."""

    def __init__(self, hotkey_combo: str, callback: Callable):
        self.hotkey_combo = hotkey_combo
        self.callback = callback
        self.hotkey_listener: Optional[keyboard.GlobalHotKeys] = None

    def start(self) -> bool:
        """Start listening for hotkeys."""
        try:
            # Convert our config format to pynput format
            pynput_hotkey = self._convert_hotkey_format(self.hotkey_combo)

            # Create hotkey map
            hotkey_map = {pynput_hotkey: self.callback}

            self.hotkey_listener = keyboard.GlobalHotKeys(hotkey_map)
            self.hotkey_listener.start()

            print(f"Hotkey '{self.hotkey_combo}' registered successfully as '{
                  pynput_hotkey}'")
            return True

        except Exception as e:
            print(f"Failed to register hotkey '{self.hotkey_combo}': {e}")
            return False

    def _convert_hotkey_format(self, hotkey: str) -> str:
        """Convert config hotkey format to pynput format."""
        # Convert common formats to pynput format
        # config: "ctrl+shift+;" -> pynput: "<ctrl>+<shift>+;"

        parts = hotkey.lower().split('+')
        converted_parts = []

        for part in parts:
            part = part.strip()
            if part in ['ctrl', 'control']:
                converted_parts.append('<ctrl>')
            elif part in ['shift']:
                converted_parts.append('<shift>')
            elif part in ['alt']:
                converted_parts.append('<alt>')
            elif part in ['cmd', 'win', 'super']:
                converted_parts.append('<cmd>')
            elif len(part) == 1:  # Single character
                converted_parts.append(part)
            else:
                # For special keys like 'space', 'enter', etc.
                converted_parts.append(f'<{part}>')

        return '+'.join(converted_parts)

    def stop(self):
        """Stop listening for hotkeys."""
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None
            print("Hotkey listener stopped")
