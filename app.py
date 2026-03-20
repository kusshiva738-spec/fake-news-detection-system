from flask import Flask,render_template,request,redirect,session
import sqlite3
import feedparser
import urllib.parse
import secrets

app = Flask(__name__)

# 🔐 Session Secret Key
app.secret_key = "supersecretkey123"

# 👤 Admin Credentials
ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "Shiva@8815"

# DATABASE

def init_db():
    conn = sqlite3.connect("verification.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS verification(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    news TEXT,
    city TEXT,
    status TEXT,
    comment TEXT,
    token TEXT
    )""")

    conn.commit()
    conn.close()

init_db()

# WELCOME PAGE

@app.route("/", methods=["GET","POST"])
def welcome():
    if request.method == "POST":
        name = request.form["name"]
        return redirect(f"/index?name={name}")
    return render_template("welcome.html")

# NEWS CHECK FUNCTION

def check_news(news):

    query = urllib.parse.quote(news)
    url = f"https://news.google.com/rss/search?q={query}"

    feed = feedparser.parse(url)

    if len(feed.entries) > 0:
        source = feed.entries[0].source.title
        date = feed.entries[0].published
        score = 80
        result = "Trusted News Found"
    else:
        source = None
        date = None
        score = 20
        result = "News Not Found in Trusted Sources"

    return result,score,source,date

# INDEX PAGE

@app.route("/index",methods=["GET","POST"])
def index():

    name = request.args.get("name")

    if request.method == "POST":

        news = request.form["news"]

        result,score,source,date = check_news(news)

        email = None
        verification_status = None
        verify_link = None

        if source is None:

            city = "Unknown"

            conn = sqlite3.connect("verification.db")
            c = conn.cursor()

            c.execute("SELECT * FROM verification WHERE news=? AND city=?", (news,city))
            data = c.fetchone()

            if data:
                verification_status = data[4]

            else:
                verification_status = "Under Verification"
                email = "authority@example.com"

                token = secrets.token_hex(16)

                c.execute("INSERT INTO verification(name,news,city,status,token) VALUES(?,?,?,?,?)",
                (name,news,city,"Under Verification",token))

                conn.commit()

                id = c.lastrowid

                verify_link = f"/verify/{id}?token={token}"

            conn.close()

        return render_template("index.html",
        name=name,
        result=result,
        score=score,
        source=source,
        date=date,
        email=email,
        news=news,
        status=verification_status,
        verify_link=verify_link)

    return render_template("index.html",name=name)

# VERIFY PAGE

@app.route("/verify/<int:id>",methods=["GET","POST"])
def verify(id):

    token = request.args.get("token")

    conn = sqlite3.connect("verification.db")
    c = conn.cursor()

    c.execute("SELECT news,token FROM verification WHERE id=?", (id,))
    data = c.fetchone()

    if not data:
        return "<h2>Invalid request</h2>"

    news,db_token = data

    if token != db_token:
        return "<h2>Unauthorized</h2>"

    if request.method == "POST":

        status = request.form["status"]
        comment = request.form["comment"]

        c.execute("UPDATE verification SET status=?,comment=? WHERE id=?",
        (status,comment,id))

        conn.commit()
        conn.close()

        return "<h2>Verification Updated</h2>"

    conn.close()

    return render_template("verify.html",news=news,id=id)

# 🔐 ADMIN LOGIN

@app.route("/admin-login", methods=["GET","POST"])
def admin_login():

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
        else:
            return "<h3>Invalid Credentials</h3>"

    return render_template("admin_login.html")

# 🔐 ADMIN PANEL (PROTECTED)

@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/admin-login")

    conn = sqlite3.connect("verification.db")
    c = conn.cursor()

    c.execute("SELECT * FROM verification ORDER BY id DESC")
    data = c.fetchall()

    c.execute("SELECT COUNT(*) FROM verification")
    total = c.fetchone()[0]

    conn.close()

    return render_template("admin.html",data=data,total=total)

# 🔓 LOGOUT

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")

# RUN

if __name__ == "__main__":
    app.run()