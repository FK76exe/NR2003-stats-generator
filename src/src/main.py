from flask import Flask, render_template
import file_scraper as file_scraper
from series import series_page
from track import track_page
from driver import driver_page
from race import race_page
from points import points_page
from team import team_page
import webbrowser

app = Flask(__name__)
app.register_blueprint(series_page)
app.register_blueprint(track_page)
app.register_blueprint(driver_page)
app.register_blueprint(race_page)
app.register_blueprint(points_page)
app.register_blueprint(team_page)

@app.route("/")
def home():
    return render_template('home.html')

if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000", 2)
    app.run()