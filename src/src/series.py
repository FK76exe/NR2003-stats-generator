from flask import Blueprint, render_template, request, redirect, url_for
from markupsafe import escape
import sqlite3
import file_scraper as file_scraper

series_page = Blueprint('series_page', __name__, url_prefix='/series')
DATABASE_NAME = "../../db/nr-stats-gen.db"

@series_page.route("/", methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        add_series(request.form)
    return list_all_series()

def add_series(form):
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

@series_page.route("/<series>/<season>/", methods=['GET', 'POST'])
def season_main(series, season):
    """return list of races, with track and winner for a given season."""
    
    if request.method == 'POST':
        return add_weekend(series, season, request)
    else:
        return get_schedule(series, season)

def get_schedule(series, season):
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()

        season_id_query = f"SELECT id FROM seasons WHERE series_id = {series} AND season_num = {season}"
        season_id = cursor.execute(season_id_query).fetchall()[0][0]

        query = f"SELECT races.id as race_id, name, tracks.id as track_id, track_name AS Track, game_id AS Winner FROM races LEFT JOIN tracks ON track_id = tracks.id LEFT JOIN (SELECT race_id, game_id FROM race_records LEFT JOIN drivers ON driver_id = drivers.id WHERE finish_position = 1) ON race_id = races.id WHERE season_id = {season_id}"
        schedule = [{'race_id': i[0], 'race_name': i[1], 'track_id': i[2], 'track_name': i[3], 'winner': i[4]} for i in cursor.execute(query).fetchall()]

        series_query = f"SELECT name FROM seasons LEFT JOIN series ON seasons.series_id = series.id WHERE seasons.id={season_id}"
        series_name = cursor.execute(series_query).fetchall()

    return render_template('season.html', schedule=schedule, season=season, series_name=series_name[0][0], series=series, tracks=get_tracks())

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

@series_page.route("/<series>/add-season/", methods = ['POST'])
def add_season(series):
    """Add season to a given series."""
    season_num = request.form['season_num']
    query = f"INSERT INTO seasons (series_id, season_num) VALUES ({series}, {season_num})"
    
    try:
        with sqlite3.connect(DATABASE_NAME) as con:
            cursor = con.cursor()
            cursor.execute(query)
            con.commit()
        return get_schedule(series, season_num)
    except sqlite3.IntegrityError as e:
        return f"""
    <html>
        <b>ERROR</b>
        {str(e)}
        <a href="../">Go back to series page</a>
    </html>
    """

@series_page.route("<series>/<season>/delete", methods = ['DELETE'])
def delete_season(series, season):
    """Delete season of a series"""
    pragma_query = "PRAGMA foreign_keys = ON;"
    delete_query = f"DELETE FROM seasons WHERE series_id={series} AND season_num={season}"
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        cursor.execute(pragma_query)
        cursor.execute(delete_query)
        con.commit() # add this, so that everyone can see deletion
    return redirect("../", code=302)

def add_weekend(series, season, request):
    """Add a weekend (HTML file) to a given season"""

    race_name = request.form['name']
    race_track = request.form['track']
    race_file = request.files['file']
    weekend_dict = file_scraper.scrape_results(race_file.read().decode("windows-1252"))

    drivers = [(row[3], ) for row in weekend_dict['Race']]

    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()

        # get season id
        cursor.execute(f"SELECT id FROM seasons WHERE series_id={series} AND season_num={season}")
        race_season = cursor.fetchone()[0]
        
        cursor.execute(f"INSERT INTO races (name, season_id, race_file, track_id) VALUES ('{race_name}', {int(race_season)}, '{race_file.filename}', {int(race_track)})")
        race_id = cursor.lastrowid

        # create drivers if they don't exist
        cursor.executemany(f"INSERT OR IGNORE INTO drivers (game_id) VALUES (?)", drivers)

        # get id of drivers
        cursor.execute(f"SELECT id, game_id FROM drivers")
        driver_data = cursor.fetchall()
        
        driver_id_dict = {} # map id to game id
        for driver in driver_data:
            driver_id_dict[driver[1]] = driver[0]

        # add driver data
        for session in weekend_dict.keys():
            match session:
                case 'Practice':
                    practice_list = [[race_id, 1, record[0], record[1], 
                                      driver_id_dict[record[2]], record[3]
                     ] for record in weekend_dict[session]]
                    cursor.executemany("INSERT INTO timed_sessions (race_id, type, position, number, driver_id, time) VALUES (?, ?, ?, ?, ?, ?)", practice_list) 
                case 'Qualifying':
                    qualifying_list = [[race_id, 2, record[0], record[1], 
                                      driver_id_dict[record[2]], record[3]
                     ] for record in weekend_dict[session]]
                    cursor.executemany("INSERT INTO timed_sessions (race_id, type, position, number, driver_id, time) VALUES (?, ?, ?, ?, ?, ?)", qualifying_list)
                case 'Happy Hour':
                    happy_hour_list = [[race_id,3, record[0], record[1], 
                                      driver_id_dict[record[2]], record[3]
                     ] for record in weekend_dict[session]]
                    cursor.executemany("INSERT INTO timed_sessions (race_id, type, position, number, driver_id, time) VALUES (?, ?, ?, ?, ?, ?)", happy_hour_list)   
                case 'Race':
                    race_list = [[race_id] + record[:3] + [driver_id_dict[record[3]]] + [str(record[4])] + record[5:8] + [str(record[8])] for record in weekend_dict[session]] 
                    cursor.executemany("INSERT INTO race_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", race_list)
                case 'Penalties':
                    if len(weekend_dict[session]) > 0:
                        penalty_list = [[race_id] + record for record in weekend_dict[session]]
                        cursor.execute("INSERT INTO penalties (race_id, lap, number, infraction, penalty) VALUES (?, ?, ?, ?, ?)", penalty_list)
        con.commit()

    return get_schedule(series, season)

def get_tracks() -> tuple[tuple]:
    """Get id and name of all tracks registered in database."""
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        cursor.execute("SELECT id, track_name FROM tracks")
        return cursor.fetchall()