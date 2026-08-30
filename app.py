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

    teams_data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("teams.html", teams=teams_data)


# =========================
# PLAYERS
# =========================
@app.route("/players")
def players():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM players")
    players_data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("players.html", players=players_data)


# =========================
# MATCHES
# =========================
@app.route("/matches", methods=["GET", "POST"])
def matches():

    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":

        match_id = request.form["match_id"]
        team1 = request.form["team1"].strip()
        team2 = request.form["team2"].strip()
        winner = request.form["winner"].strip()
        match_date = request.form["match_date"]

        team1_score = int(request.form.get("team1_score", 0))
        team1_overs = float(request.form.get("team1_overs", 0))
        team2_score = int(request.form.get("team2_score", 0))
        team2_overs = float(request.form.get("team2_overs", 0))

        # =========================
        # ADD MATCH
        # =========================
        cursor.execute("""
            INSERT INTO matches
            (
                match_id,
                team1,
                team2,
                winner,
                match_date,
                team1_score,
                team1_overs,
                team2_score,
                team2_overs
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            match_id,
            team1,
            team2,
            winner,
            match_date,
            team1_score,
            team1_overs,
            team2_score,
            team2_overs
        ))

        # =========================
        # UPDATE WINNER
        # Case-insensitive
        # =========================
        cursor.execute("""
            UPDATE teams
            SET
                matches = matches + 1,
                wins = wins + 1,
                points = points + 2
            WHERE LOWER(teams_name) = LOWER(%s)
        """, (winner,))

        # =========================
        # UPDATE LOSER
        # =========================
        if winner.lower() == team1.lower():
            loser = team2
        else:
            loser = team1

        cursor.execute("""
            UPDATE teams
            SET
                matches = matches + 1,
                losses = losses + 1
            WHERE LOWER(teams_name) = LOWER(%s)
        """, (loser,))

        db.commit()

        cursor.close()
        db.close()

        return redirect("/matches")


    # =========================
    # SHOW MATCHES
    # =========================
    cursor.execute("""
        SELECT
            match_id,
            team1,
            team2,
            winner,
            match_date,
            team1_score,
            team1_overs,
            team2_score,
            team2_overs
        FROM matches
        ORDER BY match_date DESC
    """)

    matches_data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "matches.html",
        matches=matches_data
    )


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
        ORDER BY points DESC, wins DESC, run_rate DESC
    """)

    teams_data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "points.html",
        teams=teams_data
    )


# =========================
# ADD TEAM
# =========================
@app.route("/add_team", methods=["GET", "POST"])
def add_team():

    if request.method == "POST":

        team_name = request.form["team_name"].strip()

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO teams
            (
                teams_name,
                matches,
                wins,
                losses,
                points,
                run_rate
            )
            VALUES (%s, 0, 0, 0, 0, 0)
        """, (team_name,))

        db.commit()

        cursor.close()
        db.close()

        return redirect("/teams")

    return render_template("add_team.html")


# =========================
# RUN APP
# =========================
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )