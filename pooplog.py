import os
import time
import datetime
import threading
import pandas as pd
import matplotlib.pyplot as plt
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivymd.app import MDApp
from kivymd.uix.screen import Screen
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from firebase_admin import credentials, firestore, initialize_app

# 🔹 Prevent clipboard and OpenGL issues
os.environ["KIVY_METRICS_DENSITY"] = "1"
os.environ["KIVY_NO_CONSOLELOG"] = "1"

print("🔹 Initializing Firebase...")
cred = credentials.Certificate("offerings2rang-firebase-adminsdk-fbsvc-a746c6d5e3.json")
firebase_admin_app = initialize_app(cred)
db = firestore.client()

# Disable clipboard functions to prevent crashes in GitHub Actions
Clipboard.init = lambda *args, **kwargs: None  

class PoopTrackerApp(MDApp):
    def build(self):
        print("🔹 Inside build() method...")

        self.screen = Screen()
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        self.label = Label(text="Rate Your Poop (1-10):", font_size=24)
        self.rating_input = TextInput(hint_text="Enter a number", multiline=False)

        self.comment_label = Label(text="Comments:", font_size=20)
        self.comment_input = TextInput(hint_text="Optional comments", multiline=True)

        self.submit_button = Button(text="Log Poop", on_press=self.log_poop)
        self.stats_button = Button(text="View Stats", on_press=self.view_stats)

        layout.add_widget(self.label)
        layout.add_widget(self.rating_input)
        layout.add_widget(self.comment_label)
        layout.add_widget(self.comment_input)
        layout.add_widget(self.submit_button)
        layout.add_widget(self.stats_button)

        self.screen.add_widget(layout)

        # 🔹 Schedule an auto-close after 10 seconds to prevent GitHub Actions from freezing
        Clock.schedule_once(self.exit_app, 10)

        return self.screen

    def log_poop(self, instance):
        rating = self.rating_input.text
        comment = self.comment_input.text
        timestamp = datetime.datetime.now()

        if not rating.isdigit() or not (1 <= int(rating) <= 10):
            self.label.text = "Invalid input! Enter a number from 1-10."
            return

        poop_data = {
            "rating": int(rating),
            "comment": comment,
            "timestamp": timestamp
        }
        db.collection("poop_logs").add(poop_data)
        self.label.text = "Poop logged successfully!"

    def view_stats(self, instance):
        poops = db.collection("poop_logs").stream()
        data = [(p.get("timestamp"), p.get("rating")) for p in (p.to_dict() for p in poops)]

        if not data:
            self.label.text = "No poop data available."
            return

        df = pd.DataFrame(data, columns=["Timestamp", "Rating"])
        df = df.sort_values(by="Timestamp")

        plt.figure(figsize=(6, 4))
        plt.plot(df["Timestamp"], df["Rating"], marker='o', linestyle='-')
        plt.xlabel("Date")
        plt.ylabel("Poop Rating")
        plt.title("Poop Quality Over Time")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def exit_app(self, dt):
        print("🔹 Auto-exiting app after 10 seconds to prevent freezing...")
        self.stop()
        os._exit(0)  # Forcefully kill the process

if __name__ == "__main__":
    print("🔹 Starting PoopTrackerApp...")
    PoopTrackerApp().run()
    print("🔹 App closed.")  # Debugging print statement