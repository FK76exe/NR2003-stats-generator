from flask import Flask, render_template
from markupsafe import escape
import sqlite3

app = Flask(__name__)

DATABASE_NAME = "../db/nr-stats-gen.db"

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/<name>")
def hello(name):
    return f"Hello, {escape(name)}!"

@app.route("/points/<series>/<year>")
def show_series(series, year):
    data = []
    query = f"SELECT game_id AS DRIVER, RACES, WIN, [TOP 5], [TOP 10], POLE, LAPS, LED, [AV. S], [AV. F], DNF, LLF, POINTS FROM points_view WHERE series = '{escape(series)}' AND year = {escape(year)}"
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        cursor.execute(query)
        header = ["RANK"] + [col[0] for col in cursor.description]
        data = cursor.fetchall()
    return render_template('season_table.html',header=header, records=data)

@app.route("/driver/<game_id>")
def driver_data(game_id):
    data = []
    for i, char in enumerate(game_id):
        if char == '_':
            game_id = game_id[:i] + " " + game_id[i+1:]
    query = f"SELECT year AS YEAR, series as SERIES, RACES, WIN, [TOP 5], [TOP 10], POLE, LAPS, LED, [AV. S], [AV. F], DNF, LLF, POINTS FROM points_view WHERE game_id = '{game_id}' ORDER BY YEAR ASC"
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        cursor.execute(query)
        header = [col[0] for col in cursor.description]
        header.remove("SERIES")
        data = cursor.fetchall()

        # get aggregate data as well (use Nones for things that can't be aggregated)
        query = f"SELECT COUNT(*) || ' years', series as SERIES, SUM(RACES), SUM(WIN), SUM([TOP 5]), SUM([TOP 10]), SUM(POLE), SUM(LAPS), SUM(LED), '---', '---', SUM(DNF), SUM(LLF), SUM(POINTS) FROM points_view WHERE game_id = '{game_id}' GROUP BY series"
        cursor.execute(query)
        data += cursor.fetchall()

    # create dictionary out of it
    records_by_series = {}
    for season_record in data:
        if season_record[1] not in records_by_series.keys():
            records_by_series[season_record[1]] = [season_record[:1] + season_record[2:]]
        else:
            records_by_series[season_record[1]].append(season_record[:1] + season_record[2:])

    return render_template('driver.html', header=header, series_records=records_by_series, driver=game_id)


# TODO
"""
- driver stats (per-season and result, wiki style)
- race-by-race (wikipedia style)
- season/series overview
- track stats
"""