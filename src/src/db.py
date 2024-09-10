# run without func -> only get config info once

import sqlite3
import configparser
from os import path

BASE_PATH = path.dirname(__file__)

ini_path = path.abspath(path.join(BASE_PATH, '../config.ini'))

config = configparser.ConfigParser()
config.read(ini_path)
DB_PATH = config.get('General', 'DBPath')

# connect database and create tables if necessary 
con = sqlite3.connect(DB_PATH)
cursor = con.cursor()

# read SQL script into string and execute it
query = open(path.abspath(path.join(BASE_PATH, 'db/create-tables.sql'))).read()
query += open(path.abspath(path.join(BASE_PATH, 'db/create-views.sql'))).read()

cursor.executescript(query)
con.commit()
cursor.close()
con.close()