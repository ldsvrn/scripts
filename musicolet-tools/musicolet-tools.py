#!/usr/bin/env python3

from mscltbck import MusicoletBackup

import logging
import argparse

logger = logging.getLogger(__name__)

def main(args) -> int:
    bck = MusicoletBackup(args.path)

    # IFIFIFIFIFIFIFIFIFIFIFIFIFIF
    if args.decrypt:
        bck.export_all_files(args.decrypt)
        # exit with return code 0
        return 0
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(description="Extract information out of a Musicolet backup")
    parser.add_argument(
        "path", 
        help="Musicolet backup path"
    )
    parser.add_argument(
        "-d",
        "--decrypt",
        help="Extracts and decrypts all files to the specified directory",
        required=False,
        metavar="dir",
    )
    # pass the args to the main function
    exit(main(parser.parse_args()))
