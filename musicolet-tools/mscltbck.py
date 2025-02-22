import sqlite3
import os
import logging
import io
import json
from tempfile import NamedTemporaryFile
from Crypto.Cipher import Blowfish
from Crypto.Util.Padding import unpad
from zipfile import ZipFile
from urllib.parse import unquote, urlparse, parse_qs

logger = logging.getLogger(__name__)


class MusicoletBackup:
    def __init__(self, backup_path: str):
        def __decrypt_file(data: bytes) -> bytes:
            # key from /u/wrr666: https://www.reddit.com/r/androidapps/comments/t9zwow/musicolet_reading_backup/
            # krosbits, WHY, just WHY is the backup encrypted???
            key = "JSTMUSIC_2"
            # => Blowfish cipher in ECB mode
            cipher = Blowfish.new(bytes(key, "utf-8"), Blowfish.MODE_ECB)

            data_decrypted = cipher.decrypt(data)
            # remove padding (internet said to do it, idk)
            data_decrypted = unpad(data_decrypted, Blowfish.block_size)
            return data_decrypted

        # we can decrypt all files from the zip
        with ZipFile(backup_path, "r") as zipbackup:
            decr_files = {}
            namelist = zipbackup.namelist()
            for name in namelist:
                try:
                    decr_data = __decrypt_file(zipbackup.open(name).read())
                except ValueError as e:
                    # note: the hash file is the only one that should fail,
                    # it is not encrypted, it is the md5 hash of the unencrypted "0.musicolet.backup" file
                    logger.error(f"Decryption failed for file '{name}': {e}")
                    continue

                logger.debug(f"Decrypted '{name}' successfully.")
                decr_files[name] = decr_data
            self.backup = decr_files

        self.__maindb_file = NamedTemporaryFile()
        self.__maindb_file.write(self.backup["DB_SONGS_LOG"])
        self.__maindb_conn = sqlite3.connect(self.__maindb_file.name)
        self.__maindb_conn.row_factory = sqlite3.Row
        self.__maindb_cursor = self.__maindb_conn.cursor()

    def __del__(self):
        logger.debug("deleted object, closing temporary files...")
        self.__maindb_file.close()

    def export_all_files(self, path: str) -> None:
        # make the dir if not exists
        os.makedirs(path, exist_ok=True)
        for name in self.backup.keys():
            with open(os.path.join(path, name), "wb") as f:
                logger.debug(f"Writing {os.path.join(path, name)}")
                f.write(self.backup[name])

    def get_top_N_songs_alltime(self, n: int) -> list:
        self.__maindb_cursor.execute(
            f'SELECT * FROM "TABLE_SONGS" ORDER BY "COL_NUM_PLAYED" DESC LIMIT {n};'
        )

        # results as a list of dict
        res = [dict(row) for row in self.__maindb_cursor.fetchall()]

        return res

    @staticmethod
    def __parse_path(path: str) -> str:
        # logger.debug(f"Parsing the url {path}")
        url = urlparse(path)
        if url.scheme == "file":
            # example: file:///storage/emulated/0/Music/xxx/yyy/zzz/01.mp3
            # dirty quick way to remove "/storage/emulated/0" to be consitent with other schemes,
            # if it is not there it will just return the full real path
            return url.path.split("/storage/emulated/0/")[-1]
        elif url.scheme == "musicolet":
            # example: musicolet://media-store?p_v=primary&p_rp=Music/xxx/yyy/zzz&p_dn=01.opus&p_id=1234567890&p_mt=1
            # we need url.query and use parse_qs() to get p_rp and p_dn
            qs = parse_qs(url.query)

            # this will raise a KeyError if the url is incorrect
            folder = qs["p_rp"][0].strip()
            file = qs["p_dn"][0].strip()

            return f"{folder}/{file}"
        elif url.scheme == "content":
            # example: content://com.android.externalstorage.documents/tree/primary:Music/document/primary:Music/xxx/yyy/zzz/02.opus
            # here url.path would be: /tree/primary:Music/document/primary:Music/xxx/yyy/zzz/02.opus, soooooooo:
            return url.path.split("document/primary:")[-1]

    def __parse_playlist(self, filename: str) -> list:
        """
        Returns a list of dict [{"path": p, "title": t, "album": a, "duration": d}]
        the default format is ungodly awful,
        first we need to create a list in a more sensible format
        however there is THREE ways that paths are stored: file:// content:// and musicolet://
        aaaaAAAAaaaaAAaaaaaAAaaAAaaAAAAAAAaaaAaaaAAaaaAAAaa
        """
        logger.info(f"Parsing playlist file '{filename}'...")
        raw = json.loads(unquote(self.backup[filename]))

        formatted = [
            {"path": MusicoletBackup.__parse_path(p), "title": t, "album": a, "duration": d}
            for p, t, a, d in zip(
                raw["S_P"],
                raw["S_T"],
                raw["S_AL"],
                raw["S_D"],
            )
        ]

        return formatted

    def playlist_exists(self, name: str) -> bool:
        return name + ".mpl" in self.backup.keys()

    def get_playlist(self, name: str) -> list:
        if playlist_exists(name):
            raise FileNotFoundError(f"Playlist '{name}' does not exist!")

        return self.__parse_playlist(name + ".mpl")

    @property
    def favorites(self) -> list:
        return self.__parse_playlist("0.favs")

    @property
    def playlists(self) -> list:
        playlists = []
        for file in self.backup.keys():
            split_filename = os.path.splitext(file)
            if split_filename[1] == ".mpl":
                playlists.append(split_filename[0])
        return playlists

    @property
    def listening_time_alltime(self) -> int:
        self.__maindb_cursor.execute(
            "SELECT SUM(COL_NUM_PLAYED * COL_DURATION) AS time FROM TABLE_SONGS;"
        )
        return int(self.__maindb_cursor.fetchall()[0]["time"])

    # all of theses are very wrong
    @property
    def listening_time_year(self) -> int:
        self.__maindb_cursor.execute(
            "SELECT SUM(COL_NUM_PLAYED_Y * COL_DURATION) AS time FROM TABLE_SONGS;"
        )
        return int(self.__maindb_cursor.fetchall()[0]["time"])

    @property
    def listening_time_month(self) -> int:
        self.__maindb_cursor.execute(
            "SELECT SUM(COL_NUM_PLAYED_M * COL_DURATION) AS time FROM TABLE_SONGS;"
        )
        return int(self.__maindb_cursor.fetchall()[0]["time"])

    @property
    def listening_time_week(self) -> int:
        self.__maindb_cursor.execute(
            "SELECT SUM(COL_NUM_PLAYED_W * COL_DURATION) AS time FROM TABLE_SONGS;"
        )
        return int(self.__maindb_cursor.fetchall()[0]["time"])
