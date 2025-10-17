"""Cross-platform startup integration."""

import os
import platform
import sys
from typing import Any


class StartupManager:
    """Manages application startup with system."""

    def __init__(self):
        self.app_name = "Parrator"
        self.system = platform.system().lower()

    def is_enabled(self) -> bool:
        """Check if startup is enabled."""
        if self.system == "windows":
            return self._is_windows_startup_enabled()
        elif self.system == "darwin":
            return self._is_macos_startup_enabled()
        else:
            return self._is_linux_startup_enabled()

    def enable(self) -> bool:
        """Enable startup with system."""
        if self.system == "windows":
            return self._enable_windows_startup()
        elif self.system == "darwin":
            return self._enable_macos_startup()
        else:
            return self._enable_linux_startup()

    def disable(self) -> bool:
        """Disable startup with system."""
        if self.system == "windows":
            return self._disable_windows_startup()
        elif self.system == "darwin":
            return self._disable_macos_startup()
        else:
            return self._disable_linux_startup()

    def _get_executable_path(self) -> str:
        """Get path to current executable."""
        if getattr(sys, "frozen", False):
            return sys.executable
        else:
            return sys.executable + " " + os.path.abspath(__file__)

    # Windows implementation
    def _is_windows_startup_enabled(self) -> bool:
        try:
            import winreg

            key: Any = winreg.OpenKey(  # type: ignore[attr-defined]
                winreg.HKEY_CURRENT_USER,  # type: ignore[attr-defined]
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ,  # type: ignore[attr-defined]
            )
            winreg.QueryValueEx(key, self.app_name)  # type: ignore[attr-defined]
            winreg.CloseKey(key)  # type: ignore[attr-defined]
            return True
        except OSError:
            return False

    def _enable_windows_startup(self) -> bool:
        try:
            import winreg  # type: ignore[import]

            key: Any = winreg.OpenKey(  # type: ignore[attr-defined]
                winreg.HKEY_CURRENT_USER,  # type: ignore[attr-defined]
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE,  # type: ignore[attr-defined]
            )
            winreg.SetValueEx(  # type: ignore[attr-defined]
                key,
                self.app_name,
                0,
                winreg.REG_SZ,  # type: ignore[attr-defined]
                self._get_executable_path(),
            )
            winreg.CloseKey(key)  # type: ignore[attr-defined]
            return True
        except Exception as e:
            print(f"Failed to enable Windows startup: {e}")
            return False

    def _disable_windows_startup(self) -> bool:
        try:
            import winreg  # type: ignore[import]

            key = winreg.OpenKey(  # type: ignore[attr-defined]
                winreg.HKEY_CURRENT_USER,  # type: ignore[attr-defined]
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE,  # type: ignore[attr-defined]
            )
            winreg.DeleteValue(key, self.app_name)  # type: ignore[attr-defined]
            winreg.CloseKey(key)  # type: ignore[attr-defined]
            return True
        except OSError:
            return False

    # macOS implementation
    def _is_macos_startup_enabled(self) -> bool:
        plist_path = self._get_macos_plist_path()
        return os.path.exists(plist_path)

    def _enable_macos_startup(self) -> bool:
        try:
            plist_path = self._get_macos_plist_path()
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.parrator.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>{self._get_executable_path()}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""

            os.makedirs(os.path.dirname(plist_path), exist_ok=True)
            with open(plist_path, "w") as f:
                f.write(plist_content)
            return True
        except Exception as e:
            print(f"Failed to enable macOS startup: {e}")
            return False

    def _disable_macos_startup(self) -> bool:
        try:
            plist_path = self._get_macos_plist_path()
            if os.path.exists(plist_path):
                os.remove(plist_path)
            return True
        except OSError:
            return False

    def _get_macos_plist_path(self) -> str:
        return os.path.expanduser("~/Library/LaunchAgents/com.parrator.app.plist")

    # Linux implementation
    def _is_linux_startup_enabled(self) -> bool:
        desktop_path = self._get_linux_desktop_path()
        return os.path.exists(desktop_path)

    def _enable_linux_startup(self) -> bool:
        try:
            desktop_path = self._get_linux_desktop_path()
            desktop_content = f"""[Desktop Entry]
Type=Application
Name={self.app_name}
Exec={self._get_executable_path()}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""

            os.makedirs(os.path.dirname(desktop_path), exist_ok=True)
            with open(desktop_path, "w") as f:
                f.write(desktop_content)
            return True
        except Exception as e:
            print(f"Failed to enable Linux startup: {e}")
            return False

    def _disable_linux_startup(self) -> bool:
        try:
            desktop_path = self._get_linux_desktop_path()
            if os.path.exists(desktop_path):
                os.remove(desktop_path)
            return True
        except OSError:
            return False

    def _get_linux_desktop_path(self) -> str:
        return os.path.expanduser(
            f"~/.config/autostart/{self.app_name.lower()}.desktop"
        )
