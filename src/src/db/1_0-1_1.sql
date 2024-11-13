-- points system schema
CREATE TABLE IF NOT EXISTS point_systems  (
    id      INTEGER PRIMARY KEY,
    name    VARCHAR UNIQUE
);

-- points scoring criteria schema
CREATE TABLE  IF NOT EXISTS point_system_scores (
    system_id  REFERENCES point_systems(id) ON DELETE CASCADE,
    position   INTEGER
    points     INTEGER DEFAULT 0
);