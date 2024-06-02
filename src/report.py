from flask import Flask, render_template, request
from markupsafe import escape
import file_scraper
import sqlite3

app = Flask(__name__)

DATABASE_NAME = "../db/nr-stats-gen.db"

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/add-race", methods=['GET', 'POST'])
def add_race():
    # get all series and tracks
    series = []
    tracks = []
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        cursor.execute(f"SELECT * FROM series ORDER BY name")
        series = cursor.fetchall()
        cursor.execute(f"SELECT * FROM tracks ORDER BY track_name")
        tracks = cursor.fetchall()

    # if GET -> present form
    if request.method == 'GET':
        return render_template('add_race.html', tracks=tracks, series=series)
    # if POST -> add race data
    race_series, race_year, race_track = request.form['series'], request.form['year'], request.form['tracks']
    race_file = request.files['file']
    processed = file_scraper.scrape_race_results(race_file.read().decode("windows-1252"))

    drivers = [(row[3], ) for row in processed[1:]]

    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        cursor.execute(f"INSERT INTO races (series, year, race_file, track_id) VALUES ({int(race_series)}, {int(race_year)}, '{race_file.name}', {int(race_track)})")
        
        # create drivers if they don't exist
        cursor.executemany(f"INSERT OR IGNORE INTO drivers (game_id) VALUES (?)", drivers)

        # get id of race
        cursor.execute(f"SELECT id FROM races WHERE race_file='{race_file.name}'")
        race_id = cursor.fetchone()

        # get id of drivers
        cursor.execute(f"SELECT id, game_id FROM drivers")
        driver_data = cursor.fetchall()
        
        driver_id_dict = {}
        for driver in driver_data:
            driver_id_dict[driver[1]] = driver[0]

        # add driver data
        for row in processed[1:]:
            print(f"INSERT INTO race_records ({race_id[0]}, {row[0]}, {row[1]}, {row[2]}, {int(driver_id_dict[row[3]])}, {row[4]}, {row[5]}, {row[6]}, {row[7]}, '{row[8]}')")
            cursor.execute(f"INSERT INTO race_records VALUES ({race_id[0]}, {row[0]}, {row[1]}, {row[2]}, {int(driver_id_dict[row[3]])}, '{row[4]}', {row[5]}, {row[6]}, {row[7]}, '{row[8]}')")

        con.commit()

    return "submitted"


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