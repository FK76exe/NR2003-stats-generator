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
CREATE VIEW IF NOT EXISTS points_per_race AS
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

-- ALTER TABLE seasons ADD COLUMN points_system_id INTEGER REFERENCES points_systems(id); -- no assigned points system leads to null

CREATE TABLE IF NOT EXISTS manual_points (
    driver_id         INTEGER REFERENCES drivers (id) ON DELETE CASCADE,
    season_id         INTEGER REFERENCES seasons (id) ON DELETE CASCADE,
    adjustment_points INTEGER DEFAULT (0),
    PRIMARY KEY (
        driver_id,
        season_id
    )
);


-- safe to drop a view since its just an aggregator
DROP VIEW IF EXISTS points_view;

CREATE VIEW IF NOT EXISTS points_view AS
    SELECT seasons.season_num AS year, series.name AS series, drivers.id AS driver_id, game_id, IFNULL(races,0) as RACES, IFNULL(wins,0) as WIN, IFNULL(top5, 0) AS "TOP 5", IFNULL(top10, 0) AS "TOP 10", 
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
    SELECT points_per_race.season_id, points_per_race.driver_id, SUM(finish_points + pole_points + lap_led_points + most_led_points) + IFNULL(adjustment_points, 0) as points
    FROM points_per_race
    LEFT JOIN manual_points ON manual_points.season_id = points_per_race.season_id AND manual_points.driver_id = points_per_race.driver_id
    GROUP BY points_per_race.season_id, points_per_race.driver_id
    ) m ON drivers.id = m.driver_id AND seasons.id = m.season_id

    ORDER BY points DESC;

-- TODO add versions schema: https://stackoverflow.com/questions/3604310/alter-table-add-column-if-not-exists-in-sqlite

DROP VIEW IF EXISTS driver_race_records;

CREATE VIEW driver_race_records AS -- will be renamed
SELECT season_num AS Year,
           race_records.id AS Record_ID,
           race_name AS Race,
           b.season_id AS Season_ID,
           race_records.race_id AS Race_ID,
           track_id AS Track_ID,
           track_name AS Track,
           race_records.driver_id AS Driver_ID,
           drivers.game_id AS Driver_Name,
           race_records.entrant_id AS Entrant_ID,
           d.team_id AS Team_ID,
           d.team_name AS Team_Name,
           b.series_id AS Series_ID,
           finish_position AS Finish,
           start_position AS Start,
           car_number AS Number,
           interval AS Interval,
           laps AS Laps,
           led AS Led,
           IFNULL(total_points, race_records.points) AS Points,
           finish_status AS Status
      FROM race_records
           LEFT JOIN
           drivers ON race_records.driver_id = drivers.id
           LEFT JOIN
           (
               SELECT season_num,
                      races.season_id,
                      series_id,
                      races.id,
                      IFNULL(name, track_name) AS race_name,
                      tracks.id as track_id,
                      track_name
                 FROM races
                      LEFT JOIN
                      tracks ON races.track_id = tracks.id
                      LEFT JOIN
                      (
                          SELECT season_num,
                                 series_id,
                                 id AS season_id
                            FROM seasons
                      )
                      a ON races.season_id = a.season_id
           )
           b ON race_records.race_id = b.id
           LEFT JOIN
           (
               SELECT race_id,
                      driver_id,
                      finish_points + pole_points + lap_led_points + most_led_points AS total_points
                 FROM points_per_race
           )
           c ON race_records.race_id = c.race_id AND 
                race_records.driver_id = c.driver_id
           LEFT JOIN
           (
               SELECT entrants.id AS entrant_id,
                      teams.id AS team_id,
                      teams.name AS team_name
                 FROM entrants
                      LEFT JOIN
                      teams ON teams.id = entrants.team_id
           )
           d ON race_records.entrant_id = d.entrant_id;


CREATE TABLE IF NOT EXISTS teams (
    id   INTEGER PRIMARY KEY
                 UNIQUE
                 NOT NULL,
    name VARCHAR UNIQUE
                 NOT NULL
);

CREATE TABLE IF NOT EXISTS entries (
    id    INTEGER    PRIMARY KEY,
    num    INTEGER,
    season_id INTEGER REFERENCES seasons(id),
    team_id    INTEGER REFERENCES teams(id),
    UNIQUE(num, season_id, team_id) ON CONFLICT IGNORE
    );

CREATE TABLE IF NOT EXISTS entrants (
    id        INTEGER PRIMARY KEY,
    season_id INTEGER REFERENCES seasons (id) ON DELETE CASCADE,
    number    INTEGER,
    team_id   INTEGER REFERENCES teams (id) ON DELETE SET NULL,
    UNIQUE (
        season_id,
        number,
        team_id
    )
);

