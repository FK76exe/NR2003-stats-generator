from flask import Blueprint, render_template, request
import sqlite3

driver_page = Blueprint("driver_page", __name__, url_prefix='/driver')
DATABASE_NAME = "../../db/nr-stats-gen.db"

@driver_page.route("/<game_id>/")
def driver_overview(game_id):
    data = []

    query = f"SELECT year AS YEAR, series as SERIES, RACES, WIN, [TOP 5], [TOP 10], POLE, LAPS, LED, [AV. S], [AV. F], DNF, LLF, POINTS, RANK \
FROM (SELECT *,RANK() OVER(PARTITION BY series, year ORDER BY points DESC) as RANK from points_view) \
where game_id = '{game_id}' \
ORDER BY YEAR ASC"
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        cursor.execute(query)
        header = [col[0] for col in cursor.description]
        header.remove("SERIES")
        data = cursor.fetchall()

        # get aggregate data as well (use Nones for things that can't be aggregated)
        # || = concat
        query = f"SELECT COUNT(*) || ' years', series as SERIES, SUM(RACES), SUM(WIN), SUM([TOP 5]), SUM([TOP 10]), SUM(POLE), SUM(LAPS), SUM(LED), '---', '---', SUM(DNF), SUM(LLF), SUM(POINTS), '---' FROM points_view WHERE game_id = '{game_id}' GROUP BY series"
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

@driver_page.route("/<game_id>/<series_id>/")
def driver_results_by_series(game_id: str, series_id: int):
    """list race results of a driver for a given series across all seasons, ordered by season and then race ID"""
    pass

"""
race name (or track if null) | track | finish | start | # | interval | led | points | status
"""

@driver_page.route("/<game_id>/<series_id>/<season_num>")
def driver_results_by_season(game_id: str, series_id: int, season_num: int):
    """Return results of a driver for a given season of a series."""
    data = []
    series_name = ""

    query = f"SELECT race_name, track_name, finish_position, start_position, car_number, interval, laps, led, points, finish_status \
FROM race_records \
LEFT JOIN drivers ON driver_id = drivers.id \
RIGHT JOIN ( \
    SELECT races.id, IFNULL(name, track_name) as race_name, track_name \
    FROM races \
    LEFT JOIN tracks ON races.track_id = tracks.id \
    RIGHT JOIN (SELECT id AS season_id FROM seasons WHERE season_num = {season_num} AND series_id = {series_id}) a ON races.season_id = a.season_id \
) b ON race_records.race_id = b.id \
WHERE game_id = '{game_id}';"
    headers = ['Race', 'Track', 'Finish', 'Start', 'Car #', 'Interval', 'Laps', 'Led', 'Points', 'Status']

    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()

        cursor.execute(query)
        data = cursor.fetchall()

        series_name = cursor.execute(f"SELECT name FROM series WHERE id = {series_id}").fetchone()[0]

    return render_template('driver_season.html', records=data, series=series_name, season=season_num, driver=game_id, headers=headers)

