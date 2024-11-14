from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3
from db import DB_PATH

points_page = Blueprint("points_page", __name__, url_prefix="/points")

@points_page.route("/add/", methods=['GET', 'POST'])
def add_system():
    system_id = None
    # If GET -> return empty form
    if request.method == 'GET':
        return render_template("./points/add_system.html")
    # if POST -> insert it
    form = request.form
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        # create points system structure
        cursor.execute(f"INSERT INTO point_systems (name) VALUES ('{form['name']}')")
        system_id = cursor.lastrowid

        # add finishing points
        finish_points = []
        for i in range(1, 44):
            finish_points.append((system_id, i, int(form[str(i)])))
        cursor.executemany(f"INSERT INTO point_system_scores VALUES (?, ?, ?)", finish_points)

        # add bonus points
        bonus_points = [
            (system_id, 1, int(form['P'])),
            (system_id, 2, int(form['LL'])),
            (system_id, 3, int(form['MLL']))
        ]
        cursor.executemany(f"INSERT INTO bonus_points VALUES (?, ?, ?)", bonus_points)
        con.commit()
        cursor.close()
    return redirect(url_for('points_page.view_system',id=system_id))

@points_page.route("/<id>/", methods=['GET'])
def view_system(id: int):
    standard_points, bonus_points = [], []
    name = ''
    with sqlite3.connect(DB_PATH) as con:
        # con.row_factory = sqlite3.Row # each row is returned as a Row (see docs - can do mapping, ==, len, iter), not a tuple
        cursor = con.cursor()
        cursor.execute(f"SELECT position, points FROM point_system_scores WHERE system_id = {id}")
        standard_points = cursor.fetchall()
        
        cursor.execute(f"SELECT bonus_condition, points FROM bonus_points WHERE system_id = {id}")
        bonus_points = cursor.fetchall()

        cursor.execute(f"SELECT name FROM point_systems WHERE id = {id}")
        name = cursor.fetchone()[0]

        cursor.close()
    return render_template("./points/view_system.html", standard_points=standard_points, bonus_points=bonus_points, name=name)