-- REMEMBER TO UPDATE AS DEVELOPMENT PROGRESSES!

-- drivers
CREATE TABLE drivers (
    id      INTEGER PRIMARY KEY,
    game_id VARCHAR UNIQUE
                    NOT NULL
);

-- penalties
CREATE TABLE penalties (
    id         INTEGER PRIMARY KEY,
    race_id    INTEGER REFERENCES races (id) ON DELETE CASCADE,
    lap        INTEGER,
    number     INTEGER,
    infraction VARCHAR,
    penalty    VARCHAR
);

-- race records
CREATE TABLE race_records (
    race_id         INTEGER REFERENCES races (id) ON DELETE CASCADE,
    finish_position INTEGER,
    start_position  INTEGER,
    car_number      INTEGER,
    driver_id       INTEGER,
    interval        VARCHAR,
    laps            INTEGER,
    led             INTEGER,
    points          INTEGER,
    finish_status   VARCHAR
);

-- races
CREATE TABLE races (
    id        INTEGER PRIMARY KEY
                      UNIQUE
                      NOT NULL,
    race_file INTEGER NOT NULL
                      UNIQUE,
    track_id          REFERENCES tracks (id) ON DELETE CASCADE
                      NOT NULL,
    name,
    season_id         REFERENCES seasons (id) ON DELETE CASCADE
                      NOT NULL
);

-- seasons
CREATE TABLE seasons (
    id         INTEGER PRIMARY KEY,
    series_id  INTEGER REFERENCES series (id) ON DELETE CASCADE,
    season_num INTEGER NOT NULL,
    UNIQUE (
        series_id,
        season_num
    )
);


-- series
CREATE TABLE series (
    id   INTEGER PRIMARY KEY,
    name VARCHAR NOT NULL
                 UNIQUE
);

-- track type
CREATE TABLE track_type (
    id   INTEGER PRIMARY KEY,
    type STRING  UNIQUE
);

INSERT INTO track_type (type) VALUES ('STREET COURSE'), ('ROAD COURSE'), ('DIRT OVAL'), ('PAVED OVAL');

-- tracks
CREATE TABLE tracks (
    id           INTEGER PRIMARY KEY
                         NOT NULL,
    track_name   VARCHAR NOT NULL,
    length_miles FLOAT,
    uses_plate   INT,
    type         INT     REFERENCES track_type (id) 
);

-- timed session type (fixed)
CREATE TABLE timed_session_type (
    id      INTEGER PRIMARY KEY,
    session         UNIQUE
);

INSERT INTO timed_session_type (sessions) VALUES ('Practice'), ('Qualifying'), ('Happy Hour');

-- timed sessions
CREATE TABLE timed_sessions (
    id        INTEGER PRIMARY KEY,
    race_id   INTEGER REFERENCES races (id) ON DELETE CASCADE,
    type      INTEGER REFERENCES timed_session_type (id),
    position  INTEGER,
    number    INTEGER,
    driver_id INTEGER REFERENCES drivers (id) ON DELETE CASCADE,
    time      INTEGER
);
