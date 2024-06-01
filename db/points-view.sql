--SELECT a.year, series.name AS series, game_id, IFNULL(races,0) as RACES
--FROM drivers, series
--
--JOIN (
--SELECT year, race_id, series, driver_id, COUNT(*) as races FROM race_records LEFT JOIN races ON race_id = races.id
--GROUP BY year, series, driver_id
--) a ON drivers.id = a.driver_id AND series.id = a.series

SELECT a.year, series.name AS series, game_id, IFNULL(races,0) as RACES, IFNULL(wins,0) as WIN, IFNULL(top5, 0) AS "TOP 5", IFNULL(top10, 0) AS "TOP 10", 
IFNULL(poles,0) AS POLE, IFNULL(laps,0) AS LAPS, IFNULL(led,0) AS LED, ROUND(avs,1) AS "AV. S", ROUND(avf,1) AS "AV. F", IFNULL(dnf,0) AS "DNF", IFNULL(llf,0) as "LLF",
points as POINTS
FROM drivers, series

JOIN (
SELECT year as year, race_id, series, driver_id, COUNT(*) as races FROM race_records LEFT JOIN races ON race_id = races.id GROUP BY year, series, driver_id
) a ON drivers.id = a.driver_id AND series.id = a.series

LEFT JOIN (
SELECT year as year, race_id, series, driver_id, COUNT(*) as wins FROM race_records LEFT JOIN races ON race_id = races.id WHERE finish_position = 1 GROUP BY year, series, driver_id
) b ON drivers.id = b.driver_id AND series.id = b.series AND a.year = b.year

LEFT JOIN (
SELECT year as year, race_id, series, driver_id, COUNT(*) as top5 FROM race_records LEFT JOIN races ON race_id = races.id  WHERE finish_position < 6 GROUP BY year, series, driver_id
) c ON drivers.id = c.driver_id AND series.id = c.series AND a.year = c.year

LEFT JOIN (
SELECT year as year, race_id, series, driver_id, COUNT(*) as top10 FROM race_records LEFT JOIN races ON race_id = races.id  WHERE finish_position < 11 GROUP BY year, series, driver_id
) d ON drivers.id = d.driver_id AND series.id = d.series AND a.year = d.year

LEFT JOIN (
SELECT year as year, race_id, series, driver_id, COUNT(*) as poles FROM race_records LEFT JOIN races ON race_id = races.id  WHERE start_position = 1 GROUP BY year, series, driver_id
) h ON drivers.id = h.driver_id AND series.id = h.series AND a.year = h.year

LEFT JOIN (
SELECT year as year, race_id, series, driver_id, SUM(laps) as laps FROM race_records LEFT JOIN races ON race_id = races.id  GROUP BY year, series, driver_id
) e ON drivers.id = e.driver_id AND series.id = e.series AND a.year = e.year

LEFT JOIN (
SELECT year as year, race_id, series, driver_id, SUM(led) as led FROM race_records LEFT JOIN races ON race_id = races.id  GROUP BY year, series, driver_id
) f ON drivers.id = f.driver_id AND series.id = f.series AND a.year = f.year

LEFT JOIN (
SELECT year as year, race_id, series, driver_id, AVG(start_position) as avs FROM race_records  LEFT JOIN races ON race_id = races.id GROUP BY year, series, driver_id
) g ON drivers.id = g.driver_id AND series.id = g.series AND a.year = g.year

LEFT JOIN (
SELECT year as year, race_id, series, driver_id, AVG(finish_position) as avf FROM race_records LEFT JOIN races ON race_id = races.id  GROUP BY year, series, driver_id
) i ON drivers.id = i.driver_id AND series.id = i.series AND a.year = i.year

LEFT JOIN (
SELECT year as year, race_id, series, driver_id, COUNT(*) as dnf FROM race_records LEFT JOIN races ON race_id = races.id  WHERE finish_status IS NOT 'Running' GROUP BY year, series, driver_id 
) j ON drivers.id = j.driver_id AND series.id = j.series AND a.year = j.year

LEFT JOIN (
SELECT year as year, race_id, series, driver_id, SUM(points) as points FROM race_records LEFT JOIN races ON race_id = races.id  GROUP BY year, series, driver_id 
) k ON drivers.id = k.driver_id AND series.id = k.series AND a.year = k.year

LEFT JOIN (
SELECT year, series, driver_id, COUNT(*) as llf
FROM race_records
LEFT JOIN (
    SELECT races.id, races.year, races.series, max(laps) as total_laps
    FROM race_records
    LEFT JOIN races ON race_id = races.id
    GROUP BY races.id
) a WHERE race_id = a.id AND laps = a.total_laps
GROUP BY driver_id, year, series
) l ON drivers.id = l.driver_id AND series.id = l.series AND a.year = l.year

ORDER BY points DESC