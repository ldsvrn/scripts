#!/usr/bin/env python3

from mscltbck import MusicoletBackup

import logging
import argparse
import os

logger = logging.getLogger(__name__)


def subc_export(args, bck: MusicoletBackup) -> int:
    if os.path.exists(args.output):
        print(f"File '{args.output}' already exists!")
        return 1

    # if using the subcommand "export", at least one argument must be used,
    # either the favorites or a playlist, we can assulme
    if args.playlist:
        if bck.playlist_exists(args.playlist):
            playlist = bck.get_playlist(args.playlist)
        else:
            print(f"Playlist '{args.playlist}' does not exist!")
            return 1
    elif args.favorites:
        playlist = bck.favorites
    else:
        # argparse shouldn't let this happen
        print("Invalid arguments for the export subcommand!")
        return 1

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")  # M3U8 header
        for song in playlist:
            # it's in ms in the backup
            duration = round(song["duration"] / 1000)
            path = song["path"]

            # honestly it would be better to just use a regex here
            if args.replace:
                # HAHAHA I LOVE PYTHON LMAO
                for i in [j.split(",") for j in args.replace]:
                    path = path.replace(i[0], i[1])

            f.write(f"#EXTINF:{duration},{song['title']}\n")
            f.write(f"{path}\n")

    return 0


def subc_print(args, bck: MusicoletBackup) -> int:
    if args.favorites:
        for song in bck.favorites:
            print(song["path"] if args.paths else f"{song['album']} - {song['title']}")

    if args.playlist:
        for song in bck.get_playlist(args.playlist.strip()):
            print(song["path"] if args.paths else f"{song['album']} - {song['title']}")

    if args.all_playlists:
        for playlist in bck.playlists:
            print(playlist)
    return 0


def main(args) -> int:
    logger.debug(f"Args: {args}")
    bck = MusicoletBackup(args.backup)

    if args.decrypt:
        bck.export_all_files(args.decrypt)
        return 0

    if args.subcommand == "export":
        return subc_export(args, bck)

    if args.subcommand == "print":
        return subc_print(args, bck)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
        level=logging.CRITICAL,
        # level=logging.INFO,
    )
    parser = argparse.ArgumentParser(description="Extract information out of a Musicolet backup")
    parser.add_argument(
        "backup",
        help="Musicolet backup .zip path",
        metavar="backup_path",
    )
    parser.add_argument(
        "-d",
        "--decrypt",
        help="Extracts and decrypts all files to the specified directory",
        required=False,
        metavar="dir",
    )
    subparsers = parser.add_subparsers(help="Subcommands", dest="subcommand")

    # --- Export subparser
    subp_export = subparsers.add_parser(
        name="export",
        description="Exports playlists or favorites to m3u8 files",
        help="Exports playlists",
    )
    subp_export.add_argument(
        "output",
        help="Path of the m3u8 file",
        # required=True,
    )
    subp_export.add_argument(
        "-r",
        "--replace",
        help="Replace part of the path with something else, comma separated (old,new)",
        required=False,
        metavar="name",
        action="append",
    )
    excg_export = subp_export.add_mutually_exclusive_group(required=True)
    excg_export.add_argument(
        "-p",
        "--playlist",
        help="Choose a playlist to export",
        required=False,
        metavar="name",
    )
    excg_export.add_argument(
        "-f",
        "--favorites",
        help="Export all favourites songs",
        required=False,
        action="store_true",
    )

    # --- Print subparser
    subp_print = subparsers.add_parser(
        name="print",
        description="Print information in the terminal",
        help="Print information in the terminal",
    )
    excg_print = subp_print.add_mutually_exclusive_group()
    excg_print.add_argument(
        "-f",
        "--favorites",
        help="Print all favourites songs",
        required=False,
        action="store_true",
    )
    excg_print.add_argument(
        "-p",
        "--playlist",
        help="Print the content of a playlist",
        required=False,
        metavar="name",
    )
    excg_print.add_argument(
        "--all-playlists",
        help="Print all playlist names",
        required=False,
        action="store_true",
    )

    subp_print.add_argument(
        "--paths",
        help="Print paths instead of names",
        required=False,
        action="store_true",
    )
    # pass the args to the main function
    exit(main(parser.parse_args()))
