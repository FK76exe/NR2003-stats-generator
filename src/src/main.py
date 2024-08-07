from flask import Flask, render_template
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