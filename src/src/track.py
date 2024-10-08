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

@track_page.route("/<id>/")
def get_track_info(id):
    """Get track information by its id."""
    track_query = f"SELECT track_name, length_miles, uses_plate, track_type.type FROM tracks LEFT JOIN track_type on tracks.type = track_type.id WHERE length_miles > 0 AND tracks.id = {id}"
    record_query = f"SELECT series_id, series, season_num, name, laps, miles, pole_sitter, winner, speed FROM track_race_overview WHERE id = {id}"
    
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        cursor.execute(track_query)
        track_info = cursor.fetchall()[0]

        cursor.execute(record_query)
        data = cursor.fetchall()

    records_by_series = {}
    for season_record in data:
        if tuple(season_record[:2]) not in records_by_series.keys():
            records_by_series[tuple(season_record[:2])] = [season_record[2:]]
        else:
            records_by_series[tuple(season_record[:2])].append(season_record[2:])

    return render_template("track_overview.html", records = records_by_series, headers = ['Season', 'Race', 'Laps', 'Miles', 'Pole Sitter', 'Winner', 'Speed (mph)'], track_info = track_info)
        
def group_by_col(records: list):
    """Create a dictionary where each key is mapped to a list of records with key in field of index 0."""
    group_dict = {}
    for record in records:
        if record[0] not in group_dict.keys():
            group_dict[record[0]] = [record[1:]]
        else:
            group_dict[record[0]].append(record[1:])
    return group_dict