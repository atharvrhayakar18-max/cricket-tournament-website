from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="atharv@774384",
    database="my_first_db"
)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/teams")
def teams():
    cursor = db.cursor()

    cursor.execute("SELECT * FROM teams")

    teams = cursor.fetchall()

    cursor.close()

    return render_template("teams.html", teams=teams)


@app.route("/players")
def players():
    cursor = db.cursor()

    cursor.execute("SELECT * FROM players")

    players = cursor.fetchall()

    cursor.close()

    return render_template("players.html", players=players)


@app.route("/matches")
def matches():
    cursor = db.cursor()

    cursor.execute("SELECT * FROM matches")

    matches = cursor.fetchall()

    cursor.close()

    return render_template("matches.html", matches=matches)


@app.route("/points")
def points():
    cursor = db.cursor()

    cursor.execute("""
        SELECT * FROM teams
        ORDER BY points DESC
    """)

    teams = cursor.fetchall()

    cursor.close()

    return render_template("points.html", teams=teams)


@app.route("/add_team", methods=["GET", "POST"])
def add_team():

    if request.method == "POST":

        team_name = request.form["team_name"]

        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO teams
            (tams_name, matches, losses, points, run_rate, wins)
            VALUES (%s, 0, 0, 0, 0.00, 0)
        """, (team_name,))

        db.commit()

        cursor.close()

        return redirect("/teams")

    return render_template("add_team.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000,debug=True)
