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
        

@team_page.route("/<id>", methods=['GET', 'POST', 'DELETE'])
def single_team(id):
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        if request.method == 'GET':
            # retrieve team data
            team_name = cursor.execute(f"SELECT name FROM teams WHERE id = {id}").fetchone()
            if team_name:
                return render_template("./teams/teams_single.html", team_name = team_name[0])
            else:
                return abort(404, "Team with this id does not exist.")
        elif request.method == 'POST':
            # update team name
            cursor.execute(f"UPDATE teams SET name='{request.form['name']}' WHERE id = {id}")
            return redirect(url_for('team_page.single_team', id=id))
        else:
            # delete team
            cursor.execute(f"DELETE FROM teams WHERE id = {id}")
            return redirect(url_for('team_page.view_teams'), 303) # HTTP 303 (See Other): redirect to new URL with GET
    