from flask import Blueprint, render_template
from markupsafe import escape
import sqlite3

track_page = Blueprint('track_page', __name__, url_prefix='/tracks')
DATABASE_NAME = "../../db/nr-stats-gen.db"

@track_page.route("/")
def get_track_info():
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
