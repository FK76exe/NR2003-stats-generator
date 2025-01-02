from flask import Blueprint, render_template, redirect, url_for, request, abort
from db import DB_PATH
import sqlite3

team_page = Blueprint("team_page", __name__, url_prefix='/team')

@team_page.route("/", methods=['GET', 'POST'])
def view_teams():
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        if request.method == 'GET':
            teams = cursor.execute("SELECT * FROM teams")
            return render_template("./teams/teams_main.html", teams=teams)
        else:
            try:
                cursor.execute(f"""INSERT INTO teams (name) VALUES ("{request.form['name']}")""")
            except sqlite3.OperationalError:
                return abort(400, f"Please make sure the team name is unique and is not in use by any existing team.")
            return redirect(url_for('team_page.view_teams'))
        
@team_page.route("/<id>", methods=['GET', 'POST', 'DELETE'])
def single_team(id):    
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        if request.method == 'GET':
            # retrieve team data
            team_name = cursor.execute(f"SELECT name FROM teams WHERE id = {id}").fetchone()[0]
            if team_name:
                records = get_team_overview(id)
                return render_template("./teams/teams_single.html", team_name = team_name, records=records, id=id)
            else:
                return abort(404, "Team with this id does not exist.")
        elif request.method == 'POST':
            # update team name
            cursor.execute(f"UPDATE teams SET name='{request.form['name']}' WHERE id = {id}")
            return redirect(url_for('team_page.single_team', id=id))
        else:
            # delete team
            cursor.execute(f"DELETE FROM teams WHERE id = {id}")
            return redirect(url_for('team_page.view_teams'), 303) # HTTP 303 (See Other): redirect to new URL with GET

@team_page.route("/<id>/<series_id>")
@team_page.route("/<id>/<series_id>/<season>") # .. why didn't I learn this sooner... thanks again SO!
@team_page.route("/<id>/<series_id>/<season>/<number>")
def get_team_results_by_series(id, series_id, season=None, number=None):

    query = f"""
    SELECT Year, Race, Race_ID, Track, Number, Driver_Name AS Driver, Finish, 
            Start, Number, Interval, Laps, Led, Points, Status 
    FROM race_records_view
    WHERE Series_ID = {series_id} AND Team_ID = {id}  
    """
    if season != None: # add year query and remove Year from selection
        query.replace("Year, ","")
        query += f" AND Year={season} "
    if number != None:
        query.replace("Number, ", "")
        query += f"AND Number={number}"

    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cursor = con.cursor()

        records = cursor.execute(query).fetchall()
        headers = cursor.description

        if len(records) == 0:
            return abort(404, "No records found!")
        
        try:
            team_name = cursor.execute(f"SELECT name FROM teams WHERE id={id}").fetchone()[0]
        except TypeError: # no results
            return abort(404, "Team not found.")
        try:
            series_name = cursor.execute(f"SELECT name FROM series WHERE id={series_id}").fetchone()[0]
        except TypeError:
            return abort(404, "Series not found.")
        return render_template("./teams/team_results.html", team_name=team_name,
                                records=records, headers = headers, series=series_name, 
                                id=id, season=season, number=number)

def get_team_overview(id: int):
    record_query = f"""
    SELECT Series_ID, Year, Number, RACE, WIN, [TOP 5], [TOP 10], POLE,
    LAPS, LED, [Av. S], [Av. F], DNF, LLF, POINTS, RANK 
    FROM (
        SELECT *, 
        RANK() OVER(PARTITION BY Series_ID, Year ORDER BY POINTS DESC) 
        as RANK FROM entrant_points_view
    ) a 
    LEFT JOIN series ON series.id = a.Series_ID WHERE Team_ID ={id} 
    ORDER BY YEAR ASC 
    """
    # series id and name will be keys (we need both anyway)
    series_query = f"""
    SELECT DISTINCT Series_ID, series.name as Name FROM entrant_points_view
    LEFT JOIN series ON series.id = Series_ID
    WHERE Team_ID={id}
    """

    # aggregate query
    aggregate_query = f"""
    SELECT Series_ID, SUM(RACE) as RACE, SUM(WIN) as WIN, 
    SUM([TOP 5]) as [TOP 5], SUM([TOP 10]) as [TOP 10], SUM(POLE) as POLE, 
    SUM(LAPS) as LAPS, SUM(LED) as LED, SUM(DNF) as DNF, SUM(LLF) as LLF, 
    SUM(POINTS) as POINTS FROM entrant_points_view
    WHERE Team_ID = {id} GROUP BY Series_ID
    """

    ind_dict = group_query_results_by_key(record_query, 'Series_ID')
    series_dict = group_query_results_by_key(series_query, 'Series_ID')
    aggergate_dict = group_query_results_by_key(aggregate_query, 'Series_ID')
    return {'ind': ind_dict, 'series': series_dict, 'agg': aggergate_dict, 
            'header': ['Year','Number', 'RACE', 'WIN', 'TOP 5', 'TOP 10', 'POLE', 'LAPS', 'LED',
                       'Av. S', 'Av. F', 'DNF', 'LLF', 'POINTS', 'RANK']}

def group_query_results_by_key(query: str, field: str) -> dict:
    """Create a dictionary where a key leads to a list of dicts containing the same key-value pair"""

    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row # so much better...
        cursor = con.cursor()
        data = cursor.execute(query)

    grouped_dict = {}
    for record in data:
        if record[field] not in grouped_dict.keys():
            grouped_dict[record[field]] = [record]
        else:
            grouped_dict[record[field]].append(record)
    return grouped_dict