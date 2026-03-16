from flask import Flask, render_template, request, redirect
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# -------- UPLOAD FOLDER --------

UPLOAD_FOLDER = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------- CATEGORIES --------

categories = [
"Mobile Phone","Wallet","Bag","Laptop","Keys",
"Documents","Jewelry","ID Card","Headphones","Other"
]

# -------- DATABASE --------

def init_db():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS items(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    name TEXT,
    category TEXT,
    description TEXT,
    date TEXT,
    phone TEXT,
    place TEXT,
    image TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS messages(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER,
    message TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS claims(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER,
    proof TEXT,
    phone TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -------- DASHBOARD --------

@app.route("/")
def dashboard():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    lost = c.execute(
        "SELECT COUNT(*) FROM items WHERE type='lost'"
    ).fetchone()[0]

    found = c.execute(
        "SELECT COUNT(*) FROM items WHERE type='found'"
    ).fetchone()[0]

    messages = c.execute("""
    SELECT items.name, messages.message
    FROM messages
    JOIN items ON messages.item_id = items.id
    """).fetchall()

    claims = c.execute("""
    SELECT items.name, claims.proof, claims.phone
    FROM claims
    JOIN items ON claims.item_id = items.id
    """).fetchall()

    notification_count = len(messages) + len(claims)

    conn.close()

    return render_template(
        "dashboard.html",
        lost=lost,
        found=found,
        messages=messages,
        claims=claims,
        notification_count=notification_count
    )

# -------- VIEW ITEMS --------

@app.route("/items")
def items():

    search = request.args.get("search")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if search:
        items = c.execute(
            "SELECT * FROM items WHERE name LIKE ?",
            ("%"+search+"%",)
        ).fetchall()
    else:
        items = c.execute("SELECT * FROM items").fetchall()

    conn.close()

    return render_template("items.html", items=items)

# -------- REPORT ITEM --------

@app.route("/report", methods=["GET","POST"])
def report():

    if request.method == "POST":

        type = request.form["type"]
        name = request.form["name"]
        category = request.form["category"]
        desc = request.form["desc"]
        date = request.form["date"]
        phone = request.form["phone"]
        place = request.form["place"]

        image = request.files["image"]

        filename = None

        if image and image.filename != "":
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image.save(filepath)

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("""
        INSERT INTO items(type,name,category,description,date,phone,place,image)
        VALUES (?,?,?,?,?,?,?,?)
        """,(type,name,category,desc,date,phone,place,filename))

        conn.commit()
        conn.close()

        return redirect("/items")

    return render_template("report.html", categories=categories)

# -------- SEND MESSAGE --------

@app.route("/send_message", methods=["POST"])
def send_message():

    item_id = request.form["item_id"]
    message = request.form["message"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    INSERT INTO messages(item_id,message)
    VALUES (?,?)
    """,(item_id,message))

    conn.commit()
    conn.close()

    return redirect("/items")

# -------- CLAIM ITEM --------

@app.route("/claim", methods=["POST"])
def claim():

    item_id = request.form["item_id"]
    proof = request.form["proof"]
    phone = request.form["phone"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    INSERT INTO claims(item_id,proof,phone)
    VALUES (?,?,?)
    """,(item_id,proof,phone))

    conn.commit()
    conn.close()

    return redirect("/items")

# -------- DELETE ITEM --------

@app.route("/delete/<int:item_id>")
def delete_item(item_id):

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()

    conn.close()

    return redirect("/items")

# -------- RUN APP --------

if __name__ == "__main__":
    app.run(debug=True)
