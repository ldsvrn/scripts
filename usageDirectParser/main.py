#!/usr/bin/env python3

import argparse
import io
import sqlite3
import tempfile
import zipfile
from prettytable import PrettyTable

parser = argparse.ArgumentParser(description='Extract basic information out a usageDirect backup')
parser.add_argument('path', help='usageDirect backup path')
parser.add_argument('-n', default=10, help='Number of results')
args = parser.parse_args()

SQL_TOTAL_TIME = """
SELECT SUM(timeUsed)
FROM usageStats;
"""

SQL_NUMBER_OF_DAYS = """
SELECT (MAX(day) - MIN(day))
FROM usageStats;
"""

SQL_TOTAL_TIME_APPS = f"""
SELECT applicationId, ROUND(SUM(timeUsed) / 3600000.0, 1) AS total_timeUsed
FROM usageStats
GROUP BY applicationId
ORDER BY total_timeUsed DESC
LIMIT {args.n};
"""

db = sqlite3.connect(args.path)
cursor = db.cursor()

# Total watchtime
cursor.execute(SQL_TOTAL_TIME)
total_watchtime = int(cursor.fetchall()[0][0])
print(f"Total screentime is {round(total_watchtime / 1000 / 60 / 60, 1)}h.")

cursor.execute(SQL_NUMBER_OF_DAYS)
total_days = int(cursor.fetchall()[0][0])
print(f"Days in database: {total_days}")

cursor.execute(SQL_TOTAL_TIME_APPS)
top_apps = PrettyTable()
top_apps.field_names = ["App", "Time (h)"]
top_apps.add_rows(cursor.fetchall())
print(top_apps)

