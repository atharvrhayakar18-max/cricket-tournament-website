from flask import Flask, render_template, request, redirect
import mysql.connector
import os

app = Flask(__name__)


# Create a new MySQL connection when needed
def get_db():
    return mysql.connector.connect(
        host=os.environ["MYSQLHOST"],
        port=int(os.environ["MYSQLPORT"]),
        user=os.environ["MYSQLUSER"],
        password=os.environ["MYSQLPASSWORD"],
        database=os.environ["MYSQLDATABASE"]
    )


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/teams")
def teams():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM teams")
    teams = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("teams.html", teams=teams)


@app.route("/players")
def players():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM players")
    players = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("players.html", players=players)


@app.route("/matches")
def matches():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM matches")
    matches = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("matches.html", matches=matches)


@app.route("/points")
def points():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT * FROM teams
        ORDER BY points DESC
    """)

    teams = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("points.html", teams=teams)


@app.route("/add_team", methods=["GET", "POST"])
def add_team():

    if request.method == "POST":

        team_name = request.form["team_name"]

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO teams
            (tams_name, matches, losses, points, run_rate, wins)
            VALUES (%s, 0, 0, 0, 0.00, 0)
        """, (team_name,))

        db.commit()

        cursor.close()
        db.close()

        return redirect("/teams")

    return render_template("add_team.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)