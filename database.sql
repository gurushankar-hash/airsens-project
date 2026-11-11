BEGIN TRANSACTION;
CREATE TABLE history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, timestamp TEXT,
        aqi INTEGER, pm25 REAL, risk_score REAL, risk_level TEXT);
INSERT INTO "history" VALUES(12,'guru ','2026-10-03 22:59',85,35.4,10.27,'LOW');
INSERT INTO "history" VALUES(13,'guru ','2026-10-03 23:01',85,35.4,10.27,'LOW');
INSERT INTO "history" VALUES(15,'sai','2026-10-03 23:14',196,164.0,74.88,'HIGH');
INSERT INTO "history" VALUES(16,'guru','2026-10-03 23:20',76,76.0,58.31,'MODERATE');
INSERT INTO "history" VALUES(17,'guru','2026-10-03 23:22',76,76.0,58.31,'MODERATE');
INSERT INTO "history" VALUES(18,'guru','2026-10-03 23:24',76,76.0,60.64,'HIGH');
INSERT INTO "history" VALUES(19,'guru shankar','2026-10-03 23:27',165,68.5,31.71,'MODERATE');
INSERT INTO "history" VALUES(20,'guru','2026-10-03 23:29',76,76.0,43.97,'MODERATE');
INSERT INTO "history" VALUES(21,'guru','2026-10-03 23:31',76,76.0,43.97,'MODERATE');
INSERT INTO "history" VALUES(22,'guru shankar','2026-10-03 23:35',155,62.4,40.63,'MODERATE');
INSERT INTO "history" VALUES(23,'guru','2026-10-03 23:36',76,76.0,58.31,'MODERATE');
INSERT INTO "history" VALUES(24,'guru','2026-10-04 11:54',75,15.3,50.72,'MODERATE');
INSERT INTO "history" VALUES(25,'guru shankar','2026-10-04 12:05',142,58.2,27.18,'LOW');
INSERT INTO "history" VALUES(26,'guru','2026-10-04 12:08',53,53.0,55.09,'MODERATE');
INSERT INTO "history" VALUES(27,'guru','2026-10-05 11:13',65,16.8,41.24,'MODERATE');
INSERT INTO "history" VALUES(28,'guru','2026-10-05 16:40',76,76.0,43.97,'MODERATE');
INSERT INTO "history" VALUES(29,'guru','2026-10-19 17:01',53,53.0,55.09,'MODERATE');
INSERT INTO "history" VALUES(30,'baskaran','2026-11-10 21:33',185,185.0,58.9,'MODERATE');
CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            age INTEGER,
            dob TEXT,
            cough TEXT,
            wheezing TEXT,
            breathing TEXT,
            sneezing TEXT,
            dust TEXT
        , city TEXT DEFAULT 'Chennai');
INSERT INTO "users" VALUES(1,'guru ','1234',18,'21/10/2007','Mild','Yes','Mild','Yes','Yes','Chennai');
INSERT INTO "users" VALUES(2,'guru shankar','1234',18,'21/10/2007','Mild','Yes','Mild','Yes','Yes','Chennai');
INSERT INTO "users" VALUES(3,'kannan','1234',18,'21/10/2007','Moderate','Yes','Mild','Yes','Yes','Chennai');
INSERT INTO "users" VALUES(4,'sailesh','1234',18,'12/01/2008','Severe','Yes','None','Yes','Yes','Chennai');
INSERT INTO "users" VALUES(5,'ramu','1234',18,'20/8/1999','Moderate','Yes','Mild','Yes','Yes','Chennai');
INSERT INTO "users" VALUES(6,'somu','guru1234@',18,'21/09/1998','No','No','None','No','No','Chennai');
INSERT INTO "users" VALUES(7,'suresh','123456G@',21,'20\10\2000','Moderate','Yes','Moderate','Yes','Yes','Chennai');
INSERT INTO "users" VALUES(8,'gurushankar183@gmail.com','google_oauth',NULL,NULL,'No','No','None','No','No','Chennai');
INSERT INTO "users" VALUES(9,'nandha','123456N@',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'Chennai');
INSERT INTO "users" VALUES(10,'sameer','123456S@',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'Chennai');
INSERT INTO "users" VALUES(11,'kannan Thiruselvam','Jamuna@82',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'Chennai');
INSERT INTO "users" VALUES(12,'sai','123456@S',18,NULL,NULL,NULL,NULL,NULL,NULL,'trichy');
INSERT INTO "users" VALUES(13,'guru','123456@G',19,NULL,NULL,NULL,NULL,NULL,NULL,'Chennai');
INSERT INTO "users" VALUES(14,'shankar','Shankar@2007',18,NULL,NULL,NULL,NULL,NULL,NULL,'Chennai');
INSERT INTO "users" VALUES(15,'baskaran','Guru@2007',18,NULL,NULL,NULL,NULL,NULL,NULL,'Chennai');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('users',15);
INSERT INTO "sqlite_sequence" VALUES('history',30);
COMMIT;