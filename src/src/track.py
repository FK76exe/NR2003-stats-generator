from flask import Blueprint, render_template, request, redirect, url_for, abort
import sqlite3
from db import DB_PATH

track_page = Blueprint('track_page', __name__, url_prefix='/tracks')

@track_page.route("/", methods=['GET', 'POST'])
def track_main():
    """Handle requests to tracks/ endpoint"""
    message = None
    if request.method == "POST":
        message = add_track(request.form)
    return get_tracks(message)

def get_tracks(message):
    query = "SELECT tracks.id as ID, track_name as Name, length_miles as [Length (miles)], uses_plate as [Plate?], track_type.type AS Type FROM tracks LEFT JOIN track_type on tracks.type = track_type.id WHERE length_miles > 0 ORDER BY track_name"
    track_data = []
    track_headers = ()
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        cursor.execute(query)
        track_data = cursor.fetchall()
        track_headers = cursor.description
    return render_template("tracks.html", track_headers=track_headers, track_data=track_data, message=message)

def add_track(form):
    query = f"INSERT INTO tracks (track_name, length_miles, uses_plate, type) VALUES('{form['track_name']}', {form['track_length']}, {1 if 'uses_plate' in form.keys() else 0}, {form['track_type']})"

    with sqlite3.connect(DB_PATH) as con:
        try:
            cursor = con.cursor()
            cursor.execute(query)
        except sqlite3.Error as e:
            return f"ERROR: {str(e)}"
    return f"{form['track_name']} has been successfully added"

@track_page.route("/<id>/delete/", methods=['DELETE'])
def delete_track(id):
    # each query string can only have one statement
    pragma_query = "PRAGMA foreign_keys = ON"
    delete_query = f"DELETE FROM tracks WHERE id = {id};"
    with sqlite3.connect(DB_PATH) as con:
        try:
            cursor = con.cursor()
            cursor.execute(pragma_query)
            cursor.execute(delete_query)
        except sqlite3.Error as e:
            print(f"ERROR: {str(e)}")
    # this creates a redirect response object, which must be handled by caller
    return redirect(url_for('track_page.track_main'), code=302)

@track_page.route("/<id>/", methods=['GET', 'POST'])
def get_track_info(id):
    """Get track information by its id."""
    if request.method == 'POST':
        return update_track_info(id, request.form)

    track_query = f"SELECT track_name, length_miles, uses_plate, track_type.type FROM tracks LEFT JOIN track_type on tracks.type = track_type.id WHERE length_miles > 0 AND tracks.id = {id}"
    record_query = f"""
        SELECT
    Series_ID, series.name as Series_Name, Year, race_records_view.Race_ID,
    Race, iif(Finish=1,race_records_view.Driver_Name, NULL) AS [Winner],
    Interval AS [Race Speed], Laps, ROUND(Laps*c.length_miles, 1) AS Distance,
    -- THIS combines all strings in a column for a given group... very cool!
    GROUP_CONCAT(iif(Start=1,race_records_view.Driver_Name, NULL),',') AS [Pole Sitter],
    b.time AS [Pole Time]
    FROM race_records_view
    LEFT JOIN series ON Series_ID = series.id
    LEFT JOIN (SELECT race_id, time FROM timed_sessions WHERE type=2 AND position=1) b ON b.race_id = race_records_view.Race_ID
    LEFT JOIN (SELECT id, length_miles FROM tracks) c ON c.id = Track_ID
    WHERE Track_ID={id}
    GROUP BY race_records_view.Race_ID
    ORDER BY Series_ID ASC
    """
    
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cursor = con.cursor()
        cursor.execute(track_query)
        track_info = cursor.fetchall()[0]

        cursor.execute(record_query)
        data = cursor.fetchall()
        headers = [i[0] for i in cursor.description[2:]]
        headers.remove('Race_ID') # we aren't presenting this as a separate column for the user...

        records_by_series = {}
        for season_record in data:
            record_dict = dict(season_record)
            series_id, series_name = record_dict.pop('Series_ID'), record_dict.pop('Series_Name')
            key = tuple([series_id, series_name])
            if key not in records_by_series.keys():
                records_by_series[key] = [record_dict]
            else:
                records_by_series[key].append(record_dict)

        return render_template("track_overview.html", records = records_by_series, 
                               headers = headers, track_info = track_info)
            
@track_page.route("/<id>/<series_id>/")
def get_track_stats_by_series(id: int, series_id: int):
    query = f"""
        SELECT Driver_Name AS Driver, Starts, Wins, [Top 5], [Top 10], 
        Poles, Laps, Led, Miles, [Miles Led], [Av. S], [Av. F],  
        DNF, LLF, Points
        FROM track_aggregate_stats
        WHERE Series_ID={series_id} AND Track_ID={id}
        ORDER BY driver ASC
        """
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        data = cursor.execute(query).fetchall()
        headers = [h[0] for h in cursor.description]

        track_name_query = f"SELECT track_name FROM tracks WHERE id={id}"
        track_name = cursor.execute(track_name_query).fetchone()[0]

        return render_template("track_agg_stats.html", data=data, headers=headers, id=id, name=track_name, series_id=series_id)

def update_track_info(id: int, form: dict):
    query = f"UPDATE tracks SET track_name='{form['track_name']}', length_miles={form['track_length']}, uses_plate={1 if 'uses_plate' in form.keys() else 0}, type={form['track_type']} WHERE id={id}"

    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        cursor.execute(query)
    
    return redirect(url_for('track_page.get_track_info', id=id), 302)

def group_by_col(records: list):
    """Create a dictionary where each key is mapped to a list of records with key in field of index 0."""
    group_dict = {}
    for record in records:
        if record[0] not in group_dict.keys():
            group_dict[record[0]] = [record[1:]]
        else:
            group_dict[record[0]].append(record[1:])
    return group_dict