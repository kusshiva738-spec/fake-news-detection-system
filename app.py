
from flask import Flask,render_template,request
import sqlite3
import feedparser
import urllib.parse
import secrets

app = Flask(__name__)

# DATABASE

def init_db():
    conn = sqlite3.connect("verification.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS verification(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news TEXT,
    city TEXT,
    status TEXT,
    comment TEXT,
    token TEXT
    )""")

    conn.commit()
    conn.close()

init_db()


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


# HOME PAGE

@app.route("/",methods=["GET","POST"])
def index():

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
                verification_status = data[3]

            else:
                verification_status = "Under Verification"
                email = "authority@example.com"

                token = secrets.token_hex(16)

                c.execute("INSERT INTO verification(news,city,status,token) VALUES(?,?,?,?)",
                (news,city,"Under Verification",token))

                conn.commit()

                id = c.lastrowid

                verify_link = verify_link = f"/verify/{id}?token={token}"
            conn.close()

        return render_template("index.html",
        result=result,
        score=score,
        source=source,
        date=date,
        email=email,
        news=news,
        status=verification_status,
        verify_link=verify_link)

    return render_template("index.html")


# VERIFY PAGE

@app.route("/verify/<int:id>",methods=["GET","POST"])
def verify(id):

    token = request.args.get("token")

    conn = sqlite3.connect("verification.db")
    c = conn.cursor()

    c.execute("SELECT news,token FROM verification WHERE id=?", (id,))
    data = c.fetchone()

    if not data:
        return "<h2>Invalid verification request</h2>"

    news,db_token = data

    if token != db_token:
        return "<h2>Unauthorized verification link</h2>"

    if request.method == "POST":

        status = request.form["status"]
        comment = request.form["comment"]

        c.execute("UPDATE verification SET status=?,comment=? WHERE id=?",
        (status,comment,id))

        conn.commit()
        conn.close()

        return "<h2>Verification Updated Successfully</h2>"

    conn.close()

    return render_template("verify.html",news=news,id=id)


# ADMIN PANEL

@app.route("/admin")
def admin():

    conn = sqlite3.connect("verification.db")
    c = conn.cursor()

    c.execute("SELECT * FROM verification ORDER BY id DESC")
    data = c.fetchall()

    c.execute("SELECT COUNT(*) FROM verification")
    total = c.fetchone()[0]

    conn.close()

    return render_template("admin.html",data=data,total=total)


if __name__ == "__main__":
    app.run()