CREATE TABLE IF NOT EXISTS entrants (
    id        INTEGER PRIMARY KEY,
    season_id INTEGER REFERENCES seasons (id) ON DELETE CASCADE,
    number    INTEGER,
    team_id   INTEGER REFERENCES teams (id) ON DELETE SET NULL,
    UNIQUE (
        season_id,
        number,
        team_id
    )
    ON CONFLICT IGNORE
);

-- alter race_records -> set driver_id as foreign key for drivers (id)
-- add column entrant_id      INTEGER REFERENCES entrants (id)
-- add column id        INTEGER PRIMARY KEY
-- OK: BETTER APPROACH - FORGET ABOUT PRE-UPDATE USERS; FOCUS ON CURRENT ONE AND THEN CREATE A MIGRATION SCRIPT

-- note: this is pretty slow but much simpler than points_view -> possible refactor
-- Maybe I should use an index in one of the underlying columns of driver_race_records?
DROP VIEW IF EXISTS entrant_points_view;
CREATE VIEW entrant_points_view AS
    SELECT Season_ID,
           Year,
           Series_ID,
           driver_race_records.Entrant_ID,
           Number,
           Team_ID,
           Team_Name,
           COUNT( * ) AS RACE,
           IFNULL(wins, 0) AS WIN,
           IFNULL(Top5s, 0) AS [TOP 5],
           IFNULL(Top10s, 0) AS [TOP 10],
           IFNULL(poles, 0) AS POLE,
           SUM(Laps) AS LAPS,
           SUM(Led) AS LED,
           ROUND(AVG(Start), 1) AS [Av. S],
           ROUND(AVG(Finish), 1) AS [Av. F],
           IFNULL(dnf, 0) AS DNF,
           IFNULL(llf, 0) AS LLF,
           SUM(Points) + IFNULL(entrant_manual_points.adjustment_points, 0) AS POINTS --interestingly, int + null = null
      FROM driver_race_records
           LEFT JOIN
           (
               SELECT Entrant_ID,
                      COUNT( * ) AS wins
                 FROM driver_race_records
                WHERE Finish = 1
                GROUP BY Entrant_ID
           )
           a ON driver_race_records.Entrant_ID = a.Entrant_ID
           LEFT JOIN
           (
               SELECT Entrant_ID,
                      COUNT( * ) AS Top5s
                 FROM driver_race_records
                WHERE Finish < 6
                GROUP BY Entrant_ID
           )
           b ON driver_race_records.Entrant_ID = b.Entrant_ID
           LEFT JOIN
           (
               SELECT Entrant_ID,
                      COUNT( * ) AS Top10s
                 FROM driver_race_records
                WHERE Finish < 11
                GROUP BY Entrant_ID
           )
           c ON driver_race_records.Entrant_ID = c.Entrant_ID
           LEFT JOIN
           (
               SELECT Entrant_ID,
                      COUNT( * ) AS poles
                 FROM driver_race_records
                WHERE Start = 1
                GROUP BY Entrant_ID
           )
           d ON driver_race_records.Entrant_ID = d.Entrant_ID
           LEFT JOIN
           (
               SELECT Entrant_ID,
                      COUNT( * ) AS dnf
                 FROM driver_race_records
                WHERE Status != 'Running'
                GROUP BY Entrant_ID
           )
           e ON driver_race_records.Entrant_ID = e.Entrant_ID
           LEFT JOIN
           (
               SELECT driver_race_records.Entrant_ID,
                      COUNT( * ) AS llf
                 FROM driver_race_records
                      LEFT JOIN
                      (
                          SELECT Race_ID,
                                 MAX(Laps) AS total_laps
                            FROM driver_race_records
                           GROUP BY Race_ID
                      )
                      aa ON aa.Race_ID = driver_race_records.Race_ID
                WHERE driver_race_records.Laps = aa.total_laps
                GROUP BY driver_race_records.Entrant_ID
           )
           f ON f.Entrant_ID = driver_race_records.Entrant_ID
           LEFT JOIN
           entrant_manual_points ON entrant_manual_points.entrant_id = driver_race_records.Entrant_ID
     GROUP BY driver_race_records.Entrant_ID
     ORDER BY POINTS DESC;


--why is there so much to do 
CREATE TABLE IF NOT EXISTS entrant_manual_points (
    id                 INTEGER PRIMARY KEY,
    entrant_id         INTEGER REFERENCES drivers (id) ON DELETE CASCADE UNIQUE,
    adjustment_points INTEGER DEFAULT (0)
);
