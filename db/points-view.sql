SELECT a.year, series.name AS series, game_id, IFNULL(races,0) as RACES, IFNULL(wins,0) as WIN, IFNULL(top5, 0) AS "TOP 5", IFNULL(top10, 0) AS "TOP 10", 
IFNULL(poles,0) AS POLE, IFNULL(laps,0) AS LAPS, IFNULL(led,0) AS LED, ROUND(avs,1) AS "AV. S", ROUND(avf,1) AS "AV. F", IFNULL(dnf,0) AS "DNF", IFNULL(llf,0) as "LLF",
points as POINTS
FROM drivers, series

JOIN (
SELECT race_year as year, series_id, driver_id, COUNT(*) as races FROM race_records GROUP BY year, series_id, driver_id
) a ON drivers.id = a.driver_id AND series.id = a.series_id

LEFT JOIN (
SELECT race_year as year, series_id, driver_id, COUNT(*) as wins FROM race_records WHERE finish_position = 1 GROUP BY year, series_id, driver_id
) b ON drivers.id = b.driver_id AND series.id = b.series_id AND a.year = b.year

LEFT JOIN (
SELECT race_year as year, series_id, driver_id, COUNT(*) as top5 FROM race_records WHERE finish_position < 6 GROUP BY year, series_id, driver_id
) c ON drivers.id = c.driver_id AND series.id = c.series_id AND a.year = c.year

LEFT JOIN (
SELECT race_year as year, series_id, driver_id, COUNT(*) as top10 FROM race_records WHERE finish_position < 11 GROUP BY year, series_id, driver_id
) d ON drivers.id = d.driver_id AND series.id = d.series_id AND a.year = d.year

LEFT JOIN (
SELECT race_year as year, series_id, driver_id, COUNT(*) as poles FROM race_records WHERE start_position = 1 GROUP BY year, series_id, driver_id
) h ON drivers.id = h.driver_id AND series.id = h.series_id AND a.year = h.year

LEFT JOIN (
SELECT race_year as year, series_id, driver_id, SUM(laps) as laps FROM race_records GROUP BY year, series_id, driver_id
) e ON drivers.id = e.driver_id AND series.id = e.series_id AND a.year = e.year

LEFT JOIN (
SELECT race_year as year, series_id, driver_id, SUM(led) as led FROM race_records GROUP BY year, series_id, driver_id
) f ON drivers.id = f.driver_id AND series.id = f.series_id AND a.year = f.year

LEFT JOIN (
SELECT race_year as year, series_id, driver_id, AVG(start_position) as avs FROM race_records GROUP BY year, series_id, driver_id
) g ON drivers.id = g.driver_id AND series.id = g.series_id AND a.year = g.year

LEFT JOIN (
SELECT race_year as year, series_id, driver_id, AVG(finish_position) as avf FROM race_records GROUP BY year, series_id, driver_id
) i ON drivers.id = i.driver_id AND series.id = i.series_id AND a.year = i.year

LEFT JOIN (
SELECT race_year as year, series_id, driver_id, COUNT(*) as dnf FROM race_records WHERE finish_status IS NOT 'Running' GROUP BY year, series_id, driver_id 
) j ON drivers.id = j.driver_id AND series.id = j.series_id AND a.year = j.year

LEFT JOIN (
SELECT race_year as year, series_id, driver_id, SUM(points) as points FROM race_records GROUP BY year, series_id, driver_id 
) k ON drivers.id = k.driver_id AND series.id = k.series_id AND a.year = k.year

LEFT JOIN (
SELECT race_year as year, race_file, series_id, driver_id, COUNT(*) as llf
FROM race_records
LEFT JOIN (
    SELECT race_file as a_race_file, max(laps) as total_laps
    FROM race_records
    GROUP BY race_year, race_file
) a WHERE race_file = a_race_file AND laps = a.total_laps
GROUP BY driver_id, race_year, series_id
) l ON drivers.id = l.driver_id AND series.id = l.series_id AND a.year = l.year

ORDER BY points DESC