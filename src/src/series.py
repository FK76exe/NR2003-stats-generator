# TODO split this thing between seasons and series (see parenting of blueprints)

from flask import Blueprint, render_template, request, redirect, url_for, abort
from markupsafe import escape
import sqlite3
import file_scraper as file_scraper
from db import DB_PATH

series_page = Blueprint('series_page', __name__, url_prefix='/series')
@series_page.route("/", methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        add_series(request.form)
    return list_all_series()

def add_series(form):
    query = f"INSERT INTO series (name) VALUES ('{form['series_name']}')"
    try:
        with sqlite3.connect(DB_PATH) as con:
            cursor = con.cursor()
            cursor.execute(query)
    except sqlite3.IntegrityError:
        return abort(400, f"Please make sure the series name is unique and does not share its name with an existing series.")
    return list_all_series()

def list_all_series():
    """List all series available"""
    data = []
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        cursor.execute(f"SELECT * FROM series")
        data = cursor.fetchall()
    return render_template("series_list.html", series_list = data)

@series_page.route("/<series_id>/", methods=['GET', 'POST'])
def series_main(series_id):
    if request.method == 'POST':
        # only one form submitted at once - use this to differentiate them
        if "new_series_name" in request.form.keys():
            rename_series(series_id, request.form['new_series_name'])
        else:
            add_season(series_id, request)
    return get_series_info(series_id)

def rename_series(series_id: int, new_name: str):
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        try:
            query = f"UPDATE series SET name='{new_name}' WHERE id={series_id}"
            cursor.execute(query)
            return redirect(url_for('series_page.series_main',series_id=series_id), code=302)
        except sqlite3.IntegrityError:
            return abort(400, "Please ensure the new name is not in use.")

def get_series_info(series_id):
    """Get information about a series by `series_id`"""
    driver_desc = []
    driver_stats = ()
    season_desc = ['Year', 'Races', 'Points Leader']
    season_stats = ()
    series_name = None
    systems = []
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        cursor.execute(f"SELECT COUNT(*) as Seasons, game_id as Driver, sum(RACES) as Races, sum(WIN) as Wins, sum([TOP 5]) as [Top 5s], sum([TOP 10]) as [Top 10s], \
sum(POLE) as Poles, sum(LAPS) as Laps, sum(LED) as Led, sum(DNF) as DNFs, sum(LLF) as LLFs, sum(POINTS) as Points \
from driver_points_view \
LEFT JOIN series on driver_points_view.series = series.name \
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
    FROM driver_points_view
    GROUP BY year, series
) a ON seasons.season_num = a.year AND series.name = a.series
WHERE series.id = {series_id}
GROUP BY season_num
        """)
        season_stats = cursor.fetchall()

        series_name = cursor.execute(f"SELECT name FROM series WHERE id = {series_id}").fetchall()[0][0]
        systems = cursor.execute("SELECT id, name FROM point_systems").fetchall()
    
    return render_template('series.html', driver_headers = driver_desc, driver_stats = driver_stats,
                           season_headers = season_desc, season_stats = season_stats, series = series_name, id = series_id, systems=systems)

@series_page.route("/<series>/<season>/", methods=['GET', 'POST'])
def season_main(series, season):
    """return list of races, with track and winner for a given season."""

    if request.method == 'POST':
        return add_weekend(series, season, request)
    else:
        return get_schedule(series, season)

def get_schedule(series, season):
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()

        season_id_query = f"SELECT id FROM seasons WHERE series_id = {series} AND season_num = {season}"
        # TODO add 404 abort if no results
        season_id = cursor.execute(season_id_query).fetchall()[0][0]

        query = f"SELECT races.id as race_id, name, tracks.id as track_id, track_name AS Track, game_id AS Winner FROM races LEFT JOIN tracks ON track_id = tracks.id LEFT JOIN (SELECT race_id, game_id FROM race_records LEFT JOIN drivers ON driver_id = drivers.id WHERE finish_position = 1) ON race_id = races.id WHERE season_id = {season_id}"
        schedule = [{'race_id': i[0], 'race_name': i[1], 'track_id': i[2], 'track_name': i[3], 'winner': i[4]} for i in cursor.execute(query).fetchall()]

        series_query = f"SELECT name FROM seasons LEFT JOIN series ON seasons.series_id = series.id WHERE seasons.id={season_id}"
        series_name = cursor.execute(series_query).fetchall()

    return render_template('./season/season.html', schedule=schedule, season=season, series_name=series_name[0][0], series=series, tracks=get_tracks())

@series_page.route("/<series>/<season>/points/")
def show_series(series, season):
    data = []

    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        series_name = cursor.execute(f"SELECT name FROM series WHERE id = {series}").fetchall()[0][0]

        query = f"SELECT game_id AS DRIVER, RACES, WIN, [TOP 5], [TOP 10], POLE, LAPS, LED, [AV. S], [AV. F], DNF, LLF, POINTS FROM driver_points_view WHERE series = '{series_name}' AND year = {escape(season)}"
        cursor.execute(query)
        header = ["RANK"] + [col[0] for col in cursor.description]
        data = cursor.fetchall()
    return render_template('./season/season_table.html',header=header, records=data, series=series, season=season)

@series_page.route("/<series>/delete/", methods = ['DELETE'])
def delete_series(series):
    """Delete series based on ID"""
    pragma_query = "PRAGMA foreign_keys = ON;"
    delete_query = f"DELETE FROM series WHERE id = {series}"
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        cursor.execute(pragma_query)
        cursor.execute(delete_query)
        con.commit() # add this, so that everyone can see deletion
    return redirect(url_for('series_page.main'), code=302)

def add_season(series_id, request):
    """Add season to a given series."""
    season_num, points_system = request.form['season_num'], request.form['system']
    query = f"INSERT INTO seasons (series_id, season_num, points_system_id) VALUES ({series_id}, {season_num}, {points_system})"
    
    try:
        with sqlite3.connect(DB_PATH) as con:
            cursor = con.cursor()
            cursor.execute(query)
            con.commit()
        return get_schedule(series_id, season_num)
    except sqlite3.IntegrityError:
        return abort(400, "Please provide a number that is not currently in use.")

@series_page.route("<series>/<season>/delete", methods = ['DELETE'])
def delete_season(series, season):
    """Delete season of a series"""
    pragma_query = "PRAGMA foreign_keys = ON;"
    delete_query = f"DELETE FROM seasons WHERE series_id={series} AND season_num={season}"
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        cursor.execute(pragma_query)
        cursor.execute(delete_query)
        con.commit() # add this, so that everyone can see deletion
    return redirect("../", code=302)

@series_page.route("<series>/<season>/change_points/", methods = ['GET', 'POST'])
def update_points_system(series, season):
    if request.method == 'GET':
        systems = []
        with sqlite3.connect(DB_PATH) as con:
            systems = con.cursor().execute("SELECT id, name FROM point_systems").fetchall()
        return render_template('./season/change_points.html', systems=systems, series=series, season=season)
    else:
        with sqlite3.connect(DB_PATH) as con:
            cursor = con.cursor()
            season_id = cursor.execute(f"SELECT id FROM seasons WHERE series_id = {series} AND season_num = {season}").fetchall()[0][0]
            cursor.execute(f"UPDATE seasons SET points_system_id = {int(request.form['chosen_system'])} WHERE id = {season_id}")
            con.commit()
        return redirect(url_for('series_page.show_series', series=series, season=season))
        
@series_page.route("<series>/<season>/adjust_points/", methods=['GET', 'POST'])
def adjust_points(series, season):
    season_id = get_season_id(series, season)
    if request.method == 'GET':
        drivers = [] # array of dicts with keys ['id', 'game_id']
        with sqlite3.connect(DB_PATH) as con:
            con.row_factory = sqlite3.Row
            cursor = con.cursor()
            drivers = cursor.execute(
                f"SELECT DISTINCT id, game_id AS name, IFNULL(adjustment_points, 0) AS points \
                FROM drivers \
                LEFT JOIN driver_race_records ON drivers.id = driver_race_records.Driver_ID \
                LEFT JOIN manual_points ON drivers.id = manual_points.driver_id AND manual_points.season_id = driver_race_records.Season_ID \
                WHERE Series_ID = {series} AND driver_race_records.Season_ID = {season_id} ORDER BY game_id ASC"
                ).fetchall()
            entrants = cursor.execute(f"SELECT entrants.id, number, IFNULL(adjustment_points, 0) AS points \
                        FROM entrants LEFT JOIN entrant_manual_points ON entrants.id = entrant_manual_points.entrant_id WHERE entrants.season_id = {season_id}")
            return render_template('./season/adjust_points.html',drivers=drivers, entrants=entrants, series=series, season=season)
    
    # insert only those who have nonzero total (efficiency... I think? idk)
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        form = request.form
        for input in form.keys():
                # first, determine if it is driver or entrant -> then query correct table
                points = int(form[input])
                if input[0] == 'd':
                    driver_id = int(input[2:]) # prefix is d-
                    # this is an upsert clause (if insert violates something -> update)
                    cursor.execute(f"INSERT INTO manual_points VALUES ({driver_id}, {season_id}, {points}) \
                                    ON CONFLICT (driver_id, season_id) DO UPDATE SET adjustment_points={points}")
                else:
                    entrant_id = int(input[2:]) # prefix is e-
                    cursor.execute(f"INSERT INTO entrant_manual_points (entrant_id, adjustment_points) VALUES ({entrant_id}, {points}) \
                                    ON CONFLICT (entrant_id) DO UPDATE SET adjustment_points={points}")
        con.commit()
    return redirect(url_for('series_page.show_series', series=series, season=season))

@series_page.route("<series>/<season>/entrants/", methods=['GET', 'POST'])
def view_entrants(series, season):
    if request.method == 'GET':
        entrants = []
        teams = []
        with sqlite3.connect(DB_PATH) as con:
            con.row_factory = sqlite3.Row
            cursor = con.cursor()
            season_id = get_season_id(series, season)
            entrants = cursor.execute(f'SELECT * FROM entrants WHERE season_id = {season_id} ORDER BY number ASC').fetchall()
            teams = cursor.execute(f'SELECT * FROM teams ORDER BY name ASC').fetchall()
            return render_template('./season/entrants.html', entrants=entrants, series=series, season=season, teams=teams)

    # add
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cursor = con.cursor()
        season_id = get_season_id(series, season)
        entrant_team_tuples = [(int(request.form[entrant_id]), int(entrant_id)) for entrant_id in request.form.keys()]
        cursor.executemany(f"UPDATE entrants SET team_id = ? WHERE id = ?", entrant_team_tuples)
    return redirect(url_for('series_page.view_entrants', series=series, season=season))

def get_season_id(series_id, season_num):
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        return cursor.execute(f"SELECT id FROM seasons WHERE season_num={season_num} AND series_id={series_id}").fetchall()[0][0]

def add_weekend(series, season, request):
    """Add a weekend (HTML file) to a given season"""

    race_name = request.form['name']
    race_track = request.form['track']
    race_file = request.files['file']

    weekend_dict = file_scraper.scrape_results(race_file.read().decode("windows-1252"))
    
    # drivers/entrants - from all sessions (in case of a dns)
    drivers = set()
    entrant_nums = set()
    if 'Practice' in weekend_dict.keys():
        # a | b = union of set a and set b
        drivers = drivers | set((row[2], ) for row in weekend_dict['Practice'])
        entrant_nums = entrant_nums | set((row[1], ) for row in weekend_dict['Practice'])
    if 'Happy Hour' in weekend_dict.keys():
        drivers = drivers | set((row[2], ) for row in weekend_dict['Happy Hour'])
        entrant_nums = entrant_nums | set((row[1], ) for row in weekend_dict['Happy Hour'])
    drivers = drivers | set((row[2], ) for row in weekend_dict['Qualifying']) | set((row[3], ) for row in weekend_dict['Race'])
    entrant_nums = entrant_nums | set((row[1], ) for row in weekend_dict['Qualifying']) | set((row[2], ) for row in weekend_dict['Race'])
    entrant_nums = [int(num[0]) for num in entrant_nums]

    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()

        # get season id
        cursor.execute(f"SELECT id FROM seasons WHERE series_id={series} AND season_num={season}")
        season_id = cursor.fetchone()[0]
        
        # get new race id
        cursor.execute(f"INSERT INTO races (name, season_id, race_file, track_id) VALUES ('{race_name}', {int(season_id)}, '{race_file.filename}', {int(race_track)})")
        race_id = cursor.lastrowid

        # create drivers if they don't exist
        cursor.executemany(f"INSERT OR IGNORE INTO drivers (game_id) VALUES (?)", drivers)

        
        # create entries if they don't exist; create a map for record entry
        entrant_dict = {}
        existing_entrants = cursor.execute(f"SELECT id, number FROM entrants WHERE season_id = {season_id}").fetchall()
        for entrant in existing_entrants:
            entrant_dict[entrant[1]] = entrant[0]

        for num in entrant_nums:
            if num not in entrant_dict.keys():
                cursor.execute(f"INSERT INTO entrants (season_id, number) VALUES ({season_id}, {num})")
                entrant_dict[num] = cursor.lastrowid

        # get id of drivers
        cursor.execute(f"SELECT id, game_id FROM drivers")
        driver_ids = cursor.fetchall()
        
        driver_id_dict = {} # map id to game id
        for driver in driver_ids:
            driver_id_dict[driver[1]] = driver[0]

        # add driver data
        session_ids = {'Practice': 1, 'Qualifying': 2, 'Happy Hour': 3}
        for session in weekend_dict.keys():
            if session in session_ids.keys():
                timed_session_list = [
                    [race_id, session_ids[session], record[0], record[1],  driver_id_dict[record[2]], record[3]]
                    for record in weekend_dict[session]]
                cursor.executemany("INSERT INTO timed_sessions (race_id, type, position, number, driver_id, time) VALUES (?, ?, ?, ?, ?, ?)", timed_session_list)
            elif session == 'Race':
                race_list = [[race_id] + record[:3] + [driver_id_dict[record[3]]] + [str(record[4])] + record[5:8] + [str(record[8]), entrant_dict[int(record[2])]] for record in weekend_dict[session]] 
                cursor.executemany("INSERT INTO race_records (race_id, finish_position, start_position, car_number, driver_id, interval, laps, led, points, finish_status, entrant_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", race_list) 
            else: # penalties
                if len(weekend_dict[session]) > 0:
                    penalty_list = [[race_id] + record for record in weekend_dict[session]]
                    cursor.execute("INSERT INTO penalties (race_id, lap, number, infraction, penalty) VALUES (?, ?, ?, ?, ?)", penalty_list)
        con.commit()

    return get_schedule(series, season)

def get_tracks() -> tuple[tuple]:
    """Get id and name of all tracks registered in database."""
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        cursor.execute("SELECT id, track_name FROM tracks ORDER BY track_name ASC")
        return cursor.fetchall()
    
@series_page.route("/<series_id>/<season_num>/entrant_points/")
def get_entrant_points(series_id, season_num):
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cursor = con.cursor()
        query = f"SELECT Number as NUMBER, Team_ID, Team_Name AS TEAM, RACE, WIN, [TOP 5], [TOP 10], POLE, LAPS, LED, [Av. S], [Av. F], DNF, LLF, POINTS FROM entrant_points_view WHERE Series_ID={series_id} AND Year={season_num}"
        data = cursor.execute(query).fetchall()
        headers = [i[0] for i in cursor.description]
        return render_template("./season/entrant_points.html", headers=headers, records=data, series=series_id, season=season_num)
