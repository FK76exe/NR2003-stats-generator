-- points view
CREATE VIEW IF NOT EXISTS points_view AS
    SELECT seasons.season_num AS year,
           series.name AS series,
           game_id,
           IFNULL(races, 0) AS RACES,
           IFNULL(wins, 0) AS WIN,
           IFNULL(top5, 0) AS [TOP 5],
           IFNULL(top10, 0) AS [TOP 10],
           IFNULL(poles, 0) AS POLE,
           IFNULL(laps, 0) AS LAPS,
           IFNULL(led, 0) AS LED,
           ROUND(avs, 1) AS [AV. S],
           ROUND(avf, 1) AS [AV. F],
           IFNULL(dnf, 0) AS DNF,
           IFNULL(llf, 0) AS LLF,
           points AS POINTS
      FROM drivers,
           seasons
           JOIN
           series ON series.id = seasons.series_id
           JOIN
           (
               SELECT season_id,
                      race_id,
                      driver_id,
                      COUNT( * ) AS races
                 FROM race_records
                      LEFT JOIN
                      races ON race_id = races.id
                GROUP BY season_id,
                         driver_id
           )
           a ON drivers.id = a.driver_id AND 
                seasons.id = a.season_id
           LEFT JOIN
           (
               SELECT season_id,
                      race_id,
                      driver_id,
                      COUNT( * ) AS wins
                 FROM race_records
                      LEFT JOIN
                      races ON race_id = races.id
                WHERE finish_position = 1
                GROUP BY season_id,
                         driver_id
           )
           b ON drivers.id = b.driver_id AND 
                seasons.id = b.season_id
           LEFT JOIN
           (
               SELECT season_id,
                      race_id,
                      driver_id,
                      COUNT( * ) AS top5
                 FROM race_records
                      LEFT JOIN
                      races ON race_id = races.id
                WHERE finish_position < 6
                GROUP BY season_id,
                         driver_id
           )
           c ON drivers.id = c.driver_id AND 
                seasons.id = c.season_id
           LEFT JOIN
           (
               SELECT season_id,
                      race_id,
                      driver_id,
                      COUNT( * ) AS top10
                 FROM race_records
                      LEFT JOIN
                      races ON race_id = races.id
                WHERE finish_position < 11
                GROUP BY season_id,
                         driver_id
           )
           d ON drivers.id = d.driver_id AND 
                seasons.id = d.season_id
           LEFT JOIN
           (
               SELECT season_id,
                      race_id,
                      driver_id,
                      COUNT( * ) AS poles
                 FROM race_records
                      LEFT JOIN
                      races ON race_id = races.id
                WHERE start_position = 1
                GROUP BY season_id,
                         driver_id
           )
           h ON drivers.id = h.driver_id AND 
                seasons.id = h.season_id
           LEFT JOIN
           (
               SELECT season_id,
                      race_id,
                      driver_id,
                      SUM(laps) AS laps
                 FROM race_records
                      LEFT JOIN
                      races ON race_id = races.id
                GROUP BY season_id,
                         driver_id
           )
           e ON drivers.id = e.driver_id AND 
                seasons.id = e.season_id
           LEFT JOIN
           (
               SELECT season_id,
                      race_id,
                      driver_id,
                      SUM(led) AS led
                 FROM race_records
                      LEFT JOIN
                      races ON race_id = races.id
                GROUP BY season_id,
                         driver_id
           )
           f ON drivers.id = f.driver_id AND 
                seasons.id = f.season_id
           LEFT JOIN
           (
               SELECT season_id,
                      race_id,
                      driver_id,
                      AVG(start_position) AS avs
                 FROM race_records
                      LEFT JOIN
                      races ON race_id = races.id
                GROUP BY season_id,
                         driver_id
           )
           g ON drivers.id = g.driver_id AND 
                seasons.id = g.season_id
           LEFT JOIN
           (
               SELECT season_id,
                      race_id,
                      driver_id,
                      AVG(finish_position) AS avf
                 FROM race_records
                      LEFT JOIN
                      races ON race_id = races.id
                GROUP BY season_id,
                         driver_id
           )
           i ON drivers.id = i.driver_id AND 
                seasons.id = i.season_id
           LEFT JOIN
           (
               SELECT season_id,
                      race_id,
                      driver_id,
                      COUNT( * ) AS dnf
                 FROM race_records
                      LEFT JOIN
                      races ON race_id = races.id
                WHERE finish_status IS NOT 'Running'
                GROUP BY season_id,
                         driver_id
           )
           j ON drivers.id = j.driver_id AND 
                seasons.id = j.season_id
           LEFT JOIN
           (
               SELECT season_id,
                      race_id,
                      driver_id,
                      SUM(points) AS points
                 FROM race_records
                      LEFT JOIN
                      races ON race_id = races.id
                GROUP BY season_id,
                         driver_id
           )
           k ON drivers.id = k.driver_id AND 
                seasons.id = k.season_id
           LEFT JOIN
           (
               SELECT season_id,
                      driver_id,
                      COUNT( * ) AS llf
                 FROM race_records
                      LEFT JOIN
                      (
                          SELECT races.id,
                                 races.season_id,
                                 max(laps) AS total_laps
                            FROM race_records
                                 LEFT JOIN
                                 races ON race_id = races.id
                           GROUP BY races.id
                      )
                      a
                WHERE race_id = a.id AND 
                      laps = a.total_laps
                GROUP BY driver_id,
                         season_id
           )
           l ON drivers.id = l.driver_id AND 
                seasons.id = l.season_id
     ORDER BY points DESC;

-- track overview
CREATE VIEW IF NOT EXISTS track_race_overview AS
    SELECT tracks.id,
           series_id,
           b.name AS series,
           season_num,
           races.name,
           laps,
           ROUND(laps * tracks.length_miles) AS miles,
           pole_sitter,
           winner,
           speed
      FROM races
           LEFT JOIN
           (
               SELECT race_id,
                      game_id AS winner,
                      laps,
                      interval AS speed
                 FROM race_records
                      LEFT JOIN
                      drivers ON drivers.id = race_records.driver_id
                WHERE finish_position = 1
           )
           a ON races.id = a.race_id
           LEFT JOIN
           (
               SELECT seasons.id,
                      series.id AS series_id,
                      series.name,
                      season_num
                 FROM seasons
                      LEFT JOIN
                      series ON seasons.series_id = series.id
           )
           b ON races.season_id = b.id
           LEFT JOIN
           tracks ON tracks.id = races.track_id
           LEFT JOIN
           (
               SELECT race_id,
                      game_id AS pole_sitter
                 FROM race_records
                      LEFT JOIN
                      drivers ON drivers.id = race_records.driver_id
                WHERE start_position = 1
           )
           c ON races.id = c.race_id
     ORDER BY b.series_id ASC,
              season_num ASC;
