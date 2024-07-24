from flask import Blueprint, render_template, request
import sqlite3

driver_page = Blueprint("driver_page", __name__, url_prefix='/driver')
DATABASE_NAME = "../../db/nr-stats-gen.db"
# use this as a base, then add where clauses onto it in practice
GET_DRIVER_RESULTS_QUERY = "season_num, race_name, track_name, finish_position, start_position, car_number, interval, laps, led, points, finish_status \
FROM race_records \
LEFT JOIN drivers ON driver_id = drivers.id \
RIGHT JOIN ( \
    SELECT season_num, series_id,races.id, IFNULL(name, track_name) as race_name, track_name \
    FROM races \
    LEFT JOIN tracks ON races.track_id = tracks.id \
    RIGHT JOIN (SELECT season_num, series_id, id AS season_id FROM seasons) a ON races.season_id = a.season_id \
) b ON race_records.race_id = b.id"
RACE_RECORD_HEADER = ['Season','Race', 'Track', 'Finish', 'Start', 'Car #', 'Interval', 'Laps', 'Led', 'Points', 'Status']

@driver_page.route("/<game_id>/")
def driver_overview(game_id):
    data = []

    # remember: series have unique names
    query = f"SELECT series.id as series_id, series as SERIES, year AS YEAR, RACES, WIN, [TOP 5], [TOP 10], POLE, LAPS, LED, [AV. S], [AV. F], DNF, LLF, POINTS, RANK \
FROM (SELECT *,RANK() OVER(PARTITION BY series, year ORDER BY points DESC) as RANK from points_view) a \
LEFT JOIN series ON series.name = a.series \
where game_id = '{game_id}' \
ORDER BY YEAR ASC"
    with sqlite3.connect(DATABASE_NAME) as con:
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
    filter_dict = {'all': '', 'win': 'AND finish_position = 1', 'top5': 'AND finish_position <= 5', 'top10': 'AND finish_position <=10', 'pole': 'AND start_position = 1'}
    
    query = f"SELECT {GET_DRIVER_RESULTS_QUERY} WHERE game_id = '{game_id}' AND series_id = {series_id} {filter_dict[filter]} ORDER BY season_num ASC, race_id ASC"
    
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        series_name = get_series_name_from_id(series_id, cursor)

    return render_template('driver_season.html', records=data, series=series_name, driver=game_id, headers=RACE_RECORD_HEADER)

"""
race name (or track if null) | track | finish | start | # | interval | led | points | status
"""

@driver_page.route("/<game_id>/<series_id>/<season_num>")
def driver_results_by_season(game_id: str, series_id: int, season_num: int):
    """Return results of a driver for a given season of a series."""
    data = []
    series_name = ""

    query = f"SELECT {GET_DRIVER_RESULTS_QUERY} WHERE game_id = '{game_id}' AND series_id = {series_id} AND season_num = {season_num}"

    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()

        cursor.execute(query)
        data = cursor.fetchall()

        series_name = get_series_name_from_id(series_id, cursor)

    return render_template('driver_season.html', records=data, series=series_name, season=season_num, driver=game_id, headers=RACE_RECORD_HEADER)

def get_series_name_from_id(series_id: int, cursor: sqlite3.Cursor):
    return cursor.execute(f"SELECT name FROM series WHERE id = {series_id}").fetchone()[0]