from flask import Flask, render_template, request
from markupsafe import escape
import file_scraper as file_scraper
import sqlite3
from series import series_page
from track import track_page
from driver import driver_page

app = Flask(__name__)
app.register_blueprint(series_page)
app.register_blueprint(track_page)
app.register_blueprint(driver_page)

DATABASE_NAME = "../../db/nr-stats-gen.db"

@app.route("/")
def home():
    season_year_dict = {}
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        cursor.execute("SELECT DISTINCT series.name, season_num as year FROM races, series JOIN seasons ON races.season_id = seasons.id AND seasons.series_id = series.id ORDER BY series.name ASC, year DESC")
        data = cursor.fetchall()
        for row in data:
            s,y = row
            if s not in season_year_dict.keys():
                season_year_dict[s] = [y]
            else:
                season_year_dict[s].append(y)

    return render_template('home.html', season_year_dict=season_year_dict)        

@app.route("/seasons/<series_id>/")
def get_seasons_by_series(series_id):
    """Get all seasons linked to `series_id`"""
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        query = f"SELECT id, season_num FROM seasons WHERE series_id = {series_id}"
        cursor.execute(query)
        data = cursor.fetchall()
        return data

@app.route("/add-race/", methods=['GET', 'POST'])
def add_race():
    # get all series and tracks
    series = []
    tracks = []
    seasons = [2]
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        cursor.execute(f"SELECT * FROM series ORDER BY name")
        series = cursor.fetchall()
        cursor.execute(f"SELECT * FROM tracks ORDER BY track_name")
        tracks = cursor.fetchall()

        if len(series) > 0:
            cursor.execute(f"SELECT id, season_num FROM seasons WHERE series_id = {series[0][0]}")
            seasons = cursor.fetchall()

    # if GET -> present form
    if request.method == 'GET':
        return render_template('add_race.html', tracks=tracks, series=series, seasons=seasons)
    
    # if POST -> add race data
    race_track, race_season = request.form['tracks'], request.form['seasons']
    race_file = request.files['file']
    processed = file_scraper.scrape_race_results(race_file.read().decode("windows-1252"))

    drivers = [(row[3], ) for row in processed[1:]]

    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        cursor.execute(f"INSERT INTO races (season_id, race_file, track_id) VALUES ({int(race_season)}, '{race_file.filename}', {int(race_track)})")
        
        # create drivers if they don't exist
        cursor.executemany(f"INSERT OR IGNORE INTO drivers (game_id) VALUES (?)", drivers)

        # get id of race
        cursor.execute(f"SELECT id FROM races WHERE race_file='{race_file.filename}'")
        race_id = cursor.fetchone()

        # get id of drivers
        cursor.execute(f"SELECT id, game_id FROM drivers")
        driver_data = cursor.fetchall()
        
        driver_id_dict = {}
        for driver in driver_data:
            driver_id_dict[driver[1]] = driver[0]

        # add driver data
        for row in processed[1:]:
            cursor.execute(f"INSERT INTO race_records VALUES ({race_id[0]}, {row[0]}, {row[1]}, {row[2]}, {int(driver_id_dict[row[3]])}, '{row[4]}', {row[5]}, {row[6]}, {row[7]}, '{row[8]}')")

        con.commit()

    return "submitted"