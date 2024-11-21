from flask import Blueprint, render_template, redirect, url_for
from db import DB_PATH
import sqlite3

driver_page = Blueprint("driver_page", __name__, url_prefix='/driver')

@driver_page.route("/")
def get_drivers():
    drivers = []
    query = "SELECT game_id FROM drivers ORDER BY game_id ASC"
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        cursor.execute(query)
        drivers = cursor.fetchall()
    return render_template("driver_list.html", drivers=[driver[0] for driver in drivers])

@driver_page.route("/<game_id>/")
def driver_overview(game_id):
    data = []

    # remember: series have unique names
    query = f"SELECT series.id as series_id, series as SERIES, year AS YEAR, RACES, WIN, [TOP 5], [TOP 10], POLE, LAPS, LED, [AV. S], [AV. F], DNF, LLF, POINTS, RANK \
FROM (SELECT *,RANK() OVER(PARTITION BY series, year ORDER BY points DESC) as RANK from points_view) a \
LEFT JOIN series ON series.name = a.series \
where game_id = '{game_id}' \
ORDER BY YEAR ASC"
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        cursor.execute(query)
        header = [col[0] for col in cursor.description]
        header.remove("SERIES")
        header.remove("series_id")
        data = cursor.fetchall()

        # get aggregate data as well (use Nones for things that can't be aggregated)
        # || = concat
        query = f"SELECT series.id as series_id, series AS SERIES, COUNT(*) || ' years', SUM(RACES), SUM(WIN), SUM([TOP 5]), SUM([TOP 10]), SUM(POLE), SUM(LAPS), SUM(LED), '---', '---', SUM(DNF), SUM(LLF), SUM(POINTS), '---' FROM points_view \
        LEFT JOIN series ON series.name = points_view.series \
        WHERE game_id = '{game_id}' GROUP BY series"
        cursor.execute(query)
        data += cursor.fetchall()

    # create dictionary out of it; keys = (series_id, series_name), values = rest of record
    records_by_series = {}
    for season_record in data:
        if tuple(season_record[:2]) not in records_by_series.keys():
            records_by_series[tuple(season_record[:2])] = [season_record[2:]]
        else:
            records_by_series[tuple(season_record[:2])].append(season_record[2:])

    return render_template('driver.html', header=header, series_records=records_by_series, driver=game_id)

@driver_page.route("/<game_id>/<series_id>/<filter>/")
def driver_results_by_series(game_id: str, series_id: int, filter:str):
    """list race results of a driver for a given series across all seasons, ordered by season and then race ID"""
    data = []
    filter_dict = {'all': '', 'win': 'AND Finish = 1', 'top5': 'AND Finish <= 5', 'top10': 'AND Finish <=10', 'pole': 'AND Start = 1'}
    
    query = f"SELECT Year, Race, Track, Driver_Name, Finish, Start, Number, Interval, Laps, Led, Points, Status FROM driver_race_records WHERE Driver_Name = '{game_id}' AND series_id = {series_id} {filter_dict[filter]} ORDER BY Year ASC, Race_ID ASC"

    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        headers = [h[0] for h in cursor.description]
        series_name = get_series_name_from_id(series_id, cursor)

    # create list of dicts
    records = []
    for record in data:
        record_dict = {}
        for i, header in enumerate(headers):
            record_dict.update({header: record[i]})
        records.append(record_dict)

    return render_template('driver_season.html', records=records, series=series_name, driver=game_id, headers=headers)

@driver_page.route("/<game_id>/<series_id>/<season_num>")
def driver_results_by_season(game_id: str, series_id: int, season_num: int):
    """Return results of a driver for a given season of a series."""
    data = []
    series_name = ""

    query = f"SELECT Year, Race, Track, Driver_Name, Finish, Start, Number, Interval, Laps, Led, Points, Status FROM driver_race_records WHERE Driver_Name = '{game_id}' AND series_id = {series_id} AND Year = {season_num}"

    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()

        cursor.execute(query)
        data = cursor.fetchall()
        headers = [h[0] for h in cursor.description]
        series_name = get_series_name_from_id(series_id, cursor)

    # create list of dicts
    records = []
    for record in data:
        record_dict = {}
        for i, header in enumerate(headers):
            record_dict.update({header: record[i]})
        records.append(record_dict)


    return render_template('driver_season.html', records=records, series=series_name, season=season_num, driver=game_id, headers=headers)

def get_series_name_from_id(series_id: int, cursor: sqlite3.Cursor):
    return cursor.execute(f"SELECT name FROM series WHERE id = {series_id}").fetchone()[0]

@driver_page.route("/<game_id>/delete/", methods=['DELETE'])
def delete_driver(game_id: str):
    # each query string can only have one statement
    pragma_query = "PRAGMA foreign_keys = ON"
    delete_query = f"DELETE FROM drivers WHERE game_id = '{game_id}';"
    with sqlite3.connect(DB_PATH) as con:
        try:
            cursor = con.cursor()
            cursor.execute(pragma_query)
            cursor.execute(delete_query)
        except sqlite3.Error as e:
            print(f"ERROR: {str(e)}")
    # this creates a redirect response object, which must be handled by caller
    return redirect(url_for('driver_page.get_drivers'), code=302)
