import sqlite3
import os
import logging
from tempfile import TemporaryFile
from Crypto.Cipher import Blowfish
from Crypto.Util.Padding import unpad
from zipfile import ZipFile

logger = logging.getLogger(__name__)

class MusicoletBackup():
    def __init__(self, zipbackup: ZipFile):
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
        
        decr_files = {}
        # we can decrypt all files from the zip
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


    def export_all_files(self, path: str) -> None:
        # make the dir if not exists
        os.makedirs(path, exist_ok=True)
        for name in self.backup.keys():
            with open(os.path.join(path, name), "wb") as f:
                logger.debug(f"Writing {os.path.join(path, name)}")
                f.write(self.backup[name])
                
    
    def get_top_N_songs_alltime(self, n: int) -> list:
        if self.backup["DB_SONGS_LOG"] == None:
            raise Exception("File 'DB_SONGS_LOG' does not exist in the backup!")
        
        # we need the database to be in a file for the sqlite library to work
        with tempfile.TemporaryFile() as tempfile:
            tempfile.write(self.backup["DB_SONGS_LOG"])
            db = sqlite3.connect(tempfile).cursor()
            
            db.execute(
                f'SELECT * FROM "TABLE_SONGS" ORDER BY "COL_NUM_PLAYED" DESC LIMIT {n};'
            )
            
            return []
            