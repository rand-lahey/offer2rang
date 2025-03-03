from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.clipboard import Clipboard

Clipboard.init = lambda *args, **kwargs: None  # Disable clipboard functions

from kivymd.app import MDApp
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.screen import Screen
from kivy.metrics import dp
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import os
os.environ["KIVY_METRICS_DENSITY"] = "1"  # Prevents headless scaling issues
os.environ["KIVY_NO_CONSOLELOG"] = "1"  # Reduce unnecessary logs

# 🔹 Initialize Firebase BEFORE running the app
cred = credentials.Certificate("offerings2rang-firebase-adminsdk-fbsvc-a746c6d5e3.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Disable clipboard functions to prevent crashes in GitHub Actions
Clipboard.init = lambda *args, **kwargs: None  

class PoopTrackerApp(MDApp):
    def build(self):
        print("🔹 Inside build() method...")  # Debugging print statement

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
        return self.screen

    def log_poop(self, instance):
        rating = self.rating_input.text
        comment = self.comment_input.text
        timestamp = datetime.datetime.now()

            # Validate rating input
            if not rating.isdigit() or not (1 <= int(rating) <= 10):
                self.root.ids.status_label.text = "Invalid rating! Enter 1-10."
                return

            # Save to Firebase
            poop_data = {
                "rating": int(rating),
                "girth": float(girth) if girth else 0,
                "length": float(length) if length else 0,
                "demeanor": demeanor,
                "comment": comment,
                "timestamp": timestamp
            }
            db.collection("poop_logs").add(poop_data)

            # Update UI after successful log
            self.root.ids.status_label.text = "Poop logged successfully!"
            self.root.ids.rating_input.text = ""  # Clear input field
            self.root.ids.girth_input.text = ""
            self.root.ids.length_input.text = ""
            self.root.ids.comment_input.text = ""

        except Exception as e:
            self.root.ids.status_label.text = f"Error: {str(e)}"

    def exit_app(self, dt):
        print("🔹 Auto-exiting app after 10 seconds to prevent freezing...")
        self.stop()
        os._exit(0)  # Forcefully kill the process

if __name__ == "__main__":
    print("🔹 Starting PoopTrackerApp...")  # Debugging print statement
    PoopTrackerApp().run()