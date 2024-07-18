from flask import Blueprint, render_template
from markupsafe import escape
import sqlite3

track_page = Blueprint('track_page', __name__, url_prefix='/tracks')
DATABASE_NAME = "../../db/nr-stats-gen.db"

@track_page.route("/")
def get_tracks():
    """Return list of all tracks in database"""
    query = "SELECT tracks.id, track_name, length_miles, uses_plate, track_type.type FROM tracks LEFT JOIN track_type on tracks.type = track_type.id WHERE length_miles > 0 ORDER BY track_name"
    track_data = []
    track_headers = ()
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        cursor.execute(query)
        track_data = cursor.fetchall()
        track_headers = cursor.description
    return render_template("tracks.html", track_headers=track_headers, track_data=track_data)

@track_page.route("/<id>/")
def get_track_info(id):
    """Get track information by its id."""
    track_query = f"SELECT track_name, length_miles, uses_plate, track_type.type FROM tracks LEFT JOIN track_type on tracks.type = track_type.id WHERE length_miles > 0 AND tracks.id = {id}"
    winners_query = f"SELECT b.name, season_num,game_id \
FROM races \
LEFT JOIN (\
    SELECT race_id, game_id\
    FROM race_records LEFT JOIN drivers ON drivers.id = race_records.driver_id \
    WHERE finish_position = 1\
    ) a ON races.id = a.race_id \
LEFT JOIN (\
    SELECT seasons.id, series.id as seriesID, series.name, season_num\
    FROM seasons LEFT JOIN series ON seasons.series_id = series.id \
    ) b ON races.season_id = b.id \
LEFT JOIN tracks ON tracks.id = races.track_id \
WHERE tracks.id = {id} \
ORDER BY b.seriesID ASC, season_num ASC"
    
    with sqlite3.connect(DATABASE_NAME) as con:
        cursor = con.cursor()
        cursor.execute(track_query)
        track_info = cursor.fetchall()[0]

        cursor.execute(winners_query)
        winners_records = cursor.fetchall()
        grouped_records = group_by_col(winners_records)

    return render_template("track_overview.html", win_records = grouped_records, win_headers = ['Season', 'Winner'], track_info = track_info)

        
def group_by_col(records: list):
    """Create a dictionary where each key is mapped to a list of records with key in field of index 0."""
    group_dict = {}
    for record in records:
        if record[0] not in group_dict.keys():
            group_dict[record[0]] = [record[1:]]
        else:
            group_dict[record[0]].append(record[1:])
    return group_dict