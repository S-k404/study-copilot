"""
Study & Concept Copilot - macOS Menu Bar Assistant
Integrates with Anthropic Claude, Google Gemini, or an offline Mock engine.
"""

import os
import sys
import threading
import subprocess
import webbrowser
from PIL import Image
import mss
import rumps

from explainer_engine import ExplainerEngine

TEMP_CAPTURE_FILE = "/tmp/study_copilot_capture.png"

class StudyCopilotApp(rumps.App):
    def __init__(self):
        super(StudyCopilotApp, self).__init__("🎓 Study Copilot", quit_button=None)
        self.engine = ExplainerEngine(mode="auto")
        self.last_result = {
            "title": "No analysis yet",
            "summary": "Click 'Select Screen Region' or 'Explain Clipboard' to get started.",
            "full_explanation": "Welcome to Study Copilot!\n\nThis assistant helps break down complex questions, algorithms, and concepts step-by-step.\n\nChoose an option from the menu bar to analyze content."
        }
        
        # Build menu items
        self.menu_select_region = rumps.MenuItem("📐 Select Screen Region & Explain", callback=self.on_select_region)
        self.menu_full_screen = rumps.MenuItem("📸 Capture Full Screen & Explain", callback=self.on_full_screen)
        self.menu_clipboard = rumps.MenuItem("📋 Explain Clipboard Text", callback=self.on_explain_clipboard)
        
        self.menu_view_last = rumps.MenuItem("📖 View Latest Explanation", callback=self.on_view_last)
        
        # Engine Submenu
        self.menu_engine = rumps.MenuItem(f"⚙️ Engine: {self.engine.mode.capitalize()}")
        self.opt_mock = rumps.MenuItem("Offline Mock Mode", callback=lambda _: self.set_engine_mode("mock"))
        self.opt_claude = rumps.MenuItem("Claude 3.5 Sonnet", callback=lambda _: self.set_engine_mode("claude"))
        self.opt_gemini = rumps.MenuItem("Gemini 2.5 Flash", callback=lambda _: self.set_engine_mode("gemini"))
        self.menu_engine.update([self.opt_mock, self.opt_claude, self.opt_gemini])
        self._update_engine_checks()

        self.menu_sandbox = rumps.MenuItem("🌐 Open Practice Sandbox (Browser)", callback=self.on_open_sandbox)
        self.menu_quit = rumps.MenuItem("Quit", callback=rumps.quit_application)

        self.menu = [
            self.menu_select_region,
            self.menu_full_screen,
            self.menu_clipboard,
            None,
            self.menu_view_last,
            None,
            self.menu_engine,
            self.menu_sandbox,
            None,
            self.menu_quit
        ]

    def _update_engine_checks(self):
        self.opt_mock.state = self.engine.mode == "mock"
        self.opt_claude.state = self.engine.mode == "claude"
        self.opt_gemini.state = self.engine.mode == "gemini"
        self.menu_engine.title = f"⚙️ Engine: {self.engine.mode.capitalize()}"

    def set_engine_mode(self, mode: str):
        self.engine.set_mode(mode)
        self._update_engine_checks()
        rumps.notification("Engine Updated", "", f"Active engine set to: {mode.capitalize()}")

    def set_status(self, text: str):
        self.title = text

    def on_select_region(self, _):
        """Allows interactive drag selection using macOS screencapture."""
        def worker():
            self.set_status("🟡 Select Region...")
            # Remove previous capture if any
            if os.path.exists(TEMP_CAPTURE_FILE):
                os.remove(TEMP_CAPTURE_FILE)

            # screencapture -i launches interactive crosshair selection
            subprocess.run(["/usr/sbin/screencapture", "-i", "-x", TEMP_CAPTURE_FILE])
            
            if not os.path.exists(TEMP_CAPTURE_FILE) or os.path.getsize(TEMP_CAPTURE_FILE) == 0:
                self.set_status("🎓 Study Copilot")
                return

            self.process_image_path(TEMP_CAPTURE_FILE)

        threading.Thread(target=worker, daemon=True).start()

    def on_full_screen(self, _):
        """Captures primary monitor directly."""
        def worker():
            self.set_status("🟡 Capturing...")
            with mss.mss() as sct:
                sct.shot(mon=1, output=TEMP_CAPTURE_FILE)
            self.process_image_path(TEMP_CAPTURE_FILE)

        threading.Thread(target=worker, daemon=True).start()

    def process_image_path(self, path: str):
        try:
            self.set_status("🧠 Analyzing...")
            img = Image.open(path)
            result = self.engine.explain_image(img)
            self.last_result = result
            self.set_status("🟢 Explanation Ready")
            
            rumps.notification(
                title=f"🎓 {result.get('engine', 'Copilot')}",
                subtitle=result.get("title", "Concept Analysis")[:40],
                message=result.get("summary", "Click menu bar to view detailed breakdown.")
            )
        except Exception as e:
            self.set_status("⚠️ Error")
            rumps.alert("Analysis Error", str(e))
        finally:
            if os.path.exists(path):
                os.remove(path)

    def on_explain_clipboard(self, _):
        """Reads text from system clipboard and explains it."""
        def worker():
            self.set_status("🧠 Reading Clipboard...")
            proc = subprocess.run(["/usr/bin/pbpaste"], capture_output=True, text=True)
            text = proc.stdout.strip()
            if not text:
                self.set_status("🎓 Study Copilot")
                rumps.alert("Clipboard Empty", "Copy some question text or code to your clipboard first.")
                return

            result = self.engine.explain_text(text)
            self.last_result = result
            self.set_status("🟢 Explanation Ready")
            
            rumps.notification(
                title=f"🎓 {result.get('engine', 'Copilot')}",
                subtitle=result.get("title", "Text Analysis")[:40],
                message=result.get("summary", "")
            )

        threading.Thread(target=worker, daemon=True).start()

    def on_view_last(self, _):
        """Displays the full structured explanation in an alert window."""
        res = self.last_result
        text = f"=== {res.get('engine', 'Analysis')} ===\n\n" + res.get("full_explanation", "No content.")
        # Open detailed view via alert window
        rumps.alert(
            title=res.get("title", "Concept Breakdown"),
            message=text,
            ok="Close"
        )

    def on_open_sandbox(self, _):
        """Starts local mock quiz server if not running, and opens in browser."""
        webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    app = StudyCopilotApp()
    app.run()

