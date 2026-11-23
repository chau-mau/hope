import os
import random
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

DATABASE = os.path.join(os.path.dirname(__file__), "todo.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2 MB max upload size

AFFIRMATIONS = [
    "You are capable of amazing things.",
    "Every step you take brings you closer to your goal.",
    "Believe in yourself and all that you are.",
    "Progress, not perfection.",
    "You are stronger than you think.",
    "Learning is a journey, and you are on the right path.",
    "Your effort today builds your success tomorrow.",
    "Stay positive, work hard, make it happen.",
    "You have the power to create change.",
    "Mistakes are proof that you are trying.",
    "Keep going — you are doing great.",
    "Your potential is endless.",
    "Focus on progress, not perfection.",
    "You are enough, just as you are.",
    "Small steps every day lead to big results.",
]


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def init_db():
    with app.app_context():
        db = get_db()
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                logo_path TEXT,
                exam_date DATE
            );

            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                confidence INTEGER NOT NULL DEFAULT 0,
                preparation INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS visitors (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                count INTEGER NOT NULL DEFAULT 0
            );
            """
        )

        # Ensure the visitor counter row exists.
        db.execute("INSERT OR IGNORE INTO visitors (id, count) VALUES (1, 0)")

        # Migrate existing databases that lack newer columns.
        subject_columns = [
            row["name"]
            for row in db.execute("PRAGMA table_info(subjects)").fetchall()
        ]
        if "preparation" not in subject_columns:
            db.execute("ALTER TABLE subjects ADD COLUMN preparation INTEGER NOT NULL DEFAULT 0")

        user_columns = [
            row["name"]
            for row in db.execute("PRAGMA table_info(users)").fetchall()
        ]
        if "logo_path" not in user_columns:
            db.execute("ALTER TABLE users ADD COLUMN logo_path TEXT")

        if "exam_date" not in user_columns:
            db.execute("ALTER TABLE users ADD COLUMN exam_date DATE")

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        db.commit()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not username or not password:
            flash("Username and password are required.", "danger")
            return redirect(url_for("register"))

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        db = get_db()
        existing = db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()

        if existing:
            flash("Username already taken.", "danger")
            return redirect(url_for("register"))

        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        db.commit()
        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome, {user['username']}!")
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


def increment_visitors():
    db = get_db()
    db.execute("UPDATE visitors SET count = count + 1 WHERE id = 1")
    db.commit()
    row = db.execute("SELECT count FROM visitors WHERE id = 1").fetchone()
    return row["count"] if row else 0


def get_suggestion(preparation):
    if preparation < 25:
        return "Your preparation is just starting. Create a study schedule and focus on building the basics."
    if preparation < 50:
        return "You're making progress. Keep practising regularly and identify your weaker areas."
    if preparation < 75:
        return "Good going! Move to revision and timed practice tests now."
    if preparation < 90:
        return "Well prepared. Focus on mock tests and fine-tuning your strategy."
    return "Excellent! You seem exam-ready. Stay calm, revise, and trust your preparation."


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    subjects = db.execute(
        "SELECT * FROM subjects WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],),
    ).fetchall()

    total = len(subjects)
    average_confidence = 0
    average_preparation = 0
    if total > 0:
        average_confidence = sum(s["confidence"] for s in subjects) / total
        average_preparation = sum(s["preparation"] for s in subjects) / total

    affirmation = random.choice(AFFIRMATIONS)

    user = db.execute(
        "SELECT logo_path, exam_date FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()

    logo_url = None
    if user and user["logo_path"]:
        logo_url = url_for("static", filename=user["logo_path"])

    days_to_go = None
    exam_date = None
    if user and user["exam_date"]:
        exam_date = datetime.strptime(user["exam_date"], "%Y-%m-%d").date()
        days_to_go = (exam_date - datetime.today().date()).days

    suggestion = get_suggestion(average_preparation)
    visitor_count = increment_visitors()

    return render_template(
        "dashboard.html",
        subjects=subjects,
        total=total,
        average_confidence=round(average_confidence, 1),
        average_preparation=round(average_preparation, 1),
        affirmation=affirmation,
        affirmations=AFFIRMATIONS,
        logo_url=logo_url,
        suggestion=suggestion,
        exam_date=exam_date,
        days_to_go=days_to_go,
        visitor_count=visitor_count,
    )


def clamp_percentage(value):
    try:
        value = int(value)
    except (ValueError, TypeError):
        value = 0
    return max(0, min(100, value))


@app.route("/subject/add", methods=["POST"])
@login_required
def add_subject():
    name = request.form.get("name", "").strip()
    confidence = clamp_percentage(request.form.get("confidence", "0"))
    preparation = clamp_percentage(request.form.get("preparation", "0"))

    if not name:
        flash("Subject name is required.", "danger")
        return redirect(url_for("dashboard"))

    db = get_db()
    db.execute(
        "INSERT INTO subjects (user_id, name, confidence, preparation) VALUES (?, ?, ?, ?)",
        (session["user_id"], name, confidence, preparation),
    )
    db.commit()
    flash("Subject added.", "success")
    return redirect(url_for("dashboard"))


@app.route("/subject/update/<int:subject_id>", methods=["POST"])
@login_required
def update_subject(subject_id):
    confidence = clamp_percentage(request.form.get("confidence"))
    preparation = clamp_percentage(request.form.get("preparation"))

    db = get_db()
    subject = db.execute(
        "SELECT * FROM subjects WHERE id = ? AND user_id = ?",
        (subject_id, session["user_id"]),
    ).fetchone()

    if not subject:
        flash("Subject not found.", "danger")
        return redirect(url_for("dashboard"))

    db.execute(
        "UPDATE subjects SET confidence = ?, preparation = ? WHERE id = ?",
        (confidence, preparation, subject_id),
    )
    db.commit()
    flash("Progress updated.", "success")
    return redirect(url_for("dashboard"))


@app.route("/subject/delete/<int:subject_id>", methods=["POST"])
@login_required
def delete_subject(subject_id):
    db = get_db()
    db.execute(
        "DELETE FROM subjects WHERE id = ? AND user_id = ?",
        (subject_id, session["user_id"]),
    )
    db.commit()
    flash("Subject deleted.", "info")
    return redirect(url_for("dashboard"))


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/set-exam-date", methods=["POST"])
@login_required
def set_exam_date():
    exam_date = request.form.get("exam_date", "").strip()

    try:
        parsed = datetime.strptime(exam_date, "%Y-%m-%d").date()
        if parsed < datetime.today().date():
            flash("Exam date cannot be in the past.", "danger")
            return redirect(url_for("dashboard"))
    except ValueError:
        flash("Invalid date format.", "danger")
        return redirect(url_for("dashboard"))

    db = get_db()
    db.execute(
        "UPDATE users SET exam_date = ? WHERE id = ?",
        (exam_date, session["user_id"]),
    )
    db.commit()
    flash("Exam date updated.", "success")
    return redirect(url_for("dashboard"))


@app.route("/upload-logo", methods=["POST"])
@login_required
def upload_logo():
    if "logo" not in request.files:
        flash("No file selected.", "danger")
        return redirect(url_for("dashboard"))

    file = request.files["logo"]
    if file.filename == "":
        flash("No file selected.", "danger")
        return redirect(url_for("dashboard"))

    if file and allowed_file(file.filename):
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"user_{session['user_id']}_logo.{ext}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        db = get_db()
        db.execute(
            "UPDATE users SET logo_path = ? WHERE id = ?",
            (os.path.join("uploads", filename), session["user_id"]),
        )
        db.commit()
        flash("Exam logo uploaded successfully.", "success")
    else:
        flash("Invalid file type. Use PNG, JPG, GIF, or WEBP.", "danger")

    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=os.environ.get("FLASK_DEBUG", "False").lower() == "true")
