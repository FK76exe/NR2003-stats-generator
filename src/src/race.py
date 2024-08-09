from flask import Blueprint, render_template, redirect, abort
import sqlite3

race_page = Blueprint("race_page", __name__, url_prefix="/race")
DATABASE_NAME = "../../db/nr-stats-gen.db"

@race_page.route("/")
def race_main():
    return "<h1>Hi</h1>"

@race_page.route("/<race_id>/")
def get_race_records(race_id):
    """Get race records by race id."""
    race_records = []

    race_info = {'name': None, 'track_name': None, 'track_length': None, 'track_type': None, 'track_plate': None, 'series_id': None, 'series_name': None, 'season': None}

    # gonna need race records and race info (name, track, series, season)
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        i = cursor.execute(f"""SELECT finish_position AS finish, start_position AS start, CASE WHEN car_number > 1999 THEN '0' || (car_number-2000) ELSE car_number END AS number, game_id AS driver, interval, laps, led, points, finish_status AS status
                                FROM race_records
                                LEFT JOIN drivers ON drivers.id = race_records.driver_id
                                WHERE race_id = {race_id}"""
                        ).fetchall()
        keys = [j[0] for j in cursor.description]
        for record in i:
            race_record = {}
            for k, key in enumerate(keys):
                race_record.update({key: record[k]})
            race_records.append(race_record)
        
        # for race name and track info. Apparently short queries are better than big ones? https://dba.stackexchange.com/questions/76973/what-is-faster-one-big-query-or-many-small-queries
        track_info = cursor.execute(f"""
                                SELECT name, track_name, length_miles, CASE uses_plate WHEN 1 THEN 'Yes' ELSE 'No' END as 'plate?', type
                                FROM races
                                LEFT JOIN tracks ON tracks.id = races.track_id
                                WHERE races.id = {race_id}
                    """).fetchone()
        race_info.update({'name': track_info[0], 'track_name': track_info[1], 'track_length': track_info[2], 'track_plate': track_info[3], 'track_type': track_info[4]})

        # for series/season info
        season_info = cursor.execute(f"""SELECT series_id, season_num
                        FROM races
                        LEFT JOIN seasons ON seasons.id = races.season_id
                        WHERE races.id = {race_id}"""
                        ).fetchone()
        series = cursor.execute(f"SELECT name FROM series WHERE id = {season_info[0]}").fetchone()[0]
        race_info.update({'series_id': season_info[0], 'series_name': series, 'season': season_info[1]})

        return render_template("race.html", info=race_info, records=race_records, id=race_id)

@race_page.route("/<race_id>/<filter>/")
def get_nonrace_records(race_id, filter):
    """Get non-race session records (practice, quali, happy hour, penalties)"""
    match filter:
        case "qualifying":
            query = f"SELECT position as Position, number as Number, game_id as Driver, time as Time \
                    FROM timed_sessions LEFT JOIN drivers ON drivers.id = timed_sessions.driver_id \
                    WHERE type = 1 AND race_id = {race_id} \
                    ORDER BY position ASC"
        case "practice":
            query = f"SELECT position as Position, number as Number, game_id as Driver, time as Time \
                    FROM timed_sessions LEFT JOIN drivers ON drivers.id = timed_sessions.driver_id \
                    WHERE type = 2 AND race_id = {race_id} \
                    ORDER BY position ASC"
        case "happy_hour":
            query = f"SELECT position as Position, number as Number, game_id as Driver, time as Time \
                    FROM timed_sessions LEFT JOIN drivers ON drivers.id = timed_sessions.driver_id \
                    WHERE type = 3 AND race_id = {race_id} \
                    ORDER BY position ASC"
        case "penalties":
            query = f"SELECT lap as Lap, number as Number, infraction as Infraction, penalty as Penalty \
                    FROM penalties \
                    WHERE race_id = {race_id} \
                    ORDER BY lap ASC"
        case _:
            return abort(404, "Not a valid session.")

    headers = []
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        data = cursor.execute(query).fetchall()
        headers = [j[0] for j in cursor.description]
    
    if len(data) == 0:
        return abort(404, "No records exist.")
    
    records = []
    for record in data:
        record_dict = {}
        for h, header in enumerate(headers):
            record_dict.update({header: record[h]})
        records.append(record_dict)

    return render_template("nonrace_record.html", records=records, session=filter, id=race_id, headers=headers)

@race_page.route("/<race_id>/delete", methods = ['DELETE'])
def delete_race(race_id):
    """Delete race."""
    pragma_query = "PRAGMA foreign_keys = ON;"
    delete_query = f"DELETE FROM races WHERE id = {race_id}"
    season_series_query = f"SELECT series_id, season_num FROM races LEFT JOIN seasons ON seasons.id = races.season_id WHERE races.id={race_id}"

    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        series, season = cursor.execute(season_series_query).fetchone()
        cursor.execute(pragma_query)
        cursor.execute(delete_query)
        con.commit() # add this, so that everyone can see deletion
    return redirect(f"/series/{series}/{season}/", code=302)