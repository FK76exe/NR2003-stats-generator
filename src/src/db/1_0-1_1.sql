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

CREATE VIEW points_view AS
SELECT 
    Year AS year, 
    series.name AS series, 
    Driver_ID AS driver_id, 
    Driver_Name AS game_id, 
    COUNT(*) as RACES, 
    SUM(iif(Finish=1,1,0)) as WIN, 
    SUM(iif(Finish<6,1,0)) AS [TOP 5], 
    SUM(iif(Finish<11,1,0)) AS [TOP 10], 
    SUM(iif(Start=1,1,0)) AS POLE, 
    SUM(Laps) AS LAPS, 
    SUM(Led) AS LED, 
    ROUND(Start,1) AS [AV. S], 
    ROUND(Finish,1) AS [AV. F], 
    SUM(iif(Status='Running',0,1)) AS DNF, 
    SUM(iif(Laps=Max_Laps,1,0)) AS LLF,
    SUM(Points) as POINTS
    FROM driver_race_records
    LEFT JOIN series ON series.id = Series_ID
    LEFT JOIN (
        SELECT Race_ID, MAX(Laps) AS Max_Laps
        FROM driver_race_records
        GROUP BY Race_ID        
    ) a ON driver_race_records.Race_ID = a.Race_ID
    GROUP BY driver_id, Year, Series_ID
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
           SUM(iif(Finish=1,1,0)) AS WIN,
           SUM(iif(Finish<6,1,0)) AS [TOP 5],
           SUM(iif(Finish<11,1,0)) AS [TOP 10],
           SUM(iif(Start=1,1,0)) AS POLE,
           SUM(Laps) AS LAPS,
           SUM(Led) AS LED,
           ROUND(AVG(Start), 1) AS [Av. S],
           ROUND(AVG(Finish), 1) AS [Av. F],
           SUM(iif(Status='Running',0,1)) AS DNF,
           SUM(iif(Laps=Max_Laps,1,0)) AS LLF,
           SUM(Points) + IFNULL(entrant_manual_points.adjustment_points, 0) AS POINTS --interestingly, int + null = null
      FROM driver_race_records
           LEFT JOIN
           (
               SELECT Race_ID, MAX(Laps) as Max_Laps
               FROM driver_race_records
               GROUP BY Race_ID
           )
           a ON a.Race_ID = driver_race_records.Race_ID
           LEFT JOIN entrant_manual_points ON entrant_manual_points.entrant_id = driver_race_records.Entrant_ID
     GROUP BY driver_race_records.Entrant_ID
     ORDER BY POINTS DESC;


--why is there so much to do 
CREATE TABLE IF NOT EXISTS entrant_manual_points (
    id                 INTEGER PRIMARY KEY,
    entrant_id         INTEGER REFERENCES drivers (id) ON DELETE CASCADE UNIQUE,
    adjustment_points INTEGER DEFAULT (0)
);

DROP VIEW track_aggregate_stats;
CREATE VIEW track_aggregate_stats AS
    SELECT Driver_Name,
           Series_ID,
           Track_ID,
           Track,
           COUNT( * ) AS Starts,
           SUM(iif(Finish = 1, 1, 0) ) AS Wins,
           SUM(iif(Finish < 6, 1, 0) ) AS [Top 5],
           SUM(iif(Finish < 11, 1, 0) ) AS [Top 10],
           SUM(iif(Start = 1, 1, 0) ) AS Poles,
           SUM(Laps) AS Laps,
           ROUND(SUM(Laps * length_miles), 1) AS Miles,
           SUM(Led) AS Led,
           ROUND(SUM(Led * length_miles), 1) AS [Miles Led],
           round(avg(Start), 1) AS [Av. S],
           ROUND(avg(Finish), 1) AS [Av. F],
           SUM(iif(Status = 'Running', 0, 1) ) AS DNF,
           SUM(iif(Laps = Max_Laps, 1, 0) ) AS LLF,
           SUM(Points) AS Points
      FROM driver_race_records
           LEFT JOIN
           (
               SELECT Race_ID,
                      MAX(Laps) AS Max_Laps
                 FROM driver_race_records
                GROUP BY Race_ID
           )
           a ON driver_race_records.Race_ID = a.Race_ID
           LEFT JOIN
           tracks ON Track_ID = tracks.id
     GROUP BY Driver_Name,
              Series_ID,
              Track_ID;

