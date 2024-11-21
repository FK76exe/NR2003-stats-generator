-- points system schema
CREATE TABLE IF NOT EXISTS point_systems  (
    id      INTEGER PRIMARY KEY,
    name    VARCHAR UNIQUE
);

-- points scoring criteria schema
CREATE TABLE  IF NOT EXISTS point_system_scores (
    system_id  INTEGER REFERENCES point_systems(id) ON DELETE CASCADE,
    position   INTEGER,
    points     INTEGER DEFAULT 0,
    PRIMARY KEY (system_id, position)
);

-- bonus point enums
CREATE TABLE IF NOT EXISTS bonus_point_enums (
    id INTEGER PRIMARY KEY,
    condition VARCHAR UNIQUE
);

INSERT OR IGNORE INTO bonus_point_enums (condition) VALUES ('Pole'), ('Lap Led'), ('Most Laps Led');

CREATE TABLE IF NOT EXISTS bonus_points (
    system_id       INTEGER REFERENCES points_systems(id) ON DELETE CASCADE,
    bonus_condition INTEGER REFERENCES bonus_point_enums(id),
    points          INTEGER DEFAULT 0,
    PRIMARY KEY (system_id, bonus_condition)
);

-- for points_view to use
CREATE VIEW points_per_race AS
    SELECT seasons.id AS season_id,
           races.id AS race_id,
           driver_id,
           finish_position,
           IFNULL(point_system_scores.points, raw_points) AS finish_points, -- get raw points for seasons that do not have a point system set
           CASE WHEN won_pole = 1 THEN IFNULL(pole.points, 0) ELSE 0 END AS pole_points,
           CASE WHEN lap_led = 1 THEN IFNULL(led.points, 0) ELSE 0 END AS lap_led_points,
           CASE WHEN most_led = 1 THEN IFNULL(most_led.points, 0) ELSE 0 END AS most_led_points
      FROM races
           LEFT JOIN
           (
               SELECT race_records.race_id,
                      race_records.driver_id,
                      race_records.points AS raw_points,
                      race_records.finish_position,
                      CASE WHEN start_position = 1 THEN 1 ELSE 0 END AS won_pole,
                      CASE WHEN led > 0 THEN 1 ELSE 0 END AS lap_led,
                      CASE WHEN mll.most_led IS NOT NULL THEN 1 ELSE 0 END AS most_led
                 FROM race_records
                      LEFT JOIN
                      (
                          SELECT race_id,
                                 driver_id,
                                 MAX(led) AS most_led
                            FROM race_records
                           GROUP BY race_id
                      )
                      mll ON mll.race_id = race_records.race_id AND 
                             mll.driver_id = race_records.driver_id
           )
           a ON a.race_id = races.id
           LEFT JOIN
           seasons ON races.season_id = seasons.id
           LEFT JOIN
           point_system_scores ON seasons.points_system_id = point_system_scores.system_id AND 
                                  point_system_scores.position = finish_position
           LEFT JOIN
           (
               SELECT *
                 FROM bonus_points
                WHERE bonus_condition = 1
           )
           pole ON pole.system_id = seasons.points_system_id
           LEFT JOIN
           (
               SELECT *
                 FROM bonus_points
                WHERE bonus_condition = 2
           )
           led ON led.system_id = seasons.points_system_id
           LEFT JOIN
           (
               SELECT *
                 FROM bonus_points
                WHERE bonus_condition = 3
           )
           most_led ON most_led.system_id = seasons.points_system_id;

ALTER TABLE seasons ADD COLUMN points_system id INTEGER REFERENCES points_systems(id); -- no assigned points system leads to null

-- safe to drop a view since its just an aggregator
DROP VIEW points_view;

SELECT seasons.season_num AS year, series.name AS series, game_id, IFNULL(races,0) as RACES, IFNULL(wins,0) as WIN, IFNULL(top5, 0) AS "TOP 5", IFNULL(top10, 0) AS "TOP 10", 
IFNULL(poles,0) AS POLE, IFNULL(laps,0) AS LAPS, IFNULL(led,0) AS LED, ROUND(avs,1) AS "AV. S", ROUND(avf,1) AS "AV. F", IFNULL(dnf,0) AS "DNF", IFNULL(llf, 0) AS "LLF",
m.points as POINTS
FROM drivers, seasons

JOIN series ON series.id = seasons.series_id

JOIN (
SELECT season_id, race_id, driver_id, COUNT(*) as races 
FROM race_records 
LEFT JOIN races ON race_id = races.id GROUP BY season_id, driver_id
) a ON drivers.id = a.driver_id AND seasons.id = a.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, COUNT(*) as wins FROM race_records LEFT JOIN races ON race_id = races.id WHERE finish_position = 1 GROUP BY season_id, driver_id
) b ON drivers.id = b.driver_id AND seasons.id = b.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, COUNT(*) as top5 FROM race_records LEFT JOIN races ON race_id = races.id  WHERE finish_position < 6 GROUP BY season_id, driver_id
) c ON drivers.id = c.driver_id AND seasons.id = c.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, COUNT(*) as top10 FROM race_records LEFT JOIN races ON race_id = races.id  WHERE finish_position < 11 GROUP BY season_id, driver_id
) d ON drivers.id = d.driver_id AND seasons.id = d.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, COUNT(*) as poles FROM race_records LEFT JOIN races ON race_id = races.id  WHERE start_position = 1 GROUP BY season_id, driver_id
) h ON drivers.id = h.driver_id AND seasons.id = h.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, SUM(laps) as laps FROM race_records LEFT JOIN races ON race_id = races.id  GROUP BY season_id, driver_id
) e ON drivers.id = e.driver_id AND seasons.id = e.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, SUM(led) as led FROM race_records LEFT JOIN races ON race_id = races.id  GROUP BY season_id, driver_id
) f ON drivers.id = f.driver_id AND seasons.id = f.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, AVG(start_position) as avs FROM race_records  LEFT JOIN races ON race_id = races.id GROUP BY season_id, driver_id
) g ON drivers.id = g.driver_id AND seasons.id = g.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, AVG(finish_position) as avf FROM race_records LEFT JOIN races ON race_id = races.id  GROUP BY season_id, driver_id
) i ON drivers.id = i.driver_id AND seasons.id = i.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, COUNT(*) as dnf FROM race_records LEFT JOIN races ON race_id = races.id  WHERE finish_status IS NOT 'Running' GROUP BY season_id, driver_id 
) j ON drivers.id = j.driver_id AND seasons.id = j.season_id

LEFT JOIN (
SELECT season_id, race_id, driver_id, SUM(points) as points FROM race_records LEFT JOIN races ON race_id = races.id  GROUP BY season_id, driver_id 
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

-- points
LEFT JOIN (
SELECT season_id, driver_id, SUM(finish_points + pole_points + lap_led_points + most_led_points) as points
FROM points_per_race
GROUP BY season_id, driver_id
) m ON drivers.id = m.driver_id AND seasons.id = m.season_id

ORDER BY points DESC

-- TODO add versions schema: https://stackoverflow.com/questions/3604310/alter-table-add-column-if-not-exists-in-sqlite