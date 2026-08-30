from flask import Flask, render_template, request, redirect, session
import mysql.connector
import os

app = Flask(__name__)

# =========================
# SECRET KEY
# =========================
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key"
)


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
# ADMIN CHECK
# =========================
def admin_required():
    return session.get("admin_logged_in") is True


# =========================
# HOME
# =========================
@app.route("/")
def home():
    return render_template("home.html")


# =========================
# ADMIN LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        admin_username = os.environ.get("ADMIN_USERNAME", "")
        admin_password = os.environ.get("ADMIN_PASSWORD", "")

        if username == admin_username and password == admin_password:

            session["admin_logged_in"] = True

            return redirect("/admin")

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================
# ADMIN PANEL
# =========================
@app.route("/admin")
def admin():

    if not admin_required():
        return redirect("/login")

    return render_template("admin.html")


# =========================
# TEAMS
# =========================
@app.route("/teams")
def teams():

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            team_id,
            teams_name,
            matches,
            wins,
            losses,
            points,
            run_rate
        FROM teams
        ORDER BY points DESC, wins DESC, run_rate DESC
    """)

    teams_data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "teams.html",
        teams=teams_data
    )


# =========================
# ADD TEAM
# ADMIN ONLY
# =========================
@app.route("/add_team", methods=["GET", "POST"])
def add_team():

    if not admin_required():
        return redirect("/login")

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
            VALUES
            (%s, 0, 0, 0, 0, 0)
        """, (team_name,))

        db.commit()

        cursor.close()
        db.close()

        return redirect("/teams")

    return render_template("add_team.html")


# =========================
# PLAYERS
# =========================
@app.route("/players", methods=["GET", "POST"])
def players():

    db = get_db()
    cursor = db.cursor()

    # -------------------------
    # ADD PLAYER
    # ADMIN ONLY
    # -------------------------
    if request.method == "POST":

        if not admin_required():

            cursor.close()
            db.close()

            return redirect("/login")

        player_name = request.form["player_name"].strip()

        team_id = int(
            request.form["team_id"]
        )

        runs = int(
            request.form.get("runs", 0)
        )

        wickets = int(
            request.form.get("wickets", 0)
        )

        cursor.execute("""
            INSERT INTO players
            (
                player_name,
                team_id,
                runs,
                wickets
            )
            VALUES
            (%s, %s, %s, %s)
        """, (
            player_name,
            team_id,
            runs,
            wickets
        ))

        db.commit()

        cursor.close()
        db.close()

        return redirect("/players")


    # -------------------------
    # GET PLAYERS
    # -------------------------

    cursor.execute("""
        SELECT
            players.player_id,
            players.player_name,
            teams.teams_name,
            players.runs,
            players.wickets
        FROM players
        LEFT JOIN teams
        ON players.team_id = teams.team_id
        ORDER BY players.runs DESC
    """)

    players_data = cursor.fetchall()


    # -------------------------
    # TEAMS FOR DROPDOWN
    # -------------------------

    cursor.execute("""
        SELECT
            team_id,
            teams_name
        FROM teams
        ORDER BY teams_name
    """)

    teams_data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "players.html",
        players=players_data,
        teams=teams_data
    )


# =========================
# MATCHES
# =========================
@app.route("/matches", methods=["GET", "POST"])
def matches():

    # =========================
    # ADD MATCH
    # ADMIN ONLY
    # =========================
    if request.method == "POST":

        if not admin_required():
            return redirect("/login")

        db = get_db()
        cursor = db.cursor()

        try:

            match_id = int(
                request.form["match_id"]
            )

            team1 = request.form["team1"].strip()
            team2 = request.form["team2"].strip()
            winner = request.form["winner"].strip()
            match_date = request.form["match_date"]

            team1_score = int(
                request.form.get("team1_score", 0)
            )

            team1_overs = float(
                request.form.get("team1_overs", 0)
            )

            team2_score = int(
                request.form.get("team2_score", 0)
            )

            team2_overs = float(
                request.form.get("team2_overs", 0)
            )


            # =========================
            # CHECK TEAMS
            # =========================

            cursor.execute("""
                SELECT
                    team_id,
                    teams_name
                FROM teams
                WHERE LOWER(teams_name) IN
                (
                    LOWER(%s),
                    LOWER(%s)
                )
            """, (
                team1,
                team2
            ))

            team_rows = cursor.fetchall()

            if len(team_rows) != 2:

                return (
                    "Error: Team names database "
                    "मधल्या names प्रमाणेच टाका."
                )


            # =========================
            # CHECK WINNER
            # =========================

            if (
                winner.lower() != team1.lower()
                and
                winner.lower() != team2.lower()
            ):

                return (
                    "Error: Winner हा Team 1 "
                    "किंवा Team 2 पैकी एक असला पाहिजे."
                )


            # =========================
            # OVERS CONVERSION
            # =========================

            def convert_overs(overs):

                whole_overs = int(overs)

                balls = round(
                    (overs - whole_overs) * 10
                )

                if balls > 5:
                    balls = 5

                return whole_overs + (
                    balls / 6
                )


            actual_team1_overs = convert_overs(
                team1_overs
            )

            actual_team2_overs = convert_overs(
                team2_overs
            )


            # =========================
            # RUN RATE
            # =========================

            if actual_team1_overs > 0:

                team1_run_rate = (
                    team1_score /
                    actual_team1_overs
                )

            else:

                team1_run_rate = 0


            if actual_team2_overs > 0:

                team2_run_rate = (
                    team2_score /
                    actual_team2_overs
                )

            else:

                team2_run_rate = 0


            # =========================
            # INSERT MATCH
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
                VALUES
                (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
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
            # =========================

            if winner.lower() == team1.lower():

                winner_run_rate = (
                    team1_run_rate
                )

                loser = team2

                loser_run_rate = (
                    team2_run_rate
                )

            else:

                winner_run_rate = (
                    team2_run_rate
                )

                loser = team1

                loser_run_rate = (
                    team1_run_rate
                )


            # =========================
            # WINNER UPDATE
            # =========================

            cursor.execute("""
                UPDATE teams
                SET
                    matches = matches + 1,
                    wins = wins + 1,
                    points = points + 2,
                    run_rate = %s
                WHERE LOWER(teams_name)
                    = LOWER(%s)
            """, (
                winner_run_rate,
                winner
            ))


            # =========================
            # LOSER UPDATE
            # =========================

            cursor.execute("""
                UPDATE teams
                SET
                    matches = matches + 1,
                    losses = losses + 1,
                    run_rate = %s
                WHERE LOWER(teams_name)
                    = LOWER(%s)
            """, (
                loser_run_rate,
                loser
            ))


            # =========================
            # SAVE
            # =========================

            db.commit()

        except Exception as e:

            db.rollback()

            cursor.close()
            db.close()

            return "Error: " + str(e)

        cursor.close()
        db.close()

        return redirect("/matches")


    # =========================
    # SHOW MATCHES
    # =========================

    db = get_db()
    cursor = db.cursor()

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
        SELECT
            team_id,
            teams_name,
            matches,
            wins,
            losses,
            points,
            run_rate
        FROM teams
        ORDER BY
            points DESC,
            wins DESC,
            run_rate DESC
    """)

    teams_data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "points.html",
        teams=teams_data
    )


# =========================
# RUN APPLICATION
# =========================
if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )