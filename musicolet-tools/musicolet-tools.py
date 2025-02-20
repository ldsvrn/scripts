#!/usr/bin/env python3

from mscltbck import MusicoletBackup

import logging
import argparse

logger = logging.getLogger(__name__)


def main(args) -> int:
    logger.debug(f"Args: {args}")
    bck = MusicoletBackup(args.path)

    # IFIFIFIFIFIFIFIFIFIFIFIFIFIF
    if args.decrypt:
        bck.export_all_files(args.decrypt)
        # exit with return code 0
        return 0

    if args.print_fav:
        for fav in bck.favorites:
            print(f"{fav['album']} - {fav['title']}")

    if args.print_fav_path:
        for fav in bck.favorites:
            print(fav["path"])

    if args.print_playlists:
        for playlist in bck.playlists:
            print(playlist)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
        level=logging.CRITICAL,
    )
    parser = argparse.ArgumentParser(description="Extract information out of a Musicolet backup")
    parser.add_argument("path", help="Musicolet backup path")
    parser.add_argument(
        "-d",
        "--decrypt",
        help="Extracts and decrypts all files to the specified directory",
        required=False,
        metavar="dir",
    )
    print_group = parser.add_mutually_exclusive_group()
    print_group.add_argument(
        "--print-fav",
        help="Print all of the favourites songs (Album - Song)",
        required=False,
        action="store_true",
    )
    print_group.add_argument(
        "--print-fav-path",
        help="Print all of the favourites songs paths",
        required=False,
        action="store_true",
    )
    print_group.add_argument(
        "--print-playlists",
        help="Print all of playlists names",
        required=False,
        action="store_true",
    )
    # pass the args to the main function
    exit(main(parser.parse_args()))
