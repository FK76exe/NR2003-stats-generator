SELECT DISTINCT track_name
FROM race_records
WHERE NOT EXISTS (SELECT track_name FROM tracks)