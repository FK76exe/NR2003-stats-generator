# TODO function for retrieving database
# TODO function for filling up database

# run without func -> only get config info once

import sqlite3
import configparser
import os

config = configparser.ConfigParser()
config.read('config.ini')
db_path = config.get('General', 'DBPath')

# connect database and create tables if necessary 
con = sqlite3.connect(db_path)
cursor = con.cursor()

# read SQL script into string and execute it
query = open(r'../../db/create-tables.sql').read()
query += open(r'../../db/create-views.sql').read()
cursor.executescript(query)
