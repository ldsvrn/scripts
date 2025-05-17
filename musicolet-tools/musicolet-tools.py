#!/usr/bin/env python3

from mscltbck import MusicoletBackup

import logging
import argparse
import os

logger = logging.getLogger(__name__)


def subc_export(args, bck: MusicoletBackup) -> int:
    # make the output dir if it does not exist
    try:
        os.makedirs(args.output, exist_ok=True)
    except FileExistsError:
        print(f"FileExistsError: {args.output} is probably a file!")

    # if using the subcommand "export", at least one argument must be used
    # the 'playlists' variable is a zip with the name of playlist and the dict
    if args.playlist:
        if bck.playlist_exists(args.playlist):
            playlists = zip([args.playlist], [bck.get_playlist(args.playlist)])
        else:
            print(f"Playlist '{args.playlist}' does not exist!")
            return 1
    elif args.favorites:
        playlists = zip(["Favorites"], [bck.favorites])
    elif args.all:
        playlists = zip(
            bck.playlists + ["Favorites"],
            [bck.get_playlist(i) for i in bck.playlists] + [bck.favorites],
        )
    elif args.top or args.top_time:
        # if by time use get_top_songs_alltime_by_time
        top_raw = (
            bck.get_top_songs_alltime(args.top)
            if args.top
            else bck.get_top_songs_alltime_by_time(args.top_time)
        )
        # i need to adapt the data in the correct format for the m3u8 code to work
        name = (
            f"Top {args.top} songs by listens (alltime)"
            if args.top
            else f"Top {args.top_time} songs by time (alltime)"
        )
        top = [
            {
                "path": i["COL_PATH"],
                "duration": int(i["COL_DURATION"]),
                "title": i["COL_TITLE"],
            }
            for i in top_raw
        ]
        playlists = zip([name], [top])

    else:
        # argparse shouldn't let this happen
        print("Invalid arguments for the export subcommand!")
        return 1

    for cur_playlist_name, cur_playlist in playlists:
        m3u8_path = os.path.join(args.output, cur_playlist_name + ".m3u8")
        # add a number to the file if dest file already exists
        if os.path.exists(m3u8_path):
            number = 1
            while os.path.exists(m3u8_path):
                m3u8_path = os.path.join(args.output, cur_playlist_name + f" ({number}).m3u8")
                number += 1

        exported_count = 0
        with open(m3u8_path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")  # M3U8 header
            for song in cur_playlist:
                # it's in ms in the backup
                duration = round(song["duration"] / 1000)
                path = song["path"]

                # honestly it would be better to just use a regex here
                if args.replace:
                    # HAHAHA I LOVE PYTHON LMAO
                    for i in [j.split(",") for j in args.replace]:
                        # this is so bad but who cares
                        # the reason I need this is if I want a second replace
                        # applied only if the first replace is done
                        if i[0] in path:
                            path = path.replace(i[0], i[1])
                            if len(i) == 4:
                                path = path.replace(i[2], i[3])
                # if --check flag is set args.check=True, the file will have to exist
                # to be written in the playlist
                if not args.check or os.path.exists(path):
                    f.write(f"#EXTINF:{duration},{song['title']}\n")
                    f.write(f"{path}\n")
                    exported_count += 1
                else:
                    logger.info(f"Skipping {path}")
        print(
            f"=> Successfully exported {exported_count} songs out of {len(cur_playlist)} in {m3u8_path}."
        )
    return 0


def subc_print(args, bck: MusicoletBackup) -> int:
    if args.favorites:
        for song in bck.favorites:
            print(song["path"] if args.paths else f"{song['title']} - {song['album']}")

    if args.playlist:
        for song in bck.get_playlist(args.playlist.strip()):
            print(song["path"] if args.paths else f"{song['title']} - {song['album']}")

    if args.top or args.top_time:
        # if by time use get_top_songs_alltime_by_time
        top = (
            bck.get_top_songs_alltime(args.top)
            if args.top
            else bck.get_top_songs_alltime_by_time(args.top_time)
        )
        for song in top:
            # the IS the artists here, and i COULD lookup the artist in the DB for the fav and playlists
            # but i WON'T because i aleady committed way too much time on this project
            minutes = round((song["COL_NUM_PLAYED"] * song["COL_DURATION"]) / 60000)
            # I want the info so fuck PEP8
            print(
                song["COL_PATH"]
                if args.paths
                else f"(Listens: {song['COL_NUM_PLAYED']}, {minutes}min, {round(minutes/60, 1)}h) {song['COL_TITLE'] } - {song['COL_ALBUM']} - {song['COL_ARTIST']}"
            )

    if args.all_playlists:
        for playlist in bck.playlists:
            print(playlist)
    return 0


def subc_makezip(args) -> int:
    if not args.output.endswith(".zip"):
        print("ERROR: Output is not a .zip!")
        return 1

    MusicoletBackup.encrypt_backup(args.input, args.output)
    return 0


def main(args) -> int:
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
        level=logging.DEBUG if args.verbose else logging.CRITICAL,
    )

    logger.debug(f"Args: {args}")

    # makezip does not need the backup
    if args.subcommand == "makezip":
        return subc_makezip(args)

    bck = MusicoletBackup(args.backup)

    if args.decrypt:
        bck.export_all_files(args.decrypt)
        return 0

    if args.subcommand == "export":
        return subc_export(args, bck)

    if args.subcommand == "print":
        return subc_print(args, bck)


