-- Sample data to get the user started immediately

-- Latford points system
INSERT OR IGNORE INTO point_systems (name) VALUES ('Latford System');

INSERT OR IGNORE INTO point_system_scores
VALUES
(1, 1, 175),
(1, 2, 170),
(1, 3, 165),
(1, 4, 160),
(1, 5, 155),
(1, 6, 150),
(1, 7, 146),
(1, 8, 142),
(1, 9, 138),
(1, 10, 134),
(1, 11, 130),
(1, 12, 127),
(1, 13, 124),
(1, 14, 121),
(1, 15, 118),
(1, 16, 115),
(1, 17, 112),
(1, 18, 109),
(1, 19, 106),
(1, 20, 103),
(1, 21, 100),
(1, 22, 97),
(1, 23, 94),
(1, 24, 91),
(1, 25, 88),
(1, 26, 85),
(1, 27, 82),
(1, 28, 79),
(1, 29, 76),
(1, 30, 73),
(1, 31, 70),
(1, 32, 67),
(1, 33, 64),
(1, 34, 61),
(1, 35, 58),
(1, 36, 55),
(1, 37, 52),
(1, 38, 49),
(1, 39, 46),
(1, 40, 43),
(1, 41, 40),
(1, 42, 37),
(1, 43, 34);

INSERT OR IGNORE INTO bonus_points (system_id, bonus_condition, points)
VALUES
(1, 1, 0),
(1, 2, 5),
(1, 3, 5);

INSERT OR IGNORE INTO tracks 
VALUES
(1, 'Daytona', 2.5, 1, 4),
(2, 'Rockingham', 1.017, 0, 4),
(3, 'Las Vegas', 1.5, 0, 4),
(4, 'Atlanta', 1.54, 0 ,4),
(5, 'Darlington', 1.366, 0, 4),
(6, 'Bristol', 0.533, 0, 4),
(7, 'Texas', 1.5, 0, 4),
(8, 'Talladega', 2.66, 1, 4),
(9, 'Martinsville', 0.526, 0, 4),
(10, 'Fontana', 2.0, 0, 4),
(11, 'Richmond', 0.75, 0, 4),
(12, 'Charlotte', 1.5, 0, 4),
(13, 'Dover', 1, 0, 4),
(14, 'Pocono', 2.5, 0, 4),
(15, 'Michigan', 2, 0, 4),
(16, 'Sonoma', 1.99, 0, 2),
(17, 'Chicagoland', 1.5, 0, 4),
(18, 'New Hampshire', 1.058, 0, 4),
(19, 'Indianapolis', 2.5, 0, 4),
(20, 'Watkins Glen', 2.45, 0, 2),
(21, 'Kansas', 1.5, 0, 2),
(22, 'Phoenix', 1, 0, 2),
(23, 'Homestead', 1.5, 0, 2);