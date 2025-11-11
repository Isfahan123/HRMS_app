"""
Minimal Toga GUI test.
Shows a window with a label and a button, then exits automatically after 2 seconds.
Requires `toga` to be installed in the current Python environment.
"""
import sys
import threading
import time

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

APP_NAME = 'Toga GUI Test'

class TestApp(toga.App):
    def startup(self):
        # Main window
        self.main_window = toga.MainWindow(title=APP_NAME)

        label = toga.Label('Toga is running!', style=Pack(padding=12))
        btn = toga.Button('Close now', on_press=self.on_close, style=Pack(padding=12))

        box = toga.Box(children=[label, btn], style=Pack(direction=COLUMN, padding=12))
        self.main_window.content = box
        self.main_window.show()

        # Schedule automatic exit after 2 seconds on a background thread
        def delayed_quit():
            time.sleep(2)
            try:
                # Use the main window API to close
                self.main_window.close()
                # Stop the app from the main thread
                self.exit()
            except Exception:
                pass

        threading.Thread(target=delayed_quit, daemon=True).start()

    def on_close(self, widget):
        try:
            self.main_window.close()
            self.exit()
        except Exception:
            pass


def main():
    app = TestApp(APP_NAME, 'org.example.toga_test')
    return app

if __name__ == '__main__':
    main().main_loop()
