from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"  # Change this to a secure key
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pc_tracking.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# PC Model
class PC(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coy_number = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    serial_number = db.Column(db.String(50), nullable=False, unique=True)
    issue_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)

# Login Page
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "Admin" and password == "Eastplats@2025":
            session["admin"] = True
            return redirect(url_for("dashboard"))  # Redirect after successful login
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

# Dashboard (PC List Only Appears After Search)
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect(url_for("login"))
    return render_template("dashboard.html", pcs=None)

# Unified Issue/Return Page
@app.route("/issue_pc", methods=["GET", "POST"])
def issue_pc():
    if not session.get("admin"):
        return redirect(url_for("login"))

    message = None  # For displaying alerts

    if request.method == "POST":
        action = request.form["action"]

        if action == "issue":
            coy_number = request.form["coy_number"]
            username = request.form["username"]
            serial_number = request.form["serial_number"]
            issue_date = request.form["issue_date"]
            return_date = request.form.get("return_date", None)

            new_pc = PC(
                coy_number=coy_number,
                username=username,
                serial_number=serial_number,
                issue_date=datetime.strptime(issue_date, "%Y-%m-%d"),
                return_date=datetime.strptime(return_date, "%Y-%m-%d") if return_date else None
            )

            try:
                db.session.add(new_pc)
                db.session.commit()
                message = "Laptop issued successfully."
            except Exception as e:
                message = f"Error issuing laptop: {str(e)}"

        elif action == "return":
            serial_number = request.form["serial_number"]
            pc = PC.query.filter_by(serial_number=serial_number).first()

            if not pc:
                message = "Serial Number doesn't exist."
            elif pc.return_date:
                message = "Laptop has already been returned."
            else:
                pc.return_date = datetime.today()
                db.session.commit()
                message = "Laptop returned successfully."

    return render_template("issue_pc.html", message=message)

# Search PC
@app.route("/search")
def search():
    if not session.get("admin"):
        return redirect(url_for("login"))

    query = request.args.get("query", "").strip()
    pcs = PC.query.filter(
        (PC.coy_number.ilike(f"%{query}%")) |
        (PC.username.ilike(f"%{query}%")) |
        (PC.serial_number.ilike(f"%{query}%"))
    ).all()

    return render_template("dashboard.html", pcs=pcs)

# Logout
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("login"))  # Redirect to login after logout

# Run App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

