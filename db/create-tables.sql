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


SELECT seasons.season_num AS year, series.name AS series, game_id, IFNULL(races,0) as RACES, IFNULL(wins,0) as WIN, IFNULL(top5, 0) AS "TOP 5", IFNULL(top10, 0) AS "TOP 10", 
IFNULL(poles,0) AS POLE, IFNULL(laps,0) AS LAPS, IFNULL(led,0) AS LED, ROUND(avs,1) AS "AV. S", ROUND(avf,1) AS "AV. F", IFNULL(dnf,0) AS "DNF", 
points as POINTS
FROM drivers, seasons

JOIN series ON series.id = seasons.series_id

JOIN (
SELECT season_id, race_id, driver_id, COUNT(*) as races 
FROM race_records 
LEFT JOIN races ON race_id = races.id GROUP BY year, season_id, driver_id
) a ON drivers.id = a.driver_id AND seasons.id = a.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, COUNT(*) as wins FROM race_records LEFT JOIN races ON race_id = races.id WHERE finish_position = 1 GROUP BY year, series, driver_id
) b ON drivers.id = b.driver_id AND seasons.id = b.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, COUNT(*) as top5 FROM race_records LEFT JOIN races ON race_id = races.id  WHERE finish_position < 6 GROUP BY year, series, driver_id
) c ON drivers.id = c.driver_id AND seasons.id = c.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, COUNT(*) as top10 FROM race_records LEFT JOIN races ON race_id = races.id  WHERE finish_position < 11 GROUP BY year, series, driver_id
) d ON drivers.id = d.driver_id AND seasons.id = d.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, COUNT(*) as poles FROM race_records LEFT JOIN races ON race_id = races.id  WHERE start_position = 1 GROUP BY year, series, driver_id
) h ON drivers.id = h.driver_id AND seasons.id = h.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, SUM(laps) as laps FROM race_records LEFT JOIN races ON race_id = races.id  GROUP BY year, series, driver_id
) e ON drivers.id = e.driver_id AND seasons.id = e.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, SUM(led) as led FROM race_records LEFT JOIN races ON race_id = races.id  GROUP BY year, series, driver_id
) f ON drivers.id = f.driver_id AND seasons.id = f.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, AVG(start_position) as avs FROM race_records  LEFT JOIN races ON race_id = races.id GROUP BY year, series, driver_id
) g ON drivers.id = g.driver_id AND seasons.id = g.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, AVG(finish_position) as avf FROM race_records LEFT JOIN races ON race_id = races.id  GROUP BY year, series, driver_id
) i ON drivers.id = i.driver_id AND seasons.id = i.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, COUNT(*) as dnf FROM race_records LEFT JOIN races ON race_id = races.id  WHERE finish_status IS NOT 'Running' GROUP BY year, series, driver_id 
) j ON drivers.id = j.driver_id AND seasons.id = j.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, SUM(points) as points FROM race_records LEFT JOIN races ON race_id = races.id  GROUP BY year, series, driver_id 
) k ON drivers.id = k.driver_id AND seasons.id = k.season_id

LEFT JOIN (
SELECT season_id, driver_id, COUNT(*) as llf
FROM race_records
LEFT JOIN (
    SELECT races.id, races.season_id, max(laps) as total_laps
    FROM race_records
    LEFT JOIN races ON race_id = races.id
    GROUP BY races.id
) a WHERE race_id = a.id AND laps = a.total_laps
GROUP BY driver_id, season_id
) l ON drivers.id = l.driver_id AND seasons.id = l.season_id

ORDER BY points DESC