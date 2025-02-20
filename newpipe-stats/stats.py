#!/usr/bin/env python3

import argparse
import io
import sqlite3
import tempfile
import zipfile
from prettytable import PrettyTable

parser = argparse.ArgumentParser(description="Extract basic information out a NewPipe backup")
parser.add_argument("path", help="NewPipe backup path")
parser.add_argument("-n", default=10, help="Number of results in top channels")
args = parser.parse_args()

# god bless chatgpt
sql_total_watchtime = """
SELECT CAST(SUM(progress_time) / (1000 * 60 * 60) AS TEXT) || ':' ||
    substr('00' || CAST((SUM(progress_time) / (1000 * 60)) % 60 AS TEXT), -2, 2) || ':' ||
    substr('00' || CAST((SUM(progress_time) / 1000) % 60 AS TEXT), -2, 2) as total_watchtime
FROM stream_state;
"""

sql_top_channels_time = f"""
SELECT uploader, COUNT(uploader) as videos_started, CAST(SUM(progress_time) / (1000 * 60 * 60) AS TEXT) || ':' ||
    substr('00' || CAST((SUM(progress_time) / (1000 * 60)) % 60 AS TEXT), -2, 2) || ':' ||
    substr('00' || CAST((SUM(progress_time) / 1000) % 60 AS TEXT), -2, 2) as channel_time
FROM stream_state
JOIN streams ON stream_state.stream_id = streams.uid
GROUP BY uploader
ORDER BY COUNT(uploader) DESC
LIMIT {args.n};
"""

sql_number_videos = f"""
SELECT uploader, COUNT(uploader) AS videos_in_db
FROM streams
GROUP BY uploader
ORDER BY COUNT(uploader) DESC
LIMIT {args.n};
"""

with zipfile.ZipFile(args.path, "r") as newpipe_data:
    with tempfile.TemporaryDirectory() as tempdir:
        newpipe_data.extract("newpipe.db", tempdir)
        db = sqlite3.connect(f"{tempdir}/newpipe.db")
        cursor = db.cursor()

        print(
            "/!\ Watchtimes are calculated with the saved playback positions and are not accurate.\n"
        )

        # Total watchtime
        cursor.execute(sql_total_watchtime)
        total_watchtime = cursor.fetchall()[0][0]
        print(f"Total watchtime is {total_watchtime}.")

        # Top channels time
        cursor.execute(sql_top_channels_time)
        top_chan = PrettyTable()
        top_chan.field_names = ["Channel", " Started Videos", "Watchtime"]
        top_chan.add_rows(cursor.fetchall())

        # Number of videos in database
        cursor.execute(sql_number_videos)
        top_chan2 = PrettyTable()
        top_chan2.field_names = ["Channel", "Videos in database"]
        top_chan2.add_rows(cursor.fetchall())

        print(top_chan, end="\n\n")
        print(top_chan2)
