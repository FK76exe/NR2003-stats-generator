# TODO function for retrieving database
# TODO function for filling up database

# run without func -> only get config info once

import sqlite3
import configparser
from enum import Enum

config = configparser.ConfigParser()
config.read('config.ini')
DB_PATH = config.get('General', 'DBPath')

# connect database and create tables if necessary 
con = sqlite3.connect(DB_PATH)
cursor = con.cursor()

# read SQL script into string and execute it
query = open(r'../../db/create-tables.sql').read()
query += open(r'../../db/create-views.sql').read()
cursor.executescript(query)
con.commit()
cursor.close()
con.close()