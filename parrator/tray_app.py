"""
Simplified tray application.
"""

import contextlib
import os
import subprocess
import sys
import threading
import time
from typing import Optional

import pystray  # type: ignore[import-untyped]
from PIL import Image  # type: ignore[import]

from .audio_recorder import AudioRecorder
from .cleanup import CleanupManager
from .config import Config
from .hotkey_manager import HotkeyManager
from .notifications import NotificationManager
from .startup import StartupManager
from .text_refiner import TextRefiner
from .transcriber import Transcriber


class ParratorTrayApp:
    """Main tray application."""

    def __init__(self):
        self.config = Config()
        self.transcriber = Transcriber(self.config)
        self.transcriber_mandarin: Optional[Transcriber] = None
        self.audio_recorder = AudioRecorder(self.config)
        self.text_refiner = TextRefiner(self.config)
        self.cleanup_manager = CleanupManager(self.config.config)
        self.notification_manager = NotificationManager()
        self.startup_manager = StartupManager()
        self.hotkey_manager: Optional[HotkeyManager] = None
        self.hotkey_manager_zh: Optional[HotkeyManager] = None
        self.tray_icon: Optional[pystray.Icon] = None
        self.is_recording = False
        self.model_loaded = False
        self.active_transcriber: Optional[str] = None  # 'en' or 'zh'

    def start(self):
        """Start the application."""
        print("Starting Parrator...")

        # Load transcription model in background
        self._load_model_async()

        # Setup tray icon
        self._setup_tray()

        # Setup hotkeys
        self._setup_hotkeys()

        hotkey_label = self.config.get("hotkey")
        hotkey_label_zh = self.config.get("hotkey_mandarin", "ctrl+alt+m")
        print(f"Ready! Press {hotkey_label} (EN) or {hotkey_label_zh} (ZH) to record")

        # Run tray (this blocks)
        assert self.tray_icon is not None
        try:
            self.tray_icon.run()
        except KeyboardInterrupt:
            print("Application interrupted")
        finally:
            self.cleanup()

    def _load_model_async(self):
        """Load the transcription model in a background thread."""

        def load_model():
            if self.transcriber.load_model():
                self.model_loaded = True
                self._update_tray_icon()
                print("Model loaded successfully")
            else:
                print("Failed to load model")

        thread = threading.Thread(target=load_model, daemon=True)
        thread.start()

    def _setup_tray(self):
        """Setup the system tray icon."""
        # Load icon from resources
        icon_path = self._get_icon_path()
        try:
            image = Image.open(icon_path)
        except Exception as e:
            print(f"Could not load icon: {e}")
            # Create simple fallback icon
            image = Image.new("RGB", (64, 64), color="blue")

        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem("Toggle Recording", self._toggle_recording),
            # Secondary Mandarin toggle via config-only hotkey; keep menu minimal
            pystray.MenuItem("Settings", self._show_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Text Refinement",
                self._toggle_text_refinement,
                checked=lambda item: self.config.get("text_refinement.enabled", True),
            ),
            pystray.MenuItem(
                "Smart Cleanup",
                self._toggle_smart_cleanup,
                checked=lambda item: self.config.get("cleanup.enabled", True),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Start with System",
                self._toggle_startup,
                checked=lambda item: self.startup_manager.is_enabled(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit_application),
        )

        self.tray_icon = pystray.Icon("parrator", image, "Parrator - Loading...", menu)

    def _setup_hotkeys(self):
        """Setup global hotkeys."""
        hotkey_combo_en = self.config.get("hotkey", "ctrl+shift+;")
        self.hotkey_manager = HotkeyManager(hotkey_combo_en, self._toggle_recording)

        if not self.hotkey_manager.start():
            print(f"Could not register hotkey: {hotkey_combo_en}")

        if Transcriber.funasr_supported():
            hotkey_combo_zh = self.config.get("hotkey_mandarin", "ctrl+alt+m")
            self.hotkey_manager_zh = HotkeyManager(
                hotkey_combo_zh, self._toggle_recording_mandarin
            )
            if not self.hotkey_manager_zh.start():
                print(f"Could not register mandarin hotkey: {hotkey_combo_zh}")
        else:
            print("FunASR dependencies not installed; Mandarin hotkey disabled")

    def _toggle_recording(self):
        """Toggle recording state."""
        if not self.model_loaded:
            print("Model still loading, please wait...")
            return

        if not self.is_recording:
            self.active_transcriber = "en"
            self._start_recording()
        else:
            self._stop_recording()

    def _toggle_recording_mandarin(self):
        """Toggle recording for Mandarin using FunASR (lazy-load)."""
        if not Transcriber.funasr_supported():
            print(
                "FunASR backend unavailable; install optional dependencies to "
                "enable Mandarin hotkey"
            )
            return

        if self.transcriber_mandarin is None:
            backend = self.config.get("mandarin_backend", "funasr")
            model_name = self.config.get("mandarin_model_name", "funasr/paraformer-zh")
            self.transcriber_mandarin = Transcriber(
                self.config, backend=backend, model_name=model_name
            )
            if not self.transcriber_mandarin.load_model():
                print("Failed to load Mandarin model")
                self.transcriber_mandarin = None
                return

        if not self.is_recording:
            self.active_transcriber = "zh"
            self._start_recording()
        else:
            self._stop_recording()

    def _start_recording(self):
        """Start audio recording."""
        print("Recording started...")
        self.is_recording = True
        self._update_tray_icon()

        if not self.audio_recorder.start_recording():
            print("Failed to start recording")
            self.is_recording = False
            self._update_tray_icon()

    def _stop_recording(self):
        """Stop recording and process audio."""
        print("Recording stopped, processing...")
        self.is_recording = False
        self._update_tray_icon()

        # Stop recording and get audio data
        audio_data = self.audio_recorder.stop_recording()

        if audio_data is not None:
            selected = self.active_transcriber or "en"
            self._process_audio_async(audio_data, transcriber_id=selected)
        else:
            print("No audio data captured")

    def _process_audio_async(self, audio_data, transcriber_id: str = "en"):
        """Process audio in background thread."""

        def process():
            try:
                # Save temporary audio file
                temp_path = self.audio_recorder.save_temp_audio(audio_data)
                if not temp_path:
                    print("Failed to save audio")
                    return

                # Transcribe
                if transcriber_id == "zh" and self.transcriber_mandarin is not None:
                    success, text = self.transcriber_mandarin.transcribe_file(temp_path)
                else:
                    success, text = self.transcriber.transcribe_file(temp_path)

                # Cleanup temp file
                with contextlib.suppress(Exception):
                    os.remove(temp_path)

                if success and text:
                    self._handle_transcription_result(text, transcriber_id)
                else:
                    print("Transcription failed")

            except Exception as e:
                print(f"Processing error: {e}")

        thread = threading.Thread(target=process, daemon=True)
        thread.start()

    def _handle_transcription_result(self, text: str, transcriber_id: str = "en"):
        """Handle successful transcription."""
        print(f"Transcribed: {text}")

        # Check for Shift key bypass
        bypass_cleanup = self._is_shift_pressed()

        # Apply smart cleanup if enabled and not bypassed
        cleaned_text = self._apply_smart_cleanup(text, bypass=bypass_cleanup)

        # Apply legacy text refinement if enabled (for compatibility)
        if not bypass_cleanup:
            refined_text = self._refine_transcription(cleaned_text, transcriber_id)
        else:
            refined_text = cleaned_text

        if refined_text != text:
            print(f"Processed: {refined_text}")

        # Copy to clipboard
        try:
            import pyperclip  # type: ignore[import-untyped]

            pyperclip.copy(refined_text)
            print("Copied to clipboard")

            # Auto-paste if enabled
            if self.config.get("auto_paste", True):
                self._auto_paste()

        except Exception as e:
            print(f"Clipboard error: {e}")

    def _refine_transcription(self, text: str, transcriber_id: str = "en") -> str:
        """Refine transcription text using AI models."""
        try:
            # Get current ASR model name
            if transcriber_id == "zh" and self.transcriber_mandarin is not None:
                asr_model = self.transcriber_mandarin.model_name or ""
            else:
                asr_model = self.transcriber.model_name or ""

            # Apply text refinement
            return self.text_refiner.refine_text(text, asr_model)

        except Exception as e:
            print(f"Text refinement error: {e}")
            return text

    def _apply_smart_cleanup(self, text: str, bypass: bool = False) -> str:
        """Apply smart cleanup to transcribed text."""
        if bypass or not text or not text.strip():
            return text

        try:
            # Get cleanup mode from config
            cleanup_config = self.config.get("cleanup", {})
            mode = cleanup_config.get("mode", "standard")

            # Apply cleanup
            return self.cleanup_manager.clean_text(text, mode, bypass)

        except Exception as e:
            print(f"Smart cleanup error: {e}")
            return text

    def _is_shift_pressed(self) -> bool:
        """Check if Shift key is currently pressed (for bypass)."""
        try:
            import keyboard  # type: ignore[import-untyped]
            return keyboard.is_pressed('shift')
        except ImportError:
            # Fallback: try with pyautogui
            try:
                import pyautogui  # type: ignore[import-untyped]
                # pyautogui doesn't have a direct way to check key state
                # so we'll return False and rely on config-based bypass
                return False
            except ImportError:
                return False
        except Exception:
            return False

    def _auto_paste(self):
        """Automatically paste from clipboard."""
        try:
            import pyautogui  # type: ignore[import-untyped]

            time.sleep(0.1)
            pyautogui.hotkey("ctrl", "v")
            print("Auto-pasted")
        except Exception as e:
            print(f"Auto-paste failed: {e}")

    def _update_tray_icon(self):
        """Update tray icon title based on current state."""
        if self.tray_icon:
            if self.is_recording:
                title = "Parrator - Recording..."
            elif self.model_loaded:
                title = "Parrator - Ready"
            else:
                title = "Parrator - Loading..."

            self.tray_icon.title = title

    def _show_settings(self):
        """Open settings file in default editor."""
        try:
            config_path = self.config.config_path

            if sys.platform == "win32":
                os.startfile(config_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", config_path])
            else:
                subprocess.run(["xdg-open", config_path])

            print(f"Opened settings: {config_path}")

        except Exception as e:
            print(f"Could not open settings: {e}")

    def _toggle_text_refinement(self):
        """Toggle text refinement on/off."""
        current_state = self.config.get("text_refinement.enabled", True)
        new_state = not current_state
        self.config.set("text_refinement.enabled", new_state)

        if new_state:
            print("Text refinement enabled")
        else:
            print("Text refinement disabled")

    def _toggle_smart_cleanup(self):
        """Toggle smart cleanup on/off."""
        current_state = self.config.get("cleanup.enabled", True)
        new_state = not current_state
        self.config.set("cleanup.enabled", new_state)

        if new_state:
            print("Smart cleanup enabled")
            # Show available engines
            status = self.cleanup_manager.get_engine_status()
            available = [name for name, status_text in status.items() if "available" in status_text.lower()]
            print(f"Available engines: {', '.join(available)}")
        else:
            print("Smart cleanup disabled")

    def _toggle_startup(self):
        """Toggle startup with system."""
        if self.startup_manager.is_enabled():
            if self.startup_manager.disable():
                print("Disabled startup with system")
            else:
                print("Failed to disable startup")
        else:
            if self.startup_manager.enable():
                print("Enabled startup with system")
            else:
                print("Failed to enable startup")

    def _quit_application(self):
        """Quit the application."""
        print("Quitting...")
        self.cleanup()
        assert self.tray_icon is not None
        self.tray_icon.stop()

    def _get_icon_path(self):
        """Get path to tray icon."""
        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS  # type: ignore[attr-defined]
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        return os.path.join(base_path, "resources", "icon.png")

    def cleanup(self):
        """Clean up resources."""
        if self.hotkey_manager:
            self.hotkey_manager.stop()
        if self.hotkey_manager_zh:
            self.hotkey_manager_zh.stop()
        if self.audio_recorder:
            self.audio_recorder.cleanup()
