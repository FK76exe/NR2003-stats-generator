from flask import Blueprint, render_template, redirect, url_for, request, abort
from db import DB_PATH
import sqlite3

team_page = Blueprint("team_page", __name__, url_prefix='/team')

@team_page.route("/", methods=['GET', 'POST'])
def view_teams():
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        if request.method == 'GET':
            teams = cursor.execute("SELECT * FROM teams")
            return render_template("./teams/teams_main.html", teams=teams)
        else:
            try:
                cursor.execute(f"""INSERT INTO teams (name) VALUES ("{request.form['name']}")""")
            except sqlite3.OperationalError:
                return abort(400, f"Please make sure the team name is unique and is not in use by any existing team.")
            return redirect(url_for('team_page.view_teams'))
        

@team_page.route("/<id>")
def view_single_team():
    pass