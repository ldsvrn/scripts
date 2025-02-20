#!/usr/bin/env python3

import argparse
import tempfile
import zipfile
import os
import json
from sys import exit
from glob import glob

# from statistics import mode
import collections

# from prettytable import PrettyTable

parser = argparse.ArgumentParser(
    description="Extract basic information out a Spotify Extended Streaming History"
)
parser.add_argument("-p", default="./my_spotify_data.zip", help="MyData.zip path")
parser.add_argument("-n", default=10, help="Number of results in top")
args = parser.parse_args()

if not os.path.exists(args.p):
    print(f"File {args.p} does not exist.")
    exit(1)

timePlayed = 0
artists = []
songs = []
artist_time = {}
song_time = {}

with zipfile.ZipFile(args.p, "r") as spotify_data:
    with tempfile.TemporaryDirectory() as tempdir:
        spotify_data.extractall(path=tempdir)
        json_files = glob(f"{tempdir}/MyData/*json")
        for json_f in json_files:
            with open(json_f, "r", encoding="utf8") as file:
                history = json.loads(file.read())

                for event in history:
                    artist = event.get("master_metadata_album_artist_name")
                    song = event.get("master_metadata_track_name")
                    msplayed = int(event.get("ms_played"))

                    try:
                        artist_time[artist] += msplayed
                    except KeyError:
                        artist_time[artist] = msplayed

                    try:
                        song_time[f"{artist} - {song}"] += msplayed
                    except KeyError:
                        song_time[f"{artist} - {song}"] = msplayed

                    artists.append(artist)
                    songs.append(song)
                    timePlayed += msplayed

top_artists = collections.Counter(artist_time)
top_songs = collections.Counter(song_time)

# Get the most listened
top_artists = top_artists.most_common(int(args.n))
top_songs = top_songs.most_common(int(args.n))

print(f"TOP {args.n} ARTISTS ({len(set(artists))} in total):")
for artist, time_played in top_artists:
    print(f"Artist: {artist}, Time Played: {round(time_played /3600000, 2)}h")

print(f"\n\nTOP {args.n} SONGS: ({len(set(songs))} different songs, {len(songs)} in total)")
for song, time_played in top_songs:
    print(f"Song: {song}, Time Played: {round(time_played /3600000, 2)}h")

exit(0)
