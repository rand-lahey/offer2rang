from flask import Flask, render_template, redirect, url_for, request, session
import firebase_admin
from firebase_admin import auth, credentials, firestore
from flask_session import Session  # For persistent sessions
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64 
import random
import string

app = Flask(__name__)
app.secret_key = "your_secret_key"

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/generate-invite", methods=["POST"])
def generate_invite():
    if "user" not in session:
        return "Unauthorized", 403  # Ensure only logged-in users can invite

    user_id = session["user"]
    invite_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))  # Generate random code

    db.collection("invites").document(invite_code).set({
        "created_by": user_id,
        "used": False
    })

    invite_link = f"http://127.0.0.1:5000/invite/{invite_code}"
    return f"Invite link: {invite_link}"

@app.route("/invite/<invite_code>")
def accept_invite(invite_code):
    invite_ref = db.collection("invites").document(invite_code)
    invite_doc = invite_ref.get()

    if not invite_doc.exists or invite_doc.to_dict().get("used"):
        return "Invalid or expired invite link."

    return render_template("signup.html", invite_code=invite_code)

@app.route("/register", methods=["POST"])
def register():
    invite_code = request.form.get("invite_code")
    email = request.form.get("email")
    password = request.form.get("password")

    try:
        user = auth.create_user(email=email, password=password)
        user_id = user.uid

        # Mark invite as used
        invite_ref = db.collection("invites").document(invite_code)
        invite_ref.update({"used": True})

        return "Registration successful! You can now log in."
    except Exception as e:
        return f"Error: {e}"
    
# Configure Flask-Session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialize Firebase
cred = credentials.Certificate("/Users/wolastoqeducation/Desktop/PoopLog/offerings2rang-firebase-adminsdk-fbsvc-a746c6d5e3.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route("/")
def landing_page():
    print("Session Data:", session)  # Debugging
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")


@app.route("/login", methods=["POST"])
def login():
    id_token = request.form.get("idToken")
    print("Received ID Token:", id_token)  # Debugging

    try:
        decoded_token = auth.verify_id_token(id_token)
        print("Decoded Token:", decoded_token)  # Debugging
        session["user"] = decoded_token["uid"]
        print("Session after login:", session)  # Debugging
        return redirect(url_for("dashboard"))
    except Exception as e:
        print("Login Error:", e)  # Debugging
        return str(e), 401

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("landing_page"))

    user_id = session["user"]

    # Fetch user's poops
    poops_ref = db.collection("poop_logs").where("user_id", "==", user_id).stream()
    poops = [{"time": p.get("time"), "type": p.get("type"), "notes": p.get("notes")} for p in poops_ref]

    return render_template("dashboard.html", poops=poops)

@app.route("/log-poop", methods=["POST"])
def log_poop():
    if "user" not in session:
        return redirect(url_for("landing_page"))

    user_id = session["user"]
    poop_data = {
        "user_id": user_id,
        "time": request.form.get("time"),
        "type": request.form.get("type"),
        "girth": float(request.form.get("girth", 0)),
        "length": float(request.form.get("length", 0)),
        "notes": request.form.get("notes", ""),
    }
    db.collection("poop_logs").add(poop_data)

    return redirect(url_for("dashboard"))   

@app.route("/set-nickname", methods=["POST"])
def set_nickname():
    if "user" not in session:
        return redirect(url_for("landing_page"))

    user_id = session["user"]
    nickname = request.form.get("nickname")
    show_on_leaderboard = request.form.get("show_on_leaderboard") == "on"

    db.collection("users").document(user_id).set({
        "nickname": nickname,
        "show_on_leaderboard": show_on_leaderboard
    }, merge=True)

    return redirect(url_for("dashboard"))

@app.route("/leaderboard-graph")
def leaderboard_graph():
    print("Session Data:", session)  # Debugging
    if "user" not in session:
        return "Unauthorized", 403  # Ensure user is logged in

    poops_ref = db.collection("poop_logs").stream()

    girths = []
    lengths = []
    for poop in poops_ref:
        data = poop.to_dict()
        print("Poop Data:", data)  # Debugging
        if "girth" in data and "length" in data:
            girths.append(data["girth"])
            lengths.append(data["length"])

    print("Girths:", girths)
    print("Lengths:", lengths)

    if not girths or not lengths:
        return "No poop data available for graphing."

    # Create the plot
    plt.figure(figsize=(6, 4))
    plt.scatter(girths, lengths, alpha=0.7)
    plt.xlabel("Girth (cm)")
    plt.ylabel("Length (cm)")
    plt.title("Poop Girth vs. Length")

    # Convert plot to image
    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    encoded_img = base64.b64encode(img.getvalue()).decode()

    return render_template("leaderboard_graph.html", graph_data=encoded_img)

@app.route("/leaderboard")
def leaderboard():
    users_ref = db.collection("users").where("show_on_leaderboard", "==", True).stream()
    leaderboard_data = []

    for user in users_ref:
        user_data = user.to_dict()
        user_id = user.id
        poop_count = db.collection("poop_logs").where("user_id", "==", user_id).stream()
        
        leaderboard_data.append({
            "nickname": user_data.get("nickname", "Anonymous"),
            "count": len(list(poop_count))
        })

    leaderboard_data.sort(key=lambda x: x["count"], reverse=True)  # Sort by most poops

    return render_template("leaderboard.html", leaderboard=leaderboard_data)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("landing_page"))

if __name__ == "__main__":
    app.run(debug=True)