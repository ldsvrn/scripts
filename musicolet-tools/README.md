# WIP: Musicolet backup tools

This is a WIP script to pull information from a Musicolet backup .zip file. 

[Musicolet](https://play.google.com/store/apps/details?id=in.krosbits.musicolet) is a free (as in beer) but closed source music player for Android. However it is completely offline, it doesn't even have the network permission. 

Even after multiple years of searching, I'm unable to find an open-source equivalent that even comes close to it in terms of functionalities.

Musicolet uses unencrypted .zip backups, however every file in the archive is BLowfish encrypted with the **hardcoded key** `JSTMUSIC_2`. Yes, it is indeed using a **HARDCODED ENCRYPTION KEY** (see [here](https://www.reddit.com/r/androidapps/comments/t9zwow/comment/i0tfpaa/))for some unknown reason. This key is prone to change depending on the developper mind, but since its hardcoded (completely useless) it can always be found again. 

## Usage (WIP)
```
usage: musicolet-tools.py [-h] [-d dir] path

Extract information out of a Musicolet backup

positional arguments:
  path               Musicolet backup path

options:
  -h, --help         show this help message and exit
  -d, --decrypt dir  Extracts and decrypts all files to the specified directory
```