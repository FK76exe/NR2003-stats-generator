from flask import Flask, render_template
import file_scraper as file_scraper
import sqlite3
from series import series_page
from track import track_page
from driver import driver_page
from race import race_page

app = Flask(__name__)
app.register_blueprint(series_page)
app.register_blueprint(track_page)
app.register_blueprint(driver_page)
app.register_blueprint(race_page)

@app.route("/")
def home():
    return render_template('home.html')