from flask import Flask, render_template, request, redirect
import mysql.connector
import os

app = Flask(__name__)


# =========================
# DATABASE CONNECTION
# =========================
def get_db():
    return mysql.connector.connect(
        host=os.environ["MYSQLHOST"],
        port=int(os.environ["MYSQLPORT"]),
        user=os.environ["MYSQLUSER"],
        password=os.environ["MYSQLPASSWORD"],
        database=os.environ["MYSQLDATABASE"]
    )


# =========================
# HOME
# =========================
@app.route("/")
def home():
    return render_template("home.html")


# =========================
# TEAMS
# =========================
@app.route("/teams")
def teams():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM teams
        ORDER BY points DESC
    """)

    teams = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("teams.html", teams=teams)


# =========================
# PLAYERS
# =========================
@app.route("/players")
def players():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM players")
    players = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("players.html", players=players)


# =========================
# MATCHES
# =========================
@app.route("/matches", methods=["GET", "POST"])
def matches():

    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":

        match_id = request.form["match_id"]
        team1 = request.form["team1"]
        team2 = request.form["team2"]
        winner = request.form["winner"]
        match_date = request.form["match_date"]

        # -------------------------
        # ADD MATCH
        # -------------------------
        cursor.execute("""
            INSERT INTO matches
            (match_id, team1, team2, winner, match_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            match_id,
            team1,
            team2,
            winner,
            match_date
        ))

        # -------------------------
        # UPDATE WINNER
        # -------------------------
        cursor.execute("""
            UPDATE teams
            SET
                matches = matches + 1,
                wins = wins + 1,
                points = points + 2
            WHERE teams_name = %s
        """, (winner,))

        # -------------------------
        # UPDATE LOSER
        # -------------------------
        loser = team2 if winner == team1 else team1

        cursor.execute("""
            UPDATE teams
            SET
                matches = matches + 1,
                losses = losses + 1
            WHERE teams_name = %s
        """, (loser,))

        db.commit()

        cursor.close()
        db.close()

        return redirect("/matches")

    # -------------------------
    # SHOW MATCHES
    # -------------------------
    cursor.execute("""
        SELECT *
        FROM matches
        ORDER BY match_date DESC
    """)

    matches = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("matches.html", matches=matches)


# =========================
# POINTS TABLE
# =========================
@app.route("/points")
def points():

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM teams
        ORDER BY points DESC
    """)

    teams = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("points.html", teams=teams)


# =========================
# ADD TEAM
# =========================
@app.route("/add_team", methods=["GET", "POST"])
def add_team():

    if request.method == "POST":

        team_name = request.form["team_name"]

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO teams
            (teams_name, matches, losses, points, run_rate, wins)
            VALUES (%s, 0, 0, 0, 0.00, 0)
        """, (team_name,))

        db.commit()

        cursor.close()
        db.close()

        return redirect("/teams")

    return render_template("add_team.html")


# =========================
# RUN APPLICATION
# =========================
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )