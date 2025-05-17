import sqlite3
import os
import logging
import io
import json
from hashlib import md5
from tempfile import NamedTemporaryFile
from Crypto.Cipher import Blowfish
from Crypto.Util.Padding import unpad, pad
import zipfile
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
        with zipfile.ZipFile(backup_path, "r") as zipbackup:
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

    @staticmethod
    def encrypt_backup(dirpath: str, outpath: str):
        """This function can be used to create a valid Musicolet backup zip from a decrypted
        backup. Note: for now it does NOT support adding files to the backup!!

        Args:
            dirpath (str): path of the decrypted backup dir
            outpath (str): path of the zip
        """

        def __encrypt_file(data: bytes) -> bytes:
            key = "JSTMUSIC_2"
            cipher = Blowfish.new(bytes(key, "utf-8"), Blowfish.MODE_ECB)
            return cipher.encrypt(pad(data, Blowfish.block_size))

        bck_files = {}

        for root, _, files in os.walk(dirpath):
            if "0.musicolet.backup" not in files:
                raise Exception("there is no '0.musicolet.backup' file!")

            for file in files:
                filepath = os.path.join(root, file)
                relpath = os.path.relpath(filepath, dirpath)

                with open(filepath, "rb") as f:
                    data = f.read()

                if file != "0.musicolet.backup":
                    logger.debug(f"adding {file} in the dict")
                    bck_files[relpath] = {"data": data, "md5": md5(data).hexdigest()}
                else:
                    backup_file = json.loads(data)

        # preparing the "0.musicolet.backup" file
        for file in backup_file["md5"].keys():
            # replace all md4 in the "0.musicolet.backup" file with the newly calculated ones
            try:
                backup_file["md5"][file] = bck_files[file]["md5"]
            except KeyError:
                raise Exception(
                    f"File '{file}' is present in '0.musicolet.backup' but not in the dir!"
                )

        with zipfile.ZipFile(outpath, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in bck_files.keys():
                logger.debug(f"adding {file} in the {outpath} zipfile.")
                zipf.writestr(file, __encrypt_file(bck_files[file]["data"]))

            # write the hash file
            zipf.writestr(
                "hash", md5(json.dumps(backup_file).encode("utf-8")).hexdigest().encode("utf-8")
            )

    def export_all_files(self, path: str) -> None:
        # make the dir if not exists
        os.makedirs(path, exist_ok=True)
        for name in self.backup.keys():
            with open(os.path.join(path, name), "wb") as f:
                logger.debug(f"Writing {os.path.join(path, name)}")
                f.write(self.backup[name])

    def get_top_songs_alltime(self, n: int = 0) -> list:
        """
        returns a list of dict object with top n songs, by the number of times it was listened to
        """
        if n >= 1:
            sql = f'SELECT * FROM "TABLE_SONGS" ORDER BY "COL_NUM_PLAYED" DESC LIMIT {n};'
        elif n == 0:
            sql = 'SELECT * FROM "TABLE_SONGS" ORDER BY "COL_NUM_PLAYED" DESC;'
        else:
            raise ValueError("Value of n cannot be negative!")

        logger.debug(f"Running '{sql}' on 'DB_SONGS_LOG'...")
        self.__maindb_cursor.execute(sql)

        # results as a list of dict, parsing the path is probably overkill here,
        # since "COL_LOGPATH" has clean paths but I want paths to be consitent with playlists
        return [
            {**dict(row), "COL_PATH": MusicoletBackup.__parse_path(row["COL_PATH"])}
            for row in self.__maindb_cursor.fetchall()
        ]

    def get_top_songs_alltime_by_time(self, n: int = 0) -> list:
        """
        returns a list of dict object with the top n songs, accounts for the length of the songs
        """
        if n >= 1:
            sql = f"""
            SELECT * FROM "TABLE_SONGS" 
            ORDER BY ("COL_NUM_PLAYED" * "COL_DURATION") DESC 
            LIMIT {n};
            """
        elif n == 0:
            sql = """
            SELECT * FROM "TABLE_SONGS" 
            ORDER BY ("COL_NUM_PLAYED" * "COL_DURATION") DESC;
            """
        else:
            raise ValueError("Value of n cannot be negative!")

        logger.debug(f"Running '{sql}' on 'DB_SONGS_LOG'...")
        self.__maindb_cursor.execute(sql)

        # results as a list of dict, parsing the path is probably overkill here,
        # since "COL_LOGPATH" has clean paths but I want paths to be consitent with playlists
        return [
            {**dict(row), "COL_PATH": MusicoletBackup.__parse_path(row["COL_PATH"])}
            for row in self.__maindb_cursor.fetchall()
        ]

    @staticmethod
    def __parse_path(path: str) -> str:
        # logger.debug(f"Parsing the url {path}")
        url = urlparse(path)
        # we unquote at the end because for the musicolet:// scheme parse_qs() would fail if the path has '&' chars
        if url.scheme == "file":
            # example: file:///storage/emulated/0/Music/xxx/yyy/zzz/01.mp3
            # dirty quick way to remove "/storage/emulated/0" to be consitent with other schemes,
            # if it is not there it will just return the full real path
            return unquote(url.path.split("/storage/emulated/0/")[-1])
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
            return unquote(url.path).split("document/primary:")[-1]
        else:
            raise Exception(f"Unexpected '{url.scheme}' url scheme!")

    def __parse_playlist(self, filename: str) -> list:
        """
        Returns a list of dict [{"path": p, "title": t, "album": a, "duration": d}]
        the default format is ungodly awful,
        first we need to create a list in a more sensible format
        however there is THREE ways that paths are stored: file:// content:// and musicolet://
        aaaaAAAAaaaaAAaaaaaAAaaAAaaAAAAAAAaaaAaaaAAaaaAAAaa
        """
        logger.info(f"Parsing playlist file '{filename}'...")
        raw = json.loads(self.backup[filename])

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
        exist = f"{name}.mpl" in self.backup
        if not exist:
            logging.debug(f"Playlist not found '{name}.mpl' in {self.backup.keys()}")
        return exist

    def get_playlist(self, name: str) -> list:
        if not self.playlist_exists(name):
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
