import os
from kivy.app import App
from kivy.uix.label import Label
from kivy.clock import Clock

# Prevent clipboard and OpenGL issues
os.environ["KIVY_METRICS_DENSITY"] = "1"
os.environ["KIVY_NO_CONSOLELOG"] = "1"

print("🔹 Starting Test App...")

class TestApp(App):
    def build(self):
        print("🔹 Inside build() method...")
        Clock.schedule_once(self.exit_app, 5)  # Close after 5 seconds
        return Label(text="Hello, GitHub Actions!")

    def exit_app(self, dt):
        print("🔹 Closing app automatically...")
        self.stop()

if __name__ == "__main__":
    print("🔹 Running TestApp...")
    TestApp().run()
    print("🔹 App closed.")