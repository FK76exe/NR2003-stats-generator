-- This needs to be set up when user firsts opens new application

-- entrants -> create and then populate
INSERT OR IGNORE INTO entrants (season_id, number)
SELECT DISTINCT [Season_ID], Number
FROM race_records_view

-- update race_records (make id and entrants column before)
UPDATE race_records
SET entrant_id = (
   SELECT entrants.id FROM race_records as rr
    LEFT JOIN races ON rr.race_id = races.id
    LEFT JOIN seasons ON seasons.id = races.season_id
    LEFT JOIN entrants ON rr.car_number = entrants.number AND seasons.id = entrants.season_id
    WHERE rr.id = race_records.id
)