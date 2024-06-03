SELECT seasons.season_num AS year, series.name AS series, game_id, IFNULL(races,0) as RACES, IFNULL(wins,0) as WIN, IFNULL(top5, 0) AS "TOP 5", IFNULL(top10, 0) AS "TOP 10", 
IFNULL(poles,0) AS POLE, IFNULL(laps,0) AS LAPS, IFNULL(led,0) AS LED, ROUND(avs,1) AS "AV. S", ROUND(avf,1) AS "AV. F", IFNULL(dnf,0) AS "DNF", IFNULL(llf, 0) AS "LLF",
points as POINTS
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

ORDER BY points DESC