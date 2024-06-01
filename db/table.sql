-- for SQLite

CREATE TABLE series (
    id        INTEGER     PRIMARY KEY,
    initial   VARCHAR(1)  NOT NULL UNIQUE,
    `name`    VARCHAR    NOT NULL UNIQUE
);

CREATE TABLE driver (
    id          INTEGER        PRIMARY KEY,
    report_name VARCHAR        NOT NULL UNIQUE,
    full_name   VARCHAR        NOT NULL
);

CREATE TABLE race (
    id          INTEGER        PRIMARY KEY,
    series      INTEGER        NOT NULL,
    season      INTEGER        NOT NULL,
    `name`      VARCHAR        NOT NULL,
    track       INTEGER        NOT NULL,
    FOREIGN KEY(series) REFERENCES series(id),
    FOREIGN KEY(track) REFERENCES track(id)
);

CREATE TABLE track_types (
    `name`      VARCHAR        PRIMARY KEY
);

CREATE TABLE track (
    id              INTEGER     PRIMARY KEY,
    `name`          VARCHAR     NOT NULL,
    `type`          VARCHAR     NOT NULL,
    length_miles    FLOAT       NOT NULL,
    FOREIGN KEY(`type`) REFERENCES track_types(`name`)
);

CREATE TABLE race_record (
    id          INTEGER     PRIMARY KEY,
    race        INTEGER     NOT NULL,
    finish      INTEGER     NOT NULL,
    `start`     INTEGER     NOT NULL,
    car_no      INTEGER     NOT NULL, --change 0x to 200x
    driver      INTEGER     NOT NULL,
    interval    FLOAT       NOT NULL,
    laps        INTEGER     NOT NULL,
    led         INTEGER     NOT NULL,
    points      INTEGER     NOT NULL,
    `status`    VARCHAR     NOT NULL,
    FOREIGN KEY (race) REFERENCES race(id),
    FOREIGN KEY (driver) REFERENCES driver(id)
);