if __name__ == "__main__":
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
    parser.add_argument(
        "-v",
        "--verbose",
        help="Include DEBUG level logs",
        required=False,
        action="store_true",
    )
    subparsers = parser.add_subparsers(help="Subcommands", dest="subcommand")

    # --------------------------------------------- Export subparser
    subp_export = subparsers.add_parser(
        name="export",
        description="Exports playlists or favorites to m3u8 files",
        help="Exports playlists",
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
        "-t",
        "--top",
        help="Export the top N songs alltime (by listens)",
        required=False,
        metavar="N",
        type=int,
    )
    excg_export.add_argument(
        "--top-time",
        help="Export the top N songs alltime (by time)",
        required=False,
        metavar="N",
        type=int,
    )
    excg_export.add_argument(
        "-f",
        "--favorites",
        help="Export all favourites songs",
        required=False,
        action="store_true",
    )
    excg_export.add_argument(
        "-a",
        "--all",
        help="Export all playlists and favourites songs",
        required=False,
        action="store_true",
    )
    subp_export.add_argument(
        "-r",
        "--replace",
        help="""Replace part of the path with something else, comma separated 'old,new,old2,new2', 
        last 2 values are not required and will apply only if the first replace is done, 
        this argument can be called multiple times""",
        required=False,
        metavar="csv",
        action="append",
    )
    subp_export.add_argument(
        "-c",
        "--check",
        help="Check if file exists before writing it to the m3u8, test done after replace",
        required=False,
        action="store_true",
    )
    subp_export.add_argument(
        "output",
        help="Output dir",
        # required=True,
    )

    # --------------------------------------------- Print subparser
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
        "-t",
        "--top",
        help="Print top N played songs (by listens)",
        required=False,
        metavar="N",
        type=int,
    )
    excg_print.add_argument(
        "--top-time",
        help="Print top N played songs (by time)",
        required=False,
        metavar="N",
        type=int,
    )
    excg_print.add_argument(
        "-a",
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

    subp_makezip = subparsers.add_parser(
        name="makezip",
        description="Make a valid Musicolet backup from a directory",
        help="Make a valid Musicolet backup from a directory",
    )

    subp_makezip.add_argument(
        "input",
        help="Input dir",
    )

    subp_makezip.add_argument(
        "output",
        help="Output zipfile",
    )

    # pass the args to the main function
    exit(main(parser.parse_args()))
