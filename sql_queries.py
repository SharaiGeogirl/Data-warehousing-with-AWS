import configparser
# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

ARN = config.get('IAM_ROLE', 'ARN')
SONG_DATA = config.get('S3', 'SONG_DATA')
LOG_DATA = config.get('S3', 'LOG_DATA')
LOG_JSONPATH = config.get('S3', 'LOG_JSONPATH')


# DROP TABLES
staging_events_table_drop = "DROP TABLE IF EXISTS staging_events;"
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs;"
songplay_table_drop = "DROP TABLE IF EXISTS songplays;"
user_table_drop = "DROP TABLE IF EXISTS users;"
song_table_drop = "DROP TABLE IF EXISTS songs;"
artist_table_drop = "DROP TABLE IF EXISTS artists;"
time_table_drop = "DROP TABLE IF EXISTS time;"



# CREATE TABLES
staging_events_table_create= ("""CREATE TABLE IF NOT EXISTS staging_events (
                                                                            artist     VARCHAR,
                                                                            auth       VARCHAR,
                                                                            firstName  VARCHAR,
                                                                            gender     VARCHAR,
                                                                            itemInSession INTEGER,
                                                                            lastName   VARCHAR,
                                                                            length     NUMERIC,
                                                                            level      VARCHAR,
                                                                            location   VARCHAR, 
                                                                            method     VARCHAR,
                                                                            page       VARCHAR,
                                                                            registration NUMERIC,
                                                                            session_id INTEGER,
                                                                            song       VARCHAR,
                                                                            status     INTEGER,
                                                                            ts         BIGINT,
                                                                            user_Agent VARCHAR,
                                                                            userId    INTEGER
);""")


staging_songs_table_create = (""" CREATE TABLE IF NOT EXISTS staging_songs (
                                                                            num_songs INTEGER,
                                                                            artist_id VARCHAR,
                                                                            artist_latitude DECIMAL,
                                                                            artist_longitude DECIMAL,
                                                                            artist_location VARCHAR,
                                                                            artist_name VARCHAR,
                                                                            song_id VARCHAR,
                                                                            title VARCHAR,
                                                                            duration DECIMAL,
                                                                            year INTEGER
);""")


songplay_table_create = (""" CREATE TABLE IF NOT EXISTS songplays(
                                                        songplay_id  INTEGER IDENTITY(0,1) NOT NULL, 
                                                        start_time   TIMESTAMP sortkey, 
                                                        user_id      INTEGER  NOT NULL  distkey, 
                                                        level        VARCHAR ,
                                                        song_id      VARCHAR  , 
                                                        artist_id    VARCHAR ,
                                                        session_id   INTEGER,
                                                        location     VARCHAR , 
                                                        user_agent   VARCHAR,
                                                        PRIMARY KEY (songplay_id)
);""")

user_table_create = (""" CREATE TABLE IF NOT EXISTS users(
                                                        user_id     INTEGER NOT NULL distkey,
                                                        first_name  VARCHAR ,
                                                        last_name   VARCHAR ,
                                                        gender      VARCHAR ,
                                                        level       VARCHAR ,
                                                        PRIMARY KEY (user_id)
);""")

song_table_create = (""" CREATE TABLE IF NOT EXISTS songs(
                                                        song_id     VARCHAR NOT NULL sortkey, 
                                                        title       VARCHAR , 
                                                        artist_id   VARCHAR  ,
                                                        year        INTEGER  , 
                                                        duration    INTEGER ,
                                                        PRIMARY KEY (song_id)
);""")

artist_table_create = ("""CREATE TABLE IF NOT EXISTS artists (
                                                        artist_id   VARCHAR NOT NULL sortkey, 
                                                        name        VARCHAR  , 
                                                        location    VARCHAR  ,
                                                        latitude    DECIMAL ,
                                                        longitude   DECIMAL,
                                                        PRIMARY KEY (artist_id)
);""")

time_table_create = ("""CREATE TABLE IF NOT EXISTS time (
                                                        start_time  TIMESTAMP sortkey,
                                                        hour        INTEGER , 
                                                        day         INTEGER , 
                                                        week        INTEGER , 
                                                        month       INTEGER ,
                                                        year        INTEGER , 
                                                        weekday     INTEGER ,
                                                        PRIMARY KEY (start_time)
);""")


# STAGING TABLES

staging_events_copy = (""" COPY staging_events
                            from {}
                            credentials {}
                            FORMAT AS JSON {}
                            region 'us-west-2';
""").format(config['S3']['LOG_DATA'],config['IAM_ROLE']['ARN'], config['S3']['LOG_JSONPATH'])


staging_songs_copy = ("""COPY staging_songs 
                            from {}
                            credentials {}
                            FORMAT AS JSON 'auto'
                            region 'us-west-2';
""").format(config['S3']['SONG_DATA'],config['IAM_ROLE']['ARN'])


# FINAL TABLES


songplay_table_insert= (""" INSERT INTO songplays(start_time, user_id, level, song_id, artist_id,
                                                    session_id, location, user_agent)
                            SELECT DISTINCT timestamp with time zone 'epoch' + se.ts/1000 * interval '1 second',
                                            se.userId, 
                                            se.level, 
                                            ss.song_id,
                                            ss.artist_id,
                                            se.session_id, 
                                            se.location, 
                                            se.user_agent
                            FROM staging_songs ss
                            LEFT JOIN staging_events se
                                  ON se.song = ss.title AND se.artist = ss.artist_name
                            WHERE se.page= 'NextSong';
""")

        
        
user_table_insert=    ("""INSERT INTO users(user_id, first_name, last_name, gender, level)
                            SELECT DISTINCT  userId,
                                             firstName, 
                                             lastName,
                                             gender, 
                                             level
                                    FROM staging_events 
                                    WHERE userId IS NOT NULL AND page= 'NextSong';
                                   
""")


song_table_insert=    ("""INSERT INTO songs(song_id, title, artist_id, year, duration)
                           SELECT 
                                s.song_id,
                                s.title, 
                                s.artist_id,
                                s.year, 
                                s.duration
                            FROM staging_songs s
                            WHERE song_id IS NOT NULL;
""")


artist_table_insert=  ("""INSERT INTO artists(artist_id, name, location, latitude, longitude)
                           SELECT DISTINCT 
                                 artist_id,
                                 artist_name, 
                                 artist_location,
                                 artist_latitude, 
                                 artist_longitude
                            FROM staging_songs ;
""")

#got assisted by mentor. 
time_table_insert=     ("""INSERT INTO time (start_time, hour, day, week, month, year, weekday)
                                WITH temp_time AS (SELECT TIMESTAMP 'epoch'
                                    + (ts / 1000 * INTERVAL '1 second') AS ts, page FROM staging_events)
                                        SELECT DISTINCT
                                            ts,
                                            EXTRACT(hour FROM ts),
                                            EXTRACT(day FROM ts),
                                            EXTRACT(week FROM ts),
                                            EXTRACT(month FROM ts),
                                            EXTRACT(year FROM ts),
                                            EXTRACT(weekday FROM ts)
                                        FROM temp_time
                                        WHERE page = 'NextSong';

""")


# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create, songplay_table_create, user_table_create, song_table_create, artist_table_create, time_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]
