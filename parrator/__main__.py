#!/usr/bin/env python3
"""
Parrator Tray - Simple Speech-to-Text System Tray Application
"""

import signal
import sys

from parrator.tray_app import ParratorTrayApp


def signal_handler(signum, frame):
    """Handle system signals for clean shutdown."""
    print("Received shutdown signal, cleaning up...")
    sys.exit(0)


def main():
    """Main entry point."""
    # Handle clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and start the tray application
    app = ParratorTrayApp()

    try:
        app.start()
    except KeyboardInterrupt:
        print("Application interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()
