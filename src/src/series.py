from flask import Blueprint, render_template, request, redirect, url_for
from markupsafe import escape
import sqlite3

series_page = Blueprint('series_page', __name__, url_prefix='/series')
DATABASE_NAME = "../../db/nr-stats-gen.db"

@series_page.route("/", methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        add_track(request.form)
    return list_all_series()

def add_track(form):
    query = f"INSERT INTO series (name) VALUES ('{form['series_name']}')"
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        cursor.execute(query)
    return list_all_series()

def list_all_series():
    """List all series available"""
    data = []
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        cursor.execute(f"SELECT * FROM series")
        data = cursor.fetchall()
    return render_template("series_list.html", series_list = data)

@series_page.route("/<series_id>/")
def get_series_info(series_id):
    """Get information about a series by `series_id`"""
    driver_desc = []
    driver_stats = ()
    season_desc = ['Year', 'Races', 'Points Leader']
    season_stats = ()
    series_name = None
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        cursor.execute(f"SELECT COUNT(*) as Seasons, game_id as Driver, sum(RACES) as Races, sum(WIN) as Wins, sum([TOP 5]) as [Top 5s], sum([TOP 10]) as [Top 10s], \
sum(POLE) as Poles, sum(LAPS) as Laps, sum(LED) as Led, sum(DNF) as DNFs, sum(LLF) as LLFs, sum(POINTS) as Points \
from points_view \
LEFT JOIN series on points_view.series = series.name \
WHERE series.id = {series_id} \
group by game_id order by points DESC")
        
        driver_stats = cursor.fetchall()
        driver_desc = cursor.description
        cursor.execute(f"""
        SELECT season_num, COUNT(races.id), game_id
FROM seasons
LEFT JOIN races ON races.season_id = seasons.id
LEFT JOIN series ON seasons.series_id = series.id
LEFT JOIN (
    SELECT year, series, game_id
    FROM points_view
    GROUP BY year, series
) a ON seasons.season_num = a.year AND series.name = a.series
WHERE series.id = {series_id}
GROUP BY season_num
        """)
        season_stats = cursor.fetchall()

        series_name = cursor.execute(f"SELECT name FROM series WHERE id = {series_id}").fetchall()[0][0]
    
    return render_template('series.html', driver_headers = driver_desc, driver_stats = driver_stats,
                           season_headers = season_desc, season_stats = season_stats, series = series_name, id = series_id)

@series_page.route("/<series>/<season>/")
def get_schedule(series, season):
    """return list of races, with track and winner for a given season."""
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()

        season_id_query = f"SELECT id FROM seasons WHERE series_id = {series} AND season_num = {season}"
        print(season_id_query)
        season_id = cursor.execute(season_id_query).fetchall()[0][0]

        query = f"SELECT track_name AS Track, game_id AS Winner FROM races LEFT JOIN tracks ON track_id = tracks.id LEFT JOIN (SELECT race_id, game_id FROM race_records LEFT JOIN drivers ON driver_id = drivers.id WHERE finish_position = 1) ON race_id = races.id WHERE season_id = {season_id}"
        schedule = cursor.execute(query).fetchall()

        series_query = f"SELECT name FROM seasons LEFT JOIN series ON seasons.series_id = series.id WHERE seasons.id={season_id}"
        series_name = cursor.execute(series_query).fetchall()

    return render_template('season.html', schedule=schedule, season=season, series_name=series_name[0][0], series=series)

@series_page.route("/<series>/<season>/points/")
def show_series(series, season):
    data = []

    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        series_name = cursor.execute(f"SELECT name FROM series WHERE id = {series}").fetchall()[0][0]

        query = f"SELECT game_id AS DRIVER, RACES, WIN, [TOP 5], [TOP 10], POLE, LAPS, LED, [AV. S], [AV. F], DNF, LLF, POINTS FROM points_view WHERE series = '{series_name}' AND year = {escape(season)}"
        cursor.execute(query)
        header = ["RANK"] + [col[0] for col in cursor.description]
        data = cursor.fetchall()
    return render_template('season_table.html',header=header, records=data, series=series, season=season)

@series_page.route("/<series>/delete/", methods = ['DELETE'])
def delete_series(series):
    """Delete series based on ID"""
    pragma_query = "PRAGMA foreign_keys = ON;"
    delete_query = f"DELETE FROM series WHERE id = {series}"
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        cursor.execute(pragma_query)
        cursor.execute(delete_query)
        con.commit() # add this, so that everyone can see deletion
    return redirect(url_for('series_page.main'), code=302)