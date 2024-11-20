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

-- ALTER TABLE seasons ADD COLUMN points_system id INTEGER REFERENCES points_systems(id); -- no assigned points system leads to null

-- TODO add versions schema: https://stackoverflow.com/questions/3604310/alter-table-add-column-if-not-exists-in-sqlite