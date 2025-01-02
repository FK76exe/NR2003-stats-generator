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

# Check if a table exists
# If tables are present (schema is made, don't run the script)
# else: it's a new db, so add tables and sample data
# problem with 'INSERT OR IGNORE INTO' -> doesn't work for sample data
schemas_count = int(cursor.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0])

if schemas_count == 0:
    query = open(path.abspath(path.join(BASE_PATH, 'db/version_1_1_script_full.sql'))).read()
    query += open(path.abspath(path.join(BASE_PATH, 'db/sample_data_1_1.sql'))).read()
    cursor.executescript(query)
    con.commit()

cursor.close()
con.close()