#!/usr/bin/env python3
from Crypto.Cipher import Blowfish
from Crypto.Util.Padding import unpad
from zipfile import ZipFile 

import logging
import argparse
import sqlite3
import tempfile
import os

logger = logging.getLogger(__name__)

def decrypt_file(data: bytes) -> bytes:
    # key from /u/wrr666: https://www.reddit.com/r/androidapps/comments/t9zwow/musicolet_reading_backup/
    # thanks to you I dont have to reverse engineer the apk to find the hard coded encryption key
    # also krosbits, WHY, just WHY is the backup encrypted??? 
    key = 'JSTMUSIC_2'  
    # => Blowfish cipher in ECB mode
    cipher = Blowfish.new(bytes(key, 'utf-8'), Blowfish.MODE_ECB)

    data_decrypted = cipher.decrypt(data)
    # remove padding (internet said to do it, idk)
    data_decrypted = unpad(data_decrypted, Blowfish.block_size)
    return data_decrypted


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    parser = argparse.ArgumentParser(description='Extract information out of a Musicolet backup')
    parser.add_argument('path', help='Musicolet backup path')
    parser.add_argument('-d', '--decrypt', help='Extracts and decrypts all files to the specified directory', required=False, metavar="dir")
    args = parser.parse_args()

    # open and extract all files from the backup
    with ZipFile(args.path, 'r') as encr_zip:
        # we can decrypt all files from the zip
        decr_files = {}
        namelist = encr_zip.namelist()
        # decrypt all files
        for name in namelist:
            try:
                decr_data = decrypt_file(encr_zip.open(name).read())
            except ValueError as e:
                logger.error(f"Decryption failed for file '{name}': {e}")
                continue

            decr_files[name] = decr_data 
            
        # if we only want to extract we can skip the temporary dir stuff
        if args.decrypt:
            # make the dir if not exists
            os.makedirs(args.decrypt, exist_ok=True)
            for name in decr_files.keys():
                with open(os.path.join(args.decrypt, name), "wb") as f:
                    f.write(decr_files[name])
            
        with tempfile.TemporaryDirectory() as tempdir:
            pass