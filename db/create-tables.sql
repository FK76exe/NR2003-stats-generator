CREATE TABLE drivers (id INTEGER PRIMARY KEY, game_id VARCHAR UNIQUE NOT NULL, full_name VARCHAR);
CREATE TABLE track_aliases (track_alias VARCHAR PRIMARY KEY, track_id INTEGER);
CREATE TABLE tracks (id INTEGER PRIMARY KEY NOT NULL, track_name VARCHAR NOT NULL);
CREATE TABLE race_records (race_id INTEGER REFERENCES races (id), finish_position INTEGER, start_position INTEGER, car_number INTEGER, driver_id INTEGER, interval VARCHAR, laps INTEGER, led INTEGER, points INTEGER, finish_status VARCHAR);
CREATE TABLE series (id INTEGER PRIMARY KEY, name VARCHAR NOT NULL UNIQUE);

CREATE TABLE races (
    id        INTEGER PRIMARY KEY
                      UNIQUE
                      NOT NULL,
    race_file INTEGER NOT NULL
                      UNIQUE,
    track_id          REFERENCES tracks (id) 
                      NOT NULL,
    seqnum,
    name,
    season_id         REFERENCES seasons (id) ON DELETE CASCADE
                      NOT NULL
);


CREATE TABLE seasons (
    id         INTEGER PRIMARY KEY,
    series_id  INTEGER REFERENCES series (id),
    season_num INTEGER NOT NULL,
    UNIQUE (
        series_id,
        season_num
    )
);