#!/usr/bin/env python3

from mscltbck import MusicoletBackup

import os
import logging
import json

logger = logging.getLogger(__name__)


def main() -> int:
    bck = MusicoletBackup(os.path.expanduser("~/Desktop/bck.zip"))
    top = bck.get_top_N_songs_alltime(10)
    print("name\t\t\tartist\t\tlistens\tlistensY\tlistensM\tlistensW")
    for song in top:
        print(
            f"{song['COL_TITLE']}\t{song['COL_ARTIST']}\t{song['COL_NUM_PLAYED']}\t{song['COL_NUM_PLAYED_Y']}\t{song['COL_NUM_PLAYED_M']}\t{song['COL_NUM_PLAYED_W']}"
        )

    alltime = bck.listening_time_alltime / 1000 / 60 / 60
    print(alltime)

    year = bck.listening_time_year / 1000 / 60 / 60
    print(year)

    month = bck.listening_time_month / 1000 / 60 / 60
    print(month)

    week = bck.listening_time_week / 1000 / 60 / 60
    print(week)

    with open(os.path.expanduser("~/Desktop/favs.json"), "w") as f:
        f.write(json.dumps(bck.favorites, ensure_ascii=False))


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
        level=logging.DEBUG,
    )
    exit(main())
