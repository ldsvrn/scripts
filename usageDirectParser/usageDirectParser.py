#!/usr/bin/env python3

import argparse
import io
import sqlite3
import tempfile
import zipfile
from prettytable import PrettyTable

parser = argparse.ArgumentParser(description='Extract basic information out a usageDirect backup')
parser.add_argument('path', help='usageDirect backup path')
parser.add_argument('-n', default=20, help='Number of results')
parser.add_argument('-i', '--ignore', help='Ignore apps (csv)', metavar="AppId", type=str, required=False)
args = parser.parse_args()

# some apps, like the clock have a HUGE screen time because of always on displays
# this is technically unsafe as it allows for SQL injection but how cares here ? 
IGNORED_APPS = ",".join([f'"{item.strip()}"' for item in ["com.android.deskclock"] + args.ignore.split(',')]) \
                if args.ignore else '"com.android.deskclock"'  

SQL_TOTAL_TIME = f"""
SELECT SUM(timeUsed)
FROM usageStats
WHERE applicationId NOT IN  ( {IGNORED_APPS} );
"""

SQL_NUMBER_OF_DAYS = """
SELECT (MAX(day) - MIN(day))
FROM usageStats;
"""

SQL_TOTAL_TIME_APPS = f"""
SELECT applicationId, ROUND(SUM(timeUsed) / 3600000.0, 1) AS total_timeUsed
FROM usageStats
WHERE applicationId NOT IN ( {IGNORED_APPS} )
GROUP BY applicationId
ORDER BY total_timeUsed DESC
LIMIT {args.n};
"""

db = sqlite3.connect(args.path)
cursor = db.cursor()

# Total watchtime
cursor.execute(SQL_TOTAL_TIME)
total_screentime = int(cursor.fetchall()[0][0]) / 1000 / 60 / 60
print(f"Total screentime is {round(total_screentime , 1)}h.")

cursor.execute(SQL_NUMBER_OF_DAYS)
total_days = int(cursor.fetchall()[0][0])
print(f"Days in database: {total_days}, average: {round(total_screentime/total_days, 1)}h/day")

cursor.execute(SQL_TOTAL_TIME_APPS)
top_apps = PrettyTable()
top_apps.field_names = ["App", "Time (h)"]
data = cursor.fetchall()
top_apps.add_rows(data)
print(top_apps)

total_shown_time = 0
for item in data:
    total_shown_time += item[1]
# what the f--- this is awful
print(f"Total for the top {args.n} apps: {round(total_shown_time, 1)}h ({round(total_shown_time / total_screentime * 100, 1)}% of total)")

